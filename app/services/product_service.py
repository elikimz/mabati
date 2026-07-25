"""Product business logic for catalogue products, images, and priced variations."""
import re
from decimal import Decimal
from typing import Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductImage, ProductVariation
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductImageCreate,
    ProductUpdate,
    ProductVariationCreate,
    ProductVariationUpsert,
)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductRepository(db)
        self.cat_repo = CategoryRepository(db)

    async def _validate_category(self, category_id: int):
        category = await self.cat_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
        return category

    async def _ensure_unique_slug(self, base_slug: str, exclude_id: Optional[int] = None) -> str:
        slug = base_slug
        counter = 1
        while True:
            existing = await self.repo.get_by_slug(slug)
            if existing is None or (exclude_id and existing.id == exclude_id):
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1

    async def _validate_variation_skus(
        self,
        variations: Iterable[ProductVariationCreate | ProductVariationUpsert],
    ) -> None:
        seen_skus: set[str] = set()
        for variation in variations:
            if not variation.sku:
                continue
            normalized = variation.sku.strip().lower()
            if normalized in seen_skus:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Duplicate variation SKU '{variation.sku}' in this product",
                )
            seen_skus.add(normalized)

            existing = await self.repo.get_variation_by_sku(variation.sku.strip())
            if existing and existing.id != getattr(variation, "id", None):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Variation SKU '{variation.sku}' is already in use",
                )

    @staticmethod
    def _build_variation(data: ProductVariationCreate | ProductVariationUpsert) -> ProductVariation:
        payload = data.model_dump(exclude={"id"}, exclude_none=True)
        if payload.get("sku"):
            payload["sku"] = payload["sku"].strip()
        return ProductVariation(**payload)

    @staticmethod
    def _apply_variation_data(
        variation: ProductVariation,
        data: ProductVariationUpsert,
    ) -> None:
        payload = data.model_dump(exclude={"id"}, exclude_none=True)
        if payload.get("sku"):
            payload["sku"] = payload["sku"].strip()
        for field, value in payload.items():
            setattr(variation, field, value)

    @staticmethod
    def _refresh_price_summary(product: Product) -> None:
        """Keep old aggregate fields meaningful for variation-enabled products."""
        active_variations = [item for item in product.variations if item.is_active]
        if not active_variations:
            return

        effective_prices = [
            Decimal(item.discount_price if item.discount_price is not None else item.price)
            for item in active_variations
        ]
        minimum = min(effective_prices)
        maximum = max(effective_prices)
        product.price_from = minimum
        product.price_to = maximum if maximum != minimum else None
        # A product-wide discount cannot accurately represent variation-specific offers.
        product.discount_price = None

    async def create(self, data: ProductCreate) -> Product:
        await self._validate_category(data.category_id)
        await self._validate_variation_skus(data.variations)

        images_data = data.images
        product_dict = data.model_dump(exclude={"images", "variations"})
        if not product_dict.get("slug"):
            product_dict["slug"] = await self._ensure_unique_slug(_slugify(product_dict["name"]))

        variations = [self._build_variation(item) for item in data.variations]
        if variations:
            product_dict["price_from"] = min(
                item.discount_price if item.discount_price is not None else item.price
                for item in variations
            )
            effective_prices = [
                item.discount_price if item.discount_price is not None else item.price
                for item in variations
            ]
            product_dict["price_to"] = max(effective_prices) if max(effective_prices) != min(effective_prices) else None
            product_dict["discount_price"] = None

        product = Product(**product_dict)
        product.variations = variations
        product.images = [
            ProductImage(
                image_url=image.image_url,
                is_primary=image.is_primary or index == 0,
                display_order=image.display_order if image.display_order else index,
                alt_text=image.alt_text,
            )
            for index, image in enumerate(images_data)
        ]
        self._refresh_price_summary(product)
        return await self.repo.create(product)

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if data.category_id is not None:
            await self._validate_category(data.category_id)

        update_dict = data.model_dump(exclude_unset=True, exclude={"variations"})
        if "name" in update_dict and "slug" not in update_dict:
            update_dict["slug"] = await self._ensure_unique_slug(
                _slugify(update_dict["name"]),
                exclude_id=product_id,
            )
        for field, value in update_dict.items():
            setattr(product, field, value)

        if data.variations is not None:
            await self._validate_variation_skus(data.variations)
            current_by_id = {variation.id: variation for variation in product.variations}
            replacement: list[ProductVariation] = []

            for incoming in data.variations:
                if incoming.id is None:
                    replacement.append(self._build_variation(incoming))
                    continue

                variation = current_by_id.get(incoming.id)
                if not variation:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Variation {incoming.id} does not belong to product {product_id}",
                    )
                self._apply_variation_data(variation, incoming)
                replacement.append(variation)

            # Treat the supplied list as the desired state. ORM delete-orphan removes
            # omitted child rows while historical order snapshots remain intact.
            product.variations = replacement
            self._refresh_price_summary(product)

        return await self.repo.update(product)

    async def delete(self, product_id: int) -> None:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        await self.repo.delete(product)

    async def add_image(self, product_id: int, data: ProductImageCreate) -> ProductImage:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        image = ProductImage(
            product_id=product_id,
            image_url=data.image_url,
            is_primary=data.is_primary,
            display_order=data.display_order,
            alt_text=data.alt_text,
        )
        return await self.repo.add_image(image)

    async def delete_image(self, product_id: int, image_id: int) -> None:
        image = await self.repo.get_image_by_id(image_id)
        if not image or image.product_id != product_id:
            raise HTTPException(status_code=404, detail="Image not found")
        await self.repo.delete_image(image)

    async def get_related(self, product_id: int, limit: int = 6):
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return await self.repo.get_related(product, limit=limit)

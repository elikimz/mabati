"""Product business logic service — upgraded with slug, images, and related products."""
import re
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductImage
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductImageCreate, ProductUpdate


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductRepository(db)
        self.cat_repo = CategoryRepository(db)

    async def _validate_category(self, category_id: int):
        cat = await self.cat_repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
        return cat

    async def _ensure_unique_slug(self, base_slug: str, exclude_id: int = None) -> str:
        slug = base_slug
        counter = 1
        while True:
            existing = await self.repo.get_by_slug(slug)
            if existing is None or (exclude_id and existing.id == exclude_id):
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1

    async def create(self, data: ProductCreate) -> Product:
        await self._validate_category(data.category_id)
        images_data = data.images or []
        product_dict = data.model_dump(exclude={"images"})
        if not product_dict.get("slug"):
            base_slug = _slugify(product_dict["name"])
            product_dict["slug"] = await self._ensure_unique_slug(base_slug)
        product = Product(**product_dict)
        product = await self.repo.create(product)
        for idx, img_data in enumerate(images_data):
            img = ProductImage(
                product_id=product.id,
                image_url=img_data.image_url,
                is_primary=img_data.is_primary or idx == 0,
                display_order=img_data.display_order if img_data.display_order else idx,
                alt_text=img_data.alt_text,
            )
            await self.repo.add_image(img)
        return await self.repo.get_by_id(product.id)

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if data.category_id is not None:
            await self._validate_category(data.category_id)
        update_dict = data.model_dump(exclude_unset=True)
        if "name" in update_dict and "slug" not in update_dict:
            base_slug = _slugify(update_dict["name"])
            update_dict["slug"] = await self._ensure_unique_slug(base_slug, exclude_id=product_id)
        for field, value in update_dict.items():
            setattr(product, field, value)
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
        img = ProductImage(
            product_id=product_id,
            image_url=data.image_url,
            is_primary=data.is_primary,
            display_order=data.display_order,
            alt_text=data.alt_text,
        )
        return await self.repo.add_image(img)

    async def delete_image(self, product_id: int, image_id: int) -> None:
        img = await self.repo.get_image_by_id(image_id)
        if not img or img.product_id != product_id:
            raise HTTPException(status_code=404, detail="Image not found")
        await self.repo.delete_image(img)

    async def get_related(self, product_id: int, limit: int = 6):
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return await self.repo.get_related(product, limit=limit)

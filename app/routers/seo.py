"""SEO router — robots.txt and sitemap.xml endpoints."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.product import Product
from app.models.category import Category

router = APIRouter(tags=["SEO"])

# ── Configuration ─────────────────────────────────────────────────────────────
# Change this to your actual production domain
SITE_DOMAIN = "mrmmabati.co.ke"
FRONTEND_URL = f"https://{SITE_DOMAIN}"


# ── robots.txt ────────────────────────────────────────────────────────────────
ROBOTS_TXT = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/admin/
Disallow: /docs
Disallow: /redoc
Disallow: /openapi.json
Disallow: /login
Disallow: /register
Disallow: /my-orders

Sitemap: {FRONTEND_URL}/sitemap.xml
"""


@router.get("/robots.txt", response_class=Response)
async def robots_txt():
    """Serve robots.txt for search engine crawlers."""
    return Response(
        content=ROBOTS_TXT,
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )


# ── sitemap.xml ───────────────────────────────────────────────────────────────
SITEMAP_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
SITEMAP_FOOTER = "</urlset>\n"


def _url_xml(loc: str, lastmod: Optional[datetime] = None, changefreq: str = "weekly", priority: str = "0.8") -> str:
    """Build a single <url> entry for the sitemap."""
    xml = f"  <url>\n    <loc>{loc}</loc>\n"
    if lastmod:
        xml += f"    <lastmod>{lastmod.strftime('%Y-%m-%d')}</lastmod>\n"
    xml += f"    <changefreq>{changefreq}</changefreq>\n"
    xml += f"    <priority>{priority}</priority>\n"
    xml += "  </url>\n"
    return xml


@router.get("/sitemap.xml", response_class=Response)
async def sitemap_xml(db: AsyncSession = Depends(get_db)):
    """Generate and serve sitemap.xml with all public pages and products."""
    urls = []

    # ── Static public pages ──────────────────────────────────────────────────
    urls.append(_url_xml(f"{FRONTEND_URL}/", changefreq="daily", priority="1.0"))
    urls.append(_url_xml(f"{FRONTEND_URL}/products", changefreq="daily", priority="0.9"))
    urls.append(_url_xml(f"{FRONTEND_URL}/about", changefreq="monthly", priority="0.7"))
    urls.append(_url_xml(f"{FRONTEND_URL}/contact", changefreq="monthly", priority="0.7"))

    # ── Category pages ────────────────────────────────────────────────────────
    cat_result = await db.execute(
        select(Category).filter(
            Category.is_active == True
        ).order_by(Category.id)
    )
    categories = cat_result.scalars().all()
    for cat in categories:
        lastmod = getattr(cat, "updated_at", None)
        urls.append(
            _url_xml(
                f"{FRONTEND_URL}/products?category_id={cat.id}",
                lastmod=lastmod,
                changefreq="weekly",
                priority="0.8",
            )
        )

    # ── Product pages ─────────────────────────────────────────────────────────
    prod_result = await db.execute(
        select(Product).filter(
            Product.is_active == True,
            Product.is_available == True,
        ).order_by(Product.id)
    )
    products = prod_result.scalars().all()
    for product in products:
        if product.slug:
            product_url = f"{FRONTEND_URL}/products/{product.slug}"
        else:
            product_url = f"{FRONTEND_URL}/products/{product.id}"
        urls.append(
            _url_xml(
                product_url,
                lastmod=product.updated_at,
                changefreq="weekly",
                priority="0.8",
            )
        )

    sitemap = SITEMAP_HEADER + "\n".join(urls) + SITEMAP_FOOTER

    return Response(
        content=sitemap,
        media_type="application/xml; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=3600",
        },
    )


# ── Crawler status endpoint ──────────────────────────────────────────────────
@router.get("/status", response_class=Response)
async def crawler_status():
    """Minimal status endpoint for crawlers and monitoring."""
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?>\n<status><ok>true</ok></status>\n',
        media_type="application/xml; charset=utf-8",
    )

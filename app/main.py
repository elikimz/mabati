"""Main FastAPI application entry point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.utils.logging import setup_logging

# Configure logging before anything else
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Professional REST API for Mabati Roofing Materials — "
        "products, categories, inventory, orders, and admin management."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security & Cache Headers ─────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers and cache control for SEO and safety."""
    response = await call_next(request)
    # Prevent admin/API paths from being indexed
    if request.url.path.startswith("/admin/") or request.url.path.startswith("/api/admin/"):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    # Add X-Content-Type-Options for security
    if "X-Content-Type-Options" not in response.headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
    # Add X-Frame-Options
    if "X-Frame-Options" not in response.headers:
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
    # Add Referrer-Policy
    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers.auth import router as auth_router
from app.routers.users import router as admin_users_router, profile_router
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.inventory import router as inventory_router
from app.routers.orders import router as orders_router
from app.routers.dashboard import router as dashboard_router
from app.routers.banners import router as banners_router
from app.routers.site_content import router as site_content_router
from app.routers.gallery import router as gallery_router
from app.routers.seo import router as seo_router

app.include_router(seo_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(admin_users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(orders_router)
app.include_router(dashboard_router)
app.include_router(banners_router)
app.include_router(site_content_router)
app.include_router(gallery_router)

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {"status": "healthy"}

logger.info("Mabati Roofing API started — %s v%s", settings.APP_NAME, settings.APP_VERSION)

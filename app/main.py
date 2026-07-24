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

# ── Routers ───────────────────────────────────────────────────────────────────

from app.routers.auth import router as auth_router
from app.routers.users import router as admin_users_router, profile_router
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.inventory import router as inventory_router
from app.routers.orders import router as orders_router
from app.routers.dashboard import router as dashboard_router

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(admin_users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(orders_router)
app.include_router(dashboard_router)


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

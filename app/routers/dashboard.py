"""Admin dashboard router: aggregated statistics."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.dashboard import DashboardStats, SalesSummary

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Return aggregated statistics for the admin dashboard."""
    product_repo = ProductRepository(db)
    category_repo = CategoryRepository(db)
    user_repo = UserRepository(db)
    order_repo = OrderRepository(db)

    total_products = await product_repo.count()
    total_categories = await category_repo.count()
    total_customers = await user_repo.count_customers()
    total_orders = await order_repo.count()
    total_revenue = await order_repo.total_revenue()
    completed_orders = await order_repo.count_by_status("completed")
    pending_orders = await order_repo.count_by_status("pending")
    cancelled_orders = await order_repo.count_by_status("cancelled")
    low_stock = await product_repo.get_low_stock()

    return DashboardStats(
        total_products=total_products,
        total_categories=total_categories,
        total_customers=total_customers,
        total_orders=total_orders,
        sales_summary=SalesSummary(
            total_revenue=total_revenue,
            completed_orders=completed_orders,
            pending_orders=pending_orders,
            cancelled_orders=cancelled_orders,
        ),
        low_stock_products=low_stock,
    )

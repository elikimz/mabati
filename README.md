# Mabati Roofing API

A professional, production-ready **FastAPI** backend for a Mabati (roofing materials) e-commerce platform.

## Quick Start

1. Clone: `git clone https://github.com/elikimz/mabatiAPI.git`
2. Install: `pip install -r requirements.txt`
3. Configure: `cp .env.example .env` then edit with your DB URL and SECRET_KEY
4. Migrate: `alembic upgrade head`
5. Run: `uvicorn app.main:app --reload`
6. Docs: http://localhost:8000/docs

## API Endpoints (27 total)

### Auth
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- GET /auth/me

### Products
- GET /products (search, filter by category/color/gauge/price)
- GET /products/{id}
- POST /admin/products
- PUT /admin/products/{id}
- DELETE /admin/products/{id}

### Categories
- GET /categories
- POST /admin/categories
- PUT /admin/categories/{id}
- DELETE /admin/categories/{id}

### Inventory
- GET /admin/inventory/
- POST /admin/inventory/{id}/adjust
- GET /admin/inventory/{id}/logs

### Orders
- POST /orders
- GET /orders/my-orders
- GET /orders/{id}
- GET /admin/orders
- PUT /admin/orders/{id}/status

### Admin Dashboard
- GET /admin/dashboard

## Tests

43 passing tests covering all endpoints.

```bash
pytest tests/ -v
```

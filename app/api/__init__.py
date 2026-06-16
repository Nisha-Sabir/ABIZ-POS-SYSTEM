from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.digi_khata import router as digi_khata_router
from app.api.inventory import router as inventory_router
from app.api.license_keys import router as license_keys_router
from app.api.products import router as products_router
from app.api.sales import router as sales_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(digi_khata_router)
api_router.include_router(inventory_router)
api_router.include_router(license_keys_router)
api_router.include_router(products_router)
api_router.include_router(sales_router)

__all__ = ["api_router"]

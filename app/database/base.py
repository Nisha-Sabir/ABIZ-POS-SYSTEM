from app.database.session import Base

# Import all models here so Alembic can discover them from Base.metadata.
from app.models.cart_item import CartItem  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.digi_khata import DigiKhata  # noqa: F401
from app.models.inventory_transaction import InventoryTransaction  # noqa: F401
from app.models.license_key import LicenseKey  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.sale import Sale  # noqa: F401
from app.models.sale_item import SaleItem  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ["Base"]

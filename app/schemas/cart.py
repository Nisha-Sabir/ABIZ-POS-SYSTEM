from decimal import Decimal

from pydantic import BaseModel, Field


class ProductScanResponse(BaseModel):
    product_id: int
    name: str
    qr_code: str
    sale_price: Decimal
    available_stock: int


class CartItemRequest(BaseModel):
    qr_code: str = Field(min_length=1, max_length=255)
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    product_id: int
    name: str
    qr_code: str
    quantity: int
    unit_price: Decimal
    item_total: Decimal
    profit_per_unit: Decimal
    total_profit: Decimal
    available_stock: int


class CartResponse(BaseModel):
    user_id: int
    items: list[CartItemResponse]
    total_amount: Decimal
    total_profit: Decimal

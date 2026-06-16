from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SaleItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    profit: Decimal

    model_config = ConfigDict(from_attributes=True)


class SaleResponse(BaseModel):
    id: int
    total_amount: Decimal
    total_profit: Decimal
    created_at: datetime
    items: list[SaleItemResponse]

    model_config = ConfigDict(from_attributes=True)


class CheckoutResponse(BaseModel):
    sale: SaleResponse
    message: str = "Sale completed successfully."

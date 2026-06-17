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
    client_sale_id: str | None = None
    source: str
    total_amount: Decimal
    total_profit: Decimal
    created_at: datetime
    items: list[SaleItemResponse]

    model_config = ConfigDict(from_attributes=True)


class CheckoutResponse(BaseModel):
    sale: SaleResponse
    message: str = "Sale completed successfully."


class OfflineSaleItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal | None = None


class OfflineSaleCreate(BaseModel):
    client_sale_id: str
    created_at: datetime
    items: list[OfflineSaleItemCreate]


class OfflineSyncRequest(BaseModel):
    sales: list[OfflineSaleCreate]


class OfflineSyncResult(BaseModel):
    client_sale_id: str
    status: str
    sale_id: int | None = None
    message: str | None = None


class OfflineSyncResponse(BaseModel):
    results: list[OfflineSyncResult]

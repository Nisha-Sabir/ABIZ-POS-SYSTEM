from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory_transaction import InventoryTransactionType


class StockInRequest(BaseModel):
    quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)


class StockOutRequest(BaseModel):
    quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)


class InventoryResponse(BaseModel):
    product_id: int
    product_name: str
    stock_quantity: int


class InventoryHistoryResponse(BaseModel):
    id: int
    product_id: int
    transaction_type: InventoryTransactionType
    quantity: int
    notes: str | None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

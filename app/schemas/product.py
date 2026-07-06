from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    qr_code: str | None = Field(default=None, min_length=1, max_length=255)
    purchase_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)
    category_id: int = Field(gt=0)

    @field_validator("name", "qr_code")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value

    @model_validator(mode="after")
    def validate_prices(self) -> "ProductCreate":
        if self.sale_price < self.purchase_price:
            raise ValueError("Sale price must be greater than or equal to purchase price.")
        return self


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    qr_code: str | None = Field(default=None, min_length=1, max_length=255)
    purchase_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)
    category_id: int | None = Field(default=None, gt=0)

    @field_validator("name", "qr_code")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class ProductResponse(BaseModel):
    id: int
    name: str
    qr_code: str
    purchase_price: Decimal
    sale_price: Decimal
    stock_quantity: int
    low_stock_threshold: int
    category_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DigiKhataResponse(BaseModel):
    id: int
    date: date
    total_sales: Decimal
    total_profit: Decimal

    model_config = ConfigDict(from_attributes=True)

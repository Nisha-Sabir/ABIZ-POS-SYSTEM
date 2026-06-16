from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class DigiKhata(Base):
    __tablename__ = "digi_khata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True, unique=True)
    total_sales: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_sale_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="online")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items: Mapped[list["SaleItem"]] = relationship(
        back_populates="sale",
        cascade="all, delete-orphan",
    )

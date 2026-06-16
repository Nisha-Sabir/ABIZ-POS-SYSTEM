from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.digi_khata import DigiKhata


def update_daily_digi_khata(
    db: Session,
    entry_date: date,
    sale_amount: Decimal,
    profit_amount: Decimal,
) -> DigiKhata:
    statement = select(DigiKhata).where(DigiKhata.date == entry_date)
    entry = db.scalars(statement).first()

    if entry is None:
        entry = DigiKhata(
            date=entry_date,
            total_sales=sale_amount,
            total_profit=profit_amount,
        )
        db.add(entry)
    else:
        entry.total_sales += sale_amount
        entry.total_profit += profit_amount

    return entry


def get_digi_khata_entries(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[DigiKhata]:
    statement = select(DigiKhata).order_by(DigiKhata.date.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())

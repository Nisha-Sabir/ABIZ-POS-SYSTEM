from datetime import date, datetime, time, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.inventory_transaction import (
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.product import Product


def get_product_stock(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def add_stock(
    db: Session,
    product: Product,
    quantity: int,
    created_by: int,
    notes: str | None = None,
) -> InventoryTransaction:
    product.stock_quantity += quantity

    transaction = InventoryTransaction(
        product_id=product.id,
        transaction_type=InventoryTransactionType.STOCK_IN,
        quantity=quantity,
        notes=notes,
        created_by=created_by,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    db.refresh(product)
    return transaction


def remove_stock(
    db: Session,
    product: Product,
    quantity: int,
    created_by: int,
    notes: str | None = None,
) -> InventoryTransaction:
    product.stock_quantity -= quantity

    transaction = InventoryTransaction(
        product_id=product.id,
        transaction_type=InventoryTransactionType.STOCK_OUT,
        quantity=quantity,
        notes=notes,
        created_by=created_by,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    db.refresh(product)
    return transaction


def get_inventory_history(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    product_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[InventoryTransaction]:
    statement: Select[tuple[InventoryTransaction]] = select(InventoryTransaction).join(
        Product,
        InventoryTransaction.product_id == Product.id,
    )

    if search:
        statement = statement.where(Product.name.ilike(f"%{search.strip()}%"))

    if product_id is not None:
        statement = statement.where(InventoryTransaction.product_id == product_id)

    if start_date is not None:
        start_datetime = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        statement = statement.where(InventoryTransaction.created_at >= start_datetime)

    if end_date is not None:
        end_datetime = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        statement = statement.where(InventoryTransaction.created_at <= end_datetime)

    statement = (
        statement.order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_low_stock_products(
    db: Session,
    threshold: int = 10,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> list[Product]:
    statement = select(Product).where(Product.stock_quantity <= threshold)

    if search:
        statement = statement.where(Product.name.ilike(f"%{search.strip()}%"))

    statement = statement.order_by(Product.stock_quantity.asc(), Product.name).offset(skip).limit(limit)
    return list(db.scalars(statement).all())

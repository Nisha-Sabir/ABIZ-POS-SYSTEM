from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.services.cart_service import clear_user_cart, get_user_cart_items
from app.services.digi_khata_service import update_daily_digi_khata


def get_sales(db: Session, skip: int = 0, limit: int = 100) -> list[Sale]:
    statement = select(Sale).order_by(Sale.created_at.desc(), Sale.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_sale_by_id(db: Session, sale_id: int) -> Sale | None:
    return db.get(Sale, sale_id)


def calculate_cart_totals(cart_items: list[CartItem]) -> tuple[Decimal, Decimal]:
    total_amount = Decimal("0.00")
    total_profit = Decimal("0.00")

    for cart_item in cart_items:
        product = cart_item.product
        quantity = cart_item.quantity
        total_amount += product.sale_price * quantity
        total_profit += (product.sale_price - product.purchase_price) * quantity

    return total_amount, total_profit


def validate_cart_stock(cart_items: list[CartItem]) -> str | None:
    for cart_item in cart_items:
        if cart_item.product.stock_quantity < cart_item.quantity:
            return cart_item.product.name

    return None


def checkout_cart(db: Session, user_id: int) -> Sale:
    cart_items = get_user_cart_items(db, user_id)

    if not cart_items:
        raise ValueError("Cart is empty.")

    unavailable_product = validate_cart_stock(cart_items)
    if unavailable_product:
        raise ValueError(f"Insufficient stock for {unavailable_product}.")

    total_amount, total_profit = calculate_cart_totals(cart_items)
    sale = Sale(total_amount=total_amount, total_profit=total_profit)
    db.add(sale)
    db.flush()

    for cart_item in cart_items:
        product = cart_item.product
        quantity = cart_item.quantity
        item_profit = (product.sale_price - product.purchase_price) * quantity
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.sale_price,
            profit=item_profit,
        )
        db.add(sale_item)
        product.stock_quantity -= quantity

    update_daily_digi_khata(
        db=db,
        entry_date=date.today(),
        sale_amount=total_amount,
        profit_amount=total_profit,
    )
    clear_user_cart(db, user_id)
    db.commit()
    db.refresh(sale)
    return sale

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.cart import CartItemResponse, CartResponse


def get_cart_item(db: Session, user_id: int, product_id: int) -> CartItem | None:
    statement = select(CartItem).where(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id,
    )
    return db.scalars(statement).first()


def add_product_to_cart(db: Session, user_id: int, product: Product, quantity: int) -> CartItem:
    cart_item = get_cart_item(db, user_id, product.id)

    if cart_item is None:
        cart_item = CartItem(user_id=user_id, product_id=product.id, quantity=quantity)
        db.add(cart_item)
    else:
        cart_item.quantity += quantity

    db.commit()
    db.refresh(cart_item)
    return cart_item


def get_user_cart_items(db: Session, user_id: int) -> list[CartItem]:
    statement = select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)
    return list(db.scalars(statement).all())


def remove_product_from_cart(db: Session, user_id: int, product_id: int) -> bool:
    cart_item = get_cart_item(db, user_id, product_id)

    if cart_item is None:
        return False

    db.delete(cart_item)
    db.commit()
    return True


def clear_user_cart(db: Session, user_id: int) -> None:
    for cart_item in get_user_cart_items(db, user_id):
        db.delete(cart_item)
    db.commit()


def build_cart_response(user_id: int, cart_items: list[CartItem]) -> CartResponse:
    items: list[CartItemResponse] = []
    total_amount = Decimal("0.00")
    total_profit = Decimal("0.00")

    for cart_item in cart_items:
        product = cart_item.product
        quantity = cart_item.quantity
        item_total = product.sale_price * quantity
        profit_per_unit = product.sale_price - product.purchase_price
        item_profit = profit_per_unit * quantity
        total_amount += item_total
        total_profit += item_profit

        items.append(
            CartItemResponse(
                product_id=product.id,
                name=product.name,
                qr_code=product.qr_code,
                quantity=quantity,
                unit_price=product.sale_price,
                item_total=item_total,
                profit_per_unit=profit_per_unit,
                total_profit=item_profit,
                available_stock=product.stock_quantity,
            )
        )

    return CartResponse(
        user_id=user_id,
        items=items,
        total_amount=total_amount,
        total_profit=total_profit,
    )

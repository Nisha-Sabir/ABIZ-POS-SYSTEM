from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import UserRole
from app.schemas.sale import OfflineSaleCreate, OfflineSyncResult
from app.services.cart_service import clear_user_cart, get_user_cart_items
from app.services.digi_khata_service import update_daily_digi_khata


def get_sales(db: Session, skip: int = 0, limit: int = 100, current_user=None) -> list[Sale]:
    statement = select(Sale).order_by(Sale.created_at.desc(), Sale.id.desc())

    # Data isolation: admin sees only their own sales, super_admin sees all
    if current_user and current_user.role == UserRole.ADMIN:
        statement = statement.where(Sale.created_by_id == current_user.id)

    statement = statement.offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_sale_by_id(db: Session, sale_id: int) -> Sale | None:
    return db.get(Sale, sale_id)


def get_sale_by_client_sale_id(db: Session, client_sale_id: str) -> Sale | None:
    statement = select(Sale).where(Sale.client_sale_id == client_sale_id)
    return db.scalars(statement).first()


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
    sale = Sale(total_amount=total_amount, total_profit=total_profit, created_by_id=user_id)
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


def sync_offline_sales(db: Session, offline_sales: list[OfflineSaleCreate]) -> list[OfflineSyncResult]:
    results: list[OfflineSyncResult] = []

    for offline_sale in offline_sales:
        existing_sale = get_sale_by_client_sale_id(db, offline_sale.client_sale_id)
        if existing_sale:
            results.append(
                OfflineSyncResult(
                    client_sale_id=offline_sale.client_sale_id,
                    status="already_synced",
                    sale_id=existing_sale.id,
                )
            )
            continue

        if not offline_sale.items:
            results.append(
                OfflineSyncResult(
                    client_sale_id=offline_sale.client_sale_id,
                    status="failed",
                    message="Sale has no items.",
                )
            )
            continue

        products_by_id: dict[int, Product] = {}
        total_amount = Decimal("0.00")
        total_profit = Decimal("0.00")
        failed_message: str | None = None

        for item in offline_sale.items:
            product = db.get(Product, item.product_id)
            if product is None:
                failed_message = f"Product {item.product_id} not found."
                break
            if product.stock_quantity < item.quantity:
                failed_message = f"Insufficient stock for {product.name}."
                break

            products_by_id[item.product_id] = product
            unit_price = item.unit_price or product.sale_price
            total_amount += unit_price * item.quantity
            total_profit += (unit_price - product.purchase_price) * item.quantity

        if failed_message:
            results.append(
                OfflineSyncResult(
                    client_sale_id=offline_sale.client_sale_id,
                    status="failed",
                    message=failed_message,
                )
            )
            continue

        discount = max(Decimal("0.00"), offline_sale.discount or Decimal("0.00"))
        total_amount = max(Decimal("0.00"), total_amount - discount)
        total_profit = total_profit - discount

        sale = Sale(
            client_sale_id=offline_sale.client_sale_id,
            source="desktop_offline",
            total_amount=total_amount,
            total_profit=total_profit,
            created_at=offline_sale.created_at,
        )
        db.add(sale)
        db.flush()

        for item in offline_sale.items:
            product = products_by_id[item.product_id]
            unit_price = item.unit_price or product.sale_price
            item_profit = (unit_price - product.purchase_price) * item.quantity
            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    profit=item_profit,
                )
            )
            product.stock_quantity -= item.quantity

        update_daily_digi_khata(
            db=db,
            entry_date=offline_sale.created_at.date(),
            sale_amount=total_amount,
            profit_amount=total_profit,
        )
        db.commit()
        db.refresh(sale)
        results.append(
            OfflineSyncResult(
                client_sale_id=offline_sale.client_sale_id,
                status="synced",
                sale_id=sale.id,
            )
        )

    return results

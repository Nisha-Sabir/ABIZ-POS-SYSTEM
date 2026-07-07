from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import UserRole
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.qr_code import generate_product_qr_code


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_product_by_qr_code(db: Session, qr_code: str) -> Product | None:
    statement = select(Product).where(Product.qr_code == qr_code.strip())
    return db.scalars(statement).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    category_id: int | None = None,
    current_user=None,
) -> list[Product]:
    statement = select(Product).order_by(Product.created_at.desc(), Product.id.desc())

    # Data isolation: admin sees only their own products, super_admin sees all
    if current_user and current_user.role == UserRole.ADMIN:
        statement = statement.where(Product.owner_id == current_user.id)

    if search:
        statement = statement.where(Product.name.ilike(f"%{search.strip()}%"))

    if category_id is not None:
        statement = statement.where(Product.category_id == category_id)

    statement = statement.offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def create_product(db: Session, product_data: ProductCreate, owner_id: int | None = None) -> Product:
    product_values = product_data.model_dump()
    product_values["qr_code"] = product_values["qr_code"] or generate_unique_product_qr_code(db)
    product_values["owner_id"] = owner_id  # Assign owner for data isolation
    product = Product(**product_values)
    db.add(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(product)
    return product


def update_product(
    db: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:
    update_data = product_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(product)
    return product


def generate_unique_product_qr_code(db: Session) -> str:
    while True:
        qr_code = generate_product_qr_code()
        if get_product_by_qr_code(db, qr_code) is None:
            return qr_code


def assign_product_qr_code(db: Session, product: Product) -> Product:
    if not product.qr_code:
        product.qr_code = generate_unique_product_qr_code(db)
        db.commit()
        db.refresh(product)

    return product


def regenerate_product_qr_code(db: Session, product: Product) -> Product:
    product.qr_code = generate_unique_product_qr_code(db)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()

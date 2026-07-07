from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.qr import QRCodeResponse
from app.services.category_service import get_category_by_id
from app.services.product_service import (
    assign_product_qr_code,
    create_product,
    delete_product,
    get_product_by_id,
    get_product_by_qr_code,
    get_products,
    regenerate_product_qr_code,
    update_product,
)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_admin)],
)


def _validate_product_category(db: Session, category_id: int | None) -> None:
    if category_id is None:
        return

    if get_category_by_id(db, category_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )


def _validate_product_prices(
    purchase_price: Decimal | None,
    sale_price: Decimal | None,
) -> None:
    if purchase_price is None or sale_price is None:
        return

    if sale_price < purchase_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sale price must be greater than or equal to purchase price.",
        )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_new_product(
    product_data: ProductCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    if product_data.qr_code and get_product_by_qr_code(db, product_data.qr_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this QR code already exists.",
        )

    _validate_product_category(db, product_data.category_id)

    try:
        return create_product(db, product_data, owner_id=current_user.id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this QR code already exists.",
        )


@router.get("", response_model=list[ProductResponse])
def read_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[ProductResponse]:
    return get_products(
        db,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        current_user=current_user,
    )


@router.get("/qr/{qr_code}", response_model=ProductResponse)
def read_product_by_qr_code(
    qr_code: str,
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    product = get_product_by_qr_code(db, qr_code)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product


@router.get("/{product_id}", response_model=ProductResponse)
def read_product_by_id(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product


@router.post("/{product_id}/qr", response_model=QRCodeResponse)
def generate_product_qr(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> QRCodeResponse:
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    product = assign_product_qr_code(db, product)
    return QRCodeResponse(
        product_id=product.id,
        product_name=product.name,
        qr_code=product.qr_code,
    )


@router.post("/{product_id}/qr/regenerate", response_model=QRCodeResponse)
def regenerate_product_qr(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> QRCodeResponse:
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    product = regenerate_product_qr_code(db, product)
    return QRCodeResponse(
        product_id=product.id,
        product_name=product.name,
        qr_code=product.qr_code,
    )


@router.put("/{product_id}", response_model=ProductResponse)
def update_existing_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    if product_data.qr_code:
        existing_product = get_product_by_qr_code(db, product_data.qr_code)
        if existing_product and existing_product.id != product.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this QR code already exists.",
            )

    _validate_product_category(db, product_data.category_id)
    _validate_product_prices(
        product_data.purchase_price or product.purchase_price,
        product_data.sale_price or product.sale_price,
    )

    try:
        return update_product(db, product, product_data)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this QR code already exists.",
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    product = get_product_by_id(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    try:
        delete_product(db, product)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product cannot be deleted because it is linked to sales records.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

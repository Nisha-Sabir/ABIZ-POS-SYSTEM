from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.cart import CartItemRequest, CartResponse, ProductScanResponse
from app.schemas.sale import CheckoutResponse, SaleResponse
from app.services.cart_service import (
    add_product_to_cart,
    build_cart_response,
    get_cart_item,
    get_user_cart_items,
    remove_product_from_cart,
)
from app.services.product_service import get_product_by_qr_code
from app.services.sale_service import checkout_cart, get_sale_by_id, get_sales

router = APIRouter(prefix="/sales", tags=["Sales Foundation"])


@router.get("/scan/{qr_code}", response_model=ProductScanResponse)
def scan_product_by_qr(
    qr_code: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ProductScanResponse:
    product = get_product_by_qr_code(db, qr_code)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found for this QR code.",
        )

    return ProductScanResponse(
        product_id=product.id,
        name=product.name,
        qr_code=product.qr_code,
        sale_price=product.sale_price,
        available_stock=product.stock_quantity,
    )


@router.post("/cart/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    cart_data: CartItemRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CartResponse:
    product = get_product_by_qr_code(db, cart_data.qr_code)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found for this QR code.",
        )

    existing_cart_item = get_cart_item(db, current_user.id, product.id)
    existing_quantity = existing_cart_item.quantity if existing_cart_item else 0
    requested_quantity = existing_quantity + cart_data.quantity

    if product.stock_quantity < requested_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock available.",
        )

    add_product_to_cart(db, current_user.id, product, cart_data.quantity)
    return build_cart_response(current_user.id, get_user_cart_items(db, current_user.id))


@router.get("/cart", response_model=CartResponse)
def view_cart(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CartResponse:
    return build_cart_response(current_user.id, get_user_cart_items(db, current_user.id))


@router.delete("/cart/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_cart(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    removed = remove_product_from_cart(db, current_user.id, product_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/checkout", response_model=CheckoutResponse)
def checkout_current_cart(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CheckoutResponse:
    try:
        sale = checkout_cart(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return CheckoutResponse(sale=sale)


@router.get("", response_model=list[SaleResponse])
def read_sales(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[SaleResponse]:
    return get_sales(db, skip=skip, limit=limit)


@router.get("/{sale_id}", response_model=SaleResponse)
def read_sale_by_id(
    sale_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SaleResponse:
    sale = get_sale_by_id(db, sale_id)

    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    return sale

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.inventory import (
    InventoryHistoryResponse,
    InventoryResponse,
    StockInRequest,
    StockOutRequest,
)
from app.schemas.product import ProductResponse
from app.services.inventory_service import (
    add_stock,
    get_inventory_history,
    get_low_stock_products,
    get_product_stock,
    remove_stock,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _inventory_response(product_id: int, product_name: str, stock_quantity: int) -> InventoryResponse:
    return InventoryResponse(
        product_id=product_id,
        product_name=product_name,
        stock_quantity=stock_quantity,
    )


@router.post("/products/{product_id}/stock-in", response_model=InventoryResponse)
def stock_in(
    product_id: int,
    stock_data: StockInRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
) -> InventoryResponse:
    product = get_product_stock(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    add_stock(
        db=db,
        product=product,
        quantity=stock_data.quantity,
        notes=stock_data.notes,
        created_by=current_user.id,
    )
    return _inventory_response(product.id, product.name, product.stock_quantity)


@router.post("/products/{product_id}/stock-out", response_model=InventoryResponse)
def stock_out(
    product_id: int,
    stock_data: StockOutRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
) -> InventoryResponse:
    product = get_product_stock(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    if product.stock_quantity < stock_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock available.",
        )

    remove_stock(
        db=db,
        product=product,
        quantity=stock_data.quantity,
        notes=stock_data.notes,
        created_by=current_user.id,
    )
    return _inventory_response(product.id, product.name, product.stock_quantity)


@router.get("/products/{product_id}/stock", response_model=InventoryResponse)
def read_product_stock(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> InventoryResponse:
    product = get_product_stock(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return _inventory_response(product.id, product.name, product.stock_quantity)


@router.get("/history", response_model=list[InventoryHistoryResponse])
def read_inventory_history(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    product_id: Annotated[int | None, Query(gt=0)] = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[InventoryHistoryResponse]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be before or equal to end_date.",
        )

    return get_inventory_history(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/low-stock", response_model=list[ProductResponse])
def read_low_stock_products(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    threshold: Annotated[int, Query(ge=0)] = 10,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
) -> list[ProductResponse]:
    return get_low_stock_products(
        db=db,
        threshold=threshold,
        skip=skip,
        limit=limit,
        search=search,
    )

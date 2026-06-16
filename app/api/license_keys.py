from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.license_key import LicenseKeyAssign, LicenseKeyCreate, LicenseKeyResponse
from app.services.license_key_service import (
    assign_license_key,
    create_license_key,
    get_license_key_by_id,
    get_license_keys,
    revoke_license_key,
)

router = APIRouter(prefix="/license-keys", tags=["Super Admin License Keys"])


@router.post("", response_model=LicenseKeyResponse, status_code=status.HTTP_201_CREATED)
def create_new_license_key(
    payload: LicenseKeyCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_super_admin)],
) -> LicenseKeyResponse:
    return create_license_key(db, assigned_to=payload.assigned_to)


@router.get("", response_model=list[LicenseKeyResponse])
def read_license_keys(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_super_admin)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[LicenseKeyResponse]:
    return get_license_keys(db, skip=skip, limit=limit)


@router.post("/{license_id}/assign", response_model=LicenseKeyResponse)
def assign_existing_license_key(
    license_id: int,
    payload: LicenseKeyAssign,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_super_admin)],
) -> LicenseKeyResponse:
    license_key = get_license_key_by_id(db, license_id)

    if license_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License key not found.")

    return assign_license_key(db, license_key, payload.assigned_to)


@router.post("/{license_id}/revoke", response_model=LicenseKeyResponse)
def revoke_existing_license_key(
    license_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_super_admin)],
) -> LicenseKeyResponse:
    license_key = get_license_key_by_id(db, license_id)

    if license_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License key not found.")

    return revoke_license_key(db, license_key)

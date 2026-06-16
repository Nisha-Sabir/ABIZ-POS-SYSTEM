from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.digi_khata import DigiKhataResponse
from app.services.digi_khata_service import get_digi_khata_entries

router = APIRouter(prefix="/digi-khata", tags=["Digi Khata"])


@router.get("", response_model=list[DigiKhataResponse])
def read_digi_khata_entries(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[DigiKhataResponse]:
    return get_digi_khata_entries(db, skip=skip, limit=limit)

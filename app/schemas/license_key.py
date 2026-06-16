from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.license_key import LicenseStatus


class LicenseKeyCreate(BaseModel):
    assigned_to: str | None = Field(default=None, max_length=255)


class LicenseKeyAssign(BaseModel):
    assigned_to: str = Field(min_length=2, max_length=255)


class LicenseKeyResponse(BaseModel):
    id: int
    license_key: str
    status: LicenseStatus
    assigned_to: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

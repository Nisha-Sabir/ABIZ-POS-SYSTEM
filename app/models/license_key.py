from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"


class LicenseKey(Base):
    __tablename__ = "license_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    license_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[LicenseStatus] = mapped_column(
        SqlEnum(
            LicenseStatus,
            name="license_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=LicenseStatus.INACTIVE,
    )
    assigned_to: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

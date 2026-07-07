from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.license_key import LicenseKey, LicenseStatus


def generate_license_key_value() -> str:
    return f"ABIZ-{uuid4().hex[:4]}-{uuid4().hex[:4]}-{uuid4().hex[:4]}".upper()


def get_license_keys(db: Session, skip: int = 0, limit: int = 100) -> list[LicenseKey]:
    statement = select(LicenseKey).order_by(LicenseKey.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_license_key_by_id(db: Session, license_id: int) -> LicenseKey | None:
    return db.get(LicenseKey, license_id)


def get_license_key_by_value(db: Session, license_key_value: str) -> LicenseKey | None:
    statement = select(LicenseKey).where(LicenseKey.license_key == license_key_value)
    return db.scalar(statement)


def create_license_key(db: Session, assigned_to: str | None = None) -> LicenseKey:
    license_key = LicenseKey(
        license_key=generate_license_key_value(),
        status=LicenseStatus.ACTIVE,  # Auto-activate on creation
        assigned_to=assigned_to,
    )
    db.add(license_key)
    db.commit()
    db.refresh(license_key)
    return license_key


def assign_license_key(db: Session, license_key: LicenseKey, assigned_to: str) -> LicenseKey:
    license_key.assigned_to = assigned_to
    license_key.status = LicenseStatus.ACTIVE
    db.commit()
    db.refresh(license_key)
    return license_key


def revoke_license_key(db: Session, license_key: LicenseKey) -> LicenseKey:
    license_key.status = LicenseStatus.REVOKED
    db.commit()
    db.refresh(license_key)
    return license_key

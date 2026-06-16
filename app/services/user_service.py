from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalars(statement).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def users_exist(db: Session) -> bool:
    statement = select(func.count(User.id))
    return (db.scalar(statement) or 0) > 0


def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        full_name=user_data.full_name,
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def can_publicly_register_role(db: Session, role: UserRole) -> bool:
    if role == UserRole.ADMIN:
        return True

    return role == UserRole.SUPER_ADMIN and not users_exist(db)

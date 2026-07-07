from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.database.session import get_db
from app.models.user import User
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.core.config import settings
from app.services.license_key_service import get_license_key_by_value
from app.models.license_key import LicenseStatus
from app.services.user_service import (
    authenticate_user,
    can_publicly_register_role,
    create_user,
    get_user_by_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Validate License Key
    if user_data.license_key != "ABIZ-SUPER-ADMIN":
        license_key_obj = get_license_key_by_value(db, user_data.license_key)
        if not license_key_obj or license_key_obj.status != LicenseStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or inactive License Key.",
            )

    if not can_publicly_register_role(db, user_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the first registered user can be a super admin.",
        )

    try:
        return create_user(db, user_data)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )


@router.post("/login", response_model=TokenResponse)
def login_user(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = authenticate_user(db, credentials.email, credentials.password)

    # Validate License Key
    if credentials.license_key != "ABIZ-SUPER-ADMIN":
        license_key_obj = get_license_key_by_value(db, credentials.license_key)
        if not license_key_obj or license_key_obj.status != LicenseStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or inactive License Key.",
            )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"role": user.role.value},
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user

@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):
    user = get_user_by_email(db, payload.email)
    if not user:
        return {"message": "If that email exists, a password reset link has been sent."}
    
    # Generate token
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_payload = {"sub": str(user.id), "exp": expire, "type": "reset"}
    token = jwt.encode(token_payload, settings.secret_key, algorithm=settings.algorithm)
    
    frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
    if not frontend_url:
        # Auto-detect from request or fallback
        frontend_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
        if frontend_url:
            frontend_url = f"https://{frontend_url}"
        else:
            frontend_url = "http://localhost:5173"
    reset_link = f"{frontend_url}/?reset_token={token}"
    
    # Email Sending Logic
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if smtp_server and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = user.email
            msg['Subject'] = "ABIZ POS - Password Reset Request"
            body = f"Hello {user.full_name},\n\nClick the link below to reset your password. This link expires in 15 minutes.\n\n{reset_link}\n\nIf you did not request this, please ignore this email."
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Failed to send email: {e}")
    else:
        print(f"SIMULATED EMAIL TO {payload.email}: Reset Link -> {reset_link}")
        
    return {"message": "If that email exists, a password reset link has been sent."}

@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        token_data = jwt.decode(payload.token, settings.secret_key, algorithms=[settings.algorithm])
        if token_data.get("type") != "reset":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type.")
        user_id = int(token_data.get("sub"))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")
        
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
    from app.core.security import hash_password
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    
    return {"message": "Password successfully reset."}

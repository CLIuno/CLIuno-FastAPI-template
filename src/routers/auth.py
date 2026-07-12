
import secrets

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.config import settings
from src.dependencies.auth import CurrentUser, DbSession
from src.models.models import BlacklistedToken, Role, User
from src.schemas.schemas import (
    ChangePasswordRequest,
    CheckTokenRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OtpRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    UserCreate,
    VerifyEmailRequest,
)
from src.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password_timing_safe,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _success(message: str, data: dict | None = None):
    return {"status": "success", "message": message, "data": data}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: DbSession):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    if body.phone and db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(status_code=400, detail="Phone already exists")
    if len(body.password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters")

    # Default role is created on first use so a fresh install works out of the box
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        user_role = Role(name="user")
        db.add(user_role)
        db.commit()
        db.refresh(user_role)

    user = User(
        username=body.username,
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        hashed_password=hash_password(body.password),
        role_id=user_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    user.refresh_token = refresh_token
    db.commit()

    return _success(
        "User registered successfully",
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )


@router.post("/login")
def login(body: LoginRequest, db: DbSession):
    user = (
        db.query(User)
        .filter(
            (User.username == body.login) | (User.email == body.login),
            User.is_deleted == False,  # noqa: E712
        )
        .first()
    )

    if not verify_password_timing_safe(body.password, user.hashed_password if user else None):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    user.refresh_token = refresh_token
    db.commit()

    return _success(
        "Login successful",
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token": access_token,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )


@router.post("/logout")
def logout(
    current_user: CurrentUser,
    db: DbSession,
    token: str = Depends(oauth2_scheme),
):
    blacklisted = BlacklistedToken(token=token)
    db.add(blacklisted)
    current_user.refresh_token = None
    db.commit()
    return _success("Logged out successfully")


@router.post("/refresh-token")
def refresh_token(body: RefreshTokenRequest, db: DbSession):
    payload = decode_refresh_token(body.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not user or user.refresh_token != body.refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    user.refresh_token = new_refresh_token
    db.commit()

    return _success(
        "Token refreshed successfully",
        {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        },
    )


@router.post("/check-token")
def check_token(body: CheckTokenRequest, db: DbSession):
    payload = decode_access_token(body.token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    blacklisted = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == body.token).first()
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return _success(
        "Token is valid",
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        },
    )


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current_user: CurrentUser, db: DbSession):
    if not verify_password_timing_safe(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=400, detail="New password must be at least 6 characters")

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return _success("Password changed successfully")


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: DbSession):
    user = db.query(User).filter(User.email == body.email, User.is_deleted == False).first()  # noqa: E712
    if user:
        user.reset_token = secrets.token_urlsafe(32)
        db.commit()
        # In production, email the token; templates keep it local to the database.
    return _success("If the email exists, a reset link has been sent")


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: DbSession):
    user = db.query(User).filter(User.reset_token == body.token).first() if body.token else None
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user.hashed_password = hash_password(body.password)
    user.reset_token = None
    db.commit()
    return _success("Password has been reset successfully")


@router.post("/send-verify-email")
def send_verify_email(current_user: CurrentUser, db: DbSession):
    current_user.verify_token = secrets.token_urlsafe(32)
    db.commit()
    # In production, email the token; templates keep it local to the database.
    return _success("Verification email sent")


@router.post("/verify-email")
def verify_email(body: VerifyEmailRequest, db: DbSession):
    user = db.query(User).filter(User.verify_token == body.token).first() if body.token else None
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user.is_verified = True
    user.verify_token = None
    db.commit()
    return _success("Email verified successfully")


@router.post("/otp/generate")
def otp_generate(current_user: CurrentUser, db: DbSession):
    secret = pyotp.random_base32()
    current_user.otp_secret = secret
    current_user.is_otp_enabled = False
    db.commit()

    otpauth_url = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.username, issuer_name=settings.APP_NAME)
    return _success("OTP secret generated", {"secret": secret, "otpauth_url": otpauth_url})


@router.post("/otp/verify")
def otp_verify(body: OtpRequest, current_user: CurrentUser, db: DbSession):
    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="OTP is not set up")
    if not pyotp.TOTP(current_user.otp_secret).verify(body.otp, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    current_user.is_otp_enabled = True
    db.commit()
    return _success("OTP enabled successfully")


@router.post("/otp/validate")
def otp_validate(body: OtpRequest, current_user: CurrentUser):
    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="OTP is not set up")
    if not pyotp.TOTP(current_user.otp_secret).verify(body.otp, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    return _success("OTP is valid")


@router.post("/otp/disable")
def otp_disable(current_user: CurrentUser, db: DbSession):
    current_user.otp_secret = None
    current_user.is_otp_enabled = False
    db.commit()
    return _success("OTP disabled successfully")

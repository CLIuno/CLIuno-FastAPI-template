
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.dependencies.auth import CurrentUser, DbSession
from src.models.models import BlacklistedToken, Role, User
from src.schemas.schemas import (
    ChangePasswordRequest,
    CheckTokenRequest,
    LoginRequest,
    RefreshTokenRequest,
    UserCreate,
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

    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        raise HTTPException(status_code=500, detail="Default role not found")

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

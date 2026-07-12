from datetime import datetime

from pydantic import AliasChoices, BaseModel, EmailStr, Field


# --- Generic Response ---
class ApiResponse(BaseModel):
    status: str
    message: str
    data: dict | list | None = None


# --- Role ---
class RoleCreate(BaseModel):
    name: str


class RoleUpdate(BaseModel):
    name: str


class RoleOut(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- User ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None = None
    password: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class AdminUserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role_id: str | None = None


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    role_id: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserWithRole(UserOut):
    role: RoleOut


# --- Auth ---
class LoginRequest(BaseModel):
    # Frontends send `usernameOrEmail`; `login` is kept for API/test compatibility
    login: str = Field(validation_alias=AliasChoices("login", "usernameOrEmail"))
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    password: str
    token: str


class VerifyEmailRequest(BaseModel):
    token: str


class OtpRequest(BaseModel):
    otp: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CheckTokenRequest(BaseModel):
    token: str


# --- Post ---
class PostCreate(BaseModel):
    title: str
    content: str | None = None


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class PostOut(BaseModel):
    id: str
    title: str
    content: str | None = None
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentOut(BaseModel):
    id: str
    content: str
    user_id: str
    post_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostWithComments(PostOut):
    comments: list[CommentOut] = []
    user: UserOut | None = None


# --- Comment ---
class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


# --- Todo ---
class TodoCreate(BaseModel):
    title: str
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


class TodoOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    completed: bool
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Follow ---
class FollowOut(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: datetime

    model_config = {"from_attributes": True}

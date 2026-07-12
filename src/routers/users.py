from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from src.dependencies.auth import CurrentAdmin, CurrentUser, DbSession
from src.models.models import User
from src.schemas.schemas import AdminUserUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _success(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "role_id": user.role_id,
        "is_deleted": user.is_deleted,
        "created_at": str(user.created_at),
        "updated_at": str(user.updated_at),
    }


@router.get("/current")
def get_current_user(current_user: CurrentUser):
    return _success("Current user retrieved", {"user": _user_dict(current_user)})


@router.patch("/current")
def update_current_user(body: UserUpdate, current_user: CurrentUser, db: DbSession):
    if body.first_name is not None:
        current_user.first_name = body.first_name
    if body.last_name is not None:
        current_user.last_name = body.last_name
    if body.phone is not None:
        existing = db.query(User).filter(
            User.phone == body.phone, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Phone already in use")
        current_user.phone = body.phone
    db.commit()
    db.refresh(current_user)
    return _success("User updated successfully", {"user": _user_dict(current_user)})


@router.delete("/current")
def delete_current_user(current_user: CurrentUser, db: DbSession):
    current_user.is_deleted = True
    current_user.deleted_at = datetime.now(UTC)
    db.commit()
    return _success("Account deleted successfully")


@router.get("/username/{username}")
def get_by_username(username: str, db: DbSession):
    user = db.query(User).filter(User.username == username, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _success("User retrieved", {"user": _user_dict(user)})


@router.get("/{user_id}/posts")
def get_user_posts(user_id: str, current_user: CurrentUser, db: DbSession):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    posts = [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "user_id": p.user_id,
            "created_at": str(p.created_at),
            "updated_at": str(p.updated_at),
        }
        for p in user.posts
    ]
    return _success("User posts retrieved", {"posts": posts})


@router.get("/{user_id}/roles")
def get_user_roles(user_id: str, current_user: CurrentUser, db: DbSession):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = user.role
    return _success(
        "User role retrieved",
        {"role": {"id": role.id, "name": role.name} if role else None},
    )


@router.get("")
def list_users(current_user: CurrentUser, db: DbSession):
    # Any authenticated user may list users (the frontend users page relies on it)
    users = db.query(User).filter(User.is_deleted == False).all()  # noqa: E712
    return _success("Users retrieved", {"users": [_user_dict(u) for u in users]})


@router.get("/{user_id}")
def get_user(user_id: str, current_user: CurrentUser, db: DbSession):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _success("User retrieved", {"user": _user_dict(user)})


@router.patch("/{user_id}")
def admin_update_user(user_id: str, body: AdminUserUpdate, admin: CurrentAdmin, db: DbSession):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.phone is not None:
        user.phone = body.phone
    if body.role_id is not None:
        user.role_id = body.role_id
    db.commit()
    db.refresh(user)
    return _success("User updated successfully", {"user": _user_dict(user)})


@router.delete("/{user_id}")
def admin_delete_user(user_id: str, admin: CurrentAdmin, db: DbSession):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_deleted = True
    user.deleted_at = datetime.now(UTC)
    db.commit()
    return _success("User deleted successfully")

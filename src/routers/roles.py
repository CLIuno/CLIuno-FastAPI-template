from fastapi import APIRouter, HTTPException, status

from src.dependencies.auth import CurrentAdmin, DbSession
from src.models.models import Role, User

router = APIRouter(prefix="/roles", tags=["Roles"])


def _success(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


def _role_dict(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "created_at": str(role.created_at),
        "updated_at": str(role.updated_at),
    }


@router.get("")
def list_roles(admin: CurrentAdmin, db: DbSession):
    roles = db.query(Role).all()
    return _success("Roles retrieved", [_role_dict(r) for r in roles])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_role(body: dict, admin: CurrentAdmin, db: DbSession):
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if db.query(Role).filter(Role.name == name).first():
        raise HTTPException(status_code=400, detail="Role already exists")
    role = Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return _success("Role created successfully", _role_dict(role))


@router.get("/{role_id}")
def get_role(role_id: str, admin: CurrentAdmin, db: DbSession):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return _success("Role retrieved", _role_dict(role))


@router.patch("/{role_id}")
def update_role(role_id: str, body: dict, admin: CurrentAdmin, db: DbSession):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    name = body.get("name")
    if name:
        role.name = name
    db.commit()
    db.refresh(role)
    return _success("Role updated successfully", _role_dict(role))


@router.delete("/{role_id}")
def delete_role(role_id: str, admin: CurrentAdmin, db: DbSession):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return _success("Role deleted successfully")


@router.get("/{role_id}/users")
def get_role_users(role_id: str, admin: CurrentAdmin, db: DbSession):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    users = db.query(User).filter(User.role_id == role_id, User.is_deleted == False).all()  # noqa: E712
    return _success(
        "Role users retrieved",
        [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
            }
            for u in users
        ],
    )

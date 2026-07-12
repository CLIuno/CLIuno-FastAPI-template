from fastapi import APIRouter, HTTPException, status

from src.dependencies.auth import CurrentUser, DbSession
from src.models.models import Todo

router = APIRouter(prefix="/todos", tags=["Todos"])


def _success(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


def _todo_dict(todo: Todo) -> dict:
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "user_id": todo.user_id,
        "created_at": str(todo.created_at),
        "updated_at": str(todo.updated_at),
    }


@router.get("")
def list_todos(current_user: CurrentUser, db: DbSession):
    todos = db.query(Todo).all()
    return _success("Todos retrieved", [_todo_dict(t) for t in todos])


@router.get("/current-user")
def current_user_todos(current_user: CurrentUser, db: DbSession):
    todos = db.query(Todo).filter(Todo.user_id == current_user.id).all()
    return _success("User todos retrieved", [_todo_dict(t) for t in todos])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_todo(body: dict, current_user: CurrentUser, db: DbSession):
    title = body.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    todo = Todo(
        title=title,
        description=body.get("description"),
        user_id=current_user.id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return _success("Todo created successfully", _todo_dict(todo))


@router.get("/{todo_id}")
def get_todo(todo_id: str, current_user: CurrentUser, db: DbSession):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return _success("Todo retrieved", _todo_dict(todo))


@router.patch("/{todo_id}")
def update_todo(todo_id: str, body: dict, current_user: CurrentUser, db: DbSession):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if "title" in body:
        todo.title = body["title"]
    if "description" in body:
        todo.description = body["description"]
    if "completed" in body:
        todo.completed = body["completed"]
    db.commit()
    db.refresh(todo)
    return _success("Todo updated successfully", _todo_dict(todo))


@router.delete("/{todo_id}")
def delete_todo(todo_id: str, current_user: CurrentUser, db: DbSession):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(todo)
    db.commit()
    return _success("Todo deleted successfully")


@router.patch("/{todo_id}/toggle")
def toggle_todo(todo_id: str, current_user: CurrentUser, db: DbSession):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    todo.completed = not todo.completed
    db.commit()
    db.refresh(todo)
    return _success("Todo toggled successfully", _todo_dict(todo))

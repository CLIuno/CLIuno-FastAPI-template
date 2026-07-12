from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload

from src.dependencies.auth import CurrentUser, DbSession
from src.models.models import Post

router = APIRouter(prefix="/posts", tags=["Posts"])


def _success(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


def _post_dict(post: Post, include_user: bool = False, include_comments: bool = False) -> dict:
    d = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "user_id": post.user_id,
        "created_at": str(post.created_at),
        "updated_at": str(post.updated_at),
    }
    if include_comments:
        d["comments"] = [
            {
                "id": c.id,
                "content": c.content,
                "user_id": c.user_id,
                "post_id": c.post_id,
                "created_at": str(c.created_at),
                "updated_at": str(c.updated_at),
            }
            for c in post.comments
        ]
    if include_user:
        d["user"] = {
            "id": post.user.id,
            "username": post.user.username,
            "email": post.user.email,
            "first_name": post.user.first_name,
            "last_name": post.user.last_name,
        }
    return d


@router.get("")
def list_posts(db: DbSession):
    posts = db.query(Post).options(joinedload(Post.user),
                                   joinedload(Post.comments)).all()
    return _success("Posts retrieved", [_post_dict(p, include_user=True, include_comments=True) for p in posts])


@router.get("/current-user")
def current_user_posts(current_user: CurrentUser, db: DbSession):
    posts = db.query(Post).filter(Post.user_id == current_user.id).all()
    return _success("User posts retrieved", [_post_dict(p) for p in posts])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(body: dict, current_user: CurrentUser, db: DbSession):
    title = body.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    post = Post(title=title, content=body.get(
        "content"), user_id=current_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _success("Post created successfully", _post_dict(post))


@router.get("/{post_id}")
def get_post(post_id: str, db: DbSession):
    post = (
        db.query(Post)
        .options(joinedload(Post.user), joinedload(Post.comments))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _success("Post retrieved", _post_dict(post, include_user=True, include_comments=True))


@router.patch("/{post_id}")
def update_post(post_id: str, body: dict, current_user: CurrentUser, db: DbSession):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if "title" in body:
        post.title = body["title"]
    if "content" in body:
        post.content = body["content"]
    db.commit()
    db.refresh(post)
    return _success("Post updated successfully", _post_dict(post))


@router.delete("/{post_id}")
def delete_post(post_id: str, current_user: CurrentUser, db: DbSession):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(post)
    db.commit()
    return _success("Post deleted successfully")


@router.get("/{post_id}/user")
def get_post_author(post_id: str, db: DbSession):
    post = db.query(Post).options(joinedload(Post.user)
                                  ).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    user = post.user
    return _success(
        "Post author retrieved",
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    )

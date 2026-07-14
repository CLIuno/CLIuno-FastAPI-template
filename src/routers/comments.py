from fastapi import APIRouter, HTTPException, status

from src.dependencies.auth import CurrentUser, DbSession
from src.models.models import Comment, Post

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["Comments"])


def _success(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


def _comment_dict(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "created_at": str(comment.created_at),
        "updated_at": str(comment.updated_at),
    }


@router.get("")
def list_comments(post_id: str, db: DbSession):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return _success("Comments retrieved", {"comments": [_comment_dict(c) for c in comments]})


@router.post("", status_code=status.HTTP_201_CREATED)
def create_comment(post_id: str, body: dict, current_user: CurrentUser, db: DbSession):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    content = body.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    comment = Comment(content=content, user_id=current_user.id, post_id=post_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _success("Comment created successfully", {"comment": _comment_dict(comment)})


@router.patch("/{comment_id}")
def update_comment(
    post_id: str, comment_id: str, body: dict, current_user: CurrentUser, db: DbSession
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    content = body.get("content")
    if content:
        comment.content = content
    db.commit()
    db.refresh(comment)
    return _success("Comment updated successfully", {"comment": _comment_dict(comment)})


@router.delete("/{comment_id}")
def delete_comment(post_id: str, comment_id: str, current_user: CurrentUser, db: DbSession):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return _success("Comment deleted successfully")

from fastapi import APIRouter, HTTPException, status

from src.dependencies.auth import CurrentUser, DbSession
from src.models.models import Follow, User

router = APIRouter(prefix="/follows", tags=["Follows"])


def _success(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


@router.post("/{user_id}/follow", status_code=status.HTTP_201_CREATED)
def follow_user(user_id: str, current_user: CurrentUser, db: DbSession):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == current_user.id, Follow.following_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")

    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return _success("Followed successfully")


@router.delete("/{user_id}/follow")
def unfollow_user(user_id: str, current_user: CurrentUser, db: DbSession):
    follow = (
        db.query(Follow)
        .filter(Follow.follower_id == current_user.id, Follow.following_id == user_id)
        .first()
    )
    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")
    db.delete(follow)
    db.commit()
    return _success("Unfollowed successfully")


@router.get("/{user_id}/followers")
def get_followers(user_id: str, db: DbSession):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    followers = db.query(Follow).filter(Follow.following_id == user_id).all()
    follower_ids = [f.follower_id for f in followers]
    users = db.query(User).filter(User.id.in_(follower_ids)).all() if follower_ids else []
    return _success(
        "Followers retrieved",
        {
            "followers": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                }
                for u in users
            ]
        },
    )


@router.get("/{user_id}/following")
def get_following(user_id: str, db: DbSession):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    following = db.query(Follow).filter(Follow.follower_id == user_id).all()
    following_ids = [f.following_id for f in following]
    users = db.query(User).filter(User.id.in_(following_ids)).all() if following_ids else []
    return _success(
        "Following retrieved",
        {
            "following": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                }
                for u in users
            ]
        },
    )


@router.get("/{user_id}/is-following")
def is_following(user_id: str, current_user: CurrentUser, db: DbSession):
    follow = (
        db.query(Follow)
        .filter(Follow.follower_id == current_user.id, Follow.following_id == user_id)
        .first()
    )
    return _success("Follow status retrieved", {"isFollowing": follow is not None})

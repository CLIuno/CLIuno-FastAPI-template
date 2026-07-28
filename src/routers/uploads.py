import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from src.config import settings
from src.dependencies.auth import get_current_user
from src.models.models import User

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Uploaded files live at the repo root and are served statically from /uploads.
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

# 5 MB — matches every other CLIuno backend template.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# The extension comes from the detected mime, never from the client's filename.
ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    """Store the bytes and hand back a URL.

    Attaching it to a user or a post is the caller's job
    (PATCH /users/current, POST /posts) — upload mutates nothing.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds the 5 MB limit",
        )

    filename = f"{uuid.uuid4()}{ALLOWED_IMAGE_TYPES[file.content_type]}"
    (ensure_upload_dir() / filename).write_bytes(contents)

    # Absolute so a frontend on another origin can use it straight as an image source.
    base = (getattr(settings, "PUBLIC_BASE_URL", "") or str(request.base_url)).rstrip("/")
    return {
        "status": "success",
        "message": "Image uploaded",
        "data": {"url": f"{base}/uploads/{filename}", "filename": filename},
    }

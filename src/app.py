from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.database import Base, engine
from src.routers import auth, comments, follows, posts, roles, todos, uploads, users
from src.routers.uploads import ensure_upload_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(todos.router, prefix="/api/v1")
app.include_router(follows.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")

# Uploaded images are public and unversioned — no /api/v1 prefix.
app.mount("/uploads", StaticFiles(directory=ensure_upload_dir()), name="uploads")


@app.get("/up")
def health_check():
    return {"status": "ok"}

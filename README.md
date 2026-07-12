# CLIuno FastAPI Template

A production-ready FastAPI REST API template with JWT authentication, role-based access control, and CRUD operations.

## Features

- **FastAPI 0.135+** with automatic OpenAPI/Swagger docs
- **JWT Authentication** (access + refresh tokens) with token blacklisting
- **Role-Based Access Control** (admin/user roles)
- **SQLAlchemy 2.0** ORM with SQLite (swap to PostgreSQL/MySQL easily)
- **Argon2** password hashing via pwdlib
- **Pydantic v2** request/response validation
- **Soft Delete** for users
- **85 Tests** with pytest + httpx
- **Ruff** linting and formatting
- **Docker** ready

## Tech Stack

| Package | Version |
|---------|---------|
| FastAPI | 0.135+ |
| SQLAlchemy | 2.0+ |
| PyJWT | 2.10+ |
| pwdlib | 0.2+ (Argon2) |
| Pydantic | 2.0+ |
| Ruff | 0.9+ |
| pytest | 8.0+ |

## Getting Started

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Seed database
python -m src.seed

# Run server
uvicorn src.app:app --reload

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format src/ tests/
```

## API Endpoints

### Health
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/up` | - | Health check |

### Auth (`/api/v1/auth`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | - | Register new user |
| POST | `/login` | - | Login (username or email) |
| POST | `/logout` | Bearer | Logout (blacklists token) |
| POST | `/refresh-token` | - | Refresh access token |
| POST | `/check-token` | - | Validate a token |
| POST | `/change-password` | Bearer | Change password |

### Users (`/api/v1/users`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/current` | Bearer | Get current user |
| PATCH | `/current` | Bearer | Update current user |
| DELETE | `/current` | Bearer | Soft delete current user |
| GET | `/username/{username}` | - | Get user by username |
| GET | `/posts` | Bearer | Get current user's posts |
| GET | `/role` | Bearer | Get current user's role |
| GET | `/` | Admin | List all users |
| GET | `/{user_id}` | Admin | Get user by ID |
| PATCH | `/{user_id}` | Admin | Update user |
| DELETE | `/{user_id}` | Admin | Soft delete user |

### Roles (`/api/v1/roles`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Admin | List all roles |
| POST | `/` | Admin | Create role |
| GET | `/{role_id}` | Admin | Get role |
| PATCH | `/{role_id}` | Admin | Update role |
| DELETE | `/{role_id}` | Admin | Delete role |
| GET | `/{role_id}/users` | Admin | Get role's users |

### Posts (`/api/v1/posts`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | - | List all posts (with user & comments) |
| GET | `/current-user` | Bearer | Get current user's posts |
| POST | `/` | Bearer | Create post |
| GET | `/{post_id}` | - | Get post |
| PATCH | `/{post_id}` | Bearer | Update post (owner/admin) |
| DELETE | `/{post_id}` | Bearer | Delete post (owner/admin) |
| GET | `/{post_id}/user` | - | Get post author |

### Comments (`/api/v1/posts/{post_id}/comments`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | - | List comments |
| POST | `/` | Bearer | Create comment |
| PATCH | `/{comment_id}` | Bearer | Update comment (owner/admin) |
| DELETE | `/{comment_id}` | Bearer | Delete comment (owner/admin) |

### Todos (`/api/v1/todos`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Bearer | List all todos |
| GET | `/current-user` | Bearer | Get current user's todos |
| POST | `/` | Bearer | Create todo |
| GET | `/{todo_id}` | Bearer | Get todo |
| PATCH | `/{todo_id}` | Bearer | Update todo (owner/admin) |
| DELETE | `/{todo_id}` | Bearer | Delete todo (owner/admin) |
| PATCH | `/{todo_id}/toggle` | Bearer | Toggle todo completion |

### Follows (`/api/v1/follows`)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/{user_id}/follow` | Bearer | Follow user |
| DELETE | `/{user_id}/follow` | Bearer | Unfollow user |
| GET | `/{user_id}/followers` | - | Get user's followers |
| GET | `/{user_id}/following` | - | Get user's following |
| GET | `/{user_id}/is-following` | Bearer | Check if following |

## Project Structure

```
src/
├── app.py              # FastAPI app with lifespan, CORS, routers
├── config.py           # Settings via pydantic-settings
├── database.py         # SQLAlchemy engine, session, Base
├── seed.py             # Database seeder
├── models/
│   └── models.py       # SQLAlchemy models (7 entities)
├── schemas/
│   └── schemas.py      # Pydantic request/response schemas
├── services/
│   └── auth_service.py # JWT + Argon2 password utilities
├── dependencies/
│   └── auth.py         # Auth dependencies (current user, admin)
└── routers/
    ├── auth.py         # Auth endpoints
    ├── users.py        # User endpoints
    ├── roles.py        # Role endpoints (admin)
    ├── posts.py        # Post endpoints
    ├── comments.py     # Comment endpoints
    ├── todos.py        # Todo endpoints
    └── follows.py      # Follow endpoints
tests/
├── conftest.py         # Test fixtures, test DB
├── test_auth.py
├── test_users.py
├── test_roles.py
├── test_posts.py
├── test_comments.py
├── test_todos.py
└── test_follows.py
```

## Docker

```bash
docker build -t cliuno-fastapi .
docker run -p 8000:8000 cliuno-fastapi
```

## License

MIT

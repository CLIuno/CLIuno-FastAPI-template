# CLIuno FastAPI template

FastAPI + SQLAlchemy 2 (uv-managed) REST API serving the CLIuno contract: JWT auth
(refresh, reset, email verification, OTP via pyotp), users, todos, posts+comments,
follows, roles — under `/api/v1`.

## Commands

```bash
uv sync --extra dev            # install (uv.lock committed)
uv run fastapi dev src/app.py  # dev server (or: uv run uvicorn src.app:app)
uv run pytest                  # test suite — keep it green
uv run ruff check .            # lint (line-length 100)
```

If a foreign venv is active, `unset VIRTUAL_ENV` first. SQLite via `DATABASE_URL`
(default `sqlite:///./app.db`); tables are `create_all` on startup — **model changes need
a fresh db file** (delete `app.db`), tests use in-memory sqlite.

## Structure

`src/app.py` (routers + create_all) → `src/routers/` → `src/models/models.py`,
`src/schemas/schemas.py`, `src/dependencies/auth.py` (`CurrentUser`, `CurrentAdmin`,
`DbSession`), `src/services/auth_service.py` (JWT + hashing).

## Contract rules this codebase follows

- Responses: `_success(message, data)` → `{status, message, data}` with the exact keys
  frontends destructure (`data.users/user/todos/todo/posts/post/followers/following/`
  `isFollowing`; login/refresh include **both** `token` and `access_token`).
- Request compatibility via pydantic `AliasChoices`: `usernameOrEmail`|`login`,
  `refreshToken`|`refresh_token`, `oldPassword`|`current_password`, etc. Keep aliases
  when adding schemas.
- One-time tokens live on the user (`reset_token`, `verify_token`); lookups are by token.
- The `user` role is created on first registration (fresh clone needs no seeding).
- OTP endpoints act on `CurrentUser`; `GET /users` and `GET /users/:id` are CurrentUser,
  `PATCH/DELETE /users/:id` are CurrentAdmin.

## Conventions

Conventional commits; tests in `tests/` assert contract shapes — update together with
any envelope change; ruff must stay clean.

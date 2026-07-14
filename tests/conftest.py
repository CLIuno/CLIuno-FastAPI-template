import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.database import Base, get_db
from src.models.models import Role, User
from src.services.auth_service import create_access_token, hash_password

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_get_db(db):
    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def admin_role(db):
    role = Role(name="admin")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture()
def user_role(db):
    role = Role(name="user")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture()
def admin_user(db, admin_role):
    user = User(
        username="admin",
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        hashed_password=hash_password("password"),
        role_id=admin_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def regular_user(db, user_role):
    user = User(
        username="testuser",
        email="test@test.com",
        first_name="Test",
        last_name="User",
        hashed_password=hash_password("password"),
        role_id=user_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def second_user(db, user_role):
    user = User(
        username="testuser2",
        email="test2@test.com",
        first_name="Test2",
        last_name="User2",
        hashed_password=hash_password("password"),
        role_id=user_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def admin_token(admin_user):
    return create_access_token(data={"sub": admin_user.id})


@pytest.fixture()
def user_token(regular_user):
    return create_access_token(data={"sub": regular_user.id})


@pytest.fixture()
def second_user_token(second_user):
    return create_access_token(data={"sub": second_user.id})


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

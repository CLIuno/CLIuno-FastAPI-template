from src.database import Base, SessionLocal
from src.models.models import Role, User
from src.services.auth_service import hash_password


def seed():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        user_role = db.query(Role).filter(Role.name == "user").first()
        if not user_role:
            user_role = Role(name="user")
            db.add(user_role)
            db.commit()
            db.refresh(user_role)

        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                hashed_password=hash_password("password"),
                role_id=admin_role.id,
            )
            db.add(admin_user)
            db.commit()

        print("Database seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    from src.database import Base, engine

    Base.metadata.create_all(bind=engine)
    seed()

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

db = SessionLocal()

user = db.query(User).filter(User.username == "admin").first()

if user:
    print("L'utilisateur existe déjà.")
else:
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Administrateur",
        hashed_password=get_password_hash("Admin123@"),
        role=UserRole.ADMINISTRATEUR,
        is_active=True,
    )

    db.add(admin)
    db.commit()

    print("Super utilisateur créé avec succès.")

db.close()
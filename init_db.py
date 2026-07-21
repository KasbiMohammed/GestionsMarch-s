"""
Script d'initialisation de la base de données
Crée les tables et l'utilisateur administrateur par défaut
"""

from app.database import init_db, SessionLocal
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

def initialize_database():
    """Initialise la base de données avec l'utilisateur admin par défaut"""
    print("🔧 Initialisation de la base de données...")
    
    # Créer les tables
    init_db()
    print("✅ Tables créées avec succès")
    
    # Créer l'utilisateur admin par défaut
    db = SessionLocal()
    
    try:
        # Vérifier si l'admin existe déjà
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@commune.ma",
                full_name="Administrateur Système",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                department="Direction"
            )
            
            db.add(admin_user)
            db.commit()
            print("✅ Utilisateur administrateur créé (username: admin, password: admin123)")
            print("⚠️  N'oubliez pas de changer le mot de passe par défaut!")
        else:
            print("ℹ️  L'utilisateur administrateur existe déjà")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur admin: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("🎉 Initialisation terminée!")

if __name__ == "__main__":
    initialize_database()

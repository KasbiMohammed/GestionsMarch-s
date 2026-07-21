"""
Tests de l'API
Tests des endpoints REST
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.utils.security import get_password_hash


# Base de données de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dépendance de base de données pour les tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override de la dépendance
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    """Fixture de base de données pour les tests"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db):
    """Fixture utilisateur de test"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.ADMINISTRATEUR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestAuthAPI:
    """Tests de l'API d'authentification"""
    
    def test_login_success(self, test_user):
        """Test de connexion réussie"""
        response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test de connexion avec identifiants invalides"""
        response = client.post("/api/auth/login/json", json={
            "username": "invalid",
            "password": "invalid"
        })
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        """Test de connexion avec champs manquants"""
        response = client.post("/api/auth/login/json", json={
            "username": "testuser"
        })
        assert response.status_code == 422


class TestUsersAPI:
    """Tests de l'API des utilisateurs"""
    
    def test_get_users(self, test_user):
        """Test de récupération de la liste des utilisateurs"""
        # D'abord se connecter
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        # Récupérer les utilisateurs
        response = client.get("/api/users/", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_create_user(self, test_user):
        """Test de création d'utilisateur"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.post("/api/users/", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass",
                "role": "service_marches",
                "full_name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
    
    def test_get_user_by_id(self, test_user):
        """Test de récupération d'un utilisateur par ID"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(f"/api/users/{test_user.id}", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id


class TestMarketsAPI:
    """Tests de l'API des marchés"""
    
    def test_get_markets(self, test_user):
        """Test de récupération de la liste des marchés"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/api/markets/", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_market(self, test_user):
        """Test de création d'un marché"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.post("/api/markets/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "market_number": "TEST-001",
                "object": "Test Market",
                "owner": "Test Owner",
                "type": "travaux",
                "budget": 100000.0,
                "status": "en_attente"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["market_number"] == "TEST-001"


class TestDashboardAPI:
    """Tests de l'API du tableau de bord"""
    
    def test_get_statistics(self, test_user):
        """Test de récupération des statistiques"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/api/dashboard/statistics", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_markets" in data
    
    def test_get_kpis(self, test_user):
        """Test de récupération des KPIs"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/api/dashboard/kpis", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "market_kpis" in data


class TestStagesAPI:
    """Tests de l'API des étapes"""
    
    def test_get_stages(self, test_user):
        """Test de récupération des étapes"""
        login_response = client.post("/api/auth/login/json", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/api/stages/", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

"""
Tests des services
Tests de la logique métier
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User, UserRole
from app.models.market import Market, MarketStatus, MarketType
from app.models.stage import Stage, StageStatus
from app.services.market_service import MarketService
from app.services.stage_service import StageService
from app.services.notification_service import NotificationService
from app.utils.security import get_password_hash


# Base de données de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


@pytest.fixture(scope="function")
def test_market(db, test_user):
    """Fixture marché de test"""
    market = Market(
        market_number="TEST-001",
        object="Test Market",
        owner="Test Owner",
        type=MarketType.TRAVAUX,
        procurement_mode="Appel d'offres",
        budget=1000000.0,
        credits=1000000.0,
        status=MarketStatus.EN_ATTENTE,
        created_by=test_user.id
    )
    db.add(market)
    db.commit()
    db.refresh(market)
    return market


class TestMarketService:
    """Tests du service de marchés"""
    
    def test_create_market(self, db, test_user):
        """Test de création d'un marché"""
        service = MarketService(db)
        
        market_data = {
            "market_number": "TEST-002",
            "object": "Test Market 2",
            "owner": "Test Owner",
            "type": MarketType.FOURNITURES,
            "budget": 500000.0,
            "status": MarketStatus.EN_ATTENTE
        }
        
        market = service.create_market(market_data, test_user.id)
        
        assert market.market_number == "TEST-002"
        assert market.object == "Test Market 2"
        assert market.created_by == test_user.id
    
    def test_update_market(self, db, test_market, test_user):
        """Test de mise à jour d'un marché"""
        service = MarketService(db)
        
        updated_data = {
            "object": "Updated Market Object",
            "budget": 1500000.0
        }
        
        updated_market = service.update_market(test_market.id, updated_data, test_user.id)
        
        assert updated_market.object == "Updated Market Object"
        assert updated_market.budget == 1500000.0
    
    def test_delete_market(self, db, test_market, test_user):
        """Test de suppression d'un marché"""
        service = MarketService(db)
        
        result = service.delete_market(test_market.id, test_user.id)
        
        assert result is True
        assert test_market.is_deleted is True
    
    def test_get_market_statistics(self, db, test_market):
        """Test des statistiques de marchés"""
        service = MarketService(db)
        
        stats = service.get_market_statistics()
        
        assert "total_markets" in stats
        assert "by_status" in stats
        assert "total_budget" in stats


class TestStageService:
    """Tests du service d'étapes"""
    
    def test_create_stage(self, db, test_market, test_user):
        """Test de création d'une étape"""
        service = StageService(db)
        
        stage_data = {
            "market_id": test_market.id,
            "name": "Test Stage",
            "order": 1,
            "status": StageStatus.NOT_STARTED
        }
        
        stage = service.create_stage(stage_data, test_user.id)
        
        assert stage.name == "Test Stage"
        assert stage.market_id == test_market.id
    
    def test_initialize_standard_stages(self, db, test_market, test_user):
        """Test d'initialisation des étapes standard"""
        service = StageService(db)
        
        stages = service.initialize_standard_stages(test_market.id, test_user.id)
        
        assert len(stages) == 40  # 40 étapes standard
        assert all(s.market_id == test_market.id for s in stages)
    
    def test_update_stage_status(self, db, test_market, test_user):
        """Test de mise à jour du statut d'étape"""
        service = StageService(db)
        
        # Créer une étape
        stage_data = {
            "market_id": test_market.id,
            "name": "Test Stage",
            "order": 1,
            "status": StageStatus.NOT_STARTED
        }
        stage = service.create_stage(stage_data, test_user.id)
        
        # Mettre à jour le statut
        updated_stage = service.update_stage_status(
            stage.id, 
            StageStatus.COMPLETED, 
            test_user.id
        )
        
        assert updated_stage.status == StageStatus.COMPLETED
        assert updated_stage.progress_percentage == 100
    
    def test_get_stage_statistics(self, db, test_market):
        """Test des statistiques d'étapes"""
        service = StageService(db)
        
        # Initialiser les étapes standard
        service.initialize_standard_stages(test_market.id, 1)
        
        stats = service.get_stage_statistics(test_market.id)
        
        assert "total_stages" in stats
        assert "by_status" in stats
        assert stats["total_stages"] == 40


class TestNotificationService:
    """Tests du service de notifications"""
    
    def test_get_upcoming_deadlines(self, db, test_market, test_user):
        """Test de récupération des échéances à venir"""
        service = NotificationService(db)
        
        # Créer une étape avec une date proche
        from datetime import datetime, timedelta
        stage = Stage(
            market_id=test_market.id,
            name="Urgent Stage",
            order=1,
            status=StageStatus.NOT_STARTED,
            planned_date=datetime.now() + timedelta(days=3),
            created_by=test_user.id
        )
        db.add(stage)
        db.commit()
        
        deadlines = service.get_upcoming_deadlines(days_ahead=7)
        
        assert len(deadlines) >= 1
        assert any(d["title"] == "Échéance: Urgent Stage" for d in deadlines)
    
    def test_get_overdue_items(self, db, test_market, test_user):
        """Test de récupération des éléments en retard"""
        service = NotificationService(db)
        
        # Créer une étape en retard
        stage = Stage(
            market_id=test_market.id,
            name="Late Stage",
            order=1,
            status=StageStatus.IN_PROGRESS,
            planned_date=datetime.now() - timedelta(days=10),
            is_late=True,
            delay_days=10,
            created_by=test_user.id
        )
        db.add(stage)
        db.commit()
        
        overdue = service.get_overdue_items()
        
        assert len(overdue) >= 1
    
    def test_get_notification_summary(self, db):
        """Test du résumé des notifications"""
        service = NotificationService(db)
        
        summary = service.get_notification_summary()
        
        assert "upcoming_count" in summary
        assert "overdue_count" in summary
        assert "critical_count" in summary

"""
Script de peuplement de la base de données avec des données de test
Crée des utilisateurs, marchés et étapes exemples
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.market import Market, MarketStatus, MarketType
from app.models.stage import Stage, StageStatus
from app.models.annual_planning import Service
from app.services.stage_service import StageService
from app.services.auth_service import AuthService
from app.utils.security import get_password_hash


def seed_users(db: Session):
    """Crée des utilisateurs de test"""
    print("Création des utilisateurs...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@commune.ma',
            'password': 'admin123',
            'full_name': 'Administrateur Système',
            'role': UserRole.ADMINISTRATEUR,
            'phone': '+212600000001'
        },
        {
            'username': 'president',
            'email': 'president@commune.ma',
            'password': 'president123',
            'full_name': 'Mohammed Benali',
            'role': UserRole.PRESIDENT,
            'phone': '+212600000002'
        },
        {
            'username': 'directeur',
            'email': 'directeur@commune.ma',
            'password': 'directeur123',
            'full_name': 'Fatima Zahra',
            'role': UserRole.DIRECTEUR_GENERAL_SERVICES,
            'phone': '+212600000003'
        },
        {
            'username': 'marches',
            'email': 'marches@commune.ma',
            'password': 'marches123',
            'full_name': 'Ahmed El Fassi',
            'role': UserRole.SERVICE_MARCHES,
            'phone': '+212600000004'
        },
        {
            'username': 'technique',
            'email': 'technique@commune.ma',
            'password': 'technique123',
            'full_name': 'Karim Tazi',
            'role': UserRole.SERVICE_TECHNIQUE,
            'phone': '+212600000005'
        },
        {
            'username': 'financier',
            'email': 'financier@commune.ma',
            'password': 'financier123',
            'full_name': 'Samira Bensalem',
            'role': UserRole.SERVICE_FINANCIER,
            'phone': '+212600000006'
        },
        {
            'username': 'controle',
            'email': 'controle@commune.ma',
            'password': 'controle123',
            'full_name': 'Youssef Amrani',
            'role': UserRole.CONTROLE_INTERNE,
            'phone': '+212600000007'
        },
        {
            'username': 'consultation',
            'email': 'consultation@commune.ma',
            'password': 'consultation123',
            'full_name': 'Laila Mansouri',
            'role': UserRole.CONSULTATION,
            'phone': '+212600000008'
        }
    ]
    
    created_users = {}
    for user_data in users_data:
        # Vérifier si l'utilisateur existe déjà
        existing = db.query(User).filter(User.username == user_data['username']).first()
        if not existing:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                hashed_password=get_password_hash(user_data['password']),
                full_name=user_data['full_name'],
                role=user_data['role'],
                phone=user_data['phone'],
                is_active=True,
                created_at=datetime.now()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users[user_data['username']] = user
            print(f"  ✓ Utilisateur créé: {user_data['username']}")
        else:
            created_users[user_data['username']] = existing
            print(f"  - Utilisateur existe déjà: {user_data['username']}")
    
    return created_users


def seed_services(db: Session):
    """Crée les services de la commune"""
    print("\nCréation des services...")
    
    services_data = [
        {
            'code': 'SRV001',
            'name': 'مصلحة التعمير والممتلكات',
            'description': 'Service de l\'urbanisme et des propriétés'
        },
        {
            'code': 'SRV002',
            'name': 'مصلحة حفظ الصحة والبيئة والاشغال الجماعية',
            'description': 'Service de la santé, de l\'environnement et des travaux publics'
        },
        {
            'code': 'SRV003',
            'name': 'مصلحة الشؤون القانونية والمنازعات',
            'description': 'Service des affaires juridiques et des litiges'
        },
        {
            'code': 'SRV004',
            'name': 'رئيس مصلحة الموارد المالية',
            'description': 'Chef du service des ressources financières'
        },
        {
            'code': 'SRV005',
            'name': 'مصلحة دراسات الصفقات وتتبع الأشغال',
            'description': 'Service des études de marchés et du suivi des travaux'
        },
        {
            'code': 'SRV006',
            'name': 'رئيس مصلحة الميزانية والشؤون المالية',
            'description': 'Chef du service du budget et des affaires financières'
        },
        {
            'code': 'SRV007',
            'name': 'مصلحة تدبير الموارد البشرية وتقوية القدرات',
            'description': 'Service de la gestion des ressources humaines et du renforcement des capacités'
        },
        {
            'code': 'SRV008',
            'name': 'مصلحة الشؤون الاجتماعية والثقافية والرياضية وتدبير المرافق العمومية',
            'description': 'Service des affaires sociales, culturelles et sportives et de la gestion des équipements publics'
        },
        {
            'code': 'SRV009',
            'name': 'مصلحة الحالة المدنية وتصحيح الإمضاء والشرطة الإدارية والرخص الاقتصادية',
            'description': 'Service de l\'état civil, de la correction de signature, de la police administrative et des licences économiques'
        }
    ]
    
    created_services = []
    for service_data in services_data:
        # Vérifier si le service existe déjà
        existing = db.query(Service).filter(Service.code == service_data['code']).first()
        if not existing:
            service = Service(**service_data)
            db.add(service)
            db.commit()
            db.refresh(service)
            created_services.append(service)
            print(f"  ✓ Service créé: {service_data['code']} - {service_data['name']}")
        else:
            created_services.append(existing)
            print(f"  - Service existe déjà: {service_data['code']} - {service_data['name']}")
    
    return created_services


def seed_markets(db: Session, users: dict):
    """Crée des marchés de test"""
    print("\nCréation des marchés...")
    
    markets_data = [
        {
            'market_number': '2024-TRAVAUX-001',
            'object': 'Réhabilitation du centre culturel communal',
            'owner': 'Commune Urbaine de Casablanca',
            'type': MarketType.TRAVAUX,
            'procurement_mode': 'Appel d\'offres ouvert',
            'budget': 2500000.00,
            'credits': 2500000.00,
            'responsible_service': 'Service Technique',
            'followup_responsibles': 'Karim Tazi, Ahmed El Fassi',
            'awardee': 'BTP Maroc SARL',
            'estimated_amount': 2400000.00,
            'final_amount': 2385000.00,
            'duration': 180,
            'status': MarketStatus.EN_COURS,
            'start_date': datetime.now() - timedelta(days=60),
            'expected_end_date': datetime.now() + timedelta(days=120),
            'created_by': users['admin'].id
        },
        {
            'market_number': '2024-FOURNITURES-002',
            'object': 'Fourniture de matériel informatique pour l\'administration',
            'owner': 'Commune Urbaine de Casablanca',
            'type': MarketType.FOURNITURES,
            'procurement_mode': 'Appel d\'offres restreint',
            'budget': 500000.00,
            'credits': 500000.00,
            'responsible_service': 'Service Informatique',
            'followup_responsibles': 'Ahmed El Fassi',
            'awardee': 'Tech Solutions SA',
            'estimated_amount': 480000.00,
            'final_amount': 475000.00,
            'duration': 30,
            'status': MarketStatus.TERMINE,
            'start_date': datetime.now() - timedelta(days=90),
            'expected_end_date': datetime.now() - timedelta(days=60),
            'actual_end_date': datetime.now() - timedelta(days=58),
            'created_by': users['admin'].id
        },
        {
            'market_number': '2024-SERVICES-003',
            'object': 'Services de nettoyage des bâtiments communaux',
            'owner': 'Commune Urbaine de Casablanca',
            'type': MarketType.SERVICES,
            'procurement_mode': 'Consultation',
            'budget': 800000.00,
            'credits': 800000.00,
            'responsible_service': 'Service des Affaires Générales',
            'followup_responsibles': 'Fatima Zahra',
            'awardee': 'Propreté Express SARL',
            'estimated_amount': 750000.00,
            'final_amount': 745000.00,
            'duration': 365,
            'status': MarketStatus.EN_COURS,
            'start_date': datetime.now() - timedelta(days=30),
            'expected_end_date': datetime.now() + timedelta(days=335),
            'created_by': users['admin'].id
        },
        {
            'market_number': '2024-ETUDES-004',
            'object': 'Étude d\'aménagement du quartier Nouvelle Médina',
            'owner': 'Commune Urbaine de Casablanca',
            'type': MarketType.ETUDES,
            'procurement_mode': 'Appel d\'offres ouvert',
            'budget': 350000.00,
            'credits': 350000.00,
            'responsible_service': 'Service Urbanisme',
            'followup_responsibles': 'Karim Tazi',
            'awardee': 'Urbanisme Conseil SARL',
            'estimated_amount': 340000.00,
            'final_amount': None,
            'duration': 90,
            'status': MarketStatus.EN_ATTENTE,
            'start_date': None,
            'expected_end_date': None,
            'created_by': users['admin'].id
        },
        {
            'market_number': '2024-TRAVAUX-005',
            'object': 'Construction d\'une école primaire dans le quartier Sidi Moumen',
            'owner': 'Commune Urbaine de Casablanca',
            'type': MarketType.TRAVAUX,
            'procurement_mode': 'Appel d\'offres ouvert',
            'budget': 4500000.00,
            'credits': 4500000.00,
            'responsible_service': 'Service Technique',
            'followup_responsibles': 'Karim Tazi, Ahmed El Fassi',
            'awardee': 'Construction Modern SARL',
            'estimated_amount': 4400000.00,
            'final_amount': None,
            'duration': 365,
            'status': MarketStatus.EN_RETARD,
            'start_date': datetime.now() - timedelta(days=180),
            'expected_end_date': datetime.now() + timedelta(days=185),
            'created_by': users['admin'].id
        }
    ]
    
    created_markets = []
    for market_data in markets_data:
        # Vérifier si le marché existe déjà
        existing = db.query(Market).filter(
            Market.market_number == market_data['market_number']
        ).first()
        
        if not existing:
            market = Market(**market_data)
            market.created_at = datetime.now()
            db.add(market)
            db.commit()
            db.refresh(market)
            created_markets.append(market)
            print(f"  ✓ Marché créé: {market.market_number}")
        else:
            created_markets.append(existing)
            print(f"  - Marché existe déjà: {market.market_number}")
    
    return created_markets


def seed_stages(db: Session, markets: list, users: dict):
    """Crée les étapes standard pour les marchés"""
    print("\nCréation des étapes pour les marchés...")
    
    stage_service = StageService(db)
    
    for market in markets:
        # Vérifier si le marché a déjà des étapes
        existing_stages = db.query(Stage).filter(Stage.market_id == market.id).count()
        
        if existing_stages == 0:
            # Créer les 40 étapes standard
            stages = stage_service.initialize_standard_stages(
                market_id=market.id,
                created_by=users['admin'].id
            )
            
            # Simuler la progression pour certains marchés
            if market.status == MarketStatus.TERMINE:
                # Toutes les étapes terminées
                for stage in stages:
                    stage.status = StageStatus.COMPLETED
                    stage.progress_percentage = 100
                    stage.actual_date = stage.planned_date - timedelta(days=random.randint(1, 5)) if stage.planned_date else None
                    stage.updated_at = datetime.now()
                    stage.updated_by = users['admin'].id
                    stage.calculate_delay()
            
            elif market.status == MarketStatus.EN_COURS:
                # Progression partielle
                completed_count = int(len(stages) * 0.6)  # 60% complété
                for i, stage in enumerate(stages):
                    if i < completed_count:
                        stage.status = StageStatus.COMPLETED
                        stage.progress_percentage = 100
                        stage.actual_date = stage.planned_date - timedelta(days=random.randint(1, 5)) if stage.planned_date else None
                    elif i == completed_count:
                        stage.status = StageStatus.IN_PROGRESS
                        stage.progress_percentage = 50
                    else:
                        stage.status = StageStatus.NOT_STARTED
                        stage.progress_percentage = 0
                    
                    stage.updated_at = datetime.now()
                    stage.updated_by = users['admin'].id
                    stage.calculate_delay()
            
            elif market.status == MarketStatus.EN_RETARD:
                # Progression avec retards
                completed_count = int(len(stages) * 0.4)  # 40% complété
                for i, stage in enumerate(stages):
                    if i < completed_count:
                        stage.status = StageStatus.COMPLETED
                        stage.progress_percentage = 100
                        stage.actual_date = stage.planned_date + timedelta(days=random.randint(5, 15)) if stage.planned_date else None
                        stage.is_late = True
                        stage.delay_days = random.randint(5, 15)
                    elif i == completed_count:
                        stage.status = StageStatus.IN_PROGRESS
                        stage.progress_percentage = 30
                        stage.is_late = True
                        stage.delay_days = random.randint(10, 20)
                    else:
                        stage.status = StageStatus.NOT_STARTED
                        stage.progress_percentage = 0
                    
                    stage.updated_at = datetime.now()
                    stage.updated_by = users['admin'].id
            
            elif market.status == MarketStatus.EN_ATTENTE:
                # Quelques étapes commencées
                for i, stage in enumerate(stages):
                    if i < 5:
                        stage.status = StageStatus.COMPLETED
                        stage.progress_percentage = 100
                        stage.actual_date = stage.planned_date - timedelta(days=random.randint(1, 3)) if stage.planned_date else None
                    elif i == 5:
                        stage.status = StageStatus.WAITING
                        stage.progress_percentage = 20
                    else:
                        stage.status = StageStatus.NOT_STARTED
                        stage.progress_percentage = 0
                    
                    stage.updated_at = datetime.now()
                    stage.updated_by = users['admin'].id
            
            db.commit()
            print(f"  ✓ {len(stages)} étapes créées pour {market.market_number}")
        else:
            print(f"  - Étapes existent déjà pour {market.market_number}")


def main():
    """Fonction principale de peuplement"""
    print("=" * 60)
    print("Peuplement de la base de données avec des données de test")
    print("=" * 60)
    
    # Créer les tables
    print("\nInitialisation de la base de données...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables créées")
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Import random pour la simulation
        import random
        random.seed(42)  # Pour la reproductibilité
        
        # Peupler les utilisateurs
        users = seed_users(db)
        
        # Peupler les services
        services = seed_services(db)
        
        # Peupler les marchés
        markets = seed_markets(db, users)
        
        # Peupler les étapes
        seed_stages(db, markets, users)
        
        print("\n" + "=" * 60)
        print("Peuplement terminé avec succès !")
        print("=" * 60)
        print("\nUtilisateurs de test créés:")
        print("  - admin / admin123 (Administrateur)")
        print("  - president / president123 (Président)")
        print("  - directeur / directeur123 (Directeur des Services)")
        print("  - marches / marches123 (Service des Marchés)")
        print("  - technique / technique123 (Service Technique)")
        print("  - financier / financier123 (Service Financier)")
        print("  - controle / controle123 (Contrôle Interne)")
        print("  - consultation / consultation123 (Consultation)")
        
    except Exception as e:
        print(f"\nErreur lors du peuplement: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

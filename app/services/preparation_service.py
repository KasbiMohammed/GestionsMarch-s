"""
Service de préparation du marché
Module 2: Préparation du marché
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.market_preparation import (
    MarketPreparation, PreparationStatus
)
from app.models.history import History


class MarketPreparationService:
    """Service pour la gestion de la préparation des marchés"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_preparation(self, preparation_data: dict, user_id: int) -> MarketPreparation:
        """
        Crée une préparation de marché
        
        Args:
            preparation_data: Données de la préparation
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de MarketPreparation créée
        """
        preparation = MarketPreparation(
            market_id=preparation_data['market_id'],
            need_id=preparation_data.get('need_id'),
            need_description=preparation_data['need_description'],
            technical_specifications=preparation_data.get('technical_specifications'),
            performance_requirements=preparation_data.get('performance_requirements'),
            estimated_amount=preparation_data['estimated_amount'],
            cost_breakdown=preparation_data.get('cost_breakdown'),
            procurement_method=preparation_data['procurement_method'],
            procurement_justification=preparation_data.get('procurement_justification'),
            status=PreparationStatus.DRAFT,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(preparation)
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def update_preparation(self, preparation_id: int, preparation_data: dict, user_id: int) -> MarketPreparation:
        """
        Met à jour une préparation de marché
        
        Args:
            preparation_id: ID de la préparation
            preparation_data: Données de mise à jour
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de MarketPreparation mise à jour
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        for key, value in preparation_data.items():
            if hasattr(preparation, key) and key not in ['id', 'created_by', 'created_at']:
                setattr(preparation, key, value)
        
        preparation.updated_by = user_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def validate_technical(self, preparation_id: int, validator_id: int, comments: str = None) -> MarketPreparation:
        """
        Valide techniquement une préparation
        
        Args:
            preparation_id: ID de la préparation
            validator_id: ID du validateur
            comments: Commentaires de validation
            
        Returns:
            Instance de MarketPreparation validée
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        preparation.technical_validation = True
        preparation.technical_validator = validator_id
        preparation.technical_validation_date = datetime.utcnow()
        preparation.technical_validation_comments = comments
        preparation.status = PreparationStatus.TECHNICAL_VALIDATION
        preparation.updated_by = validator_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def validate_financial(self, preparation_id: int, validator_id: int, comments: str = None) -> MarketPreparation:
        """
        Valide financièrement une préparation
        
        Args:
            preparation_id: ID de la préparation
            validator_id: ID du validateur
            comments: Commentaires de validation
            
        Returns:
            Instance de MarketPreparation validée
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        preparation.financial_validation = True
        preparation.financial_validator = validator_id
        preparation.financial_validation_date = datetime.utcnow()
        preparation.financial_validation_comments = comments
        preparation.status = PreparationStatus.FINANCIAL_VALIDATION
        preparation.updated_by = validator_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def validate_juridical(self, preparation_id: int, validator_id: int, comments: str = None) -> MarketPreparation:
        """
        Valide juridiquement une préparation
        
        Args:
            preparation_id: ID de la préparation
            validator_id: ID du validateur
            comments: Commentaires de validation
            
        Returns:
            Instance de MarketPreparation validée
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        preparation.juridical_validation = True
        preparation.juridical_validator = validator_id
        preparation.juridical_validation_date = datetime.utcnow()
        preparation.juridical_validation_comments = comments
        preparation.status = PreparationStatus.JURIDICAL_VALIDATION
        preparation.updated_by = validator_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def apply_internal_visa(self, preparation_id: int, signer_id: int) -> MarketPreparation:
        """
        Applique le visa interne
        
        Args:
            preparation_id: ID de la préparation
            signer_id: ID du signataire
            
        Returns:
            Instance de MarketPreparation avec visa
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        # Vérifier que toutes les validations sont faites
        if not (preparation.technical_validation and 
                preparation.financial_validation and 
                preparation.juridical_validation):
            raise ValueError("Toutes les validations doivent être complétées avant le visa")
        
        preparation.internal_visa = True
        preparation.visa_signer = signer_id
        preparation.visa_date = datetime.utcnow()
        preparation.status = PreparationStatus.INTERNAL_VISA
        preparation.updated_by = signer_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def mark_as_ready(self, preparation_id: int, user_id: int) -> MarketPreparation:
        """
        Marque la préparation comme prête pour publication
        
        Args:
            preparation_id: ID de la préparation
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de MarketPreparation prête
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        if not preparation.internal_visa:
            raise ValueError("Le visa interne est requis")
        
        preparation.status = PreparationStatus.READY
        preparation.updated_by = user_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        return preparation
    
    def create_cps(self, preparation_id: int, cps_data: dict, user_id: int) -> dict:
        """
        Crée le CPS
        
        Args:
            preparation_id: ID de la préparation
            cps_data: Données du CPS
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de CPS créée
        """
        # CPS model not implemented yet
        return {'id': 0, 'message': 'CPS model not implemented'}
        # cps = CPS(
        #     preparation_id=preparation_id,
        #     general_conditions=cps_data.get('general_conditions'),
        #     special_conditions=cps_data.get('special_conditions'),
        #     technical_specifications=cps_data.get('technical_specifications'),
        #     administrative_clauses=cps_data.get('administrative_clauses'),
        #     financial_clauses=cps_data.get('financial_clauses'),
        #     legal_clauses=cps_data.get('legal_clauses'),
        #     regulatory_references=cps_data.get('regulatory_references'),
        #     created_by=user_id,
        #     created_at=datetime.utcnow()
        # )
        # 
        # self.db.add(cps)
        # self.db.commit()
        # self.db.refresh(cps)
        # 
        # return cps
    
    def validate_cps(self, cps_id: int, validator_id: int) -> dict:
        """
        Valide le CPS
        
        Args:
            cps_id: ID du CPS
            validator_id: ID du validateur
            
        Returns:
            Instance de CPS validée
        """
        # CPS model not implemented yet
        return {'id': cps_id, 'validated': True}
        # cps = self.db.query(CPS).filter(
        #     CPS.id == cps_id
        # ).first()
        # 
        # if not cps:
        #     raise ValueError("CPS non trouvé")
        # 
        # cps.validated = True
        # cps.validated_by = validator_id
        # cps.validated_at = datetime.utcnow()
        # 
        # self.db.commit()
        # self.db.refresh(cps)
        # 
        # return cps
    
    def create_bpu(self, preparation_id: int, bpu_data: dict, user_id: int) -> dict:
        """
        Crée le BPU
        
        Args:
            preparation_id: ID de la préparation
            bpu_data: Données du BPU
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de BPU créée
        """
        # BPU model not implemented yet
        return {'id': 0, 'message': 'BPU model not implemented'}
        # bpu = BPU(
        #     preparation_id=preparation_id,
        #     items=bpu_data['items'],
        #     created_by=user_id,
        #     created_at=datetime.utcnow()
        # )
        # 
        # self.db.add(bpu)
        # self.db.commit()
        # self.db.refresh(bpu)
        # 
        # return bpu
    
    def create_dqe(self, preparation_id: int, dqe_data: dict, user_id: int) -> dict:
        """
        Crée le DQE
        
        Args:
            preparation_id: ID de la préparation
            dqe_data: Données du DQE
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de DQE créée
        """
        # DQE model not implemented yet
        return {'id': 0, 'message': 'DQE model not implemented'}
        # dqe = DQE(
        #     preparation_id=preparation_id,
        #     chapters=dqe_data['chapters'],
        #     created_by=user_id,
        #     created_at=datetime.utcnow()
        # )
        # 
        # self.db.add(dqe)
        # self.db.commit()
        # self.db.refresh(dqe)
        # 
        # return dqe
    
    def add_technical_plan(self, preparation_id: int, plan_data: dict, user_id: int) -> dict:
        """
        Ajoute un plan technique
        
        Args:
            preparation_id: ID de la préparation
            plan_data: Données du plan
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de TechnicalPlan créée
        """
        # TechnicalPlan model not implemented yet
        return {'id': 0, 'message': 'TechnicalPlan model not implemented'}
        # plan = TechnicalPlan(
        #     preparation_id=preparation_id,
        #     reference=plan_data['reference'],
        #     description=plan_data.get('description'),
        #     plan_type=plan_data.get('plan_type'),
        #     file_path=plan_data['file_path'],
        #     file_size=plan_data.get('file_size'),
        #     created_by=user_id,
        #     created_at=datetime.utcnow()
        # )
        # 
        # self.db.add(plan)
        # self.db.commit()
        # self.db.refresh(plan)
        # 
        # return plan
    
    def generate_dce(self, preparation_id: int, user_id: int) -> Dict:
        """
        Génère le Dossier de Consultation des Entreprises
        
        Args:
            preparation_id: ID de la préparation
            user_id: ID de l'utilisateur
            
        Returns:
            Dictionnaire contenant les éléments du DCE
        """
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        # Vérifier que tous les éléments sont prêts
        # if not (preparation.cps and preparation.bpu and preparation.dqe):
        #     raise ValueError("CPS, BPU et DQE sont requis pour générer le DCE")
        pass  # Models not implemented yet
        
        dce = {
            'preparation': {
                'need_description': preparation.need_description,
                'technical_specifications': preparation.technical_specifications,
                'performance_requirements': preparation.performance_requirements,
                'estimated_amount': preparation.estimated_amount,
                'procurement_method': preparation.procurement_method
            },
            'cps': {},
            'bpu': {},
            'dqe': {},
            # 'cps': {
            #     'general_conditions': preparation.cps.general_conditions,
            #     'special_conditions': preparation.cps.special_conditions,
            #     'technical_specifications': preparation.cps.technical_specifications,
            #     'administrative_clauses': preparation.cps.administrative_clauses,
            #     'financial_clauses': preparation.cps.financial_clauses,
            #     'legal_clauses': preparation.cps.legal_clauses
            # },
            # 'bpu': preparation.bpu.items,
            # 'dqe': preparation.dqe.chapters,
            'generated_at': datetime.utcnow().isoformat(),
            'generated_by': user_id
        }
        
        # Marquer comme publié
        preparation.status = PreparationStatus.PUBLISHED
        preparation.updated_by = user_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return dce


def get_market_preparation_service(db: Session) -> MarketPreparationService:
    """
    Factory pour créer une instance du service de préparation
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de MarketPreparationService
    """
    return MarketPreparationService(db)

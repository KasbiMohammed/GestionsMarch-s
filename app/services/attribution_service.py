"""
Service d'attribution des marchés
Module 8: Attribution
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.attribution import (
    Attribution, Reclamation, AttributionStatus
)
from app.models.offer_management import Offer
from app.models.history import History


class AttributionService:
    """Service pour la gestion de l'attribution des marchés"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_provisional_attribution(self, attribution_data: dict, user_id: int) -> Attribution:
        """
        Crée une attribution provisoire
        
        Args:
            attribution_data: Données de l'attribution
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Attribution créée
        """
        attribution = Attribution(
            market_id=attribution_data['market_id'],
            offer_id=attribution_data['offer_id'],
            attributed_amount=attribution_data['attributed_amount'],
            currency=attribution_data.get('currency', 'MAD'),
            status=AttributionStatus.PROVISIONAL,
            provisional_decision_date=datetime.utcnow(),
            provisional_decision_by=user_id,
            provisional_pv_reference=attribution_data.get('provisional_pv_reference'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(attribution)
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def notify_attribution(self, attribution_id: int, notification_method: str, user_id: int) -> Attribution:
        """
        Notifie l'attribution
        
        Args:
            attribution_id: ID de l'attribution
            notification_method: Méthode de notification
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Attribution notifiée
        """
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if not attribution:
            raise ValueError("Attribution non trouvée")
        
        attribution.status = AttributionStatus.NOTIFIED
        attribution.notification_date = datetime.utcnow()
        attribution.notification_method = notification_method
        attribution.notification_reference = self._generate_notification_reference(attribution_id)
        
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def create_reclamation(self, attribution_id: int, reclamation_data: dict) -> Reclamation:
        """
        Crée une réclamation contre une attribution
        
        Args:
            attribution_id: ID de l'attribution
            reclamation_data: Données de la réclamation
            
        Returns:
            Instance de Reclamation créée
        """
        reclamation = Reclamation(
            attribution_id=attribution_id,
            claimant_id=reclamation_data['claimant_id'],
            reclamation_date=datetime.utcnow(),
            reclamation_type=reclamation_data.get('reclamation_type'),
            content=reclamation_data['content'],
            created_at=datetime.utcnow()
        )
        
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if attribution:
            attribution.has_reclamation = True
            attribution.reclamation_date = datetime.utcnow()
            attribution.status = AttributionStatus.RECLAMATION_PENDING
        
        self.db.add(reclamation)
        self.db.commit()
        self.db.refresh(reclamation)
        
        return reclamation
    
    def process_reclamation(self, reclamation_id: int, response: str, accepted: bool, user_id: int) -> Reclamation:
        """
        Traite une réclamation
        
        Args:
            reclamation_id: ID de la réclamation
            response: Réponse à la réclamation
            accepted: Si la réclamation est acceptée
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Reclamation traitée
        """
        reclamation = self.db.query(Reclamation).filter(
            Reclamation.id == reclamation_id
        ).first()
        
        if not reclamation:
            raise ValueError("Réclamation non trouvée")
        
        reclamation.processed = True
        reclamation.processed_by = user_id
        reclamation.processed_at = datetime.utcnow()
        reclamation.response = response
        reclamation.accepted = accepted
        reclamation.decision_date = datetime.utcnow()
        reclamation.decision_reference = self._generate_decision_reference(reclamation_id)
        
        attribution = reclamation.attribution
        if attribution:
            attribution.status = AttributionStatus.RECLAMATION_PROCESSED
            attribution.reclamation_response = response
            attribution.reclamation_response_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(reclamation)
        
        return reclamation
    
    def create_definitive_attribution(self, attribution_id: int, user_id: int) -> Attribution:
        """
        Crée l'attribution définitive
        
        Args:
            attribution_id: ID de l'attribution provisoire
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Attribution définitive
        """
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if not attribution:
            raise ValueError("Attribution non trouvée")
        
        if attribution.has_reclamation and not self._is_reclamation_resolved(attribution_id):
            raise ValueError("Les réclamations doivent être résolues avant l'attribution définitive")
        
        attribution.status = AttributionStatus.DEFINITIVE
        attribution.definitive_decision_date = datetime.utcnow()
        attribution.definitive_decision_by = user_id
        attribution.definitive_pv_reference = self._generate_pv_reference(attribution_id, 'définitif')
        
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def approve_attribution(self, attribution_id: int, user_id: int, approval_reference: str = None) -> Attribution:
        """
        Approuve une attribution
        
        Args:
            attribution_id: ID de l'attribution
            user_id: ID de l'approbateur
            approval_reference: Référence de l'approbation
            
        Returns:
            Instance de Attribution approuvée
        """
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if not attribution:
            raise ValueError("Attribution non trouvée")
        
        if attribution.status != AttributionStatus.DEFINITIVE:
            raise ValueError("L'attribution doit être définitive pour être approuvée")
        
        attribution.status = AttributionStatus.APPROVED
        attribution.approval_date = datetime.utcnow()
        attribution.approved_by = user_id
        attribution.approval_reference = approval_reference or self._generate_approval_reference(attribution_id)
        
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def apply_visa(self, attribution_id: int, user_id: int, visa_reference: str = None) -> Attribution:
        """
        Applique le visa à une attribution
        
        Args:
            attribution_id: ID de l'attribution
            user_id: ID du signataire
            visa_reference: Référence du visa
            
        Returns:
            Instance de Attribution avec visa
        """
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if not attribution:
            raise ValueError("Attribution non trouvée")
        
        if attribution.status != AttributionStatus.APPROVED:
            raise ValueError("L'attribution doit être approuvée pour recevoir le visa")
        
        attribution.status = AttributionStatus.VISA
        attribution.visa_date = datetime.utcnow()
        attribution.visa_by = user_id
        attribution.visa_reference = visa_reference or self._generate_visa_reference(attribution_id)
        
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def notify_awardee(self, attribution_id: int, notification_method: str, user_id: int) -> Attribution:
        """
        Notifie le titulaire du marché
        
        Args:
            attribution_id: ID de l'attribution
            notification_method: Méthode de notification
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Attribution notifiée
        """
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if not attribution:
            raise ValueError("Attribution non trouvée")
        
        attribution.awardee_notification_date = datetime.utcnow()
        attribution.awardee_notification_method = notification_method
        
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def cancel_attribution(self, attribution_id: int, reason: str, user_id: int) -> Attribution:
        """
        Annule une attribution
        
        Args:
            attribution_id: ID de l'attribution
            reason: Motif de l'annulation
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Attribution annulée
        """
        attribution = self.db.query(Attribution).filter(
            Attribution.id == attribution_id
        ).first()
        
        if not attribution:
            raise ValueError("Attribution non trouvée")
        
        attribution.status = AttributionStatus.CANCELLED
        attribution.observations = f"ANNULÉ: {reason}"
        attribution.updated_by = user_id
        attribution.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(attribution)
        
        return attribution
    
    def get_attribution_by_market(self, market_id: int) -> Optional[Attribution]:
        """
        Récupère l'attribution d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Instance de Attribution ou None
        """
        return self.db.query(Attribution).filter(
            Attribution.market_id == market_id
        ).first()
    
    def get_reclamations_by_attribution(self, attribution_id: int) -> List[Reclamation]:
        """
        Récupère les réclamations d'une attribution
        
        Args:
            attribution_id: ID de l'attribution
            
        Returns:
            Liste des réclamations
        """
        return self.db.query(Reclamation).filter(
            Reclamation.attribution_id == attribution_id
        ).all()
    
    def _is_reclamation_resolved(self, attribution_id: int) -> bool:
        """Vérifie si toutes les réclamations sont résolues"""
        reclamations = self.db.query(Reclamation).filter(
            Reclamation.attribution_id == attribution_id
        ).all()
        
        return all(r.processed for r in reclamations)
    
    def _generate_notification_reference(self, attribution_id: int) -> str:
        """Génère une référence de notification"""
        return f"NOTIF-{attribution_id}-{datetime.utcnow().strftime('%Y%m%d')}"
    
    def _generate_pv_reference(self, attribution_id: int, pv_type: str) -> str:
        """Génère une référence de PV"""
        return f"PV-{pv_type.upper()}-{attribution_id}-{datetime.utcnow().strftime('%Y%m%d')}"
    
    def _generate_decision_reference(self, reclamation_id: int) -> str:
        """Génère une référence de décision"""
        return f"DEC-{reclamation_id}-{datetime.utcnow().strftime('%Y%m%d')}"
    
    def _generate_approval_reference(self, attribution_id: int) -> str:
        """Génère une référence d'approbation"""
        return f"APPROV-{attribution_id}-{datetime.utcnow().strftime('%Y%m%d')}"
    
    def _generate_visa_reference(self, attribution_id: int) -> str:
        """Génère une référence de visa"""
        return f"VISA-{attribution_id}-{datetime.utcnow().strftime('%Y%m%d')}"


def get_attribution_service(db: Session) -> AttributionService:
    """
    Factory pour créer une instance du service d'attribution
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de AttributionService
    """
    return AttributionService(db)

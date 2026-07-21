"""
Service de gestion des commissions
Module 4: Gestion des commissions
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.commission import (
    Commission, CommissionMember, CommissionConvocation,
    CommissionType, CommissionStatus
)
from app.models.user import User
from app.models.history import History


class CommissionService:
    """Service pour la gestion des commissions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_commission(self, commission_data: dict, user_id: int) -> Commission:
        """
        Crée une nouvelle commission
        
        Args:
            commission_data: Données de la commission
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Commission créée
        """
        # Générer une référence
        reference = self._generate_reference(commission_data['commission_type'])
        
        commission = Commission(
            market_id=commission_data['market_id'],
            commission_type=commission_data['commission_type'],
            reference=reference,
            title=commission_data['title'],
            description=commission_data.get('description'),
            planned_date=commission_data['planned_date'],
            planned_time=commission_data.get('planned_time'),
            location=commission_data.get('location'),
            status=CommissionStatus.PLANNED,
            required_members=commission_data.get('required_members', 3),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(commission)
        self.db.commit()
        self.db.refresh(commission)
        
        return commission
    
    def add_member(self, commission_id: int, member_data: dict) -> CommissionMember:
        """
        Ajoute un membre à une commission
        
        Args:
            commission_id: ID de la commission
            member_data: Données du membre
            
        Returns:
            Instance de CommissionMember créée
        """
        member = CommissionMember(
            commission_id=commission_id,
            user_id=member_data['user_id'],
            role=member_data['role'],
            is_president=member_data.get('is_president', False),
            created_at=datetime.utcnow()
        )
        
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        
        return member
    
    def convocate_members(self, commission_id: int, user_id: int) -> List[CommissionConvocation]:
        """
        Envoie les convocations aux membres de la commission
        
        Args:
            commission_id: ID de la commission
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des convocations créées
        """
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        members = self.db.query(CommissionMember).filter(
            CommissionMember.commission_id == commission_id
        ).all()
        
        convocations = []
        for member in members:
            convocation = CommissionConvocation(
                commission_id=commission_id,
                member_id=member.id,
                sent_at=datetime.utcnow(),
                sent_by=user_id,
                sending_method='email'
            )
            
            self.db.add(convocation)
            convocations.append(convocation)
        
        commission.status = CommissionStatus.CONVOKED
        commission.updated_by = user_id
        commission.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return convocations
    
    def start_commission(self, commission_id: int, user_id: int) -> Commission:
        """
        Démarre une commission (marque comme en cours)
        
        Args:
            commission_id: ID de la commission
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Commission mise à jour
        """
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        commission.status = CommissionStatus.IN_PROGRESS
        commission.updated_by = user_id
        commission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(commission)
        
        return commission
    
    def record_attendance(self, commission_id: int, attendance_data: dict) -> Commission:
        """
        Enregistre la présence des membres
        
        Args:
            commission_id: ID de la commission
            attendance_data: Dictionnaire {member_id: attended}
            
        Returns:
            Instance de Commission mise à jour
        """
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        members = self.db.query(CommissionMember).filter(
            CommissionMember.commission_id == commission_id
        ).all()
        
        actual_members = 0
        for member in members:
            attended = attendance_data.get(member.id, False)
            member.attended = attended
            if attended:
                member.attendance_time = datetime.utcnow()
                actual_members += 1
        
        commission.actual_members = actual_members
        commission.quorum_reached = actual_members >= commission.required_members
        
        self.db.commit()
        self.db.refresh(commission)
        
        return commission
    
    def generate_pv(self, commission_id: int, pv_content: str, user_id: int) -> Commission:
        """
        Génère le procès-verbal de la commission
        
        Args:
            commission_id: ID de la commission
            pv_content: Contenu du PV
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Commission mise à jour
        """
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        commission.pv_content = pv_content
        commission.pv_generated = True
        commission.pv_generated_by = user_id
        commission.pv_generated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(commission)
        
        return commission
    
    def complete_commission(self, commission_id: int, user_id: int) -> Commission:
        """
        Termine une commission
        
        Args:
            commission_id: ID de la commission
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Commission terminée
        """
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        commission.status = CommissionStatus.COMPLETED
        commission.updated_by = user_id
        commission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(commission)
        
        return commission
    
    def cancel_commission(self, commission_id: int, user_id: int, reason: str) -> Commission:
        """
        Annule une commission
        
        Args:
            commission_id: ID de la commission
            user_id: ID de l'utilisateur
            reason: Motif de l'annulation
            
        Returns:
            Instance de Commission annulée
        """
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        commission.status = CommissionStatus.CANCELLED
        commission.description = f"ANNULÉ: {reason}"
        commission.updated_by = user_id
        commission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(commission)
        
        return commission
    
    def get_upcoming_commissions(self, days_ahead: int = 7) -> List[Commission]:
        """
        Récupère les commissions à venir dans les X jours
        
        Args:
            days_ahead: Nombre de jours à venir
            
        Returns:
            Liste des commissions à venir
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(Commission).filter(
            and_(
                Commission.planned_date >= datetime.utcnow(),
                Commission.planned_date <= cutoff_date,
                Commission.status.in_([CommissionStatus.PLANNED, CommissionStatus.CONVOKED])
            )
        ).order_by(Commission.planned_date).all()
    
    def get_commissions_by_market(self, market_id: int) -> List[Commission]:
        """
        Récupère toutes les commissions d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Liste des commissions
        """
        return self.db.query(Commission).filter(
            Commission.market_id == market_id
        ).order_by(Commission.planned_date).all()
    
    def _generate_reference(self, commission_type: CommissionType) -> str:
        """
        Génère une référence de commission
        
        Args:
            commission_type: Type de commission
            
        Returns:
            Référence générée
        """
        prefix = {
            CommissionType.OPENING: "CO",
            CommissionType.TECHNICAL: "CT",
            CommissionType.FINANCIAL: "CF",
            CommissionType.ATTRIBUTION: "CA",
            CommissionType.APPEL_OFFRES: "CAP"
        }
        
        year = datetime.utcnow().year
        count = self.db.query(Commission).filter(
            Commission.commission_type == commission_type
        ).count() + 1
        
        return f"{prefix.get(commission_type, 'COM')}-{year}-{count:04d}"


def get_commission_service(db: Session) -> CommissionService:
    """
    Factory pour créer une instance du service de commission
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de CommissionService
    """
    return CommissionService(db)

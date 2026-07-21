"""
Service d'exécution des marchés
Module 9: Exécution du marché
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.execution import (
    ServiceOrder, ExecutionPlan, Milestone, Attachment, Payment,
    Amendment, Guarantee, Penalty, Reception, ExecutionStatus
)
from app.models.history import History


class ExecutionService:
    """Service pour la gestion de l'exécution des marchés"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_service_order(self, order_data: dict, user_id: int) -> ServiceOrder:
        """
        Crée un ordre de service
        
        Args:
            order_data: Données de l'ordre de service
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de ServiceOrder créée
        """
        # Générer un numéro d'ordre
        order_number = self._generate_order_number(order_data['market_id'], order_data['order_type'])
        
        order = ServiceOrder(
            market_id=order_data['market_id'],
            order_number=order_number,
            order_type=order_data['order_type'],
            order_date=order_data['order_date'],
            description=order_data.get('description'),
            instructions=order_data.get('instructions'),
            effective_date=order_data.get('effective_date'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def create_execution_plan(self, plan_data: dict, user_id: int) -> ExecutionPlan:
        """
        Crée un plan d'exécution
        
        Args:
            plan_data: Données du plan d'exécution
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de ExecutionPlan créée
        """
        plan = ExecutionPlan(
            market_id=plan_data['market_id'],
            start_date=plan_data['start_date'],
            end_date=plan_data['end_date'],
            total_duration=plan_data['total_duration'],
            phases=plan_data.get('phases'),
            status=ExecutionStatus.NOT_STARTED,
            progress_percentage=0.0,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        
        return plan
    
    def add_milestone(self, execution_plan_id: int, milestone_data: dict) -> Milestone:
        """
        Ajoute un jalon à un plan d'exécution
        
        Args:
            execution_plan_id: ID du plan d'exécution
            milestone_data: Données du jalon
            
        Returns:
            Instance de Milestone créée
        """
        milestone = Milestone(
            execution_plan_id=execution_plan_id,
            name=milestone_data['name'],
            description=milestone_data.get('description'),
            planned_date=milestone_data['planned_date'],
            created_at=datetime.utcnow()
        )
        
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        
        return milestone
    
    def create_attachment(self, attachment_data: dict, user_id: int) -> Attachment:
        """
        Crée un attachement (constat d'avancement)
        
        Args:
            attachment_data: Données de l'attachement
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Attachment créée
        """
        attachment_number = self._generate_attachment_number(attachment_data['market_id'])
        
        attachment = Attachment(
            market_id=attachment_data['market_id'],
            attachment_number=attachment_number,
            attachment_date=attachment_data['attachment_date'],
            period_start=attachment_data['period_start'],
            period_end=attachment_data['period_end'],
            work_percentage=attachment_data['work_percentage'],
            amount=attachment_data['amount'],
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        
        return attachment
    
    def create_payment(self, payment_data: dict, user_id: int) -> Payment:
        """
        Crée un paiement
        
        Args:
            payment_data: Données du paiement
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Payment créée
        """
        payment_number = self._generate_payment_number(payment_data['market_id'])
        
        payment = Payment(
            market_id=payment_data['market_id'],
            attachment_id=payment_data.get('attachment_id'),
            payment_type=payment_data['payment_type'],
            payment_number=payment_number,
            amount=payment_data['amount'],
            currency=payment_data.get('currency', 'MAD'),
            payment_date=payment_data['payment_date'],
            due_date=payment_data.get('due_date'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def create_amendment(self, amendment_data: dict, user_id: int) -> Amendment:
        """
        Crée un avenant
        
        Args:
            amendment_data: Données de l'avenant
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Amendment créée
        """
        amendment_number = self._generate_amendment_number(amendment_data['market_id'])
        
        amendment = Amendment(
            market_id=amendment_data['market_id'],
            amendment_number=amendment_number,
            amendment_date=amendment_data['amendment_date'],
            amendment_type=amendment_data['amendment_type'],
            original_amount=amendment_data.get('original_amount'),
            new_amount=amendment_data.get('new_amount'),
            amount_difference=amendment_data.get('amount_difference'),
            original_duration=amendment_data.get('original_duration'),
            new_duration=amendment_data.get('new_duration'),
            duration_difference=amendment_data.get('duration_difference'),
            justification=amendment_data.get('justification'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(amendment)
        self.db.commit()
        self.db.refresh(amendment)
        
        return amendment
    
    def create_guarantee(self, guarantee_data: dict) -> Guarantee:
        """
        Crée une garantie/caution
        
        Args:
            guarantee_data: Données de la garantie
            
        Returns:
            Instance de Guarantee créée
        """
        guarantee = Guarantee(
            market_id=guarantee_data['market_id'],
            guarantee_type=guarantee_data['guarantee_type'],
            guarantee_number=guarantee_data['guarantee_number'],
            bank_name=guarantee_data['bank_name'],
            bank_reference=guarantee_data.get('bank_reference'),
            amount=guarantee_data['amount'],
            currency=guarantee_data.get('currency', 'MAD'),
            issue_date=guarantee_data['issue_date'],
            expiry_date=guarantee_data['expiry_date'],
            document_path=guarantee_data.get('document_path'),
            created_at=datetime.utcnow()
        )
        
        self.db.add(guarantee)
        self.db.commit()
        self.db.refresh(guarantee)
        
        return guarantee
    
    def create_penalty(self, penalty_data: dict, user_id: int) -> Penalty:
        """
        Crée une pénalité
        
        Args:
            penalty_data: Données de la pénalité
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Penalty créée
        """
        penalty_reference = self._generate_penalty_reference(penalty_data['market_id'])
        
        penalty = Penalty(
            market_id=penalty_data['market_id'],
            penalty_type=penalty_data['penalty_type'],
            penalty_reference=penalty_reference,
            amount=penalty_data['amount'],
            currency=penalty_data.get('currency', 'MAD'),
            reason=penalty_data['reason'],
            penalty_date=penalty_data['penalty_date'],
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(penalty)
        self.db.commit()
        self.db.refresh(penalty)
        
        return penalty
    
    def create_reception(self, reception_data: dict, user_id: int) -> Reception:
        """
        Crée une réception (provisoire ou définitive)
        
        Args:
            reception_data: Données de la réception
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Reception créée
        """
        reception_number = self._generate_reception_number(
            reception_data['market_id'], 
            reception_data['reception_type']
        )
        
        reception = Reception(
            market_id=reception_data['market_id'],
            reception_type=reception_data['reception_type'],
            reception_number=reception_number,
            reception_date=reception_data['reception_date'],
            has_reserves=reception_data.get('has_reserves', False),
            reserves=reception_data.get('reserves'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(reception)
        self.db.commit()
        self.db.refresh(reception)
        
        return reception
    
    def lift_reserves(self, reception_id: int, user_id: int) -> Reception:
        """
        Lève les réserves d'une réception
        
        Args:
            reception_id: ID de la réception
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Reception mise à jour
        """
        reception = self.db.query(Reception).filter(
            Reception.id == reception_id
        ).first()
        
        if not reception:
            raise ValueError("Réception non trouvée")
        
        reception.reserves_lifted = True
        reception.reserves_lifted_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(reception)
        
        return reception
    
    def get_expiring_guarantees(self, days_ahead: int = 30) -> List[Guarantee]:
        """
        Récupère les garanties qui expirent dans les X jours
        
        Args:
            days_ahead: Nombre de jours à venir
            
        Returns:
            Liste des garanties expirant bientôt
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        return self.db.query(Guarantee).filter(
            and_(
                Guarantee.active == True,
                Guarantee.expiry_date <= cutoff_date,
                Guarantee.expiry_date >= datetime.utcnow()
            )
        ).order_by(Guarantee.expiry_date).all()
    
    def get_execution_statistics(self, market_id: int) -> Dict:
        """
        Récupère les statistiques d'exécution d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire des statistiques
        """
        attachments = self.db.query(Attachment).filter(
            Attachment.market_id == market_id
        ).all()
        
        payments = self.db.query(Payment).filter(
            Payment.market_id == market_id
        ).all()
        
        amendments = self.db.query(Amendment).filter(
            Amendment.market_id == market_id
        ).all()
        
        penalties = self.db.query(Penalty).filter(
            Penalty.market_id == market_id
        ).all()
        
        total_paid = sum(p.amount for p in payments if p.paid)
        total_penalties = sum(p.amount for p in penalties if p.applied)
        
        return {
            'total_attachments': len(attachments),
            'total_payments': len(payments),
            'total_amendments': len(amendments),
            'total_penalties': len(penalties),
            'total_paid': total_paid,
            'total_penalties': total_penalties,
            'average_progress': sum(a.work_percentage for a in attachments) / len(attachments) if attachments else 0
        }
    
    def _generate_order_number(self, market_id: int, order_type: str) -> str:
        """Génère un numéro d'ordre de service"""
        prefix = {
            'démarrage': 'OS-D',
            'reprise': 'OS-R',
            'suspension': 'OS-S',
            'arrêt': 'OS-A'
        }.get(order_type, 'OS')
        
        count = self.db.query(ServiceOrder).filter(
            ServiceOrder.market_id == market_id
        ).count() + 1
        
        return f"{prefix}-{market_id}-{count:03d}"
    
    def _generate_attachment_number(self, market_id: int) -> str:
        """Génère un numéro d'attachement"""
        count = self.db.query(Attachment).filter(
            Attachment.market_id == market_id
        ).count() + 1
        
        return f"ATT-{market_id}-{count:03d}"
    
    def _generate_payment_number(self, market_id: int) -> str:
        """Génère un numéro de paiement"""
        count = self.db.query(Payment).filter(
            Payment.market_id == market_id
        ).count() + 1
        
        return f"PAY-{market_id}-{count:03d}"
    
    def _generate_amendment_number(self, market_id: int) -> str:
        """Génère un numéro d'avenant"""
        count = self.db.query(Amendment).filter(
            Amendment.market_id == market_id
        ).count() + 1
        
        return f"AV-{market_id}-{count:03d}"
    
    def _generate_penalty_reference(self, market_id: int) -> str:
        """Génère une référence de pénalité"""
        count = self.db.query(Penalty).filter(
            Penalty.market_id == market_id
        ).count() + 1
        
        return f"PEN-{market_id}-{count:03d}"
    
    def _generate_reception_number(self, market_id: int, reception_type: str) -> str:
        """Génère un numéro de réception"""
        prefix = 'RP' if reception_type == 'provisoire' else 'RD'
        count = self.db.query(Reception).filter(
            and_(
                Reception.market_id == market_id,
                Reception.reception_type == reception_type
            )
        ).count() + 1
        
        return f"{prefix}-{market_id}-{count:03d}"


def get_execution_service(db: Session) -> ExecutionService:
    """
    Factory pour créer une instance du service d'exécution
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de ExecutionService
    """
    return ExecutionService(db)

"""
Service de planification annuelle des achats
Module 1: Planification annuelle des achats
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.annual_planning import (
    AnnualPlanning, ServiceNeed, BudgetEstimate, Service,
    PlanningStatus, NeedPriority
)
from app.models.history import History


class AnnualPlanningService:
    """Service pour la gestion de la planification annuelle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_planning(self, planning_data: dict, user_id: int) -> AnnualPlanning:
        """
        Crée un programme prévisionnel annuel
        
        Args:
            planning_data: Données de la planification
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de AnnualPlanning créée
        """
        planning = AnnualPlanning(
            year=planning_data['year'],
            service_id=planning_data.get('service_id'),
            title=planning_data['title'],
            description=planning_data.get('description'),
            total_budget=planning_data.get('total_budget', 0.0),
            allocated_budget=planning_data.get('allocated_budget', 0.0),
            status=PlanningStatus.DRAFT,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(planning)
        self.db.commit()
        self.db.refresh(planning)
        
        # Enregistrer dans l'historique
        self._log_history(
            market_id=None,
            action="Création planification annuelle",
            description=f"Création du programme prévisionnel {planning.title} pour l'année {planning.year}",
            user_id=user_id
        )
        
        return planning
    
    def add_need(self, planning_id: int, need_data: dict, user_id: int) -> ServiceNeed:
        """
        Ajoute un besoin à une planification
        
        Args:
            planning_id: ID de la planification
            need_data: Données du besoin
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de ServiceNeed créée
        """
        need = ServiceNeed(
            planning_id=planning_id,
            service_id=need_data['service_id'],
            title=need_data['title'],
            description=need_data.get('description'),
            priority=need_data.get('priority', NeedPriority.MEDIUM),
            estimated_amount=need_data['estimated_amount'],
            estimated_duration=need_data.get('estimated_duration'),
            currency=need_data.get('currency', 'MAD'),
            market_type=need_data.get('market_type'),
            market_nature=need_data.get('market_nature'),
            planned_start_date=need_data.get('planned_start_date'),
            planned_end_date=need_data.get('planned_end_date'),
            planned_publication_date=need_data.get('planned_publication_date'),
            budget_code=need_data.get('budget_code'),
            credit_line=need_data.get('credit_line'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(need)
        self.db.commit()
        self.db.refresh(need)
        
        # Mettre à jour le budget total de la planification
        self._update_planning_budget(planning_id)
        
        return need
    
    def add_budget_estimate(self, need_id: int, estimate_data: dict, user_id: int) -> BudgetEstimate:
        """
        Ajoute une estimation budgétaire à un besoin
        
        Args:
            need_id: ID du besoin
            estimate_data: Données de l'estimation
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de BudgetEstimate créée
        """
        estimate = BudgetEstimate(
            need_id=need_id,
            category=estimate_data['category'],
            description=estimate_data.get('description'),
            quantity=estimate_data['quantity'],
            unit_price=estimate_data['unit_price'],
            total_amount=estimate_data['quantity'] * estimate_data['unit_price'],
            justification=estimate_data.get('justification'),
            reference=estimate_data.get('reference'),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(estimate)
        self.db.commit()
        self.db.refresh(estimate)
        
        return estimate
    
    def submit_planning(self, planning_id: int, user_id: int) -> AnnualPlanning:
        """
        Soumet une planification pour validation
        
        Args:
            planning_id: ID de la planification
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de AnnualPlanning mise à jour
        """
        planning = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise ValueError("Planification non trouvée")
        
        planning.status = PlanningStatus.SUBMITTED
        planning.submitted_by = user_id
        planning.submitted_at = datetime.utcnow()
        planning.updated_by = user_id
        planning.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(planning)
        
        return planning
    
    def validate_planning(self, planning_id: int, user_id: int, observations: str = None) -> AnnualPlanning:
        """
        Valide une planification
        
        Args:
            planning_id: ID de la planification
            user_id: ID du validateur
            observations: Observations optionnelles
            
        Returns:
            Instance de AnnualPlanning validée
        """
        planning = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise ValueError("Planification non trouvée")
        
        planning.status = PlanningStatus.VALIDATED
        planning.validated_by = user_id
        planning.validated_at = datetime.utcnow()
        planning.observations = observations
        planning.updated_by = user_id
        planning.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(planning)
        
        return planning
    
    def approve_planning(self, planning_id: int, user_id: int) -> AnnualPlanning:
        """
        Approuve une planification
        
        Args:
            planning_id: ID de la planification
            user_id: ID de l'approbateur
            
        Returns:
            Instance de AnnualPlanning approuvée
        """
        planning = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise ValueError("Planification non trouvée")
        
        planning.status = PlanningStatus.APPROVED
        planning.approved_by = user_id
        planning.approved_at = datetime.utcnow()
        planning.updated_by = user_id
        planning.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(planning)
        
        return planning
    
    def reject_planning(self, planning_id: int, user_id: int, reason: str) -> AnnualPlanning:
        """
        Rejette une planification
        
        Args:
            planning_id: ID de la planification
            user_id: ID de l'utilisateur
            reason: Motif du rejet
            
        Returns:
            Instance de AnnualPlanning rejetée
        """
        planning = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise ValueError("Planification non trouvée")
        
        planning.status = PlanningStatus.REJECTED
        planning.rejection_reason = reason
        planning.updated_by = user_id
        planning.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(planning)
        
        return planning
    
    def get_planning_statistics(self, year: int) -> Dict:
        """
        Récupère les statistiques de planification pour une année
        
        Args:
            year: Année
            
        Returns:
            Dictionnaire des statistiques
        """
        plannings = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.year == year
        ).all()
        
        total_budget = sum(p.total_budget for p in plannings)
        allocated_budget = sum(p.allocated_budget for p in plannings)
        consumed_budget = sum(p.consumed_budget for p in plannings)
        
        needs = self.db.query(ServiceNeed).join(AnnualPlanning).filter(
            AnnualPlanning.year == year
        ).all()
        
        total_needs = len(needs)
        realized_needs = len([n for n in needs if n.is_realized])
        
        return {
            'total_plannings': len(plannings),
            'total_budget': total_budget,
            'allocated_budget': allocated_budget,
            'consumed_budget': consumed_budget,
            'remaining_budget': total_budget - consumed_budget,
            'total_needs': total_needs,
            'realized_needs': realized_needs,
            'realization_rate': (realized_needs / total_needs * 100) if total_needs > 0 else 0,
            'by_status': self._count_by_status(plannings),
            'by_service': self._count_by_service(year)
        }
    
    def get_planning_by_service(self, service_id: int, year: int) -> Optional[AnnualPlanning]:
        """
        Récupère la planification d'un service pour une année
        
        Args:
            service_id: ID du service
            year: Année
            
        Returns:
            Instance de AnnualPlanning ou None
        """
        return self.db.query(AnnualPlanning).filter(
            and_(
                AnnualPlanning.service_id == service_id,
                AnnualPlanning.year == year
            )
        ).first()
    
    def _update_planning_budget(self, planning_id: int):
        """Met à jour le budget total d'une planification"""
        needs = self.db.query(ServiceNeed).filter(
            ServiceNeed.planning_id == planning_id
        ).all()
        
        total_budget = sum(n.estimated_amount for n in needs)
        
        planning = self.db.query(AnnualPlanning).filter(
            AnnualPlanning.id == planning_id
        ).first()
        
        if planning:
            planning.total_budget = total_budget
            self.db.commit()
    
    def _count_by_status(self, plannings: List[AnnualPlanning]) -> Dict:
        """Compte les planifications par statut"""
        status_count = {}
        for planning in plannings:
            status = planning.status.value if planning.status else 'unknown'
            status_count[status] = status_count.get(status, 0) + 1
        return status_count
    
    def _count_by_service(self, year: int) -> Dict:
        """Compte les planifications par service"""
        results = self.db.query(
            Service.name,
            func.count(AnnualPlanning.id)
        ).join(
            AnnualPlanning, Service.id == AnnualPlanning.service_id
        ).filter(
            AnnualPlanning.year == year
        ).group_by(Service.name).all()
        
        return {name: count for name, count in results}
    
    def _log_history(self, market_id: Optional[int], action: str, description: str, user_id: int):
        """Enregistre une action dans l'historique"""
        history = History(
            market_id=market_id,
            action=action,
            description=description,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()


def get_annual_planning_service(db: Session) -> AnnualPlanningService:
    """
    Factory pour créer une instance du service de planification annuelle
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de AnnualPlanningService
    """
    return AnnualPlanningService(db)

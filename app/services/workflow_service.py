"""
Service de workflow complet
Module 15: Workflow complet
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.workflow import (
    Workflow, WorkflowStepExecution, WorkflowTransition,
    WorkflowStep, WorkflowStatus
)
from app.models.history import History


class WorkflowService:
    """Service pour la gestion du workflow complet"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Ordre des étapes du workflow
    WORKFLOW_STEPS = [
        WorkflowStep.PLANNING,
        WorkflowStep.BUDGET_VALIDATION,
        WorkflowStep.TECHNICAL_STUDIES,
        WorkflowStep.DCE_PREPARATION,
        WorkflowStep.VALIDATION,
        WorkflowStep.PMMP_PUBLICATION,
        WorkflowStep.OFFER_RECEPTION,
        WorkflowStep.BID_OPENING,
        WorkflowStep.ANALYSIS,
        WorkflowStep.RANKING,
        WorkflowStep.COMMISSION,
        WorkflowStep.ATTRIBUTION,
        WorkflowStep.NOTIFICATION,
        WorkflowStep.SERVICE_ORDER,
        WorkflowStep.EXECUTION,
        WorkflowStep.PAYMENTS,
        WorkflowStep.PROVISIONAL_RECEPTION,
        WorkflowStep.RESERVE_LIFTING,
        WorkflowStep.DEFINITIVE_RECEPTION,
        WorkflowStep.ARCHIVING
    ]
    
    def create_workflow(self, market_id: int, workflow_name: str, user_id: int) -> Workflow:
        """
        Crée un workflow pour un marché
        
        Args:
            market_id: ID du marché
            workflow_name: Nom du workflow
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Workflow créée
        """
        workflow = Workflow(
            market_id=market_id,
            workflow_name=workflow_name,
            description="Workflow standard de marché public",
            status=WorkflowStatus.PENDING,
            current_step=WorkflowStep.PLANNING,
            progress_percentage=0.0,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        
        # Créer les étapes du workflow
        self._create_workflow_steps(workflow.id, user_id)
        
        return workflow
    
    def _create_workflow_steps(self, workflow_id: int, user_id: int) -> List[WorkflowStepExecution]:
        """
        Crée toutes les étapes du workflow
        
        Args:
            workflow_id: ID du workflow
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des étapes créées
        """
        steps = []
        for order, step in enumerate(self.WORKFLOW_STEPS):
            step_execution = WorkflowStepExecution(
                workflow_id=workflow_id,
                step=step,
                step_order=order,
                status=WorkflowStatus.PENDING,
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(step_execution)
            steps.append(step_execution)
        
        self.db.commit()
        return steps
    
    def start_workflow(self, workflow_id: int, user_id: int) -> Workflow:
        """
        Démarre un workflow
        
        Args:
            workflow_id: ID du workflow
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Workflow démarrée
        """
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        workflow.status = WorkflowStatus.IN_PROGRESS
        workflow.started_at = datetime.utcnow()
        workflow.current_step = WorkflowStep.PLANNING
        workflow.updated_by = user_id
        workflow.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(workflow)
        
        # Démarrer la première étape
        self._start_step(workflow_id, WorkflowStep.PLANNING, user_id)
        
        return workflow
    
    def start_step(self, workflow_id: int, step: WorkflowStep, user_id: int) -> WorkflowStepExecution:
        """
        Démarre une étape du workflow
        
        Args:
            workflow_id: ID du workflow
            step: Étape à démarrer
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de WorkflowStepExecution démarrée
        """
        return self._start_step(workflow_id, step, user_id)
    
    def _start_step(self, workflow_id: int, step: WorkflowStep, user_id: int) -> WorkflowStepExecution:
        """Méthode interne pour démarrer une étape"""
        step_execution = self.db.query(WorkflowStepExecution).filter(
            and_(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.step == step
            )
        ).first()
        
        if not step_execution:
            raise ValueError("Étape non trouvée")
        
        step_execution.status = WorkflowStatus.IN_PROGRESS
        step_execution.started_at = datetime.utcnow()
        step_execution.updated_by = user_id
        step_execution.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(step_execution)
        
        return step_execution
    
    def complete_step(self, workflow_id: int, step: WorkflowStep, result: dict = None, notes: str = None, user_id: int = None) -> WorkflowStepExecution:
        """
        Termine une étape du workflow
        
        Args:
            workflow_id: ID du workflow
            step: Étape à terminer
            result: Résultat de l'étape (JSON)
            notes: Notes sur l'étape
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de WorkflowStepExecution terminée
        """
        step_execution = self.db.query(WorkflowStepExecution).filter(
            and_(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.step == step
            )
        ).first()
        
        if not step_execution:
            raise ValueError("Étape non trouvée")
        
        step_execution.status = WorkflowStatus.COMPLETED
        step_execution.completed_at = datetime.utcnow()
        step_execution.result = result
        step_execution.notes = notes
        
        if user_id:
            step_execution.updated_by = user_id
            step_execution.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(step_execution)
        
        # Passer à l'étape suivante
        self._advance_workflow(workflow_id, user_id)
        
        return step_execution
    
    def assign_step(self, workflow_id: int, step: WorkflowStep, user_id: int, assigned_to: int) -> WorkflowStepExecution:
        """
        Assigne une étape à un utilisateur
        
        Args:
            workflow_id: ID du workflow
            step: Étape à assigner
            user_id: ID de l'utilisateur qui fait l'assignation
            assigned_to: ID de l'utilisateur assigné
            
        Returns:
            Instance de WorkflowStepExecution assignée
        """
        step_execution = self.db.query(WorkflowStepExecution).filter(
            and_(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.step == step
            )
        ).first()
        
        if not step_execution:
            raise ValueError("Étape non trouvée")
        
        step_execution.assigned_to = assigned_to
        step_execution.updated_by = user_id
        step_execution.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(step_execution)
        
        return step_execution
    
    def skip_step(self, workflow_id: int, step: WorkflowStep, reason: str, user_id: int) -> WorkflowStepExecution:
        """
        Sauter une étape du workflow
        
        Args:
            workflow_id: ID du workflow
            step: Étape à sauter
            reason: Motif du saut
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de WorkflowStepExecution sautée
        """
        step_execution = self.db.query(WorkflowStepExecution).filter(
            and_(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.step == step
            )
        ).first()
        
        if not step_execution:
            raise ValueError("Étape non trouvée")
        
        step_execution.status = WorkflowStatus.SKIPPED
        step_execution.notes = f"SAUTÉ: {reason}"
        step_execution.updated_by = user_id
        step_execution.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(step_execution)
        
        # Passer à l'étape suivante
        self._advance_workflow(workflow_id, user_id)
        
        return step_execution
    
    def _advance_workflow(self, workflow_id: int, user_id: int = None):
        """Avance le workflow à l'étape suivante"""
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            return
        
        # Trouver l'étape actuelle
        current_index = self.WORKFLOW_STEPS.index(workflow.current_step)
        
        # Trouver la prochaine étape non terminée
        for i in range(current_index + 1, len(self.WORKFLOW_STEPS)):
            next_step = self.WORKFLOW_STEPS[i]
            step_execution = self.db.query(WorkflowStepExecution).filter(
                and_(
                    WorkflowStepExecution.workflow_id == workflow_id,
                    WorkflowStepExecution.step == next_step
                )
            ).first()
            
            if step_execution and step_execution.status == WorkflowStatus.PENDING:
                workflow.current_step = next_step
                break
        
        # Calculer la progression
        completed_steps = self.db.query(WorkflowStepExecution).filter(
            and_(
                WorkflowStepExecution.workflow_id == workflow_id,
                WorkflowStepExecution.status == WorkflowStatus.COMPLETED
            )
        ).count()
        
        total_steps = len(self.WORKFLOW_STEPS)
        workflow.progress_percentage = (completed_steps / total_steps) * 100
        
        # Vérifier si le workflow est terminé
        if completed_steps == total_steps:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.current_step = WorkflowStep.ARCHIVING
            workflow.completed_at = datetime.utcnow()
        
        if user_id:
            workflow.updated_by = user_id
            workflow.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def complete_workflow(self, workflow_id: int, user_id: int) -> Workflow:
        """
        Termine un workflow
        
        Args:
            workflow_id: ID du workflow
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Workflow terminée
        """
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        workflow.status = WorkflowStatus.COMPLETED
        workflow.current_step = WorkflowStep.ARCHIVING
        workflow.progress_percentage = 100.0
        workflow.completed_at = datetime.utcnow()
        workflow.updated_by = user_id
        workflow.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(workflow)
        
        return workflow
    
    def get_workflow_status(self, workflow_id: int) -> Dict:
        """
        Récupère le statut détaillé d'un workflow
        
        Args:
            workflow_id: ID du workflow
            
        Returns:
            Dictionnaire du statut
        """
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        steps = self.db.query(WorkflowStepExecution).filter(
            WorkflowStepExecution.workflow_id == workflow_id
        ).order_by(WorkflowStepExecution.step_order).all()
        
        return {
            'workflow_id': workflow.id,
            'workflow_name': workflow.workflow_name,
            'status': workflow.status.value,
            'current_step': workflow.current_step.value if workflow.current_step else None,
            'progress_percentage': workflow.progress_percentage,
            'started_at': workflow.started_at,
            'completed_at': workflow.completed_at,
            'steps': [
                {
                    'step': step.step.value,
                    'order': step.step_order,
                    'status': step.status.value,
                    'assigned_to': step.assigned_to,
                    'started_at': step.started_at,
                    'completed_at': step.completed_at,
                    'notes': step.notes
                }
                for step in steps
            ]
        }
    
    def get_workflow_by_market(self, market_id: int) -> Optional[Workflow]:
        """
        Récupère le workflow d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Instance de Workflow ou None
        """
        return self.db.query(Workflow).filter(
            Workflow.market_id == market_id
        ).first()


def get_workflow_service(db: Session) -> WorkflowService:
    """
    Factory pour créer une instance du service de workflow
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de WorkflowService
    """
    return WorkflowService(db)

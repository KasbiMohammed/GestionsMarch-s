"""
Service métier pour le workflow de validation
Module 3: Validation administrative et technique
Relation: 1 préparation → 1 workflow de validation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.models.validation_workflow import (
    ValidationWorkflow,
    ValidationRecord,
    ValidationChecklist,
    ValidationHistory,
    ValidationAlert,
    ValidationStep,
    ValidationDecision,
    WorkflowStatus,
)
from app.models.market_preparation import MarketPreparation, PreparationStatus


class ValidationWorkflowService:
    """Service de gestion des workflows de validation"""

    SORTABLE_FIELDS = {
        "workflow_number": ValidationWorkflow.workflow_number,
        "status": ValidationWorkflow.status,
        "current_step": ValidationWorkflow.current_step,
        "conformity_percentage": ValidationWorkflow.conformity_percentage,
        "created_at": ValidationWorkflow.created_at,
    }

    # Ordre séquentiel des étapes
    STEP_ORDER = [
        ValidationStep.REQUESTING_SERVICE,
        ValidationStep.TECHNICAL_SERVICE,
        ValidationStep.FINANCIAL_SERVICE,
        ValidationStep.MARKETS_SERVICE,
        ValidationStep.ORDERING_AUTHORITY,
    ]

    def __init__(self, db: Session):
        self.db = db

    def generate_workflow_number(self) -> str:
        """Génère un numéro de workflow unique."""
        count = self.db.query(ValidationWorkflow).count()
        return f"VAL-{datetime.now().year}-{count + 1:04d}"

    def create_workflow(
        self,
        preparation_id: int,
        data: Dict,
        user_id: int,
    ) -> ValidationWorkflow:
        """Crée un nouveau workflow de validation à partir d'une préparation."""
        # Vérifier que la préparation existe
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id
        ).first()
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        # Vérifier qu'un workflow n'existe pas déjà
        existing = self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.preparation_id == preparation_id
        ).first()
        
        if existing:
            raise ValueError("Un workflow de validation existe déjà pour cette préparation")
        
        # Créer le workflow
        workflow = ValidationWorkflow(
            preparation_id=preparation_id,
            workflow_number=data.get("workflow_number") or self.generate_workflow_number(),
            status=WorkflowStatus.PENDING,
            current_step=ValidationStep.REQUESTING_SERVICE,
            conformity_percentage=0,
            started_at=datetime.utcnow(),
            created_by=user_id,
        )
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        
        # Créer la checklist par défaut
        self.create_checklist(workflow.id, user_id)
        
        # Créer les enregistrements de validation pour chaque étape
        self.create_validation_records(workflow.id)
        
        # Ajouter l'historique
        self.add_history(
            workflow.id,
            "Création",
            f"Création du workflow de validation pour la préparation {preparation_id}",
            user_id,
        )
        
        # Générer les alertes initiales
        self.generate_alerts(workflow.id)
        
        return workflow

    def get_workflow(self, workflow_id: int) -> Optional[ValidationWorkflow]:
        """Récupère un workflow par ID."""
        return self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.id == workflow_id,
            ValidationWorkflow.is_deleted == False
        ).first()

    def get_workflow_by_preparation(self, preparation_id: int) -> Optional[ValidationWorkflow]:
        """Récupère un workflow par ID de préparation."""
        return self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.preparation_id == preparation_id,
            ValidationWorkflow.is_deleted == False
        ).first()

    def list_workflows(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        current_step: Optional[ValidationStep] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[ValidationWorkflow], int]:
        """Liste paginée avec recherche, filtres et tri."""
        query = self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.is_deleted == False
        )

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    ValidationWorkflow.workflow_number.ilike(term),
                )
            )

        if status:
            query = query.filter(ValidationWorkflow.status == status)
        
        if current_step:
            query = query.filter(ValidationWorkflow.current_step == current_step)

        sort_column = self.SORTABLE_FIELDS.get(sort_by, ValidationWorkflow.created_at)
        order_fn = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(order_fn(sort_column))

        total = query.count()
        workflows = query.offset(skip).limit(limit).all()

        return workflows, total

    def update_workflow(
        self,
        workflow_id: int,
        data: Dict,
        user_id: int,
    ) -> ValidationWorkflow:
        """Met à jour un workflow."""
        workflow = self.get_workflow(workflow_id)
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        # Mise à jour des champs
        for field, value in data.items():
            if hasattr(workflow, field) and value is not None:
                setattr(workflow, field, value)
        
        workflow.updated_by = user_id
        workflow.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(workflow)
        
        # Ajouter l'historique
        self.add_history(
            workflow.id,
            "Modification",
            "Mise à jour du workflow de validation",
            user_id,
        )
        
        return workflow

    def delete_workflow(
        self,
        workflow_id: int,
        user_id: int,
    ) -> bool:
        """Suppression logique d'un workflow."""
        workflow = self.get_workflow(workflow_id)
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        workflow.is_deleted = True
        workflow.deleted_at = datetime.utcnow()
        workflow.deleted_by = user_id
        
        self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            workflow.id,
            "Suppression",
            "Suppression du workflow de validation",
            user_id,
        )
        
        return True

    def submit_validation_decision(
        self,
        workflow_id: int,
        step: ValidationStep,
        decision: ValidationDecision,
        observations: Optional[str],
        comments: Optional[str],
        return_step: Optional[ValidationStep],
        return_reason: Optional[str],
        user_id: int,
        user_name: str,
        user_role: str,
    ) -> ValidationWorkflow:
        """Soumet une décision de validation pour une étape."""
        workflow = self.get_workflow(workflow_id)
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        # Vérifier que l'étape est correcte
        if workflow.current_step != step:
            raise ValueError(f"L'étape actuelle est {workflow.current_step}, pas {step}")
        
        # Récupérer ou créer l'enregistrement de validation
        validation_record = self.db.query(ValidationRecord).filter(
            ValidationRecord.workflow_id == workflow_id,
            ValidationRecord.step == step
        ).first()
        
        if not validation_record:
            validation_record = ValidationRecord(
                workflow_id=workflow_id,
                step=step,
            )
            self.db.add(validation_record)
        
        # Mettre à jour l'enregistrement
        validation_record.decision = decision
        validation_record.validator_id = user_id
        validation_record.validator_name = user_name
        validation_record.validator_role = user_role
        validation_record.validated_at = datetime.utcnow()
        validation_record.observations = observations
        validation_record.comments = comments
        validation_record.return_step = return_step
        validation_record.return_reason = return_reason
        
        # Mettre à jour le statut du workflow selon la décision
        if decision == ValidationDecision.VALIDATED:
            # Passer à l'étape suivante
            next_step = self.get_next_step(step)
            if next_step:
                workflow.current_step = next_step
                workflow.status = WorkflowStatus.IN_PROGRESS
            else:
                # Dernière étape validée
                workflow.status = WorkflowStatus.VALIDATED
                workflow.completed_at = datetime.utcnow()
                workflow.current_step = step
        elif decision == ValidationDecision.REJECTED:
            workflow.status = WorkflowStatus.REJECTED
        elif decision == ValidationDecision.NEEDS_COMPLETION:
            workflow.status = WorkflowStatus.NEEDS_COMPLETION
            if return_step:
                workflow.current_step = return_step
        
        workflow.updated_by = user_id
        workflow.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(workflow)
        
        # Ajouter l'historique
        action = f"Validation {step.value}"
        description = f"Décision: {decision.value}"
        if comments:
            description += f" - {comments}"
        if return_step:
            description += f" - Retour à {return_step.value}"
        
        self.add_history(
            workflow.id,
            action,
            description,
            user_id,
            from_step=step,
            to_step=workflow.current_step,
            decision=decision,
        )
        
        # Mettre à jour les alertes
        self.generate_alerts(workflow_id)
        
        return workflow

    def get_next_step(self, current_step: ValidationStep) -> Optional[ValidationStep]:
        """Récupère l'étape suivante dans la séquence."""
        try:
            current_index = self.STEP_ORDER.index(current_step)
            if current_index < len(self.STEP_ORDER) - 1:
                return self.STEP_ORDER[current_index + 1]
        except ValueError:
            pass
        return None

    def get_previous_step(self, current_step: ValidationStep) -> Optional[ValidationStep]:
        """Récupère l'étape précédente dans la séquence."""
        try:
            current_index = self.STEP_ORDER.index(current_step)
            if current_index > 0:
                return self.STEP_ORDER[current_index - 1]
        except ValueError:
            pass
        return None

    def create_checklist(self, workflow_id: int, user_id: int):
        """Crée la checklist de conformité par défaut."""
        checklist = ValidationChecklist(
            workflow_id=workflow_id,
            documents_complete=False,
            budget_valid=False,
            estimates_valid=False,
            signatures_valid=False,
            information_coherent=False,
            regulatory_compliance=False,
            calculated_percentage=0,
            checked_by=user_id,
            checked_at=datetime.utcnow(),
        )
        
        self.db.add(checklist)
        self.db.commit()

    def update_checklist(
        self,
        workflow_id: int,
        data: Dict,
        user_id: int,
    ) -> ValidationChecklist:
        """Met à jour la checklist de conformité."""
        checklist = self.db.query(ValidationChecklist).filter(
            ValidationChecklist.workflow_id == workflow_id
        ).first()
        
        if not checklist:
            raise ValueError("Checklist non trouvée")
        
        # Mise à jour des champs
        for field, value in data.items():
            if hasattr(checklist, field) and value is not None:
                setattr(checklist, field, value)
        
        # Calculer le pourcentage de conformité
        checklist.calculated_percentage = self.calculate_conformity_percentage(checklist)
        checklist.checked_by = user_id
        checklist.checked_at = datetime.utcnow()
        checklist.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(checklist)
        
        # Mettre à jour le workflow
        workflow = self.get_workflow(workflow_id)
        if workflow:
            workflow.conformity_percentage = checklist.calculated_percentage
            workflow.updated_by = user_id
            workflow.updated_at = datetime.utcnow()
            self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            workflow_id,
            "Mise à jour checklist",
            f"Pourcentage de conformité: {checklist.calculated_percentage}%",
            user_id,
        )
        
        return checklist

    def calculate_conformity_percentage(self, checklist: ValidationChecklist) -> int:
        """Calcule le pourcentage de conformité."""
        criteria = [
            checklist.documents_complete,
            checklist.budget_valid,
            checklist.estimates_valid,
            checklist.signatures_valid,
            checklist.information_coherent,
            checklist.regulatory_compliance,
        ]
        
        met_criteria = sum(1 for c in criteria if c)
        total_criteria = len(criteria)
        
        return int((met_criteria / total_criteria) * 100) if total_criteria > 0 else 0

    def create_validation_records(self, workflow_id: int):
        """Crée les enregistrements de validation pour chaque étape."""
        for step in self.STEP_ORDER:
            record = ValidationRecord(
                workflow_id=workflow_id,
                step=step,
                decision=ValidationDecision.PENDING,
            )
            self.db.add(record)
        
        self.db.commit()

    def add_history(
        self,
        workflow_id: int,
        action: str,
        description: Optional[str],
        user_id: int,
        from_step: Optional[ValidationStep] = None,
        to_step: Optional[ValidationStep] = None,
        decision: Optional[ValidationDecision] = None,
    ) -> ValidationHistory:
        """Ajoute une entrée à l'historique."""
        from app.models.user import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user else "Inconnu"
        user_role = str(user.role) if user else "Inconnu"
        
        history = ValidationHistory(
            workflow_id=workflow_id,
            action=action,
            description=description,
            from_step=from_step,
            to_step=to_step,
            decision=decision,
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history

    def get_history(self, workflow_id: int) -> List[ValidationHistory]:
        """Récupère l'historique d'un workflow."""
        return self.db.query(ValidationHistory).filter(
            ValidationHistory.workflow_id == workflow_id
        ).order_by(ValidationHistory.created_at.desc()).all()

    def generate_alerts(self, workflow_id: int):
        """Génère les alertes pour un workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return
        
        # Supprimer les anciennes alertes non résolues
        self.db.query(ValidationAlert).filter(
            ValidationAlert.workflow_id == workflow_id,
            ValidationAlert.is_resolved == False
        ).delete()
        
        # Alerte: Validation en attente
        if workflow.status == WorkflowStatus.PENDING:
            alert = ValidationAlert(
                workflow_id=workflow_id,
                alert_type="pending_validation",
                severity="medium",
                title="Validation en attente",
                message=f"Le workflow est en attente de validation à l'étape: {workflow.current_step.value}",
                step=workflow.current_step,
            )
            self.db.add(alert)
        
        # Alerte: À compléter
        if workflow.status == WorkflowStatus.NEEDS_COMPLETION:
            alert = ValidationAlert(
                workflow_id=workflow_id,
                alert_type="needs_completion",
                severity="high",
                title="Dossier à compléter",
                message="Le dossier nécessite des compléments avant de continuer",
            )
            self.db.add(alert)
        
        # Alerte: Rejeté
        if workflow.status == WorkflowStatus.REJECTED:
            alert = ValidationAlert(
                workflow_id=workflow_id,
                alert_type="rejected",
                severity="critical",
                title="Dossier rejeté",
                message="Le dossier a été rejeté lors de la validation",
            )
            self.db.add(alert)
        
        # Alerte: Validation en retard (deadline dépassée)
        current_record = self.db.query(ValidationRecord).filter(
            ValidationRecord.workflow_id == workflow_id,
            ValidationRecord.step == workflow.current_step,
            ValidationRecord.decision == ValidationDecision.PENDING
        ).first()
        
        if current_record and current_record.deadline and current_record.deadline < datetime.utcnow():
            alert = ValidationAlert(
                workflow_id=workflow_id,
                alert_type="overdue_validation",
                severity="high",
                title="Validation en retard",
                message=f"La validation pour l'étape {workflow.current_step.value} est en retard",
                step=workflow.current_step,
            )
            self.db.add(alert)
        
        self.db.commit()

    def get_alerts(self, workflow_id: int) -> List[ValidationAlert]:
        """Récupère les alertes d'un workflow."""
        return self.db.query(ValidationAlert).filter(
            ValidationAlert.workflow_id == workflow_id,
            ValidationAlert.is_resolved == False
        ).order_by(ValidationAlert.created_at.desc()).all()

    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Résout une alerte."""
        alert = self.db.query(ValidationAlert).filter(
            ValidationAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        
        self.db.commit()
        
        return True

    def get_statistics(self) -> Dict:
        """Calcule les statistiques des workflows."""
        total = self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.is_deleted == False
        ).count()
        
        by_status = {}
        for status in WorkflowStatus:
            count = self.db.query(ValidationWorkflow).filter(
                ValidationWorkflow.status == status,
                ValidationWorkflow.is_deleted == False
            ).count()
            by_status[status.value] = count
        
        by_step = {}
        for step in ValidationStep:
            count = self.db.query(ValidationWorkflow).filter(
                ValidationWorkflow.current_step == step,
                ValidationWorkflow.is_deleted == False
            ).count()
            by_step[step.value] = count
        
        avg_conformity = self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.is_deleted == False
        ).with_entities(
            ValidationWorkflow.conformity_percentage
        ).all()
        
        avg_conformity_value = sum(c[0] for c in avg_conformity) / len(avg_conformity) if avg_conformity else 0
        
        return {
            "total": total,
            "by_status": by_status,
            "by_step": by_step,
            "average_conformity": avg_conformity_value,
        }

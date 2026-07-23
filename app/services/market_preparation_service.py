"""
Service métier pour la préparation des marchés
Module 2: Préparation du dossier du marché
Relation: 1 planification → 1 dossier de préparation
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.models.market_preparation import (
    MarketPreparation,
    PreparationDocument,
    PreparationHistory,
    PreparationAlert,
    PreparationStatus,
)
from app.models.market_planning import MarketPlanning, MarketPlanningStatus


class MarketPreparationService:
    """Service de gestion des préparations de marchés"""

    SORTABLE_FIELDS = {
        "preparation_number": MarketPreparation.preparation_number,
        "object": MarketPreparation.object,
        "estimated_budget": MarketPreparation.estimated_budget,
        "status": MarketPreparation.status,
        "progress_percentage": MarketPreparation.progress_percentage,
        "created_at": MarketPreparation.created_at,
    }

    def __init__(self, db: Session):
        self.db = db

    def generate_preparation_number(self) -> str:
        """Génère un numéro de préparation unique."""
        count = self.db.query(MarketPreparation).count()
        return f"PREP-{datetime.now().year}-{count + 1:04d}"

    def create_preparation(
        self,
        planning_id: int,
        data: Dict,
        user_id: int,
    ) -> MarketPreparation:
        """Crée un nouveau dossier de préparation à partir d'une planification validée."""
        # Vérifier que la planification existe et est validée
        planning = self.db.query(MarketPlanning).filter(
            MarketPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise ValueError("Planification non trouvée")
        
        if planning.status != MarketPlanningStatus.VALIDEE:
            raise ValueError("La planification doit être validée pour créer un dossier de préparation")
        
        # Vérifier qu'une préparation n'existe pas déjà
        existing = self.db.query(MarketPreparation).filter(
            MarketPreparation.planning_id == planning_id
        ).first()
        
        if existing:
            raise ValueError("Un dossier de préparation existe déjà pour cette planification")
        
        # Créer la préparation
        preparation = MarketPreparation(
            planning_id=planning_id,
            preparation_number=data.get("preparation_number") or self.generate_preparation_number(),
            object=data.get("object", planning.title),
            procurement_type=data.get("procurement_type", planning.project_type.value),
            procedure_type=data.get("procedure_type", planning.procedure_type.value),
            requesting_service=data.get("requesting_service", planning.requesting_service_name),
            responsible_id=data.get("responsible_id", planning.responsible_id),
            duration=data.get("duration"),
            location=data.get("location"),
            estimated_budget=data.get("estimated_budget", planning.estimated_budget),
            funding_source=data.get("funding_source", planning.funding_source),
            progress_percentage=0,
            status=PreparationStatus.DRAFT,
            observations=data.get("observations"),
            created_by=user_id,
        )
        
        self.db.add(preparation)
        self.db.commit()
        self.db.refresh(preparation)
        
        # Ajouter l'historique
        self.add_history(
            preparation.id,
            "Création",
            f"Création du dossier de préparation à partir de la planification {planning.planning_number}",
            user_id,
        )
        
        # Créer les documents requis par défaut
        self.create_default_documents(preparation.id, user_id)
        
        # Générer les alertes initiales
        self.generate_alerts(preparation.id)
        
        return preparation

    def get_preparation(self, preparation_id: int) -> Optional[MarketPreparation]:
        """Récupère une préparation par ID."""
        return self.db.query(MarketPreparation).filter(
            MarketPreparation.id == preparation_id,
            MarketPreparation.is_deleted == False
        ).first()

    def get_preparation_by_planning(self, planning_id: int) -> Optional[MarketPreparation]:
        """Récupère une préparation par ID de planification."""
        return self.db.query(MarketPreparation).filter(
            MarketPreparation.planning_id == planning_id,
            MarketPreparation.is_deleted == False
        ).first()

    def list_preparations(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[PreparationStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[MarketPreparation], int]:
        """Liste paginée avec recherche, filtres et tri."""
        query = self.db.query(MarketPreparation).filter(
            MarketPreparation.is_deleted == False
        )

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    MarketPreparation.preparation_number.ilike(term),
                    MarketPreparation.object.ilike(term),
                    MarketPreparation.requesting_service.ilike(term),
                )
            )

        if status:
            query = query.filter(MarketPreparation.status == status)

        sort_column = self.SORTABLE_FIELDS.get(sort_by, MarketPreparation.created_at)
        order_fn = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(order_fn(sort_column))

        total = query.count()
        preparations = query.offset(skip).limit(limit).all()

        return preparations, total

    def update_preparation(
        self,
        preparation_id: int,
        data: Dict,
        user_id: int,
    ) -> MarketPreparation:
        """Met à jour une préparation."""
        preparation = self.get_preparation(preparation_id)
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        # Mise à jour des champs
        for field, value in data.items():
            if hasattr(preparation, field) and value is not None:
                setattr(preparation, field, value)
        
        preparation.updated_by = user_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        # Ajouter l'historique
        self.add_history(
            preparation.id,
            "Modification",
            "Mise à jour du dossier de préparation",
            user_id,
        )
        
        # Recalculer la progression
        self.calculate_progress(preparation_id)
        
        # Mettre à jour les alertes
        self.generate_alerts(preparation_id)
        
        return preparation

    def delete_preparation(
        self,
        preparation_id: int,
        user_id: int,
    ) -> bool:
        """Suppression logique d'une préparation."""
        preparation = self.get_preparation(preparation_id)
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        preparation.is_deleted = True
        preparation.deleted_at = datetime.utcnow()
        preparation.deleted_by = user_id
        
        self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            preparation.id,
            "Suppression",
            "Suppression du dossier de préparation",
            user_id,
        )
        
        return True

    def validate_preparation(
        self,
        preparation_id: int,
        validation_type: str,
        approved: bool,
        comments: Optional[str],
        user_id: int,
    ) -> MarketPreparation:
        """Valide une préparation (technique, financière ou administrative)."""
        preparation = self.get_preparation(preparation_id)
        
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        validation_date = datetime.utcnow()
        
        if validation_type == "technical":
            preparation.technical_validation = approved
            preparation.technical_validator = user_id
            preparation.technical_validation_date = validation_date
            preparation.technical_validation_comments = comments
        elif validation_type == "financial":
            preparation.financial_validation = approved
            preparation.financial_validator = user_id
            preparation.financial_validation_date = validation_date
            preparation.financial_validation_comments = comments
        elif validation_type == "administrative":
            preparation.administrative_validation = approved
            preparation.administrative_validator = user_id
            preparation.administrative_validation_date = validation_date
            preparation.administrative_validation_comments = comments
        else:
            raise ValueError("Type de validation invalide")
        
        # Mettre à jour le statut global
        self.update_status_based_on_validations(preparation)
        
        preparation.updated_by = user_id
        preparation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(preparation)
        
        # Ajouter l'historique
        action = f"Validation {validation_type}"
        description = f"Validation {validation_type}: {'Approuvée' if approved else 'Rejetée'}"
        if comments:
            description += f" - {comments}"
        self.add_history(preparation.id, action, description, user_id)
        
        # Mettre à jour les alertes
        self.generate_alerts(preparation_id)
        
        return preparation

    def update_status_based_on_validations(self, preparation: MarketPreparation):
        """Met à jour le statut en fonction des validations."""
        if not preparation.technical_validation:
            preparation.status = PreparationStatus.DRAFT
        elif not preparation.financial_validation:
            preparation.status = PreparationStatus.IN_PROGRESS
        elif not preparation.administrative_validation:
            preparation.status = PreparationStatus.PENDING_VALIDATION
        elif all([
            preparation.technical_validation,
            preparation.financial_validation,
            preparation.administrative_validation,
        ]):
            preparation.status = PreparationStatus.VALIDATED
        else:
            preparation.status = PreparationStatus.REJECTED

    def calculate_progress(self, preparation_id: int):
        """Calcule le pourcentage de progression de la préparation."""
        preparation = self.get_preparation(preparation_id)
        if not preparation:
            return
        
        # Calcul basé sur les validations et les documents
        total_steps = 6  # 3 validations + documents complets + informations complètes + observations
        completed_steps = 0
        
        if preparation.technical_validation:
            completed_steps += 1
        if preparation.financial_validation:
            completed_steps += 1
        if preparation.administrative_validation:
            completed_steps += 1
        
        # Vérifier les documents
        required_docs = self.db.query(PreparationDocument).filter(
            PreparationDocument.preparation_id == preparation_id,
            PreparationDocument.is_required == True
        ).count()
        
        uploaded_docs = self.db.query(PreparationDocument).filter(
            PreparationDocument.preparation_id == preparation_id,
            PreparationDocument.is_required == True,
            PreparationDocument.is_uploaded == True
        ).count()
        
        if required_docs > 0 and uploaded_docs == required_docs:
            completed_steps += 1
        
        # Vérifier les informations de base
        if preparation.object and preparation.estimated_budget:
            completed_steps += 1
        
        # Vérifier les observations
        if preparation.observations:
            completed_steps += 1
        
        progress = int((completed_steps / total_steps) * 100)
        preparation.progress_percentage = progress
        self.db.commit()

    def create_default_documents(self, preparation_id: int, user_id: int):
        """Crée les documents requis par défaut."""
        required_documents = [
            {"type": "CPS", "title": "Cahier des Prescriptions Spéciales", "required": True},
            {"type": "RC", "title": "Règlement de Consultation", "required": True},
            {"type": "AE", "title": "Acte d'Engagement", "required": True},
            {"type": "BPU", "title": "Bordereau des Prix Unitaires", "required": True},
            {"type": "DQE", "title": "Devis Quantitatif Estimatif", "required": True},
            {"type": "ESTIMATION", "title": "Estimation détaillée", "required": True},
            {"type": "PLANS", "title": "Plans techniques", "required": False},
            {"type": "AUTRES", "title": "Autres documents", "required": False},
        ]
        
        for doc in required_documents:
            document = PreparationDocument(
                preparation_id=preparation_id,
                document_type=doc["type"],
                title=doc["title"],
                is_required=doc["required"],
                is_uploaded=False,
                created_by=user_id,
            )
            self.db.add(document)
        
        self.db.commit()

    def add_document(
        self,
        preparation_id: int,
        document_type: str,
        title: str,
        file_path: str,
        file_name: str,
        file_size: int,
        file_type: str,
        user_id: int,
        description: Optional[str] = None,
    ) -> PreparationDocument:
        """Ajoute un document à la préparation."""
        preparation = self.get_preparation(preparation_id)
        if not preparation:
            raise ValueError("Préparation non trouvée")
        
        document = PreparationDocument(
            preparation_id=preparation_id,
            document_type=document_type,
            title=title,
            description=description,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            is_uploaded=True,
            uploaded_by=user_id,
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Ajouter l'historique
        self.add_history(
            preparation_id,
            "Ajout document",
            f"Ajout du document: {title}",
            user_id,
        )
        
        # Recalculer la progression
        self.calculate_progress(preparation_id)
        
        # Mettre à jour les alertes
        self.generate_alerts(preparation_id)
        
        return document

    def delete_document(self, document_id: int, user_id: int) -> bool:
        """Supprime un document."""
        document = self.db.query(PreparationDocument).filter(
            PreparationDocument.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document non trouvé")
        
        preparation_id = document.preparation_id
        self.db.delete(document)
        self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            preparation_id,
            "Suppression document",
            f"Suppression du document: {document.title}",
            user_id,
        )
        
        # Recalculer la progression
        self.calculate_progress(preparation_id)
        
        # Mettre à jour les alertes
        self.generate_alerts(preparation_id)
        
        return True

    def add_history(
        self,
        preparation_id: int,
        action: str,
        description: Optional[str],
        user_id: int,
    ) -> PreparationHistory:
        """Ajoute une entrée à l'historique."""
        from app.models.user import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user else "Inconnu"
        
        history = PreparationHistory(
            preparation_id=preparation_id,
            action=action,
            description=description,
            user_id=user_id,
            user_name=user_name,
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history

    def get_history(self, preparation_id: int) -> List[PreparationHistory]:
        """Récupère l'historique d'une préparation."""
        return self.db.query(PreparationHistory).filter(
            PreparationHistory.preparation_id == preparation_id
        ).order_by(PreparationHistory.created_at.desc()).all()

    def generate_alerts(self, preparation_id: int):
        """Génère les alertes pour une préparation."""
        preparation = self.get_preparation(preparation_id)
        if not preparation:
            return
        
        # Supprimer les anciennes alertes non résolues
        self.db.query(PreparationAlert).filter(
            PreparationAlert.preparation_id == preparation_id,
            PreparationAlert.is_resolved == False
        ).delete()
        
        # Alerte: Documents manquants
        required_docs = self.db.query(PreparationDocument).filter(
            PreparationDocument.preparation_id == preparation_id,
            PreparationDocument.is_required == True
        ).all()
        
        missing_docs = [d for d in required_docs if not d.is_uploaded]
        if missing_docs:
            alert = PreparationAlert(
                preparation_id=preparation_id,
                alert_type="missing_documents",
                severity="high",
                title="Documents manquants",
                message=f"{len(missing_docs)} document(s) requis(s) non téléchargé(s)",
            )
            self.db.add(alert)
        
        # Alerte: Validations en attente
        if preparation.status == PreparationStatus.PENDING_VALIDATION:
            alert = PreparationAlert(
                preparation_id=preparation_id,
                alert_type="pending_validation",
                severity="medium",
                title="Validation en attente",
                message="Validation administrative en attente",
            )
            self.db.add(alert)
        
        # Alerte: Observations ouvertes
        if preparation.observations:
            alert = PreparationAlert(
                preparation_id=preparation_id,
                alert_type="open_observations",
                severity="low",
                title="Observations présentes",
                message="Des observations ont été ajoutées au dossier",
            )
            self.db.add(alert)
        
        self.db.commit()

    def get_alerts(self, preparation_id: int) -> List[PreparationAlert]:
        """Récupère les alertes d'une préparation."""
        return self.db.query(PreparationAlert).filter(
            PreparationAlert.preparation_id == preparation_id,
            PreparationAlert.is_resolved == False
        ).order_by(PreparationAlert.created_at.desc()).all()

    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Résout une alerte."""
        alert = self.db.query(PreparationAlert).filter(
            PreparationAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        
        self.db.commit()
        
        return True

    def get_statistics(self) -> Dict:
        """Calcule les statistiques des préparations."""
        total = self.db.query(MarketPreparation).filter(
            MarketPreparation.is_deleted == False
        ).count()
        
        by_status = {}
        for status in PreparationStatus:
            count = self.db.query(MarketPreparation).filter(
                MarketPreparation.status == status,
                MarketPreparation.is_deleted == False
            ).count()
            by_status[status.value] = count
        
        total_budget = self.db.query(MarketPreparation).filter(
            MarketPreparation.is_deleted == False
        ).with_entities(
            MarketPreparation.estimated_budget
        ).all()
        
        total_budget_sum = sum(b[0] for b in total_budget) if total_budget else 0
        
        return {
            "total": total,
            "by_status": by_status,
            "total_budget": total_budget_sum,
        }

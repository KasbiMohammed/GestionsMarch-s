"""
Service métier pour la planification des marchés
Module: Planification des Marchés
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.annual_planning import Service
from app.models.history import History
from app.models.market_planning import (
    MarketPlanning,
    MarketPlanningStatus,
    PlanningDocument,
    PlanningPriority,
    ProcedureType,
    ProjectType,
)


class MarketPlanningService:
    """Service de gestion des planifications de marchés"""

    SORTABLE_FIELDS = {
        "planning_number": MarketPlanning.planning_number,
        "fiscal_year": MarketPlanning.fiscal_year,
        "title": MarketPlanning.title,
        "estimated_budget": MarketPlanning.estimated_budget,
        "priority": MarketPlanning.priority,
        "status": MarketPlanning.status,
        "created_at": MarketPlanning.created_at,
        "launch_date": MarketPlanning.launch_date,
    }

    def __init__(self, db: Session):
        self.db = db

    def generate_planning_number(self, fiscal_year: int) -> str:
        """Génère un numéro de planification unique pour l'exercice."""
        count = self.db.query(MarketPlanning).filter(
            MarketPlanning.fiscal_year == fiscal_year
        ).count()
        return f"PLAN-{fiscal_year}-{count + 1:04d}"

    def list_plannings(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        project_type: Optional[ProjectType] = None,
        procedure_type: Optional[ProcedureType] = None,
        status: Optional[MarketPlanningStatus] = None,
        priority: Optional[PlanningPriority] = None,
        requesting_service_id: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[MarketPlanning], int]:
        """Liste paginée avec recherche, filtres et tri."""
        query = self.db.query(MarketPlanning)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    MarketPlanning.planning_number.ilike(term),
                    MarketPlanning.title.ilike(term),
                    MarketPlanning.description.ilike(term),
                    MarketPlanning.requesting_service_name.ilike(term),
                    MarketPlanning.responsible_name.ilike(term),
                    MarketPlanning.funding_source.ilike(term),
                )
            )

        if fiscal_year:
            query = query.filter(MarketPlanning.fiscal_year == fiscal_year)
        if project_type:
            query = query.filter(MarketPlanning.project_type == project_type)
        if procedure_type:
            query = query.filter(MarketPlanning.procedure_type == procedure_type)
        if status:
            query = query.filter(MarketPlanning.status == status)
        if priority:
            query = query.filter(MarketPlanning.priority == priority)
        if requesting_service_id:
            query = query.filter(
                MarketPlanning.requesting_service_id == requesting_service_id
            )

        sort_column = self.SORTABLE_FIELDS.get(sort_by, MarketPlanning.created_at)
        order_fn = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(order_fn(sort_column))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_by_id(self, planning_id: int) -> Optional[MarketPlanning]:
        """Récupère une planification par ID."""
        return self.db.query(MarketPlanning).filter(
            MarketPlanning.id == planning_id
        ).first()

    def get_by_number(self, planning_number: str) -> Optional[MarketPlanning]:
        """Récupère une planification par numéro."""
        return self.db.query(MarketPlanning).filter(
            MarketPlanning.planning_number == planning_number
        ).first()

    def create(self, data: dict, user_id: int) -> MarketPlanning:
        """Crée une nouvelle planification."""
        if not data.get("planning_number"):
            data["planning_number"] = self.generate_planning_number(data["fiscal_year"])

        if self.get_by_number(data["planning_number"]):
            raise ValueError("Ce numéro de planification existe déjà")

        planning = MarketPlanning(
            **data,
            created_by=user_id,
            modified_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(planning)
        self.db.commit()
        self.db.refresh(planning)

        self._log_history(
            planning.id,
            "Création planification",
            f"Création de la planification {planning.planning_number}",
            user_id,
        )
        return planning

    def update(
        self, planning_id: int, data: dict, user_id: int
    ) -> Optional[MarketPlanning]:
        """Met à jour une planification existante."""
        planning = self.get_by_id(planning_id)
        if not planning:
            return None

        if "planning_number" in data and data["planning_number"]:
            existing = self.get_by_number(data["planning_number"])
            if existing and existing.id != planning_id:
                raise ValueError("Ce numéro de planification existe déjà")

        for key, value in data.items():
            if value is not None and hasattr(planning, key):
                setattr(planning, key, value)

        planning.modified_by = user_id
        planning.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(planning)

        self._log_history(
            planning.id,
            "Modification planification",
            f"Modification de la planification {planning.planning_number}",
            user_id,
        )
        return planning

    def delete(self, planning_id: int, user_id: int) -> bool:
        """Supprime une planification et ses documents."""
        planning = self.get_by_id(planning_id)
        if not planning:
            return False

        for doc in planning.documents:
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except OSError:
                    pass

        number = planning.planning_number
        self.db.delete(planning)
        self.db.commit()

        self._log_history(
            None,
            "Suppression planification",
            f"Suppression de la planification {number}",
            user_id,
        )
        return True

    def add_document(
        self,
        planning_id: int,
        file_content: bytes,
        original_filename: str,
        name: str,
        user_id: int,
        description: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[PlanningDocument]:
        """Ajoute un document joint à une planification."""
        planning = self.get_by_id(planning_id)
        if not planning:
            return None

        upload_dir = os.path.join(settings.UPLOAD_DIR, "planifications", str(planning_id))
        os.makedirs(upload_dir, exist_ok=True)

        ext = os.path.splitext(original_filename)[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_dir, stored_name)

        with open(file_path, "wb") as f:
            f.write(file_content)

        document = PlanningDocument(
            planning_id=planning_id,
            name=name,
            description=description,
            file_name=original_filename,
            file_path=file_path,
            file_size=len(file_content),
            file_type=content_type,
            uploaded_by=user_id,
            uploaded_at=datetime.utcnow(),
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: int) -> bool:
        """Supprime un document joint."""
        document = self.db.query(PlanningDocument).filter(
            PlanningDocument.id == document_id
        ).first()
        if not document:
            return False

        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except OSError:
                pass

        self.db.delete(document)
        self.db.commit()
        return True

    def get_statistics(self, fiscal_year: Optional[int] = None) -> Dict:
        """Calcule les statistiques pour le tableau de bord."""
        query = self.db.query(MarketPlanning)
        if fiscal_year:
            query = query.filter(MarketPlanning.fiscal_year == fiscal_year)

        plannings = query.all()
        total_budget = sum(p.estimated_budget or 0 for p in plannings)

        by_project_type = {}
        for pt in ProjectType:
            by_project_type[pt.value] = sum(
                1 for p in plannings if p.project_type == pt
            )

        by_procedure_type = {}
        for proc in ProcedureType:
            by_procedure_type[proc.value] = sum(
                1 for p in plannings if p.procedure_type == proc
            )

        by_status = {}
        for st in MarketPlanningStatus:
            by_status[st.value] = sum(
                1 for p in plannings if p.status == st
            )

        return {
            "total_count": len(plannings),
            "total_budget": total_budget,
            "by_project_type": by_project_type,
            "by_procedure_type": by_procedure_type,
            "by_status": by_status,
        }

    def list_services(self) -> List[Service]:
        """Liste les services disponibles."""
        return self.db.query(Service).order_by(Service.name).all()

    def _log_history(
        self,
        planning_id: Optional[int],
        action: str,
        description: str,
        user_id: int,
    ):
        """Enregistre une action dans l'historique."""
        history = History(
            market_id=None,
            action=action,
            description=description,
            user_id=user_id,
            created_at=datetime.utcnow(),
        )
        self.db.add(history)
        self.db.commit()


def get_market_planning_service(db: Session) -> MarketPlanningService:
    """Factory pour le service de planification."""
    return MarketPlanningService(db)

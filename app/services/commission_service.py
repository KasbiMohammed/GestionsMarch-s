"""
Service métier pour la gestion des commissions
Module 4: Constitution et gestion de la commission
Relation: 1 workflow de validation → 1 commission
Une commission peut avoir plusieurs séances indépendantes
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.models.commission import (
    Commission,
    CommissionMember,
    CommissionSession,
    CommissionAlert,
    CommissionHistory,
    CommissionStatus,
    SessionStatus,
    MemberRole,
)
from app.models.validation_workflow import ValidationWorkflow, WorkflowStatus
from app.models.user import User


class CommissionService:
    """Service de gestion des commissions"""

    SORTABLE_FIELDS = {
        "commission_number": Commission.commission_number,
        "title": Commission.title,
        "status": Commission.status,
        "constituted_at": Commission.constituted_at,
        "created_at": Commission.created_at,
    }

    def __init__(self, db: Session):
        self.db = db

    def generate_commission_number(self) -> str:
        """Génère un numéro de commission unique."""
        count = self.db.query(Commission).count()
        return f"COM-{datetime.now().year}-{count + 1:04d}"

    def create_commission(
        self,
        workflow_id: int,
        data: Dict,
        user_id: int,
    ) -> Commission:
        """Crée une nouvelle commission à partir d'un workflow validé."""
        # Vérifier que le workflow existe et est validé
        workflow = self.db.query(ValidationWorkflow).filter(
            ValidationWorkflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise ValueError("Workflow non trouvé")
        
        if workflow.status != WorkflowStatus.VALIDATED:
            raise ValueError("Le workflow doit être validé pour créer une commission")
        
        # Vérifier qu'une commission n'existe pas déjà
        existing = self.db.query(Commission).filter(
            Commission.workflow_id == workflow_id
        ).first()
        
        if existing:
            raise ValueError("Une commission existe déjà pour ce workflow")
        
        # Créer la commission
        commission = Commission(
            workflow_id=workflow_id,
            commission_number=data.get("commission_number") or self.generate_commission_number(),
            title=data.get("title"),
            description=data.get("description"),
            status=CommissionStatus.TO_BE_CONSTITUTED,
            observations=data.get("observations"),
            created_by=user_id,
        )
        
        self.db.add(commission)
        self.db.commit()
        self.db.refresh(commission)
        
        # Ajouter les membres si fournis
        members_data = data.get("members", [])
        for member_data in members_data:
            self.add_member(commission.id, member_data, user_id)
        
        # Ajouter l'historique
        self.add_history(
            commission.id,
            "Création",
            f"Création de la commission pour le workflow {workflow_id}",
            user_id,
        )
        
        # Générer les alertes initiales
        self.generate_alerts(commission.id)
        
        return commission

    def get_commission(self, commission_id: int) -> Optional[Commission]:
        """Récupère une commission par ID."""
        return self.db.query(Commission).filter(
            Commission.id == commission_id,
            Commission.is_deleted == False
        ).first()

    def get_commission_by_workflow(self, workflow_id: int) -> Optional[Commission]:
        """Récupère une commission par ID de workflow."""
        return self.db.query(Commission).filter(
            Commission.workflow_id == workflow_id,
            Commission.is_deleted == False
        ).first()

    def list_commissions(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[CommissionStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Commission], int]:
        """Liste paginée avec recherche, filtres et tri."""
        query = self.db.query(Commission).filter(
            Commission.is_deleted == False
        )

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Commission.commission_number.ilike(term),
                    Commission.title.ilike(term),
                )
            )

        if status:
            query = query.filter(Commission.status == status)

        sort_column = self.SORTABLE_FIELDS.get(sort_by, Commission.created_at)
        order_fn = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(order_fn(sort_column))

        total = query.count()
        commissions = query.offset(skip).limit(limit).all()

        return commissions, total

    def update_commission(
        self,
        commission_id: int,
        data: Dict,
        user_id: int,
    ) -> Commission:
        """Met à jour une commission."""
        commission = self.get_commission(commission_id)
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        # Mise à jour des champs
        for field, value in data.items():
            if hasattr(commission, field) and value is not None:
                setattr(commission, field, value)
        
        # Mettre à jour le statut si nécessaire
        if commission.status == CommissionStatus.TO_BE_CONSTITUTED and commission.members:
            commission.status = CommissionStatus.CONSTITUTED
            commission.constituted_at = datetime.utcnow()
        
        commission.updated_by = user_id
        commission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(commission)
        
        # Ajouter l'historique
        self.add_history(
            commission.id,
            "Modification",
            "Mise à jour de la commission",
            user_id,
        )
        
        return commission

    def delete_commission(
        self,
        commission_id: int,
        user_id: int,
    ) -> bool:
        """Suppression logique d'une commission."""
        commission = self.get_commission(commission_id)
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        commission.is_deleted = True
        commission.deleted_at = datetime.utcnow()
        commission.deleted_by = user_id
        
        self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            commission.id,
            "Suppression",
            "Suppression de la commission",
            user_id,
        )
        
        return True

    def add_member(
        self,
        commission_id: int,
        data: Dict,
        user_id: int,
    ) -> CommissionMember:
        """Ajoute un membre à la commission."""
        commission = self.get_commission(commission_id)
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        from app.models.user import User
        user = self.db.query(User).filter(User.id == data["user_id"]).first()
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        member = CommissionMember(
            commission_id=commission_id,
            user_id=data["user_id"],
            role=data["role"],
            is_president=data.get("is_president", False),
            is_secretary=data.get("is_secretary", False),
            user_name=user.full_name,
            user_function=data.get("user_function"),
            user_department=data.get("user_department"),
            substitute_for_id=data.get("substitute_for_id"),
        )
        
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        
        # Ajouter l'historique
        self.add_history(
            commission_id,
            "Ajout membre",
            f"Ajout du membre {user.full_name} ({data['role']})",
            user_id,
            member_id=member.id,
        )
        
        return member

    def remove_member(
        self,
        member_id: int,
        user_id: int,
    ) -> bool:
        """Supprime un membre de la commission."""
        member = self.db.query(CommissionMember).filter(
            CommissionMember.id == member_id
        ).first()
        
        if not member:
            raise ValueError("Membre non trouvé")
        
        commission_id = member.commission_id
        self.db.delete(member)
        self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            commission_id,
            "Suppression membre",
            f"Suppression du membre ID {member_id}",
            user_id,
            member_id=member_id,
        )
        
        return True

    def create_session(
        self,
        commission_id: int,
        data: Dict,
        user_id: int,
    ) -> CommissionSession:
        """Crée une nouvelle séance pour la commission."""
        commission = self.get_commission(commission_id)
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        # Déterminer le numéro de séance
        last_session = self.db.query(CommissionSession).filter(
            CommissionSession.commission_id == commission_id
        ).order_by(CommissionSession.session_number.desc()).first()
        
        next_number = (last_session.session_number + 1) if last_session else 1
        
        session = CommissionSession(
            commission_id=commission_id,
            session_number=next_number,
            session_title=data.get("session_title", f"Séance {next_number}"),
            session_type=data.get("session_type"),
            planned_date=data["planned_date"],
            planned_time=data.get("planned_time"),
            location=data.get("location"),
            agenda=data.get("agenda"),
            observations=data.get("observations"),
            decisions=data.get("decisions"),
            created_by=user_id,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Mettre à jour le statut de la commission
        if commission.status == CommissionStatus.CONSTITUTED:
            commission.status = CommissionStatus.SESSIONS_PLANNED
            commission.updated_by = user_id
            commission.updated_at = datetime.utcnow()
            self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            commission_id,
            "Création séance",
            f"Création de la séance {next_number}: {session.session_title}",
            user_id,
            session_id=session.id,
        )
        
        # Générer les alertes
        self.generate_alerts(commission_id)
        
        return session

    def update_session(
        self,
        session_id: int,
        data: Dict,
        user_id: int,
    ) -> CommissionSession:
        """Met à jour une séance."""
        session = self.db.query(CommissionSession).filter(
            CommissionSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError("Séance non trouvée")
        
        # Mise à jour des champs
        for field, value in data.items():
            if hasattr(session, field) and value is not None:
                setattr(session, field, value)
        
        session.updated_by = user_id
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        # Ajouter l'historique
        self.add_history(
            session.commission_id,
            "Modification séance",
            f"Mise à jour de la séance {session.session_number}",
            user_id,
            session_id=session.id,
        )
        
        return session

    def update_session_status(
        self,
        session_id: int,
        status: SessionStatus,
        user_id: int,
        postponed_to: Optional[datetime] = None,
        postponed_reason: Optional[str] = None,
        suspended_reason: Optional[str] = None,
    ) -> CommissionSession:
        """Met à jour le statut d'une séance."""
        session = self.db.query(CommissionSession).filter(
            CommissionSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError("Séance non trouvée")
        
        session.status = status
        
        if status == SessionStatus.IN_PROGRESS:
            session.started_at = datetime.utcnow()
        elif status == SessionStatus.CLOSED:
            session.ended_at = datetime.utcnow()
        elif status == SessionStatus.POSTPONED:
            session.postponed_to = postponed_to
            session.postponed_reason = postponed_reason
        elif status == SessionStatus.SUSPENDED:
            session.suspended_reason = suspended_reason
        
        session.updated_by = user_id
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        # Mettre à jour le statut de la commission
        commission = self.get_commission(session.commission_id)
        if commission:
            self.update_commission_status_based_on_sessions(commission, user_id)
        
        # Ajouter l'historique
        self.add_history(
            session.commission_id,
            "Changement statut séance",
            f"Séance {session.session_number}: {status.value}",
            user_id,
            session_id=session.id,
        )
        
        # Générer les alertes
        self.generate_alerts(session.commission_id)
        
        return session

    def update_commission_status_based_on_sessions(
        self,
        commission: Commission,
        user_id: int,
    ):
        """Met à jour le statut de la commission en fonction des séances."""
        sessions = self.db.query(CommissionSession).filter(
            CommissionSession.commission_id == commission.id
        ).all()
        
        if not sessions:
            return
        
        # Vérifier si une séance est en cours
        in_progress = any(s.status == SessionStatus.IN_PROGRESS for s in sessions)
        if in_progress:
            commission.status = CommissionStatus.SESSION_IN_PROGRESS
            commission.updated_by = user_id
            commission.updated_at = datetime.utcnow()
            return
        
        # Vérifier si toutes les séances sont clôturées
        all_closed = all(s.status == SessionStatus.CLOSED for s in sessions)
        if all_closed:
            commission.status = CommissionStatus.SESSION_CLOSED
            commission.updated_by = user_id
            commission.updated_at = datetime.utcnow()
            return
        
        # Vérifier si au moins une séance est planifiée
        any_planned = any(s.status == SessionStatus.PLANNED for s in sessions)
        if any_planned:
            commission.status = CommissionStatus.SESSIONS_PLANNED
            commission.updated_by = user_id
            commission.updated_at = datetime.utcnow()
            return

    def generate_pv(
        self,
        session_id: int,
        pv_content: str,
        user_id: int,
    ) -> CommissionSession:
        """Génère le procès-verbal d'une séance."""
        session = self.db.query(CommissionSession).filter(
            CommissionSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError("Séance non trouvée")
        
        session.pv_content = pv_content
        session.pv_generated = True
        session.pv_generated_by = user_id
        session.pv_generated_at = datetime.utcnow()
        
        session.updated_by = user_id
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        # Ajouter l'historique
        self.add_history(
            session.commission_id,
            "Génération PV",
            f"PV généré pour la séance {session.session_number}",
            user_id,
            session_id=session.id,
        )
        
        return session

    def close_commission(
        self,
        commission_id: int,
        user_id: int,
    ) -> Commission:
        """Clôture la commission."""
        commission = self.get_commission(commission_id)
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        commission.status = CommissionStatus.COMMISSION_CLOSED
        commission.closed_at = datetime.utcnow()
        commission.updated_by = user_id
        commission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(commission)
        
        # Ajouter l'historique
        self.add_history(
            commission_id,
            "Clôture",
            "Clôture de la commission",
            user_id,
        )
        
        return commission

    def add_history(
        self,
        commission_id: int,
        action: str,
        description: Optional[str],
        user_id: int,
        session_id: Optional[int] = None,
        member_id: Optional[int] = None,
    ) -> CommissionHistory:
        """Ajoute une entrée à l'historique."""
        from app.models.user import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user else "Inconnu"
        
        history = CommissionHistory(
            commission_id=commission_id,
            action=action,
            description=description,
            session_id=session_id,
            member_id=member_id,
            user_id=user_id,
            user_name=user_name,
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history

    def get_history(self, commission_id: int) -> List[CommissionHistory]:
        """Récupère l'historique d'une commission."""
        return self.db.query(CommissionHistory).filter(
            CommissionHistory.commission_id == commission_id
        ).order_by(CommissionHistory.created_at.desc()).all()

    def generate_alerts(self, commission_id: int):
        """Génère les alertes pour une commission."""
        commission = self.get_commission(commission_id)
        if not commission:
            return
        
        # Supprimer les anciennes alertes non résolues
        self.db.query(CommissionAlert).filter(
            CommissionAlert.commission_id == commission_id,
            CommissionAlert.is_resolved == False
        ).delete()
        
        # Alerte: Commission à constituer
        if commission.status == CommissionStatus.TO_BE_CONSTITUTED:
            alert = CommissionAlert(
                commission_id=commission_id,
                alert_type="to_be_constituted",
                severity="medium",
                title="Commission à constituer",
                message="La commission doit être constituée avec ses membres",
            )
            self.db.add(alert)
        
        # Alerte: Séance proche (dans les 3 jours)
        sessions = self.db.query(CommissionSession).filter(
            CommissionSession.commission_id == commission_id,
            CommissionSession.status == SessionStatus.PLANNED
        ).all()
        
        for session in sessions:
            if session.planned_date:
                days_until = (session.planned_date - datetime.utcnow()).days
                if days_until <= 3 and days_until >= 0:
                    alert = CommissionAlert(
                        commission_id=commission_id,
                        session_id=session.id,
                        alert_type="session_upcoming",
                        severity="high" if days_until <= 1 else "medium",
                        title=f"Séance {session.session_number} proche (" + str(days_until) + " jours)",
                        message=f"La séance {session.session_number} est prévue le {session.planned_date.strftime('%d/%m/%Y')}",
                    )
                    self.db.add(alert)
        
        # Alerte: Séance reportée
        postponed_sessions = self.db.query(CommissionSession).filter(
            CommissionSession.commission_id == commission_id,
            CommissionSession.status == SessionStatus.POSTPONED
        ).all()
        
        for session in postponed_sessions:
            alert = CommissionAlert(
                commission_id=commission_id,
                session_id=session.id,
                alert_type="session_postponed",
                severity="high",
                title=f"Séance {session.session_number} reportée",
                message=f"La séance {session.session_number} a été reportée. Nouvelle date: {session.postponed_to.strftime('%d/%m/%Y') if session.postponed_to else 'Non définie'}",
            )
            self.db.add(alert)
        
        # Alerte: PV manquant pour les séances clôturées
        closed_sessions = self.db.query(CommissionSession).filter(
            CommissionSession.commission_id == commission_id,
            CommissionSession.status == SessionStatus.CLOSED,
            CommissionSession.pv_generated == False
        ).all()
        
        for session in closed_sessions:
            alert = CommissionAlert(
                commission_id=commission_id,
                session_id=session.id,
                alert_type="pv_missing",
                severity="high",
                title=f"PV manquant pour séance {session.session_number}",
                message=f"La séance {session.session_number} est clôturée mais le PV n'a pas été généré",
            )
            self.db.add(alert)
        
        self.db.commit()

    def get_alerts(self, commission_id: int) -> List[CommissionAlert]:
        """Récupère les alertes d'une commission."""
        return self.db.query(CommissionAlert).filter(
            CommissionAlert.commission_id == commission_id,
            CommissionAlert.is_resolved == False
        ).order_by(CommissionAlert.created_at.desc()).all()

    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Résout une alerte."""
        alert = self.db.query(CommissionAlert).filter(
            CommissionAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        
        self.db.commit()
        
        return True

    def get_statistics(self) -> Dict:
        """Calcule les statistiques des commissions."""
        total = self.db.query(Commission).filter(
            Commission.is_deleted == False
        ).count()
        
        by_status = {}
        for status in CommissionStatus:
            count = self.db.query(Commission).filter(
                Commission.status == status,
                Commission.is_deleted == False
            ).count()
            by_status[status.value] = count
        
        total_sessions = self.db.query(CommissionSession).count()
        
        sessions_by_status = {}
        for status in SessionStatus:
            count = self.db.query(CommissionSession).filter(
                CommissionSession.status == status
            ).count()
            sessions_by_status[status.value] = count
        
        return {
            "total": total,
            "by_status": by_status,
            "total_sessions": total_sessions,
            "sessions_by_status": sessions_by_status,
        }


def get_commission_service(db: Session) -> CommissionService:
    """Factory function pour obtenir une instance de CommissionService."""
    return CommissionService(db)

"""
Service métier pour la gestion des publications
Module 5: Publication de l'avis et lancement de la consultation
Relation: 1 commission → plusieurs publications
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.models.publication import (
    Publication,
    PublicationSupport,
    PublicationDeadline,
    PublicationAlert,
    PublicationHistory,
    PublicationType,
    PublicationStatus,
    ProcedureType,
    SupportType,
)
from app.models.commission import Commission, CommissionStatus
from app.models.user import User


class PublicationService:
    """Service de gestion des publications"""

    SORTABLE_FIELDS = {
        "publication_number": Publication.publication_number,
        "object": Publication.object,
        "status": Publication.status,
        "publication_date": Publication.publication_date,
        "submission_deadline": Publication.submission_deadline,
        "created_at": Publication.created_at,
    }

    def __init__(self, db: Session):
        self.db = db

    def generate_publication_number(self) -> str:
        """Génère un numéro de publication unique."""
        count = self.db.query(Publication).count()
        return f"PUB-{datetime.now().year}-{count + 1:04d}"

    def create_publication(
        self,
        commission_id: int,
        data: Dict,
        user_id: int,
    ) -> Publication:
        """Crée une nouvelle publication à partir d'une commission clôturée."""
        # Vérifier que la commission existe et est clôturée
        commission = self.db.query(Commission).filter(
            Commission.id == commission_id
        ).first()
        
        if not commission:
            raise ValueError("Commission non trouvée")
        
        if commission.status != CommissionStatus.COMMISSION_CLOSED:
            raise ValueError("La commission doit être clôturée pour créer une publication")
        
        # Créer la publication
        publication = Publication(
            commission_id=commission_id,
            publication_number=data.get("publication_number") or self.generate_publication_number(),
            publication_type=data.get("publication_type", PublicationType.INITIAL),
            notice_number=data.get("notice_number"),
            object=data.get("object"),
            procedure_type=data.get("procedure_type"),
            contracting_authority=data.get("contracting_authority"),
            estimated_amount=data.get("estimated_amount"),
            currency=data.get("currency", "MAD"),
            publication_date=data.get("publication_date"),
            submission_deadline=data["submission_deadline"],
            bid_opening_date=data["bid_opening_date"],
            bid_opening_time=data.get("bid_opening_time"),
            submission_delay_days=data.get("submission_delay_days"),
            status=PublicationStatus.DRAFT,
            observations=data.get("observations"),
            created_by=user_id,
        )
        
        self.db.add(publication)
        self.db.commit()
        self.db.refresh(publication)
        
        # Ajouter les supports si fournis
        supports_data = data.get("supports", [])
        for support_data in supports_data:
            self.add_support(publication.id, support_data, user_id)
        
        # Créer les échéances automatiques
        self.create_default_deadlines(publication.id, data, user_id)
        
        # Ajouter l'historique
        self.add_history(
            publication.id,
            "Création",
            f"Création de la publication pour la commission {commission_id}",
            user_id,
        )
        
        # Générer les alertes initiales
        self.generate_alerts(publication.id)
        
        return publication

    def get_publication(self, publication_id: int) -> Optional[Publication]:
        """Récupère une publication par ID."""
        return self.db.query(Publication).filter(
            Publication.id == publication_id,
            Publication.is_deleted == False
        ).first()

    def get_publications_by_commission(self, commission_id: int) -> List[Publication]:
        """Récupère toutes les publications d'une commission."""
        return self.db.query(Publication).filter(
            Publication.commission_id == commission_id,
            Publication.is_deleted == False
        ).order_by(Publication.created_at.desc()).all()

    def list_publications(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[PublicationStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Publication], int]:
        """Liste paginée avec recherche, filtres et tri."""
        query = self.db.query(Publication).filter(
            Publication.is_deleted == False
        )

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Publication.publication_number.ilike(term),
                    Publication.object.ilike(term),
                    Publication.notice_number.ilike(term),
                )
            )

        if status:
            query = query.filter(Publication.status == status)

        sort_column = self.SORTABLE_FIELDS.get(sort_by, Publication.created_at)
        order_fn = desc if sort_order.lower() == "desc" else asc
        query = query.order_by(order_fn(sort_column))

        total = query.count()
        publications = query.offset(skip).limit(limit).all()

        return publications, total

    def update_publication(
        self,
        publication_id: int,
        data: Dict,
        user_id: int,
    ) -> Publication:
        """Met à jour une publication."""
        publication = self.get_publication(publication_id)
        
        if not publication:
            raise ValueError("Publication non trouvée")
        
        # Mise à jour des champs
        for field, value in data.items():
            if hasattr(publication, field) and value is not None:
                setattr(publication, field, value)
        
        publication.updated_by = user_id
        publication.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(publication)
        
        # Ajouter l'historique
        self.add_history(
            publication.id,
            "Modification",
            "Mise à jour de la publication",
            user_id,
        )
        
        # Régénérer les alertes
        self.generate_alerts(publication_id)
        
        return publication

    def delete_publication(
        self,
        publication_id: int,
        user_id: int,
    ) -> bool:
        """Suppression logique d'une publication."""
        publication = self.get_publication(publication_id)
        
        if not publication:
            raise ValueError("Publication non trouvée")
        
        publication.is_deleted = True
        publication.deleted_at = datetime.utcnow()
        publication.deleted_by = user_id
        
        self.db.commit()
        
        # Ajouter l'historique
        self.add_history(
            publication.id,
            "Suppression",
            "Suppression de la publication",
            user_id,
        )
        
        return True

    def add_support(
        self,
        publication_id: int,
        data: Dict,
        user_id: int,
    ) -> PublicationSupport:
        """Ajoute un support de publication."""
        publication = self.get_publication(publication_id)
        
        if not publication:
            raise ValueError("Publication non trouvée")
        
        support = PublicationSupport(
            publication_id=publication_id,
            support_type=data["support_type"],
            support_name=data.get("support_name"),
            publication_date=data.get("publication_date"),
            reference=data.get("reference"),
            cost=data.get("cost"),
        )
        
        self.db.add(support)
        self.db.commit()
        self.db.refresh(support)
        
        # Ajouter l'historique
        self.add_history(
            publication_id,
            "Ajout support",
            f"Ajout du support {data['support_type'].value}",
            user_id,
        )
        
        return support

    def create_default_deadlines(
        self,
        publication_id: int,
        data: Dict,
        user_id: int,
    ):
        """Crée les échéances par défaut pour une publication."""
        submission_deadline = data.get("submission_deadline")
        bid_opening_date = data.get("bid_opening_date")
        bid_opening_time = data.get("bid_opening_time")
        
        if submission_deadline:
            deadline = PublicationDeadline(
                publication_id=publication_id,
                deadline_type="remise_offres",
                description="Délai de remise des offres",
                deadline_date=submission_deadline,
                deadline_time=None,
            )
            self.db.add(deadline)
        
        if bid_opening_date:
            deadline = PublicationDeadline(
                publication_id=publication_id,
                deadline_type="ouverture_plis",
                description="Ouverture des plis",
                deadline_date=bid_opening_date,
                deadline_time=bid_opening_time,
            )
            self.db.add(deadline)
        
        if data.get("publication_date"):
            deadline = PublicationDeadline(
                publication_id=publication_id,
                deadline_type="publication",
                description="Date de publication",
                deadline_date=data["publication_date"],
                deadline_time=None,
            )
            self.db.add(deadline)
        
        self.db.commit()

    def update_deadline(
        self,
        deadline_id: int,
        data: Dict,
        user_id: int,
    ) -> PublicationDeadline:
        """Met à jour une échéance."""
        deadline = self.db.query(PublicationDeadline).filter(
            PublicationDeadline.id == deadline_id
        ).first()
        
        if not deadline:
            raise ValueError("Échéance non trouvée")
        
        for field, value in data.items():
            if hasattr(deadline, field) and value is not None:
                setattr(deadline, field, value)
        
        deadline.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(deadline)
        
        # Ajouter l'historique
        self.add_history(
            deadline.publication_id,
            "Modification échéance",
            f"Mise à jour de l'échéance {deadline.deadline_type}",
            user_id,
        )
        
        return deadline

    def update_status(
        self,
        publication_id: int,
        status: PublicationStatus,
        user_id: int,
    ) -> Publication:
        """Met à jour le statut d'une publication."""
        publication = self.get_publication(publication_id)
        
        if not publication:
            raise ValueError("Publication non trouvée")
        
        old_status = publication.status
        publication.status = status
        publication.updated_by = user_id
        publication.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(publication)
        
        # Ajouter l'historique
        self.add_history(
            publication_id,
            "Changement statut",
            f"Statut: {old_status.value} → {status.value}",
            user_id,
            status_change=status.value,
        )
        
        # Régénérer les alertes
        self.generate_alerts(publication_id)
        
        return publication

    def add_history(
        self,
        publication_id: int,
        action: str,
        description: Optional[str],
        user_id: int,
        status_change: Optional[str] = None,
    ) -> PublicationHistory:
        """Ajoute une entrée à l'historique."""
        from app.models.user import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user else "Inconnu"
        
        history = PublicationHistory(
            publication_id=publication_id,
            action=action,
            description=description,
            status_change=status_change,
            user_id=user_id,
            user_name=user_name,
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history

    def get_history(self, publication_id: int) -> List[PublicationHistory]:
        """Récupère l'historique d'une publication."""
        return self.db.query(PublicationHistory).filter(
            PublicationHistory.publication_id == publication_id
        ).order_by(PublicationHistory.created_at.desc()).all()

    def generate_alerts(self, publication_id: int):
        """Génère les alertes pour une publication."""
        publication = self.get_publication(publication_id)
        if not publication:
            return
        
        # Supprimer les anciennes alertes non résolues
        self.db.query(PublicationAlert).filter(
            PublicationAlert.publication_id == publication_id,
            PublicationAlert.is_resolved == False
        ).delete()
        
        # Alerte: Publication en brouillon
        if publication.status == PublicationStatus.DRAFT:
            alert = PublicationAlert(
                publication_id=publication_id,
                alert_type="draft",
                severity="medium",
                title="Publication en brouillon",
                message="La publication est en brouillon et doit être finalisée",
            )
            self.db.add(alert)
        
        # Alerte: Informations manquantes
        missing_info = []
        if not publication.notice_number:
            missing_info.append("Numéro d'avis")
        if not publication.contracting_authority:
            missing_info.append("Maître d'ouvrage")
        if not publication.estimated_amount:
            missing_info.append("Montant estimé")
        
        if missing_info:
            alert = PublicationAlert(
                publication_id=publication_id,
                alert_type="missing_info",
                severity="high",
                title="Informations manquantes",
                message=f"Les informations suivantes sont manquantes: {', '.join(missing_info)}",
            )
            self.db.add(alert)
        
        # Alertes sur les échéances
        deadlines = self.db.query(PublicationDeadline).filter(
            PublicationDeadline.publication_id == publication_id
        ).all()
        
        for deadline in deadlines:
            if deadline.deadline_date:
                days_until = (deadline.deadline_date - datetime.utcnow()).days
                
                # Échéance proche (dans les 7 jours)
                if days_until <= 7 and days_until >= 0 and not deadline.is_completed:
                    severity = "critical" if days_until <= 2 else "high"
                    alert = PublicationAlert(
                        publication_id=publication_id,
                        deadline_id=deadline.id,
                        alert_type="deadline_approaching",
                        severity=severity,
                        title=f"Échéance proche: {deadline.description}",
                        message=f"{deadline.description} dans {days_until} jours ({deadline.deadline_date.strftime('%d/%m/%Y')})",
                    )
                    self.db.add(alert)
                
                # Échéance dépassée
                elif days_until < 0 and not deadline.is_completed:
                    alert = PublicationAlert(
                        publication_id=publication_id,
                        deadline_id=deadline.id,
                        alert_type="deadline_missed",
                        severity="critical",
                        title=f"Échéance dépassée: {deadline.description}",
                        message=f"{deadline.description} était prévue le {deadline.deadline_date.strftime('%d/%m/%Y')}",
                    )
                    self.db.add(alert)
        
        self.db.commit()

    def get_alerts(self, publication_id: int) -> List[PublicationAlert]:
        """Récupère les alertes d'une publication."""
        return self.db.query(PublicationAlert).filter(
            PublicationAlert.publication_id == publication_id,
            PublicationAlert.is_resolved == False
        ).order_by(PublicationAlert.created_at.desc()).all()

    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Résout une alerte."""
        alert = self.db.query(PublicationAlert).filter(
            PublicationAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alerte non trouvée")
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        
        self.db.commit()
        
        return True

    def get_statistics(self) -> Dict:
        """Calcule les statistiques des publications."""
        total = self.db.query(Publication).filter(
            Publication.is_deleted == False
        ).count()
        
        by_status = {}
        for status in PublicationStatus:
            count = self.db.query(Publication).filter(
                Publication.status == status,
                Publication.is_deleted == False
            ).count()
            by_status[status.value] = count
        
        by_type = {}
        for pub_type in PublicationType:
            count = self.db.query(Publication).filter(
                Publication.publication_type == pub_type,
                Publication.is_deleted == False
            ).count()
            by_type[pub_type.value] = count
        
        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
        }

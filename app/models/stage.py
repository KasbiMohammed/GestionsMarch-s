"""
Modèles pour la gestion des étapes des marchés publics
"""

import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StageStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class StageCategory(str, enum.Enum):
    ADMINISTRATIVE = "administrative"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    JURIDICAL = "juridical"
    EXECUTION = "execution"


class Stage(Base):
    __tablename__ = "stages"

    id = Column(Integer, primary_key=True, index=True)

    market_id = Column(
        Integer,
        ForeignKey("markets.id"),
        nullable=False,
    )

    # Informations
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, index=True)
    description = Column(Text)

    category = Column(Enum(StageCategory))
    order = Column(Integer, default=0)

    # Statut
    status = Column(
        Enum(StageStatus),
        default=StageStatus.NOT_STARTED,
    )

    is_completed = Column(Boolean, default=False)
    progress_percentage = Column(Integer, default=0)

    # Dates
    planned_date = Column(DateTime)
    actual_date = Column(DateTime)

    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Utilisateur responsable
    responsible_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    # Validation
    validated_by_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    validation_date = Column(DateTime)
    validation_notes = Column(Text)

    # Checklist
    checklist_items = Column(Text)
    completed_checklist_items = Column(Text)

    # Documents
    documents_required = Column(Text)
    documents_provided = Column(Text)

    # Commentaires
    observations = Column(Text)
    comments = Column(Text)

    # Retard
    is_late = Column(Boolean, default=False)
    delay_days = Column(Integer, default=0)
    alert_level = Column(String(20))

    # Validation
    is_validated = Column(Boolean, default=False)

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ======================
    # RELATIONS
    # ======================

    market = relationship(
        "Market",
        back_populates="stages",
    )

    responsible_user = relationship(
        "User",
        foreign_keys=[responsible_id],
        back_populates="stage_responsible",
    )

    validated_by = relationship(
        "User",
        foreign_keys=[validated_by_id],
        back_populates="validated_stages",
    )

    alerts = relationship(
        "Alert",
        back_populates="stage",
        cascade="all, delete-orphan",
    )

    @property
    def delay(self):
        if self.planned_date and self.actual_date:
            return (self.actual_date - self.planned_date).days
        return 0

    def calculate_delay(self):
        if self.planned_date and self.actual_date:
            self.delay_days = (
                self.actual_date - self.planned_date
            ).days

            self.is_late = self.delay_days > 0

            if self.delay_days <= 0:
                self.alert_level = "green"
            elif self.delay_days <= 7:
                self.alert_level = "orange"
            else:
                self.alert_level = "red"

    def __repr__(self):
        return f"<Stage {self.id} - {self.name}>"
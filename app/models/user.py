"""
Modèles pour la gestion des utilisateurs et des rôles
"""

import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    """Rôles des utilisateurs"""

    ADMINISTRATEUR = "administrateur"
    PRESIDENT = "president"
    DIRECTEUR_GENERAL_SERVICES = "directeur_general_services"
    SERVICE_MARCHES = "service_marches"
    SERVICE_TECHNIQUE = "service_technique"
    SERVICE_FINANCIER = "service_financier"
    COMPTABILITE = "comptabilite"
    CONTROLE_INTERNE = "controle_interne"
    CONSULTATION = "consultation"


class User(Base):
    """Modèle Utilisateur"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)

    hashed_password = Column(String(255), nullable=False)

    role = Column(
        Enum(UserRole),
        default=UserRole.CONSULTATION,
        nullable=False,
    )

    is_active = Column(Boolean, default=True)

    phone = Column(String(20))
    department = Column(String(100))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    last_login = Column(DateTime(timezone=True))

    # =====================================================
    # RELATIONS
    # =====================================================

    created_markets = relationship(
        "Market",
        foreign_keys="Market.created_by",
        back_populates="created_by_user",
    )

    modified_markets = relationship(
        "Market",
        foreign_keys="Market.modified_by",
        back_populates="modified_by_user",
    )

    stage_responsible = relationship(
        "Stage",
        foreign_keys="Stage.responsible_id",
        back_populates="responsible_user",
    )

    validated_stages = relationship(
        "Stage",
        foreign_keys="Stage.validated_by_id",
        back_populates="validated_by",
    )

    created_histories = relationship(
        "History",
        foreign_keys="History.user_id",
        back_populates="user",
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, "
            f"username='{self.username}', "
            f"role='{self.role.value}')>"
        )


class Role(Base):
    """Modèle des rôles"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    permissions = Column(Text)

    can_create_markets = Column(Boolean, default=False)
    can_edit_markets = Column(Boolean, default=False)
    can_delete_markets = Column(Boolean, default=False)
    can_validate_markets = Column(Boolean, default=False)
    can_view_all_markets = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_export_data = Column(Boolean, default=False)
    can_view_reports = Column(Boolean, default=True)
    can_manage_documents = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
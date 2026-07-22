"""
Gestion des permissions basée sur les rôles
Définition des droits d'accès pour chaque rôle
"""

from typing import Set
from app.models.user import UserRole


# Définition des permissions par rôle
ROLE_PERMISSIONS = {
    UserRole.ADMINISTRATEUR: {
        "create_markets", "edit_markets", "delete_markets", "validate_markets",
        "view_all_markets", "manage_users", "export_data", "view_reports",
        "manage_documents", "view_analytics", "manage_settings",
        "create_planning", "edit_planning", "delete_planning", "view_planning",
    },
    
    UserRole.PRESIDENT: {
        "view_all_markets", "validate_markets", "view_reports", "export_data",
        "view_analytics", "view_planning",
    },
    
    UserRole.DIRECTEUR_GENERAL_SERVICES: {
        "create_markets", "edit_markets", "validate_markets", "view_all_markets",
        "view_reports", "export_data", "manage_documents", "view_analytics",
        "create_planning", "edit_planning", "view_planning",
    },
    
    UserRole.SERVICE_MARCHES: {
        "create_markets", "edit_markets", "view_all_markets", "manage_documents",
        "view_reports", "export_data",
        "create_planning", "edit_planning", "delete_planning", "view_planning",
    },
    
    UserRole.SERVICE_TECHNIQUE: {
        "edit_markets", "view_all_markets", "validate_technical", "manage_documents",
        "view_reports", "create_planning", "edit_planning", "view_planning",
    },
    
    UserRole.SERVICE_FINANCIER: {
        "edit_markets", "view_all_markets", "validate_financial", "manage_documents",
        "view_reports", "export_data",
        "view_planning", "edit_planning",
    },
    
    UserRole.CONTROLE_INTERNE: {
        "view_all_markets", "view_reports", "export_data", "view_analytics",
        "view_planning",
    },
    
    UserRole.CONSULTATION: {
        "view_all_markets", "view_reports", "export_data", "view_planning",
    }
}


def has_permission(user_role: UserRole, permission: str) -> bool:
    """
    Vérifie si un rôle a une permission spécifique
    
    Args:
        user_role: Rôle de l'utilisateur
        permission: Permission à vérifier
        
    Returns:
        True si le rôle a la permission, False sinon
    """
    return permission in ROLE_PERMISSIONS.get(user_role, set())


def check_permission(user_role: UserRole, required_permissions: Set[str]) -> bool:
    """
    Vérifie si un rôle a toutes les permissions requises
    
    Args:
        user_role: Rôle de l'utilisateur
        required_permissions: Ensemble de permissions requises
        
    Returns:
        True si le rôle a toutes les permissions, False sinon
    """
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    return required_permissions.issubset(user_permissions)


def get_user_permissions(user_role: UserRole) -> Set[str]:
    """
    Récupère toutes les permissions d'un rôle
    
    Args:
        user_role: Rôle de l'utilisateur
        
    Returns:
        Ensemble des permissions du rôle
    """
    return ROLE_PERMISSIONS.get(user_role, set())


def can_create_market(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut créer des marchés"""
    return has_permission(user_role, "create_markets")


def can_edit_market(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut modifier des marchés"""
    return has_permission(user_role, "edit_markets")


def can_delete_market(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut supprimer des marchés"""
    return has_permission(user_role, "delete_markets")


def can_validate_market(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut valider des marchés"""
    return has_permission(user_role, "validate_markets")


def can_view_all_markets(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut voir tous les marchés"""
    return has_permission(user_role, "view_all_markets")


def can_manage_users(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut gérer les utilisateurs"""
    return has_permission(user_role, "manage_users")


def can_export_data(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut exporter des données"""
    return has_permission(user_role, "export_data")


def can_manage_documents(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut gérer les documents"""
    return has_permission(user_role, "manage_documents")


def can_create_planning(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut créer des planifications"""
    return has_permission(user_role, "create_planning")


def can_edit_planning(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut modifier des planifications"""
    return has_permission(user_role, "edit_planning")


def can_delete_planning(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut supprimer des planifications"""
    return has_permission(user_role, "delete_planning")


def can_view_planning(user_role: UserRole) -> bool:
    """Vérifie si l'utilisateur peut consulter les planifications"""
    return has_permission(user_role, "view_planning")

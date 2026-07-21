"""
Module d'authentification et d'autorisation
Gestion de la sécurité RBAC (Role-Based Access Control)
"""

from app.auth.dependencies import get_current_user, get_current_active_user, require_role
from app.auth.permissions import check_permission, has_permission
from app.utils.security import verify_password, get_password_hash, create_access_token

__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "require_role",
    "check_permission",
    "has_permission",
    "verify_password",
    "get_password_hash",
    "create_access_token",
]

"""
Service de gestion des utilisateurs et permissions
Module 13: Gestion utilisateurs - 9 profils avec permissions spécifiques
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User, UserRole


class UserPermissionService:
    """Service pour la gestion des utilisateurs et leurs permissions"""
    
    # Définition des permissions par rôle
    ROLE_PERMISSIONS = {
        UserRole.ADMINISTRATEUR: {
            'can_view_all_markets': True,
            'can_create_markets': True,
            'can_edit_markets': True,
            'can_delete_markets': True,
            'can_validate_markets': True,
            'can_manage_users': True,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': True,
            'can_manage_commissions': True,
            'can_approve_attribution': True,
            'can_view_all_alerts': True,
            'can_manage_workflow': True
        },
        UserRole.PRESIDENT: {
            'can_view_all_markets': True,
            'can_create_markets': False,
            'can_edit_markets': False,
            'can_delete_markets': False,
            'can_validate_markets': True,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': False,
            'can_manage_planning': True,
            'can_manage_commissions': False,
            'can_approve_attribution': True,
            'can_view_all_alerts': True,
            'can_manage_workflow': False
        },
        UserRole.DIRECTEUR_GENERAL_SERVICES: {
            'can_view_all_markets': True,
            'can_create_markets': True,
            'can_edit_markets': True,
            'can_delete_markets': False,
            'can_validate_markets': True,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': True,
            'can_manage_commissions': True,
            'can_approve_attribution': True,
            'can_view_all_alerts': True,
            'can_manage_workflow': True
        },
        UserRole.SERVICE_MARCHES: {
            'can_view_all_markets': True,
            'can_create_markets': True,
            'can_edit_markets': True,
            'can_delete_markets': False,
            'can_validate_markets': True,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': True,
            'can_manage_commissions': True,
            'can_approve_attribution': False,
            'can_view_all_alerts': True,
            'can_manage_workflow': True
        },
        UserRole.SERVICE_TECHNIQUE: {
            'can_view_all_markets': False,
            'can_create_markets': True,
            'can_edit_markets': True,
            'can_delete_markets': False,
            'can_validate_markets': True,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': True,
            'can_manage_commissions': True,
            'can_approve_attribution': False,
            'can_view_all_alerts': False,
            'can_manage_workflow': True
        },
        UserRole.SERVICE_FINANCIER: {
            'can_view_all_markets': True,
            'can_create_markets': False,
            'can_edit_markets': True,
            'can_delete_markets': False,
            'can_validate_markets': True,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': True,
            'can_manage_commissions': True,
            'can_approve_attribution': False,
            'can_view_all_alerts': True,
            'can_manage_workflow': True
        },
        UserRole.COMPTABILITE: {
            'can_view_all_markets': True,
            'can_create_markets': False,
            'can_edit_markets': False,
            'can_delete_markets': False,
            'can_validate_markets': False,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': False,
            'can_manage_commissions': False,
            'can_approve_attribution': False,
            'can_view_all_alerts': True,
            'can_manage_workflow': False
        },
        UserRole.CONTROLE_INTERNE: {
            'can_view_all_markets': True,
            'can_create_markets': False,
            'can_edit_markets': False,
            'can_delete_markets': False,
            'can_validate_markets': True,
            'can_manage_users': False,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_documents': True,
            'can_manage_planning': True,
            'can_manage_commissions': True,
            'can_approve_attribution': False,
            'can_view_all_alerts': True,
            'can_manage_workflow': False
        },
        UserRole.CONSULTATION: {
            'can_view_all_markets': False,
            'can_create_markets': False,
            'can_edit_markets': False,
            'can_delete_markets': False,
            'can_validate_markets': False,
            'can_manage_users': False,
            'can_export_data': False,
            'can_view_reports': True,
            'can_manage_documents': False,
            'can_manage_planning': False,
            'can_manage_commissions': False,
            'can_approve_attribution': False,
            'can_view_all_alerts': False,
            'can_manage_workflow': False
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_permissions(self, user_id: int) -> Dict:
        """
        Récupère les permissions d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Dictionnaire des permissions
        """
        user = self.db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        return self.ROLE_PERMISSIONS.get(user.role, {})
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique
        
        Args:
            user_id: ID de l'utilisateur
            permission: Permission à vérifier
            
        Returns:
            True si l'utilisateur a la permission
        """
        permissions = self.get_user_permissions(user_id)
        return permissions.get(permission, False)
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        Récupère les utilisateurs par rôle
        
        Args:
            role: Rôle à filtrer
            
        Returns:
            Liste des utilisateurs
        """
        return self.db.query(User).filter(
            User.role == role,
            User.is_active == True
        ).all()
    
    def get_accessible_markets(self, user_id: int) -> List[int]:
        """
        Récupère les IDs des marchés accessibles à un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des IDs de marchés accessibles
        """
        user = self.db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user:
            return []
        
        permissions = self.ROLE_PERMISSIONS.get(user.role, {})
        
        # Si l'utilisateur peut voir tous les marchés
        if permissions.get('can_view_all_markets'):
            from app.models.market import Market
            markets = self.db.query(Market.id).filter(
                Market.is_deleted == False
            ).all()
            return [m.id for m in markets]
        
        # Sinon, filtrer par service responsable (à implémenter selon la logique métier)
        # Pour l'instant, retourner une liste vide
        return []
    
    def can_validate_market(self, user_id: int) -> bool:
        """
        Vérifie si l'utilisateur peut valider des marchés
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            True si l'utilisateur peut valider
        """
        return self.has_permission(user_id, 'can_validate_markets')
    
    def can_approve_attribution(self, user_id: int) -> bool:
        """
        Vérifie si l'utilisateur peut approuver des attributions
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            True si l'utilisateur peut approuver
        """
        return self.has_permission(user_id, 'can_approve_attribution')
    
    def can_manage_users(self, user_id: int) -> bool:
        """
        Vérifie si l'utilisateur peut gérer les utilisateurs
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            True si l'utilisateur peut gérer les utilisateurs
        """
        return self.has_permission(user_id, 'can_manage_users')
    
    def get_role_description(self, role: UserRole) -> str:
        """
        Récupère la description d'un rôle
        
        Args:
            role: Rôle
            
        Returns:
            Description du rôle
        """
        descriptions = {
            UserRole.ADMINISTRATEUR: "Administrateur système - Accès complet à toutes les fonctionnalités",
            UserRole.PRESIDENT: "Président de la commune - Validation et approbation, vue d'ensemble",
            UserRole.DIRECTEUR_GENERAL_SERVICES: "Directeur Général des Services - Gestion opérationnelle complète",
            UserRole.SERVICE_MARCHES: "Service des Marchés Publics - Gestion complète des marchés",
            UserRole.SERVICE_TECHNIQUE: "Service Technique - Validation technique et suivi d'exécution",
            UserRole.SERVICE_FINANCIER: "Service Financier - Validation budgétaire et gestion des paiements",
            UserRole.COMPTABILITE: "Comptabilité - Suivi financier et comptable",
            UserRole.CONTROLE_INTERNE: "Contrôle Interne - Vérification et audit",
            UserRole.CONSULTATION: "Consultation - Accès en lecture seule aux informations"
        }
        
        return descriptions.get(role, "Rôle non défini")
    
    def get_all_roles(self) -> List[Dict]:
        """
        Récupère tous les rôles avec leurs descriptions
        
        Returns:
            Liste des rôles avec descriptions
        """
        return [
            {
                'value': role.value,
                'label': role.value.replace('_', ' ').title(),
                'description': self.get_role_description(role)
            }
            for role in UserRole
        ]
    
    def update_user_role(self, user_id: int, new_role: UserRole, updated_by: int) -> User:
        """
        Met à jour le rôle d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            new_role: Nouveau rôle
            updated_by: ID de l'utilisateur effectuant la modification
            
        Returns:
            Instance de User mise à jour
        """
        if not self.can_manage_users(updated_by):
            raise PermissionError("Vous n'avez pas la permission de gérer les utilisateurs")
        
        user = self.db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        user.role = new_role
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user_id: int, deactivated_by: int) -> User:
        """
        Désactive un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            deactivated_by: ID de l'utilisateur effectuant la désactivation
            
        Returns:
            Instance de User désactivée
        """
        if not self.can_manage_users(deactivated_by):
            raise PermissionError("Vous n'avez pas la permission de gérer les utilisateurs")
        
        user = self.db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def activate_user(self, user_id: int, activated_by: int) -> User:
        """
        Active un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            activated_by: ID de l'utilisateur effectuant l'activation
            
        Returns:
            Instance de User activée
        """
        if not self.can_manage_users(activated_by):
            raise PermissionError("Vous n'avez pas la permission de gérer les utilisateurs")
        
        user = self.db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user


def get_user_permission_service(db: Session) -> UserPermissionService:
    """
    Factory pour créer une instance du service de permissions utilisateur
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de UserPermissionService
    """
    return UserPermissionService(db)

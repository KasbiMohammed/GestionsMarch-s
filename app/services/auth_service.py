"""
Service d'authentification
Gestion de l'authentification et des tokens JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.utils.security import verify_password, get_password_hash


class AuthService:
    """Service pour la gestion de l'authentification"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur avec son nom d'utilisateur et mot de passe
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe en clair
            
        Returns:
            Utilisateur authentifié ou None
        """
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crée un token JWT d'accès
        
        Args:
            data: Données à encoder dans le token
            expires_delta: Durée de validité personnalisée
            
        Returns:
            Token JWT encodé
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Vérifie et décode un token JWT
        
        Args:
            token: Token JWT à vérifier
            
        Returns:
            Données décodées ou None si invalide
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Récupère un utilisateur à partir d'un token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Utilisateur correspondant ou None
        """
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = self.db.query(User).filter(User.username == username).first()
        return user
    
    def create_user(self, username: str, email: str, password: str, role: str, 
                    full_name: str = None, phone: str = None) -> User:
        """
        Crée un nouvel utilisateur
        
        Args:
            username: Nom d'utilisateur unique
            email: Adresse email
            password: Mot de passe en clair
            role: Rôle de l'utilisateur
            full_name: Nom complet
            phone: Numéro de téléphone
            
        Returns:
            Utilisateur créé
        """
        # Vérifier si l'utilisateur existe déjà
        existing_user = self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("Un utilisateur avec ce nom d'utilisateur ou email existe déjà")
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            full_name=full_name,
            phone=phone,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Met à jour les informations d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            **kwargs: Champs à mettre à jour
            
        Returns:
            Utilisateur mis à jour ou None
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and key != 'id':
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change le mot de passe d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            old_password: Ancien mot de passe
            new_password: Nouveau mot de passe
            
        Returns:
            True si succès, False sinon
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not verify_password(old_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Désactive un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            True si succès, False sinon
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True


def get_auth_service(db: Session) -> AuthService:
    """
    Factory pour créer une instance du service d'authentification
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de AuthService
    """
    return AuthService(db)

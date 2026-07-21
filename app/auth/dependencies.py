"""
Dépendances d'authentification FastAPI
Utilisées pour protéger les routes API
"""

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_access_token
from app.schemas.user import TokenData

# Schéma OAuth2 pour l'authentification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """
    Récupère l'utilisateur actuel à partir d'un token
    
    Args:
        token: Token JWT
        db: Session de base de données
        
    Returns:
        Utilisateur si le token est valide, None sinon
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
            
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            return None
            
        token_data = TokenData(username=username, role=UserRole(role) if role else None)
    except Exception:
        return None
    
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if user is None:
        return None
        
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance pour récupérer l'utilisateur actuel depuis le header Authorization
    
    Args:
        token: Token JWT depuis le header Authorization
        db: Session de base de données
        
    Returns:
        Utilisateur actuel
        
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    user = await get_current_user_from_token(token, db)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Récupère l'utilisateur actuel depuis un cookie
    
    Args:
        access_token: Token depuis le cookie
        db: Session de base de données
        
    Returns:
        Utilisateur si connecté, None sinon
    """
    if not access_token:
        return None
        
    return await get_current_user_from_token(access_token, db)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dépendance pour récupérer l'utilisateur actif
    
    Args:
        current_user: Utilisateur actuel
        
    Returns:
        Utilisateur actif
        
    Raises:
        HTTPException: Si l'utilisateur est inactif
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Décorateur pour restreindre l'accès à certains rôles
    
    Args:
        *allowed_roles: Rôles autorisés
        
    Returns:
        Fonction de dépendance FastAPI
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    return role_checker

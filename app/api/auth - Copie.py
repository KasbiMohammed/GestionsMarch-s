"""
API d'authentification
Endpoints pour la connexion, inscription et gestion des tokens
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.utils.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Créer un nouvel utilisateur."""

    existing_user = (
        db.query(User)
        .filter(
            (User.username == user_data.username)
            | (User.email == user_data.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        phone=user_data.phone,
        department=user_data.department,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Connexion via formulaire OAuth2."""

    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user",
        )

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
        },
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login/json", response_model=Token)
async def login_json(
    response: Response,
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Connexion via JSON."""

    user = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user",
        )

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
        },
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )
    

    response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=False,      # pour que App.getCookie() puisse le lire
    secure=False,        # localhost
    samesite="Lax",
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout")
async def logout(response: Response):
    """Déconnexion."""

    response.delete_cookie("access_token")

    return {
        "message": "Successfully logged out"
    }


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
):
    """Retourne l'utilisateur connecté."""

    return current_user


def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """
    Récupère l'utilisateur à partir d'un token d'accès
    
    Args:
        token: Token d'accès JWT
        db: Session de base de données
        
    Returns:
        Utilisateur correspondant au token ou None
    """
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        username = payload.get("sub")
        if username is None:
            return None
        
        user = db.query(User).filter(User.username == username).first()
        return user
    except Exception:
        return None
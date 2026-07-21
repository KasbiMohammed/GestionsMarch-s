"""
Schémas pour la gestion des utilisateurs
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema pour utilisateur"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    department: Optional[str] = None


class UserCreate(UserBase):
    """Schema pour la création d'utilisateur"""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.CONSULTATION


class UserUpdate(BaseModel):
    """Schema pour la mise à jour d'utilisateur"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """Schema pour la connexion"""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema pour la réponse utilisateur"""
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema pour le token JWT"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema pour les données du token"""
    username: Optional[str] = None
    role: Optional[UserRole] = None

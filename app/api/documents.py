"""
API de gestion des documents
Endpoints pour l'upload, le téléchargement et la gestion des documents
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import hashlib
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse
from app.auth.dependencies import get_current_active_user
from app.config import settings

router = APIRouter()


@router.get("/market/{market_id}", response_model=List[DocumentResponse])
async def get_market_documents(
    market_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les documents d'un marché
    
    Args:
        market_id: ID du marché
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des documents du marché
    """
    documents = db.query(Document).filter(
        Document.market_id == market_id,
        Document.is_current_version == True
    ).order_by(Document.upload_date.desc()).all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère un document par son ID
    
    Args:
        document_id: ID du document
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Document demandé
        
    Raises:
        HTTPException: Si le document n'existe pas
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    market_id: int,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    document_type: Optional[str] = None,
    category: Optional[str] = None,
    stage_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload un nouveau document
    
    Args:
        market_id: ID du marché
        file: Fichier à uploader
        name: Nom du document (optionnel, utilise le nom du fichier par défaut)
        description: Description du document
        document_type: Type de document
        category: Catégorie du document
        stage_id: ID de l'étape associée (optionnel)
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Document créé
    """
    from app.models.market import Market
    
    # Vérifier si le marché existe
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Vérifier la taille du fichier
    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Créer le répertoire de marché si nécessaire
    market_dir = os.path.join(settings.UPLOAD_DIR, f"market_{market_id}")
    os.makedirs(market_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(market_dir, safe_filename)
    
    # Calculer le hash du fichier
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Sauvegarder le fichier
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Créer le document
    db_document = Document(
        market_id=market_id,
        stage_id=stage_id,
        name=name or file.filename,
        description=description,
        document_type=document_type,
        category=category,
        file_name=file.filename,
        file_path=file_path,
        file_size=len(file_content),
        file_type=file.content_type,
        file_hash=file_hash,
        uploaded_by=current_user.id
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Télécharge un document
    
    Args:
        document_id: ID du document
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier à télécharger
        
    Raises:
        HTTPException: Si le document n'existe pas
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type=document.file_type
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour les métadonnées d'un document
    
    Args:
        document_id: ID du document
        document_update: Données de mise à jour
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Document mis à jour
        
    Raises:
        HTTPException: Si le document n'existe pas
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Mise à jour des champs
    update_data = document_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un document
    
    Args:
        document_id: ID du document
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Raises:
        HTTPException: Si le document n'existe pas
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Supprimer le fichier physique
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Supprimer de la base de données
    db.delete(document)
    db.commit()
    
    return None

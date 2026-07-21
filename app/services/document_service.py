"""
Service de gestion documentaire
Module 10: Gestion documentaire
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import hashlib
import os

from app.models.document import Document
from app.models.document_management import (
    DocumentVersion, DocumentAccess, DocumentCategory
)
from app.utils.file_utils import generate_unique_filename, validate_file_upload


class DocumentService:
    """Service pour la gestion des documents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def upload_document(self, document_data: dict, user_id: int) -> Document:
        """
        Upload un document
        
        Args:
            document_data: Données du document
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Document créée
        """
        # Valider le fichier
        file_path = document_data['file_path']
        if not os.path.exists(file_path):
            raise ValueError("Fichier non trouvé")
        
        # Calculer le hash du fichier
        file_hash = self._calculate_file_hash(file_path)
        
        # Créer le document
        document = Document(
            market_id=document_data.get('market_id'),
            stage_id=document_data.get('stage_id'),
            name=document_data['name'],
            description=document_data.get('description'),
            category=document_data.get('category'),
            file_path=file_path,
            file_name=document_data['file_name'],
            file_type=document_data.get('file_type'),
            file_size=document_data.get('file_size'),
            file_hash=file_hash,
            version=1,
            is_final=document_data.get('is_final', False),
            is_confidential=document_data.get('is_confidential', False),
            uploaded_by=user_id,
            uploaded_at=datetime.utcnow()
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Créer la version initiale
        self._create_document_version(document.id, file_path, file_hash, user_id)
        
        return document
    
    def create_new_version(self, document_id: int, file_path: str, change_description: str, user_id: int) -> Document:
        """
        Crée une nouvelle version d'un document
        
        Args:
            document_id: ID du document
            file_path: Chemin du nouveau fichier
            change_description: Description des changements
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Document mise à jour
        """
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document non trouvé")
        
        # Calculer le hash du nouveau fichier
        file_hash = self._calculate_file_hash(file_path)
        
        # Sauvegarder l'ancien fichier comme version
        self._create_document_version(document_id, document.file_path, document.file_hash, user_id)
        
        # Mettre à jour le document
        document.file_path = file_path
        document.file_hash = file_hash
        document.version += 1
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        # Créer la nouvelle version
        self._create_document_version(document_id, file_path, file_hash, user_id, change_description)
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def grant_access(self, document_id: int, user_id: int, permissions: dict, granted_by: int) -> DocumentAccess:
        """
        Accorde l'accès à un document
        
        Args:
            document_id: ID du document
            user_id: ID de l'utilisateur
            permissions: Dictionnaire des permissions
            granted_by: ID de l'utilisateur qui accorde l'accès
            
        Returns:
            Instance de DocumentAccess créée
        """
        # Vérifier si l'accès existe déjà
        existing_access = self.db.query(DocumentAccess).filter(
            and_(
                DocumentAccess.document_id == document_id,
                DocumentAccess.user_id == user_id
            )
        ).first()
        
        if existing_access:
            # Mettre à jour les permissions
            existing_access.can_view = permissions.get('can_view', True)
            existing_access.can_download = permissions.get('can_download', True)
            existing_access.can_edit = permissions.get('can_edit', False)
            existing_access.can_delete = permissions.get('can_delete', False)
            existing_access.granted_by = granted_by
            existing_access.granted_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_access)
            
            return existing_access
        else:
            # Créer un nouvel accès
            access = DocumentAccess(
                document_id=document_id,
                user_id=user_id,
                can_view=permissions.get('can_view', True),
                can_download=permissions.get('can_download', True),
                can_edit=permissions.get('can_edit', False),
                can_delete=permissions.get('can_delete', False),
                granted_by=granted_by,
                granted_at=datetime.utcnow()
            )
            
            self.db.add(access)
            self.db.commit()
            self.db.refresh(access)
            
            return access
    
    def mark_as_final(self, document_id: int, user_id: int) -> Document:
        """
        Marque un document comme final
        
        Args:
            document_id: ID du document
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Document marquée comme finale
        """
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document non trouvé")
        
        document.is_final = True
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def validate_document(self, document_id: int, validator_id: int, validation_comments: str = None) -> Document:
        """
        Valide un document
        
        Args:
            document_id: ID du document
            validator_id: ID du validateur
            validation_comments: Commentaires de validation
            
        Returns:
            Instance de Document validée
        """
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document non trouvé")
        
        document.validated = True
        document.validated_by = validator_id
        document.validated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def get_documents_by_market(self, market_id: int, category: DocumentCategory = None) -> List[Document]:
        """
        Récupère les documents d'un marché
        
        Args:
            market_id: ID du marché
            category: Catégorie optionnelle
            
        Returns:
            Liste des documents
        """
        query = self.db.query(Document).filter(
            Document.market_id == market_id
        )
        
        if category:
            query = query.filter(Document.category == category)
        
        return query.order_by(Document.uploaded_at.desc()).all()
    
    def get_documents_by_stage(self, stage_id: int) -> List[Document]:
        """
        Récupère les documents d'une étape
        
        Args:
            stage_id: ID de l'étape
            
        Returns:
            Liste des documents
        """
        return self.db.query(Document).filter(
            Document.stage_id == stage_id
        ).order_by(Document.uploaded_at.desc()).all()
    
    def get_document_versions(self, document_id: int) -> List[DocumentVersion]:
        """
        Récupère les versions d'un document
        
        Args:
            document_id: ID du document
            
        Returns:
            Liste des versions
        """
        return self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number).all()
    
    def delete_document(self, document_id: int, user_id: int) -> bool:
        """
        Supprime un document
        
        Args:
            document_id: ID du document
            user_id: ID de l'utilisateur
            
        Returns:
            True si supprimé
        """
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document non trouvé")
        
        if document.is_final:
            raise ValueError("Impossible de supprimer un document final")
        
        # Supprimer le fichier physique
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Supprimer les versions
        versions = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).all()
        
        for version in versions:
            self.db.delete(version)
        
        # Supprimer les accès
        accesses = self.db.query(DocumentAccess).filter(
            DocumentAccess.document_id == document_id
        ).all()
        
        for access in accesses:
            self.db.delete(access)
        
        # Supprimer le document
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcule le hash SHA256 d'un fichier"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _create_document_version(self, document_id: int, file_path: str, file_hash: str, user_id: int, change_description: str = None):
        """Crée une version de document"""
        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        version = DocumentVersion(
            document_id=document_id,
            version_number=document.version,
            change_description=change_description,
            file_path=file_path,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else None,
            file_hash=file_hash,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(version)
        self.db.commit()


def get_document_service(db: Session) -> DocumentService:
    """
    Factory pour créer une instance du service de documents
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de DocumentService
    """
    return DocumentService(db)

"""
API endpoints pour la Base de connaissances réglementaire
Module dédié - ne modifie pas les fonctionnalités existantes
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.services.regulatory_import_service import RegulatoryImportService, RegulatoryIndexingService
from app.services.regulatory_search_service import RegulatorySearchService, RegulatoryComplianceService
from app.models.regulatory_knowledge import (
    RegulatoryDocument, Chapter, Article, Keyword,
    DocumentType, Theme
)
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(tags=["Regulatory Knowledge"])


# ============================================
# ENDPOINTS POUR LES DOCUMENTS
# ============================================

@router.get("/documents", response_model=List[dict])
def get_documents(
    document_type: Optional[str] = None,
    theme: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère la liste des documents réglementaires
    """
    query = db.query(RegulatoryDocument).filter(RegulatoryDocument.is_active == True)
    
    if document_type:
        query = query.filter(RegulatoryDocument.document_type == document_type)
    
    if theme:
        from app.models.regulatory_knowledge import DocumentTheme
        query = query.join(DocumentTheme).filter(DocumentTheme.theme == theme)
    
    documents = query.limit(limit).all()
    
    return [{
        'id': doc.id,
        'document_type': doc.document_type,
        'reference': doc.reference,
        'title': doc.title,
        'description': doc.description,
        'publication_date': doc.publication_date.isoformat() if doc.publication_date else None,
        'effective_date': doc.effective_date.isoformat() if doc.effective_date else None,
        'issuer': doc.issuer,
        'url': doc.url
    } for doc in documents]


@router.get("/documents/{document_id}", response_model=dict)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un document avec ses chapitres et articles
    """
    search_service = RegulatorySearchService(db)
    document = search_service.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return document


@router.post("/documents/import", response_model=dict)
def import_document(
    file: UploadFile = File(...),
    document_type: str = DocumentType.AUTRE.value,
    reference: str = None,
    title: str = None,
    description: Optional[str] = None,
    publication_date: Optional[str] = None,
    effective_date: Optional[str] = None,
    issuer: Optional[str] = None,
    url: Optional[str] = None,
    keywords: Optional[str] = None,
    themes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Importe un document réglementaire
    """
    import_service = RegulatoryImportService(db)
    
    # Sauvegarder le fichier
    import os
    upload_dir = "uploads/regulatory"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    # Parser les mots-clés et thèmes
    keyword_list = keywords.split(',') if keywords else None
    theme_list = [Theme(t.strip()) for t in themes.split(',')] if themes else None
    
    # Importer le document
    document = import_service.import_document(
        file_path=file_path,
        document_type=DocumentType(document_type),
        reference=reference or file.filename,
        title=title or file.filename,
        description=description,
        publication_date=datetime.fromisoformat(publication_date) if publication_date else None,
        effective_date=datetime.fromisoformat(effective_date) if effective_date else None,
        issuer=issuer,
        url=url,
        keywords=keyword_list,
        themes=theme_list
    )
    
    # Indexer le document
    indexing_service = RegulatoryIndexingService(db)
    indexing_service.index_document(document.id)
    
    return {
        'id': document.id,
        'reference': document.reference,
        'title': document.title,
        'message': 'Document importé avec succès'
    }


@router.delete("/documents/{document_id}", response_model=dict)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un document (désactivation)
    """
    document = db.query(RegulatoryDocument).filter(
        RegulatoryDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    document.is_active = False
    db.commit()
    
    return {'message': 'Document désactivé avec succès'}


# ============================================
# ENDPOINTS POUR LA RECHERCHE
# ============================================

@router.get("/search", response_model=List[dict])
def search(
    query: str,
    document_type: Optional[str] = None,
    theme: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche dans la base de connaissances
    """
    search_service = RegulatorySearchService(db)
    results = search_service.search(query, document_type, theme, limit)
    
    return results


@router.get("/search/keyword/{keyword}", response_model=List[dict])
def search_by_keyword(
    keyword: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche par mot-clé
    """
    search_service = RegulatorySearchService(db)
    results = search_service.search_by_keyword(keyword, limit)
    
    return results


@router.get("/articles/{article_id}", response_model=dict)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un article avec ses détails
    """
    search_service = RegulatorySearchService(db)
    article = search_service.get_article_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    return article


# ============================================
# ENDPOINTS POUR LES THÈMES
# ============================================

@router.get("/themes", response_model=List[str])
def get_themes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère tous les thèmes disponibles
    """
    search_service = RegulatorySearchService(db)
    themes = search_service.get_all_themes()
    
    return themes


@router.get("/themes/{theme}/documents", response_model=List[dict])
def get_documents_by_theme(
    theme: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les documents par thème
    """
    search_service = RegulatorySearchService(db)
    documents = search_service.get_documents_by_theme(theme)
    
    return documents


@router.get("/themes/{theme}/articles", response_model=List[dict])
def get_articles_by_theme(
    theme: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les articles par thème
    """
    search_service = RegulatorySearchService(db)
    articles = search_service.get_articles_by_theme(theme, limit)
    
    return articles


# ============================================
# ENDPOINTS POUR LES LIENS ENTRE ARTICLES
# ============================================

@router.post("/articles/{source_id}/links", response_model=dict)
def create_article_link(
    source_id: int,
    target_article_id: int,
    link_type: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un lien entre deux articles
    """
    search_service = RegulatorySearchService(db)
    link = search_service.create_article_link(
        source_article_id=source_id,
        target_article_id=target_article_id,
        link_type=link_type,
        description=description,
        user_id=current_user.id
    )
    
    return {
        'id': link.id,
        'message': 'Lien créé avec succès'
    }


@router.get("/articles/{article_id}/related", response_model=List[dict])
def get_related_articles(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les articles liés
    """
    search_service = RegulatorySearchService(db)
    related = search_service.get_related_articles(article_id)
    
    return related


# ============================================
# ENDPOINTS POUR LA CONFORMITÉ
# ============================================

@router.post("/compliance/check", response_model=dict)
def check_compliance(
    context: str,
    procedure: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Vérifie la conformité réglementaire
    """
    compliance_service = RegulatoryComplianceService(db)
    result = compliance_service.check_compliance(context, procedure)
    
    return result


@router.get("/compliance/deadline/{deadline_type}", response_model=List[dict])
def get_deadline_articles(
    deadline_type: str,
    procedure: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les articles applicables pour un type de délai
    """
    compliance_service = RegulatoryComplianceService(db)
    articles = compliance_service.get_applicable_articles_for_deadline(deadline_type, procedure)
    
    return articles


# ============================================
# ENDPOINTS POUR L'INDEXATION
# ============================================

@router.post("/documents/{document_id}/index", response_model=dict)
def index_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Indexe un document
    """
    indexing_service = RegulatoryIndexingService(db)
    indexing_service.index_document(document_id)
    
    return {'message': 'Document indexé avec succès'}


@router.post("/index/all", response_model=dict)
def index_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Indexe tous les documents
    """
    indexing_service = RegulatoryIndexingService(db)
    
    documents = db.query(RegulatoryDocument).filter(
        RegulatoryDocument.is_active == True
    ).all()
    
    indexed_count = 0
    for document in documents:
        try:
            indexing_service.index_document(document.id)
            indexed_count += 1
        except Exception as e:
            print(f"Erreur lors de l'index du document {document.id}: {e}")
    
    return {
        'message': f'{indexed_count} documents indexés avec succès',
        'indexed_count': indexed_count
    }

"""
API endpoints pour le Chatbot IA métier
Module dédié - ne modifie pas les fonctionnalités existantes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.services.chatbot_service import ChatbotService
from app.services.document_indexer import DocumentIndexer, RegulatoryDocumentLoader
from app.models.chatbot import (
    ChatSession, ChatMessage, KnowledgeBase, DocumentIndex,
    ChatbotFeedback, MessageType, DocumentType
)
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


# ============================================
# ENDPOINTS POUR LES SESSIONS
# ============================================

@router.post("/sessions", response_model=dict)
def create_session(
    session_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une nouvelle session de conversation
    """
    chatbot_service = ChatbotService(db)
    session = chatbot_service.create_session(current_user.id, session_name)
    
    return {
        "id": session.id,
        "session_name": session.session_name,
        "created_at": session.created_at.isoformat() if session.created_at else None
    }


@router.get("/sessions", response_model=List[dict])
def get_sessions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les sessions de conversation de l'utilisateur
    """
    chatbot_service = ChatbotService(db)
    sessions = chatbot_service.get_user_sessions(current_user.id, limit)
    
    return [{
        "id": s.id,
        "session_name": s.session_name,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "is_active": s.is_active
    } for s in sessions]


@router.get("/sessions/{session_id}", response_model=dict)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère une session de conversation spécifique
    """
    chatbot_service = ChatbotService(db)
    session = chatbot_service.get_session(session_id, current_user.id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    return {
        "id": session.id,
        "session_name": session.session_name,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "is_active": session.is_active
    }


@router.get("/sessions/{session_id}/messages", response_model=List[dict])
def get_session_messages(
    session_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les messages d'une session
    """
    # Vérifier que la session appartient à l'utilisateur
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).limit(limit).all()
    
    return [{
        "id": m.id,
        "message_type": m.message_type,
        "content": m.content,
        "query_type": m.query_type,
        "sources": m.sources,
        "confidence": m.confidence,
        "sql_query": m.sql_query,
        "created_at": m.created_at.isoformat() if m.created_at else None
    } for m in messages]


# ============================================
# ENDPOINTS POUR LES MESSAGES
# ============================================

@router.post("/sessions/{session_id}/messages", response_model=dict)
def send_message(
    session_id: int,
    message_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envoie un message et reçoit une réponse du chatbot
    """
    content = message_data.get('content')
    if not content:
        raise HTTPException(status_code=400, detail="Le contenu du message est requis")
    
    chatbot_service = ChatbotService(db)
    response = chatbot_service.process_message(session_id, current_user.id, content)
    
    return response


# ============================================
# ENDPOINTS POUR LA BASE DE CONNAISSANCES
# ============================================

@router.get("/knowledge", response_model=List[dict])
def get_knowledge_base(
    document_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les documents de la base de connaissances
    """
    query = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
    
    if document_type:
        query = query.filter(KnowledgeBase.document_type == document_type)
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    
    documents = query.limit(limit).all()
    
    return [{
        "id": d.id,
        "document_type": d.document_type,
        "title": d.title,
        "description": d.description,
        "source": d.source,
        "category": d.category,
        "tags": d.tags,
        "language": d.language,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in documents]


@router.get("/knowledge/{doc_id}", response_model=dict)
def get_knowledge_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un document spécifique de la base de connaissances
    """
    doc = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == doc_id,
        KnowledgeBase.is_active == True
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return {
        "id": doc.id,
        "document_type": doc.document_type,
        "title": doc.title,
        "description": doc.description,
        "content": doc.content,
        "source": doc.source,
        "category": doc.category,
        "tags": doc.tags,
        "language": doc.language,
        "created_at": doc.created_at.isoformat() if doc.created_at else None
    }


@router.post("/knowledge", response_model=dict)
def add_knowledge_document(
    doc_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ajoute un document à la base de connaissances
    """
    from app.services.document_indexer import DocumentIndexer
    
    indexer = DocumentIndexer(db)
    doc = indexer.index_regulatory_document(
        title=doc_data.get('title'),
        content=doc_data.get('content'),
        source=doc_data.get('source', 'Manuel'),
        category=doc_data.get('category', 'Général'),
        document_type=DocumentType(doc_data.get('document_type', DocumentType.REGLEMENTATION.value)),
        tags=doc_data.get('tags', [])
    )
    
    return {
        "id": doc.id,
        "title": doc.title,
        "message": "Document ajouté avec succès"
    }


@router.delete("/knowledge/{doc_id}", response_model=dict)
def delete_knowledge_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un document de la base de connaissances
    """
    from app.services.document_indexer import DocumentIndexer
    
    indexer = DocumentIndexer(db)
    success = indexer.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return {"message": "Document supprimé avec succès"}


# ============================================
# ENDPOINTS POUR L'INDEXATION
# ============================================

@router.post("/index/market/{market_id}", response_model=dict)
def index_market(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Indexe un marché et ses documents
    """
    from app.services.document_indexer import DocumentIndexer
    
    indexer = DocumentIndexer(db)
    docs = indexer.index_market(market_id)
    
    return {
        "market_id": market_id,
        "indexed_documents": len(docs),
        "message": "Marché indexé avec succès"
    }


@router.post("/index/all-markets", response_model=dict)
def index_all_markets(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Indexe tous les marchés de la base de données
    """
    from app.services.document_indexer import DocumentIndexer
    
    indexer = DocumentIndexer(db)
    count = indexer.index_all_markets(limit)
    
    return {
        "indexed_markets": count,
        "message": f"{count} marchés indexés avec succès"
    }


@router.get("/index/statistics", response_model=dict)
def get_index_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les statistiques de l'index
    """
    from app.services.document_indexer import DocumentIndexer
    
    indexer = DocumentIndexer(db)
    stats = indexer.get_statistics()
    
    return stats


# ============================================
# ENDPOINTS POUR LE PEUPLEMENT RÉGLEMENTAIRE
# ============================================

@router.post("/seed/regulatory", response_model=dict)
def seed_regulatory_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Peuple la base de connaissances avec les documents réglementaires
    """
    from app.services.document_indexer import DocumentIndexer, RegulatoryDocumentLoader
    
    indexer = DocumentIndexer(db)
    loader = RegulatoryDocumentLoader()
    
    total_indexed = 0
    
    # Charger et indexer le Décret 2-22-431
    decret_articles = loader.load_decret_2_22_431()
    for article in decret_articles:
        indexer.index_regulatory_document(
            title=article['title'],
            content=article['content'],
            source=article['source'],
            category=article['category'],
            document_type=DocumentType.REGLEMENTATION,
            tags=['décret', '2-22-431', article['category']]
        )
        total_indexed += 1
    
    # Charger et indexer le CCAG Travaux
    ccag_articles = loader.load_ccag_travaux()
    for article in ccag_articles:
        indexer.index_regulatory_document(
            title=article['title'],
            content=article['content'],
            source=article['source'],
            category=article['category'],
            document_type=DocumentType.REGLEMENTATION,
            tags=['ccag', 'travaux', article['category']]
        )
        total_indexed += 1
    
    # Charger et indexer le guide PMMP
    pmmp_articles = loader.load_pmmp_guide()
    for article in pmmp_articles:
        indexer.index_regulatory_document(
            title=article['title'],
            content=article['content'],
            source=article['source'],
            category=article['category'],
            document_type=DocumentType.GUIDE,
            tags=['pmmp', 'guide', article['category']]
        )
        total_indexed += 1
    
    return {
        "total_indexed": total_indexed,
        "message": f"{total_indexed} documents réglementaires indexés avec succès"
    }


# ============================================
# ENDPOINTS POUR LE FEEDBACK
# ============================================

@router.post("/feedback", response_model=dict)
def add_feedback(
    feedback_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ajoute un feedback sur une réponse du chatbot
    """
    chatbot_service = ChatbotService(db)
    feedback = chatbot_service.add_feedback(
        message_id=feedback_data.get('message_id'),
        user_id=current_user.id,
        rating=feedback_data.get('rating'),
        is_helpful=feedback_data.get('is_helpful'),
        comment=feedback_data.get('comment')
    )
    
    return {
        "id": feedback.id,
        "message": "Feedback enregistré avec succès"
    }


# ============================================
# ENDPOINTS POUR LA RECHERCHE
# ============================================

@router.post("/search/knowledge", response_model=List[dict])
def search_knowledge(
    search_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche dans la base de connaissances
    """
    from app.services.chatbot_service import RAGEngine
    
    rag_engine = RAGEngine(db)
    results = rag_engine.search_knowledge_base(
        query=search_data.get('query'),
        document_type=search_data.get('document_type'),
        category=search_data.get('category'),
        limit=search_data.get('limit', 5)
    )
    
    return results


@router.post("/search/database", response_model=dict)
def search_database(
    search_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Interroge la base de données via le chatbot
    """
    from app.services.chatbot_service import RAGEngine
    
    rag_engine = RAGEngine(db)
    result = rag_engine.search_database(
        query=search_data.get('query'),
        limit=search_data.get('limit', 10)
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Impossible de générer une requête SQL pour cette question")
    
    return result

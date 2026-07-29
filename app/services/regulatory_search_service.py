"""
Service de recherche et de consultation réglementaire
Module dédié - Recherche rapide, liens entre articles, consultation par thème
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_, func

from app.models.regulatory_knowledge import (
    RegulatoryDocument, Chapter, Article, Keyword,
    DocumentKeyword, DocumentTheme, ArticleLink, Theme
)


class RegulatorySearchService:
    """Service de recherche dans la base de connaissances réglementaire"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(
        self,
        query: str,
        document_type: Optional[str] = None,
        theme: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans la base de connaissances
        """
        # Recherche dans les articles
        articles_query = self.db.query(
            Article.id,
            Article.article_number,
            Article.title,
            Article.content,
            RegulatoryDocument.id.label('document_id'),
            RegulatoryDocument.reference,
            RegulatoryDocument.title.label('document_title'),
            Chapter.id.label('chapter_id'),
            Chapter.title.label('chapter_title')
        ).join(
            RegulatoryDocument, Article.document_id == RegulatoryDocument.id
        ).outerjoin(
            Chapter, Article.chapter_id == Chapter.id
        ).filter(
            RegulatoryDocument.is_active == True
        )
        
        # Filtre par type de document
        if document_type:
            articles_query = articles_query.filter(
                RegulatoryDocument.document_type == document_type
            )
        
        # Filtre par thème
        if theme:
            articles_query = articles_query.join(
                DocumentTheme, DocumentTheme.document_id == RegulatoryDocument.id
            ).filter(
                DocumentTheme.theme == theme
            )
        
        # Recherche textuelle
        search_pattern = f"%{query}%"
        articles_query = articles_query.filter(
            or_(
                Article.content.ilike(search_pattern),
                Article.title.ilike(search_pattern),
                Article.article_number.ilike(search_pattern),
                RegulatoryDocument.title.ilike(search_pattern),
                RegulatoryDocument.reference.ilike(search_pattern)
            )
        )
        
        results = articles_query.limit(limit).all()
        
        # Formater les résultats
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.id,
                'article_number': result.article_number,
                'title': result.title,
                'content': result.content[:500] + '...' if len(result.content) > 500 else result.content,
                'document_id': result.document_id,
                'document_reference': result.reference,
                'document_title': result.document_title,
                'chapter_id': result.chapter_id,
                'chapter_title': result.chapter_title
            })
        
        return formatted_results
    
    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Recherche par mot-clé
        """
        keyword_obj = self.db.query(Keyword).filter(
            Keyword.keyword.ilike(f"%{keyword}%")
        ).first()
        
        if not keyword_obj:
            return []
        
        documents = self.db.query(RegulatoryDocument).join(
            DocumentKeyword, DocumentKeyword.document_id == RegulatoryDocument.id
        ).filter(
            DocumentKeyword.keyword_id == keyword_obj.id,
            RegulatoryDocument.is_active == True
        ).all()
        
        return [{
            'id': doc.id,
            'reference': doc.reference,
            'title': doc.title,
            'description': doc.description,
            'document_type': doc.document_type,
            'relevance_score': 1.0  # Score par défaut
        } for doc in documents]
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un article avec ses détails
        """
        article = self.db.query(Article).filter(Article.id == article_id).first()
        
        if not article:
            return None
        
        document = self.db.query(RegulatoryDocument).filter(
            RegulatoryDocument.id == article.document_id
        ).first()
        
        chapter = None
        if article.chapter_id:
            chapter = self.db.query(Chapter).filter(
                Chapter.id == article.chapter_id
            ).first()
        
        # Récupérer les articles liés
        related_articles = self.db.query(ArticleLink).filter(
            ArticleLink.source_article_id == article_id
        ).all()
        
        related_data = []
        for link in related_articles:
            target_article = self.db.query(Article).filter(
                Article.id == link.target_article_id
            ).first()
            if target_article:
                related_data.append({
                    'id': target_article.id,
                    'article_number': target_article.article_number,
                    'title': target_article.title,
                    'link_type': link.link_type,
                    'description': link.description
                })
        
        return {
            'id': article.id,
            'article_number': article.article_number,
            'title': article.title,
            'content': article.content,
            'keywords': article.keywords,
            'themes': article.themes,
            'doc_references': article.doc_references,
            'document': {
                'id': document.id,
                'reference': document.reference,
                'title': document.title,
                'document_type': document.document_type,
                'url': document.url
            },
            'chapter': {
                'id': chapter.id,
                'chapter_number': chapter.chapter_number,
                'title': chapter.title
            } if chapter else None,
            'related_articles': related_data
        }
    
    def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un document avec ses chapitres et articles
        """
        document = self.db.query(RegulatoryDocument).filter(
            RegulatoryDocument.id == document_id
        ).first()
        
        if not document:
            return None
        
        # Récupérer les chapitres
        chapters = self.db.query(Chapter).filter(
            Chapter.document_id == document_id
        ).order_by(Chapter.order_index).all()
        
        chapters_data = []
        for chapter in chapters:
            # Récupérer les articles du chapitre
            articles = self.db.query(Article).filter(
                Article.chapter_id == chapter.id
            ).all()
            
            articles_data = [{
                'id': art.id,
                'article_number': art.article_number,
                'title': art.title,
                'content': art.content
            } for art in articles]
            
            chapters_data.append({
                'id': chapter.id,
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'description': chapter.description,
                'articles': articles_data
            })
        
        # Récupérer les articles sans chapitre
        orphan_articles = self.db.query(Article).filter(
            Article.document_id == document_id,
            Article.chapter_id.is_(None)
        ).all()
        
        orphan_articles_data = [{
            'id': art.id,
            'article_number': art.article_number,
            'title': art.title,
            'content': art.content
        } for art in orphan_articles]
        
        # Récupérer les mots-clés
        keywords = self.db.query(Keyword).join(
            DocumentKeyword, DocumentKeyword.keyword_id == Keyword.id
        ).filter(
            DocumentKeyword.document_id == document_id
        ).all()
        
        keywords_data = [kw.keyword for kw in keywords]
        
        # Récupérer les thèmes
        themes = self.db.query(DocumentTheme).filter(
            DocumentTheme.document_id == document_id
        ).all()
        
        themes_data = [th.theme for th in themes]
        
        return {
            'id': document.id,
            'document_type': document.document_type,
            'reference': document.reference,
            'title': document.title,
            'description': document.description,
            'publication_date': document.publication_date.isoformat() if document.publication_date else None,
            'effective_date': document.effective_date.isoformat() if document.effective_date else None,
            'issuer': document.issuer,
            'url': document.url,
            'chapters': chapters_data,
            'orphan_articles': orphan_articles_data,
            'keywords': keywords_data,
            'themes': themes_data
        }
    
    def get_articles_by_theme(self, theme: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les articles par thème
        """
        articles = self.db.query(
            Article.id,
            Article.article_number,
            Article.title,
            Article.content,
            RegulatoryDocument.id.label('document_id'),
            RegulatoryDocument.reference,
            RegulatoryDocument.title.label('document_title')
        ).join(
            RegulatoryDocument, Article.document_id == RegulatoryDocument.id
        ).join(
            DocumentTheme, DocumentTheme.document_id == RegulatoryDocument.id
        ).filter(
            DocumentTheme.theme == theme,
            RegulatoryDocument.is_active == True
        ).limit(limit).all()
        
        return [{
            'id': art.id,
            'article_number': art.article_number,
            'title': art.title,
            'content': art.content[:300] + '...' if len(art.content) > 300 else art.content,
            'document_id': art.document_id,
            'document_reference': art.reference,
            'document_title': art.document_title
        } for art in articles]
    
    def get_all_themes(self) -> List[str]:
        """
        Récupère tous les thèmes disponibles
        """
        themes = self.db.query(DocumentTheme.theme).distinct().all()
        return [t[0] for t in themes]
    
    def get_documents_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """
        Récupère les documents par thème
        """
        documents = self.db.query(RegulatoryDocument).join(
            DocumentTheme, DocumentTheme.document_id == RegulatoryDocument.id
        ).filter(
            DocumentTheme.theme == theme,
            RegulatoryDocument.is_active == True
        ).all()
        
        return [{
            'id': doc.id,
            'reference': doc.reference,
            'title': doc.title,
            'description': doc.description,
            'document_type': doc.document_type,
            'publication_date': doc.publication_date.isoformat() if doc.publication_date else None,
            'issuer': doc.issuer
        } for doc in documents]
    
    def create_article_link(
        self,
        source_article_id: int,
        target_article_id: int,
        link_type: str,
        description: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ArticleLink:
        """
        Crée un lien entre deux articles
        """
        link = ArticleLink(
            source_article_id=source_article_id,
            target_article_id=target_article_id,
            link_type=link_type,
            description=description,
            created_by=user_id
        )
        
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        return link
    
    def get_related_articles(self, article_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les articles liés à un article
        """
        links = self.db.query(ArticleLink).filter(
            ArticleLink.source_article_id == article_id
        ).all()
        
        related_articles = []
        for link in links:
            article = self.db.query(Article).filter(
                Article.id == link.target_article_id
            ).first()
            
            if article:
                document = self.db.query(RegulatoryDocument).filter(
                    RegulatoryDocument.id == article.document_id
                ).first()
                
                related_articles.append({
                    'id': article.id,
                    'article_number': article.article_number,
                    'title': article.title,
                    'document_reference': document.reference,
                    'document_title': document.title,
                    'link_type': link.link_type,
                    'description': link.description
                })
        
        return related_articles


class RegulatoryComplianceService:
    """Service de vérification de conformité réglementaire"""
    
    def __init__(self, db: Session):
        self.db = db
        self.search_service = RegulatorySearchService(db)
    
    def check_compliance(
        self,
        context: str,
        procedure: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Vérifie la conformité réglementaire pour un contexte donné
        Retourne les articles applicables et les exigences
        """
        # Rechercher les articles pertinents
        articles = self.search_service.search(
            query=context,
            theme=procedure,
            limit=20
        )
        
        # Analyser les résultats pour extraire les exigences
        requirements = self._extract_requirements(articles)
        
        return {
            'context': context,
            'procedure': procedure,
            'applicable_articles': articles,
            'requirements': requirements,
            'compliance_score': self._calculate_compliance_score(requirements)
        }
    
    def _extract_requirements(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extrait les exigences réglementaires des articles
        """
        requirements = []
        
        for article in articles:
            content = article.get('content', '')
            
            # Mots-clés d'exigence
            requirement_keywords = ['doit', 'obligatoire', 'obligation', 'exige', 'nécessaire', 'requis']
            
            for keyword in requirement_keywords:
                if keyword.lower() in content.lower():
                    requirements.append({
                        'article_id': article.get('id'),
                        'article_number': article.get('article_number'),
                        'requirement': self._extract_requirement_sentence(content, keyword),
                        'source': f"{article.get('document_reference')} - {article.get('article_number')}"
                    })
                    break
        
        return requirements
    
    def _extract_requirement_sentence(self, content: str, keyword: str) -> str:
        """
        Extrait la phrase contenant l'exigence
        """
        sentences = content.split('.')
        for sentence in sentences:
            if keyword.lower() in sentence.lower():
                return sentence.strip()
        
        return content[:200]
    
    def _calculate_compliance_score(self, requirements: List[Dict]) -> float:
        """
        Calcule un score de conformité (0-1)
        """
        if not requirements:
            return 1.0  # Pas d'exigence = conforme par défaut
        
        # Score basé sur le nombre d'exigences trouvées
        # En pratique, ce serait basé sur les données de conformité réelles
        return min(len(requirements) / 10, 1.0)
    
    def get_applicable_articles_for_deadline(
        self,
        deadline_type: str,
        procedure: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les articles applicables pour un type de délai
        """
        query = f"délai {deadline_type}"
        
        return self.search_service.search(
            query=query,
            theme=procedure,
            limit=10
        )

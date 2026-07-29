"""
Service d'importation et d'indexation des documents réglementaires
Module dédié - Système extensible pour ajouter de nouveaux textes sans modifier le code
"""

from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from sqlalchemy.orm import Session
import os
import json
import re
from pathlib import Path

from app.models.regulatory_knowledge import (
    RegulatoryDocument, Chapter, Article, Keyword,
    DocumentKeyword, DocumentTheme, ArticleLink,
    DocumentType, Theme
)


class RegulatoryDocumentParser:
    """Parseur abstrait pour les documents réglementaires"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse un document et retourne les données structurées
        Doit être implémenté par les sous-classes
        """
        raise NotImplementedError("Les sous-classes doivent implémenter cette méthode")


class TextDocumentParser(RegulatoryDocumentParser):
    """Parseur pour les documents texte"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse un fichier texte"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'content': content,
            'chapters': self._extract_chapters(content),
            'articles': self._extract_articles(content)
        }
    
    def _extract_chapters(self, content: str) -> List[Dict]:
        """Extrait les chapitres du contenu"""
        chapters = []
        # Pattern pour détecter les chapitres (ex: "Chapitre 1", "CHAPITRE PREMIER")
        chapter_pattern = r'(?:Chapitre|CHAPITRE)\s*(\d+|[A-Za-z]+)\s*[:\.\-]\s*(.+?)(?=\n(?:Chapitre|CHAPITRE)|$)'
        
        matches = re.finditer(chapter_pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            chapters.append({
                'chapter_number': match.group(1),
                'title': match.group(2).strip(),
                'content': match.group(0)
            })
        
        return chapters
    
    def _extract_articles(self, content: str) -> List[Dict]:
        """Extrait les articles du contenu"""
        articles = []
        # Pattern pour détecter les articles (ex: "Article 1", "Art. 1")
        article_pattern = r'(?:Article|Art\.)\s*(\d+[\w\-]*)\s*[:\.\-]\s*(.+?)(?=\n(?:Article|Art\.)|$)'
        
        matches = re.finditer(article_pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            articles.append({
                'article_number': match.group(1),
                'title': match.group(2).strip()[:200],
                'content': match.group(2).strip()
            })
        
        return articles


class JSONDocumentParser(RegulatoryDocumentParser):
    """Parseur pour les documents JSON structurés"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse un fichier JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data


class RegulatoryImportService:
    """Service d'importation des documents réglementaires"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parsers = {
            '.txt': TextDocumentParser(),
            '.json': JSONDocumentParser()
        }
    
    def register_parser(self, extension: str, parser: RegulatoryDocumentParser):
        """
        Enregistre un nouveau parseur pour une extension de fichier
        Permet d'étendre le système sans modifier le code existant
        """
        self.parsers[extension] = parser
    
    def import_document(
        self,
        file_path: str,
        document_type: DocumentType,
        reference: str,
        title: str,
        description: Optional[str] = None,
        publication_date: Optional[datetime] = None,
        effective_date: Optional[datetime] = None,
        issuer: Optional[str] = None,
        url: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        themes: Optional[List[Theme]] = None
    ) -> RegulatoryDocument:
        """
        Importe un document réglementaire
        """
        # Déterminer le parseur approprié
        file_extension = Path(file_path).suffix.lower()
        parser = self.parsers.get(file_extension)
        
        if not parser:
            raise ValueError(f"Aucun parseur disponible pour l'extension {file_extension}")
        
        # Parser le document
        parsed_data = parser.parse(file_path)
        
        # Créer le document
        document = RegulatoryDocument(
            document_type=document_type.value,
            reference=reference,
            title=title,
            description=description,
            publication_date=publication_date,
            effective_date=effective_date,
            issuer=issuer,
            url=url,
            content=parsed_data.get('content'),
            file_path=file_path
        )
        
        self.db.add(document)
        self.db.flush()
        
        # Importer les chapitres
        chapters_data = parsed_data.get('chapters', [])
        for chapter_data in chapters_data:
            chapter = Chapter(
                document_id=document.id,
                chapter_number=chapter_data.get('chapter_number'),
                title=chapter_data.get('title'),
                description=chapter_data.get('description'),
                content=chapter_data.get('content'),
                order_index=chapter_data.get('order_index', 0)
            )
            self.db.add(chapter)
            self.db.flush()
            
            # Importer les articles du chapitre
            articles_data = chapter_data.get('articles', [])
            for article_data in articles_data:
                article = Article(
                    document_id=document.id,
                    chapter_id=chapter.id,
                    article_number=article_data.get('article_number'),
                    title=article_data.get('title'),
                    content=article_data.get('content'),
                    keywords=article_data.get('keywords'),
                    themes=article_data.get('themes')
                )
                self.db.add(article)
        
        # Importer les articles sans chapitre
        articles_data = parsed_data.get('articles', [])
        for article_data in articles_data:
            article = Article(
                document_id=document.id,
                article_number=article_data.get('article_number'),
                title=article_data.get('title'),
                content=article_data.get('content'),
                keywords=article_data.get('keywords'),
                themes=article_data.get('themes')
            )
            self.db.add(article)
        
        # Ajouter les mots-clés
        if keywords:
            for keyword_text in keywords:
                keyword = self.db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
                if not keyword:
                    keyword = Keyword(keyword=keyword_text)
                    self.db.add(keyword)
                    self.db.flush()
                
                doc_keyword = DocumentKeyword(
                    document_id=document.id,
                    keyword_id=keyword.id
                )
                self.db.add(doc_keyword)
        
        # Ajouter les thèmes
        if themes:
            for theme in themes:
                doc_theme = DocumentTheme(
                    document_id=document.id,
                    theme=theme.value
                )
                self.db.add(doc_theme)
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def import_from_directory(
        self,
        directory: str,
        document_config: Dict[str, Any]
    ) -> List[RegulatoryDocument]:
        """
        Importe tous les documents d'un répertoire selon une configuration
        Permet l'importation en lot
        """
        documents = []
        dir_path = Path(directory)
        
        for file_path in dir_path.glob('*'):
            if file_path.is_file():
                try:
                    document = self.import_document(
                        file_path=str(file_path),
                        document_type=DocumentType(document_config.get('document_type', 'autre')),
                        reference=document_config.get('reference', file_path.stem),
                        title=document_config.get('title', file_path.stem),
                        description=document_config.get('description'),
                        publication_date=document_config.get('publication_date'),
                        effective_date=document_config.get('effective_date'),
                        issuer=document_config.get('issuer'),
                        url=document_config.get('url'),
                        keywords=document_config.get('keywords'),
                        themes=document_config.get('themes')
                    )
                    documents.append(document)
                except Exception as e:
                    print(f"Erreur lors de l'import de {file_path}: {e}")
        
        return documents


class RegulatoryIndexingService:
    """Service d'indexation et de recherche"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def index_document(self, document_id: int):
        """
        Indexe un document pour la recherche
        Extrait automatiquement les mots-clés et les thèmes
        """
        document = self.db.query(RegulatoryDocument).filter(
            RegulatoryDocument.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document non trouvé")
        
        # Extraire les mots-clés du contenu
        keywords = self._extract_keywords(document.content)
        
        # Ajouter les mots-clés
        for keyword_text in keywords:
            keyword = self.db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
            if not keyword:
                keyword = Keyword(keyword=keyword_text)
                self.db.add(keyword)
                self.db.flush()
            
            doc_keyword = DocumentKeyword(
                document_id=document.id,
                keyword_id=keyword.id,
                relevance_score=keywords[keyword_text]
            )
            self.db.add(doc_keyword)
        
        # Détecter les thèmes
        detected_themes = self._detect_themes(document.content)
        
        for theme in detected_themes:
            doc_theme = DocumentTheme(
                document_id=document.id,
                theme=theme.value,
                relevance_score=detected_themes[theme]
            )
            self.db.add(doc_theme)
        
        self.db.commit()
    
    def _extract_keywords(self, content: str) -> Dict[str, float]:
        """
        Extrait les mots-clés du contenu avec leur score de pertinence
        """
        keywords = {}
        
        if not content:
            return keywords
        
        # Mots-clés réglementaires courants
        regulatory_terms = [
            'marché public', 'procédure', 'commission', 'attribution',
            'publication', 'exécution', 'réception', 'paiement',
            'délai', 'cahier des charges', 'offre', 'plis',
            'contrat', 'avenant', 'résiliation', 'contentieux',
            'contrôle', 'budget', 'engagement', 'liquidation'
        ]
        
        content_lower = content.lower()
        
        for term in regulatory_terms:
            count = content_lower.count(term)
            if count > 0:
                keywords[term] = min(count / 10, 1.0)  # Score entre 0 et 1
        
        return keywords
    
    def _detect_themes(self, content: str) -> Dict[Theme, float]:
        """
        Détecte les thèmes applicables au document
        """
        themes = {}
        
        if not content:
            return themes
        
        content_lower = content.lower()
        
        # Mots-clés par thème
        theme_keywords = {
            Theme.PLANIFICATION: ['planification', 'programmation', 'budget', 'prévisionnel'],
            Theme.PREPARATION: ['préparation', 'cahier des charges', 'dossier', 'consultation'],
            Theme.PUBLICITE: ['publicité', 'annonce', 'journal', 'boamp'],
            Theme.COMMISSION: ['commission', 'ouverture', 'examen', 'jugement'],
            Theme.ATTRIBUTION: ['attribution', 'notification', 'contrat', 'signature'],
            Theme.EXECUTION: ['exécution', 'ordre de service', 'chantier', 'travaux'],
            Theme.RECEPTION: ['réception', 'levée des réserves', 'conforme'],
            Theme.PAIEMENT: ['paiement', 'mandatement', 'liquidation', 'facture'],
            Theme.BUDGET: ['budget', 'crédit', 'engagement', 'dépense'],
            Theme.CONTROLE: ['contrôle', 'inspection', 'vérification', 'audit'],
            Theme.CONTENTIEUX: ['contentieux', 'litige', 'tribunal', 'recours']
        }
        
        for theme, keywords in theme_keywords.items():
            score = sum(content_lower.count(kw) for kw in keywords) / len(keywords)
            if score > 0:
                themes[theme] = min(score / 5, 1.0)  # Score entre 0 et 1
        
        return themes

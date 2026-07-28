"""
Service Chatbot IA métier pour les marchés publics
Architecture RAG (Retrieval Augmented Generation)
Module dédié - ne modifie pas les fonctionnalités existantes
"""

import json
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.chatbot import (
    ChatSession, ChatMessage, KnowledgeBase, DocumentIndex,
    ChatbotFeedback, MessageType, DocumentType, QueryType
)
from app.models.market import Market
from app.models.stage import Stage
from app.models.document import Document
from app.models.user import User


class EmbeddingProvider:
    """Abstraction pour les fournisseurs d'embeddings"""
    
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """
        Génère un embedding pour un texte
        Par défaut, utilise une méthode simple basée sur TF-IDF
        Peut être étendu pour utiliser OpenAI, HuggingFace, etc.
        """
        # Méthode simple basée sur le hash du texte pour la démonstration
        # En production, utiliser sentence-transformers ou OpenAI embeddings
        words = text.lower().split()
        embedding = [0.0] * 384  # Taille standard pour sentence-transformers
        
        for i, word in enumerate(words[:384]):
            # Hash simple du mot pour générer une valeur
            word_hash = hash(word) % 1000 / 1000.0
            embedding[i] = word_hash
        
        return embedding
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class LLMProvider:
    """Abstraction pour les fournisseurs de LLM"""
    
    @staticmethod
    def generate_response(
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Génère une réponse basée sur le contexte et la requête
        Par défaut, utilise une méthode basée sur des templates
        Peut être étendu pour utiliser OpenAI GPT, Anthropic Claude, etc.
        """
        if not context:
            return "Je n'ai pas trouvé d'informations pertinentes dans ma base de connaissances. Pouvez-vous reformuler votre question ?"
        
        # Construire le contexte
        context_text = "\n\n".join([
            f"- {doc.get('title', 'Document')}: {doc.get('content', '')[:200]}..."
            for doc in context[:3]
        ])
        
        # Réponse basée sur le contexte
        if len(context) == 1:
            source = context[0].get('source', 'document')
            return f"Selon {source}, {context[0].get('content', '')[:300]}..."
        else:
            return f"Voici ce que j'ai trouvé dans ma base de connaissances :\n\n{context_text}\n\nSouhaitez-vous plus de détails sur un point particulier ?"
    
    @staticmethod
    def generate_sql_query(query: str, schema: Dict[str, Any]) -> Optional[str]:
        """
        Génère une requête SQL à partir d'une question en langage naturel
        Par défaut, utilise une méthode basée sur des patterns
        Peut être étendu pour utiliser des modèles spécialisés
        """
        query_lower = query.lower()
        
        # Patterns simples pour les questions courantes
        if "en retard" in query_lower and "marché" in query_lower:
            return """
                SELECT m.market_number, m.object, m.status, m.progress_percentage
                FROM markets m
                WHERE m.status = 'en_retard'
                ORDER BY m.created_at DESC
                LIMIT 10
            """
        
        elif "échéance" in query_lower and "marché" in query_lower:
            return """
                SELECT m.market_number, m.object, m.expected_end_date, m.status
                FROM markets m
                WHERE m.expected_end_date >= date('now')
                ORDER BY m.expected_end_date ASC
                LIMIT 10
            """
        
        elif "validation" in query_lower and "attente" in query_lower:
            return """
                SELECT m.market_number, m.object, m.status
                FROM markets m
                WHERE m.status IN ('en_validation', 'en_attente')
                ORDER BY m.created_at DESC
                LIMIT 10
            """
        
        elif "document" in query_lower and "manquant" in query_lower:
            return """
                SELECT m.market_number, m.object, COUNT(d.id) as doc_count
                FROM markets m
                LEFT JOIN documents d ON m.id = d.market_id
                GROUP BY m.id
                HAVING doc_count = 0
                LIMIT 10
            """
        
        elif "alerte" in query_lower:
            return """
                SELECT COUNT(*) as alert_count
                FROM deadline_alerts
                WHERE acknowledged = 0
            """
        
        elif "statistique" in query_lower or "tableau de bord" in query_lower:
            return """
                SELECT 
                    COUNT(*) as total_markets,
                    SUM(CASE WHEN status = 'en_cours' THEN 1 ELSE 0 END) as en_cours,
                    SUM(CASE WHEN status = 'en_retard' THEN 1 ELSE 0 END) as en_retard,
                    SUM(CASE WHEN status = 'termine' THEN 1 ELSE 0 END) as termine
                FROM markets
            """
        
        return None


class RAGEngine:
    """Moteur RAG pour la recherche et la génération"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = EmbeddingProvider()
        self.llm_provider = LLMProvider()
    
    def search_knowledge_base(
        self,
        query: str,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans la base de connaissances
        """
        # Générer l'embedding de la requête
        query_embedding = self.embedding_provider.get_embedding(query)
        
        # Construire la requête de recherche
        base_query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.is_active == True
        )
        
        if document_type:
            base_query = base_query.filter(KnowledgeBase.document_type == document_type)
        
        if category:
            base_query = base_query.filter(KnowledgeBase.category == category)
        
        # Récupérer les documents
        documents = base_query.all()
        
        # Calculer les similarités
        results = []
        for doc in documents:
            if doc.embedding:
                similarity = self.embedding_provider.cosine_similarity(
                    query_embedding,
                    doc.embedding
                )
                if similarity > 0.1:  # Seuil de similarité
                    results.append({
                        'id': doc.id,
                        'title': doc.title,
                        'content': doc.content,
                        'source': doc.source,
                        'category': doc.category,
                        'similarity': similarity
                    })
        
        # Trier par similarité
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:limit]
    
    def search_database(
        self,
        query: str,
        limit: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Interroge la base de données via génération SQL
        """
        # Schéma simplifié de la base de données
        schema = {
            'markets': ['id', 'market_number', 'object', 'status', 'progress_percentage', 'expected_end_date'],
            'stages': ['id', 'market_id', 'name', 'status', 'is_late'],
            'documents': ['id', 'market_id', 'title', 'type'],
            'deadline_alerts': ['id', 'deadline_id', 'acknowledged']
        }
        
        # Générer la requête SQL
        sql_query = self.llm_provider.generate_sql_query(query, schema)
        
        if not sql_query:
            return None
        
        # Exécuter la requête de manière sécurisée
        try:
            result = self.db.execute(text(sql_query))
            columns = result.keys()
            rows = result.fetchall()
            
            # Convertir en liste de dictionnaires
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                'sql_query': sql_query,
                'data': data,
                'row_count': len(data)
            }
        except Exception as e:
            print(f"Erreur SQL: {e}")
            return None
    
    def generate_response(
        self,
        query: str,
        query_type: QueryType,
        context: List[Dict[str, Any]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Génère une réponse basée sur le type de requête et le contexte
        """
        if query_type == QueryType.DATABASE and context:
            # Formater les résultats de la base de données
            db_result = context[0] if context else None
            if db_result and db_result.get('data'):
                data = db_result['data']
                if not data:
                    return "Aucun résultat trouvé dans la base de données."
                
                # Formater les résultats
                if len(data) == 1:
                    return f"J'ai trouvé 1 résultat : {self._format_db_result(data[0])}"
                else:
                    response = f"J'ai trouvé {len(data)} résultats :\n\n"
                    for i, row in enumerate(data[:5], 1):
                        response += f"{i}. {self._format_db_result(row)}\n"
                    return response
            else:
                return "Je n'ai pas pu interpréter votre requête pour la base de données."
        
        elif query_type == QueryType.KNOWLEDGE:
            # Utiliser le LLM pour générer une réponse basée sur le contexte
            return self.llm_provider.generate_response(query, context, conversation_history)
        
        elif query_type == QueryType.ASSISTANCE:
            # Réponses d'assistance prédéfinies
            return self._get_assistance_response(query)
        
        elif query_type == QueryType.MIXED:
            # Combiner les sources
            return self.llm_provider.generate_response(query, context, conversation_history)
        
        return "Je n'ai pas compris votre demande. Pouvez-vous reformuler ?"
    
    def _format_db_result(self, row: Dict[str, Any]) -> str:
        """Formate un résultat de base de données"""
        if 'market_number' in row:
            return f"Marché {row.get('market_number')}: {row.get('object', 'N/A')} - Statut: {row.get('status', 'N/A')}"
        elif 'name' in row:
            return f"{row.get('name')}: {row.get('status', 'N/A')}"
        else:
            return str(row)
    
    def _get_assistance_response(self, query: str) -> str:
        """Réponses d'assistance prédéfinies"""
        query_lower = query.lower()
        
        if "créer" in query_lower and "marché" in query_lower:
            return "Pour créer un nouveau marché, allez dans le menu 'Marchés' puis cliquez sur 'Nouveau Marché'. Remplissez les informations requises (objet, type de procédure, montant estimé, etc.) et validez."
        
        elif "publier" in query_lower and "marché" in query_lower:
            return "Pour publier un marché sur le PMMP, assurez-vous d'abord que le marché est validé. Ensuite, allez dans la section 'Publication' du marché et suivez les étapes pour générer et envoyer l'avis d'appel d'offres."
        
        elif "valider" in query_lower:
            return "La validation d'un marché se fait via le module 'Validation Workflow'. Vous pouvez suivre l'état de validation dans le tableau de bord ou dans la page détaillée du marché."
        
        elif "document" in query_lower and "ajouter" in query_lower:
            return "Pour ajouter un document, allez dans la section 'Documents' du marché concerné, puis cliquez sur 'Ajouter un document'. Sélectionnez le type de document et uploadez le fichier."
        
        elif "navigation" in query_lower or "comment" in query_lower:
            return "L'application est organisée en modules accessibles via le menu latéral : Marchés, Planification, Préparation, Validation, Commissions, Publication, Exécution, Documents, Analyse, et Délais Réglementaires."
        
        else:
            return "Je suis là pour vous aider avec l'utilisation de l'application. Vous pouvez me poser des questions sur la création de marchés, la publication, la validation, les documents, ou la navigation."


class ChatbotService:
    """Service principal du chatbot"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_engine = RAGEngine(db)
    
    def create_session(self, user_id: int, session_name: str = None) -> ChatSession:
        """Crée une nouvelle session de conversation"""
        session = ChatSession(
            user_id=user_id,
            session_name=session_name or f"Conversation {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        """Récupère une session de conversation"""
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
    
    def get_user_sessions(self, user_id: int, limit: int = 10) -> List[ChatSession]:
        """Récupère les sessions d'un utilisateur"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    def process_message(
        self,
        session_id: int,
        user_id: int,
        message: str
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur et génère une réponse
        """
        # Récupérer la session
        session = self.get_session(session_id, user_id)
        if not session:
            return {'error': 'Session non trouvée'}
        
        # Enregistrer le message utilisateur
        user_message = ChatMessage(
            session_id=session_id,
            message_type=MessageType.USER.value,
            content=message
        )
        self.db.add(user_message)
        
        # Récupérer l'historique de conversation
        conversation_history = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).limit(10).all()
        
        history = [
            {'role': msg.message_type, 'content': msg.content}
            for msg in conversation_history
        ]
        
        # Analyser le type de requête
        query_type = self._analyze_query_type(message)
        
        # Rechercher dans les sources appropriées
        context = []
        sources = []
        sql_query = None
        confidence = 0.7
        
        if query_type in [QueryType.DATABASE, QueryType.MIXED]:
            db_result = self.rag_engine.search_database(message)
            if db_result:
                context.append(db_result)
                sources.append({'type': 'database', 'query': db_result.get('sql_query')})
                sql_query = db_result.get('sql_query')
        
        if query_type in [QueryType.KNOWLEDGE, QueryType.MIXED]:
            kb_results = self.rag_engine.search_knowledge_base(message)
            if kb_results:
                context.extend(kb_results)
                sources.extend([
                    {'type': 'knowledge', 'source': doc.get('source'), 'title': doc.get('title')}
                    for doc in kb_results
                ])
                confidence = max([doc.get('similarity', 0) for doc in kb_results])
        
        if query_type == QueryType.ASSISTANCE:
            sources.append({'type': 'assistance'})
        
        # Générer la réponse
        response = self.rag_engine.generate_response(
            message,
            query_type,
            context,
            history
        )
        
        # Enregistrer la réponse de l'assistant
        assistant_message = ChatMessage(
            session_id=session_id,
            message_type=MessageType.ASSISTANT.value,
            content=response,
            query_type=query_type.value,
            sources=sources,
            confidence=confidence,
            sql_query=sql_query
        )
        self.db.add(assistant_message)
        
        # Mettre à jour la session
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(assistant_message)
        
        return {
            'message_id': assistant_message.id,
            'content': response,
            'query_type': query_type.value,
            'sources': sources,
            'confidence': confidence,
            'sql_query': sql_query
        }
    
    def _analyze_query_type(self, query: str) -> QueryType:
        """Analyse le type de requête"""
        query_lower = query.lower()
        
        # Mots-clés pour les requêtes de base de données
        db_keywords = ['combien', 'quels', 'quelle', 'liste', 'statistique', 'en retard', 
                      'échéance', 'attente', 'manquant', 'alerte', 'fournisseur', 'service']
        
        # Mots-clés pour l'assistance
        assistance_keywords = ['comment', 'créer', 'ajouter', 'modifier', 'supprimer', 
                              'publier', 'valider', 'navigation', 'utiliser', 'aide']
        
        # Mots-clés réglementaires
        reg_keywords = ['décret', 'réglementation', 'loi', 'article', 'ccag', 'pmmp']
        
        has_db = any(kw in query_lower for kw in db_keywords)
        has_assistance = any(kw in query_lower for kw in assistance_keywords)
        has_reg = any(kw in query_lower for kw in reg_keywords)
        
        if has_assistance:
            return QueryType.ASSISTANCE
        elif has_db and has_reg:
            return QueryType.MIXED
        elif has_db:
            return QueryType.DATABASE
        elif has_reg:
            return QueryType.KNOWLEDGE
        else:
            return QueryType.KNOWLEDGE  # Par défaut
    
    def add_feedback(
        self,
        message_id: int,
        user_id: int,
        rating: Optional[int] = None,
        is_helpful: Optional[bool] = None,
        comment: Optional[str] = None
    ) -> ChatbotFeedback:
        """Ajoute un feedback sur une réponse"""
        feedback = ChatbotFeedback(
            message_id=message_id,
            rating=rating,
            is_helpful=is_helpful,
            comment=comment,
            created_by=user_id
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

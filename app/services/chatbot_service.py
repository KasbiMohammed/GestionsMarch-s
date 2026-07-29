"""
Service Chatbot IA métier pour les marchés publics
Architecture RAG (Retrieval Augmented Generation)
Module dédié - ne modifie pas les fonctionnalités existantes
"""

import logging
import math
from typing import Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.chatbot import (
    ChatSession, ChatMessage, KnowledgeBase,
    ChatbotFeedback, MessageType, QueryType
)

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Abstraction pour les fournisseurs d'embeddings"""

    # Taille standard pour sentence-transformers (all-MiniLM-L6-v2)
    EMBEDDING_SIZE: int = 384

    @staticmethod
    def get_embedding(text: str) -> list[float]:
        """
        Génère un embedding déterministe pour un texte.
        En production, remplacer par sentence-transformers, OpenAI, etc.
        """
        if not text:
            return [0.0] * EmbeddingProvider.EMBEDDING_SIZE

        words = text.lower().split()
        embedding = [0.0] * EmbeddingProvider.EMBEDDING_SIZE

        for i, word in enumerate(words[:EmbeddingProvider.EMBEDDING_SIZE]):
            # Hachage déterministe (zlib.crc32) au lieu de hash() randomisé
            import zlib
            word_hash = (zlib.crc32(word.encode("utf-8")) & 0xFFFFFFFF) / 0xFFFFFFFF
            embedding[i] = word_hash

        return embedding

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = 0.0
        mag1 = 0.0
        mag2 = 0.0

        for a, b in zip(vec1, vec2):
            dot_product += a * b
            mag1 += a * a
            mag2 += b * b

        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0

        return dot_product / (math.sqrt(mag1) * math.sqrt(mag2))


class LLMProvider:
    """Abstraction pour les fournisseurs de LLM"""

    @staticmethod
    def generate_response(
        query: str,
        context: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Génère une réponse basée sur le contexte et la requête.
        Peut être étendu pour utiliser OpenAI GPT, Anthropic Claude, etc.
        """
        if not context:
            return (
                "Je n'ai pas trouvé d'informations pertinentes dans ma base de "
                "connaissances. Pouvez-vous reformuler votre question ?"
            )

        # Construire le contexte (troncature intelligente)
        context_text = "\n\n".join([
            f"- {doc.get('title', 'Document')}: {LLMProvider._smart_truncate(doc.get('content', ''), 200)}"
            for doc in context[:3]
        ])

        if len(context) == 1:
            source = context[0].get("source", "document")
            content = LLMProvider._smart_truncate(context[0].get("content", ""), 300)
            return f"Selon {source}, {content}"

        return (
            f"Voici ce que j'ai trouvé dans ma base de connaissances :\n\n"
            f"{context_text}\n\n"
            f"Souhaitez-vous plus de détails sur un point particulier ?"
        )

    @staticmethod
    def _smart_truncate(text: str, max_length: int) -> str:
        """Tronque un texte uniquement s'il dépasse la limite."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(" ", 1)[0] + "…"

    @staticmethod
    def generate_sql_query(query: str, schema: dict[str, Any]) -> str | None:
        """
        Génère une requête SQL à partir d'une question en langage naturel.
        ⚠️  En production, utiliser des paramètres bindés ou un LLM SQL sécurisé.
        """
        query_lower = query.lower()

        # Patterns simples pour les questions courantes (requêtes hardcodées = safe)
        patterns = {
            "en retard": """
                SELECT m.market_number, m.object, m.status, m.progress_percentage
                FROM markets m
                WHERE m.status = 'en_retard'
                ORDER BY m.created_at DESC
                LIMIT 10
            """,
            "échéance": """
                SELECT m.market_number, m.object, m.expected_end_date, m.status
                FROM markets m
                WHERE m.expected_end_date >= CURRENT_DATE
                ORDER BY m.expected_end_date ASC
                LIMIT 10
            """,
            "validation": """
                SELECT m.market_number, m.object, m.status
                FROM markets m
                WHERE m.status IN ('en_validation', 'en_attente')
                ORDER BY m.created_at DESC
                LIMIT 10
            """,
            "document manquant": """
                SELECT m.market_number, m.object, COUNT(d.id) as doc_count
                FROM markets m
                LEFT JOIN documents d ON m.id = d.market_id
                GROUP BY m.id
                HAVING COUNT(d.id) = 0
                LIMIT 10
            """,
            "alerte": """
                SELECT COUNT(*) as alert_count
                FROM deadline_alerts
                WHERE acknowledged = FALSE
            """,
            "statistique": """
                SELECT
                    COUNT(*) as total_markets,
                    SUM(CASE WHEN status = 'en_cours' THEN 1 ELSE 0 END) as en_cours,
                    SUM(CASE WHEN status = 'en_retard' THEN 1 ELSE 0 END) as en_retard,
                    SUM(CASE WHEN status = 'termine' THEN 1 ELSE 0 END) as termine
                FROM markets
            """,
        }

        for keyword, sql in patterns.items():
            if keyword in query_lower:
                return sql.strip()

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
        document_type: str | None = None,
        category: str | None = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Recherche dans la base de connaissances par similarité cosinus.
        ⚠️  En production, utiliser pgvector ou un index vectoriel pour
        éviter le scan complet en mémoire.
        """
        try:
            query_embedding = self.embedding_provider.get_embedding(query)

            base_query = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.is_active.is_(True)
            )

            if document_type:
                base_query = base_query.filter(
                    KnowledgeBase.document_type == document_type
                )
            if category:
                base_query = base_query.filter(KnowledgeBase.category == category)

            # TODO: Remplacer par une requête SQL avec pgvector pour la performance
            documents = base_query.all()

            results: list[dict[str, Any]] = []
            for doc in documents:
                if doc.embedding:
                    similarity = self.embedding_provider.cosine_similarity(
                        query_embedding, doc.embedding
                    )
                    if similarity > 0.1:
                        results.append({
                            "id": doc.id,
                            "title": doc.title,
                            "content": doc.content,
                            "source": doc.source,
                            "category": doc.category,
                            "similarity": similarity,
                        })

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]

        except Exception as exc:
            logger.exception("Erreur lors de la recherche dans la base de connaissances")
            return []

    def search_database(
        self,
        query: str,
        limit: int = 10
    ) -> dict[str, Any] | None:
        """
        Interroge la base de données via génération SQL.
        """
        try:
            schema = {
                "markets": [
                    "id", "market_number", "object", "status",
                    "progress_percentage", "expected_end_date"
                ],
                "stages": ["id", "market_id", "name", "status", "is_late"],
                "documents": ["id", "market_id", "title", "type"],
                "deadline_alerts": ["id", "deadline_id", "acknowledged"],
            }

            sql_query = self.llm_provider.generate_sql_query(query, schema)
            if not sql_query:
                return None

            # Les requêtes sont hardcodées dans LLMProvider, donc sûres.
            # Si elles deviennent dynamiques, utiliser text(sql).bindparams(...)
            result = self.db.execute(text(sql_query))
            columns = list(result.keys())
            rows = result.fetchall()

            data = [dict(zip(columns, row)) for row in rows]

            return {
                "sql_query": sql_query,
                "data": data,
                "row_count": len(data),
            }

        except Exception as exc:
            logger.exception("Erreur lors de l'interrogation de la base de données")
            return None

    def generate_response(
        self,
        query: str,
        query_type: QueryType,
        context: list[dict[str, Any]] | None = None,
        conversation_history: list[dict[str, str]] | None = None
    ) -> str:
        """Génère une réponse basée sur le type de requête et le contexte."""
        context = context or []

        if query_type == QueryType.DATABASE and context:
            db_result = context[0]
            data = db_result.get("data") if isinstance(db_result, dict) else None
            if not data:
                return "Aucun résultat trouvé dans la base de données."

            if len(data) == 1:
                return f"J'ai trouvé 1 résultat : {self._format_db_result(data[0])}"

            response_lines = [
                f"J'ai trouvé {len(data)} résultats :",
                "",
            ]
            for i, row in enumerate(data[:5], 1):
                response_lines.append(f"{i}. {self._format_db_result(row)}")
            return "\n".join(response_lines)

        if query_type == QueryType.KNOWLEDGE:
            return self.llm_provider.generate_response(
                query, context, conversation_history
            )

        if query_type == QueryType.ASSISTANCE:
            return self._get_assistance_response(query)

        if query_type == QueryType.MIXED:
            return self.llm_provider.generate_response(
                query, context, conversation_history
            )

        return "Je n'ai pas compris votre demande. Pouvez-vous reformuler ?"

    @staticmethod
    def _format_db_result(row: dict[str, Any]) -> str:
        """Formate un résultat de base de données de manière lisible."""
        if "market_number" in row:
            return (
                f"Marché {row.get('market_number')}: "
                f"{row.get('object', 'N/A')} — Statut: {row.get('status', 'N/A')}"
            )
        if "name" in row:
            return f"{row.get('name')}: {row.get('status', 'N/A')}"
        if "alert_count" in row:
            return f"Nombre d'alertes: {row.get('alert_count', 0)}"
        if "total_markets" in row:
            parts = [
                f"Total: {row.get('total_markets', 0)}",
                f"En cours: {row.get('en_cours', 0)}",
                f"En retard: {row.get('en_retard', 0)}",
                f"Terminés: {row.get('termine', 0)}",
            ]
            return " | ".join(parts)

        # Fallback lisible
        return ", ".join(f"{k}={v}" for k, v in row.items())

    @staticmethod
    def _get_assistance_response(query: str) -> str:
        """Réponses d'assistance prédéfinies."""
        query_lower = query.lower()

        if "créer" in query_lower and "marché" in query_lower:
            return (
                "Pour créer un nouveau marché, allez dans le menu 'Marchés' puis "
                "cliquez sur 'Nouveau Marché'. Remplissez les informations requises "
                "(objet, type de procédure, montant estimé, etc.) et validez."
            )

        if "publier" in query_lower and "marché" in query_lower:
            return (
                "Pour publier un marché sur le PMMP, assurez-vous d'abord que le "
                "marché est validé. Ensuite, allez dans la section 'Publication' du "
                "marché et suivez les étapes pour générer et envoyer l'avis d'appel d'offres."
            )

        if "valider" in query_lower:
            return (
                "La validation d'un marché se fait via le module 'Validation Workflow'. "
                "Vous pouvez suivre l'état de validation dans le tableau de bord ou dans "
                "la page détaillée du marché."
            )

        if "document" in query_lower and "ajouter" in query_lower:
            return (
                "Pour ajouter un document, allez dans la section 'Documents' du marché "
                "concerné, puis cliquez sur 'Ajouter un document'. Sélectionnez le type "
                "de document et uploadez le fichier."
            )

        if "navigation" in query_lower or "comment" in query_lower:
            return (
                "L'application est organisée en modules accessibles via le menu latéral : "
                "Marchés, Planification, Préparation, Validation, Commissions, Publication, "
                "Exécution, Documents, Analyse, et Délais Réglementaires."
            )

        return (
            "Je suis là pour vous aider avec l'utilisation de l'application. Vous pouvez "
            "me poser des questions sur la création de marchés, la publication, la validation, "
            "les documents, ou la navigation."
        )


class ChatbotServiceError(Exception):
    """Exception métier du chatbot."""
    pass


class SessionNotFoundError(ChatbotServiceError):
    pass


class ChatbotService:
    """Service principal du chatbot"""

    def __init__(self, db: Session):
        self.db = db
        self.rag_engine = RAGEngine(db)

    def create_session(self, user_id: int, session_name: str | None = None) -> ChatSession:
        """Crée une nouvelle session de conversation."""
        try:
            name = session_name or datetime.now(timezone.utc).strftime("Conversation %d/%m/%Y %H:%M")
            session = ChatSession(user_id=user_id, session_name=name)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except Exception as exc:
            self.db.rollback()
            logger.exception("Erreur lors de la création de la session")
            raise ChatbotServiceError("Impossible de créer la session") from exc

    def get_session(self, session_id: int, user_id: int) -> ChatSession | None:
        """Récupère une session de conversation."""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

    def get_user_sessions(self, user_id: int, limit: int = 10) -> list[ChatSession]:
        """Récupère les sessions d'un utilisateur."""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )

    def process_message(
        self,
        session_id: int,
        user_id: int,
        message: str
    ) -> dict[str, Any]:
        """
        Traite un message utilisateur et génère une réponse.
        Toute l'opération est atomique (commit unique à la fin).
        """
        try:
            session = self.get_session(session_id, user_id)
            if not session:
                raise SessionNotFoundError("Session non trouvée")

            # Enregistrer le message utilisateur (non flushé immédiatement)
            user_message = ChatMessage(
                session_id=session_id,
                message_type=MessageType.USER.value,
                content=message.strip(),
            )
            self.db.add(user_message)

            # Historique (limité aux 10 messages précédents)
            conversation_history = [
                {"role": msg.message_type, "content": msg.content}
                for msg in self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(10)
                .all()[::-1]  # remettre dans l'ordre chronologique
            ]

            query_type = self._analyze_query_type(message)

            context: list[dict[str, Any]] = []
            sources: list[dict[str, Any]] = []
            sql_query: str | None = None
            confidence = 0.7

            if query_type in (QueryType.DATABASE, QueryType.MIXED):
                db_result = self.rag_engine.search_database(message)
                if db_result:
                    context.append(db_result)
                    sources.append({
                        "type": "database",
                        "query": db_result.get("sql_query"),
                    })
                    sql_query = db_result.get("sql_query")

            if query_type in (QueryType.KNOWLEDGE, QueryType.MIXED):
                kb_results = self.rag_engine.search_knowledge_base(message)
                if kb_results:
                    context.extend(kb_results)
                    sources.extend([
                        {
                            "type": "knowledge",
                            "source": doc.get("source"),
                            "title": doc.get("title"),
                        }
                        for doc in kb_results
                    ])
                    confidence = max(
                        (doc.get("similarity", 0.0) for doc in kb_results),
                        default=0.0,
                    )

            if query_type == QueryType.ASSISTANCE:
                sources.append({"type": "assistance"})

            response = self.rag_engine.generate_response(
                message, query_type, context, conversation_history
            )

            assistant_message = ChatMessage(
                session_id=session_id,
                message_type=MessageType.ASSISTANT.value,
                content=response,
                query_type=query_type.value,
                sources=sources,
                confidence=confidence,
                sql_query=sql_query,
            )
            self.db.add(assistant_message)

            # Mise à jour atomique
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(assistant_message)

            return {
                "message_id": assistant_message.id,
                "content": response,
                "query_type": query_type.value,
                "sources": sources,
                "confidence": confidence,
                "sql_query": sql_query,
            }
        except SessionNotFoundError:
            raise
        except Exception as exc:
            self.db.rollback()
            logger.exception("Erreur lors du traitement du message")
            raise ChatbotServiceError(f"Erreur lors du traitement: {str(exc)}") from exc

    def _analyze_query_type(self, query: str) -> QueryType:
        """
        Analyse le type de requête avec une logique de scoring
        plutôt qu'une simple priorité linéaire.
        """
        query_lower = query.lower()

        db_keywords = {
            "combien", "quels", "quelle", "liste", "statistique", "en retard",
            "échéance", "attente", "manquant", "alerte", "fournisseur", "service",
            "budget", "montant", "total", "nombre",
        }
        assistance_keywords = {
            "comment", "créer", "ajouter", "modifier", "supprimer",
            "publier", "valider", "navigation", "utiliser", "aide", "où",
        }
        reg_keywords = {
            "décret", "réglementation", "loi", "article", "ccag", "pmmp",
            "code", "arrêté",
        }

        score_db = sum(1 for kw in db_keywords if kw in query_lower)
        score_assistance = sum(1 for kw in assistance_keywords if kw in query_lower)
        score_reg = sum(1 for kw in reg_keywords if kw in query_lower)

        # Si la requête est clairement une question de données
        if score_db > 0 and score_db >= score_assistance:
            if score_reg > 0:
                return QueryType.MIXED
            return QueryType.DATABASE

        # Si c'est une demande d'aide pure
        if score_assistance > 0 and score_assistance > score_db:
            return QueryType.ASSISTANCE

        # Si c'est une question réglementaire sans donnée
        if score_reg > 0:
            return QueryType.KNOWLEDGE

        return QueryType.KNOWLEDGE

    def add_feedback(
        self,
        message_id: int,
        user_id: int,
        rating: int | None = None,
        is_helpful: bool | None = None,
        comment: str | None = None
    ) -> ChatbotFeedback:
        """Ajoute un feedback sur une réponse."""
        if rating is not None and not (1 <= rating <= 5):
            raise ValueError("Le rating doit être compris entre 1 et 5")

        feedback = ChatbotFeedback(
            message_id=message_id,
            rating=rating,
            is_helpful=is_helpful,
            comment=comment,
            created_by=user_id,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
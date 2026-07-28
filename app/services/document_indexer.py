"""
Service d'indexation des documents pour le Chatbot IA
Module dédié - Indexation des documents réglementaires et internes
"""

import os
import re
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.chatbot import KnowledgeBase, DocumentIndex, DocumentType
from app.models.market import Market
from app.models.stage import Stage
from app.models.document import Document
from app.services.chatbot_service import EmbeddingProvider


class DocumentIndexer:
    """Service d'indexation des documents"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_provider = EmbeddingProvider()
    
    def index_regulatory_document(
        self,
        title: str,
        content: str,
        source: str,
        category: str,
        document_type: DocumentType = DocumentType.REGLEMENTATION,
        tags: List[str] = None
    ) -> KnowledgeBase:
        """
        Indexe un document réglementaire
        """
        # Découper le contenu en chunks si nécessaire
        chunks = self._split_into_chunks(content, max_length=1000)
        
        indexed_docs = []
        for i, chunk in enumerate(chunks):
            # Générer l'embedding
            embedding = self.embedding_provider.get_embedding(chunk)
            
            doc = KnowledgeBase(
                document_type=document_type.value,
                title=f"{title} (Partie {i+1}/{len(chunks)})" if len(chunks) > 1 else title,
                description=title,
                content=chunk,
                chunk_id=f"{source}_{i}",
                chunk_index=i,
                source=source,
                category=category,
                tags=tags or [],
                embedding=embedding,
                language="fr"
            )
            
            self.db.add(doc)
            indexed_docs.append(doc)
        
        self.db.commit()
        
        return indexed_docs[0] if indexed_docs else None
    
    def index_internal_document(
        self,
        document_type: str,
        document_id: int,
        title: str,
        content: str,
        doc_metadata: Dict = None
    ) -> DocumentIndex:
        """
        Indexe un document interne de l'application
        """
        # Générer l'embedding
        embedding = self.embedding_provider.get_embedding(content)
        
        doc = DocumentIndex(
            document_type=document_type,
            document_id=document_id,
            title=title,
            content=content,
            doc_metadata=doc_metadata or {},
            embedding=embedding
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        return doc
    
    def index_market(self, market_id: int) -> List[DocumentIndex]:
        """
        Indexe un marché et ses informations
        """
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            return []
        
        indexed_docs = []
        
        # Indexer les informations principales du marché
        content = f"""
        Marché {market.market_number}
        Objet: {market.object}
        Maître d'ouvrage: {market.master_of_work}
        Type de marché: {market.market_type}
        Procédure: {market.procurement_method}
        Montant estimé: {market.estimated_amount}
        Montant définitif: {market.definitive_amount}
        Statut: {market.status}
        Progression: {market.progress_percentage}%
        Service responsable: {market.responsible_service}
        Date de publication: {market.publication_date}
        Date d'ouverture: {market.opening_date}
        Date d'attribution: {market.attribution_date}
        Date de début: {market.start_date}
        Date de fin prévue: {market.expected_end_date}
        Observations: {market.observations}
        """
        
        doc = self.index_internal_document(
            document_type="market",
            document_id=market.id,
            title=f"Marché {market.market_number} - {market.object}",
            content=content.strip(),
            doc_metadata={
                'market_number': market.market_number,
                'status': market.status,
                'market_type': market.market_type
            }
        )
        indexed_docs.append(doc)
        
        # Indexer les étapes du marché
        stages = self.db.query(Stage).filter(Stage.market_id == market_id).all()
        for stage in stages:
            stage_content = f"""
            Étape: {stage.name}
            Code: {stage.code}
            Description: {stage.description}
            Catégorie: {stage.category}
            Statut: {stage.status}
            Progression: {stage.progress_percentage}%
            Date prévue: {stage.planned_date}
            Date réelle: {stage.actual_date}
            En retard: {stage.is_late}
            """
            
            doc = self.index_internal_document(
                document_type="stage",
                document_id=stage.id,
                title=f"Étape {stage.name} - Marché {market.market_number}",
                content=stage_content.strip(),
                doc_metadata={
                    'market_id': market.id,
                    'stage_name': stage.name,
                    'status': stage.status
                }
            )
            indexed_docs.append(doc)
        
        # Indexer les documents du marché
        documents = self.db.query(Document).filter(Document.market_id == market_id).all()
        for doc in documents:
            doc_content = f"""
            Document: {doc.title}
            Type: {doc.document_type}
            Description: {doc.description}
            Date du document: {doc.document_date}
            Statut: {doc.status}
            """
            
            indexed_doc = self.index_internal_document(
                document_type="document",
                document_id=doc.id,
                title=f"Document {doc.title} - Marché {market.market_number}",
                content=doc_content.strip(),
                doc_metadata={
                    'market_id': market.id,
                    'document_type': doc.document_type
                }
            )
            indexed_docs.append(indexed_doc)
        
        return indexed_docs
    
    def index_all_markets(self, limit: int = 100) -> int:
        """
        Indexe tous les marchés de la base de données
        """
        markets = self.db.query(Market).order_by(Market.created_at.desc()).limit(limit).all()
        
        count = 0
        for market in markets:
            try:
                self.index_market(market.id)
                count += 1
            except Exception as e:
                print(f"Erreur lors de l'indexation du marché {market.id}: {e}")
        
        return count
    
    def reindex_document(self, doc_id: int) -> Optional[KnowledgeBase]:
        """
        Réindexe un document existant
        """
        doc = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == doc_id).first()
        if not doc:
            return None
        
        # Régénérer l'embedding
        doc.embedding = self.embedding_provider.get_embedding(doc.content)
        doc.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(doc)
        
        return doc
    
    def delete_document(self, doc_id: int) -> bool:
        """
        Supprime un document de l'index
        """
        doc = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == doc_id).first()
        if not doc:
            return False
        
        self.db.delete(doc)
        self.db.commit()
        
        return True
    
    def search_by_category(self, category: str, limit: int = 20) -> List[KnowledgeBase]:
        """
        Recherche des documents par catégorie
        """
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.category == category,
            KnowledgeBase.is_active == True
        ).limit(limit).all()
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Retourne des statistiques sur l'index
        """
        total_kb = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.is_active == True
        ).count()
        
        total_docs = self.db.query(DocumentIndex).filter(
            DocumentIndex.is_active == True
        ).count()
        
        by_type = {}
        for doc_type in DocumentType:
            count = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.document_type == doc_type.value,
                KnowledgeBase.is_active == True
            ).count()
            by_type[doc_type.value] = count
        
        return {
            'total_knowledge_base': total_kb,
            'total_documents': total_docs,
            'by_type': by_type
        }
    
    def _split_into_chunks(self, text: str, max_length: int = 1000) -> List[str]:
        """
        Découpe un texte en chunks pour l'indexation
        """
        # Nettoyer le texte
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class RegulatoryDocumentLoader:
    """Chargeur de documents réglementaires"""
    
    @staticmethod
    def load_decret_2_22_431() -> List[Dict[str, str]]:
        """
        Charge les articles du Décret n°2-22-431
        Retourne une liste de dictionnaires avec les articles
        """
        articles = [
            {
                'title': 'Article 1 - Champ d\'application',
                'content': 'Le présent décret fixe les règles relatives à la passation, à l\'exécution et au contrôle des marchés publics conclus par l\'Etat, les établissements publics, les collectivités territoriales et les autres personnes morales de droit public.',
                'category': 'Généralités',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 2 - Définitions',
                'content': 'On entend par marché public, tout contrat à titre onéreux conclu entre un maître d\'ouvrage public et une personne physique ou morale pour répondre à ses besoins en matière de travaux, de fournitures ou de services.',
                'category': 'Généralités',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 3 - Principes fondamentaux',
                'content': 'Les marchés publics sont passés et exécutés conformément aux principes de liberté d\'accès, d\'égalité de traitement des candidats, de transparence des procédures et d\'efficacité de la dépense publique.',
                'category': 'Généralités',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 4 - Types de procédures',
                'content': 'Les marchés publics sont conclus selon les procédures suivantes : appel d\'offres ouvert, appel d\'offres restreint, procédure négociée, consultation, bon de commande, et marché de conception-réalisation.',
                'category': 'Procédures',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 5 - Appel d\'offres ouvert',
                'content': 'L\'appel d\'offres ouvert est la procédure par laquelle le maître d\'ouvrage public invite tous les candidats intéressés à présenter une offre. Les offres sont ouvertes en séance publique.',
                'category': 'Procédures',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 6 - Délai de publication',
                'content': 'L\'avis d\'appel d\'offres est publié sur le Portail Marocain des Marchés Publics (PMMP) au moins 15 jours avant la date limite de réception des offres pour les marchés de travaux et de fournitures, et 10 jours pour les marchés de services.',
                'category': 'Publication',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 7 - Critères d\'attribution',
                'content': 'Les offres sont évaluées sur la base de critères préalablement définis dans le dossier de consultation, notamment le prix, la qualité technique, les délais d\'exécution, et les garanties offertes.',
                'category': 'Attribution',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 8 - Délai de validité des offres',
                'content': 'La durée de validité des offres est fixée par le maître d\'ouvrage public. Elle ne peut être inférieure à 90 jours à compter de la date limite de réception des offres.',
                'category': 'Offres',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 9 - Délai d\'attente (standstill)',
                'content': 'Un délai d\'attente de 10 jours minimum est observé entre la décision d\'attribution et la notification de l\'attribution au soumissionnaire retenu.',
                'category': 'Attribution',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 10 - Notification d\'attribution',
                'content': 'La décision d\'attribution est notifiée au soumissionnaire retenu dans un délai de 15 jours à compter de l\'expiration du délai d\'attente.',
                'category': 'Attribution',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 11 - Garantie soumissionnaire',
                'content': 'Le soumissionnaire doit fournir une garantie soumissionnaire d\'un montant généralement égal à 1% du montant estimé du marché. Cette garantie est libérée après la signature du marché.',
                'category': 'Garanties',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 12 - Garantie d\'exécution',
                'content': 'Le titulaire du marché doit constituer une garantie d\'exécution d\'un montant généralement égal à 5% du montant du marché. Cette garantie est libérée après réception définitive.',
                'category': 'Garanties',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 13 - Ordre de service',
                'content': 'L\'ordre de service notifie au titulaire le début des travaux ou l\'exécution des prestations. Il fixe la date de début d\'exécution et les délais d\'exécution.',
                'category': 'Exécution',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 14 - Réception provisoire',
                'content': 'La réception provisoire est prononcée à l\'achèvement des travaux ou à la livraison des fournitures. Elle constate la conformité avec les stipulations du marché.',
                'category': 'Réception',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 15 - Réception définitive',
                'content': 'La réception définitive est prononcée à l\'expiration de la période de garantie, généralement fixée à un an à compter de la réception provisoire.',
                'category': 'Réception',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 16 - Délai de paiement',
                'content': 'Le paiement est effectué dans un délai de 30 à 90 jours à compter de la date de la facture ou de la situation de travaux, selon les dispositions du marché.',
                'category': 'Paiement',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 17 - Avenants',
                'content': 'Les avenants au marché ne peuvent modifier son objet ni augmenter son montant de plus de 20% du montant initial du marché.',
                'category': 'Modification',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 18 - Résiliation',
                'content': 'Le marché peut être résilié en cas de faute du titulaire, de force majeure, ou d\'intérêt général. La résiliation est prononcée par décision motivée du maître d\'ouvrage.',
                'category': 'Résiliation',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 19 - Contentieux',
                'content': 'Tout soumissionnaire écarté peut introduire un recours auprès de la commission de recours dans un délai de 15 jours à compter de la notification de la décision.',
                'category': 'Recours',
                'source': 'Décret n°2-22-431'
            },
            {
                'title': 'Article 20 - Sanctions',
                'content': 'Le non-respect des obligations du marché peut entraîner des sanctions, notamment des pénalités de retard, la réduction du montant du marché, ou l\'exclusion du soumissionnaire des marchés publics.',
                'category': 'Sanctions',
                'source': 'Décret n°2-22-431'
            }
        ]
        
        return articles
    
    @staticmethod
    def load_ccag_travaux() -> List[Dict[str, str]]:
        """
        Charge les articles du CCAG Travaux
        """
        articles = [
            {
                'title': 'CCAG Travaux - Article 1 - Objet',
                'content': 'Le Cahier des Clauses Administratives Générales (CCAG) Travaux s\'applique à tous les marchés publics de travaux conclus par les maîtres d\'ouvrage publics.',
                'category': 'Généralités',
                'source': 'CCAG Travaux'
            },
            {
                'title': 'CCAG Travaux - Article 2 - Définitions',
                'content': 'On entend par travaux, tous les ouvrages de bâtiment, de génie civil, d\'infrastructures et tous les travaux connexes nécessaires à leur réalisation.',
                'category': 'Généralités',
                'source': 'CCAG Travaux'
            },
            {
                'title': 'CCAG Travaux - Article 3 - Pénalités de retard',
                'content': 'En cas de retard dans l\'exécution des travaux, des pénalités sont appliquées. Le taux des pénalités est fixé à 1/1000 du montant du marché par jour de retard.',
                'category': 'Sanctions',
                'source': 'CCAG Travaux'
            },
            {
                'title': 'CCAG Travaux - Article 4 - Réception',
                'content': 'La réception des travaux est prononcée par le maître d\'ouvrage après vérification de la conformité avec les stipulations du marché et les documents techniques.',
                'category': 'Réception',
                'source': 'CCAG Travaux'
            }
        ]
        
        return articles
    
    @staticmethod
    def load_pmmp_guide() -> List[Dict[str, str]]:
        """
        Charge le guide du Portail Marocain des Marchés Publics
        """
        articles = [
            {
                'title': 'Guide PMMP - Introduction',
                'content': 'Le Portail Marocain des Marchés Publics (PMMP) est la plateforme officielle de publication des avis d\'appel d\'offres et des résultats des marchés publics au Maroc.',
                'category': 'Généralités',
                'source': 'Guide PMMP'
            },
            {
                'title': 'Guide PMMP - Publication',
                'content': 'Tous les avis d\'appel d\'offres doivent être publiés sur le PMMP. La publication est obligatoire pour les marchés supérieurs à 200 000 DH.',
                'category': 'Publication',
                'source': 'Guide PMMP'
            },
            {
                'title': 'Guide PMMP - Inscription',
                'content': 'Les entreprises souhaitant participer aux marchés publics doivent s\'inscrire sur le PMMP et obtenir un identifiant unique.',
                'category': 'Inscription',
                'source': 'Guide PMMP'
            }
        ]
        
        return articles

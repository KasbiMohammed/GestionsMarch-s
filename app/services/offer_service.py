"""
Service de gestion des offres
Module 6: Réception des offres
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.offer_management import (
    PMMPPublication, Offer, OfferDocument,
    PublicationStatus, OfferStatus
)
from app.models.market import Company
from app.models.history import History


class OfferService:
    """Service pour la gestion des offres"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_company(self, company_data: dict) -> Company:
        """
        Crée une entreprise soumissionnaire
        
        Args:
            company_data: Données de l'entreprise
            
        Returns:
            Instance de Company créée
        """
        # Vérifier si l'entreprise existe déjà
        existing = self.db.query(Company).filter(
            Company.rc_number == company_data.get('rc_number')
        ).first()
        
        if existing:
            return existing
        
        company = Company(
            name=company_data['name'],
            legal_form=company_data.get('legal_form'),
            rc_number=company_data.get('rc_number'),
            if_number=company_data.get('if_number'),
            tax_id=company_data.get('tax_id'),
            address=company_data.get('address'),
            city=company_data.get('city'),
            country=company_data.get('country', 'Maroc'),
            phone=company_data.get('phone'),
            email=company_data.get('email'),
            contact_person=company_data.get('contact_person'),
            contact_position=company_data.get('contact_position'),
            created_at=datetime.utcnow()
        )
        
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        
        return company
    
    def create_offer(self, offer_data: dict, user_id: int) -> Offer:
        """
        Crée une offre
        
        Args:
            offer_data: Données de l'offre
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de Offer créée
        """
        offer = Offer(
            market_id=offer_data['market_id'],
            company_id=offer_data['company_id'],
            offer_reference=offer_data['offer_reference'],
            submission_date=offer_data['submission_date'],
            financial_amount=offer_data['financial_amount'],
            currency=offer_data.get('currency', 'MAD'),
            status=OfferStatus.RECEIVED,
            received_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(offer)
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def add_offer_document(self, offer_id: int, document_data: dict) -> OfferDocument:
        """
        Ajoute un document à une offre
        
        Args:
            offer_id: ID de l'offre
            document_data: Données du document
            
        Returns:
            Instance de OfferDocument créée
        """
        document = OfferDocument(
            offer_id=offer_id,
            document_type=document_data['document_type'],
            document_name=document_data['document_name'],
            file_path=document_data['file_path'],
            file_size=document_data.get('file_size'),
            file_hash=document_data.get('file_hash'),
            uploaded_at=datetime.utcnow()
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def validate_administrative_compliance(self, offer_id: int, compliant: bool, validator_id: int, comments: str = None) -> Offer:
        """
        Valide la conformité administrative d'une offre
        
        Args:
            offer_id: ID de l'offre
            compliant: Si conforme
            validator_id: ID du validateur
            comments: Commentaires
            
        Returns:
            Instance de Offer mise à jour
        """
        offer = self.db.query(Offer).filter(
            Offer.id == offer_id
        ).first()
        
        if not offer:
            raise ValueError("Offre non trouvée")
        
        offer.administrative_compliance = compliant
        offer.updated_by = validator_id
        offer.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def validate_technical_compliance(self, offer_id: int, compliant: bool, validator_id: int, comments: str = None) -> Offer:
        """
        Valide la conformité technique d'une offre
        
        Args:
            offer_id: ID de l'offre
            compliant: Si conforme
            validator_id: ID du validateur
            comments: Commentaires
            
        Returns:
            Instance de Offer mise à jour
        """
        offer = self.db.query(Offer).filter(
            Offer.id == offer_id
        ).first()
        
        if not offer:
            raise ValueError("Offre non trouvée")
        
        offer.technical_compliance = compliant
        offer.updated_by = validator_id
        offer.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def validate_overall_compliance(self, offer_id: int, validator_id: int) -> Offer:
        """
        Valide la conformité globale d'une offre
        
        Args:
            offer_id: ID de l'offre
            validator_id: ID du validateur
            
        Returns:
            Instance de Offer mise à jour
        """
        offer = self.db.query(Offer).filter(
            Offer.id == offer_id
        ).first()
        
        if not offer:
            raise ValueError("Offre non trouvée")
        
        # La conformité globale est vraie si administrative et technique sont conformes
        offer.overall_compliance = (
            offer.administrative_compliance and 
            offer.technical_compliance
        )
        
        # Mettre à jour le statut
        if offer.overall_compliance:
            offer.status = OfferStatus.ADMISSIBLE
        else:
            offer.status = OfferStatus.INADMISSIBLE
        
        offer.updated_by = validator_id
        offer.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def verify_digital_signature(self, offer_id: int, signature_hash: str) -> Offer:
        """
        Vérifie la signature électronique d'une offre
        
        Args:
            offer_id: ID de l'offre
            signature_hash: Hash de la signature
            
        Returns:
            Instance de Offer mise à jour
        """
        offer = self.db.query(Offer).filter(
            Offer.id == offer_id
        ).first()
        
        if not offer:
            raise ValueError("Offre non trouvée")
        
        # Dans une implémentation réelle, on vérifierait la signature avec une clé publique
        # Ici on simule la vérification
        offer.digital_signature = signature_hash
        offer.signature_verified = True
        
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def rank_offer(self, offer_id: int, rank: int, score: float, user_id: int) -> Offer:
        """
        Classe une offre
        
        Args:
            offer_id: ID de l'offre
            rank: Rang
            score: Score
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Offer classée
        """
        offer = self.db.query(Offer).filter(
            Offer.id == offer_id
        ).first()
        
        if not offer:
            raise ValueError("Offre non trouvée")
        
        offer.rank = rank
        offer.score = score
        offer.status = OfferStatus.SELECTED if rank == 1 else OfferStatus.REJECTED
        offer.updated_by = user_id
        offer.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def withdraw_offer(self, offer_id: int, user_id: int) -> Offer:
        """
        Retire une offre
        
        Args:
            offer_id: ID de l'offre
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de Offer retirée
        """
        offer = self.db.query(Offer).filter(
            Offer.id == offer_id
        ).first()
        
        if not offer:
            raise ValueError("Offre non trouvée")
        
        offer.status = OfferStatus.WITHDRAWN
        offer.updated_by = user_id
        offer.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(offer)
        
        return offer
    
    def get_offers_by_market(self, market_id: int, status: OfferStatus = None) -> List[Offer]:
        """
        Récupère les offres d'un marché
        
        Args:
            market_id: ID du marché
            status: Statut optionnel
            
        Returns:
            Liste des offres
        """
        query = self.db.query(Offer).filter(
            Offer.market_id == market_id
        )
        
        if status:
            query = query.filter(Offer.status == status)
        
        return query.order_by(Offer.financial_amount).all()
    
    def get_admissible_offers(self, market_id: int) -> List[Offer]:
        """
        Récupère les offres admissibles d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Liste des offres admissibles
        """
        return self.db.query(Offer).filter(
            and_(
                Offer.market_id == market_id,
                Offer.status == OfferStatus.ADMISSIBLE
            )
        ).order_by(Offer.financial_amount).all()
    
    def get_offer_statistics(self, market_id: int) -> Dict:
        """
        Récupère les statistiques des offres d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire des statistiques
        """
        offers = self.db.query(Offer).filter(
            Offer.market_id == market_id
        ).all()
        
        if not offers:
            return {
                'total_offers': 0,
                'admissible_offers': 0,
                'inadmissible_offers': 0,
                'withdrawn_offers': 0,
                'average_amount': 0,
                'min_amount': 0,
                'max_amount': 0
            }
        
        amounts = [o.financial_amount for o in offers]
        
        return {
            'total_offers': len(offers),
            'admissible_offers': len([o for o in offers if o.status == OfferStatus.ADMISSIBLE]),
            'inadmissible_offers': len([o for o in offers if o.status == OfferStatus.INADMISSIBLE]),
            'withdrawn_offers': len([o for o in offers if o.status == OfferStatus.WITHDRAWN]),
            'average_amount': sum(amounts) / len(amounts),
            'min_amount': min(amounts),
            'max_amount': max(amounts)
        }
    
    def create_pmmp_publication(self, publication_data: dict, user_id: int) -> PMMPPublication:
        """
        Crée une publication PMMP
        
        Args:
            publication_data: Données de la publication
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de PMMPPublication créée
        """
        publication = PMMPPublication(
            market_id=publication_data['market_id'],
            pmmp_reference=publication_data.get('pmmp_reference'),
            pmmp_url=publication_data.get('pmmp_url'),
            publication_date=publication_data.get('publication_date'),
            closing_date=publication_data.get('closing_date'),
            opening_date=publication_data.get('opening_date'),
            status=PublicationStatus.DRAFT,
            published_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(publication)
        self.db.commit()
        self.db.refresh(publication)
        
        return publication
    
    def publish_to_pmmp(self, publication_id: int, user_id: int) -> PMMPPublication:
        """
        Publie sur le portail PMMP
        
        Args:
            publication_id: ID de la publication
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de PMMPPublication publiée
        """
        publication = self.db.query(PMMPPublication).filter(
            PMMPPublication.id == publication_id
        ).first()
        
        if not publication:
            raise ValueError("Publication non trouvée")
        
        publication.status = PublicationStatus.PUBLISHED
        publication.publication_date = datetime.utcnow()
        publication.published_by = user_id
        publication.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(publication)
        
        return publication
    
    def track_downloads(self, publication_id: int) -> PMMPPublication:
        """
        Incrémente le compteur de téléchargements
        
        Args:
            publication_id: ID de la publication
            
        Returns:
            Instance de PMMPPublication mise à jour
        """
        publication = self.db.query(PMMPPublication).filter(
            PMMPPublication.id == publication_id
        ).first()
        
        if not publication:
            raise ValueError("Publication non trouvée")
        
        publication.downloads_count += 1
        publication.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(publication)
        
        return publication


def get_offer_service(db: Session) -> OfferService:
    """
    Factory pour créer une instance du service d'offres
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de OfferService
    """
    return OfferService(db)

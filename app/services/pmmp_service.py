"""
Service d'intégration avec l'API PMMP
Module 5: Publication PMMP - Connexion API, suivi des publications
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from app.models.offer_management import PMMPPublication, PublicationStatus
from app.models.market import Market

logger = logging.getLogger(__name__)


class PMMPService:
    """Service pour l'intégration avec le portail PMMP"""
    
    PMMP_BASE_URL = "https://www.marchespublics.gov.ma"
    PMMP_API_URL = "https://www.marchespublics.gov.ma/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def login(self, username: str, password: str) -> bool:
        """
        Connexion au portail PMMP
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            
        Returns:
            True si connexion réussie
        """
        try:
            login_url = f"{self.PMMP_BASE_URL}/login"
            
            # Récupérer la page de login pour obtenir le token CSRF
            response = self.session.get(login_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrf_token'})
            
            # Effectuer la connexion
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token.get('value') if csrf_token else None
            }
            
            response = self.session.post(login_url, data=login_data)
            
            if response.status_code == 200 and 'dashboard' in response.url:
                logger.info("Connexion PMMP réussie")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion PMMP: {e}")
            return False
    
    def publish_market(self, market_id: int, publication_data: dict) -> Dict:
        """
        Publie un marché sur le portail PMMP
        
        Args:
            market_id: ID du marché
            publication_data: Données de publication
            
        Returns:
            Dictionnaire avec le résultat de la publication
        """
        try:
            # Préparer les données pour l'API PMMP
            pmmp_data = {
                'reference': publication_data.get('reference'),
                'objet': publication_data.get('object'),
                'type_marche': publication_data.get('market_type'),
                'procedure': publication_data.get('procurement_method'),
                'montant_estime': publication_data.get('estimated_amount'),
                'date_publication': publication_data.get('publication_date'),
                'date_limite': publication_data.get('closing_date'),
                'date_ouverture': publication_data.get('opening_date'),
                'lieu_execution': publication_data.get('execution_location'),
                'caution': publication_data.get('guarantee_amount'),
                'pieces_jointes': publication_data.get('documents', [])
            }
            
            # Appel à l'API PMMP
            publish_url = f"{self.PMMP_API_URL}/marches/publier"
            response = self.session.post(publish_url, json=pmmp_data)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'pmmp_reference': result.get('reference'),
                    'pmmp_url': f"{self.PMMP_BASE_URL}/marches/{result.get('reference')}",
                    'publication_date': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la publication PMMP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_publication_status(self, pmmp_reference: str) -> Dict:
        """
        Récupère le statut d'une publication PMMP
        
        Args:
            pmmp_reference: Référence PMMP
            
        Returns:
            Dictionnaire avec le statut
        """
        try:
            status_url = f"{self.PMMP_API_URL}/marches/{pmmp_reference}/status"
            response = self.session.get(status_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'error',
                    'message': 'Impossible de récupérer le statut'
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut PMMP: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def download_documents(self, pmmp_reference: str) -> List[Dict]:
        """
        Télécharge les documents d'une publication PMMP
        
        Args:
            pmmp_reference: Référence PMMP
            
        Returns:
            Liste des documents téléchargés
        """
        try:
            docs_url = f"{self.PMMP_API_URL}/marches/{pmmp_reference}/documents"
            response = self.session.get(docs_url)
            
            if response.status_code == 200:
                documents = response.json()
                return documents
            else:
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement des documents PMMP: {e}")
            return []
    
    def track_publication(self, pmmp_reference: str) -> Dict:
        """
        Suit une publication PMMP (téléchargements, vues)
        
        Args:
            pmmp_reference: Référence PMMP
            
        Returns:
            Statistiques de suivi
        """
        try:
            stats_url = f"{self.PMMP_API_URL}/marches/{pmmp_reference}/statistiques"
            response = self.session.get(stats_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'downloads': 0,
                    'views': 0,
                    'offers': 0
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du suivi de la publication PMMP: {e}")
            return {
                'downloads': 0,
                'views': 0,
                'offers': 0
            }
    
    def withdraw_publication(self, pmmp_reference: str, reason: str) -> bool:
        """
        Retire une publication PMMP
        
        Args:
            pmmp_reference: Référence PMMP
            reason: Motif du retrait
            
        Returns:
            True si retrait réussi
        """
        try:
            withdraw_url = f"{self.PMMP_API_URL}/marches/{pmmp_reference}/retirer"
            response = self.session.post(withdraw_url, json={'reason': reason})
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erreur lors du retrait de la publication PMMP: {e}")
            return False
    
    def get_market_info(self, pmmp_reference: str) -> Optional[Dict]:
        """
        Récupère les informations d'un marché depuis PMMP
        
        Args:
            pmmp_reference: Référence PMMP
            
        Returns:
            Dictionnaire des informations du marché
        """
        try:
            market_url = f"{self.PMMP_BASE_URL}/marches/{pmmp_reference}"
            response = self.session.get(market_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extraire les informations du marché
                info = {
                    'reference': pmmp_reference,
                    'object': self._extract_text(soup, 'objet'),
                    'owner': self._extract_text(soup, 'maitre_ouvrage'),
                    'estimated_amount': self._extract_amount(soup, 'montant_estime'),
                    'publication_date': self._extract_date(soup, 'date_publication'),
                    'closing_date': self._extract_date(soup, 'date_limite'),
                    'procedure': self._extract_text(soup, 'procedure')
                }
                
                return info
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos PMMP: {e}")
            return None
    
    def search_markets(self, criteria: dict) -> List[Dict]:
        """
        Recherche des marchés sur PMMP
        
        Args:
            criteria: Critères de recherche
            
        Returns:
            Liste des marchés trouvés
        """
        try:
            search_url = f"{self.PMMP_API_URL}/marches/recherche"
            response = self.session.post(search_url, json=criteria)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche PMMP: {e}")
            return []
    
    def get_offers(self, pmmp_reference: str) -> List[Dict]:
        """
        Récupère les offres d'un marché depuis PMMP
        
        Args:
            pmmp_reference: Référence PMMP
            
        Returns:
            Liste des offres
        """
        try:
            offers_url = f"{self.PMMP_API_URL}/marches/{pmmp_reference}/offres"
            response = self.session.get(offers_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des offres PMMP: {e}")
            return []
    
    def _extract_text(self, soup: BeautifulSoup, field: str) -> str:
        """Extrait un texte du HTML"""
        element = soup.find(class_=field) or soup.find(id=field)
        return element.get_text(strip=True) if element else ''
    
    def _extract_amount(self, soup: BeautifulSoup, field: str) -> Optional[float]:
        """Extrait un montant du HTML"""
        text = self._extract_text(soup, field)
        if text:
            # Nettoyer le texte et extraire le montant
            import re
            match = re.search(r'[\d,]+\.?\d*', text.replace(' ', ''))
            if match:
                return float(match.group().replace(',', '.'))
        return None
    
    def _extract_date(self, soup: BeautifulSoup, field: str) -> Optional[str]:
        """Extrait une date du HTML"""
        text = self._extract_text(soup, field)
        if text:
            # Parser la date française
            from datetime import datetime
            try:
                return datetime.strptime(text, '%d/%m/%Y').isoformat()
            except:
                return None
        return None
    
    def validate_connection(self) -> bool:
        """
        Valide la connexion avec PMMP
        
        Returns:
            True si connexion valide
        """
        try:
            response = self.session.get(f"{self.PMMP_BASE_URL}/api/health")
            return response.status_code == 200
        except:
            return False


class PMMPIntegrationService:
    """Service d'intégration PMMP avec base de données"""
    
    def __init__(self, db):
        self.db = db
        self.pmmp_service = PMMPService()
    
    def publish_market_to_pmmp(self, market_id: int, pmmp_credentials: dict) -> Dict:
        """
        Publie un marché sur PMMP et enregistre dans la base de données
        
        Args:
            market_id: ID du marché
            pmmp_credentials: Identifiants PMMP
            
        Returns:
            Résultat de la publication
        """
        # Récupérer le marché
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            return {'success': False, 'error': 'Marché non trouvé'}
        
        # Connexion à PMMP
        if not self.pmmp_service.login(
            pmmp_credentials.get('username'),
            pmmp_credentials.get('password')
        ):
            return {'success': False, 'error': 'Échec de connexion PMMP'}
        
        # Préparer les données de publication
        publication_data = {
            'reference': market.market_number,
            'object': market.object,
            'market_type': market.type.value if market.type else None,
            'procurement_method': market.procurement_method,
            'estimated_amount': market.estimated_amount,
            'publication_date': datetime.utcnow().isoformat(),
            'closing_date': market.closing_date.isoformat() if market.closing_date else None,
            'opening_date': market.opening_date.isoformat() if market.opening_date else None,
            'execution_location': market.location,
            'guarantee_amount': market.guarantee_amount
        }
        
        # Publier sur PMMP
        result = self.pmmp_service.publish_market(market_id, publication_data)
        
        if result['success']:
            # Enregistrer la publication dans la base de données
            publication = PMMPPublication(
                market_id=market_id,
                pmmp_reference=result['pmmp_reference'],
                pmmp_url=result['pmmp_url'],
                publication_date=datetime.utcnow(),
                status=PublicationStatus.PUBLISHED
            )
            
            self.db.add(publication)
            self.db.commit()
        
        return result
    
    def sync_publication_status(self, publication_id: int) -> Dict:
        """
        Synchronise le statut d'une publication depuis PMMP
        
        Args:
            publication_id: ID de la publication
            
        Returns:
            Statut synchronisé
        """
        publication = self.db.query(PMMPPublication).filter(
            PMMPPublication.id == publication_id
        ).first()
        
        if not publication:
            return {'success': False, 'error': 'Publication non trouvée'}
        
        # Récupérer le statut depuis PMMP
        status = self.pmmp_service.get_publication_status(publication.pmmp_reference)
        
        # Mettre à jour les statistiques
        stats = self.pmmp_service.track_publication(publication.pmmp_reference)
        
        publication.downloads_count = stats.get('downloads', 0)
        publication.views_count = stats.get('views', 0)
        
        self.db.commit()
        
        return {
            'success': True,
            'status': status,
            'statistics': stats
        }
    
    def withdraw_from_pmmp(self, publication_id: int, reason: str) -> bool:
        """
        Retire une publication de PMMP
        
        Args:
            publication_id: ID de la publication
            reason: Motif du retrait
            
        Returns:
            True si retrait réussi
        """
        publication = self.db.query(PMMPPublication).filter(
            PMMPPublication.id == publication_id
        ).first()
        
        if not publication:
            return False
        
        # Retirer de PMMP
        if self.pmmp_service.withdraw_publication(publication.pmmp_reference, reason):
            publication.status = PublicationStatus.WITHDRAWN
            self.db.commit()
            return True
        
        return False


def get_pmmp_service(db=None) -> PMMPService:
    """Factory pour créer une instance du service PMMP"""
    return PMMPService()


def get_pmmp_integration_service(db) -> PMMPIntegrationService:
    """Factory pour créer une instance du service d'intégration PMMP"""
    return PMMPIntegrationService(db)

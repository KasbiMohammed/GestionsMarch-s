"""
Scraper du portail PMMP (Portail des Marchés Publics du Maroc)
Récupération automatique des données des marchés publics
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

from app.config import settings


class PMMPScraper:
    """Classe pour le scraping du portail PMMP"""
    
    def __init__(self):
        self.base_url = settings.PMMP_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Récupère une page web et retourne un objet BeautifulSoup
        
        Args:
            url: URL de la page
            
        Returns:
            Objet BeautifulSoup ou None en cas d'erreur
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'lxml')
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de la page {url}: {e}")
            return None
    
    def extract_market_id_from_url(self, url: str) -> Optional[str]:
        """
        Extrait l'ID du marché depuis l'URL
        
        Args:
            url: URL du marché
            
        Returns:
            ID du marché ou None
        """
        # Pattern typique des URLs PMMP
        patterns = [
            r'id=(\d+)',
            r'consultation/(\d+)',
            r'marche/(\d+)',
            r'(\d+)/?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def scrape_market_from_url(self, url: str) -> Optional[Dict]:
        """
        Scrape les données d'un marché depuis son URL
        
        Args:
            url: URL du marché sur le portail PMMP
            
        Returns:
            Dictionnaire contenant les données du marché ou None
        """
        soup = self.get_page(url)
        if not soup:
            return None
        
        market_data = {
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'raw_html': str(soup)
        }
        
        # Extraction des informations de base
        market_data.update(self._extract_basic_info(soup))
        
        # Extraction des entreprises et montants
        market_data['companies'] = self._extract_companies(soup)
        
        # Extraction des dates importantes
        market_data.update(self._extract_dates(soup))
        
        # Extraction des documents
        market_data['documents'] = self._extract_documents(soup)
        
        return market_data
    
    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict:
        """
        Extrait les informations de base du marché
        
        Args:
            soup: Objet BeautifulSoup
            
        Returns:
            Dictionnaire des informations de base
        """
        info = {}
        
        # Numéro du marché
        number_elem = soup.find(text=re.compile(r'(numéro|N°|reference)', re.I))
        if number_elem:
            info['market_number'] = number_elem.parent.find_next_sibling('td').get_text(strip=True)
        
        # Objet du marché
        object_elem = soup.find(text=re.compile(r'(objet|intitulé|libellé)', re.I))
        if object_elem:
            info['object'] = object_elem.parent.find_next_sibling('td').get_text(strip=True)
        
        # Maître d'ouvrage
        master_elem = soup.find(text=re.compile(r'(maître|maitre|client|acheteur)', re.I))
        if master_elem:
            info['master_of_work'] = master_elem.parent.find_next_sibling('td').get_text(strip=True)
        
        # Type de marché
        type_elem = soup.find(text=re.compile(r'(type|nature|catégorie)', re.I))
        if type_elem:
            info['market_type'] = type_elem.parent.find_next_sibling('td').get_text(strip=True)
        
        # Mode de passation
        procedure_elem = soup.find(text=re.compile(r'(procédure|mode|passation)', re.I))
        if procedure_elem:
            info['procurement_method'] = procedure_elem.parent.find_next_sibling('td').get_text(strip=True)
        
        # Montant estimé
        amount_elem = soup.find(text=re.compile(r'(montant|budget|estimation)', re.I))
        if amount_elem:
            amount_text = amount_elem.parent.find_next_sibling('td').get_text(strip=True)
            info['estimated_amount'] = self._parse_amount(amount_text)
        
        return info
    
    def _extract_companies(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extrait les entreprises participantes et leurs montants
        
        Args:
            soup: Objet BeautifulSoup
            
        Returns:
            Liste des dictionnaires d'entreprises
        """
        companies = []
        
        # Recherche du tableau des offres
        tables = soup.find_all('table')
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            # Vérifier si c'est le tableau des offres
            if any(keyword in ' '.join(headers) for keyword in ['entreprise', 'soumissionnaire', 'offres', 'montant']):
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        company = {
                            'name': cells[0].get_text(strip=True),
                            'offer_amount': self._parse_amount(cells[1].get_text(strip=True))
                        }
                        
                        # Extraire le rang si disponible
                        if len(cells) >= 3:
                            company['rank'] = cells[2].get_text(strip=True)
                        
                        companies.append(company)
        
        return companies
    
    def _extract_dates(self, soup: BeautifulSoup) -> Dict:
        """
        Extrait les dates importantes
        
        Args:
            soup: Objet BeautifulSoup
            
        Returns:
            Dictionnaire des dates
        """
        dates = {}
        
        date_patterns = {
            'publication': r'(publication|diffusion|annonce)',
            'opening': r'(ouverture|plis|remise)',
            'attribution': r'(attribution|résultat)',
            'limit': r'(limite|clôture|délai)'
        }
        
        all_text = soup.get_text()
        
        for date_type, pattern in date_patterns.items():
            match = re.search(pattern + r'[:\s]*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})', all_text, re.I)
            if match:
                dates[date_type] = match.group(1)
        
        return dates
    
    def _extract_documents(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extrait les liens vers les documents
        
        Args:
            soup: Objet BeautifulSoup
            
        Returns:
            Liste des dictionnaires de documents
        """
        documents = []
        
        # Recherche des liens PDF
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in pdf_links:
            doc = {
                'name': link.get_text(strip=True),
                'url': urljoin(self.base_url, link['href'])
            }
            documents.append(doc)
        
        return documents
    
    def _parse_amount(self, text: str) -> Optional[float]:
        """
        Parse un montant depuis une chaîne de caractères
        
        Args:
            text: Chaîne contenant le montant
            
        Returns:
            Montant en float ou None
        """
        # Nettoyer le texte
        text = text.strip()
        
        # Supprimer les espaces et les symboles de devise
        text = re.sub(r'[\s MAD DH]', '', text)
        
        # Remplacer la virgule par un point
        text = text.replace(',', '.')
        
        try:
            return float(text)
        except ValueError:
            return None
    
    def search_markets(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des marchés sur le portail
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des marchés trouvés
        """
        # URL de recherche (à adapter selon la structure réelle du portail)
        search_url = f"{self.base_url}/search"
        
        params = {
            'q': query,
            'limit': limit
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            results = []
            
            # Extraire les résultats de recherche
            result_links = soup.find_all('a', href=re.compile(r'/consultation/'))
            
            for link in result_links[:limit]:
                market_url = urljoin(self.base_url, link['href'])
                market_id = self.extract_market_id_from_url(market_url)
                
                results.append({
                    'id': market_id,
                    'title': link.get_text(strip=True),
                    'url': market_url
                })
            
            return results
            
        except requests.RequestException as e:
            print(f"Erreur lors de la recherche: {e}")
            return []


def scrape_market_data(url: str) -> Optional[Dict]:
    """
    Fonction helper pour scraper les données d'un marché
    
    Args:
        url: URL du marché
        
    Returns:
        Données du marché ou None
    """
    scraper = PMMPScraper()
    return scraper.scrape_market_from_url(url)

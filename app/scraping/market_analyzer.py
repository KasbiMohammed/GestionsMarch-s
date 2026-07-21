"""
Analyseur de marchés publics
Calcul statistique des offres et détection d'anomalies
"""

import numpy as np
from typing import List, Dict, Optional
from statistics import median, mean
import pandas as pd


class MarketAnalyzer:
    """Classe pour l'analyse statistique des offres de marchés"""
    
    def __init__(self):
        self.offers = []
        self.amounts = []
    
    def load_offers(self, companies: List[Dict]) -> None:
        """
        Charge les offres des entreprises
        
        Args:
            companies: Liste des dictionnaires d'entreprises avec montants
        """
        self.offers = []
        self.amounts = []
        
        for company in companies:
            if company.get('offer_amount'):
                self.offers.append(company)
                self.amounts.append(company['offer_amount'])
    
    def calculate_median(self) -> Optional[float]:
        """
        Calcule la médiane des montants
        
        Returns:
            Médiane ou None
        """
        if not self.amounts:
            return None
        return median(self.amounts)
    
    def calculate_mean(self) -> Optional[float]:
        """
        Calcule la moyenne des montants
        
        Returns:
            Moyenne ou None
        """
        if not self.amounts:
            return None
        return mean(self.amounts)
    
    def calculate_trimmed_mean(self, proportion: float = 0.1) -> Optional[float]:
        """
        Calcule la moyenne tronquée (trimmed mean)
        
        Args:
            proportion: Proportion à supprimer de chaque extrémité (0.1 = 10%)
            
        Returns:
            Moyenne tronquée ou None
        """
        if not self.amounts or len(self.amounts) < 3:
            return None
        
        sorted_amounts = sorted(self.amounts)
        n = len(sorted_amounts)
        k = int(n * proportion)
        
        if k == 0:
            return mean(sorted_amounts)
        
        trimmed = sorted_amounts[k:n-k]
        return mean(trimmed)
    
    def calculate_iqr(self) -> Optional[Dict]:
        """
        Calcule l'écart interquartile (IQR)
        
        Returns:
            Dictionnaire contenant Q1, Q3, IQR ou None
        """
        if not self.amounts or len(self.amounts) < 4:
            return None
        
        sorted_amounts = sorted(self.amounts)
        n = len(sorted_amounts)
        
        q1_index = int(n * 0.25)
        q3_index = int(n * 0.75)
        
        q1 = sorted_amounts[q1_index]
        q3 = sorted_amounts[q3_index]
        iqr = q3 - q1
        
        return {
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'lower_bound': q1 - 1.5 * iqr,
            'upper_bound': q3 + 1.5 * iqr
        }
    
    def calculate_reference_price(self, method: str = 'median') -> Optional[float]:
        """
        Calcule le prix de référence selon différentes méthodes
        
        Args:
            method: Méthode de calcul ('median', 'mean', 'trimmed_mean', 'iqr')
            
        Returns:
            Prix de référence ou None
        """
        if method == 'median':
            return self.calculate_median()
        elif method == 'mean':
            return self.calculate_mean()
        elif method == 'trimmed_mean':
            return self.calculate_trimmed_mean()
        elif method == 'iqr':
            iqr_data = self.calculate_iqr()
            if iqr_data:
                return (iqr_data['q1'] + iqr_data['q3']) / 2
        return None
    
    def detect_abnormal_offers(self, method: str = 'iqr') -> Dict:
        """
        Détecte les offres anormalement basses ou élevées
        
        Args:
            method: Méthode de détection ('iqr', 'percentage')
            
        Returns:
            Dictionnaire avec les offres anormales
        """
        if not self.amounts:
            return {'low': [], 'high': []}
        
        abnormal = {'low': [], 'high': []}
        
        if method == 'iqr':
            iqr_data = self.calculate_iqr()
            if iqr_data:
                lower_bound = iqr_data['lower_bound']
                upper_bound = iqr_data['upper_bound']
                
                for offer in self.offers:
                    amount = offer['offer_amount']
                    if amount < lower_bound:
                        abnormal['low'].append({
                            'company': offer['name'],
                            'amount': amount,
                            'deviation': (lower_bound - amount) / lower_bound * 100
                        })
                    elif amount > upper_bound:
                        abnormal['high'].append({
                            'company': offer['name'],
                            'amount': amount,
                            'deviation': (amount - upper_bound) / upper_bound * 100
                        })
        
        elif method == 'percentage':
            # Méthode basée sur le pourcentage par rapport à la moyenne
            avg = self.calculate_mean()
            if avg:
                threshold_low = avg * 0.7  # 30% inférieur à la moyenne
                threshold_high = avg * 1.3  # 30% supérieur à la moyenne
                
                for offer in self.offers:
                    amount = offer['offer_amount']
                    if amount < threshold_low:
                        abnormal['low'].append({
                            'company': offer['name'],
                            'amount': amount,
                            'deviation': (avg - amount) / avg * 100
                        })
                    elif amount > threshold_high:
                        abnormal['high'].append({
                            'company': offer['name'],
                            'amount': amount,
                            'deviation': (amount - avg) / avg * 100
                        })
        
        return abnormal
    
    def rank_companies(self) -> List[Dict]:
        """
        Classe les entreprises par montant d'offre
        
        Returns:
            Liste des entreprises classées
        """
        if not self.offers:
            return []
        
        # Trier par montant croissant
        sorted_offers = sorted(self.offers, key=lambda x: x['offer_amount'])
        
        ranked = []
        for i, offer in enumerate(sorted_offers, 1):
            ranked.append({
                'rank': i,
                'company': offer['name'],
                'amount': offer['offer_amount'],
                'difference_from_median': offer['offer_amount'] - self.calculate_median() if self.calculate_median() else 0,
                'percentage_of_median': (offer['offer_amount'] / self.calculate_median() * 100) if self.calculate_median() else 0
            })
        
        return ranked
    
    def generate_analysis_report(self) -> Dict:
        """
        Génère un rapport d'analyse complet
        
        Returns:
            Dictionnaire contenant toutes les statistiques et analyses
        """
        return {
            'total_offers': len(self.offers),
            'total_amount': sum(self.amounts) if self.amounts else 0,
            'statistics': {
                'median': self.calculate_median(),
                'mean': self.calculate_mean(),
                'trimmed_mean': self.calculate_trimmed_mean(),
                'iqr': self.calculate_iqr(),
                'min': min(self.amounts) if self.amounts else None,
                'max': max(self.amounts) if self.amounts else None,
                'std_dev': np.std(self.amounts) if self.amounts else None
            },
            'reference_prices': {
                'median': self.calculate_reference_price('median'),
                'mean': self.calculate_reference_price('mean'),
                'trimmed_mean': self.calculate_reference_price('trimmed_mean'),
                'iqr': self.calculate_reference_price('iqr')
            },
            'abnormal_offers': {
                'iqr_method': self.detect_abnormal_offers('iqr'),
                'percentage_method': self.detect_abnormal_offers('percentage')
            },
            'ranking': self.rank_companies()
        }


def analyze_offers(companies: List[Dict]) -> Dict:
    """
    Fonction helper pour analyser les offres
    
    Args:
        companies: Liste des entreprises avec montants
        
    Returns:
        Rapport d'analyse complet
    """
    analyzer = MarketAnalyzer()
    analyzer.load_offers(companies)
    return analyzer.generate_analysis_report()

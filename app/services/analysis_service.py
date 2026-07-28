"""
Service d'analyse automatique des offres
Module 7: Analyse automatique
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from statistics import median, mean, stdev
from dataclasses import dataclass

from app.models.offer_management import Offer, OfferStatus
from app.models.market import Market


@dataclass
class AnalysisResult:
    """Résultat de l'analyse"""
    reference_price: Optional[float]
    median: Optional[float]
    mean: Optional[float]
    trimmed_mean: Optional[float]
    std_dev: Optional[float]
    min_amount: Optional[float]
    max_amount: Optional[float]
    abnormal_offers: Dict[str, List[Dict]]
    ranking: List[Dict]
    statistics: Dict


class AnalysisService:
    """Service pour l'analyse automatique des offres"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_offers(self, market_id: int) -> AnalysisResult:
        """
        Analyse automatiquement les offres d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Instance de AnalysisResult
        """
        # Récupérer le marché pour obtenir l'estimation
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        # Récupérer les offres admissibles
        offers = self.db.query(Offer).filter(
            and_(
                Offer.market_id == market_id,
                Offer.status == OfferStatus.ADMISSIBLE
            )
        ).all()
        
        if not offers:
            return AnalysisResult(
                reference_price=None,
                median=None,
                mean=None,
                trimmed_mean=None,
                std_dev=None,
                min_amount=None,
                max_amount=None,
                abnormal_offers={'low': [], 'high': []},
                ranking=[],
                statistics={}
            )
        
        amounts = [o.financial_amount for o in offers]
        
        # Calculer les statistiques
        median_price = median(amounts)
        mean_price = mean(amounts)
        std_dev_price = stdev(amounts) if len(amounts) > 1 else 0
        
        # Calculer la moyenne tronquée (sans les valeurs extrêmes)
        sorted_amounts = sorted(amounts)
        if len(sorted_amounts) > 2:
            trimmed_amounts = sorted_amounts[1:-1]
            trimmed_mean_price = mean(trimmed_amounts)
        else:
            trimmed_mean_price = mean_price
        
        # Calculer le prix de référence avec la formule personnalisée
        estimated_amount = market.estimated_amount if market else 0
        reference_price = self._calculate_reference_price(amounts, estimated_amount)
        
        # Détecter les offres anormales
        abnormal_offers = self._detect_abnormal_offers(offers, median_price, std_dev_price)
        
        # Classer les entreprises
        ranking = self._rank_companies(offers, median_price)
        
        # Statistiques détaillées
        statistics = {
            'total_offers': len(offers),
            'median': median_price,
            'mean': mean_price,
            'trimmed_mean': trimmed_mean_price,
            'std_dev': std_dev_price,
            'min': min(amounts),
            'max': max(amounts),
            'range': max(amounts) - min(amounts),
            'coefficient_of_variation': (std_dev_price / mean_price * 100) if mean_price > 0 else 0
        }
        
        return AnalysisResult(
            reference_price=reference_price,
            median=median_price,
            mean=mean_price,
            trimmed_mean=trimmed_mean_price,
            std_dev=std_dev_price,
            min_amount=min(amounts),
            max_amount=max(amounts),
            abnormal_offers=abnormal_offers,
            ranking=ranking,
            statistics=statistics
        )
    
    def _calculate_reference_price(self, amounts: List[float], estimated_amount: float = 0) -> float:
        """
        Calcule le prix de référence selon la formule personnalisée:
        Prix de référence = (somme des prix / nombre d'entreprises + Estimation) / 2
        
        Args:
            amounts: Liste des montants
            estimated_amount: Montant estimé du marché
            
        Returns:
            Prix de référence
        """
        if not amounts:
            return 0.0
        
        # Calculer la moyenne des offres
        average_offers = sum(amounts) / len(amounts)
        
        # Formule personnalisée: (moyenne des offres + estimation) / 2
        reference_price = (average_offers + estimated_amount) / 2
        
        return reference_price
    
    def _detect_abnormal_offers(self, offers: List[Offer], median: float, std_dev: float) -> Dict[str, List[Dict]]:
        """
        Détecte les offres anormalement basses ou élevées
        
        Args:
            offers: Liste des offres
            median: Médiane des montants
            std_dev: Écart-type
            
        Returns:
            Dictionnaire avec les offres anormales
        """
        abnormal_offers = {'low': [], 'high': []}
        
        # Seuils pour les offres anormales (selon la réglementation)
        low_threshold = median * 0.7  # 30% en dessous de la médiane
        high_threshold = median * 1.3  # 30% au-dessus de la médiane
        
        for offer in offers:
            deviation = ((offer.financial_amount - median) / median) * 100
            
            if offer.financial_amount < low_threshold:
                abnormal_offers['low'].append({
                    'offer_id': offer.id,
                    'company': offer.company.name,
                    'amount': offer.financial_amount,
                    'deviation': deviation,
                    'threshold': low_threshold
                })
            elif offer.financial_amount > high_threshold:
                abnormal_offers['high'].append({
                    'offer_id': offer.id,
                    'company': offer.company.name,
                    'amount': offer.financial_amount,
                    'deviation': deviation,
                    'threshold': high_threshold
                })
        
        return abnormal_offers
    
    def _rank_companies(self, offers: List[Offer], median: float) -> List[Dict]:
        """
        Classe les entreprises selon leurs offres
        
        Args:
            offers: Liste des offres
            median: Médiane des montants
            
        Returns:
            Liste des entreprises classées
        """
        # Trier par montant (croissant pour les travaux, décroissant pour les services)
        sorted_offers = sorted(offers, key=lambda o: o.financial_amount)
        
        ranking = []
        for rank, offer in enumerate(sorted_offers, start=1):
            percentage_of_median = (offer.financial_amount / median) * 100 if median > 0 else 0
            
            ranking.append({
                'rank': rank,
                'offer_id': offer.id,
                'company': offer.company.name,
                'amount': offer.financial_amount,
                'percentage_of_median': percentage_of_median,
                'deviation_from_median': percentage_of_median - 100
            })
        
        return ranking
    
    def generate_analysis_report(self, market_id: int) -> Dict:
        """
        Génère un rapport d'analyse complet
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire du rapport d'analyse
        """
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            raise ValueError("Marché non trouvé")
        
        analysis = self.analyze_offers(market_id)
        
        report = {
            'market_info': {
                'market_number': market.market_number,
                'object': market.object,
                'owner': market.owner,
                'estimated_amount': market.estimated_amount,
                'budget': market.budget
            },
            'analysis': {
                'reference_price': analysis.reference_price,
                'statistics': analysis.statistics,
                'abnormal_offers': analysis.abnormal_offers,
                'ranking': analysis.ranking
            },
            'recommendations': self._generate_recommendations(analysis),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self, analysis: AnalysisResult) -> List[str]:
        """
        Génère des recommandations basées sur l'analyse
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        # Recommandations sur les offres anormales
        if analysis.abnormal_offers['low']:
            recommendations.append(
                f"{len(analysis.abnormal_offers['low'])} offre(s) anormalement basse(s) détectée(s). "
                "Une analyse approfondie est recommandée."
            )
        
        if analysis.abnormal_offers['high']:
            recommendations.append(
                f"{len(analysis.abnormal_offers['high'])} offre(s) anormalement élevée(s) détectée(s). "
                "Vérifiez la cohérence des montants proposés."
            )
        
        # Recommandations sur le prix de référence
        if analysis.reference_price:
            if analysis.statistics.get('coefficient_of_variation', 0) > 20:
                recommendations.append(
                    "Fort dispersion des offres. Le prix de référence peut ne pas être représentatif."
                )
            else:
                recommendations.append(
                    "Dispersion normale des offres. Le prix de référence est fiable."
                )
        
        # Recommandations sur le nombre d'offres
        if analysis.statistics.get('total_offers', 0) < 3:
            recommendations.append(
                "Nombre d'offres insuffisant pour une analyse statistique fiable."
            )
        
        return recommendations
    
    def calculate_iqr(self, amounts: List[float]) -> Optional[float]:
        """
        Calcule l'intervalle interquartile (IQR)
        
        Args:
            amounts: Liste des montants
            
        Returns:
            IQR ou None
        """
        if len(amounts) < 4:
            return None
        
        sorted_amounts = sorted(amounts)
        n = len(sorted_amounts)
        
        q1_index = n // 4
        q3_index = 3 * n // 4
        
        q1 = sorted_amounts[q1_index]
        q3 = sorted_amounts[q3_index]
        
        return q3 - q1
    
    def detect_outliers_iqr(self, offers: List[Offer]) -> List[Dict]:
        """
        Détecte les valeurs aberrantes en utilisant l'IQR
        
        Args:
            offers: Liste des offres
            
        Returns:
            Liste des offres aberrantes
        """
        amounts = [o.financial_amount for o in offers]
        iqr = self.calculate_iqr(amounts)
        
        if not iqr:
            return []
        
        sorted_amounts = sorted(amounts)
        n = len(sorted_amounts)
        
        q1_index = n // 4
        q3_index = 3 * n // 4
        
        q1 = sorted_amounts[q1_index]
        q3 = sorted_amounts[q3_index]
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for offer in offers:
            if offer.financial_amount < lower_bound or offer.financial_amount > upper_bound:
                outliers.append({
                    'offer_id': offer.id,
                    'company': offer.company.name,
                    'amount': offer.financial_amount,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                })
        
        return outliers


def get_analysis_service(db: Session) -> AnalysisService:
    """
    Factory pour créer une instance du service d'analyse
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de AnalysisService
    """
    return AnalysisService(db)

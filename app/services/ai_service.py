"""
Service d'intelligence artificielle
Module 14: Intelligence artificielle - Analyse CPS, détection incohérences, prédictions
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import re

from app.models.market_preparation import MarketPreparation, CPS
from app.models.market import Market
from app.models.stage import Stage


class AIService:
    """Service pour les fonctionnalités d'intelligence artificielle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_cps(self, cps_id: int) -> Dict:
        """
        Analyse automatique du CPS
        
        Args:
            cps_id: ID du CPS
            
        Returns:
            Dictionnaire avec l'analyse du CPS
        """
        cps = self.db.query(CPS).filter(
            CPS.id == cps_id
        ).first()
        
        if not cps:
            raise ValueError("CPS non trouvé")
        
        analysis = {
            'completeness': self._check_cps_completeness(cps),
            'missing_sections': self._detect_missing_sections(cps),
            'inconsistencies': self._detect_inconsistencies(cps),
            'suggestions': self._generate_cps_suggestions(cps),
            'risk_assessment': self._assess_cps_risks(cps),
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        return analysis
    
    def _check_cps_completeness(self, cps: CPS) -> Dict:
        """Vérifie la complétude du CPS"""
        required_sections = {
            'general_conditions': cps.general_conditions,
            'special_conditions': cps.special_conditions,
            'technical_specifications': cps.technical_specifications,
            'administrative_clauses': cps.administrative_clauses,
            'financial_clauses': cps.financial_clauses,
            'legal_clauses': cps.legal_clauses
        }
        
        completed = sum(1 for section in required_sections.values() if section)
        total = len(required_sections)
        
        return {
            'percentage': (completed / total * 100) if total > 0 else 0,
            'completed_sections': completed,
            'total_sections': total,
            'section_status': {
                section: bool(content)
                for section, content in required_sections.items()
            }
        }
    
    def _detect_missing_sections(self, cps: CPS) -> List[str]:
        """Détecte les sections manquantes du CPS"""
        missing = []
        
        if not cps.general_conditions:
            missing.append("Conditions générales")
        if not cps.special_conditions:
            missing.append("Conditions spéciales")
        if not cps.technical_specifications:
            missing.append("Spécifications techniques")
        if not cps.administrative_clauses:
            missing.append("Clauses administratives")
        if not cps.financial_clauses:
            missing.append("Clauses financières")
        if not cps.legal_clauses:
            missing.append("Clauses juridiques")
        
        return missing
    
    def _detect_inconsistencies(self, cps: CPS) -> List[Dict]:
        """Détecte les incohérences dans le CPS"""
        inconsistencies = []
        
        # Vérifier les incohérences de montants
        if cps.technical_specifications and cps.financial_clauses:
            # Recherche de montants dans les spécifications techniques
            tech_amounts = re.findall(r'(\d+(?:,\d+)*)\s*(?:MAD|DH|Dirham)', cps.technical_specifications)
            fin_amounts = re.findall(r'(\d+(?:,\d+)*)\s*(?:MAD|DH|Dirham)', cps.financial_clauses)
            
            if tech_amounts and fin_amounts:
                # Comparaison simplifiée
                inconsistencies.append({
                    'type': 'montant',
                    'description': 'Vérifier la cohérence des montants entre spécifications techniques et clauses financières',
                    'severity': 'medium'
                })
        
        # Vérifier les incohérences de délais
        if cps.administrative_clauses:
            deadlines = re.findall(r'(\d+)\s*(?:jours|semaines|mois)', cps.administrative_clauses)
            if len(set(deadlines)) > 3:
                inconsistencies.append({
                    'type': 'délai',
                    'description': 'Multiples délais différents détectés, vérifier la cohérence',
                    'severity': 'low'
                })
        
        return inconsistencies
    
    def _generate_cps_suggestions(self, cps: CPS) -> List[str]:
        """Génère des suggestions d'amélioration pour le CPS"""
        suggestions = []
        
        if not cps.regulatory_references:
            suggestions.append("Ajouter les références réglementaires (décret, articles)")
        
        if not cps.special_conditions:
            suggestions.append("Compléter les conditions spéciales du marché")
        
        if cps.technical_specifications and len(cps.technical_specifications) < 500:
            suggestions.append("Les spécifications techniques semblent trop brèves, les détailler davantage")
        
        return suggestions
    
    def _assess_cps_risks(self, cps: CPS) -> Dict:
        """Évalue les risques liés au CPS"""
        risks = {
            'high_risks': [],
            'medium_risks': [],
            'low_risks': []
        }
        
        completeness = self._check_cps_completeness(cps)
        
        if completeness['percentage'] < 50:
            risks['high_risks'].append("CPS incomplet - risque de contentieux")
        elif completeness['percentage'] < 80:
            risks['medium_risks'].append("CPS partiellement complet")
        
        inconsistencies = self._detect_inconsistencies(cps)
        high_severity = [i for i in inconsistencies if i['severity'] == 'high']
        if high_severity:
            risks['high_risks'].extend([i['description'] for i in high_severity])
        
        return risks
    
    def check_missing_documents(self, market_id: int) -> Dict:
        """
        Vérifie les pièces manquantes pour un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire des pièces manquantes
        """
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            raise ValueError("Marché non trouvé")
        
        required_documents = {
            'CPS': False,
            'BPU': False,
            'DQE': False,
            'Acte d\'engagement': False,
            'Plans techniques': False
        }
        
        # Vérifier la préparation
        if market.preparation:
            if market.preparation.cps:
                required_documents['CPS'] = True
            if market.preparation.bpu:
                required_documents['BPU'] = True
            if market.preparation.dqe:
                required_documents['DQE'] = True
        
        # Vérifier les documents
        from app.models.document import Document
        documents = self.db.query(Document).filter(
            Document.market_id == market_id
        ).all()
        
        for doc in documents:
            if doc.category:
                category_name = doc.category.value
                if category_name in required_documents:
                    required_documents[category_name] = True
        
        missing = [doc for doc, present in required_documents.items() if not present]
        
        return {
            'required_documents': required_documents,
            'missing_documents': missing,
            'completion_percentage': (
                sum(required_documents.values()) / len(required_documents) * 100
            ) if required_documents else 0,
            'checked_at': datetime.utcnow().isoformat()
        }
    
    def generate_market_summary(self, market_id: int) -> str:
        """
        Génère un résumé automatique d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Résumé textuel du marché
        """
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            raise ValueError("Marché non trouvé")
        
        summary = f"""
Marché N° {market.market_number}
Objet: {market.object}
Maître d'ouvrage: {market.owner}
Montant estimatif: {market.estimated_amount:,.2f} MAD
Budget: {market.budget:,.2f} MAD
Statut: {market.status.value if market.status else 'Non défini'}
Type: {market.type.value if market.type else 'Non défini'}
Mode de passation: {market.procurement_method if market.procurement_method else 'Non défini'}
Date de création: {market.created_at.strftime('%d/%m/%Y') if market.created_at else 'Non défini'}
"""
        
        return summary.strip()
    
    def estimate_cost(self, market_data: dict) -> Dict:
        """
        Estime automatiquement le coût d'un marché basé sur des marchés similaires
        
        Args:
            market_data: Données du marché à estimer
            
        Returns:
            Dictionnaire avec l'estimation
        """
        # Récupérer les marchés similaires
        similar_markets = self.db.query(Market).filter(
            and_(
                Market.type == market_data.get('type'),
                Market.is_deleted == False,
                Market.final_amount.isnot(None)
            )
        ).limit(10).all()
        
        if not similar_markets:
            return {
                'estimated_amount': None,
                'confidence': 0,
                'method': 'no_similar_markets',
                'message': 'Aucun marché similaire trouvé pour l\'estimation'
            }
        
        amounts = [m.final_amount for m in similar_markets]
        avg_amount = sum(amounts) / len(amounts)
        
        # Ajuster selon la surface/quantité si disponible
        adjustment_factor = 1.0
        if market_data.get('surface'):
            avg_surface = sum(m.surface for m in similar_markets if hasattr(m, 'surface') and m.surface) / len(similar_markets)
            adjustment_factor = market_data['surface'] / avg_surface if avg_surface > 0 else 1.0
        
        estimated_amount = avg_amount * adjustment_factor
        
        return {
            'estimated_amount': estimated_amount,
            'confidence': min(90, len(similar_markets) * 10),
            'method': 'similar_markets_average',
            'reference_markets': len(similar_markets),
            'average_similar_amount': avg_amount,
            'adjustment_factor': adjustment_factor
        }
    
    def find_similar_markets(self, market_id: int, limit: int = 5) -> List[Dict]:
        """
        Recherche des marchés similaires
        
        Args:
            market_id: ID du marché de référence
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des marchés similaires
        """
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            raise ValueError("Marché non trouvé")
        
        # Critères de similarité
        similar = self.db.query(Market).filter(
            and_(
                Market.id != market_id,
                Market.is_deleted == False,
                Market.type == market.type,
                Market.owner == market.owner
            )
        ).limit(limit).all()
        
        return [
            {
                'id': m.id,
                'market_number': m.market_number,
                'object': m.object,
                'final_amount': m.final_amount,
                'status': m.status.value if m.status else None,
                'similarity_score': self._calculate_similarity(market, m)
            }
            for m in similar
        ]
    
    def _calculate_similarity(self, market1: Market, market2: Market) -> float:
        """Calcule un score de similarité entre deux marchés"""
        score = 0.0
        
        # Type identique
        if market1.type == market2.type:
            score += 30
        
        # Même propriétaire
        if market1.owner == market2.owner:
            score += 20
        
        # Montant similaire (±20%)
        if market1.final_amount and market2.final_amount:
            ratio = market1.final_amount / market2.final_amount
            if 0.8 <= ratio <= 1.2:
                score += 25
        
        # Même mode de passation
        if market1.procurement_method == market2.procurement_method:
            score += 15
        
        # Objet similaire (comparaison simple de mots)
        if market1.object and market2.object:
            words1 = set(market1.object.lower().split())
            words2 = set(market2.object.lower().split())
            intersection = words1.intersection(words2)
            if intersection:
                score += 10 * (len(intersection) / max(len(words1), len(words2)))
        
        return min(score, 100)
    
    def predict_delays(self, market_id: int) -> Dict:
        """
        Prédit les délais potentiels d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire avec les prédictions de délais
        """
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            raise ValueError("Marché non trouvé")
        
        # Analyser les marchés similaires terminés
        similar_completed = self.db.query(Market).filter(
            and_(
                Market.type == market.type,
                Market.status == 'termine',
                Market.is_deleted == False,
                Market.actual_duration.isnot(None),
                Market.planned_duration.isnot(None)
            )
        ).all()
        
        if not similar_completed:
            return {
                'predicted_delay_days': None,
                'confidence': 0,
                'message': 'Insuffisamment de données historiques'
            }
        
        # Calculer le délai moyen
        delays = [
            m.actual_duration - m.planned_duration
            for m in similar_completed
        ]
        
        avg_delay = sum(delays) / len(delays)
        
        # Facteurs de risque
        risk_factors = []
        if market.estimated_amount > 1000000:
            risk_factors.append("Montant élevé")
        if market.type == 'travaux':
            risk_factors.append("Type travaux")
        
        return {
            'predicted_delay_days': max(0, avg_delay),
            'confidence': min(85, len(similar_completed) * 15),
            'risk_factors': risk_factors,
            'reference_markets': len(similar_completed)
        }
    
    def detect_risks(self, market_id: int) -> Dict:
        """
        Détecte les risques potentiels d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire des risques détectés
        """
        market = self.db.query(Market).filter(
            Market.id == market_id
        ).first()
        
        if not market:
            raise ValueError("Marché non trouvé")
        
        risks = {
            'financial_risks': [],
            'operational_risks': [],
            'legal_risks': [],
            'overall_risk_level': 'low'
        }
        
        # Risques financiers
        if market.budget and market.estimated_amount:
            if market.estimated_amount > market.budget:
                risks['financial_risks'].append("Estimation supérieure au budget")
        
        if market.estimated_amount and market.estimated_amount > 5000000:
            risks['financial_risks'].append("Montant élevé - risque de dépassement")
        
        # Risques opérationnels
        if market.type == 'travaux':
            risks['operational_risks'].append("Travaux - risques techniques")
        
        if market.procurement_method in ['appel_offres_ouvert', 'appel_offres_restreint']:
            risks['operational_risks'].append("Procédure complexe - risque de retard")
        
        # Risques juridiques
        if market.preparation and not market.preparation.internal_visa:
            risks['legal_risks'].append("Visa interne non obtenu")
        
        # Évaluation globale
        total_risks = (
            len(risks['financial_risks']) +
            len(risks['operational_risks']) +
            len(risks['legal_risks'])
        )
        
        if total_risks >= 4:
            risks['overall_risk_level'] = 'high'
        elif total_risks >= 2:
            risks['overall_risk_level'] = 'medium'
        
        return risks
    
    def generate_ai_report(self, market_id: int) -> Dict:
        """
        Génère un rapport IA complet pour un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire du rapport IA complet
        """
        return {
            'cps_analysis': self.analyze_cps(market_id) if self._has_cps(market_id) else None,
            'missing_documents': self.check_missing_documents(market_id),
            'market_summary': self.generate_market_summary(market_id),
            'similar_markets': self.find_similar_markets(market_id),
            'delay_prediction': self.predict_delays(market_id),
            'risk_assessment': self.detect_risks(market_id),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _has_cps(self, market_id: int) -> bool:
        """Vérifie si le marché a un CPS"""
        from app.models.market_preparation import MarketPreparation
        preparation = self.db.query(MarketPreparation).filter(
            MarketPreparation.market_id == market_id
        ).first()
        
        return preparation and preparation.cps is not None


def get_ai_service(db: Session) -> AIService:
    """
    Factory pour créer une instance du service IA
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de AIService
    """
    return AIService(db)

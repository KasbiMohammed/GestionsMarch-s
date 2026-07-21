"""
Service de choix automatique de la procédure
Module 3: Choix automatique de la procédure
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.procurement_rules import (
    ProcurementRule, ProcurementDecision, ProcurementMethod, MarketNature
)
from app.models.market_preparation import MarketPreparation


class ProcurementService:
    """Service pour le choix automatique de la procédure de passation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def determine_procedure(self, estimated_amount: float, market_nature: str) -> ProcurementDecision:
        """
        Détermine automatiquement la procédure de passation selon le montant et la nature
        
        Args:
            estimated_amount: Montant estimatif
            market_nature: Nature du marché (travaux, fournitures, services)
            
        Returns:
            Instance de ProcurementDecision
        """
        # Récupérer les règles actives
        rules = self.db.query(ProcurementRule).filter(
            ProcurementRule.is_active == True
        ).all()
        
        # Trouver la règle applicable
        applicable_rule = self._find_applicable_rule(rules, estimated_amount, market_nature)
        
        if not applicable_rule:
            # Règle par défaut si aucune règle n'est trouvée
            default_method = self._get_default_method(estimated_amount, market_nature)
        else:
            default_method = applicable_rule.procurement_method
        
        # Créer la décision
        decision = ProcurementDecision(
            estimated_amount=estimated_amount,
            market_nature=market_nature,
            chosen_method=default_method,
            applied_rule_id=applicable_rule.id if applicable_rule else None,
            justification=self._generate_justification(applicable_rule, estimated_amount, market_nature)
        )
        
        return decision
    
    def _find_applicable_rule(self, rules: list, amount: float, nature: str) -> Optional[ProcurementRule]:
        """
        Trouve la règle applicable selon le montant et la nature
        
        Args:
            rules: Liste des règles
            amount: Montant estimatif
            nature: Nature du marché
            
        Returns:
            Règle applicable ou None
        """
        for rule in rules:
            # Vérifier si le montant est dans la plage
            if rule.min_amount is not None and amount < rule.min_amount:
                continue
            if rule.max_amount is not None and amount > rule.max_amount:
                continue
            
            # Vérifier si la nature correspond (si spécifiée)
            if rule.market_nature and rule.market_nature != nature:
                continue
            
            # Règle applicable trouvée
            return rule
        
        return None
    
    def _get_default_method(self, amount: float, nature: str) -> ProcurementMethod:
        """
        Retourne la méthode par défaut selon le décret marocain
        
        Args:
            amount: Montant estimatif
            nature: Nature du marché
            
        Returns:
            ProcurementMethod par défaut
        """
        # Seuils selon le décret (en MAD)
        # Ces valeurs sont à ajuster selon la réglementation en vigueur
        
        if amount <= 200000:
            return ProcurementMethod.BON_COMMANDE
        elif amount <= 500000:
            if nature == MarketNature.SERVICES:
                return ProcurementMethod.DIALOGUE_COMPETITIF
            else:
                return ProcurementMethod.AO_OUVERT_SIMPLIFIE
        elif amount <= 2000000:
            return ProcurementMethod.AO_OUVERT
        elif amount <= 5000000:
            return ProcurementMethod.AO_RESTREINT
        else:
            return ProcurementMethod.AO_OUVERT
    
    def _generate_justification(self, rule: Optional[ProcurementRule], amount: float, nature: str) -> str:
        """
        Génère la justification de la décision
        
        Args:
            rule: Règle appliquée
            amount: Montant estimatif
            nature: Nature du marché
            
        Returns:
            Justification textuelle
        """
        if rule:
            return f"Procédure choisie selon la règle {rule.regulatory_reference} - {rule.description}"
        else:
            return f"Procédure choisie selon le décret pour un marché de nature {nature} d'un montant de {amount:,.2f} MAD"
    
    def save_decision(self, preparation_id: int, decision: ProcurementDecision, user_id: int) -> ProcurementDecision:
        """
        Sauvegarde une décision de procédure
        
        Args:
            preparation_id: ID de la préparation
            decision: Décision à sauvegarder
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de ProcurementDecision sauvegardée
        """
        decision.preparation_id = preparation_id
        decision.created_by = user_id
        decision.created_at = datetime.utcnow()
        
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        
        return decision
    
    def validate_decision(self, decision_id: int, user_id: int) -> ProcurementDecision:
        """
        Valide une décision de procédure
        
        Args:
            decision_id: ID de la décision
            user_id: ID du validateur
            
        Returns:
            Instance de ProcurementDecision validée
        """
        decision = self.db.query(ProcurementDecision).filter(
            ProcurementDecision.id == decision_id
        ).first()
        
        if not decision:
            raise ValueError("Décision non trouvée")
        
        decision.validated = True
        decision.validated_by = user_id
        decision.validated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(decision)
        
        return decision
    
    def get_all_rules(self) -> list:
        """
        Récupère toutes les règles de procédure
        
        Returns:
            Liste des ProcurementRule
        """
        return self.db.query(ProcurementRule).all()
    
    def create_rule(self, rule_data: dict, user_id: int) -> ProcurementRule:
        """
        Crée une nouvelle règle de procédure
        
        Args:
            rule_data: Données de la règle
            user_id: ID de l'utilisateur créateur
            
        Returns:
            Instance de ProcurementRule créée
        """
        rule = ProcurementRule(
            min_amount=rule_data.get('min_amount'),
            max_amount=rule_data.get('max_amount'),
            market_nature=rule_data.get('market_nature'),
            procurement_method=rule_data['procurement_method'],
            regulatory_reference=rule_data.get('regulatory_reference'),
            article_reference=rule_data.get('article_reference'),
            description=rule_data.get('description'),
            conditions=rule_data.get('conditions'),
            is_active=rule_data.get('is_active', True),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule
    
    def update_rule(self, rule_id: int, rule_data: dict, user_id: int) -> ProcurementRule:
        """
        Met à jour une règle de procédure
        
        Args:
            rule_id: ID de la règle
            rule_data: Données de mise à jour
            user_id: ID de l'utilisateur
            
        Returns:
            Instance de ProcurementRule mise à jour
        """
        rule = self.db.query(ProcurementRule).filter(
            ProcurementRule.id == rule_id
        ).first()
        
        if not rule:
            raise ValueError("Règle non trouvée")
        
        for key, value in rule_data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_by = user_id
        rule.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(rule)
        
        return rule


def get_procurement_service(db: Session) -> ProcurementService:
    """
    Factory pour créer une instance du service de procédure
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de ProcurementService
    """
    return ProcurementService(db)

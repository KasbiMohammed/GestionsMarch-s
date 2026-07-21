"""
Service de gestion des marchés
Logique métier pour la gestion des marchés publics
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.market import Market, MarketStatus, MarketType
from app.models.stage import Stage, StageStatus
from app.models.history import History
from app.models.user import User


class MarketService:
    """Service pour la gestion des marchés publics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_market(self, market_data: dict, created_by: int) -> Market:
        """
        Crée un nouveau marché public
        
        Args:
            market_data: Données du marché
            created_by: ID de l'utilisateur créateur
            
        Returns:
            Marché créé
        """
        market = Market(**market_data)
        market.created_by = created_by
        market.created_at = datetime.now()
        
        self.db.add(market)
        self.db.commit()
        self.db.refresh(market)
        
        # Créer l'historique
        self._add_history(
            market_id=market.id,
            action="Création",
            description="Création du marché",
            user_id=created_by
        )
        
        return market
    
    def update_market(self, market_id: int, market_data: dict, updated_by: int) -> Optional[Market]:
        """
        Met à jour un marché
        
        Args:
            market_id: ID du marché
            market_data: Données à mettre à jour
            updated_by: ID de l'utilisateur modificateur
            
        Returns:
            Marché mis à jour ou None
        """
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            return None
        
        # Sauvegarder les anciennes valeurs pour l'historique
        old_values = {key: getattr(market, key) for key in market_data.keys()}
        
        # Mettre à jour les champs
        for key, value in market_data.items():
            if hasattr(market, key) and key != 'id':
                setattr(market, key, value)
        
        market.updated_at = datetime.now()
        market.updated_by = updated_by
        
        self.db.commit()
        self.db.refresh(market)
        
        # Créer l'historique
        self._add_history(
            market_id=market.id,
            action="Modification",
            description="Mise à jour du marché",
            user_id=updated_by,
            old_values=old_values,
            new_values=market_data
        )
        
        return market
    
    def delete_market(self, market_id: int, deleted_by: int) -> bool:
        """
        Supprime un marché (soft delete)
        
        Args:
            market_id: ID du marché
            deleted_by: ID de l'utilisateur supprimeur
            
        Returns:
            True si succès, False sinon
        """
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            return False
        
        market.is_deleted = True
        market.deleted_at = datetime.now()
        market.deleted_by = deleted_by
        
        self.db.commit()
        
        # Créer l'historique
        self._add_history(
            market_id=market.id,
            action="Suppression",
            description="Suppression du marché",
            user_id=deleted_by
        )
        
        return True
    
    def get_market(self, market_id: int) -> Optional[Market]:
        """
        Récupère un marché par son ID
        
        Args:
            market_id: ID du marché
            
        Returns:
            Marché ou None
        """
        return self.db.query(Market).filter(
            and_(Market.id == market_id, Market.is_deleted == False)
        ).first()
    
    def get_all_markets(self, skip: int = 0, limit: int = 100) -> List[Market]:
        """
        Récupère tous les marchés (pagination)
        
        Args:
            skip: Nombre d'éléments à sauter
            limit: Nombre maximum d'éléments
            
        Returns:
            Liste des marchés
        """
        return self.db.query(Market).filter(
            Market.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_markets_by_status(self, status: MarketStatus) -> List[Market]:
        """
        Récupère les marchés par statut
        
        Args:
            status: Statut du marché
            
        Returns:
            Liste des marchés
        """
        return self.db.query(Market).filter(
            and_(Market.status == status, Market.is_deleted == False)
        ).all()
    
    def get_markets_by_year(self, year: int) -> List[Market]:
        """
        Récupère les marchés par année
        
        Args:
            year: Année
            
        Returns:
            Liste des marchés
        """
        return self.db.query(Market).filter(
            and_(
                func.extract('year', Market.created_at) == year,
                Market.is_deleted == False
            )
        ).all()
    
    def search_markets(self, query: str, filters: dict = None) -> List[Market]:
        """
        Recherche de marchés avec filtres
        
        Args:
            query: Terme de recherche
            filters: Filtres additionnels
            
        Returns:
            Liste des marchés correspondants
        """
        query_filter = (
            (Market.market_number.ilike(f'%{query}%')) |
            (Market.object.ilike(f'%{query}%')) |
            (Market.owner.ilike(f'%{query}%')) |
            (Market.awardee.ilike(f'%{query}%'))
        )
        
        markets = self.db.query(Market).filter(
            and_(query_filter, Market.is_deleted == False)
        )
        
        if filters:
            if 'status' in filters:
                markets = markets.filter(Market.status == filters['status'])
            if 'type' in filters:
                markets = markets.filter(Market.type == filters['type'])
            if 'year' in filters:
                markets = markets.filter(
                    func.extract('year', Market.created_at) == filters['year']
                )
            if 'min_budget' in filters:
                markets = markets.filter(Market.budget >= filters['min_budget'])
            if 'max_budget' in filters:
                markets = markets.filter(Market.budget <= filters['max_budget'])
        
        return markets.all()
    
    def get_market_statistics(self) -> Dict:
        """
        Récupère les statistiques globales des marchés
        
        Returns:
            Dictionnaire de statistiques
        """
        total = self.db.query(func.count(Market.id)).filter(
            Market.is_deleted == False
        ).scalar()
        
        by_status = {}
        for status in MarketStatus:
            count = self.db.query(func.count(Market.id)).filter(
                and_(Market.status == status, Market.is_deleted == False)
            ).scalar()
            by_status[status.value] = count
        
        total_budget = self.db.query(func.sum(Market.budget)).filter(
            Market.is_deleted == False
        ).scalar() or 0
        
        avg_duration = self.db.query(
            func.avg(
                func.julianday(Market.actual_end_date) - func.julianday(Market.start_date)
            )
        ).filter(
            and_(
                Market.actual_end_date.isnot(None),
                Market.start_date.isnot(None),
                Market.is_deleted == False
            )
        ).scalar()
        
        return {
            'total': total,
            'by_status': by_status,
            'total_budget': total_budget,
            'average_duration_days': avg_duration
        }
    
    def get_market_progress(self, market_id: int) -> Dict:
        """
        Calcule la progression d'un marché
        
        Args:
            market_id: ID du marché
            
        Returns:
            Dictionnaire avec les informations de progression
        """
        market = self.get_market(market_id)
        if not market:
            return None
        
        stages = self.db.query(Stage).filter(Stage.market_id == market_id).all()
        
        total_stages = len(stages)
        completed_stages = len([s for s in stages if s.status == StageStatus.COMPLETED])
        in_progress_stages = len([s for s in stages if s.status == StageStatus.IN_PROGRESS])
        
        progress_percentage = (completed_stages / total_stages * 100) if total_stages > 0 else 0
        
        # Calculer le retard global
        late_stages = [s for s in stages if s.is_late]
        
        return {
            'total_stages': total_stages,
            'completed_stages': completed_stages,
            'in_progress_stages': in_progress_stages,
            'progress_percentage': round(progress_percentage, 2),
            'late_stages_count': len(late_stages),
            'on_track': len(late_stages) == 0
        }
    
    def _add_history(self, market_id: int, action: str, description: str, 
                    user_id: int, old_values: dict = None, new_values: dict = None):
        """
        Ajoute une entrée d'historique
        
        Args:
            market_id: ID du marché
            action: Action effectuée
            description: Description de l'action
            user_id: ID de l'utilisateur
            old_values: Anciennes valeurs
            new_values: Nouvelles valeurs
        """
        history = History(
            market_id=market_id,
            action=action,
            description=description,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            created_at=datetime.now()
        )
        
        self.db.add(history)
        self.db.commit()


def get_market_service(db: Session) -> MarketService:
    """
    Factory pour créer une instance du service de marchés
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de MarketService
    """
    return MarketService(db)

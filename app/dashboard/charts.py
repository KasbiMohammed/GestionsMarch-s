"""
Service de graphiques
Génération de graphiques avec Plotly
"""

from typing import Dict, List
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy.orm import Session

from app.models.market import Market, MarketStatus, MarketType
from app.models.stage import Stage, StageStatus
from app.dashboard.statistics import StatisticsService


class ChartsService:
    """Service pour la génération de graphiques"""
    
    def __init__(self, db: Session):
        self.db = db
        self.stats_service = StatisticsService(db)
    
    def get_markets_by_status_chart(self) -> Dict:
        """
        Génère un graphique des marchés par statut
        
        Returns:
            Dictionnaire Plotly JSON
        """
        stats = self.stats_service.get_global_statistics()
        by_status = stats['by_status']
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(by_status.keys()),
                y=list(by_status.values()),
                marker_color=[
                    '#28a745' if status == 'terminé' else
                    '#ffc107' if status == 'en_cours' else
                    '#dc3545' if status == 'en_retard' else
                    '#6c757d'
                    for status in by_status.keys()
                ]
            )
        ])
        
        fig.update_layout(
            title='Répartition des marchés par statut',
            xaxis_title='Statut',
            yaxis_title='Nombre de marchés',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_markets_by_type_chart(self) -> Dict:
        """
        Génère un graphique des marchés par type
        
        Returns:
            Dictionnaire Plotly JSON
        """
        stats = self.stats_service.get_global_statistics()
        by_type = stats['by_type']
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(by_type.keys()),
                values=list(by_type.values()),
                hole=0.4
            )
        ])
        
        fig.update_layout(
            title='Répartition des marchés par type',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_monthly_evolution_chart(self, year: int = None) -> Dict:
        """
        Génère un graphique de l'évolution mensuelle
        
        Args:
            year: Année à afficher
            
        Returns:
            Dictionnaire Plotly JSON
        """
        if year is None:
            year = 2024  # Default year
        
        monthly_stats = self.stats_service.get_monthly_statistics(year)
        
        months = list(range(1, 13))
        created = [monthly_stats[m]['created'] for m in months]
        completed = [monthly_stats[m]['completed'] for m in months]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=created,
            mode='lines+markers',
            name='Créés',
            line=dict(color='#28a745')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=completed,
            mode='lines+markers',
            name='Terminés',
            line=dict(color='#007bff')
        ))
        
        fig.update_layout(
            title=f'Évolution mensuelle des marchés ({year})',
            xaxis_title='Mois',
            yaxis_title='Nombre de marchés',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_budget_distribution_chart(self) -> Dict:
        """
        Génère un graphique de la distribution budgétaire
        
        Returns:
            Dictionnaire Plotly JSON
        """
        stats = self.stats_service.get_budget_statistics()
        budget_by_type = stats['budget_by_type']
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(budget_by_type.keys()),
                y=list(budget_by_type.values()),
                marker_color='#17a2b8'
            )
        ])
        
        fig.update_layout(
            title='Distribution budgétaire par type de marché',
            xaxis_title='Type de marché',
            yaxis_title='Budget (MAD)',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_stages_progress_chart(self, market_id: int = None) -> Dict:
        """
        Génère un graphique de la progression des étapes
        
        Args:
            market_id: ID du marché (optionnel, pour un marché spécifique)
            
        Returns:
            Dictionnaire Plotly JSON
        """
        if market_id:
            stages = self.db.query(Stage).filter(
                Stage.market_id == market_id
            ).order_by(Stage.order).all()
        else:
            # Progression globale de tous les marchés
            from app.dashboard.statistics import StatisticsService
            stage_stats = self.stats_service.get_stage_statistics()
            by_status = stage_stats['by_status']
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(by_status.keys()),
                    values=list(by_status.values()),
                    hole=0.4
                )
            ])
            
            fig.update_layout(
                title='Progression globale des étapes',
                template='plotly_white'
            )
            
            return fig.to_json()
        
        # Progression pour un marché spécifique
        stage_names = [s.name for s in stages]
        progress_values = [s.progress_percentage for s in stages]
        
        fig = go.Figure(data=[
            go.Bar(
                x=stage_names,
                y=progress_values,
                marker_color=[
                    '#28a745' if p == 100 else
                    '#ffc107' if p >= 50 else
                    '#dc3545'
                    for p in progress_values
                ]
            )
        ])
        
        fig.update_layout(
            title='Progression des étapes par marché',
            xaxis_title='Étape',
            yaxis_title='Progression (%)',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_delay_analysis_chart(self) -> Dict:
        """
        Génère un graphique de l'analyse des retards
        
        Returns:
            Dictionnaire Plotly JSON
        """
        delay_stats = self.stats_service.get_delay_statistics()
        by_range = delay_stats['by_delay_range']
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(by_range.keys()),
                y=list(by_range.values()),
                marker_color=[
                    '#ffc107' if '1-7' in r else
                    '#fd7e14' if '8-14' in r else
                    '#dc3545'
                    for r in by_range.keys()
                ]
            )
        ])
        
        fig.update_layout(
            title='Analyse des retards par durée',
            xaxis_title='Durée du retard',
            yaxis_title="Nombre d'étapes",
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_yearly_comparison_chart(self, years: int = 5) -> Dict:
        """
        Génère un graphique de comparaison annuelle
        
        Args:
            years: Nombre d'années à comparer
            
        Returns:
            Dictionnaire Plotly JSON
        """
        yearly_stats = self.stats_service.get_yearly_statistics(years)
        
        years_list = list(yearly_stats.keys())
        created = [yearly_stats[y]['created'] for y in years_list]
        budgets = [yearly_stats[y]['budget'] for y in years_list]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=years_list,
            y=created,
            name='Marchés créés',
            marker_color='#28a745'
        ))
        
        fig.add_trace(go.Scatter(
            x=years_list,
            y=budgets,
            name='Budget total',
            yaxis='y2',
            line=dict(color='#007bff')
        ))
        
        fig.update_layout(
            title='Comparaison annuelle',
            xaxis_title='Année',
            yaxis_title='Nombre de marchés',
            yaxis2=dict(
                title='Budget (MAD)',
                overlaying='y',
                side='right'
            ),
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def get_kpi_dashboard_chart(self) -> Dict:
        """
        Génère un graphique combiné pour le tableau de bord KPI
        
        Returns:
            Dictionnaire Plotly JSON
        """
        stats = self.stats_service.get_global_statistics()
        
        fig = go.Figure()
        
        # KPI 1: Taux de complétion
        total = stats['total_markets']
        completed = stats['by_status'].get('terminé', 0)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=completion_rate,
            title={'text': "Taux de complétion (%)"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#28a745"},
                'steps': [
                    {'range': [0, 50], 'color': "#ffebee"},
                    {'range': [50, 80], 'color': "#fff3e0"},
                    {'range': [80, 100], 'color': "#e8f5e9"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            title='Indicateurs de performance',
            template='plotly_white'
        )
        
        return fig.to_json()


def get_charts_service(db: Session) -> ChartsService:
    """
    Factory pour créer une instance du service de graphiques
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de ChartsService
    """
    return ChartsService(db)

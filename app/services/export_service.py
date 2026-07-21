"""
Service d'export
Gestion des exports Excel, PDF et Word
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO

from app.models.market import Market
from app.models.stage import Stage
from app.models.user import User


class ExportService:
    """Service pour la gestion des exports"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_markets_to_excel(self, filters: dict = None) -> BytesIO:
        """
        Exporte les marchés vers Excel
        
        Args:
            filters: Filtres pour la sélection des marchés
            
        Returns:
            Fichier Excel en mémoire
        """
        # Récupérer les marchés
        query = self.db.query(Market).filter(Market.is_deleted == False)
        
        if filters:
            if 'status' in filters:
                query = query.filter(Market.status == filters['status'])
            if 'year' in filters:
                from sqlalchemy import extract
                query = query.filter(extract('year', Market.created_at) == filters['year'])
        
        markets = query.all()
        
        # Préparer les données
        data = []
        for market in markets:
            data.append({
                'Numéro de marché': market.market_number,
                'Objet': market.object,
                'Maître d\'ouvrage': market.owner,
                'Type': market.type.value if market.type else '',
                'Mode de passation': market.procurement_mode,
                'Budget': market.budget,
                'Crédits': market.credits,
                'Service responsable': market.responsible_service,
                'Entreprise attributaire': market.awardee,
                'Montant définitif': market.final_amount,
                'Statut': market.status.value if market.status else '',
                'Date de début': market.start_date.strftime('%d/%m/%Y') if market.start_date else '',
                'Date de fin prévue': market.expected_end_date.strftime('%d/%m/%Y') if market.expected_end_date else '',
                'Date de fin réelle': market.actual_end_date.strftime('%d/%m/%Y') if market.actual_end_date else '',
                'Créé le': market.created_at.strftime('%d/%m/%Y %H:%M') if market.created_at else ''
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Marchés', index=False)
            
            # Ajuster les colonnes
            worksheet = writer.sheets['Marchés']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    
    def export_market_to_excel(self, market_id: int) -> BytesIO:
        """
        Exporte un marché détaillé vers Excel
        
        Args:
            market_id: ID du marché
            
        Returns:
            Fichier Excel en mémoire
        """
        market = self.db.query(Market).filter(Market.id == market_id).first()
        if not market:
            raise ValueError("Marché non trouvé")
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille Informations générales
            general_info = pd.DataFrame([{
                'Numéro de marché': market.market_number,
                'Objet': market.object,
                'Maître d\'ouvrage': market.owner,
                'Type': market.type.value if market.type else '',
                'Mode de passation': market.procurement_mode,
                'Budget': market.budget,
                'Crédits': market.credits,
                'Service responsable': market.responsible_service,
                'Responsables du suivi': market.followup_responsibles,
                'Entreprise attributaire': market.awardee,
                'Montant estimé': market.estimated_amount,
                'Montant définitif': market.final_amount,
                'Délai': market.duration,
                'Statut': market.status.value if market.status else '',
                'Date de début': market.start_date.strftime('%d/%m/%Y') if market.start_date else '',
                'Date de fin prévue': market.expected_end_date.strftime('%d/%m/%Y') if market.expected_end_date else '',
                'Date de fin réelle': market.actual_end_date.strftime('%d/%m/%Y') if market.actual_end_date else ''
            }])
            general_info.to_excel(writer, sheet_name='Informations', index=False)
            
            # Feuille Étapes
            stages = self.db.query(Stage).filter(Stage.market_id == market_id).all()
            stages_data = []
            for stage in stages:
                stages_data.append({
                    'Ordre': stage.order,
                    'Nom': stage.name,
                    'Statut': stage.status.value if stage.status else '',
                    'Progression (%)': stage.progress_percentage,
                    'Date prévue': stage.planned_date.strftime('%d/%m/%Y') if stage.planned_date else '',
                    'Date réelle': stage.actual_date.strftime('%d/%m/%Y') if stage.actual_date else '',
                    'Responsable': stage.responsible,
                    'Observations': stage.observations,
                    'En retard': 'Oui' if stage.is_late else 'Non'
                })
            
            if stages_data:
                stages_df = pd.DataFrame(stages_data)
                stages_df.to_excel(writer, sheet_name='Étapes', index=False)
        
        output.seek(0)
        return output
    
    def export_stages_to_excel(self, market_id: int) -> BytesIO:
        """
        Exporte les étapes d'un marché vers Excel
        
        Args:
            market_id: ID du marché
            
        Returns:
            Fichier Excel en mémoire
        """
        stages = self.db.query(Stage).filter(Stage.market_id == market_id).all()
        
        data = []
        for stage in stages:
            data.append({
                'Ordre': stage.order,
                'Nom': stage.name,
                'Statut': stage.status.value if stage.status else '',
                'Progression (%)': stage.progress_percentage,
                'Date prévue': stage.planned_date.strftime('%d/%m/%Y') if stage.planned_date else '',
                'Date réelle': stage.actual_date.strftime('%d/%m/%Y') if stage.actual_date else '',
                'Responsable': stage.responsible,
                'Observations': stage.observations,
                'En retard': 'Oui' if stage.is_late else 'Non',
                'Jours de retard': stage.delay_days if stage.delay_days else 0
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Étapes', index=False)
        
        output.seek(0)
        return output
    
    def export_dashboard_to_excel(self) -> BytesIO:
        """
        Exporte les données du tableau de bord vers Excel
        
        Returns:
            Fichier Excel en mémoire
        """
        # Statistiques globales
        from sqlalchemy import func
        
        total_markets = self.db.query(func.count(Market.id)).filter(
            Market.is_deleted == False
        ).scalar()
        
        # Par statut
        status_stats = {}
        from app.models.market import MarketStatus
        for status in MarketStatus:
            count = self.db.query(func.count(Market.id)).filter(
                (Market.status == status) & (Market.is_deleted == False)
            ).scalar()
            status_stats[status.value] = count or 0
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Statistiques générales
            general_stats = pd.DataFrame([{
                'Total des marchés': total_markets,
                'Date de l\'export': datetime.now().strftime('%d/%m/%Y %H:%M')
            }])
            general_stats.to_excel(writer, sheet_name='Général', index=False)
            
            # Par statut
            status_df = pd.DataFrame(list(status_stats.items()), 
                                    columns=['Statut', 'Nombre'])
            status_df.to_excel(writer, sheet_name='Par statut', index=False)
        
        output.seek(0)
        return output
    
    def get_export_filename(self, export_type: str, market_id: int = None) -> str:
        """
        Génère un nom de fichier pour l'export
        
        Args:
            export_type: Type d'export
            market_id: ID du marché (optionnel)
            
        Returns:
            Nom du fichier
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_type == 'markets':
            return f"marches_{timestamp}.xlsx"
        elif export_type == 'market':
            return f"marche_{market_id}_{timestamp}.xlsx"
        elif export_type == 'stages':
            return f"etapes_marche_{market_id}_{timestamp}.xlsx"
        elif export_type == 'dashboard':
            return f"tableau_bord_{timestamp}.xlsx"
        else:
            return f"export_{timestamp}.xlsx"


def get_export_service(db: Session) -> ExportService:
    """
    Factory pour créer une instance du service d'export
    
    Args:
        db: Session de base de données
        
    Returns:
        Instance de ExportService
    """
    return ExportService(db)

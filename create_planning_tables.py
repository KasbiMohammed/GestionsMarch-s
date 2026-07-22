"""
Script pour créer les tables de planification des marchés
Exécutez ce script pour ajouter les tables market_plannings et planning_documents
"""

from app.database import engine, Base
from app.models.market_planning import MarketPlanning, PlanningDocument

def create_planning_tables():
    """Crée les tables de planification si elles n'existent pas"""
    print("Création des tables de planification...")
    
    # Créer uniquement les tables de planification
    MarketPlanning.__table__.create(engine, checkfirst=True)
    PlanningDocument.__table__.create(engine, checkfirst=True)
    
    print("Tables créées avec succès !")
    print("- market_plannings")
    print("- planning_documents")

if __name__ == "__main__":
    create_planning_tables()

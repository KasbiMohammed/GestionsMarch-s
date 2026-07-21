"""
API d'analyse des marchés
Endpoints pour l'analyse automatique des marchés PMMP
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.market import Market
from app.auth.dependencies import get_current_active_user
from app.scraping.pmmp_scraper import scrape_market_data
from app.scraping.market_analyzer import analyze_offers

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Requête d'analyse de marché"""
    url: str
    method: str = "median"  # median, mean, trimmed_mean, iqr


class AnalysisResponse(BaseModel):
    """Réponse d'analyse de marché"""
    market_data: Dict
    analysis_results: Dict
    recommendations: list


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_market_from_url(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyse un marché depuis son URL PMMP
    
    Args:
        request: Requête d'analyse avec URL et méthode
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Résultats de l'analyse complets
        
    Raises:
        HTTPException: Si l'URL est invalide ou le scraping échoue
    """
    # Scraper les données du marché
    market_data = scrape_market_data(request.url)
    
    if not market_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to scrape market data from the provided URL"
        )
    
    # Analyser les offres
    companies = market_data.get('companies', [])
    analysis_results = analyze_offers(companies)
    
    # Calculer le prix de référence avec la méthode demandée
    reference_price = analysis_results['reference_prices'].get(request.method)
    
    # Générer des recommandations
    recommendations = generate_recommendations(analysis_results, reference_price)
    
    return AnalysisResponse(
        market_data=market_data,
        analysis_results=analysis_results,
        recommendations=recommendations
    )


@router.post("/import")
async def import_market_from_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Importe un marché analysé dans la base de données
    
    Args:
        request: Requête d'analyse avec URL
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Marché créé
        
    Raises:
        HTTPException: Si l'import échoue
    """
    # Scraper les données
    market_data = scrape_market_data(request.url)
    
    if not market_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to scrape market data"
        )
    
    # Créer le marché
    from app.models.market import Market, Company
    from app.models.market import MarketType, ProcurementMethod
    
    # Mapper les types
    type_mapping = {
        'travaux': MarketType.TRAVAUX,
        'fournitures': MarketType.FOURNITURES,
        'services': MarketType.SERVICES,
        'études': MarketType.ETUDES
    }
    
    method_mapping = {
        'appel d\'offres ouvert': ProcurementMethod.APPEL_OFFRES_OUVERT,
        'appel d\'offres restreint': ProcurementMethod.APPEL_OFFRES_RESTREINT,
        'marché négocié': ProcurementMethod.MARCHE_NEGOCIE,
        'bon de commande': ProcurementMethod.BON_COMMANDE,
        'marché simplifié': ProcurementMethod.MARCHE_SIMPLIFIE
    }
    
    # Créer le marché
    db_market = Market(
        market_number=market_data.get('market_number', f"PMMP-{market_data.get('id', 'UNKNOWN')}"),
        object=market_data.get('object', 'Importé depuis PMMP'),
        master_of_work=market_data.get('master_of_work', 'Non spécifié'),
        market_type=type_mapping.get(market_data.get('market_type', '').lower(), MarketType.SERVICES),
        procurement_method=method_mapping.get(market_data.get('procurement_method', '').lower(), ProcurementMethod.APPEL_OFFRES_OUVERT),
        estimated_amount=market_data.get('estimated_amount', 0),
        created_by=current_user.id,
        modified_by=current_user.id,
        participating_companies_count=len(market_data.get('companies', []))
    )
    
    db.add(db_market)
    db.flush()
    
    # Ajouter les entreprises
    for company_data in market_data.get('companies', []):
        db_company = Company(
            name=company_data.get('name', 'Non spécifié'),
            offer_amount=company_data.get('offer_amount'),
            market_id=db_market.id
        )
        db.add(db_company)
    
    db.commit()
    db.refresh(db_market)
    
    return db_market


def generate_recommendations(analysis_results: Dict, reference_price: float) -> list:
    """
    Génère des recommandations basées sur l'analyse
    
    Args:
        analysis_results: Résultats de l'analyse
        reference_price: Prix de référence
        
    Returns:
        Liste de recommandations
    """
    recommendations = []
    
    # Vérifier les offres anormalement basses
    abnormal_low = analysis_results['abnormal_offers']['iqr_method']['low']
    if abnormal_low:
        recommendations.append({
            'type': 'warning',
            'message': f"{len(abnormal_low)} offre(s) anormalement basse(s) détectée(s). Vérification recommandée.",
            'details': abnormal_low
        })
    
    # Vérifier les offres anormalement élevées
    abnormal_high = analysis_results['abnormal_offers']['iqr_method']['high']
    if abnormal_high:
        recommendations.append({
            'type': 'warning',
            'message': f"{len(abnormal_high)} offre(s) anormalement haute(s) détectée(s). Vérification recommandée.",
            'details': abnormal_high
        })
    
    # Recommandation sur le prix de référence
    if reference_price:
        recommendations.append({
            'type': 'info',
            'message': f"Le prix de référence calculé est de {reference_price:,.2f} MAD.",
            'details': f"Méthode utilisée : médiane des offres"
        })
    
    # Vérifier le nombre d'offres
    total_offers = analysis_results['total_offers']
    if total_offers < 3:
        recommendations.append({
            'type': 'warning',
            'message': f"Seulement {total_offers} offre(s) reçue(s). Concurrence limitée.",
            'details': None
        })
    elif total_offers >= 10:
        recommendations.append({
            'type': 'success',
            'message': f"Fort concurrence avec {total_offers} offres reçues.",
            'details': None
        })
    
    # Analyse de la dispersion
    stats = analysis_results['statistics']
    if stats.get('std_dev') and stats.get('mean'):
        cv = (stats['std_dev'] / stats['mean']) * 100  # Coefficient de variation
        if cv > 30:
            recommendations.append({
                'type': 'warning',
                'message': f"Dispersion élevée des offres (CV: {cv:.1f}%). Analyse détaillée recommandée.",
                'details': None
            })
        else:
            recommendations.append({
                'type': 'success',
                'message': f"Dispersion normale des offres (CV: {cv:.1f}%).",
                'details': None
            })
    
    return recommendations

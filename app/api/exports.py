"""
API d'export de données
Endpoints pour l'export en Excel, PDF et Word
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.market import Market
from app.models.market_planning import MarketPlanning
from app.auth.dependencies import get_current_active_user
from app.auth.permissions import can_export_data
from app.exports.excel_export import export_markets_to_excel, export_plannings_to_excel
from app.exports.pdf_export import export_market_to_pdf, export_planning_to_pdf

router = APIRouter()


@router.get("/markets/excel")
async def export_markets_excel(
    market_ids: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte les marchés en Excel
    
    Args:
        market_ids: IDs des marchés à exporter (séparés par des virgules)
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier Excel
        
    Raises:
        HTTPException: Si l'utilisateur n'a pas les permissions
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    # Construire la requête
    query = db.query(Market)
    
    if market_ids:
        ids = [int(id.strip()) for id in market_ids.split(",")]
        query = query.filter(Market.id.in_(ids))
    
    markets = query.all()
    
    # Générer le fichier Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"marches_export_{timestamp}.xlsx"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    export_markets_to_excel(markets, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/markets/{market_id}/pdf")
async def export_market_pdf(
    market_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte un marché en PDF
    
    Args:
        market_id: ID du marché
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier PDF
        
    Raises:
        HTTPException: Si le marché n'existe pas ou permissions insuffisantes
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    market = db.query(Market).filter(Market.id == market_id).first()
    
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Générer le fichier PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"marche_{market.market_number}_{timestamp}.pdf"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    export_market_to_pdf(market, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/report/monthly")
async def export_monthly_report(
    month: int,
    year: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte le rapport mensuel en PDF
    
    Args:
        month: Mois (1-12)
        year: Année
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier PDF du rapport mensuel
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    from app.exports.pdf_export import generate_monthly_report
    
    # Récupérer les marchés du mois
    from datetime import date
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    markets = db.query(Market).filter(
        Market.created_at >= start_date,
        Market.created_at < end_date
    ).all()
    
    # Générer le rapport
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_mensuel_{month}_{year}_{timestamp}.pdf"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    generate_monthly_report(markets, month, year, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/market-planning/excel")
async def export_planning_excel(
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte les planifications en Excel
    
    Args:
        fiscal_year: Année fiscale optionnelle
        status: Statut optionnel
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier Excel
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    # Construire la requête
    query = db.query(MarketPlanning)
    
    if fiscal_year:
        query = query.filter(MarketPlanning.fiscal_year == fiscal_year)
    if status:
        query = query.filter(MarketPlanning.status == status)
    
    plannings = query.all()
    
    # Générer le fichier Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"planifications_export_{timestamp}.xlsx"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    export_plannings_to_excel(plannings, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/market-planning/pdf")
async def export_plannings_pdf(
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte les planifications en PDF
    
    Args:
        fiscal_year: Année fiscale optionnelle
        status: Statut optionnel
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier PDF
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    # Construire la requête
    query = db.query(MarketPlanning)
    
    if fiscal_year:
        query = query.filter(MarketPlanning.fiscal_year == fiscal_year)
    if status:
        query = query.filter(MarketPlanning.status == status)
    
    plannings = query.all()
    
    # Générer le fichier PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"planifications_export_{timestamp}.pdf"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    from app.exports.pdf_export import export_plannings_to_pdf
    export_plannings_to_pdf(plannings, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/market-planning/{planning_id}/pdf")
async def export_planning_pdf(
    planning_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte une planification en PDF
    
    Args:
        planning_id: ID de la planification
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier PDF
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    planning = db.query(MarketPlanning).filter(MarketPlanning.id == planning_id).first()
    
    if not planning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planning not found"
        )
    
    # Générer le fichier PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"planification_{planning.planning_number}_{timestamp}.pdf"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    export_planning_to_pdf(planning, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/dashboard/excel")
async def export_dashboard_excel(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte les données du tableau de bord en Excel
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier Excel avec les statistiques du dashboard
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    from app.exports.excel_export import export_dashboard_to_excel
    
    # Récupérer les données du dashboard
    from app.api.dashboard import get_dashboard_statistics
    stats = await get_dashboard_statistics(current_user, db)
    
    # Générer le fichier Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_export_{timestamp}.xlsx"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    export_dashboard_to_excel(stats, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/dashboard/pdf")
async def export_dashboard_pdf(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exporte les données du tableau de bord en PDF
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Fichier PDF avec les statistiques du dashboard
    """
    if not can_export_data(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export data"
        )
    
    from app.exports.pdf_export import export_dashboard_to_pdf
    
    # Récupérer les données du dashboard
    from app.api.dashboard import get_dashboard_statistics
    stats = await get_dashboard_statistics(current_user, db)
    
    # Générer le fichier PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_export_{timestamp}.pdf"
    filepath = os.path.join("exports", filename)
    
    os.makedirs("exports", exist_ok=True)
    
    export_dashboard_to_pdf(stats, filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )

"""
API du tableau de bord
Endpoints pour les statistiques, KPIs et graphiques
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.market import Market, MarketStatus
from app.models.stage import Stage, StageStatus
from app.models.market_planning import MarketPlanning
from app.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/statistics")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les statistiques globales du tableau de bord
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Statistiques du tableau de bord
    """
    from app.dashboard.statistics import get_statistics_service
    
    stats_service = get_statistics_service(db)
    global_stats = stats_service.get_global_statistics()
    
    # Statistiques des marchés
    total_markets = db.query(Market).count()
    markets_en_cours = db.query(Market).filter(Market.status == MarketStatus.EN_COURS).count()
    markets_termine = db.query(Market).filter(Market.status == MarketStatus.TERMINE).count()
    markets_en_retard = db.query(Market).filter(Market.status == MarketStatus.EN_RETARD).count()
    markets_en_attente = db.query(Market).filter(Market.status == MarketStatus.EN_ATTENTE).count()
    markets_annule = db.query(Market).filter(Market.status == MarketStatus.ANNULE).count() if hasattr(MarketStatus, 'ANNULE') else 0
    markets_suspendu = db.query(Market).filter(Market.status == MarketStatus.SUSPENDU).count() if hasattr(MarketStatus, 'SUSPENDU') else 0
    
    # Montants
    total_estimated = db.query(func.sum(Market.estimated_amount)).scalar() or 0
    total_definitive = db.query(func.sum(Market.definitive_amount)).scalar() or 0
    total_attributed = db.query(func.sum(Market.definitive_amount)).filter(Market.status == MarketStatus.TERMINE).scalar() or 0
    total_paid = db.query(func.sum(Market.paid_amount)).scalar() or 0 if hasattr(Market, 'paid_amount') else 0
    remaining_budget = total_definitive - total_paid if total_definitive else 0
    
    # Écart estimation vs attribution
    variance = total_definitive - total_estimated
    
    # Progression moyenne
    avg_progress = db.query(func.avg(Market.progress_percentage)).scalar() or 0
    
    # Délais moyens
    avg_procurement_delay = db.query(func.avg(Market.procurement_delay_days)).scalar() or 0 if hasattr(Market, 'procurement_delay_days') else 0
    avg_execution_delay = db.query(func.avg(Market.execution_delay_days)).scalar() or 0 if hasattr(Market, 'execution_delay_days') else 0
    
    # Statistiques des étapes
    total_stages = db.query(Stage).count()
    stages_completed = db.query(Stage).filter(Stage.status == StageStatus.COMPLETED).count()
    stages_in_progress = db.query(Stage).filter(Stage.status == StageStatus.IN_PROGRESS).count()
    stages_late = db.query(Stage).filter(Stage.is_late == True).count()
    
    # Statistiques de planification
    total_plannings = db.query(MarketPlanning).count()
    plannings_budget = db.query(func.sum(MarketPlanning.estimated_budget)).scalar() or 0
    plannings_validated = db.query(MarketPlanning).filter(MarketPlanning.status == 'validee').count()
    plannings_programmed = db.query(MarketPlanning).filter(MarketPlanning.status == 'programmee').count()
    
    # Marchés proches des échéances (7 jours)
    from datetime import datetime, timedelta
    upcoming_deadline = datetime.now() + timedelta(days=7)
    markets_near_deadline = db.query(Stage).filter(
        Stage.planned_date <= upcoming_deadline,
        Stage.planned_date >= datetime.now(),
        Stage.status != StageStatus.COMPLETED
    ).count()
    
    return {
        "markets": {
            "total": total_markets,
            "en_cours": markets_en_cours,
            "termine": markets_termine,
            "en_retard": markets_en_retard,
            "en_attente": markets_en_attente,
            "annule": markets_annule,
            "suspendu": markets_suspendu,
            "actifs": markets_en_cours + markets_en_attente
        },
        "amounts": {
            "total_estimated": float(total_estimated),
            "total_definitive": float(total_definitive),
            "total_attributed": float(total_attributed),
            "total_paid": float(total_paid),
            "remaining": float(remaining_budget),
            "variance": float(variance)
        },
        "progress": {
            "average": float(avg_progress)
        },
        "delays": {
            "avg_procurement": float(avg_procurement_delay),
            "avg_execution": float(avg_execution_delay)
        },
        "deadlines": {
            "near_deadline": markets_near_deadline
        },
        "stages": {
            "total": total_stages,
            "completed": stages_completed,
            "in_progress": stages_in_progress,
            "late": stages_late
        },
        "planning": {
            "total": total_plannings,
            "budget": float(plannings_budget),
            "validated": plannings_validated,
            "programmed": plannings_programmed
        }
    }


@router.get("/markets-by-status")
async def get_markets_by_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Récupère le nombre de marchés par statut
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Dictionnaire des comptes par statut
    """
    status_counts = {}
    
    for status in MarketStatus:
        count = db.query(Market).filter(Market.status == status).count()
        status_counts[status.value] = count
    
    return status_counts


@router.get("/markets-by-type")
async def get_markets_by_type(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Récupère le nombre de marchés par type
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Dictionnaire des comptes par type
    """
    from app.models.market import MarketType
    
    type_counts = {}
    
    for market_type in MarketType:
        count = db.query(Market).filter(Market.market_type == market_type).count()
        type_counts[market_type.value] = count
    
    return type_counts


@router.get("/planning-statistics")
async def get_planning_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les statistiques de planification pour le tableau de bord
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Statistiques de planification
    """
    from app.models.market_planning import ProjectType, ProcedureType, MarketPlanningStatus
    
    total_plannings = db.query(MarketPlanning).count()
    total_budget = db.query(func.sum(MarketPlanning.estimated_budget)).scalar() or 0
    
    # Répartition par type de projet
    by_project_type = {}
    for pt in ProjectType:
        count = db.query(MarketPlanning).filter(MarketPlanning.project_type == pt).count()
        by_project_type[pt.value] = count
    
    # Répartition par type de procédure
    by_procedure_type = {}
    for proc in ProcedureType:
        count = db.query(MarketPlanning).filter(MarketPlanning.procedure_type == proc).count()
        by_procedure_type[proc.value] = count
    
    # Répartition par statut
    by_status = {}
    for st in MarketPlanningStatus:
        count = db.query(MarketPlanning).filter(MarketPlanning.status == st).count()
        by_status[st.value] = count
    
    return {
        "total_count": total_plannings,
        "total_budget": float(total_budget),
        "by_project_type": by_project_type,
        "by_procedure_type": by_procedure_type,
        "by_status": by_status
    }


@router.get("/recent-markets")
async def get_recent_markets(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les marchés les plus récents
    
    Args:
        limit: Nombre maximum de marchés à retourner
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des marchés récents
    """
    from app.schemas.market import MarketResponse
    
    markets = db.query(Market).order_by(Market.created_at.desc()).limit(limit).all()
    return [MarketResponse.model_validate(market) for market in markets]


@router.get("/late-stages")
async def get_late_stages(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les étapes en retard
    
    Args:
        limit: Nombre maximum d'étapes à retourner
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des étapes en retard
    """
    from app.schemas.stage import StageResponse
    
    stages = db.query(Stage).filter(
        Stage.is_late == True
    ).order_by(Stage.delay_days.desc()).limit(limit).all()
    
    return [StageResponse.model_validate(stage) for stage in stages]


@router.get("/markets-by-procedure")
async def get_markets_by_procedure(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Récupère le nombre de marchés par procédure
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Dictionnaire des comptes par procédure
    """
    from app.models.market import ProcurementMethod
    
    procedure_counts = {}
    
    for procedure in ProcurementMethod:
        count = db.query(Market).filter(Market.procurement_method == procedure).count()
        procedure_counts[procedure.value] = count
    
    return procedure_counts


@router.get("/markets-by-service")
async def get_markets_by_service(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Récupère le nombre de marchés par service maître d'ouvrage
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Dictionnaire des comptes par service
    """
    from app.models.market import Market
    from sqlalchemy import func
    
    service_counts = db.query(
        Market.master_of_work,
        func.count(Market.id).label('count')
    ).group_by(
        Market.master_of_work
    ).all()
    
    return {service.master_of_work: service.count for service in service_counts}


@router.get("/risk-metrics")
async def get_risk_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les métriques de gestion des risques
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Métriques de risque
    """
    from datetime import datetime, timedelta
    
    # Top 10 marchés à risque (en retard avec délai élevé)
    risk_markets = db.query(Market).filter(
        Market.status == MarketStatus.EN_RETARD
    ).order_by(
        Market.progress_percentage.asc()
    ).limit(10).all()
    
    # Top 10 marchés en retard
    late_markets = db.query(Market).filter(
        Market.status == MarketStatus.EN_RETARD
    ).order_by(
        Market.created_at.desc()
    ).limit(10).all()
    
    # Marchés proches des échéances (30 jours)
    upcoming_deadline = datetime.now() + timedelta(days=30)
    near_deadline_markets = db.query(Stage).filter(
        Stage.planned_date <= upcoming_deadline,
        Stage.planned_date >= datetime.now(),
        Stage.status != StageStatus.COMPLETED
    ).count()
    
    # Marchés bloqués
    blocked_markets = db.query(Market).filter(
        Market.status == MarketStatus.SUSPENDU
    ).count() if hasattr(MarketStatus, 'SUSPENDU') else 0
    
    return {
        "at_risk_count": len(risk_markets),
        "late_count": len(late_markets),
        "near_deadline_count": near_deadline_markets,
        "blocked_count": blocked_markets,
        "at_risk_markets": [{"id": m.id, "number": m.market_number, "object": m.object, "progress": m.progress_percentage} for m in risk_markets],
        "late_markets": [{"id": m.id, "number": m.market_number, "object": m.object} for m in late_markets]
    }


@router.get("/commission-statistics")
async def get_commission_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les statistiques des commissions
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Statistiques des commissions
    """
    from app.models.commission import Commission, CommissionSession
    
    total_commissions = db.query(Commission).count()
    
    # Sessions planifiées, en cours, clôturées
    sessions_planned = db.query(CommissionSession).filter(
        CommissionSession.status == 'planifiee'
    ).count()
    sessions_in_progress = db.query(CommissionSession).filter(
        CommissionSession.status == 'en_cours'
    ).count()
    sessions_closed = db.query(CommissionSession).filter(
        CommissionSession.status == 'cloturee'
    ).count()
    
    # Sessions reportées
    sessions_postponed = db.query(CommissionSession).filter(
        CommissionSession.status == 'reportee'
    ).count()
    
    return {
        "total_commissions": total_commissions,
        "sessions_planned": sessions_planned,
        "sessions_in_progress": sessions_in_progress,
        "sessions_closed": sessions_closed,
        "sessions_postponed": sessions_postponed
    }


@router.get("/document-alert-metrics")
async def get_document_alert_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les métriques de documents et alertes
    
    Args:
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Métriques de documents et alertes
    """
    from app.models.market import Document
    
    # Documents obligatoires manquants
    missing_documents = db.query(Document).filter(
        Document.is_required == True,
        Document.file_path == None
    ).count() if hasattr(Document, 'is_required') else 0
    
    # Alertes critiques
    from app.models.alert import Alert
    critical_alerts = db.query(Alert).filter(
        Alert.level == 'critical',
        Alert.is_resolved == False
    ).count() if hasattr(Alert, 'level') else 0
    
    return {
        "missing_documents": missing_documents,
        "critical_alerts": critical_alerts
    }


@router.get("/monthly-statistics")
async def get_monthly_statistics(
    months: int = 12,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les statistiques mensuelles sur les derniers mois
    
    Args:
        months: Nombre de mois à analyser
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Statistiques mensuelles
    """
    monthly_data = []
    
    for i in range(months):
        date = datetime.now() - timedelta(days=30 * i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        markets_created = db.query(Market).filter(
            and_(
                Market.created_at >= month_start,
                Market.created_at <= month_end
            )
        ).count()
        
        markets_completed = db.query(Market).filter(
            and_(
                Market.definitive_acceptance_date >= month_start,
                Market.definitive_acceptance_date <= month_end
            )
        ).count()
        
        monthly_data.append({
            "month": month_start.strftime("%Y-%m"),
            "markets_created": markets_created,
            "markets_completed": markets_completed
        })
    
    return {"monthly_data": monthly_data[::-1]}


@router.get("/top-companies")
async def get_top_companies(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les entreprises les plus attributaires
    
    Args:
        limit: Nombre maximum d'entreprises à retourner
        current_user: Utilisateur actuel
        db: Session de base de données
        
    Returns:
        Liste des entreprises les plus attributaires
    """
    from app.models.market import Company
    from sqlalchemy import desc
    
    companies = db.query(
        Company.name,
        func.count(Company.id).label('count'),
        func.sum(Company.offer_amount).label('total_amount')
    ).filter(
        Company.is_attributed == True
    ).group_by(
        Company.name
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [
        {
            "name": company.name,
            "markets_count": company.count,
            "total_amount": float(company.total_amount) if company.total_amount else 0
        }
        for company in companies
    ]

"""
Services métier
Logique métier réutilisable
"""

# Services existants
from app.services.notification_service import NotificationService, get_notification_service
from app.services.auth_service import AuthService, get_auth_service
from app.services.market_service import MarketService, get_market_service
from app.services.stage_service import StageService, get_stage_service
from app.services.export_service import ExportService, get_export_service

# Nouveaux services pour les 15 modules
from app.services.annual_planning_service import AnnualPlanningService, get_annual_planning_service
from app.services.preparation_service import MarketPreparationService, get_market_preparation_service
from app.services.procurement_service import ProcurementService, get_procurement_service
from app.services.commission_service import CommissionService, get_commission_service
from app.services.offer_service import OfferService, get_offer_service
from app.services.analysis_service import AnalysisService, get_analysis_service
from app.services.attribution_service import AttributionService, get_attribution_service
from app.services.execution_service import ExecutionService, get_execution_service
from app.services.document_service import DocumentService, get_document_service
from app.services.alert_service import AlertService, get_alert_service
from app.services.workflow_service import WorkflowService, get_workflow_service
from app.services.dashboard_service import DashboardService, get_dashboard_service
from app.services.user_permission_service import UserPermissionService, get_user_permission_service
from app.services.ai_service import AIService, get_ai_service
from app.services.pmmp_service import PMMPService, get_pmmp_service, PMMPIntegrationService, get_pmmp_integration_service

__all__ = [
    # Services existants
    "NotificationService",
    "get_notification_service",
    "AuthService",
    "get_auth_service",
    "MarketService",
    "get_market_service",
    "StageService",
    "get_stage_service",
    "ExportService",
    "get_export_service",
    
    # Module 1: Planification annuelle
    "AnnualPlanningService",
    "get_annual_planning_service",
    
    # Module 2: Préparation du marché
    "MarketPreparationService",
    "get_market_preparation_service",
    
    # Module 3: Choix automatique de la procédure
    "ProcurementService",
    "get_procurement_service",
    
    # Module 4: Gestion des commissions
    "CommissionService",
    "get_commission_service",
    
    # Module 5 & 6: Publication PMMP et Réception des offres
    "OfferService",
    "get_offer_service",
    
    # Module 7: Analyse automatique
    "AnalysisService",
    "get_analysis_service",
    
    # Module 8: Attribution
    "AttributionService",
    "get_attribution_service",
    
    # Module 9: Exécution du marché
    "ExecutionService",
    "get_execution_service",
    
    # Module 10: Gestion documentaire
    "DocumentService",
    "get_document_service",
    
    # Module 11: Alertes intelligentes
    "AlertService",
    "get_alert_service",
    
    # Module 15: Workflow complet
    "WorkflowService",
    "get_workflow_service",
    
    # Module 12: Tableaux de bord
    "DashboardService",
    "get_dashboard_service",
    
    # Module 13: Gestion utilisateurs
    "UserPermissionService",
    "get_user_permission_service",
    
    # Module 14: Intelligence artificielle
    "AIService",
    "get_ai_service",
    
    # Module 5: Intégration PMMP
    "PMMPService",
    "get_pmmp_service",
    "PMMPIntegrationService",
    "get_pmmp_integration_service",
]

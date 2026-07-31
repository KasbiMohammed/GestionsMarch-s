"""
Modèles de la base de données
Définition des tables SQLAlchemy
"""

from app.models.user import User, Role
from app.models.market import Market, Company
from app.models.stage import Stage, StageStatus
from app.models.document import Document
from app.models.history import History

# Nouveaux modèles pour les 15 modules
from app.models.annual_planning import (
    AnnualPlanning, ServiceNeed, BudgetEstimate, Service,
    PlanningStatus, NeedPriority
)
from app.models.market_preparation import (
    MarketPreparation,
    PreparationDocument,
    PreparationHistory,
    PreparationAlert,
    PreparationStatus
)
from app.models.validation_workflow import (
    ValidationWorkflow,
    ValidationRecord,
    ValidationChecklist,
    ValidationHistory,
    ValidationAlert,
    ValidationStep,
    ValidationDecision,
    WorkflowStatus
)
from app.models.procurement_rules import (
    ProcurementRule, ProcurementDecision, ProcurementMethod, MarketNature
)
from app.models.commission import (
    Commission,
    CommissionMember,
    CommissionSession,
    CommissionAlert,
    CommissionHistory,
    CommissionStatus,
    SessionStatus,
    MemberRole
)
from app.models.publication import (
    Publication,
    PublicationSupport,
    PublicationDeadline,
    PublicationAlert,
    PublicationHistory,
    PublicationType,
    PublicationStatus,
    ProcedureType,
    SupportType
)
from app.models.offer_management import (
    PMMPPublication, Offer, OfferDocument,
    PublicationStatus, OfferStatus
)
from app.models.attribution import (
    Attribution, Reclamation, AttributionStatus
)
from app.models.execution import (
    ServiceOrder, ExecutionPlan, Milestone, Attachment, Payment,
    Amendment, Guarantee, Penalty, Reception, ExecutionStatus
)
from app.models.document_management import (
     DocumentVersion, DocumentAccess, DocumentCategory
)
from app.models.alerts import (
    Alert, AlertRule, AlertType, AlertSeverity, AlertStatus
)
from app.models.workflow import (
    Workflow, WorkflowStepExecution, WorkflowTransition,
    WorkflowStep, WorkflowStatus
)

__all__ = [
    # Modèles existants
    "User",
    "Role",
    "Market",
    "Company",
    "Stage",
    "StageStatus",
    "Document",
    "History",
    
    # Module 1: Planification annuelle
    "AnnualPlanning", "ServiceNeed", "BudgetEstimate", "Service",
    "PlanningStatus", "NeedPriority",
    
    # Module 2: Préparation du marché
    "MarketPreparation", "CPS", "BPU", "DQE", "TechnicalPlan", "PreparationStatus",
    
    # Module 3: Choix automatique de la procédure
    "ProcurementRule", "ProcurementDecision", "ProcurementMethod", "MarketNature",
    
    # Module 4: Gestion des commissions
    "Commission", "CommissionMember", "CommissionConvocation",
    "CommissionType", "CommissionStatus",
    
    # Module 5 & 6: Publication PMMP et Réception des offres
    "PMMPPublication", "Offer", "OfferDocument",
    "PublicationStatus", "OfferStatus",
    
    # Module 8: Attribution
    "Attribution", "Reclamation", "AttributionStatus",
    
    # Module 9: Exécution du marché
    "ServiceOrder", "ExecutionPlan", "Milestone", "Attachment", "Payment",
    "Amendment", "Guarantee", "Penalty", "Reception", "ExecutionStatus",
    
    # Module 10: Gestion documentaire
    "DocumentVersion", "DocumentAccess", "DocumentCategory",
    
    # Module 11: Alertes intelligentes
    "Alert", "AlertRule", "AlertType", "AlertSeverity", "AlertStatus",
    
    # Module 15: Workflow complet
    "Workflow", "WorkflowStepExecution", "WorkflowTransition",
    "WorkflowStep", "WorkflowStatus",
]

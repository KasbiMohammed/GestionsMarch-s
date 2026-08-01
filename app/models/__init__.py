"""
Modèles de la base de données
Définition des tables SQLAlchemy

CORRECTIONS APPLIQUEES :
1. Ajout de l'import manquant MarketPlanning (référencé par relationship)
2. Cohérence __all__ / imports : retrait des noms non importés (CPS, BPU, DQE,
   TechnicalPlan, CommissionConvocation, CommissionType) et ajout des imports manquants
3. Résolution des conflits de noms par alias (WorkflowStatus, ProcedureType, PlanningPriority)
4. Suppression des imports dupliqués écrasant les précédents
"""

from app.models.user import User, Role
from app.models.market import Market, Company
from app.models.stage import Stage, StageStatus
from app.models.document import Document
from app.models.history import History

# ───────────────────────────────────────────────────────────────
# Module 1 : Planification annuelle
# ───────────────────────────────────────────────────────────────
from app.models.annual_planning import (
    AnnualPlanning, ServiceNeed, BudgetEstimate, Service,
    PlanningStatus, NeedPriority
)

# ───────────────────────────────────────────────────────────────
# Module 2 : Préparation du marché
# ───────────────────────────────────────────────────────────────
from app.models.market_preparation import (
    MarketPreparation,
    PreparationDocument,
    PreparationHistory,
    PreparationAlert,
    PreparationStatus
)

# ───────────────────────────────────────────────────────────────
# Module 3 : Workflow de validation
# ───────────────────────────────────────────────────────────────
from app.models.validation_workflow import (
    ValidationWorkflow,
    ValidationRecord,
    ValidationChecklist,
    ValidationHistory,
    ValidationAlert,
    ValidationStep,
    ValidationDecision,
    WorkflowStatus as ValidationWorkflowStatus   # ← ALIAS : évite l'écrasement
)

# ───────────────────────────────────────────────────────────────
# Module 4 : Règles de passation
# ───────────────────────────────────────────────────────────────
from app.models.procurement_rules import (
    ProcurementRule, ProcurementDecision, ProcurementMethod, MarketNature
)

# ───────────────────────────────────────────────────────────────
# Module 5 : Gestion des commissions
# ───────────────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────────────
# Module 6 : Publication
# ───────────────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────────────
# Module 7 : Gestion des offres (PMMP)
# NOTE : PublicationStatus retiré car déjà importé depuis publication (évite le shadowing)
# ───────────────────────────────────────────────────────────────
from app.models.offer_management import (
    PMMPPublication, Offer, OfferDocument, OfferStatus
)

# ───────────────────────────────────────────────────────────────
# Module 8 : Attribution
# ───────────────────────────────────────────────────────────────
from app.models.attribution import (
    Attribution, Reclamation, AttributionStatus
)

# ───────────────────────────────────────────────────────────────
# Module 9 : Exécution du marché
# ───────────────────────────────────────────────────────────────
from app.models.execution import (
    ServiceOrder, ExecutionPlan, Milestone, Attachment, Payment,
    Amendment, Guarantee, Penalty, Reception, ExecutionStatus
)

# ───────────────────────────────────────────────────────────────
# Module 10 : Gestion documentaire
# ───────────────────────────────────────────────────────────────
from app.models.document_management import (
     DocumentVersion, DocumentAccess, DocumentCategory
)

# ───────────────────────────────────────────────────────────────
# Module 11 : Alertes intelligentes
# ───────────────────────────────────────────────────────────────
from app.models.alerts import (
    Alert, AlertRule, AlertType, AlertSeverity, AlertStatus
)

# ───────────────────────────────────────────────────────────────
# Module 12 : Workflow complet
# ───────────────────────────────────────────────────────────────
from app.models.workflow import (
    Workflow, WorkflowStepExecution, WorkflowTransition,
    WorkflowStep, WorkflowStatus
)

# ───────────────────────────────────────────────────────────────
# CORRECTION CRITIQUE : Import manquant pour MarketPlanning
# Nécessaire car MarketPreparation fait référence à relationship("MarketPlanning")
# Si le module market_planning n'existe pas dans votre projet, commentez ce bloc
# et remplacez le relationship par une référence chaîne : relationship("MarketPlanning")
# ───────────────────────────────────────────────────────────────
from app.models.market_planning import (
    MarketPlanning,
    PlanningDocument as MarketPlanningDocument,      # ← ALIAS : évite le conflit
    ProjectType,
    ProcedureType as MarketProcedureType,            # ← ALIAS : déjà défini dans publication
    PlanningPriority as MarketPlanningPriority,      # ← ALIAS : déjà défini dans annual_planning
    MarketPlanningStatus
)


# ═══════════════════════════════════════════════════════════════
# EXPORTS PUBLICS
# ═══════════════════════════════════════════════════════════════
__all__ = [
    # ── Modèles existants ──
    "User",
    "Role",
    "Market",
    "Company",
    "Stage",
    "StageStatus",
    "Document",
    "History",

    # ── Module 1 : Planification annuelle ──
    "AnnualPlanning", "ServiceNeed", "BudgetEstimate", "Service",
    "PlanningStatus", "NeedPriority",

    # ── Module 2 : Préparation du marché ──
    "MarketPreparation",
    "PreparationDocument",
    "PreparationHistory",
    "PreparationAlert",
    "PreparationStatus",
    # SUPPRESSIONS : CPS, BPU, DQE, TechnicalPlan (non importés / inexistants)

    # ── Module 3 : Workflow de validation ──
    "ValidationWorkflow",
    "ValidationRecord",
    "ValidationChecklist",
    "ValidationHistory",
    "ValidationAlert",
    "ValidationStep",
    "ValidationDecision",
    "ValidationWorkflowStatus",

    # ── Module 4 : Règles de passation ──
    "ProcurementRule", "ProcurementDecision", "ProcurementMethod", "MarketNature",

    # ── Module 5 : Gestion des commissions ──
    "Commission",
    "CommissionMember",
    "CommissionSession",
    "CommissionAlert",
    "CommissionHistory",
    "CommissionStatus",
    "SessionStatus",
    "MemberRole",
    # SUPPRESSIONS : CommissionConvocation, CommissionType (non importés / inexistants)

    # ── Module 6 : Publication ──
    "Publication",
    "PublicationSupport",
    "PublicationDeadline",
    "PublicationAlert",
    "PublicationHistory",
    "PublicationType",
    "PublicationStatus",
    "ProcedureType",
    "SupportType",

    # ── Module 7 : Gestion des offres (PMMP) ──
    "PMMPPublication", "Offer", "OfferDocument", "OfferStatus",

    # ── Module 8 : Attribution ──
    "Attribution", "Reclamation", "AttributionStatus",

    # ── Module 9 : Exécution du marché ──
    "ServiceOrder", "ExecutionPlan", "Milestone", "Attachment", "Payment",
    "Amendment", "Guarantee", "Penalty", "Reception", "ExecutionStatus",

    # ── Module 10 : Gestion documentaire ──
    "DocumentVersion", "DocumentAccess", "DocumentCategory",

    # ── Module 11 : Alertes intelligentes ──
    "Alert", "AlertRule", "AlertType", "AlertSeverity", "AlertStatus",

    # ── Module 12 : Workflow complet ──
    "Workflow", "WorkflowStepExecution", "WorkflowTransition",
    "WorkflowStep", "WorkflowStatus",

    # ── Module 13 : Planification de marché (import manquant corrigé) ──
    "MarketPlanning",
    "MarketPlanningDocument",
    "ProjectType",
    "MarketProcedureType",
    "MarketPlanningPriority",
    "MarketPlanningStatus",
]
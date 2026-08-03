"""
Application FastAPI principale
Point d'entrée de l'application web
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db, init_db
from app.api import (
    auth, users, markets, stages, documents, dashboard,
    search, exports, analysis, market_planning, market_preparation,
    validation_workflow, commission, publication, supervision, deadlines, chatbot, calendar, regulatory_knowledge
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Lifespan (remplace @app.on_event déprécié)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    try:
        init_db()
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} démarrée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise
    yield
    # Shutdown
    logger.info(f"{settings.APP_NAME} arrêtée")


# ─────────────────────────────────────────────
# Création de l'application FastAPI
# ─────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Application de gestion des marchés publics pour les communes territoriales marocaines",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# Configuration CORS (sécurisée)
# ─────────────────────────────────────────────
# allow_credentials=True est INCOMPATIBLE avec allow_origins=["*"]
cors_origins = getattr(settings, "CORS_ORIGINS", ["http://localhost:8000", "http://127.0.0.1:8000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Fichiers statiques et templates
# ─────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

templates = Jinja2Templates(directory="app/templates")

# ─────────────────────────────────────────────
# Filtres Jinja2 personnalisés
# ─────────────────────────────────────────────
def get_status_color(status):
    """Retourne la couleur Bootstrap pour un statut de marché"""
    colors = {
        'en_preparation': 'info',
        'en_cours': 'warning',
        'termine': 'success',
        'en_attente': 'secondary',
        'en_retard': 'danger',
        'annule': 'danger',
        'suspendu': 'dark'
    }
    return colors.get(status, 'secondary')

# Enregistrer comme filtre ET comme fonction globale
templates.env.filters['getStatusColor'] = get_status_color
templates.env.globals['getStatusColor'] = get_status_color

# ─────────────────────────────────────────────
# Helper d'authentification (factorisé)
# ─────────────────────────────────────────────
def get_current_user_or_none(request: Request, db: Session):
    """
    Récupère l'utilisateur connecté depuis le cookie access_token.
    Retourne None si non authentifié ou token invalide.
    """
    from app.api.auth import get_current_user_from_token
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    try:
        return get_current_user_from_token(access_token, db)
    except Exception:
        return None


# ─────────────────────────────────────────────
# Routes API
# ─────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
app.include_router(stages.router, prefix="/api/stages", tags=["Stages"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(market_planning.router, prefix="/api/market-planning", tags=["Market Planning"])
app.include_router(market_preparation.router, prefix="/api/market-preparation", tags=["Market Preparation"])
app.include_router(validation_workflow.router, prefix="/api/validation-workflow", tags=["Validation Workflow"])
app.include_router(commission.router, prefix="/api/commission", tags=["Commission"])
app.include_router(publication.router, prefix="/api/publication", tags=["Publication"])
app.include_router(supervision.router, prefix="/api/supervision", tags=["Supervision"])
app.include_router(deadlines.router, prefix="/api/deadlines", tags=["Deadlines"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(regulatory_knowledge.router, prefix="/api/regulatory-knowledge", tags=["Regulatory Knowledge"])


# ─────────────────────────────────────────────
# Routes pages HTML
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request, db: Session = Depends(get_db)):
    """Page racine - redirige vers le dashboard si authentifié, sinon login"""
    user = get_current_user_or_none(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    """Page du tableau de bord"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/markets", response_class=HTMLResponse)
async def markets_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion des marchés"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("markets/list.html", {"request": request, "user": user})


@app.get("/markets/new", response_class=HTMLResponse)
async def market_new_page(request: Request, db: Session = Depends(get_db)):
    """Page de création d'un marché"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    # Rediriger vers la liste avec un paramètre pour ouvrir le modal de création
    return RedirectResponse(url="/markets?mode=new", status_code=302)


@app.get("/markets/{market_id}", response_class=HTMLResponse)
async def market_detail_page(request: Request, market_id: int, db: Session = Depends(get_db)):
    """Page de détail d'un marché"""
    from app.models.market import Market

    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})

    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        return RedirectResponse(url="/markets", status_code=302)

    # Convertir l'objet SQLAlchemy en dict pour éviter les problèmes Jinja2
    market_dict = {
        'id': market.id,
        'market_number': market.market_number,
        'object': market.object,
        'master_of_work': market.master_of_work,
        'market_type': market.market_type.value if market.market_type else None,
        'procurement_method': market.procurement_method.value if market.procurement_method else None,
        'estimated_amount': market.estimated_amount,
        'definitive_amount': market.definitive_amount,
        'budget': market.budget,
        'credits': market.credits,
        'responsible_service': market.responsible_service,
        'follow_up_responsible': market.follow_up_responsible,
        'launch_date': market.launch_date,
        'publication_date': market.publication_date,
        'opening_date': market.opening_date,
        'attribution_date': market.attribution_date,
        'notification_date': market.notification_date,
        'start_date': market.start_date,
        'provisional_acceptance_date': market.provisional_acceptance_date,
        'definitive_acceptance_date': market.definitive_acceptance_date,
        'expected_end_date': market.expected_end_date,
        'actual_end_date': market.actual_end_date,
        'status': market.status.value if market.status else None,
        'progress_percentage': market.progress_percentage,
        'participating_companies_count': market.participating_companies_count,
        'observations': market.observations,
        'comments': market.comments,
        'companies': [
            {
                'id': c.id,
                'name': c.name,
                'rc_number': c.rc_number,
                'if_number': c.if_number,
                'address': c.address,
                'phone': c.phone,
                'email': c.email,
                'offer_amount': c.offer_amount,
                'offer_rank': c.offer_rank,
                'is_attributed': c.is_attributed,
                'technical_score': c.technical_score,
                'financial_score': c.financial_score,
                'total_score': c.total_score,
                'observations': c.observations
            }
            for c in market.companies
        ]
    }

    return templates.TemplateResponse(
        "markets/detail.html",
        {"request": request, "user": user, "market": market_dict}
    )


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request, db: Session = Depends(get_db)):
    """Page d'analyse des marchés PMMP"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("markets/analysis.html", {"request": request, "user": user})


@app.get("/planification", response_class=HTMLResponse)
async def planification_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion de la planification des marchés"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("planification/list.html", {"request": request, "user": user})


@app.get("/planification/new", response_class=HTMLResponse)
async def planification_new_page(request: Request, db: Session = Depends(get_db)):
    """Page de création d'une planification"""
    from app.models.annual_planning import Service
    from app.models.user import User

    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})

    services = db.query(Service).order_by(Service.name).all()
    users = db.query(User).filter(User.is_active == True).order_by(User.full_name).all()

    return templates.TemplateResponse(
        "planification/form.html",
        {
            "request": request,
            "user": user,
            "planning": None,
            "services": services,
            "users": users,
            "current_year": 2025
        }
    )


@app.get("/planification/{planning_id}", response_class=HTMLResponse)
async def planification_detail_page(request: Request, planning_id: int, db: Session = Depends(get_db)):
    """Page de détail d'une planification"""
    from app.models.market_planning import MarketPlanning

    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})

    planning = db.query(MarketPlanning).filter(MarketPlanning.id == planning_id).first()
    if not planning:
        return RedirectResponse(url="/planification", status_code=302)

    # Passage de l'objet SQLAlchemy directement (cohérent avec edit)
    return templates.TemplateResponse(
        "planification/detail.html",
        {"request": request, "user": user, "planning": planning}
    )


@app.get("/planification/{planning_id}/edit", response_class=HTMLResponse)
async def planification_edit_page(request: Request, planning_id: int, db: Session = Depends(get_db)):
    """Page de modification d'une planification"""
    from app.models.market_planning import MarketPlanning
    from app.models.annual_planning import Service
    from app.models.user import User

    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})

    planning = db.query(MarketPlanning).filter(MarketPlanning.id == planning_id).first()
    if not planning:
        return RedirectResponse(url="/planification", status_code=302)

    services = db.query(Service).order_by(Service.name).all()
    users = db.query(User).filter(User.is_active == True).order_by(User.full_name).all()

    return templates.TemplateResponse(
        "planification/form.html",
        {
            "request": request,
            "user": user,
            "planning": planning,
            "services": services,
            "users": users,
            "current_year": planning.fiscal_year
        }
    )


@app.get("/preparation", response_class=HTMLResponse)
async def preparation_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion de la préparation des marchés"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("preparation/list.html", {"request": request, "user": user})


@app.get("/preparation/new", response_class=HTMLResponse)
async def preparation_new_page(request: Request, db: Session = Depends(get_db)):
    """Page de création d'une préparation"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})

    planning_id = request.query_params.get("planning_id")

    return templates.TemplateResponse(
        "preparation/form.html",
        {
            "request": request,
            "user": user,
            "planning_id": planning_id
        }
    )


@app.get("/preparation/{preparation_id}", response_class=HTMLResponse)
async def preparation_detail_page(request: Request, preparation_id: int, db: Session = Depends(get_db)):
    """Page de détail d'une préparation"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("preparation/detail.html", {"request": request, "user": user})


@app.get("/validation", response_class=HTMLResponse)
async def validation_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion de la validation des dossiers"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("validation/list.html", {"request": request, "user": user})


@app.get("/validation/{workflow_id}", response_class=HTMLResponse)
async def validation_detail_page(request: Request, workflow_id: int, db: Session = Depends(get_db)):
    """Page de détail d'un workflow de validation"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("validation/detail.html", {"request": request, "user": user})


@app.get("/commission", response_class=HTMLResponse)
async def commission_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion des commissions"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("commission/list.html", {"request": request, "user": user})


@app.get("/commission/{commission_id}", response_class=HTMLResponse)
async def commission_detail_page(request: Request, commission_id: int, db: Session = Depends(get_db)):
    """Page de détail d'une commission"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("commission/detail.html", {"request": request, "user": user})


@app.get("/publication", response_class=HTMLResponse)
async def publication_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion des publications"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("publication/list.html", {"request": request, "user": user})


@app.get("/publication/{publication_id}", response_class=HTMLResponse)
async def publication_detail_page(request: Request, publication_id: int, db: Session = Depends(get_db)):
    """Page de détail d'une publication"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("publication/detail.html", {"request": request, "user": user})


@app.get("/supervision", response_class=HTMLResponse)
async def supervision_page(request: Request, db: Session = Depends(get_db)):
    """Page du dashboard de supervision"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("supervision/dashboard.html", {"request": request, "user": user})


@app.get("/deadlines", response_class=HTMLResponse)
async def deadlines_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion des délais réglementaires"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("deadlines/index.html", {"request": request, "user": user})


@app.get("/deadlines/settings", response_class=HTMLResponse)
async def deadlines_settings_page(request: Request, db: Session = Depends(get_db)):
    """Page des paramètres des délais"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("deadlines/settings.html", {"request": request, "user": user})


@app.get("/deadlines/calendar", response_class=HTMLResponse)
async def deadlines_calendar_page(request: Request, db: Session = Depends(get_db)):
    """Page du calendrier des délais"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("deadlines/calendar.html", {"request": request, "user": user})


@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, db: Session = Depends(get_db)):
    """Page du chatbot IA"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("chatbot/chat.html", {"request": request, "user": user})


@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, db: Session = Depends(get_db)):
    """Page du calendrier intelligent"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("calendar/calendar.html", {"request": request, "user": user})


@app.get("/regulatory-knowledge", response_class=HTMLResponse)
async def regulatory_knowledge_page(request: Request, db: Session = Depends(get_db)):
    """Page de la base de connaissances réglementaire"""
    user = get_current_user_or_none(request, db)
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    return templates.TemplateResponse("regulatory_knowledge/index.html", {"request": request, "user": user})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
"""
Application FastAPI principale
Point d'entrée de l'application web
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os
from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.database import engine, get_db, init_db
from app.api import auth, users, markets, stages, documents, dashboard, search, exports, analysis

# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Application de gestion des marchés publics pour les communes territoriales marocaines",
    debug=settings.DEBUG
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Configuration des templates Jinja2
templates = Jinja2Templates(directory="app/templates")


# Événements de démarrage et d'arrêt
@app.on_event("startup")
async def startup_event():
    """Actions effectuées au démarrage de l'application"""
    # Initialisation de la base de données
    init_db()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} démarrée avec succès")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions effectuées à l'arrêt de l'application"""
    print(f"{settings.APP_NAME} arrêtée")


# Route racine
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Page d'accueil - Redirection vers le tableau de bord ou la connexion"""
    from app.api.auth import get_current_user_from_token
    
    # Vérifier si l'utilisateur est connecté
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            user = get_current_user_from_token(access_token, db)
            if user:
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>Dashboard</title></head>
                <body>
                    <h1>Dashboard</h1>
                    <p>Bienvenue, {}!</p>
                    <a href="/api/auth/logout">Déconnexion</a>
                </body>
                </html>
                """.format(user.full_name))
        except:
            pass
    
    # Page de connexion simple
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connexion - Gestion des Marchés Publics</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card shadow">
                        <div class="card-body p-5">
                            <h3 class="text-center mb-4">Gestion des Marchés Publics</h3>
                            <p class="text-center text-muted mb-4">Communes Territoriales Marocaines</p>
                            <form id="loginForm">
                                <div class="mb-3">
                                    <label class="form-label">Nom d'utilisateur</label>
                                    <input type="text" class="form-control" id="username" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Mot de passe</label>
                                    <input type="password" class="form-control" id="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Se connecter</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            try {
                const response = await fetch('/api/auth/login/json', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                if (response.ok) {
                    document.cookie = 'access_token=' + data.access_token + '; path=/; max-age=1800';
                    window.location.href = '/';
                } else {
                    alert(data.detail || 'Erreur de connexion');
                }
            } catch (error) {
                alert('Erreur de connexion au serveur');
            }
        });
        </script>
    </body>
    </html>
    """)


# Enregistrement des routes API
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
app.include_router(stages.router, prefix="/api/stages", tags=["Stages"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


# Routes pages HTML
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    """Page du tableau de bord"""
    from app.api.auth import get_current_user_from_token
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    
    user = get_current_user_from_token(access_token, db)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/markets", response_class=HTMLResponse)
async def markets_page(request: Request, db: Session = Depends(get_db)):
    """Page de gestion des marchés"""
    from app.api.auth import get_current_user_from_token
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    
    user = get_current_user_from_token(access_token, db)
    return templates.TemplateResponse("markets/list.html", {"request": request, "user": user})


@app.get("/markets/{market_id}", response_class=HTMLResponse)
async def market_detail_page(request: Request, market_id: int, db: Session = Depends(get_db)):
    """Page de détail d'un marché"""
    from app.api.auth import get_current_user_from_token
    from app.models.market import Market
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    
    user = get_current_user_from_token(access_token, db)
    market = db.query(Market).filter(Market.id == market_id).first()
    
    return templates.TemplateResponse(
        "markets/detail.html",
        {"request": request, "user": user, "market": market}
    )


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request, db: Session = Depends(get_db)):
    """Page d'analyse des marchés PMMP"""
    from app.api.auth import get_current_user_from_token
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        return templates.TemplateResponse("auth/login.html", {"request": request})
    
    user = get_current_user_from_token(access_token, db)
    return templates.TemplateResponse("markets/analysis.html", {"request": request, "user": user})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

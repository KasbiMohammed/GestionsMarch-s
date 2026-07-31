"""
API de gestion de la planification des marchés
Endpoints CRUD complets avec documents joints
"""

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import (
    can_create_planning,
    can_delete_planning,
    can_edit_planning,
    can_export_data,
    can_view_planning,
)
from app.config import settings
from app.database import get_db
from app.models.market_planning import (
    MarketPlanningStatus,
    PlanningDocument,
    PlanningPriority,
    ProcedureType,
    ProjectType,
)
from app.models.user import User
from app.schemas.market_planning import (
    MarketPlanningCreate,
    MarketPlanningListResponse,
    MarketPlanningResponse,
    MarketPlanningStatistics,
    MarketPlanningUpdate,
    PlanningDocumentResponse,
)
from app.services.market_planning_service import get_market_planning_service

router = APIRouter()

# ─────────────────────────────────────────
# Constantes de sécurité
# ─────────────────────────────────────────
ALLOWED_SORT_COLUMNS = {
    "created_at",
    "updated_at",
    "planning_number",
    "title",
    "estimated_budget",
    "launch_date",
    "fiscal_year",
    "status",
    "priority",
}

ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"}


class ServiceResponse(BaseModel):
    id: int
    code: Optional[str] = None
    name: str


class PlanningNumberResponse(BaseModel):
    planning_number: str


# ─────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────
@router.get("/", response_model=MarketPlanningListResponse)
async def list_plannings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    fiscal_year: Optional[int] = None,
    project_type: Optional[ProjectType] = None,
    procedure_type: Optional[ProcedureType] = None,
    status: Optional[MarketPlanningStatus] = None,
    priority: Optional[PlanningPriority] = None,
    requesting_service_id: Optional[int] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste paginée des planifications avec recherche, filtres et tri."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Sécurité : whitelist du tri pour éviter l'injection SQL
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Colonne de tri non autorisée. Valeurs possibles : {', '.join(sorted(ALLOWED_SORT_COLUMNS))}",
        )

    # Nettoyage de la recherche
    if search:
        search = search.strip()
        if not search:
            search = None

    service = get_market_planning_service(db)
    items, total = service.list_plannings(
        skip=skip,
        limit=limit,
        search=search,
        fiscal_year=fiscal_year,
        project_type=project_type,
        procedure_type=procedure_type,
        status=status,
        priority=priority,
        requesting_service_id=requesting_service_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = (total + limit - 1) // limit if limit else 1
    current_page = (skip // limit) + 1 if limit else 1

    return MarketPlanningListResponse(
        items=items,
        total=total,
        page=current_page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.get("/statistics", response_model=MarketPlanningStatistics)
async def get_planning_statistics(
    fiscal_year: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques de planification pour le tableau de bord."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    return service.get_statistics(fiscal_year=fiscal_year)


@router.get("/services", response_model=list[ServiceResponse])
async def list_services(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste des services demandeurs."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    services = service.list_services()
    return [
        ServiceResponse(id=s.id, code=getattr(s, "code", None), name=s.name)
        for s in services
    ]


@router.get("/generate-number", response_model=PlanningNumberResponse)
async def generate_planning_number(
    fiscal_year: int = Query(..., ge=2000, le=2100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Génère un numéro de planification pour un exercice."""
    if not can_create_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    return PlanningNumberResponse(planning_number=service.generate_planning_number(fiscal_year))


@router.get("/{planning_id}", response_model=MarketPlanningResponse)
async def get_planning(
    planning_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Récupère une planification par ID."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    planning = service.get_by_id(planning_id)
    if not planning:
        raise HTTPException(status_code=404, detail="Planification non trouvée")
    return planning


@router.post("/", response_model=MarketPlanningResponse, status_code=status.HTTP_201_CREATED)
async def create_planning(
    planning_data: MarketPlanningCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle planification."""
    if not can_create_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    try:
        return service.create(planning_data.model_dump(), current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{planning_id}", response_model=MarketPlanningResponse)
async def update_planning(
    planning_id: int,
    planning_data: MarketPlanningUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une planification."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    try:
        planning = service.update(
            planning_id,
            planning_data.model_dump(exclude_unset=True),
            current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not planning:
        raise HTTPException(status_code=404, detail="Planification non trouvée")
    return planning


@router.delete("/{planning_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planning(
    planning_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Supprime une planification."""
    if not can_delete_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)
    if not service.delete(planning_id, current_user.id):
        raise HTTPException(status_code=404, detail="Planification non trouvée")


@router.post(
    "/{planning_id}/documents",
    response_model=PlanningDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    planning_id: int,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ajoute un document joint à une planification."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Nettoyage des entrées texte
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Le nom du document est requis")
    if description:
        description = description.strip() or None

    # Validation du nom de fichier
    original_filename = (file.filename or "document").strip()
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non autorisé. Extensions acceptées : {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}",
        )

    # Vérification de la taille AVANT lecture complète en mémoire
    try:
        file.file.seek(0, 2)  # seek to end
        file_size = file.file.tell()
        file.file.seek(0)     # seek back to start
    except (OSError, AttributeError):
        file_size = None

    if file_size is not None and file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo)")

    content = await file.read()

    # Double vérification après lecture (sécurité défense en profondeur)
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 Mo)")

    service = get_market_planning_service(db)
    document = service.add_document(
        planning_id=planning_id,
        file_content=content,
        original_filename=original_filename,
        name=name,
        user_id=current_user.id,
        description=description,
        content_type=file.content_type,
    )
    if not document:
        raise HTTPException(status_code=404, detail="Planification non trouvée")
    return document


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Télécharge un document joint."""
    if not can_view_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)

    # Vérifier que le document existe
    document = db.query(PlanningDocument).filter(PlanningDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    # Vérifier que la planification parente existe et est accessible
    planning = service.get_by_id(document.planning_id)
    if not planning:
        raise HTTPException(status_code=404, detail="Planification associée non trouvée")

    # Protection contre le path traversal
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    file_path = Path(document.file_path).resolve()
    if not str(file_path).startswith(str(upload_dir)):
        raise HTTPException(status_code=403, detail="Accès interdit au fichier")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé sur le disque")

    return FileResponse(
        path=str(file_path),
        filename=document.file_name,
        media_type=document.file_type or "application/octet-stream",
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Supprime un document joint."""
    if not can_edit_planning(current_user.role):
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    service = get_market_planning_service(db)

    # Vérifier l'existence et l'appartenance avant suppression
    document = db.query(PlanningDocument).filter(PlanningDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    planning = service.get_by_id(document.planning_id)
    if not planning:
        raise HTTPException(status_code=404, detail="Planification associée non trouvée")

    # La suppression est déléguée au service (qui peut vérifier des règles métier supplémentaires)
    if not service.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document non trouvé")
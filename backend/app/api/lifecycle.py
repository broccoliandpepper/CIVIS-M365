"""
Endpoints Archive & Lifecycle
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db_hot, get_db_config
from app.services.lifecycle_service import LifecycleService
from app.models.auth import User
from app.api.auth import get_current_user, require_admin


router = APIRouter(prefix="/api/v1/lifecycle", tags=["Lifecycle"])


@router.get("/status")
async def get_archive_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Statut des bases de données HOT et Archive"""
    return LifecycleService.get_archive_status(db)


@router.post("/backup/create")
async def create_backup(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Crée un backup chiffré de la DB HOT"""
    result = LifecycleService.create_backup(
        db,
        created_by=current_user.username
    )
    return result


@router.get("/backups")
async def list_backups(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config)
):
    """Liste les backups disponibles"""
    backups = LifecycleService.list_backups(db, limit)
    return {
        "backups": backups,
        "total": len(backups)
    }


@router.get("/logs")
async def list_lifecycle_logs(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config)
):
    """Liste les logs du lifecycle"""
    logs = LifecycleService.list_lifecycle_logs(db, limit)
    return {
        "logs": logs,
        "total": len(logs)
    }


@router.get("/backup/{backup_id}/contents")
async def inspect_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config)
):
    """Inspecte le contenu d'un backup."""
    return LifecycleService.inspect_backup(db, backup_id)


@router.post("/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Restaure un backup dans un dossier isolé."""
    return LifecycleService.restore_backup(db, backup_id, restored_by=current_user.username)


@router.post("/backup/{backup_id}/verify")
async def verify_backup(
    backup_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Vérifie l'intégrité d'un backup"""
    return LifecycleService.verify_backup(db, backup_id)
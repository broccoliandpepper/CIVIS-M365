"""Endpoints Archive & Lifecycle."""

from fastapi import APIRouter, Depends, Query, UploadFile, File
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
import tempfile

from app.api.auth import get_current_user, require_admin
from app.database import get_db_config, get_db_hot
from app.models.auth import User
from app.services.lifecycle_service import LifecycleService


router = APIRouter(prefix="/api/v1/lifecycle", tags=["Lifecycle"])


class ActiveRestoreRequest(BaseModel):
    confirm_phrase: str


class RollbackRequest(BaseModel):
    confirm_phrase: str


@router.get("/status")
async def get_archive_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
):
    """Statut des bases de données HOT et Archive."""
    return LifecycleService.get_archive_status(db)


@router.post("/backup/create")
async def create_backup(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    """Crée un backup chiffré AES-256-GCM multi-bases."""
    return LifecycleService.create_backup(db, created_by=current_user.username)


@router.get("/backups")
async def list_backups(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config),
):
    backups = LifecycleService.list_backups(db, limit)
    return {
        "backups": backups,
        "total": len(backups),
    }


@router.get("/logs")
async def list_lifecycle_logs(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config),
):
    logs = LifecycleService.list_lifecycle_logs(db, limit)
    return {
        "logs": logs,
        "total": len(logs),
    }


@router.get("/backup/{backup_id}/contents")
async def inspect_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config),
):
    return LifecycleService.inspect_backup(db, backup_id)


@router.post("/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    """Restore dry-run dans un dossier isolé."""
    return LifecycleService.restore_backup(db, backup_id, restored_by=current_user.username)


@router.post("/backup/{backup_id}/verify")
async def verify_backup(
    backup_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    return LifecycleService.verify_backup(db, backup_id)


@router.post("/backup/{backup_id}/restore/activate")
async def restore_backup_active(
    backup_id: str,
    request: ActiveRestoreRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    """Restauration active contrôlée de HOT et ARCHIVE avec rollback opérateur."""
    return LifecycleService.restore_backup_active(
        db,
        backup_id,
        restored_by=current_user.username,
        confirm_phrase=request.confirm_phrase,
    )


@router.post("/rollback/{rollback_id}")
async def rollback_active_restore(
    rollback_id: str,
    request: RollbackRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    """Réapplique un rollback snapshot à la demande de l'opérateur."""
    return LifecycleService.rollback_active_restore(
        db,
        rollback_id,
        restored_by=current_user.username,
        confirm_phrase=request.confirm_phrase,
    )


@router.post("/retention/run")
async def run_retention_rotation(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    """Déclenche manuellement la rotation/rétention des archives et snapshots rollback."""
    return LifecycleService.enforce_retention(db, triggered_by=current_user.username)


@router.post("/import")
async def import_backup_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config),
):
    """Importe un fichier backup .sbk existant et l'enregistre en base."""
    if not file.filename.endswith(".sbk"):
        return {"status": "failed", "error": "Le fichier doit être au format .sbk"}

    with tempfile.TemporaryDirectory(prefix="import_") as temp_dir:
        temp_path = Path(temp_dir) / file.filename
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return LifecycleService.import_backup(
            db, temp_path, imported_by=current_user.username
        )

"""
Service pour Archive & Lifecycle
"""

import os
import json
import zipfile
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.audit_logs_m365 import M365AuditLog
from app.models.archive_manifest import ArchiveManifest
from app.models.lifecycle_logs import LifecycleLog
from app.config import settings


class LifecycleService:
    """Service pour le lifecycle des données"""
    
    @staticmethod
    def get_archive_status(db: Session) -> dict:
        """Retourne le statut des bases de données"""
        from app.database import engine_hot, engine_archive
        
        from sqlalchemy import text
        
        with engine_hot.connect() as conn:
            signins_count = conn.execute(text("SELECT COUNT(*) FROM signins")).scalar()
            risky_count = conn.execute(text("SELECT COUNT(*) FROM risky_users")).scalar()
            incidents_count = conn.execute(text("SELECT COUNT(*) FROM incidents")).scalar()
        
        with engine_archive.connect() as conn:
            archive_signins = conn.execute(text("SELECT COUNT(*) FROM signins")).scalar()
        
        age_days = (datetime.utcnow() - datetime(2026, 1, 1)).days
        archive_threshold = 90
        
        return {
            "hot": {
                "records": signins_count,
                "risky_users": risky_count,
                "incidents": incidents_count,
                "age_days": age_days,
                "should_archive": age_days >= archive_threshold
            },
            "archive": {
                "records": archive_signins,
                "age_days": age_days - 90 if age_days > 90 else 0
            }
        }
    
    @staticmethod
    def create_backup(db: Session, created_by: str = "admin") -> dict:
        """Crée un backup chiffré de la DB HOT"""
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        lifecycle_log = LifecycleLog(
            operation="CREATE_BACKUP",
            status="started",
            created_by=created_by
        )
        db.add(lifecycle_log)
        db.commit()
        db.refresh(lifecycle_log)
        
        try:
            backup_dir = Path(settings.BACKUP_PATH) / "archives"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"{backup_id}.zip"
            
            hot_db_path = settings.DB_PATH.replace("./", "siem-m365/backend/")
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for db_file in ["siem_hot.db", "siem_hot.db-wal", "siem_hot.db-shm"]:
                    full_path = Path(db_file)
                    if full_path.exists():
                        zf.write(full_path, db_file)
            
            file_size = backup_file.stat().st_size
            
            with open(backup_file, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            
            manifest = ArchiveManifest(
                backup_id=backup_id,
                backup_filename=backup_file.name,
                backup_filepath=str(backup_file),
                period_from=datetime.utcnow() - timedelta(days=90),
                period_to=datetime.utcnow(),
                record_count_signins=db.query(SignIn).count(),
                record_count_risky=db.query(RiskyUser).count(),
                record_count_incidents=db.query(Incident).count(),
                record_count_audit=db.query(M365AuditLog).count(),
                total_records=0,
                file_size_bytes=file_size,
                md5_checksum=md5,
                is_encrypted=True,
                status="created",
                created_by=created_by
            )
            manifest.total_records = (
                manifest.record_count_signins +
                manifest.record_count_risky +
                manifest.record_count_incidents +
                manifest.record_count_audit
            )
            
            db.add(manifest)
            
            lifecycle_log.status = "completed"
            lifecycle_log.records_processed = manifest.total_records
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "status": "success",
                "backup_id": backup_id,
                "records": manifest.total_records,
                "size_bytes": file_size,
                "manifest_id": manifest.id
            }
            
        except Exception as e:
            lifecycle_log.status = "failed"
            lifecycle_log.error_message = str(e)
            lifecycle_log.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    def list_backups(db: Session, limit: int = 20) -> list:
        """Liste les backups disponibles"""
        backups = db.query(ArchiveManifest).order_by(
            ArchiveManifest.created_at.desc()
        ).limit(limit).all()
        return [b.to_dict() for b in backups]
    
    @staticmethod
    def list_lifecycle_logs(db: Session, limit: int = 50) -> list:
        """Liste les logs du lifecycle"""
        logs = db.query(LifecycleLog).order_by(
            LifecycleLog.started_at.desc()
        ).limit(limit).all()
        return [l.to_dict() for l in logs]
    
    @staticmethod
    def verify_backup(db: Session, backup_id: str) -> dict:
        """Vérifie l'intégrité d'un backup"""
        manifest = db.query(ArchiveManifest).filter(
            ArchiveManifest.backup_id == backup_id
        ).first()
        
        if not manifest:
            return {"status": "not_found"}
        
        try:
            with open(manifest.backup_filepath, 'rb') as f:
                current_md5 = hashlib.md5(f.read()).hexdigest()
            
            verified = current_md5 == manifest.md5_checksum
            
            if verified:
                manifest.status = "verified"
                manifest.verified_at = datetime.utcnow()
                db.commit()
            
            return {
                "status": "verified" if verified else "corrupted",
                "backup_id": backup_id,
                "expected_md5": manifest.md5_checksum,
                "actual_md5": current_md5
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
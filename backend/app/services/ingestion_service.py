"""
Service d'ingestion - Gestion des uploads et parsing
"""

import hashlib
import json
import logging
import traceback
from datetime import datetime
from typing import Tuple
from sqlalchemy.orm import Session

from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.truth_list import TruthListUser
from app.models.ingestion_logs import IngestionLog

logger = logging.getLogger("ingestion")


class IngestionService:
    """Service pour toutes les opérations d'ingestion"""
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calcule le hash SHA256 d'un fichier"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def create_ingestion_log(
        db: Session,
        filename: str,
        file_hash: str,
        file_size: int,
        source_type: str,
        uploaded_by: str
    ) -> IngestionLog:
        """Crée un log d'ingestion"""
        log = IngestionLog(
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            source_type=source_type,
            uploaded_by=uploaded_by,
            status="processing"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def update_ingestion_log(
        db: Session,
        log_id: int,
        lines_total: int,
        lines_added: int,
        lines_duplicate: int,
        lines_error: int,
        status: str,
        error_message: str = None
    ):
        """Met à jour le log d'ingestion"""
        log = db.query(IngestionLog).filter(IngestionLog.id == log_id).first()
        if log:
            log.lines_total = lines_total
            log.lines_added = lines_added
            log.lines_duplicate = lines_duplicate
            log.lines_error = lines_error
            log.status = status
            log.error_message = error_message
            log.completed_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def ingest_signins(db: Session, records: list, ingestion_log_id: int = None) -> Tuple[int, int, int]:
        """Ingère les SignIns avec déduplication"""
        import logging
        import traceback
        
        logger = logging.getLogger("ingestion")
        added = 0
        duplicates = 0
        errors = 0
        
        import json
        for idx, record in enumerate(records):
            try:
                event_id = record.get('event_id')
                if not event_id:
                    errors += 1
                    continue
                    
                existing = db.query(SignIn).filter(SignIn.event_id == event_id).first()
                if existing:
                    duplicates += 1
                    continue
                
                from datetime import datetime
                
                ts_value = record.get('timestamp')
                if isinstance(ts_value, str):
                    # Handle M365 ISO format: 2026-04-11T16:22:41Z or 2026-04-11T16:22:41.123456Z
                    ts_cleaned = ts_value.replace('Z', '').replace('+00:00', '')
                    try:
                        if '.' in ts_cleaned:
                            ts_value = datetime.fromisoformat(ts_cleaned)
                        else:
                            ts_value = datetime.fromisoformat(ts_cleaned)
                    except Exception:
                        ts_value = datetime.utcnow()
                elif not isinstance(ts_value, datetime):
                    ts_value = datetime.utcnow()
                
                signin = SignIn(
                    event_id=event_id,
                    timestamp=ts_value,
                    user_principal=record.get('user_principal'),
                    display_name=record.get('display_name'),
                    user_id=record.get('user_id'),
                    user_type=record.get('user_type'),
                    ip_address=record.get('ip_address'),
                    location_city=record.get('location_city'),
                    location_country=record.get('location_country'),
                    location_state=record.get('location_state'),
                    status=record.get('status'),
                    failure_reason=record.get('failure_reason'),
                    error_code=record.get('error_code'),
                    correlation_id=record.get('correlation_id'),
                    conditional_access_status=record.get('conditional_access_status'),
                    mfa_status=record.get('mfa_status'),
                    auth_method=record.get('auth_method'),
                    auth_requirement=record.get('auth_requirement'),
                    app_name=record.get('app_name'),
                    app_id=record.get('app_id'),
                    client_app=record.get('client_app'),
                    device_os=record.get('device_os'),
                    device_browser=record.get('device_browser'),
                    device_is_compliant=record.get('device_is_compliant'),
                    device_is_managed=record.get('device_is_managed'),
                    risk_detail=record.get('risk_detail'),
                    risk_state=record.get('risk_state'),
                    risk_level=record.get('risk_level'),
                    flagged_for_review=record.get('flagged_for_review'),
                    raw_json=record.get('raw_json', json.dumps(record))
                )
                db.add(signin)
                added += 1
            except Exception as e:
                logger.error(f"Error parsing signin {idx}: {e}")
                logger.error(traceback.format_exc())
                errors += 1
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing signins: {e}")
            logger.error(traceback.format_exc())
            db.rollback()
            errors += len(records) - duplicates
            added = 0
        
        return added, duplicates, errors
    
    @staticmethod
    def ingest_risky_users(db: Session, records: list) -> Tuple[int, int, int]:
        """Ingère les Risky Users avec déduplication"""
        added = 0
        duplicates = 0
        errors = 0
        
        import json
        for record in records:
            try:
                event_id = record.event_id
                if not event_id:
                    errors += 1
                    continue
                    
                existing = db.query(RiskyUser).filter(RiskyUser.event_id == event_id).first()
                if existing:
                    duplicates += 1
                    continue
                
                user = RiskyUser(
                    event_id=event_id,
                    timestamp=record.timestamp,
                    user_principal=record.user_principal,
                    user_id=record.user_id,
                    user_display_name=record.user_display_name,
                    risk_level=record.risk_level,
                    risk_state=record.risk_state,
                    risk_detail=record.risk_detail,
                    risk_last_updated=record.risk_last_updated,
                    is_deleted=record.is_deleted,
                    is_processing=record.is_processing,
                    detection_type=record.detection_type,
                    detection_timing=record.detection_timing,
                    raw_json=record.raw_json
                )
                db.add(user)
                added += 1
            except Exception as e:
                errors += 1
        
        db.commit()
        return added, duplicates, errors
    
    @staticmethod
    def ingest_incidents(db: Session, records: list) -> Tuple[int, int, int]:
        """Ingère les Incidents avec déduplication"""
        added = 0
        duplicates = 0
        errors = 0
        
        import json
        for record in records:
            try:
                incident_id = record.incident_id
                if not incident_id:
                    errors += 1
                    continue
                    
                existing = db.query(Incident).filter(Incident.incident_id == incident_id).first()
                if existing:
                    duplicates += 1
                    continue
                
                incident = Incident(
                    incident_id=incident_id,
                    timestamp=record.timestamp,
                    title=record.title,
                    severity=record.severity,
                    status=record.status,
                    assigned_to=record.assigned_to,
                    category=record.category,
                    priority_score=record.priority_score,
                    tags=record.tags,
                    investigation_state=record.investigation_state,
                    impacted_assets=record.impacted_assets,
                    active_alerts=record.active_alerts,
                    service_sources=record.service_sources,
                    detection_sources=record.detection_sources,
                    last_update_time=record.last_update_time,
                    last_activity=record.last_activity,
                    policy_name=record.policy_name,
                    data_sensitivity=record.data_sensitivity,
                    classification=record.classification,
                    determination=record.determination,
                    device_groups=record.device_groups,
                    creation_time=record.creation_time,
                    workspaces=record.workspaces,
                    cloud_scopes=record.cloud_scopes,
                    description=record.description,
                    raw_json=record.raw_json
                )
                db.add(incident)
                added += 1
            except Exception as e:
                errors += 1
        
        db.commit()
        return added, duplicates, errors
    
    @staticmethod
    def ingest_truth_list(db: Session, records: list, imported_by: str) -> int:
        """Ingère la Truth List"""
        added = 0
        
        for record in records:
            existing = db.query(TruthListUser).filter(
                TruthListUser.user_principal == record.user_principal
            ).first()
            
            if existing:
                existing.display_name = record.display_name
                existing.department = record.department
                existing.job_title = record.job_title
                existing.is_active = record.is_active
                existing.notes = record.notes
                existing.imported_at = datetime.utcnow()
                existing.imported_by = imported_by
            else:
                user = TruthListUser(
                    user_principal=record.user_principal,
                    display_name=record.display_name,
                    department=record.department,
                    job_title=record.job_title,
                    is_active=record.is_active,
                    notes=record.notes,
                    imported_by=imported_by
                )
                db.add(user)
                added += 1
                
        db.commit()
        return added
    
    @staticmethod
    def ingest_audit_logs(db: Session, records: list) -> Tuple[int, int, int]:
        """Ingère les Audit Logs M365"""
        from app.models.audit_logs_m365 import M365AuditLog
        
        logger.info(f"=== INGEST_AUDIT_LOGS START: {len(records)} records ===")
        
        added = 0
        duplicates = 0
        errors = 0
        
        for idx, record in enumerate(records):
            try:
                audit_id = record.audit_id or record.id
                logger.info(f"Record {idx}: audit_id={audit_id}")
                
                if not audit_id:
                    logger.error(f"Record {idx}: No audit_id, skipping")
                    errors += 1
                    continue
                
                existing = db.query(M365AuditLog).filter(M365AuditLog.audit_id == audit_id).first()
                if existing:
                    logger.info(f"Record {idx}: Duplicate found, skipping")
                    duplicates += 1
                    continue
                
                log = M365AuditLog(
                    audit_id=audit_id,
                    timestamp=record.timestamp,
                    record_type=record.record_type,
                    category=record.category,
                    operation=record.operation,
                    result=record.result,
                    result_reason=record.result_reason,
                    user_id=record.user_id,
                    user_principal=record.user_principal,
                    user_type=record.user_type,
                    ip_address=record.ip_address,
                    client_ip=record.client_ip,
                    client_info=record.client_info,
                    city=record.city,
                    country_or_region=record.country_or_region,
                    workload=record.workload,
                    target_id=record.target_id,
                    target_type=record.target_type,
                    target_display_name=record.target_display_name,
                    target_resource=record.target_resource,
                    user_agent=record.user_agent,
                    initiated_by=record.initiated_by,
                    correlation_id=record.correlation_id,
                    raw_json=record.raw_json
                )
                db.add(log)
                added += 1
                logger.info(f"Record {idx}: Added! audit_id={audit_id}")
            except Exception as e:
                logger.error(f"Record {idx}: ERROR {e}")
                logger.error(traceback.format_exc())
                errors += 1
        
        db.commit()
        logger.info(f"=== INGEST_AUDIT_LOGS DONE: added={added}, dup={duplicates}, err={errors} ===")
        return added, duplicates, errors
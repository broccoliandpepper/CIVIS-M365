"""
Endpoints d'ingestion
"""

import csv
import io
import json
import logging
import traceback
from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db_hot, get_db_config
from app.services.ingestion_service import IngestionService
from app.services.alert_service import AlertService
from app.services.audit_service import AuditService
from app.schemas.ingestion import (
    SignInRecord, RiskyUserRecord, IncidentRecord, 
    TruthListRecord, AuditRecord, IngestionResponse
)
from app.api.auth import get_current_user
from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


def parse_truth_list_csv(content: bytes) -> list[TruthListRecord]:
    content_str = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content_str))
    records: list[TruthListRecord] = []

    for row in reader:
        if not any(value and value.strip() for value in row.values() if value is not None):
            continue

        normalized = {key.strip().lower(): (value.strip() if value is not None else '') for key, value in row.items()}
        user_principal = normalized.get('userprincipalname') or normalized.get('user_principal')
        if not user_principal:
            continue

        display_name = normalized.get('displayname') or normalized.get('display_name')
        department = normalized.get('department')
        job_title = normalized.get('jobtitle') or normalized.get('job_title')
        company_name = normalized.get('companyname')
        country = normalized.get('country')
        created_date = normalized.get('createddatetime')
        sign_in_activity = normalized.get('signinactivity')

        notes = []
        if company_name:
            notes.append(f"company={company_name}")
        if country:
            notes.append(f"country={country}")
        if created_date:
            notes.append(f"created={created_date}")
        if sign_in_activity:
            notes.append(f"signInActivity={sign_in_activity}")

        records.append(TruthListRecord(
            user_principal=user_principal,
            display_name=display_name or None,
            department=department or None,
            job_title=job_title or None,
            is_active=True,
            notes='; '.join(notes) if notes else None
        ))

    return records


def parse_incidents_csv(content: bytes) -> list[IncidentRecord]:
    content_str = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content_str))
    records: list[IncidentRecord] = []

    for row in reader:
        if not any(value and value.strip() for value in row.values() if value is not None):
            continue

        normalized = {key.strip().lower(): (value.strip() if value is not None else '') for key, value in row.items()}
        incident_id = normalized.get('incident id') or normalized.get('incident_id')
        title = normalized.get('incident name') or normalized.get('title')
        severity = normalized.get('severity') or normalized.get('priority score') or 'unknown'
        status_raw = normalized.get('status') or normalized.get('investigation state') or 'unknown'
        assigned_to = normalized.get('assigned to') or normalized.get('assigned_to')
        category = normalized.get('categories') or normalized.get('category')
        priority_score = normalized.get('priority score')
        tags = normalized.get('tags')
        investigation_state = normalized.get('investigation state')
        impacted_assets = normalized.get('impacted assets')
        active_alerts = normalized.get('active alerts')
        service_sources = normalized.get('service sources')
        detection_sources = normalized.get('detection sources')
        last_update_time = normalized.get('last update time')
        last_activity = normalized.get('last activity')
        policy_name = normalized.get('policy name')
        data_sensitivity = normalized.get('data sensitivity')
        classification = normalized.get('classification')
        determination = normalized.get('determination')
        device_groups = normalized.get('device groups')
        creation_time = normalized.get('creation time')
        workspaces = normalized.get('workspaces')
        cloud_scopes = normalized.get('cloud scopes')
        if not incident_id or not title:
            continue

        severity = severity.strip().lower() if severity else 'unknown'
        status = status_raw.strip().lower() if status_raw else 'unknown'
        if status in ('in progress', 'inprogress', 'investigating', 'under investigation'):
            status = 'active'
        elif status in ('resolved', 'closed', 'dismissed'):
            status = 'closed'
        elif status == 'new':
            status = 'new'
        elif status == 'active':
            status = 'active'
        else:
            status = status.replace(' ', '_') if status else 'unknown'

        timestamp_str = normalized.get('last update time') or normalized.get('creation time') or normalized.get('creationtime')

        description_parts = []
        for field_name in [
            'tags', 'impacted assets', 'active alerts', 'service sources',
            'detection sources', 'last activity', 'policy name', 'data sensitivity',
            'classification', 'determination', 'device groups', 'workspaces', 'cloud scopes'
        ]:
            value = normalized.get(field_name)
            if value:
                description_parts.append(f"{field_name}: {value}")

        description = '\n'.join(description_parts) if description_parts else None
        raw_json = json.dumps({k: v for k, v in row.items() if v is not None})

        from datetime import datetime
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception:
                timestamp = None

        if timestamp is None:
            timestamp = datetime.utcnow()

        records.append(IncidentRecord(
            incident_id=incident_id,
            timestamp=timestamp,
            title=title,
            severity=severity,
            status=status,
            assigned_to=assigned_to or None,
            category=category or None,
            priority_score=priority_score or None,
            tags=tags or None,
            investigation_state=investigation_state or None,
            impacted_assets=impacted_assets or None,
            active_alerts=active_alerts or None,
            service_sources=service_sources or None,
            detection_sources=detection_sources or None,
            last_update_time=last_update_time or None,
            last_activity=last_activity or None,
            policy_name=policy_name or None,
            data_sensitivity=data_sensitivity or None,
            classification=classification or None,
            determination=determination or None,
            device_groups=device_groups or None,
            creation_time=creation_time or None,
            workspaces=workspaces or None,
            cloud_scopes=cloud_scopes or None,
            description=description,
            raw_json=raw_json
        ))

    return records


@router.post("/upload/signins", response_model=IngestionResponse)
async def upload_signins(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Upload de fichier SignIns (JSON)"""
    content = await file.read()
    
    # Validate file is not empty
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    file_hash = IngestionService.calculate_file_hash(content)
    file_size = len(content)
    
    ingestion_log = IngestionService.create_ingestion_log(
        db=db_config,
        filename=file.filename,
        file_hash=file_hash,
        file_size=file_size,
        source_type="signins",
        uploaded_by=current_user.username
    )
    
    try:
        data = json.loads(content.decode('utf-8'))
        
        # Handle both formats: [array] or {records: [array]}
        if isinstance(data, list):
            records = data
        else:
            records = data.get('records', [])
        
        logger.info(f"Loaded {len(records)} signin records from file")
        
        # Parse M365 JSON to match SignInRecord schema
        parsed_records = []
        for idx, r in enumerate(records):
            try:
                location = r.get('location', {})
                device = r.get('deviceDetail', {})
                status_obj = r.get('status', {})
                
                parsed = {
                    'event_id': r.get('id'),
                    'timestamp': r.get('createdDateTime'),
                    'user_principal': r.get('userPrincipalName'),
                    'display_name': r.get('userDisplayName'),
                    'user_id': r.get('userId'),
                    'user_type': r.get('userType'),
                    'ip_address': r.get('ipAddress'),
                    'location_city': location.get('city'),
                    'location_country': location.get('countryOrRegion'),
                    'location_state': location.get('state'),
                    'status': 'success' if status_obj.get('errorCode') == 0 else 'failure',
                    'failure_reason': status_obj.get('failureReason'),
                    'error_code': str(status_obj.get('errorCode')),
                    'correlation_id': r.get('correlationId'),
                    'conditional_access_status': r.get('conditionalAccessStatus'),
                    'mfa_status': json.dumps(r.get('mfaDetail')) if isinstance(r.get('mfaDetail'), dict) else r.get('mfaDetail'),
                    'auth_method': r.get('authenticationMethodsUsed', [None])[0] if r.get('authenticationMethodsUsed') else None,
                    'auth_requirement': r.get('authenticationRequirement'),
                    'app_name': r.get('appDisplayName'),
                    'app_id': r.get('appId'),
                    'client_app': r.get('clientAppUsed'),
                    'device_os': device.get('operatingSystem'),
                    'device_browser': device.get('browser'),
                    'device_is_compliant': str(device.get('isCompliant')),
                    'device_is_managed': str(device.get('isManaged')),
                    'risk_detail': r.get('riskDetail'),
                    'risk_state': r.get('riskState'),
                    'risk_level': r.get('riskLevelAggregated'),
                    'flagged_for_review': str(r.get('flaggedForReview')),
                    'raw_json': json.dumps(r)
                }
                parsed_records.append(parsed)
            except Exception as e:
                logger.error(f"Error parsing signin record {idx}: {e}")
                logger.error(traceback.format_exc())
        
        logger.info(f"Parsed {len(parsed_records)} signin records successfully")
        
        added, duplicates, errors = IngestionService.ingest_signins(
            db=db,
            records=parsed_records,
            ingestion_log_id=ingestion_log.id
        )
        
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=errors,
            status="completed"
        )
        
        AuditService.log_action(
            db=db_config,
            username=current_user.username,
            action="FILE_UPLOAD",
            status="SUCCESS",
            resource_type="SIGNINS",
            resource_id=str(ingestion_log.id),
            details={"filename": file.filename, "added": added, "duplicates": duplicates}
        )
        
        return IngestionResponse(
            status="completed",
            filename=file.filename,
            source_type="signins",
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=errors,
            ingestion_log_id=ingestion_log.id,
            message=f"Successfully ingested {added} records ({duplicates} duplicates)"
        )
    except Exception as e:
        logger.error(f"SignIn ingest error: {e}")
        logger.error(traceback.format_exc())
        
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=0,
            lines_added=0,
            lines_duplicate=0,
            lines_error=0,
            status="failed",
            error_message=str(e)
        )
        
        return IngestionResponse(
            status="failed",
            filename=file.filename,
            source_type="signins",
            lines_total=0,
            lines_added=0,
            lines_duplicate=0,
            lines_error=0,
            ingestion_log_id=ingestion_log.id,
            message=f"Error during ingestion: {str(e)}"
        )


@router.post("/upload/risky-users", response_model=IngestionResponse)
async def upload_risky_users(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Upload de fichier Risky Users (JSON)"""
    content = await file.read()
    
    # Validate file is not empty
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    file_hash = IngestionService.calculate_file_hash(content)
    
    ingestion_log = IngestionService.create_ingestion_log(
        db=db_config,
        filename=file.filename,
        file_hash=file_hash,
        file_size=len(content),
        source_type="risky_users",
        uploaded_by=current_user.username
    )
    
    try:
        data = json.loads(content.decode('utf-8'))
        
        # Handle both formats: [array] or {records: [array]}
        if isinstance(data, list):
            records_list = data
        else:
            records_list = data.get('records', [])
        
        logger.info(f"Loaded {len(records_list)} risky user records from file")
        
        records = []
        for idx, r in enumerate(records_list):
            try:
                from datetime import datetime
                
                # Parse timestamp from riskLastUpdatedDateTime
                ts_str = r.get('riskLastUpdatedDateTime') or r.get('timestamp')
                ts_value = None
                if ts_str:
                    ts_cleaned = ts_str.replace('Z', '').replace('+00:00', '')
                    try:
                        if '.' in ts_cleaned:
                            ts_value = datetime.fromisoformat(ts_cleaned)
                        else:
                            ts_value = datetime.fromisoformat(ts_cleaned)
                    except Exception:
                        ts_value = datetime.utcnow()
                else:
                    ts_value = datetime.utcnow()
                
                record = RiskyUserRecord(
                    event_id=r.get('id'),
                    timestamp=ts_value,
                    user_principal=r.get('userPrincipalName'),
                    user_id=r.get('id'),
                    user_display_name=r.get('userDisplayName'),
                    risk_level=r.get('riskLevel'),
                    risk_state=r.get('riskState'),
                    risk_detail=r.get('riskDetail'),
                    risk_last_updated=ts_value,
                    is_deleted=str(r.get('isDeleted')),
                    is_processing=str(r.get('isProcessing')),
                    raw_json=json.dumps(r)
                )
                records.append(record)
            except Exception as e:
                logger.error(f"Error parsing risky user record {idx}: {e}")
                logger.error(traceback.format_exc())
        
        logger.info(f"Parsed {len(records)} risky user records successfully")
        
        added, duplicates, errors = IngestionService.ingest_risky_users(
            db=db,
            records=records
        )
        
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=errors,
            status="completed"
        )
        
        return IngestionResponse(
            status="completed",
            filename=file.filename,
            source_type="risky_users",
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=errors,
            ingestion_log_id=ingestion_log.id,
            message=f"Successfully ingested {added} records"
        )
    except Exception as e:
        logger.error(f"Error during risky users ingestion: {e}")
        logger.error(traceback.format_exc())
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=0,
            lines_added=0,
            lines_duplicate=0,
            lines_error=0,
            status="failed",
            error_message=str(e)
        )
        return IngestionResponse(
            status="failed",
            filename=file.filename,
            source_type="risky_users",
            lines_total=0,
            lines_added=0,
            lines_duplicate=0,
            lines_error=0,
            ingestion_log_id=ingestion_log.id,
            message=f"Error during ingestion: {str(e)}"
        )


@router.post("/upload/incidents", response_model=IngestionResponse)
async def upload_incidents(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Upload de fichier Incidents (JSON ou CSV)"""
    content = await file.read()
    
    # Validate file is not empty
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    file_hash = IngestionService.calculate_file_hash(content)
    
    ingestion_log = IngestionService.create_ingestion_log(
        db=db_config,
        filename=file.filename,
        file_hash=file_hash,
        file_size=len(content),
        source_type="incidents",
        uploaded_by=current_user.username
    )
    
    try:
        records: list[IncidentRecord] = []
        content_str = content.decode('utf-8-sig')

        try:
            data = json.loads(content_str)
            raw_records = []
            if isinstance(data, dict):
                raw_records = data.get('records', [])
            elif isinstance(data, list):
                raw_records = data

            if raw_records:
                records = [IncidentRecord(**r, raw_json=json.dumps(r)) for r in raw_records]
            else:
                raise ValueError("No records found in JSON incidents file")
        except json.JSONDecodeError:
            records = parse_incidents_csv(content)

        if not records:
            raise ValueError("No incident records parsed from file")
        
        added, duplicates, errors = IngestionService.ingest_incidents(
            db=db,
            records=records
        )
        
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=errors,
            status="completed"
        )
        
        return IngestionResponse(
            status="completed",
            filename=file.filename,
            source_type="incidents",
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=errors,
            ingestion_log_id=ingestion_log.id,
            message=f"Successfully ingested {added} records"
        )
    except Exception as e:
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=0,
            lines_added=0,
            lines_duplicate=0,
            lines_error=0,
            status="failed",
            error_message=str(e)
        )
        raise


@router.post("/upload/truth-list", response_model=IngestionResponse)
async def upload_truth_list(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Upload de fichier Truth List (JSON ou CSV exportUsers)"""
    content = await file.read()
    
    # Validate file is not empty
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    file_hash = IngestionService.calculate_file_hash(content)
    
    ingestion_log = IngestionService.create_ingestion_log(
        db=db_config,
        filename=file.filename,
        file_hash=file_hash,
        file_size=len(content),
        source_type="truth_list",
        uploaded_by=current_user.username
    )
    
    try:
        records: list[TruthListRecord] = []
        content_str = content.decode('utf-8-sig')

        try:
            data = json.loads(content_str)
            raw_records = []
            if isinstance(data, dict):
                raw_records = data.get('records', [])
            elif isinstance(data, list):
                raw_records = data

            if raw_records:
                records = [TruthListRecord(**r) for r in raw_records]
            else:
                raise ValueError("No records found in JSON truth list file")
        except json.JSONDecodeError:
            records = parse_truth_list_csv(content)

        if not records:
            raise ValueError("No truth list records parsed from file")
        
        added = IngestionService.ingest_truth_list(
            db=db,
            records=records,
            imported_by=current_user.username
        )
        
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=len(records) - added,
            lines_error=0,
            status="completed"
        )
        
        return IngestionResponse(
            status="completed",
            filename=file.filename,
            source_type="truth_list",
            lines_total=len(records),
            lines_added=added,
            lines_duplicate=len(records) - added,
            lines_error=0,
            ingestion_log_id=ingestion_log.id,
            message=f"Successfully imported {added} users"
        )
    except Exception as e:
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=0,
            lines_added=0,
            lines_duplicate=0,
            lines_error=0,
            status="failed",
            error_message=str(e)
        )
        raise
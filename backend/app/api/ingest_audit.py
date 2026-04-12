"""
Endpoints d'ingestion pour Audit Logs
"""

import json
import logging
import traceback
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db_hot, get_db_config
from app.services.ingestion_service import IngestionService
from app.schemas.ingestion import AuditRecord, IngestionResponse
from app.api.auth import get_current_user
from app.models.auth import User

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


@router.post("/upload/audit-logs", response_model=IngestionResponse)
async def upload_audit_logs(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Upload de fichier Audit Logs M365 (JSON)"""
    with open('debug_direct.txt', 'a') as f:
        f.write(f"=== START upload_audit_logs ===\n")
    
    content = await file.read()
    with open('debug_direct.txt', 'a') as f:
        f.write(f"File: {file.filename} size={len(content)}\n")
    file_hash = IngestionService.calculate_file_hash(content)
    
    ingestion_log = IngestionService.create_ingestion_log(
        db=db_config,
        filename=file.filename,
        file_hash=file_hash,
        file_size=len(content),
        source_type="audit_logs_m365",
        uploaded_by=current_user.username
    )
    
    try:
        content_str = content.decode('utf-8')
        logger.info(f"Content length: {len(content_str)}")
        
        # Check if empty
        if not content_str.strip():
            raise HTTPException(status_code=400, detail="Empty file")
        
        data = json.loads(content_str)
        logger.info(f"Data type: {type(data)}")
        logger.info(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        # Support both formats: {"records": [...]} or [...]
        if isinstance(data, dict):
            records_list = data.get('records', data.get('AuditLogs', []))
            if not records_list:
                # Find first list value
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0:
                        records_list = v
                        logger.info(f"Using list from key: {k}")
                        break
        elif isinstance(data, list):
            records_list = data
            logger.info(f"Direct list found with {len(records_list)} items")
        else:
            records_list = []
        
        logger.info(f"Found {len(records_list)} records to process")
        
        if len(records_list) == 0:
            logger.error("ERROR: No records found in file!")
            raise HTTPException(status_code=400, detail="No records found in file")
        
        records = []
        parse_errors = 0
        
        # Parse each record into AuditRecord
        for idx, r in enumerate(records_list):
            logger.debug(f"Processing record {idx}: id={r.get('id')}, category={r.get('category')}")
            try:
                raw_json_str = json.dumps(r)
                
                # Handle M365 format - activityDateTime is the correct field
                timestamp_str = r.get('activityDateTime') or r.get('timestamp')
                timestamp = None
                if timestamp_str:
                    ts = timestamp_str.replace('+00:00', 'Z').replace('Z', '')
                    if '.' in ts:
                        ts = ts.split('.')[0] + '.000000'
                    from datetime import datetime
                    try:
                        timestamp = datetime.fromisoformat(ts)
                    except:
                        try:
                            timestamp = datetime.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S')
                        except:
                            pass
                
                if not timestamp:
                    timestamp = datetime.utcnow()
                
                # Handle initiatedBy - can be app or user
                initiated_by = r.get('initiatedBy', {})
                user_id = None
                user_principal = None
                user_type = None
                if isinstance(initiated_by, dict):
                    if initiated_by.get('user'):
                        user = initiated_by.get('user', {})
                        user_id = user.get('userPrincipalName') or user.get('displayName')
                        user_principal = user.get('userPrincipalName')
                        user_type = 'user'
                    elif initiated_by.get('app'):
                        app_data = initiated_by.get('app', {})
                        user_id = app_data.get('displayName')
                        user_type = 'app'
                    else:
                        user_id = 'System'
                else:
                    user_id = 'System'

                # Handle target resources
                target_res = r.get('targetResources', [{}])[0] if r.get('targetResources') else {}
                target_id = target_res.get('id')
                target_type = target_res.get('type')
                target_name = target_res.get('displayName') or target_res.get('userPrincipalName')
                target_resource = target_res.get('displayName') or target_res.get('id')

                # Handle additionalDetails - array of key/value objects
                additional_details = r.get('additionalDetails', [])
                result_reason = r.get('resultReason', '')
                if additional_details and isinstance(additional_details, list):
                    for detail in additional_details:
                        if isinstance(detail, dict) and detail.get('key') == 'Result':
                            result_reason = detail.get('value', '')
                            break

                record = AuditRecord(
                    id=r.get('id'),
                    audit_id=r.get('id'),
                    timestamp=timestamp,
                    record_type=r.get('recordType'),
                    category=r.get('category'),
                    operation=r.get('activityDisplayName') or r.get('operation') or 'Unknown',
                    result=r.get('result') or r.get('resultStatus'),
                    result_reason=result_reason,
                    user_id=user_id,
                    user_principal=user_principal,
                    user_type=user_type,
                    ip_address=r.get('ipAddress'),
                    client_ip=r.get('ipAddress'),
                    client_info=r.get('userAgent'),
                    city=r.get('city'),
                    country_or_region=r.get('countryOrRegion') or r.get('country_or_region'),
                    workload=r.get('loggedByService') or r.get('workload'),
                    target_id=target_id,
                    target_type=target_type,
                    target_display_name=target_name,
                    target_resource=target_resource,
                    user_agent=r.get('userAgent'),
                    initiated_by=json.dumps(initiated_by) if initiated_by else None,
                    correlation_id=r.get('correlationId'),
                    raw_json=raw_json_str
                )
                records.append(record)
            except Exception as e:
                logger.error(f"Error parsing record {idx}: {e}")
                logger.error(traceback.format_exc())
                parse_errors += 1
        
        logger.info(f"Parsed {len(records)} records, {parse_errors} parse errors")
        if records:
            logger.info(f"First record: id={records[0].id}, audit_id={records[0].audit_id}, timestamp={records[0].timestamp}")
        
        if len(records) == 0:
            logger.error("ERROR: No records parsed successfully!")
            raise HTTPException(status_code=400, detail="No records parsed")
        
        added, duplicates, errs = IngestionService.ingest_audit_logs(
            db=db,
            records=records
        )
        
        logger.info(f"Ingestion result: added={added}, duplicates={duplicates}, errs={errs}")
        
        total = len(records)
        IngestionService.update_ingestion_log(
            db=db_config,
            log_id=ingestion_log.id,
            lines_total=total,
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=parse_errors + errs,
            status="completed"
        )

        return IngestionResponse(
            status="completed",
            filename=file.filename,
            source_type="audit_logs_m365",
            lines_total=total,
            lines_added=added,
            lines_duplicate=duplicates,
            lines_error=parse_errors + errs,
            ingestion_log_id=ingestion_log.id,
            message=f"Successfully imported {added} audit logs"
        )
    except Exception as e:
        logger.error(f"ERROR: {e}")
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
        raise
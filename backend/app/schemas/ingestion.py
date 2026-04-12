"""
Schemas pour l'ingestion
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SignInRecord(BaseModel):
    event_id: str
    timestamp: datetime
    user_principal: str
    display_name: Optional[str] = None
    user_id: Optional[str] = None
    user_type: Optional[str] = None
    ip_address: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    location_state: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None
    conditional_access_status: Optional[str] = None
    mfa_status: Optional[str] = None
    auth_method: Optional[str] = None
    auth_requirement: Optional[str] = None
    app_name: Optional[str] = None
    app_id: Optional[str] = None
    client_app: Optional[str] = None
    device_os: Optional[str] = None
    device_browser: Optional[str] = None
    device_is_compliant: Optional[str] = None
    device_is_managed: Optional[str] = None
    risk_detail: Optional[str] = None
    risk_state: Optional[str] = None
    risk_level: Optional[str] = None
    flagged_for_review: Optional[str] = None
    raw_json: str = ""


class RiskyUserRecord(BaseModel):
    event_id: str
    timestamp: datetime
    user_principal: str
    user_id: Optional[str] = None
    user_display_name: Optional[str] = None
    risk_level: str
    risk_state: Optional[str] = None
    risk_detail: Optional[str] = None
    risk_last_updated: Optional[datetime] = None
    is_deleted: Optional[str] = None
    is_processing: Optional[str] = None
    detection_type: Optional[str] = None
    detection_timing: Optional[str] = None
    raw_json: str = ""


class IncidentRecord(BaseModel):
    incident_id: str
    timestamp: datetime
    title: str
    severity: str
    status: str
    assigned_to: Optional[str] = None
    category: Optional[str] = None
    priority_score: Optional[str] = None
    tags: Optional[str] = None
    investigation_state: Optional[str] = None
    impacted_assets: Optional[str] = None
    active_alerts: Optional[str] = None
    service_sources: Optional[str] = None
    detection_sources: Optional[str] = None
    last_update_time: Optional[str] = None
    last_activity: Optional[str] = None
    policy_name: Optional[str] = None
    data_sensitivity: Optional[str] = None
    classification: Optional[str] = None
    determination: Optional[str] = None
    device_groups: Optional[str] = None
    creation_time: Optional[str] = None
    workspaces: Optional[str] = None
    cloud_scopes: Optional[str] = None
    description: Optional[str] = None
    raw_json: str = ""


class TruthListRecord(BaseModel):
    user_principal: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None


class AuditRecord(BaseModel):
    id: Optional[str] = None
    audit_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    record_type: Optional[str] = None
    category: Optional[str] = None
    operation: Optional[str] = None
    result: Optional[str] = None
    result_reason: Optional[str] = None
    user_id: Optional[str] = None
    user_principal: Optional[str] = None
    user_type: Optional[str] = None
    ip_address: Optional[str] = None
    client_ip: Optional[str] = None
    client_info: Optional[str] = None
    city: Optional[str] = None
    country_or_region: Optional[str] = None
    workload: Optional[str] = None
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    target_display_name: Optional[str] = None
    target_resource: Optional[str] = None
    user_agent: Optional[str] = None
    initiated_by: Optional[str] = None
    correlation_id: Optional[str] = None
    raw_json: str = ""


class IngestionResponse(BaseModel):
    status: str
    filename: str
    source_type: str
    lines_total: int
    lines_added: int
    lines_duplicate: int
    lines_error: int
    ingestion_log_id: int
    message: str
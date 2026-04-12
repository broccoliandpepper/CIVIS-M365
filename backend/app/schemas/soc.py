"""
Schemas pour les réponses SOC
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SOCAnomalyResponse(BaseModel):
    id: int
    anomaly_id: str
    timestamp: Optional[str]
    user_principal: str
    user_display_name: Optional[str]
    user_id: Optional[str]
    event_type: str
    severity: str
    ip_address: Optional[str]
    country: Optional[str]
    city: Optional[str]
    app_name: Optional[str]
    reason: Optional[str]
    related_signin_id: Optional[str]
    related_incident_id: Optional[str]
    related_risky_user_id: Optional[str]
    status: str
    notes: Optional[str]


class SOCMetricResponse(BaseModel):
    metric_date: str
    total_signins: int
    failed_signins: int
    out_of_list_signins: int
    risk_user_signins: int
    concurrent_ip_events: int
    failed_auth_spikes: int
    unique_users: int
    unique_countries: int
    out_of_list_countries: int
    critical_anomalies: int
    high_anomalies: int
    medium_anomalies: int
    low_anomalies: int
    related_incidents: int


class SOCExecutiveSummary(BaseModel):
    period: str  # "today", "last_7_days", "last_30_days", "custom"
    start_date: str
    end_date: str
    
    total_anomalies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    total_signins: int
    failed_signins: int
    failed_rate: float  # percentage
    
    out_of_list_signins: int
    out_of_list_countries: List[str]  # unique countries outside allowed list
    
    risk_users_signins: int
    affected_risk_users: List[str]
    
    failed_auth_spikes: int
    concurrent_ip_events: int
    related_incidents: int
    
    top_countries: dict  # {country_code: count}
    top_users: dict  # {user_principal: count}


class SOCAnalysisRequest(BaseModel):
    period: str = "today"  # "today", "last_7_days", "last_30_days", "custom"
    start_date: Optional[str] = None  # YYYY-MM-DD for custom
    end_date: Optional[str] = None  # YYYY-MM-DD for custom


class SOCUserProfile(BaseModel):
    user_principal: str
    user_display_name: Optional[str]
    user_id: Optional[str]
    
    total_signins: int
    failed_signins: int
    failed_rate: float
    
    countries_accessed: List[str]
    out_of_list_countries: List[str]
    
    apps_accessed: List[str]
    last_signin: Optional[str]
    
    risk_status: Optional[str]  # from RiskyUsers
    risk_level: Optional[str]
    
    anomalies_count: int
    anomalies: List[SOCAnomalyResponse]
    
    related_incidents: List[dict]  # [{"id": "...", "severity": "..."}]


class SOCExportRequest(BaseModel):
    period: str = "today"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    include_details: bool = True
    anomalies_only: bool = False

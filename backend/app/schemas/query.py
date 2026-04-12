"""
Schemas pour les requêtes et pagination
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, le=1000)
    page_size: int = Field(default=50, ge=1, le=500)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SignInsFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_principal: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    mfa_status: Optional[str] = None
    app_name: Optional[str] = None
    location_country: Optional[str] = None
    page: int = 1
    page_size: int = 50


class RiskyUsersFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_principal: Optional[str] = None
    risk_level: Optional[str] = None
    risk_state: Optional[str] = None
    detection_type: Optional[str] = None
    page: int = 1
    page_size: int = 50


class IncidentsFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    title_contains: Optional[str] = None
    assigned_to: Optional[str] = None
    page: int = 1
    page_size: int = 50


class AuditLogsFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_principal: Optional[str] = None
    operation: Optional[str] = None
    workload: Optional[str] = None
    target_resource: Optional[str] = None
    result_status: Optional[str] = None
    is_critical: bool = False
    page: int = 1
    page_size: int = 50
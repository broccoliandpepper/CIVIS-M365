"""
Schemas pour Dashboard Direction
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class KpiCard(BaseModel):
    title: str
    value: float = 0.0
    unit: str = ""
    trend: Optional[str] = None
    trend_percentage: Optional[float] = None
    color: str = "blue"
    icon: str = "chart-bar"
    tooltip: Optional[str] = None


class DashboardKpiResponse(BaseModel):
    generated_at: datetime
    period_days: int
    kpis: Dict[str, KpiCard]
    role_view: str = "director"


class TrendPoint(BaseModel):
    date: str
    value: int
    label: Optional[str] = None


class TrendChart(BaseModel):
    title: str
    type: str = "line"
    data: List[TrendPoint]
    unit: str = ""
    color: str = "#3B82F6"


class DashboardTrendsResponse(BaseModel):
    charts: List[TrendChart]
    period_days: int


class PdfExportRequest(BaseModel):
    period_days: int = Field(default=30, ge=1, le=365)
    include_details: bool = True
    include_charts: bool = True
    kpis_only: bool = False


class CsvExportRequest(BaseModel):
    source_type: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None


class SecuritySummary(BaseModel):
    overall_status: str  # "good", "warning", "critical"
    score: int  # 0-100
    last_incident_days: Optional[int] = None
    activeThreats: int = 0
    pendingAlerts: int = 0
    usersAtRisk: int = 0


class DirectorDashboardResponse(BaseModel):
    kpis: DashboardKpiResponse
    trends: DashboardTrendsResponse
    security_summary: SecuritySummary
    exported_at: datetime
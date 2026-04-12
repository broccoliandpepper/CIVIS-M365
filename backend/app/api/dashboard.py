"""
Endpoints Dashboard Direction
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db_hot
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardKpiResponse, DashboardTrendsResponse, 
    SecuritySummary, DirectorDashboardResponse
)
from app.models.auth import User
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=DashboardKpiResponse)
async def get_director_kpis(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """KPIs du Dashboard Direction"""
    return DashboardService.get_director_kpis(db, days)


@router.get("/trends", response_model=DashboardTrendsResponse)
async def get_trends(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Tendances du Dashboard"""
    return DashboardService.get_trends(db, days)


@router.get("/security-summary", response_model=SecuritySummary)
async def get_security_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Résumé de sécurité"""
    return DashboardService.get_security_summary(db)


@router.get("/director", response_model=DirectorDashboardResponse)
async def get_director_dashboard(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Dashboard complet Direction"""
    kpis = DashboardService.get_director_kpis(db, days)
    trends = DashboardService.get_trends(db, days)
    security = DashboardService.get_security_summary(db)
    
    return DirectorDashboardResponse(
        kpis=kpis,
        trends=trends,
        security_summary=security,
        exported_at=datetime.utcnow()
    )


@router.get("/director-pdf")
async def export_director_pdf(
    days: int = Query(30, ge=1, le=365),
    include_details: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Export PDF du Dashboard Direction"""
    kpis = DashboardService.get_director_kpis(db, days)
    trends = DashboardService.get_trends(db, days)
    security = DashboardService.get_security_summary(db)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIEM M365 - Rapport Direction</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1e3a8a; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
            .kpi-card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; }}
            .kpi-value {{ font-size: 32px; font-weight: bold; color: #1e3a8a; }}
            .kpi-title {{ color: #6b7280; font-size: 14px; }}
            .generated {{ color: #6b7280; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <h1>Rapport SIEM M365 - Direction</h1>
        <p>Periode: {days} derniers jours</p>
        <p>Score de securite: {security.score}/100 ({security.overall_status})</p>
        
        <h2>Indicateurs Cles</h2>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">{kpis.kpis['total_connexions'].title}</div>
                <div class="kpi-value">{kpis.kpis['total_connexions'].value}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">{kpis.kpis['success_rate'].title}</div>
                <div class="kpi-value">{kpis.kpis['success_rate'].value}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">{kpis.kpis['risky_users'].title}</div>
                <div class="kpi-value">{kpis.kpis['risky_users'].value}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">{kpis.kpis['open_incidents'].title}</div>
                <div class="kpi-value">{kpis.kpis['open_incidents'].value}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">{kpis.kpis['critical_ops'].title}</div>
                <div class="kpi-value">{kpis.kpis['critical_ops'].value}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">{kpis.kpis['unique_users'].title}</div>
                <div class="kpi-value">{kpis.kpis['unique_users'].value}</div>
            </div>
        </div>
        
        <div class="generated">Genere le: {datetime.utcnow().isoformat()}</div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
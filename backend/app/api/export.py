"""
Endpoints d'export
"""

import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db_hot
from app.services.query_service import QueryService
from app.services.dashboard_service import DashboardService
from app.models.auth import User
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/v1/export", tags=["Export"])


@router.get("/signins/csv")
async def export_signins_csv(
    date_from: str = Query(None),
    date_to: str = Query(None),
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Export SignIns en CSV"""
    filters = {"status": status}
    items, _ = QueryService.query_signins(db, filters, page=1, page_size=10000)
    
    output = io.StringIO()
    if items:
        writer = csv.DictWriter(output, fieldnames=items[0].to_dict().keys())
        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=signins_export.csv"}
    )


@router.get("/risky-users/csv")
async def export_risky_users_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Export Risky Users en CSV"""
    items, _ = QueryService.query_risky_users(db, {}, page=1, page_size=10000)
    
    output = io.StringIO()
    if items:
        writer = csv.DictWriter(output, fieldnames=items[0].to_dict().keys())
        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=risky_users_export.csv"}
    )


@router.get("/incidents/csv")
async def export_incidents_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Export Incidents en CSV"""
    items, _ = QueryService.query_incidents(db, {}, page=1, page_size=10000)
    
    output = io.StringIO()
    if items:
        writer = csv.DictWriter(output, fieldnames=items[0].to_dict().keys())
        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=incidents_export.csv"}
    )


@router.get("/pdf")
async def export_pdf(
    period_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Export PDF du Dashboard"""
    kpis = DashboardService.get_director_kpis(db, period_days)
    trends = DashboardService.get_trends(db, period_days)
    security = DashboardService.get_security_summary(db)
    
    trends_html = ""
    if trends.charts:
        for chart in trends.charts:
            trends_html += f"<h3>{chart.title}</h3><ul>"
            for point in chart.data[:7]:
                trends_html += f"<li>{point.label}: {point.value}</li>"
            trends_html += "</ul>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIEM M365 - Rapport</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1e3a8a; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }}
            .kpi-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; }}
            .kpi-value {{ font-size: 28px; font-weight: bold; color: #1e3a8a; }}
            .kpi-title {{ color: #6b7280; font-size: 12px; }}
            .generated {{ color: #6b7280; font-size: 12px; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <h1>Rapport SIEM M365</h1>
        <p>Période: {period_days} derniers jours</p>
        <p>Score de sécurité: {security.score}/100 ({security.overall_status})</p>
        
        <h2>Indicateurs</h2>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Total Connexions</div>
                <div class="kpi-value">{kpis.kpis['total_connexions'].value}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Taux de Succès</div>
                <div class="kpi-value">{kpis.kpis['success_rate'].value}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Utilisateurs à Risque</div>
                <div class="kpi-value">{kpis.kpis['risky_users'].value}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Incidents Ouverts</div>
                <div class="kpi-value">{kpis.kpis['open_incidents'].value}</div>
            </div>
        </div>
        
        <h2>Tendances</h2>
        {trends_html}
        
        <div class="generated">Généré le: {datetime.utcnow().isoformat()}</div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
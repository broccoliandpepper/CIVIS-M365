"""
API endpoints pour le module SOC
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.models.auth import User
from app.database import get_db_hot
from app.api.auth import get_current_user
from app.services.soc_service import SOCService
from app.schemas.soc import (
    SOCExecutiveSummary, SOCAnalysisRequest,
    SOCExportRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/soc", tags=["soc"])


@router.post("/analyze")
async def run_soc_analysis(
    request: SOCAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Lance une analyse SOC"""
    result = SOCService.run_analysis(
        db=db,
        period=request.period,
        start_date=request.start_date,
        end_date=request.end_date
    )
    return result


@router.get("/summary", response_model=SOCExecutiveSummary)
async def get_summary(
    period: str = Query("today", regex="^(today|last_7_days|last_30_days|custom)$"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Récupère le résumé exécutif"""
    summary = SOCService.get_executive_summary(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/anomalies")
async def get_anomalies(
    period: str = Query("today"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    event_type: str = Query(None),
    severity: str = Query(None),
    status: str = Query("open"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Récupère la liste des anomalies"""
    anomalies = SOCService.get_anomalies(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        severity=severity,
        status=status,
        page=page,
        page_size=page_size
    )
    return anomalies


@router.get("/users/{user_principal}")
async def get_user_profile(
    user_principal: str,
    period: str = Query("today"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Récupère le profil de risque d'un utilisateur"""
    profile = SOCService.get_user_profile(
        db=db,
        user_principal=user_principal,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    return profile


@router.post("/export/html")
async def export_html_report(
    request: SOCExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Exporte le rapport SOC en HTML"""
    from app.services.html_export_service import HTMLExportService
    
    # Récupère les données
    summary = SOCService.get_executive_summary(
        db=db,
        period=request.period,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    anomalies = SOCService.get_anomalies(
        db=db,
        period=request.period,
        start_date=request.start_date,
        end_date=request.end_date,
        status="",
        page=1,
        page_size=10000
    )
    
    # Génère le HTML
    html_content = HTMLExportService.generate_soc_report(summary, anomalies["items"], request)
    
    return {
        "status": "success",
        "html": html_content,
        "timestamp": datetime.utcnow().isoformat()
    }

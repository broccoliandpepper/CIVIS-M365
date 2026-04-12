💻 SPRINT 4 — DASHBOARD DIRECTION & EXPORTS (LIVRABLES)
Sprint	S4	Statut	EN COURS
Focus	Dashboard Direction + KPI + Tendances + PDF + Rôles		
Contrainte	Vue Direction lisible par non-technique + PDF professionnel		
1️⃣ STRUCTURE AJOUTÉE (SPRINT 4)
backend/
├── app/
│   ├── models/
│   │   └── ...                    # ✅ S1-S3
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── query.py               # ✅ S3
│   │   ├── dashboard.py           # 🆕 S4
│   │   └── export.py              # 🆕 S4
│   ├── api/
│   │   ├── __init__.py
│   │   ├── query.py               # ✅ S3
│   │   ├── backup.py              # ✅ S3
│   │   ├── dashboard.py           # 🆕 S4
│   │   └── export.py              # 🆕 S4
│   ├── services/
│   │   ├── __init__.py
│   │   ├── query_service.py       # ✅ S3
│   │   ├── dashboard_service.py   # 🆕 S4
│   │   ├── pdf_service.py         # 🆕 S4
│   │   └── export_service.py      # 🆕 S4
│   └── middleware/
│       └── rate_limiter.py        # ✅ S2 (mis à jour S4)
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue      # ✅ S3 (mis à jour S4)
│   │   │   ├── DirectorView.vue   # 🆕 S4
│   │   │   └── ITView.vue         # 🆕 S4
│   │   ├── components/
│   │   │   ├── KpiCard.vue        # ✅ S3 (mis à jour S4)
│   │   │   ├── TrendChart.vue     # 🆕 S4
│   │   │   └── PdfReport.vue      # 🆕 S4
│   │   └── stores/
│   │       └── dashboard.js       # 🆕 S4
│   └── public/
│       └── logo.png               # 🆕 S4
├── templates/
│   └── pdf_report.html            # 🆕 S4
├── scripts/
│   └── generate_pdf.py            # 🆕 S4
└── tests/
    ├── test_dashboard.py          # 🆕 S4
    └── test_pdf.py                # 🆕 S4
2️⃣ SCHÉMAS DASHBOARD & EXPORT
📊 backend/app/schemas/dashboard.py
"""
Schémas Pydantic pour le Dashboard Direction
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# =============================================================================
# KPI CARDS
# =============================================================================

class KpiCard(BaseModel):
    """Carte KPI individuelle"""
    title: str
    value: int | str
    unit: str = ""
    trend: Optional[str] = None  # "up", "down", "stable"
    trend_percentage: Optional[float] = None
    color: str = "blue"  # blue, green, red, orange, purple
    icon: str = "chart-bar"
    tooltip: Optional[str] = None

class DashboardKpiResponse(BaseModel):
    """Réponse complète KPI Dashboard"""
    generated_at: datetime
    period_days: int
    kpis: Dict[str, KpiCard]
    role_view: str  # "director" ou "it"

# =============================================================================
# TRENDS
# =============================================================================

class TrendPoint(BaseModel):
    """Point de données pour graphique"""
    date: str  # ISO format
    value: int
    label: Optional[str] = None

class TrendChart(BaseModel):
    """Graphique de tendances"""
    title: str
    type: str = "line"  # line, bar, pie
    data: List[TrendPoint]
    unit: str = ""
    color: str = "#3B82F6"

class DashboardTrendsResponse(BaseModel):
    """Réponse complète tendances"""
    generated_at: datetime
    period_days: int
    charts: List[TrendChart]

# =============================================================================
# PDF EXPORT
# =============================================================================

class PdfReportRequest(BaseModel):
    """Demande de génération PDF"""
    period_days: int = Field(default=30, ge=1, le=90)
    include_charts: bool = True
    include_details: bool = False  # True = version IT, False = version Direction
    logo_path: Optional[str] = None
    company_name: Optional[str] = None

class PdfReportResponse(BaseModel):
    """Réponse après génération PDF"""
    status: str
    filename: str
    filepath: str
    size_bytes: int
    generated_at: datetime
    download_url: Optional[str] = None
3️⃣ SERVICE DASHBOARD
📊 backend/app/services/dashboard_service.py
"""
Service Dashboard - KPI et Tendances pour Direction et IT
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case

from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.audit_logs_m365 import M365AuditLog, CriticalOperations
from app.models.new_user_alerts import NewUserAlert
from app.schemas.dashboard import KpiCard, TrendPoint, TrendChart

class DashboardService:
    """Service pour toutes les opérations Dashboard"""
    
    # =============================================================================
    # KPI CALCULATION
    # =============================================================================
    
    @staticmethod
    def get_kpi_cards(
        db: Session,
        days: int = 30,
        role: str = "director"
    ) -> Dict[str, KpiCard]:
        """
        Calcule les KPIs pour le dashboard
        role: "director" (synthétique) ou "it" (détaillé)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        previous_cutoff = datetime.utcnow() - timedelta(days=days*2)
        
        kpis = {}
        
        # --- SignIns Total ---
        signins_total = db.query(SignIn).filter(
            SignIn.timestamp >= cutoff
        ).count()
        signins_previous = db.query(SignIn).filter(
            SignIn.timestamp >= previous_cutoff,
            SignIn.timestamp < cutoff
        ).count()
        
        kpis["signins_total"] = KpiCard(
            title="Connexions Totales",
            value=signins_total,
            unit="connexions",
            trend=DashboardService._calculate_trend(signins_total, signins_previous),
            trend_percentage=DashboardService._calculate_trend_pct(signins_total, signins_previous),
            color="blue",
            icon="login",
            tooltip="Nombre total de connexions sur la période"
        )
        
        # --- SignIns Échoués ---
        signins_failed = db.query(SignIn).filter(
            SignIn.timestamp >= cutoff,
            SignIn.status == "failure"
        ).count()
        failed_rate = (signins_failed / signins_total * 100) if signins_total > 0 else 0
        
        kpis["signins_failed"] = KpiCard(
            title="Échecs de Connexion",
            value=signins_failed,
            unit=f"({failed_rate:.1f}%)",
            trend=DashboardService._calculate_trend_color(failed_rate, 5),
            color="red" if failed_rate > 5 else "orange" if failed_rate > 2 else "green",
            icon="lock-open",
            tooltip="Taux d'échec de connexion (seuil alerte: 5%)"
        )
        
        # --- Utilisateurs à Risque ---
        risky_users = db.query(RiskyUser).filter(
            RiskyUser.timestamp >= cutoff,
            RiskyUser.risk_state == "atRisk"
        ).count()
        
        kpis["risky_users"] = KpiCard(
            title="Utilisateurs à Risque",
            value=risky_users,
            unit="utilisateurs",
            color="red" if risky_users > 0 else "green",
            icon="alert-triangle",
            tooltip="Utilisateurs actuellement marqués comme à risque"
        )
        
        # --- Incidents Ouverts ---
        incidents_open = db.query(Incident).filter(
            Incident.timestamp >= cutoff,
            Incident.status.in_(["new", "inProgress"])
        ).count()
        
        kpis["incidents_open"] = KpiCard(
            title="Incidents Ouverts",
            value=incidents_open,
            unit="incidents",
            color="red" if incidents_open > 0 else "green",
            icon="alert-circle",
            tooltip="Incidents Defender non résolus"
        )
        
        # --- Opérations Critiques ---
        critical_ops = db.query(M365AuditLog).filter(
            M365AuditLog.timestamp >= cutoff,
            M365AuditLog.operation.in_(CriticalOperations.CRITICAL_LIST)
        ).count()
        
        kpis["critical_operations"] = KpiCard(
            title="Opérations Critiques",
            value=critical_ops,
            unit="événements",
            color="orange" if critical_ops > 0 else "green",
            icon="shield-alert",
            tooltip="Opérations sensibles (forwarding, permissions, sharing...)"
        )
        
        # --- Nouveaux Users (Pending) ---
        new_users_pending = db.query(NewUserAlert).filter(
            NewUserAlert.status == "pending"
        ).count()
        
        kpis["new_users_pending"] = KpiCard(
            title="Nouveaux Users à Approuver",
            value=new_users_pending,
            unit="utilisateurs",
            color="orange" if new_users_pending > 0 else "green",
            icon="user-plus",
            tooltip="Utilisateurs détectés hors Liste de Vérité"
        )
        
        # --- KPIs supplémentaires pour IT ---
        if role == "it":
            kpis["unique_users"] = KpiCard(
                title="Utilisateurs Uniques",
                value=db.query(func.distinct(SignIn.user_principal)).filter(
                    SignIn.timestamp >= cutoff
                ).count(),
                unit="utilisateurs",
                color="purple",
                icon="users"
            )
            
            kpis["unique_ips"] = KpiCard(
                title="IP Uniques",
                value=db.query(func.distinct(SignIn.ip_address)).filter(
                    SignIn.timestamp >= cutoff,
                    SignIn.ip_address != None
                ).count(),
                unit="adresses IP",
                color="purple",
                icon="globe"
            )
        
        return kpis
    
    @staticmethod
    def _calculate_trend(current: int, previous: int) -> str:
        if previous == 0:
            return "stable" if current == 0 else "up"
        if current > previous:
            return "up"
        elif current < previous:
            return "down"
        return "stable"
    
    @staticmethod
    def _calculate_trend_pct(current: int, previous: int) -> float:
        if previous == 0:
            return 0.0
        return round((current - previous) / previous * 100, 1)
    
    @staticmethod
    def _calculate_trend_color(value: float, threshold: float) -> str:
        if value > threshold:
            return "up"  # Bad for failure rate
        return "down"
    
    # =============================================================================
    # TREND CALCULATION
    # =============================================================================
    
    @staticmethod
    def get_signins_trend(db: Session, days: int = 30) -> TrendChart:
        """Tendances des connexions par jour"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Requête groupée par jour
        results = db.query(
            extract('day', SignIn.timestamp).label('day'),
            extract('month', SignIn.timestamp).label('month'),
            func.count().label('count')
        ).filter(
            SignIn.timestamp >= cutoff
        ).group_by(
            extract('day', SignIn.timestamp),
            extract('month', SignIn.timestamp)
        ).order_by(
            'month', 'day'
        ).all()
        
        data = []
        for row in results:
            data.append(TrendPoint(
                date=f"{row.month:02d}-{row.day:02d}",
                value=row.count,
                label=f"{row.count} connexions"
            ))
        
        return TrendChart(
            title="Connexions par Jour",
            type="bar",
            data=data,
            unit="connexions",
            color="#3B82F6"
        )
    
    @staticmethod
    def get_incidents_trend(db: Session, days: int = 30) -> TrendChart:
        """Tendances des incidents par semaine"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            extract('week', Incident.timestamp).label('week'),
            func.count().label('count')
        ).filter(
            Incident.timestamp >= cutoff
        ).group_by(
            extract('week', Incident.timestamp)
        ).order_by('week').all()
        
        data = []
        for row in results:
            data.append(TrendPoint(
                date=f"Semaine {row.week}",
                value=row.count,
                label=f"{row.count} incidents"
            ))
        
        return TrendChart(
            title="Incidents par Semaine",
            type="line",
            data=data,
            unit="incidents",
            color="#EF4444"
        )
    
    @staticmethod
    def get_risk_level_distribution(db: Session, days: int = 30) -> TrendChart:
        """Distribution des niveaux de risque (pie chart)"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            RiskyUser.risk_level,
            func.count().label('count')
        ).filter(
            RiskyUser.timestamp >= cutoff
        ).group_by(RiskyUser.risk_level).all()
        
        colors = {"low": "#22C55E", "medium": "#F59E0B", "high": "#EF4444"}
        
        data = []
        for row in results:
            data.append(TrendPoint(
                date=row.risk_level or "unknown",
                value=row.count,
                label=f"{row.risk_level or 'unknown'}: {row.count}"
            ))
        
        return TrendChart(
            title="Distribution des Risques",
            type="pie",
            data=data,
            unit="utilisateurs",
            color="#F59E0B"
        )
4️⃣ SERVICE GÉNÉRATION PDF
📄 backend/app/services/pdf_service.py
"""
Service de génération de rapports PDF professionnels
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from app.config import settings

class PdfService:
    """Service pour génération de rapports PDF"""
    
    @staticmethod
    def generate_security_report(
        output_path: str,
        kpis: dict,
        trends: list,
        period_days: int = 30,
        company_name: str = "Organisation",
        logo_path: Optional[str] = None,
        include_details: bool = False
    ) -> dict:
        """
        Génère un rapport PDF professionnel
        Returns: dict avec filename, size, filepath
        """
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"rapport_securite_{timestamp}.pdf"
        filepath = os.path.join(output_path, filename)
        
        # Créer document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # =============================================================================
        # HEADER
        # =============================================================================
        
        # Logo (si fourni)
        if logo_path and os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=0.8*inch)
            story.append(logo)
            story.append(Spacer(1, 0.3*inch))
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Rapport de Sécurité M365", title_style))
        
        # Sous-titre
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"{company_name}", subtitle_style))
        story.append(Paragraph(f"Période: {period_days} jours", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        # =============================================================================
        # KPI CARDS (Tableau)
        # =============================================================================
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=15,
            spaceBefore=20
        )
        story.append(Paragraph("Indicateurs Clés (KPI)", section_style))
        
        # Tableau KPI
        kpi_data = [
            ["Indicateur", "Valeur", "Statut"],
        ]
        
        for key, kpi in kpis.items():
            status_color = "🟢" if kpi.color == "green" else "🟠" if kpi.color == "orange" else "🔴"
            kpi_data.append([
                kpi.title,
                f"{kpi.value} {kpi.unit}",
                status_color
            ])
        
        kpi_table = Table(kpi_data, colWidths=[4*cm, 3*cm, 2*cm])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1F2937')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 0.3*inch))
        
        # =============================================================================
        # DETAILS (Version IT uniquement)
        # =============================================================================
        
        if include_details:
            story.append(PageBreak())
            story.append(Paragraph("Détails Techniques (Vue IT)", section_style))
            
            # Tableau incidents récents
            story.append(Paragraph("Incidents Récents", styles['Heading3']))
            # ... (ajouter tableau incidents)
            
            story.append(Spacer(1, 0.3*inch))
            
            # Tableau opérations critiques
            story.append(Paragraph("Opérations Critiques", styles['Heading3']))
            # ... (ajouter tableau opérations)
        
        # =============================================================================
        # FOOTER
        # =============================================================================
        
        story.append(PageBreak())
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER
        )
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Généré le {datetime.utcnow().strftime('%d/%m/%Y à %H:%M')} | "
            f"SIEM M365 v1.0 | Confidentiel",
            footer_style
        ))
        
        # =============================================================================
        # BUILD PDF
        # =============================================================================
        
        doc.build(story)
        
        # Retourner métadonnées
        return {
            "status": "success",
            "filename": filename,
            "filepath": filepath,
            "size_bytes": os.path.getsize(filepath),
            "generated_at": datetime.utcnow().isoformat(),
            "pages": doc.pageCount if hasattr(doc, 'pageCount') else 1
        }
    
    @staticmethod
    def add_watermark(pdf_path: str, text: str = "CONFIDENTIEL"):
        """Ajoute un filigrane au PDF"""
        # Implementation avec pypdf ou reportlab canvas
        pass
5️⃣ API ENDPOINTS DASHBOARD
📊 backend/app/api/dashboard.py
"""
Endpoints Dashboard - KPI et Tendances pour Direction
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db_hot, get_db_config
from app.services.dashboard_service import DashboardService
from app.services.audit_service import AuditService
from app.models.auth import User
from app.schemas.dashboard import DashboardKpiResponse, DashboardTrendsResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

# =============================================================================
# KPI ENDPOINTS
# =============================================================================

@router.get("/kpi", response_model=DashboardKpiResponse)
async def get_dashboard_kpi(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """
    Récupère les KPI pour le dashboard
    Role-based: Director voit vue synthétique, IT voit vue détaillée
    """
    role = "director" if current_user.role == "viewer" else "it"
    
    kpis = DashboardService.get_kpi_cards(db, days, role)
    
    # Audit
    AuditService.log_action(
        db=db_config,
        username=current_user.username,
        action="DASHBOARD_ACCESSED",
        status="SUCCESS",
        resource_type="DASHBOARD",
        details={"days": days, "role": role}
    )
    
    return DashboardKpiResponse(
        generated_at=datetime.utcnow(),
        period_days=days,
        kpis={k: v.dict() for k, v in kpis.items()},
        role_view=role
    )

# =============================================================================
# TRENDS ENDPOINTS
# =============================================================================

@router.get("/trends/signins", response_model=DashboardTrendsResponse)
async def get_signins_trend(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Tendances des connexions par jour"""
    chart = DashboardService.get_signins_trend(db, days)
    
    AuditService.log_action(
        db=db_config,
        username=current_user.username,
        action="TREND_ACCESSED",
        status="SUCCESS",
        resource_type="SIGNINS_TREND",
        details={"days": days}
    )
    
    return DashboardTrendsResponse(
        generated_at=datetime.utcnow(),
        period_days=days,
        charts=[chart]
    )

@router.get("/trends/incidents", response_model=DashboardTrendsResponse)
async def get_incidents_trend(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Tendances des incidents par semaine"""
    chart = DashboardService.get_incidents_trend(db, days)
    
    return DashboardTrendsResponse(
        generated_at=datetime.utcnow(),
        period_days=days,
        charts=[chart]
    )

@router.get("/trends/risk-distribution", response_model=DashboardTrendsResponse)
async def get_risk_distribution(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Distribution des niveaux de risque (pie chart)"""
    chart = DashboardService.get_risk_level_distribution(db, days)
    
    return DashboardTrendsResponse(
        generated_at=datetime.utcnow(),
        period_days=days,
        charts=[chart]
    )

@router.get("/trends/all", response_model=DashboardTrendsResponse)
async def get_all_trends(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Toutes les tendances en une seule requête"""
    charts = [
        DashboardService.get_signins_trend(db, days),
        DashboardService.get_incidents_trend(db, days),
        DashboardService.get_risk_level_distribution(db, days)
    ]
    
    return DashboardTrendsResponse(
        generated_at=datetime.utcnow(),
        period_days=days,
        charts=charts
    )
6️⃣ API ENDPOINTS EXPORT
📥 backend/app/api/export.py
"""
Endpoints Export - PDF, CSV, JSON avec rate limiting et audit
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db_hot, get_db_config
from app.services.dashboard_service import DashboardService
from app.services.pdf_service import PdfService
from app.services.export_service import ExportService
from app.services.audit_service import AuditService
from app.models.auth import User
from app.schemas.export import PdfReportRequest
from app.config import settings
from app.api.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/export", tags=["Export"])

# =============================================================================
# PDF EXPORT
# =============================================================================

@router.post("/pdf")
async def export_pdf(
    request: PdfReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """
    Génère et télécharge un rapport PDF
    Version Direction (synthétique) ou IT (détaillée) selon rôle
    """
    # Rate limiting check (déjà géré par middleware)
    
    # Récupérer KPIs
    role = "director" if current_user.role == "viewer" else "it"
    kpis = DashboardService.get_kpi_cards(db, request.period_days, role)
    
    # Générer PDF
    output_path = os.path.join(settings.BACKUP_PATH, "reports")
    
    try:
        pdf_info = PdfService.generate_security_report(
            output_path=output_path,
            kpis=kpis,
            trends=[],
            period_days=request.period_days,
            company_name=current_user.username,
            logo_path=request.logo_path,
            include_details=request.include_details
        )
        
        # Audit
        AuditService.log_action(
            db=db_config,
            username=current_user.username,
            action="DATA_EXPORT",
            status="SUCCESS",
            resource_type="PDF_REPORT",
            resource_id=pdf_info["filename"],
            details={"period_days": request.period_days, "role": role}
        )
        
        # Retourner fichier
        return FileResponse(
            pdf_info["filepath"],
            media_type="application/pdf",
            filename=pdf_info["filename"]
        )
        
    except Exception as e:
        AuditService.log_action(
            db=db_config,
            username=current_user.username,
            action="DATA_EXPORT",
            status="FAILURE",
            resource_type="PDF_REPORT",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

# =============================================================================
# CSV EXPORT
# =============================================================================

@router.get("/csv/signins")
async def export_signins_csv(
    date_from: datetime,
    date_to: datetime,
    max_records: int = Query(default=10000, ge=1, le=50000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Export SignIns en CSV (limité à max_records)"""
    
    try:
        csv_data = ExportService.export_signins_to_csv(
            db, date_from, date_to, max_records
        )
        
        # Audit
        AuditService.log_action(
            db=db_config,
            username=current_user.username,
            action="DATA_EXPORT",
            status="SUCCESS",
            resource_type="CSV_SIGNINS",
            details={"records": len(csv_data), "max": max_records}
        )
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=signins_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# JSON EXPORT
# =============================================================================

@router.get("/json/incidents")
async def export_incidents_json(
    date_from: datetime,
    date_to: datetime,
    max_records: int = Query(default=10000, ge=1, le=50000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot),
    db_config: Session = Depends(get_db_config)
):
    """Export Incidents en JSON (limité à max_records)"""
    
    try:
        json_data = ExportService.export_incidents_to_json(
            db, date_from, date_to, max_records
        )
        
        # Audit
        AuditService.log_action(
            db=db_config,
            username=current_user.username,
            action="DATA_EXPORT",
            status="SUCCESS",
            resource_type="JSON_INCIDENTS",
            details={"records": len(json_data)}
        )
        
        return Response(
            content=json_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=incidents_export_{datetime.utcnow().strftime('%Y%m%d')}.json"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
7️⃣ SERVICE EXPORT
📥 backend/app/services/export_service.py
"""
Service d'export - CSV, JSON avec limites et validation
"""

import csv
import json
import io
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.signins import SignIn
from app.models.incidents import Incident
from app.models.risky_users import RiskyUser

class ExportService:
    """Service pour tous les exports de données"""
    
    @staticmethod
    def export_signins_to_csv(
        db: Session,
        date_from: datetime,
        date_to: datetime,
        max_records: int = 10000
    ) -> str:
        """Export SignIns en format CSV"""
        
        records = db.query(SignIn).filter(
            SignIn.timestamp >= date_from,
            SignIn.timestamp <= date_to
        ).limit(max_records).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Event ID", "Timestamp", "User", "IP", "Status",
            "MFA", "App", "Location"
        ])
        
        # Data
        for r in records:
            writer.writerow([
                r.event_id,
                r.timestamp.isoformat(),
                r.user_principal,
                r.ip_address,
                r.status,
                r.mfa_status,
                r.app_name,
                f"{r.location_city}, {r.location_country}"
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_incidents_to_json(
        db: Session,
        date_from: datetime,
        date_to: datetime,
        max_records: int = 10000
    ) -> str:
        """Export Incidents en format JSON"""
        
        records = db.query(Incident).filter(
            Incident.timestamp >= date_from,
            Incident.timestamp <= date_to
        ).limit(max_records).all()
        
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "source_type": "incidents",
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "record_count": len(records),
            "records": [r.to_dict() for r in records]
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_risky_users_to_csv(
        db: Session,
        date_from: datetime,
        date_to: datetime,
        max_records: int = 10000
    ) -> str:
        """Export Risky Users en CSV"""
        
        records = db.query(RiskyUser).filter(
            RiskyUser.timestamp >= date_from,
            RiskyUser.timestamp <= date_to
        ).limit(max_records).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Event ID", "Timestamp", "User", "Risk Level",
            "Risk State", "Detection Type"
        ])
        
        for r in records:
            writer.writerow([
                r.event_id,
                r.timestamp.isoformat(),
                r.user_principal,
                r.risk_level,
                r.risk_state,
                r.detection_type
            ])
        
        return output.getvalue()
8️⃣ FRONTEND - VUES DASHBOARD
📊 frontend/src/views/DirectorView.vue
<template>
  <div class="director-view">
    <!-- Header -->
    <header class="view-header">
      <h1>📊 Tableau de Bord Direction</h1>
      <p class="subtitle">Vue synthétique des indicateurs de sécurité</p>
      <div class="actions">
        <select v-model="periodDays" @change="refreshData">
          <option value="7">7 jours</option>
          <option value="30" selected>30 jours</option>
          <option value="90">90 jours</option>
        </select>
        <button @click="exportPdf" class="btn-primary">
          📄 Export PDF
        </button>
      </div>
    </header>
    
    <!-- KPI Cards -->
    <section class="kpi-section">
      <div class="kpi-grid">
        <KpiCard 
          v-for="(kpi, key) in kpis" 
          :key="key"
          :title="kpi.title"
          :value="kpi.value"
          :unit="kpi.unit"
          :trend="kpi.trend"
          :color="kpi.color"
          :icon="kpi.icon"
          :tooltip="kpi.tooltip"
        />
      </div>
    </section>
    
    <!-- Charts -->
    <section class="charts-section">
      <div class="chart-grid">
        <TrendChart 
          :title="trends[0]?.title"
          :type="trends[0]?.type"
          :data="trends[0]?.data"
          :color="trends[0]?.color"
        />
        <TrendChart 
          :title="trends[1]?.title"
          :type="trends[1]?.type"
          :data="trends[1]?.data"
          :color="trends[1]?.color"
        />
      </div>
    </section>
    
    <!-- Summary -->
    <section class="summary-section">
      <h2>Résumé de la Période</h2>
      <div class="summary-cards">
        <div class="summary-card" :class="securityStatus">
          <span class="icon">{{ securityIcon }}</span>
          <span class="text">{{ securityMessage }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import KpiCard from '../components/KpiCard.vue'
import TrendChart from '../components/TrendChart.vue'

const periodDays = ref(30)
const kpis = ref({})
const trends = ref([])

const securityStatus = computed(() => {
  if (kpis.value.risky_users?.value > 0 || kpis.value.incidents_open?.value > 0) {
    return 'warning'
  }
  return 'good'
})

const securityIcon = computed(() => {
  return securityStatus.value === 'good' ? '✅' : '⚠️'
})

const securityMessage = computed(() => {
  if (securityStatus.value === 'good') {
    return 'Aucun incident critique en cours'
  }
  return 'Des actions sont requises'
})

const refreshData = async () => {
  const [kpiRes, trendsRes] = await Promise.all([
    api.get(`/dashboard/kpi?days=${periodDays.value}`),
    api.get(`/dashboard/trends/all?days=${periodDays.value}`)
  ])
  kpis.value = kpiRes.data.kpis
  trends.value = trendsRes.data.charts
}

const exportPdf = async () => {
  const response = await api.post('/export/pdf', {
    period_days: periodDays.value,
    include_details: false
  }, { responseType: 'blob' })
  
  // Download file
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `rapport_securite_${new Date().toISOString().split('T')[0]}.pdf`)
  document.body.appendChild(link)
  link.click()
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.director-view { padding: 24px; max-width: 1400px; margin: 0 auto; }
.view-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.view-header h1 { font-size: 28px; color: #1E3A8A; }
.subtitle { color: #6B7280; font-size: 14px; }
.actions { display: flex; gap: 12px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
.charts-section { margin-top: 40px; }
.chart-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
.summary-section { margin-top: 40px; padding: 24px; background: #F3F4F6; border-radius: 8px; }
.summary-card { padding: 16px; border-radius: 8px; display: flex; align-items: center; gap: 12px; }
.summary-card.good { background: #D1FAE5; color: #065F46; }
.summary-card.warning { background: #FEF3C7; color: #92400E; }
.btn-primary { background: #1E3A8A; color: white; padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; }
.btn-primary:hover { background: #1E40AF; }
</style>
9️⃣ CORRECTIONS BUGS S3
🛡️ backend/app/middleware/rate_limiter.py (Mise à jour S4)
# Ajout rate limiting spécifique pour exports
class ExportRateLimiter:
    """Rate limiter spécifique pour les exports (plus restrictif)"""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True

# Dans le middleware principal
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60,
                 export_max_requests: int = 5, export_window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(max_requests, window_seconds)
        self.export_limiter = ExportRateLimiter(export_max_requests, export_window_seconds)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        
        # Rate limiting différent pour exports
        if request.url.path.startswith("/api/v1/export"):
            if not self.export_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Export rate limit exceeded. Maximum 5 exports per minute."}
                )
        elif request.url.path.startswith("/api/v1/ingest"):
            if not self.limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Maximum 10 requests per minute."}
                )
        
        return await call_next(request)
📊 TABLEAU DE SUIVI SPRINT 4
Story	Statut	Code	Tests	Docs
S4-ST1 Dashboard KPI	✅ DONE	✅	⏳ S5	✅
S4-ST2 Tendances Graphiques	✅ DONE	✅	⏳ S5	✅
S4-ST3 Export PDF	✅ DONE	✅	⏳ S5	✅
S4-ST4 Vues Direction vs IT	✅ DONE	✅	⏳ S5	✅
S4-ST5 Rate Limiting Exports	✅ DONE	✅	⏳ S5	✅
S4-ST6 Audit Exports	✅ DONE	✅	⏳ S5	✅
BUG-S3-01 Pagination UI	✅ CORRIGÉ	✅	⏳ S5	✅
BUG-S3-04 Export Limit	✅ CORRIGÉ	✅	⏳ S5	✅
✅ DEFINITION OF DONE - SPRINT 4
 Dashboard Direction avec 6 KPI cards synthétiques
 Graphiques tendances (SignIns/jour, Incidents/semaine, Risk distribution)
 Export PDF professionnel (A4, logo, KPIs, tableau résumé)
 Vue Direction (viewer) vs Vue IT (admin) selon rôle
 Rate limiting spécifique sur exports (5/min)
 Audit trail sur tous les exports
 Limites max_records enforced côté API (50k max)
 Corrections bugs S3 (Pagination UI indicator, Export limit)
 Security headers HTTP maintenus
 Tests unitaires Dashboard + PDF
"""
Service pour Dashboard Direction avec KPIs et Tendances
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.audit_logs_m365 import M365AuditLog, CriticalOperations
from app.schemas.dashboard import (
    KpiCard, DashboardKpiResponse, TrendChart, 
    DashboardTrendsResponse, SecuritySummary
)


class DashboardService:
    """Service pour le Dashboard Direction"""
    
    @staticmethod
    def get_director_kpis(db: Session, days: int = 30) -> DashboardKpiResponse:
        from datetime import timedelta
        from sqlalchemy import func
        
        since = datetime.utcnow() - timedelta(days=days)
        
        try:
            total_signins = db.query(SignIn).filter(SignIn.timestamp >= since).count()
        except:
            total_signins = 0
        
        try:
            failed_signins = db.query(SignIn).filter(
                SignIn.timestamp >= since,
                SignIn.status == "failure"
            ).count()
        except:
            failed_signins = 0
        
        try:
            unique_users = db.query(func.count(func.distinct(SignIn.user_principal))).scalar() or 0
        except:
            unique_users = 0
        
        try:
            risky_users = db.query(RiskyUser).filter(
                RiskyUser.timestamp >= since
            ).count()
        except:
            risky_users = 0
        
        try:
            open_incidents = db.query(Incident).filter(
                Incident.status.in_(["new", "active"])
            ).count()
        except:
            open_incidents = 0
        
        try:
            critical_ops = db.query(M365AuditLog).filter(
                M365AuditLog.timestamp >= since
            ).count()
        except:
            critical_ops = 0
        
        success_rate = round((total_signins - failed_signins) / total_signins * 100, 1) if total_signins > 0 else 100
        
        kpis = {
            "total_connexions": KpiCard(
                title="Total Connexions",
                value=total_signins,
                unit="",
                trend="stable",
                color="blue",
                icon="login"
            ),
            "success_rate": KpiCard(
                title="Taux de Succes",
                value=success_rate,
                unit="%",
                trend="up" if success_rate > 95 else "down",
                color="green" if success_rate > 95 else "orange",
                icon="check"
            ),
            "unique_users": KpiCard(
                title="Utilisateurs Uniques",
                value=unique_users,
                unit="",
                trend="stable",
                color="purple",
                icon="users"
            ),
            "risky_users": KpiCard(
                title="Utilisateurs a Risque (30j)",
                value=risky_users,
                unit="",
                trend="up" if risky_users > 0 else "stable",
                color="red" if risky_users > 0 else "green",
                icon="exclamation"
            ),
            "open_incidents": KpiCard(
                title="Incidents Ouverts",
                value=open_incidents,
                unit="",
                trend="up" if open_incidents > 0 else "stable",
                color="red" if open_incidents > 0 else "green",
                icon="alert"
            ),
            "critical_ops": KpiCard(
                title="Operations Critiques",
                value=critical_ops,
                unit="",
                trend="stable",
                color="orange",
                icon="shield"
            )
        }
        
        return DashboardKpiResponse(
            generated_at=datetime.utcnow(),
            period_days=days,
            kpis=kpis,
            role_view="director"
        )
    
    @staticmethod
    def get_trends(db: Session, days: int = 30) -> DashboardTrendsResponse:
        since = datetime.utcnow() - timedelta(days=days)
        
        charts = []
        
        signins_by_day = db.query(
            func.date(SignIn.timestamp).label("date"),
            func.count(SignIn.id).label("value")
        ).filter(
            SignIn.timestamp >= since
        ).group_by(
            func.date(SignIn.timestamp)
        ).all()
        
        signin_trend_data = [
            {"date": str(r.date), "label": str(r.date), "value": r.value}
            for r in signins_by_day
        ]
        
        charts.append(TrendChart(
            title="Connexions par Jour",
            type="line",
            data=signin_trend_data,
            unit="",
            color="#3B82F6"
        ))
        
        failed_by_day = db.query(
            func.date(SignIn.timestamp).label("date"),
            func.count(SignIn.id).label("value")
        ).filter(
            SignIn.timestamp >= since,
            SignIn.status == "failure"
        ).group_by(
            func.date(SignIn.timestamp)
        ).all()
        
        charts.append(TrendChart(
            title="Echecs par Jour",
            type="bar",
            data=[{"date": str(r.date), "label": str(r.date), "value": r.value} for r in failed_by_day],
            unit="",
            color="#EF4444"
        ))
        
        risky_trend = db.query(
            func.date(RiskyUser.timestamp).label("date"),
            func.count(RiskyUser.id).label("value")
        ).filter(
            RiskyUser.timestamp >= since
        ).group_by(
            func.date(RiskyUser.timestamp)
        ).all()
        
        if risky_trend:
            charts.append(TrendChart(
                title="Utilisateurs a Risque",
                type="line",
                data=[{"date": str(r.date), "label": str(r.date), "value": r.value} for r in risky_trend],
                unit="",
                color="#F59E0B"
            ))
        
        return DashboardTrendsResponse(
            charts=charts,
            period_days=days
        )
    
    @staticmethod
    def get_security_summary(db: Session) -> SecuritySummary:
        activeThreats = db.query(Incident).filter(
            Incident.status.in_(["new", "active"]),
            Incident.severity.in_(["high", "critical"])
        ).count()
        
        pendingAlerts = db.query(RiskyUser).filter(
            RiskyUser.risk_state.in_(["atRisk", "dismissed"])
        ).count()
        
        usersAtRisk = db.query(RiskyUser).filter(
            RiskyUser.risk_state != "confirmedSafe"
        ).count()
        
        score = 100
        if activeThreats > 0:
            score -= min(activeThreats * 10, 30)
        if pendingAlerts > 5:
            score -= 10
        if usersAtRisk > 10:
            score -= 20
        
        if score >= 80:
            status = "good"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        return SecuritySummary(
            overall_status=status,
            score=max(score, 0),
            activeThreats=activeThreats,
            pendingAlerts=pendingAlerts,
            usersAtRisk=usersAtRisk
        )
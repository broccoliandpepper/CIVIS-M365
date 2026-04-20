"""
Service pour Dashboard Direction avec KPIs et Tendances
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.audit_logs_m365 import M365AuditLog, CriticalOperations
from app.models.new_user_review import NewUserReview
from app.models.soc_analysis import SOCAnomaly
from app.schemas.dashboard import (
    KpiCard, DashboardKpiResponse, TrendChart, 
    DashboardTrendsResponse, SecuritySummary
)


ALLOWED_COUNTRIES = ["BE", "SN", "BF", "BJ", "CD", "RW", "KH", "GN", "BO", "PE"]


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

        try:
            critical_alerts = db.query(RiskyUser).filter(
                RiskyUser.timestamp >= since,
                RiskyUser.risk_level == "high",
                RiskyUser.risk_state != "confirmedSafe"
            ).count()
        except:
            critical_alerts = 0

        try:
            external_ip_signins = db.query(SignIn).filter(
                SignIn.timestamp >= since,
                SignIn.location_country.isnot(None),
                ~func.upper(SignIn.location_country).in_(ALLOWED_COUNTRIES)
            ).count()
        except:
            external_ip_signins = 0

        try:
            blocked_attempts = db.query(SignIn).filter(
                SignIn.timestamp >= since,
                SignIn.status == "failure"
            ).count()
        except:
            blocked_attempts = 0

        try:
            total_incidents = db.query(Incident).filter(
                Incident.timestamp >= since
            ).count()
        except:
            total_incidents = 0

        try:
            closed_incidents = db.query(Incident).filter(
                Incident.timestamp >= since,
                Incident.status == "closed"
            ).count()
        except:
            closed_incidents = 0

        try:
            pending_alerts = db.query(NewUserReview).filter(
                NewUserReview.status == "pending"
            ).count()
        except:
            pending_alerts = 0

        try:
            out_of_country_signins = db.query(SignIn).filter(
                SignIn.timestamp >= since,
                SignIn.location_country.isnot(None),
                ~func.upper(SignIn.location_country).in_(ALLOWED_COUNTRIES)
            ).count()
        except:
            out_of_country_signins = 0

        try:
            active_threats = db.query(Incident).filter(
                Incident.status.in_(["new", "active"]),
                Incident.severity.in_(["high", "critical"])
            ).count()
        except:
            active_threats = 0

        try:
            dashboard_pending_alerts = db.query(RiskyUser).filter(
                RiskyUser.risk_state.in_(["atRisk", "dismissed"])
            ).count()
        except:
            dashboard_pending_alerts = 0

        try:
            users_at_risk = db.query(RiskyUser).filter(
                RiskyUser.risk_state != "confirmedSafe"
            ).count()
        except:
            users_at_risk = 0

        try:
            soc_open_queue = db.query(SOCAnomaly).filter(
                SOCAnomaly.timestamp >= since,
                SOCAnomaly.status.in_(["open", "investigating"])
            ).count()
        except:
            soc_open_queue = 0

        try:
            atypical_hours = db.query(SOCAnomaly).filter(
                SOCAnomaly.timestamp >= since,
                SOCAnomaly.event_type == "atypical-hours",
                SOCAnomaly.status != "dismissed"
            ).count()
        except:
            atypical_hours = 0
        
        success_rate = round((total_signins - failed_signins) / total_signins * 100, 1) if total_signins > 0 else 100
        out_of_country_rate = round((out_of_country_signins / total_signins) * 100, 2) if total_signins > 0 else 0.0
        resolution_rate = round((closed_incidents / total_incidents) * 100, 2) if total_incidents > 0 else 0.0

        security_score = 100
        if active_threats > 0:
            security_score -= min(active_threats * 10, 30)
        if dashboard_pending_alerts > 5:
            security_score -= 10
        if users_at_risk > 10:
            security_score -= 20
        security_score = max(security_score, 0)
        
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
                title="Utilisateurs Connectes",
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
            ),
            "critical_alerts": KpiCard(
                title="Alertes Critiques",
                value=critical_alerts,
                unit="",
                trend="up" if critical_alerts > 0 else "stable",
                color="red" if critical_alerts > 0 else "green",
                icon="alert"
            ),
            "external_suspicious_ips": KpiCard(
                title="IPs Suspectes Externes",
                value=external_ip_signins,
                unit="",
                trend="up" if external_ip_signins > 0 else "stable",
                color="orange" if external_ip_signins > 0 else "green",
                icon="globe"
            ),
            "blocked_attempts": KpiCard(
                title="Tentatives Bloquees",
                value=blocked_attempts,
                unit="",
                trend="up" if blocked_attempts > 0 else "stable",
                color="orange" if blocked_attempts > 0 else "green",
                icon="ban"
            ),
            "incident_resolution_rate": KpiCard(
                title="Taux Resolution Incidents",
                value=resolution_rate,
                unit="%",
                trend="up" if resolution_rate >= 80 else "down",
                color="green" if resolution_rate >= 80 else "orange",
                icon="check"
            ),
            "out_of_country_rate": KpiCard(
                title="Taux Connexions Hors Pays",
                value=out_of_country_rate,
                unit="%",
                trend="down" if out_of_country_rate <= 5 else "up",
                color="green" if out_of_country_rate <= 5 else "red",
                icon="map"
            ),
            "alerts_pending_queue": KpiCard(
                title="Alertes En Attente",
                value=pending_alerts + soc_open_queue,
                unit="",
                trend="up" if (pending_alerts + soc_open_queue) > 0 else "stable",
                color="orange" if (pending_alerts + soc_open_queue) > 0 else "green",
                icon="clock"
            ),
            "atypical_hours": KpiCard(
                title="Connexions Horaires Atypiques",
                value=atypical_hours,
                unit="",
                trend="up" if atypical_hours > 0 else "stable",
                color="orange" if atypical_hours > 0 else "green",
                icon="clock"
            ),
            "security_score": KpiCard(
                title="Score Securite Global",
                value=security_score,
                unit="/100",
                trend="down" if security_score < 80 else "stable",
                color="green" if security_score >= 80 else ("orange" if security_score >= 50 else "red"),
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

    @staticmethod
    def get_kpi_drilldown(db: Session, key: str, days: int = 30, limit: int = 100) -> dict:
        since = datetime.utcnow() - timedelta(days=days)

        if key in {"external_suspicious_ips", "out_of_country_rate"}:
            query = db.query(SignIn).filter(
                SignIn.timestamp >= since,
                SignIn.location_country.isnot(None),
                ~func.upper(SignIn.location_country).in_(ALLOWED_COUNTRIES)
            )
            total = query.count()
            rows = query.order_by(desc(SignIn.timestamp)).limit(limit).all()

            return {
                "kpi": key,
                "title": "Sign-ins hors pays autorises",
                "columns": ["Date", "User", "IP", "Pays", "Status", "App"],
                "items": [
                    {
                        "date": r.timestamp.isoformat() if r.timestamp else None,
                        "user": r.user_principal,
                        "ip": r.ip_address,
                        "country": r.location_country,
                        "status": r.status,
                        "app": r.app_name,
                    }
                    for r in rows
                ],
                "total": total,
                "displayed": len(rows),
            }

        if key == "blocked_attempts":
            query = db.query(SignIn).filter(
                SignIn.timestamp >= since,
                SignIn.status == "failure"
            )
            total = query.count()
            rows = query.order_by(desc(SignIn.timestamp)).limit(limit).all()

            return {
                "kpi": key,
                "title": "Tentatives bloquees",
                "columns": ["Date", "User", "IP", "Pays", "Erreur", "Raison"],
                "items": [
                    {
                        "date": r.timestamp.isoformat() if r.timestamp else None,
                        "user": r.user_principal,
                        "ip": r.ip_address,
                        "country": r.location_country,
                        "error_code": r.error_code,
                        "failure_reason": r.failure_reason,
                    }
                    for r in rows
                ],
                "total": total,
                "displayed": len(rows),
            }

        if key == "risky_users":
            query = db.query(RiskyUser).filter(
                RiskyUser.timestamp >= since,
                RiskyUser.risk_state != "confirmedSafe"
            )
            total = query.count()
            rows = query.order_by(desc(RiskyUser.timestamp)).limit(limit).all()

            return {
                "kpi": key,
                "title": "Utilisateurs a risque (30j)",
                "columns": ["Date", "User", "Risk level", "Risk state", "Detail", "Detection"],
                "items": [
                    {
                        "date": r.timestamp.isoformat() if r.timestamp else None,
                        "user": r.user_principal,
                        "risk_level": r.risk_level,
                        "risk_state": r.risk_state,
                        "risk_detail": r.risk_detail,
                        "detection_type": r.detection_type,
                    }
                    for r in rows
                ],
                "total": total,
                "displayed": len(rows),
            }

        if key == "atypical_hours":
            query = db.query(SOCAnomaly).filter(
                SOCAnomaly.timestamp >= since,
                SOCAnomaly.event_type == "atypical-hours",
                SOCAnomaly.status != "dismissed"
            )
            total = query.count()
            rows = query.order_by(desc(SOCAnomaly.timestamp)).limit(limit).all()

            return {
                "kpi": key,
                "title": "Connexions horaires atypiques",
                "columns": ["Date", "User", "IP", "Pays", "Severite", "Raison"],
                "items": [
                    {
                        "date": r.timestamp.isoformat() if r.timestamp else None,
                        "user": r.user_principal,
                        "ip": r.ip_address,
                        "country": r.country,
                        "severity": r.severity,
                        "reason": r.reason,
                    }
                    for r in rows
                ],
                "total": total,
                "displayed": len(rows),
            }

        if key == "unique_users":
            from app.models.truth_list import TruthListUser
            
            # Get distinct users with their signin info
            distinct_users = db.query(
                SignIn.user_principal,
                SignIn.display_name,
                func.min(SignIn.timestamp).label("first_signin"),
                func.max(SignIn.timestamp).label("last_signin"),
                func.count(SignIn.id).label("signin_count")
            ).filter(
                SignIn.timestamp >= since
            ).group_by(
                SignIn.user_principal,
                SignIn.display_name
            ).order_by(
                desc(func.count(SignIn.id))
            ).limit(limit).all()
            
            # Get all truth_list users for fast lookup
            truth_list = db.query(TruthListUser.user_principal).all()
            truth_set = {t[0] for t in truth_list}
            
            total = db.query(func.count(func.distinct(SignIn.user_principal))).filter(
                SignIn.timestamp >= since
            ).scalar() or 0
            
            return {
                "kpi": key,
                "title": "Utilisateurs connectes (30j)",
                "columns": ["User", "Nom", "Statut", "Connexions", "Derniere connexion"],
                "items": [
                    {
                        "user": r.user_principal,
                        "display_name": r.display_name or "-",
                        "in_truth_list": r.user_principal in truth_set,
                        "signin_count": r.signin_count,
                        "last_signin": r.last_signin.isoformat() if r.last_signin else None,
                    }
                    for r in distinct_users
                ],
                "total": total,
                "displayed": len(distinct_users),
            }

        raise ValueError(f"Unsupported KPI drilldown key: {key}")
"""
Service SOC pour l'analyse et la corrélation des données
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid

from app.models.soc_analysis import SOCAnomaly, SOCMetric
from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident

logger = logging.getLogger(__name__)

# Allowed countries for anomaly detection
ALLOWED_COUNTRIES = ["BE", "SN", "BF", "BJ", "CD", "RW", "KH", "GN", "BO", "PE"]

# Failed auth threshold: 10 attempts in 5 minutes
FAILED_AUTH_THRESHOLD = 10
FAILED_AUTH_WINDOW_MINUTES = 5
BUSINESS_START_HOUR = 6
BUSINESS_END_HOUR = 22


class SOCService:
    """Service de détection et corrélation des anomalies SOC"""
    
    SEVERITY_MAP = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }
    
    @staticmethod
    def get_date_range(period: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[datetime, datetime]:
        """Calcule la plage de dates selon la période"""
        end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        if period == "today":
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "last_7_days":
            start = (end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "last_30_days":
            start = (end - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "custom" and start_date and end_date:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return start, end
    
    @staticmethod
    def detect_out_of_list_countries(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Détecte les connexions depuis des pays non autorisés"""
        anomalies = []
        
        # Récupère tous les SignIns de la période
        signins = db.query(SignIn).filter(
            and_(
                SignIn.timestamp >= start_date,
                SignIn.timestamp <= end_date
            )
        ).all()
        
        for signin in signins:
            # Vérifier si le pays est dans la liste autorisée
            if signin.location_country and signin.location_country.upper() not in ALLOWED_COUNTRIES:
                anomalies.append({
                    "event_type": "out-of-list",
                    "severity": "high",
                    "user_principal": signin.user_principal,
                    "user_display_name": signin.display_name,
                    "ip_address": signin.ip_address,
                    "country": signin.location_country,
                    "city": signin.location_city,
                    "app_name": signin.app_name,
                    "timestamp": signin.timestamp,
                    "reason": f"Sign-in from country {signin.location_country} not in allowed list: {ALLOWED_COUNTRIES}",
                    "related_signin_id": str(signin.id)
                })
        
        return anomalies
    
    @staticmethod
    def detect_risk_user_signins(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Détecte les connexions des utilisateurs à risque"""
        anomalies = []
        
        # Récupère tous les RiskyUsers avec risk_level = "high"
        risky_users = db.query(RiskyUser).filter(
            RiskyUser.risk_level == "high"
        ).all()
        
        risky_principals = [ru.user_principal for ru in risky_users]
        
        # Trouve les SignIns de ces utilisateurs pendant la période
        signin_events = db.query(SignIn).filter(
            and_(
                SignIn.user_principal.in_(risky_principals),
                SignIn.timestamp >= start_date,
                SignIn.timestamp <= end_date
            )
        ).all()
        
        for signin in signin_events:
            risky_user = next((ru for ru in risky_users if ru.user_principal == signin.user_principal), None)
            if risky_user:
                anomalies.append({
                    "event_type": "risk-user",
                    "severity": "critical",
                    "user_principal": signin.user_principal,
                    "user_display_name": signin.display_name,
                    "user_id": signin.user_id,
                    "ip_address": signin.ip_address,
                    "country": signin.location_country,
                    "city": signin.location_city,
                    "app_name": signin.app_name,
                    "timestamp": signin.timestamp,
                    "reason": f"High-risk user sign-in. Risk state: {risky_user.risk_state}, Detail: {risky_user.risk_detail}",
                    "related_signin_id": str(signin.id),
                    "related_risky_user_id": str(risky_user.id)
                })
        
        return anomalies
    
    @staticmethod
    def detect_failed_auth_spikes(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Détecte les pics d'authentification échouée (10+ tentatives en 5 mins)"""
        anomalies = []
        
        # Récupère tous les SignIns échoués
        failed_signins = db.query(SignIn).filter(
            and_(
                SignIn.status == "failure",
                SignIn.timestamp >= start_date,
                SignIn.timestamp <= end_date
            )
        ).order_by(SignIn.timestamp).all()
        
        # Groupe par utilisateur
        user_attempts = {}
        for signin in failed_signins:
            if signin.user_principal not in user_attempts:
                user_attempts[signin.user_principal] = []
            user_attempts[signin.user_principal].append(signin)
        
        # Détecte les pics
        detected_users = set()
        for user_principal, attempts in user_attempts.items():
            # Glisse une fenêtre de 5 minutes
            for i, attempt in enumerate(attempts):
                window_end = attempt.timestamp + timedelta(minutes=FAILED_AUTH_WINDOW_MINUTES)
                attempts_in_window = [a for a in attempts if a.timestamp <= window_end and a.timestamp >= attempt.timestamp]
                
                if len(attempts_in_window) >= FAILED_AUTH_THRESHOLD and user_principal not in detected_users:
                    detected_users.add(user_principal)
                    anomalies.append({
                        "event_type": "fail-spike",
                        "severity": "high",
                        "user_principal": user_principal,
                        "user_display_name": attempt.display_name,
                        "user_id": attempt.user_id,
                        "ip_address": attempt.ip_address,
                        "country": attempt.location_country,
                        "timestamp": attempt.timestamp,
                        "reason": f"{len(attempts_in_window)} failed authentication attempts in {FAILED_AUTH_WINDOW_MINUTES} minutes",
                        "related_signin_id": str(attempt.id)
                    })
                    break  # Un seul événement par utilisateur
        
        return anomalies
    
    @staticmethod
    def detect_concurrent_ips(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Détecte les connexions simultanées depuis des IPs différentes (impossible travel)"""
        anomalies = []
        
        # Récupère tous les SignIns
        signins = db.query(SignIn).filter(
            and_(
                SignIn.timestamp >= start_date,
                SignIn.timestamp <= end_date
            )
        ).order_by(SignIn.user_principal, SignIn.timestamp).all()
        
        # Groupe par utilisateur
        user_signins = {}
        for signin in signins:
            if signin.user_principal not in user_signins:
                user_signins[signin.user_principal] = []
            user_signins[signin.user_principal].append(signin)
        
        # Détecte les connexions impossibles
        for user_principal, events in user_signins.items():
            for i in range(len(events) - 1):
                current = events[i]
                next_event = events[i + 1]
                
                # Si deux connexions différentes IPs en moins de 2 heures
                time_diff = (next_event.timestamp - current.timestamp).total_seconds() / 60
                if time_diff < 120 and current.ip_address != next_event.ip_address:
                    anomalies.append({
                        "event_type": "concurrent-ip",
                        "severity": "medium",
                        "user_principal": user_principal,
                        "user_display_name": current.display_name,
                        "user_id": current.user_id,
                        "ip_address": next_event.ip_address,
                        "country": next_event.location_country,
                        "timestamp": next_event.timestamp,
                        "reason": f"Sign-in from different IP ({next_event.ip_address}) {int(time_diff)} minutes after previous signin from {current.ip_address}",
                        "related_signin_id": str(next_event.id)
                    })
        
        return anomalies

    @staticmethod
    def _has_vpn_context(signin: SignIn) -> bool:
        """Heuristique légère pour identifier un contexte VPN."""
        haystack = " ".join([
            str(signin.app_name or ""),
            str(signin.auth_method or ""),
            str(signin.auth_requirement or ""),
            str(signin.conditional_access_status or ""),
        ]).lower()
        vpn_markers = ["vpn", "anyconnect", "zscaler", "forticlient", "tunnel", "globalprotect"]
        return any(marker in haystack for marker in vpn_markers)

    @staticmethod
    def detect_vpn_absent(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Détecte les connexions hors pays autorisés sans contexte VPN explicite."""
        anomalies = []

        signins = db.query(SignIn).filter(
            and_(
                SignIn.timestamp >= start_date,
                SignIn.timestamp <= end_date,
                SignIn.status == "success",
            )
        ).all()

        for signin in signins:
            country = (signin.location_country or "").upper()
            if not country or country in ALLOWED_COUNTRIES:
                continue

            if SOCService._has_vpn_context(signin):
                continue

            anomalies.append({
                "event_type": "vpn-absent",
                "severity": "high",
                "user_principal": signin.user_principal,
                "user_display_name": signin.display_name,
                "user_id": signin.user_id,
                "ip_address": signin.ip_address,
                "country": signin.location_country,
                "city": signin.location_city,
                "app_name": signin.app_name,
                "timestamp": signin.timestamp,
                "reason": "Sign-in from non-allowed country without VPN context",
                "related_signin_id": str(signin.id),
            })

        return anomalies

    @staticmethod
    def detect_atypical_hours(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Détecte les connexions en horaires atypiques."""
        anomalies = []

        signins = db.query(SignIn).filter(
            and_(
                SignIn.timestamp >= start_date,
                SignIn.timestamp <= end_date,
                SignIn.status == "success",
            )
        ).all()

        for signin in signins:
            hour = signin.timestamp.hour
            if BUSINESS_START_HOUR <= hour < BUSINESS_END_HOUR:
                continue

            anomalies.append({
                "event_type": "atypical-hours",
                "severity": "medium",
                "user_principal": signin.user_principal,
                "user_display_name": signin.display_name,
                "user_id": signin.user_id,
                "ip_address": signin.ip_address,
                "country": signin.location_country,
                "city": signin.location_city,
                "app_name": signin.app_name,
                "timestamp": signin.timestamp,
                "reason": f"Sign-in at atypical hour ({hour:02d}:00) outside {BUSINESS_START_HOUR:02d}:00-{BUSINESS_END_HOUR:02d}:00",
                "related_signin_id": str(signin.id),
            })

        return anomalies
    
    @staticmethod
    def correlate_with_incidents(db: Session, anomalies: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """Corrèle les anomalies avec les incidents"""
        
        for anomaly in anomalies:
            # Cherche les incidents liés à cet utilisateur dans une fenêtre de temps
            incident_window_start = anomaly["timestamp"] - timedelta(hours=1)
            incident_window_end = anomaly["timestamp"] + timedelta(hours=1)
            
            related_incident = db.query(Incident).filter(
                and_(
                    # Cherche par titre contenant le user_principal ou la partie avant @
                    Incident.timestamp >= incident_window_start,
                    Incident.timestamp <= incident_window_end
                )
            ).first()
            
            if related_incident:
                anomaly["related_incident_id"] = str(related_incident.id)
                # Augmente la sévérité si un incident est lié
                if anomaly["severity"] != "critical":
                    anomaly["severity"] = "high"
        
        return anomalies
    
    @staticmethod
    def save_anomalies(db: Session, anomalies_data: List[Dict]) -> int:
        """Sauvegarde les anomalies détectées"""
        if not anomalies_data:
            return 0

        deduplicated_anomalies = {}
        for anomaly in anomalies_data:
            anomaly_id = f"{anomaly['event_type']}_{anomaly['user_principal']}_{anomaly['timestamp'].isoformat()}"
            if anomaly_id not in deduplicated_anomalies:
                deduplicated_anomalies[anomaly_id] = anomaly

        anomaly_ids = list(deduplicated_anomalies.keys())
        existing_ids = {
            row[0] for row in db.query(SOCAnomaly.anomaly_id).filter(
                SOCAnomaly.anomaly_id.in_(anomaly_ids)
            ).all()
        }

        pending_objects = []
        for anomaly_id, anomaly in deduplicated_anomalies.items():
            if anomaly_id in existing_ids:
                continue

            pending_objects.append(SOCAnomaly(
                anomaly_id=anomaly_id,
                timestamp=anomaly["timestamp"],
                user_principal=anomaly["user_principal"],
                user_display_name=anomaly.get("user_display_name"),
                user_id=anomaly.get("user_id"),
                event_type=anomaly["event_type"],
                severity=anomaly["severity"],
                ip_address=anomaly.get("ip_address"),
                country=anomaly.get("country"),
                city=anomaly.get("city"),
                app_name=anomaly.get("app_name"),
                reason=anomaly.get("reason"),
                related_signin_id=anomaly.get("related_signin_id"),
                related_incident_id=anomaly.get("related_incident_id"),
                related_risky_user_id=anomaly.get("related_risky_user_id"),
                status="open"
            ))

        if not pending_objects:
            return 0

        try:
            db.add_all(pending_objects)
            db.commit()
            return len(pending_objects)
        except IntegrityError:
            db.rollback()
            logger.warning("Duplicate SOC anomalies detected during commit; retrying inserts individually")

        saved_count = 0
        for soc_anomaly in pending_objects:
            existing = db.query(SOCAnomaly.id).filter(
                SOCAnomaly.anomaly_id == soc_anomaly.anomaly_id
            ).first()
            if existing:
                continue

            try:
                db.add(soc_anomaly)
                db.commit()
                saved_count += 1
            except IntegrityError:
                db.rollback()

        return saved_count
    
    @staticmethod
    def run_analysis(db: Session, period: str = "today", start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Lance l'analyse SOC complète"""
        try:
            start_dt, end_dt = SOCService.get_date_range(period, start_date, end_date)
            
            logger.info(f"Running SOC analysis from {start_dt} to {end_dt}")
            
            # Détecte toutes les anomalies
            anomalies = []
            anomalies.extend(SOCService.detect_out_of_list_countries(db, start_dt, end_dt))
            anomalies.extend(SOCService.detect_risk_user_signins(db, start_dt, end_dt))
            anomalies.extend(SOCService.detect_failed_auth_spikes(db, start_dt, end_dt))
            anomalies.extend(SOCService.detect_concurrent_ips(db, start_dt, end_dt))
            anomalies.extend(SOCService.detect_vpn_absent(db, start_dt, end_dt))
            anomalies.extend(SOCService.detect_atypical_hours(db, start_dt, end_dt))
            
            # Corrèle avec les incidents
            anomalies = SOCService.correlate_with_incidents(db, anomalies, start_dt, end_dt)
            
            # Sauvegarde les anomalies
            saved_count = SOCService.save_anomalies(db, anomalies)
            
            logger.info(f"SOC analysis complete: {saved_count} new anomalies detected")
            
            return {
                "status": "success",
                "period": period,
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "anomalies_detected": len(anomalies),
                "anomalies_saved": saved_count
            }
        except Exception as e:
            logger.error(f"Error during SOC analysis: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def get_executive_summary(db: Session, period: str = "today", start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Récupère le résumé exécutif"""
        start_dt, end_dt = SOCService.get_date_range(period, start_date, end_date)
        
        # Récupère les anomalies
        anomalies = db.query(SOCAnomaly).filter(
            and_(
                SOCAnomaly.timestamp >= start_dt,
                SOCAnomaly.timestamp <= end_dt,
                SOCAnomaly.status != "dismissed"
            )
        ).all()
        
        # Récupère les SignIns
        signins = db.query(SignIn).filter(
            and_(
                SignIn.timestamp >= start_dt,
                SignIn.timestamp <= end_dt
            )
        ).all()
        
        # Calcule les statistiques
        failed_signins = [s for s in signins if s.status == "failure"]
        out_of_list = [a for a in anomalies if a.event_type == "out-of-list"]
        risk_user_events = [a for a in anomalies if a.event_type == "risk-user"]
        fail_spikes = [a for a in anomalies if a.event_type == "fail-spike"]
        concurrent = [a for a in anomalies if a.event_type == "concurrent-ip"]
        
        # Top countries
        countries = {}
        for signin in signins:
            if signin.location_country:
                countries[signin.location_country] = countries.get(signin.location_country, 0) + 1
        
        # Top users
        users = {}
        for signin in signins:
            users[signin.user_principal] = users.get(signin.user_principal, 0) + 1
        
        failed_rate = (len(failed_signins) / len(signins) * 100) if signins else 0
        
        return {
            "period": period,
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "total_anomalies": len(anomalies),
            "critical_count": len([a for a in anomalies if a.severity == "critical"]),
            "high_count": len([a for a in anomalies if a.severity == "high"]),
            "medium_count": len([a for a in anomalies if a.severity == "medium"]),
            "low_count": len([a for a in anomalies if a.severity == "low"]),
            "total_signins": len(signins),
            "failed_signins": len(failed_signins),
            "failed_rate": round(failed_rate, 2),
            "out_of_list_signins": len(out_of_list),
            "out_of_list_countries": list(set([a.country for a in out_of_list if a.country])),
            "risk_users_signins": len(risk_user_events),
            "affected_risk_users": list(set([a.user_principal for a in risk_user_events])),
            "failed_auth_spikes": len(fail_spikes),
            "concurrent_ip_events": len(concurrent),
            "related_incidents": len(set([a.related_incident_id for a in anomalies if a.related_incident_id])),
            "top_countries": dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_users": dict(sorted(users.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    @staticmethod
    def get_anomalies(db: Session, period: str = "today", start_date: Optional[str] = None, end_date: Optional[str] = None, 
                      event_type: Optional[str] = None, severity: Optional[str] = None, status: str = "open", 
                      page: int = 1, page_size: int = 100) -> Dict:
        """Récupère la liste des anomalies avec pagination"""
        start_dt, end_dt = SOCService.get_date_range(period, start_date, end_date)
        
        query = db.query(SOCAnomaly).filter(
            and_(
                SOCAnomaly.timestamp >= start_dt,
                SOCAnomaly.timestamp <= end_dt
            )
        )
        
        if event_type:
            query = query.filter(SOCAnomaly.event_type == event_type)
        if severity:
            query = query.filter(SOCAnomaly.severity == severity)
        if status:
            query = query.filter(SOCAnomaly.status == status)
        
        total = query.count()
        anomalies = query.order_by(SOCAnomaly.timestamp.desc()).offset((page-1)*page_size).limit(page_size).all()
        
        return {
            "items": [a.to_dict() for a in anomalies],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_previous": page > 1,
            "has_next": page < (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def get_user_profile(db: Session, user_principal: str, period: str = "today", 
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Récupère le profil de risque d'un utilisateur"""
        start_dt, end_dt = SOCService.get_date_range(period, start_date, end_date)
        
        # SignIns
        signins = db.query(SignIn).filter(
            and_(
                SignIn.user_principal == user_principal,
                SignIn.timestamp >= start_dt,
                SignIn.timestamp <= end_dt
            )
        ).all()
        
        failed = [s for s in signins if s.status == "failure"]
        failed_rate = (len(failed) / len(signins) * 100) if signins else 0
        
        # Anomalies
        anomalies = db.query(SOCAnomaly).filter(
            and_(
                SOCAnomaly.user_principal == user_principal,
                SOCAnomaly.timestamp >= start_dt,
                SOCAnomaly.timestamp <= end_dt
            )
        ).all()
        
        # RiskyUser
        risky_user = db.query(RiskyUser).filter(
            RiskyUser.user_principal == user_principal
        ).first()
        
        # Incidents
        incidents = db.query(Incident).all()  # Recherche approximative
        
        return {
            "user_principal": user_principal,
            "user_display_name": signins[0].display_name if signins else None,
            "user_id": signins[0].user_id if signins else None,
            "total_signins": len(signins),
            "failed_signins": len(failed),
            "failed_rate": round(failed_rate, 2),
            "countries_accessed": list(set([s.location_country for s in signins if s.location_country])),
            "out_of_list_countries": [s.location_country for s in signins if s.location_country and s.location_country not in ALLOWED_COUNTRIES],
            "apps_accessed": list(set([s.app_name for s in signins if s.app_name])),
            "last_signin": signins[-1].timestamp.isoformat() if signins else None,
            "risk_status": risky_user.risk_state if risky_user else None,
            "risk_level": risky_user.risk_level if risky_user else None,
            "anomalies_count": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies],
            "related_incidents": len([i for i in incidents if i.timestamp >= start_dt and i.timestamp <= end_dt])
        }

"""
Service de requêtes avec pagination
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import Optional

from app.models.signins import SignIn
from app.models.risky_users import RiskyUser
from app.models.incidents import Incident
from app.models.audit_logs_m365 import M365AuditLog, CriticalOperations

logger = logging.getLogger(__name__)


class QueryService:
    """Service pour les requêtes paginées"""
    
    @staticmethod
    def query_signins(
        db: Session,
        filters: dict,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        query = db.query(SignIn)
        
        if filters.get('date_from'):
            query = query.filter(SignIn.timestamp >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(SignIn.timestamp <= filters['date_to'])
        if filters.get('user_principal'):
            query = query.filter(SignIn.user_principal.ilike(f"%{filters['user_principal']}%"))
        if filters.get('status'):
            query = query.filter(SignIn.status == filters['status'])
        if filters.get('ip_address'):
            query = query.filter(SignIn.ip_address.ilike(f"%{filters['ip_address']}%"))
        if filters.get('location_country'):
            query = query.filter(SignIn.location_country.ilike(f"%{filters['location_country']}%"))
        if filters.get('app_name'):
            query = query.filter(SignIn.app_name.ilike(f"%{filters['app_name']}%"))
        
        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(SignIn.timestamp)).offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def query_risky_users(
        db: Session,
        filters: dict,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        query = db.query(RiskyUser)
        
        if filters.get('date_from'):
            query = query.filter(RiskyUser.timestamp >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(RiskyUser.timestamp <= filters['date_to'])
        if filters.get('user_principal'):
            query = query.filter(RiskyUser.user_principal.ilike(f"%{filters['user_principal']}%"))
        if filters.get('risk_level'):
            query = query.filter(RiskyUser.risk_level == filters['risk_level'])
        if filters.get('risk_state'):
            query = query.filter(RiskyUser.risk_state == filters['risk_state'])
        
        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(RiskyUser.timestamp)).offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def query_incidents(
        db: Session,
        filters: dict,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        query = db.query(Incident)
        
        if filters.get('date_from'):
            query = query.filter(Incident.timestamp >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(Incident.timestamp <= filters['date_to'])
        if filters.get('severity'):
            query = query.filter(Incident.severity == filters['severity'])
        if filters.get('status'):
            query = query.filter(Incident.status == filters['status'])
        if filters.get('title_contains'):
            query = query.filter(Incident.title.ilike(f"%{filters['title_contains']}%"))
        if filters.get('assigned_to'):
            query = query.filter(Incident.assigned_to.ilike(f"%{filters['assigned_to']}%"))
        
        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(Incident.timestamp)).offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def query_audit_logs(
        db: Session,
        filters: dict,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list, int]:
        try:
            query = db.query(M365AuditLog)
            
            if filters.get('date_from'):
                query = query.filter(M365AuditLog.timestamp >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(M365AuditLog.timestamp <= filters['date_to'])
            if filters.get('user_principal') and filters['user_principal']:
                try:
                    query = query.filter(M365AuditLog.user_id.ilike(f"%{filters['user_principal']}%"))
                except Exception as e:
                    logger.warning(f"Failed to filter by user_principal: {e}")
            if filters.get('operation') and filters['operation']:
                query = query.filter(M365AuditLog.operation == filters['operation'])
            if filters.get('category') and filters['category']:
                query = query.filter(M365AuditLog.category == filters['category'])
            if filters.get('is_critical'):
                try:
                    query = query.filter(M365AuditLog.operation.in_(CriticalOperations.CRITICAL_LIST))
                except Exception as e:
                    logger.warning(f"Failed to filter by critical operations: {e}")
            
            total = query.count()
            offset = (page - 1) * page_size
            items = query.order_by(desc(M365AuditLog.timestamp)).offset(offset).limit(page_size).all()
            
            return items, total
        except Exception as e:
            print(f"query_audit_logs error: {e}")
            return [], 0
    
    @staticmethod
    def get_kpis(db: Session, days: int = 30) -> dict:
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        try:
            total_signins = db.query(SignIn).filter(SignIn.timestamp >= since).count()
        except Exception as e:
            logger.error(f"Failed to query total_signins: {e}")
            total_signins = 0
        
        try:
            failed_signins = db.query(SignIn).filter(
                SignIn.timestamp >= since, 
                SignIn.status == "failure"
            ).count()
        except Exception as e:
            logger.error(f"Failed to query failed_signins: {e}")
            failed_signins = 0
        
        try:
            total_risky = db.query(RiskyUser).filter(
                RiskyUser.timestamp >= since,
                RiskyUser.risk_state != "confirmedSafe"
            ).count()
        except Exception as e:
            logger.error(f"Failed to query total_risky: {e}")
            total_risky = 0
        
        try:
            open_incidents = db.query(Incident).filter(
                Incident.status.in_(["new", "active"])
            ).count()
        except Exception as e:
            logger.error(f"Failed to query open_incidents: {e}")
            open_incidents = 0
        
        try:
            critical_ops = db.query(M365AuditLog).filter(
                M365AuditLog.timestamp >= since
            ).count()
        except Exception as e:
            logger.error(f"Failed to query critical_ops: {e}")
            critical_ops = 0
        
        return {
            "total_signins": total_signins,
            "failed_signins": failed_signins,
            "success_rate": round((total_signins - failed_signins) / total_signins * 100, 1) if total_signins > 0 else 100,
            "total_risky_users": total_risky,
            "open_incidents": open_incidents,
            "critical_operations": critical_ops
        }
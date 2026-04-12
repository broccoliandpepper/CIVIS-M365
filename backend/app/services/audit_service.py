"""
Service d'audit trail
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, AuditActions


class AuditService:
    @staticmethod
    def log_action(db: Session, username: str, action: str, status: str,
                  resource_type: str = None, resource_id: str = None,
                  details: dict = None, ip_address: str = None, error: str = None):
        audit = AuditLog(
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            error_message=error
        )
        
        if details:
            audit.set_details(details)
        
        db.add(audit)
        db.commit()
        return audit
    
    @staticmethod
    def get_audit_logs(db: Session, limit: int = 100, offset: int = 0,
                      action: str = None, username: str = None,
                      status: str = None) -> list:
        query = db.query(AuditLog)
        
        if action:
            query = query.filter(AuditLog.action == action)
        if username:
            query = query.filter(AuditLog.username == username)
        if status:
            query = query.filter(AuditLog.status == status)
        
        query = query.order_by(AuditLog.timestamp.desc())
        
        return query.offset(offset).limit(limit).all()
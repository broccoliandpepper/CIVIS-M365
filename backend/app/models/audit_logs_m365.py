"""
Modèle pour Unified Audit Log (UAL) M365
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

from app.database import Base


class M365AuditLog(Base):
    __tablename__ = "audit_logs_m365"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # M365 fields
    record_type = Column(String(50), nullable=True)
    category = Column(String(100), index=True, nullable=True)
    operation = Column(String(100), index=True, nullable=False)
    result = Column(String(50), nullable=True)
    result_reason = Column(String(255), nullable=True)
    
    user_id = Column(String(255), index=True, nullable=True)
    user_principal = Column(String(255), index=True, nullable=True)
    user_type = Column(String(50), nullable=True)

    ip_address = Column(String(45), nullable=True)
    client_ip = Column(String(45), nullable=True)
    client_info = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country_or_region = Column(String(10), nullable=True)
    workload = Column(String(100), nullable=True)

    target_id = Column(String(255), nullable=True)
    target_type = Column(String(50), nullable=True)
    target_display_name = Column(String(255), nullable=True)
    target_resource = Column(String(255), nullable=True)
    raw_json = Column(Text, nullable=True)

    user_agent = Column(String(255), nullable=True)
    initiated_by = Column(String(255), nullable=True)
    correlation_id = Column(String(100), nullable=True)

    # Aliases pour compatibilite
    @property
    def location_city(self):
        return self.city
    
    @property
    def location_country(self):
        return self.country_or_region
    
    @property
    def target_name(self):
        return self.target_display_name
    
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_operation_timestamp', 'operation', 'timestamp'),
        Index('idx_audit_category', 'category', 'timestamp'),
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "record_type": self.record_type,
            "category": self.category,
            "operation": self.operation,
            "result": self.result,
            "result_reason": self.result_reason,
            "user_id": self.user_id,
            "user_principal": self.user_principal,
            "user_type": self.user_type,
            "ip_address": self.ip_address,
            "client_ip": self.client_ip,
            "client_info": self.client_info,
            "city": self.city,
            "country_or_region": self.country_or_region,
            "workload": self.workload,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "target_display_name": self.target_display_name,
            "target_resource": self.target_resource,
            "user_agent": self.user_agent,
            "initiated_by": self.initiated_by,
            "correlation_id": self.correlation_id,
            # Aliases
            "target_name": self.target_display_name,
            "location_city": self.city,
            "location_country": self.country_or_region
        }


class CriticalOperations:
    """Opérations critiques à surveiller pour SOC"""
    
    MAIL_FORWARDING = "New-InboxRule"
    PERMISSION_CHANGE = "Add member to group"
    SHARING_EXTERNAL = "SharingInvitationCreated"
    ADMIN_ROLE_CHANGE = "Add member to role"
    APP_REGISTRATION = "Register application"
    MAILBOX_ACCESS = "MailItemsAccessed"
    HARD_DELETE = "HardDelete"
    EXPORT_DOWNLOAD = "FileDownloaded"
    
    CRITICAL_LIST = [
        MAIL_FORWARDING,
        PERMISSION_CHANGE,
        SHARING_EXTERNAL,
        ADMIN_ROLE_CHANGE,
        APP_REGISTRATION,
        MAILBOX_ACCESS,
        HARD_DELETE,
        EXPORT_DOWNLOAD
    ]
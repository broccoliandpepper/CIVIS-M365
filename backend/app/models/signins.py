"""
Modèle pour les logs de connexion (SignIns)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

from app.database import Base


class SignIn(Base):
    __tablename__ = "signins"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user_principal = Column(String(255), index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    user_id = Column(String(100), nullable=True)
    user_type = Column(String(50), nullable=True)
    
    ip_address = Column(String(45), index=True, nullable=True)
    location_city = Column(String(100), nullable=True)
    location_country = Column(String(100), nullable=True)
    location_state = Column(String(100), nullable=True)
    
    status = Column(String(50), index=True, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    error_code = Column(String(50), nullable=True)
    
    correlation_id = Column(String(100), nullable=True)
    conditional_access_status = Column(String(50), nullable=True)
    
    mfa_status = Column(String(50), nullable=True)
    auth_method = Column(String(100), nullable=True)
    auth_requirement = Column(String(100), nullable=True)
    
    app_name = Column(String(255), index=True, nullable=True)
    app_id = Column(String(100), nullable=True)
    client_app = Column(String(100), nullable=True)
    
    device_os = Column(String(100), nullable=True)
    device_browser = Column(String(100), nullable=True)
    device_is_compliant = Column(String(10), nullable=True)
    device_is_managed = Column(String(10), nullable=True)
    
    risk_detail = Column(String(50), nullable=True)
    risk_state = Column(String(50), nullable=True)
    risk_level = Column(String(50), nullable=True)
    
    flagged_for_review = Column(String(10), nullable=True)
    
    raw_json = Column(Text, nullable=False)
    
    __table_args__ = (
        Index('idx_signins_user_timestamp', 'user_principal', 'timestamp'),
        Index('idx_signins_status_timestamp', 'status', 'timestamp'),
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_principal": self.user_principal,
            "display_name": self.display_name,
            "user_id": self.user_id,
            "user_type": self.user_type,
            "ip_address": self.ip_address,
            "location_city": self.location_city,
            "location_country": self.location_country,
            "location_state": self.location_state,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "error_code": self.error_code,
            "correlation_id": self.correlation_id,
            "conditional_access_status": self.conditional_access_status,
            "mfa_status": self.mfa_status,
            "auth_method": self.auth_method,
            "auth_requirement": self.auth_requirement,
            "app_name": self.app_name,
            "app_id": self.app_id,
            "client_app": self.client_app,
            "device_os": self.device_os,
            "device_browser": self.device_browser,
            "device_is_compliant": self.device_is_compliant,
            "device_is_managed": self.device_is_managed,
            "risk_detail": self.risk_detail,
            "risk_state": self.risk_state,
            "risk_level": self.risk_level,
            "flagged_for_review": self.flagged_for_review
        }
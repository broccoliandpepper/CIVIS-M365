"""
Modèle pour les utilisateurs à risque (Risky Users)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

from app.database import Base


class RiskyUser(Base):
    __tablename__ = "risky_users"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user_principal = Column(String(255), index=True, nullable=False)
    user_id = Column(String(100), nullable=True)
    user_display_name = Column(String(255), nullable=True)
    
    risk_level = Column(String(20), index=True, nullable=False)
    risk_state = Column(String(50), index=True, nullable=True)
    risk_detail = Column(String(255), nullable=True)
    risk_last_updated = Column(DateTime, nullable=True)
    
    is_deleted = Column(String(10), nullable=True)
    is_processing = Column(String(10), nullable=True)
    
    detection_type = Column(String(100), index=True, nullable=True)
    detection_timing = Column(String(50), nullable=True)
    
    raw_json = Column(Text, nullable=False)
    
    __table_args__ = (
        Index('idx_risky_user_timestamp', 'user_principal', 'timestamp'),
        Index('idx_risky_level_timestamp', 'risk_level', 'timestamp'),
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_principal": self.user_principal,
            "user_id": self.user_id,
            "user_display_name": self.user_display_name,
            "risk_level": self.risk_level,
            "risk_state": self.risk_state,
            "risk_detail": self.risk_detail,
            "risk_last_updated": self.risk_last_updated.isoformat() if self.risk_last_updated else None,
            "is_deleted": self.is_deleted,
            "is_processing": self.is_processing,
            "detection_type": self.detection_type
        }
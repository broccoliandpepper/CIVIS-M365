"""
Modèle pour l'analyse SOC et la corrélation des données
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from datetime import datetime

from app.database import Base


class SOCAnomaly(Base):
    __tablename__ = "soc_anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # User information
    user_principal = Column(String(255), index=True, nullable=False)
    user_display_name = Column(String(255), nullable=True)
    user_id = Column(String(100), nullable=True)
    
    # Event details
    event_type = Column(String(50), index=True, nullable=False)  # "out-of-list", "risk-user", "fail-spike", "concurrent-ip"
    severity = Column(String(20), index=True, nullable=False)  # "critical", "high", "medium", "low"
    
    # Geographic/IP info
    ip_address = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Context
    app_name = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    
    # Correlation
    related_signin_id = Column(String(100), nullable=True)
    related_incident_id = Column(String(100), nullable=True)
    related_risky_user_id = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(50), default="open", nullable=False)  # "open", "investigating", "resolved", "dismissed"
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_soc_timestamp_severity', 'timestamp', 'severity'),
        Index('idx_soc_user_event', 'user_principal', 'event_type'),
        Index('idx_soc_status', 'status', 'timestamp'),
        Index('idx_soc_country', 'country', 'timestamp'),
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "anomaly_id": self.anomaly_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_principal": self.user_principal,
            "user_display_name": self.user_display_name,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "ip_address": self.ip_address,
            "country": self.country,
            "city": self.city,
            "app_name": self.app_name,
            "reason": self.reason,
            "related_signin_id": self.related_signin_id,
            "related_incident_id": self.related_incident_id,
            "related_risky_user_id": self.related_risky_user_id,
            "status": self.status,
            "notes": self.notes,
        }


class SOCMetric(Base):
    __tablename__ = "soc_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    
    total_signins = Column(Integer, default=0)
    failed_signins = Column(Integer, default=0)
    out_of_list_signins = Column(Integer, default=0)
    risk_user_signins = Column(Integer, default=0)
    concurrent_ip_events = Column(Integer, default=0)
    failed_auth_spikes = Column(Integer, default=0)
    
    unique_users = Column(Integer, default=0)
    unique_countries = Column(Integer, default=0)
    out_of_list_countries = Column(Integer, default=0)
    
    critical_anomalies = Column(Integer, default=0)
    high_anomalies = Column(Integer, default=0)
    medium_anomalies = Column(Integer, default=0)
    low_anomalies = Column(Integer, default=0)
    
    related_incidents = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_metric_date', 'metric_date'),
    )
    
    def to_dict(self) -> dict:
        return {
            "metric_date": self.metric_date,
            "total_signins": self.total_signins,
            "failed_signins": self.failed_signins,
            "out_of_list_signins": self.out_of_list_signins,
            "risk_user_signins": self.risk_user_signins,
            "concurrent_ip_events": self.concurrent_ip_events,
            "failed_auth_spikes": self.failed_auth_spikes,
            "unique_users": self.unique_users,
            "unique_countries": self.unique_countries,
            "out_of_list_countries": self.out_of_list_countries,
            "critical_anomalies": self.critical_anomalies,
            "high_anomalies": self.high_anomalies,
            "medium_anomalies": self.medium_anomalies,
            "low_anomalies": self.low_anomalies,
            "related_incidents": self.related_incidents,
        }

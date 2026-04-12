"""
Modèle pour les incidents Defender
"""

import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    title = Column(String(500), nullable=False)
    severity = Column(String(20), index=True, nullable=False)
    status = Column(String(20), index=True, nullable=False)
    
    assigned_to = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    priority_score = Column(String(50), nullable=True)
    tags = Column(String(255), nullable=True)
    investigation_state = Column(String(100), nullable=True)
    impacted_assets = Column(String(255), nullable=True)
    active_alerts = Column(String(50), nullable=True)
    service_sources = Column(String(255), nullable=True)
    detection_sources = Column(String(255), nullable=True)
    last_update_time = Column(String(100), nullable=True)
    last_activity = Column(String(100), nullable=True)
    policy_name = Column(String(255), nullable=True)
    data_sensitivity = Column(String(100), nullable=True)
    classification = Column(String(100), nullable=True)
    determination = Column(String(100), nullable=True)
    device_groups = Column(String(255), nullable=True)
    creation_time = Column(String(100), nullable=True)
    workspaces = Column(String(255), nullable=True)
    cloud_scopes = Column(String(255), nullable=True)
    
    description = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=False)
    
    __table_args__ = (
        Index('idx_incidents_status_severity', 'status', 'severity'),
        Index('idx_incidents_timestamp', 'timestamp'),
    )
    
    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "category": self.category,
            "priority_score": self.priority_score,
            "tags": self.tags,
            "investigation_state": self.investigation_state,
            "impacted_assets": self.impacted_assets,
            "active_alerts": self.active_alerts,
            "service_sources": self.service_sources,
            "detection_sources": self.detection_sources,
            "last_update_time": self.last_update_time,
            "last_activity": self.last_activity,
            "policy_name": self.policy_name,
            "data_sensitivity": self.data_sensitivity,
            "classification": self.classification,
            "determination": self.determination,
            "device_groups": self.device_groups,
            "creation_time": self.creation_time,
            "workspaces": self.workspaces,
            "cloud_scopes": self.cloud_scopes
        }
        try:
            raw = json.loads(self.raw_json) if self.raw_json else {}
        except Exception:
            raw = {}

        for raw_key, raw_value in raw.items():
            if raw_value is None:
                continue
            normalized_key = raw_key.strip().lower().replace(' ', '_')
            if normalized_key not in result:
                result[normalized_key] = raw_value

        return result
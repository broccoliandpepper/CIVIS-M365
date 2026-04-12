"""
Modèle pour les logs du cycle de vie des données
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime

from app.database import Base


class LifecycleLog(Base):
    __tablename__ = "lifecycle_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    
    source_db = Column(String(50), nullable=True)
    target_db = Column(String(50), nullable=True)
    
    records_processed = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    
    error_message = Column(Text, nullable=True)
    rollback_performed = Column(Boolean, default=False, nullable=False)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    created_by = Column(String(50), nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "operation": self.operation,
            "status": self.status,
            "source_db": self.source_db,
            "target_db": self.target_db,
            "records_processed": self.records_processed,
            "records_failed": self.records_failed,
            "error_message": self.error_message,
            "rollback_performed": self.rollback_performed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
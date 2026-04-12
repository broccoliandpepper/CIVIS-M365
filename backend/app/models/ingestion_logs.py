"""
Modèle pour les logs d'ingestion
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database import Base


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    source_type = Column(String(50), index=True, nullable=False)
    uploaded_by = Column(String(50), nullable=False)
    status = Column(String(20), default="processing", nullable=False)
    
    lines_total = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_duplicate = Column(Integer, default=0)
    lines_error = Column(Integer, default=0)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String(500), nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "source_type": self.source_type,
            "status": self.status,
            "lines_total": self.lines_total,
            "lines_added": self.lines_added,
            "lines_duplicate": self.lines_duplicate,
            "lines_error": self.lines_error,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
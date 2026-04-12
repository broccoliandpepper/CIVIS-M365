"""
Modèle pour la Liste de Vérité (Truth List)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.database import Base


class TruthListUser(Base):
    __tablename__ = "truth_list"
    
    id = Column(Integer, primary_key=True, index=True)
    user_principal = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
    
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    imported_by = Column(String(50), nullable=False)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_principal": self.user_principal,
            "display_name": self.display_name,
            "department": self.department,
            "job_title": self.job_title,
            "is_active": self.is_active,
            "notes": self.notes,
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
            "imported_by": self.imported_by
        }
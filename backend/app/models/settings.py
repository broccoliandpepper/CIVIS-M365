"""
Modeles de configuration
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database import Base


class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(50), nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by
        }
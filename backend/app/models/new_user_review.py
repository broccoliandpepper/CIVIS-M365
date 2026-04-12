"""
Modèle de revue des nouveaux utilisateurs détectés hors Truth List.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class NewUserReview(Base):
    __tablename__ = "new_user_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_principal = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    reviewed_by = Column(String(50), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_principal": self.user_principal,
            "display_name": self.display_name,
            "status": self.status,
            "notes": self.notes,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
"""
Modèle pour le manifest des backups Archive
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger
from datetime import datetime

from app.database import Base


class ArchiveManifest(Base):
    __tablename__ = "archive_manifest"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(String(100), unique=True, index=True, nullable=False)
    backup_filename = Column(String(255), nullable=False)
    backup_filepath = Column(String(500), nullable=False)
    
    period_from = Column(DateTime, nullable=False)
    period_to = Column(DateTime, nullable=False)
    
    record_count_signins = Column(BigInteger, default=0, nullable=False)
    record_count_risky = Column(BigInteger, default=0, nullable=False)
    record_count_incidents = Column(BigInteger, default=0, nullable=False)
    record_count_audit = Column(BigInteger, default=0, nullable=False)
    total_records = Column(BigInteger, default=0, nullable=False)
    
    file_size_bytes = Column(BigInteger, nullable=False)
    md5_checksum = Column(String(32), nullable=False)
    
    is_encrypted = Column(Boolean, default=True, nullable=False)
    encryption_method = Column(String(50), default="Fernet", nullable=False)
    
    status = Column(String(20), default="created", nullable=False)
    archive_cleanup_completed = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    created_by = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "backup_id": self.backup_id,
            "backup_filename": self.backup_filename,
            "period_from": self.period_from.isoformat() if self.period_from else None,
            "period_to": self.period_to.isoformat() if self.period_to else None,
            "record_counts": {
                "signins": self.record_count_signins,
                "risky_users": self.record_count_risky,
                "incidents": self.record_count_incidents,
                "audit_logs": self.record_count_audit,
                "total": self.total_records
            },
            "file_size_bytes": self.file_size_bytes,
            "md5_checksum": self.md5_checksum,
            "is_encrypted": self.is_encrypted,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "archive_cleanup_completed": self.archive_cleanup_completed
        }
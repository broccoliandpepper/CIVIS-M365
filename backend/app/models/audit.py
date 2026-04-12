"""
Modeles d'audit trail
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def set_details(self, data: dict):
        self.details = json.dumps(data, ensure_ascii=False)
    
    def get_details(self) -> dict:
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.get_details(),
            "ip_address": self.ip_address,
            "status": self.status,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class AuditActions:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETE = "DATA_DELETE"
    BACKUP_CREATED = "BACKUP_CREATED"
    BACKUP_ACCESSED = "BACKUP_ACCESSED"
    USER_CREATED = "USER_CREATED"
    USER_MODIFIED = "USER_MODIFIED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    ARCHIVE_MOVED = "ARCHIVE_MOVED"
    ARCHIVE_BACKUP = "ARCHIVE_BACKUP"
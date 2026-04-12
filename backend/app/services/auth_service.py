"""
Service d'authentification
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.audit import AuditLog, AuditActions
from app.security import create_access_token, validate_password_strength


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not user.is_active or user.is_locked:
            return None
        
        if not user.verify_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
            db.commit()
            return None
        
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_user(db: Session, username: str, password: str, email: str = None, role: str = "viewer") -> User:
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)
        
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("Username already exists")
        
        user = User(username=username, email=email, role=role, is_active=True)
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_password(db: Session, user: User, new_password: str):
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)
        
        user.set_password(new_password)
        db.commit()
        return user
    
    @staticmethod
    def create_token(user: User) -> str:
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
        return create_access_token(data=token_data)
    
    @staticmethod
    def log_auth_event(db: Session, username: str, action: str, status: str, 
                       ip_address: str = None, details: dict = None, error: str = None):
        audit = AuditLog(
            username=username,
            action=action,
            status=status,
            ip_address=ip_address,
            error_message=error
        )
        if details:
            audit.set_details(details)
        
        db.add(audit)
        db.commit()
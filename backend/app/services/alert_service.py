"""
Service d'alertes - Détection nouveaux users
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models.truth_list import TruthListUser
from app.models.signins import SignIn


class AlertService:
    """Service pour les alertes de sécurité"""
    
    @staticmethod
    def is_known_user(db: Session, user_principal: str) -> bool:
        """Vérifie si un utilisateur est dans la Truth List"""
        user = db.query(TruthListUser).filter(
            TruthListUser.user_principal == user_principal,
            TruthListUser.is_active == True
        ).first()
        return user is not None
    
    @staticmethod
    def get_unknown_signins(db: Session, limit: int = 100) -> list:
        """Récupère les connexions d'utilisateurs non autorisés"""
        users = db.query(TruthListUser.user_principal).filter(
            TruthListUser.is_active == True
        ).all()
        known_users = [u.user_principal for u in users]
        
        if known_users:
            return db.query(SignIn).filter(
                SignIn.user_principal.notin_(known_users)
            ).order_by(SignIn.timestamp.desc()).limit(limit).all()
        return db.query(SignIn).order_by(SignIn.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_risky_users_not_in_list(db: Session, limit: int = 100) -> list:
        """Récupère les Risky Users non dans la Truth List"""
        from app.models.risky_users import RiskyUser
        
        known_users = [u.user_principal for u in db.query(TruthListUser.user_principal).all()]
        
        return db.query(RiskyUser).filter(
            RiskyUser.user_principal.notin_(known_users) if known_users else True,
            RiskyUser.risk_state != "confirmedSafe"
        ).order_by(RiskyUser.timestamp.desc()).limit(limit).all()
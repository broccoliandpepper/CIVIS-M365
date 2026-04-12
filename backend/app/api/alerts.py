"""
Endpoints d'alertes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db_hot, get_db_config
from app.services.alert_service import AlertService
from app.models.auth import User
from app.api.auth import get_current_user


router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.get("/unknown-users")
async def get_unknown_users(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Récupère les utilisateurs non autorisés (hors Truth List)"""
    unknown = AlertService.get_unknown_signins(db, limit)
    return {
        "count": len(unknown),
        "users": [s.to_dict() for s in unknown]
    }


@router.get("/risky-unknown")
async def get_risky_unknown(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Récupère les Risky Users non dans la Truth List"""
    users = AlertService.get_risky_users_not_in_list(db, limit)
    return {
        "count": len(users),
        "users": [u.to_dict() for u in users]
    }


@router.get("/check-user/{user_principal}")
async def check_user(
    user_principal: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Vérifie si un utilisateur est connu"""
    is_known = AlertService.is_known_user(db, user_principal)
    return {
        "user_principal": user_principal,
        "is_known": is_known
    }
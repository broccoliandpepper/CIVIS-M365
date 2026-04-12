"""
Endpoints d'alertes
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db_hot
from app.services.alert_service import AlertService
from app.models.auth import User
from app.api.auth import get_current_user, require_admin


router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.get("/unknown-users")
async def get_unknown_users(
    limit: int = 100,
    include_reviewed: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Récupère les utilisateurs non autorisés (hors Truth List)"""
    unknown = AlertService.get_unknown_signins(db, limit, include_reviewed)
    return {
        "count": len(unknown),
        "items": unknown,
        "users": unknown
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


class ReviewUnknownUserRequest(BaseModel):
    notes: str | None = None


@router.post("/unknown-users/{user_principal}/approve")
async def approve_unknown_user(
    user_principal: str,
    request: ReviewUnknownUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_hot)
):
    try:
        return AlertService.approve_unknown_user(db, user_principal, current_user.username, request.notes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/unknown-users/{user_principal}/reject")
async def reject_unknown_user(
    user_principal: str,
    request: ReviewUnknownUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_hot)
):
    try:
        return AlertService.reject_unknown_user(db, user_principal, current_user.username, request.notes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
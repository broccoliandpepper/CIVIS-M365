"""
Endpoints d'authentification
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db_config
from app.services.auth_service import AuthService
from app.models.auth import User
from app.config import settings


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), 
                           db: Session = Depends(get_db_config)) -> User:
    from app.security import decode_access_token
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


@router.post("/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
              db: Session = Depends(get_db_config)):
    ip_address = request.client.host if request.client else "unknown"
    
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        AuthService.log_auth_event(
            db=db,
            username=form_data.username,
            action="LOGIN_FAILURE",
            status="FAILURE",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_token(user)
    
    AuthService.log_auth_event(
        db=db,
        username=user.username,
        action="LOGIN_SUCCESS",
        status="SUCCESS",
        ip_address=ip_address,
        details={"user_id": user.id, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user": user.to_dict()
    }


@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db_config)):
    ip_address = request.client.host if request.client else "unknown"
    
    AuthService.log_auth_event(
        db=db,
        username=current_user.username,
        action="LOGOUT",
        status="SUCCESS",
        ip_address=ip_address
    )
    
    return {"status": "logged_out"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_config)
):
    """Changer le mot de passe"""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user.verify_password(request.current_password):
        raise HTTPException(
            status_code=400,
            detail="Mot de passe actuel incorrect"
        )
    
    if len(request.new_password) < 12:
        raise HTTPException(
            status_code=400,
            detail="Le nouveau mot de passe doit faire au moins 12 caractères"
        )
    
    user.set_password(request.new_password)
    db.commit()
    
    return {"status": "password_changed", "message": "Mot de passe changé avec succès"}


from typing import List

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = None
    role: str = "viewer"

@router.post("/register")
async def register(
    request: RegisterRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Créer un nouvel utilisateur (admin only)"""
    try:
        user = AuthService.create_user(db, request.username, request.password, request.email, request.role)
        return {"status": "created", "user_id": user.id, "username": request.username}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[dict])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Liste tous les utilisateurs (admin only)"""
    users = db.query(User).all()
    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]


class ResetPasswordRequest(BaseModel):
    user_id: int
    new_password: str


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Reset le mot de passe d'un utilisateur (admin only)"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    AuthService.update_password(db, user, request.new_password)
    return {"status": "password_reset", "username": user.username}


class ToggleUserRequest(BaseModel):
    user_id: int
    is_active: bool


class UpdateUserRoleRequest(BaseModel):
    user_id: int
    role: str


@router.post("/toggle-user")
async def toggle_user(
    request: ToggleUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Active/désactive un utilisateur (admin only)"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.is_active = request.is_active
    db.commit()
    return {"status": "toggled", "username": user.username, "is_active": user.is_active}


@router.post("/update-role")
async def update_user_role(
    request: UpdateUserRoleRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_config)
):
    """Met à jour le rôle d'un utilisateur (admin only)"""
    if request.role not in {"admin", "viewer"}:
        raise HTTPException(status_code=400, detail="Role invalide")

    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if user.id == current_user.id and request.role != current_user.role:
        raise HTTPException(status_code=400, detail="Tu ne peux pas modifier ton propre role")

    user.role = request.role
    db.commit()
    return {"status": "role_updated", "username": user.username, "role": user.role}
"""
Endpoints pour effacer les données
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db_hot
from app.api.auth import get_current_user
from app.models.auth import User


router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

logger = logging.getLogger(__name__)


class ClearDBRequest(BaseModel):
    source_type: str


def clear_data_dep(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.post("/clear-data")
async def clear_database(
    request: ClearDBRequest,
    current_user: User = Depends(clear_data_dep),
    db: Session = Depends(get_db_hot)
):
    from app.models.signins import SignIn
    from app.models.risky_users import RiskyUser
    from app.models.incidents import Incident
    from app.models.truth_list import TruthListUser
    from app.models.audit_logs_m365 import M365AuditLog
    
    source = request.source_type
    deleted = 0
    
    try:
        if source == "signins":
            deleted = db.query(SignIn).delete()
        elif source == "risky_users":
            deleted = db.query(RiskyUser).delete()
        elif source == "incidents":
            deleted = db.query(Incident).delete()
        elif source == "truth_list":
            deleted = db.query(TruthListUser).delete()
        elif source == "audit_logs":
            deleted = db.query(M365AuditLog).delete()
        else:
            raise HTTPException(status_code=400, detail="Type invalide")
        
        db.commit()
        logger.info(f"User {current_user.username} cleared {deleted} records from {source}")
        return {"status": "cleared", "source_type": source, "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error: " + str(e))
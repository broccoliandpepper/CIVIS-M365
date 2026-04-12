"""
Endpoints de requêtes avec pagination
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db_hot
from app.services.query_service import QueryService
from app.schemas.query import PaginatedResponse
from app.models.auth import User
from app.api.auth import get_current_user
from datetime import datetime


router = APIRouter(prefix="/api/v1/query", tags=["Query"])


@router.get("/signins")
async def query_signins(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    user_principal: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    app_name: Optional[str] = Query(None),
    location_country: Optional[str] = Query(None),
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Recherche SignIns avec filtres et pagination"""
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "user_principal": user_principal,
        "ip_address": ip_address,
        "status": status,
        "app_name": app_name,
        "location_country": location_country
    }
    items, total = QueryService.query_signins(db, filters, page, page_size)
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [i.to_dict() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


@router.get("/risky-users")
async def query_risky_users(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    user_principal: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    risk_state: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Recherche Risky Users avec filtres"""
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "user_principal": user_principal,
        "risk_level": risk_level,
        "risk_state": risk_state
    }
    items, total = QueryService.query_risky_users(db, filters, page, page_size)
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [i.to_dict() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


@router.get("/incidents")
async def query_incidents(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    title_contains: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Recherche Incidents avec filtres"""
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "severity": severity,
        "status": status,
        "title_contains": title_contains
    }
    items, total = QueryService.query_incidents(db, filters, page, page_size)
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [i.to_dict() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


@router.get("/audit-logs")
async def query_audit_logs(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    user_principal: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    workload: Optional[str] = Query(None),
    is_critical: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Recherche Audit Logs M365 avec filtres"""
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "user_principal": user_principal,
        "operation": operation,
        "workload": workload,
        "is_critical": is_critical
    }
    items, total = QueryService.query_audit_logs(db, filters, page, page_size)
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [i.to_dict() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


@router.get("/truth-list")
async def query_truth_list(
    user_principal: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """Recherche Truth List avec filtres"""
    from app.models.truth_list import TruthListUser
    from sqlalchemy import func
    
    query = db.query(TruthListUser)
    
    if user_principal:
        query = query.filter(TruthListUser.user_principal.ilike(f"%{user_principal}%"))
    if department:
        query = query.filter(TruthListUser.department.ilike(f"%{department}%"))
    if is_active is not None:
        query = query.filter(TruthListUser.is_active == is_active)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": [i.to_dict() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


@router.get("/kpis")
async def get_kpis(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_hot)
):
    """KPIs du dashboard"""
    return QueryService.get_kpis(db, days)
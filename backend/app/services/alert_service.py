"""
Service d'alertes - Détection nouveaux users
"""

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.new_user_review import NewUserReview
from app.models.truth_list import TruthListUser
from app.models.signins import SignIn


class AlertService:
    """Service pour les alertes de sécurité"""

    @staticmethod
    def _normalize_user(user_principal: str) -> str:
        return (user_principal or "").strip().lower()
    
    @staticmethod
    def is_known_user(db: Session, user_principal: str) -> bool:
        """Vérifie si un utilisateur est dans la Truth List"""
        normalized = AlertService._normalize_user(user_principal)
        user = db.query(TruthListUser).filter(
            func.lower(TruthListUser.user_principal) == normalized,
            TruthListUser.is_active == True
        ).first()
        return user is not None
    
    @staticmethod
    def get_unknown_signins(db: Session, limit: int = 100, include_reviewed: bool = False) -> list[dict]:
        """Récupère les utilisateurs hors Truth List, agrégés par user principal."""
        users = db.query(TruthListUser.user_principal).filter(
            TruthListUser.is_active == True
        ).all()
        known_users = {AlertService._normalize_user(u.user_principal) for u in users}

        signins = db.query(SignIn).order_by(SignIn.timestamp.desc()).limit(max(limit * 25, 250)).all()
        reviews = {
            AlertService._normalize_user(review.user_principal): review
            for review in db.query(NewUserReview).all()
        }

        aggregated: list[dict] = []
        indexed: dict[str, dict] = {}
        for signin in signins:
            normalized = AlertService._normalize_user(signin.user_principal)
            if not normalized or normalized in known_users:
                continue

            review = reviews.get(normalized)
            review_status = review.status if review else "pending"
            if not include_reviewed and review_status in {"approved", "rejected"}:
                continue

            if normalized not in indexed:
                item = {
                    "user_principal": normalized,
                    "display_name": signin.display_name,
                    "first_seen": signin.timestamp.isoformat() if signin.timestamp else None,
                    "last_seen": signin.timestamp.isoformat() if signin.timestamp else None,
                    "latest_ip": signin.ip_address,
                    "event_count": 1,
                    "status": review_status,
                    "notes": review.notes if review else None,
                    "reviewed_by": review.reviewed_by if review else None,
                    "reviewed_at": review.reviewed_at.isoformat() if review and review.reviewed_at else None,
                }
                aggregated.append(item)
                indexed[normalized] = item
            else:
                current = indexed[normalized]
                current["event_count"] += 1
                current["first_seen"] = signin.timestamp.isoformat() if signin.timestamp else current["first_seen"]

        return aggregated[:limit]
    
    @staticmethod
    def get_risky_users_not_in_list(db: Session, limit: int = 100) -> list:
        """Récupère les Risky Users non dans la Truth List"""
        from app.models.risky_users import RiskyUser
        
        known_users = [u.user_principal for u in db.query(TruthListUser.user_principal).all()]
        
        return db.query(RiskyUser).filter(
            RiskyUser.user_principal.notin_(known_users) if known_users else True,
            RiskyUser.risk_state != "confirmedSafe"
        ).order_by(RiskyUser.timestamp.desc()).limit(limit).all()

    @staticmethod
    def approve_unknown_user(db: Session, user_principal: str, reviewed_by: str, notes: str | None = None) -> dict:
        normalized = AlertService._normalize_user(user_principal)
        latest_signin = db.query(SignIn).filter(
            func.lower(SignIn.user_principal) == normalized
        ).order_by(SignIn.timestamp.desc()).first()

        if latest_signin is None:
            raise ValueError("Utilisateur introuvable dans les SignIns")

        truth_user = db.query(TruthListUser).filter(
            func.lower(TruthListUser.user_principal) == normalized
        ).first()
        if truth_user is None:
            truth_user = TruthListUser(
                user_principal=normalized,
                display_name=latest_signin.display_name,
                is_active=True,
                notes=notes or "Approved from alerts workflow",
                imported_by=reviewed_by,
            )
            db.add(truth_user)
        else:
            truth_user.is_active = True
            truth_user.display_name = truth_user.display_name or latest_signin.display_name
            truth_user.notes = notes or truth_user.notes

        review = db.query(NewUserReview).filter(
            func.lower(NewUserReview.user_principal) == normalized
        ).first()
        if review is None:
            review = NewUserReview(user_principal=normalized)
            db.add(review)

        review.display_name = latest_signin.display_name
        review.status = "approved"
        review.notes = notes
        review.first_seen = review.first_seen or latest_signin.timestamp
        review.last_seen = latest_signin.timestamp
        review.reviewed_by = reviewed_by
        review.reviewed_at = datetime.utcnow()

        db.commit()
        return {"status": "approved", "user_principal": normalized}

    @staticmethod
    def reject_unknown_user(db: Session, user_principal: str, reviewed_by: str, notes: str | None = None) -> dict:
        normalized = AlertService._normalize_user(user_principal)
        latest_signin = db.query(SignIn).filter(
            func.lower(SignIn.user_principal) == normalized
        ).order_by(SignIn.timestamp.desc()).first()

        if latest_signin is None:
            raise ValueError("Utilisateur introuvable dans les SignIns")

        review = db.query(NewUserReview).filter(
            func.lower(NewUserReview.user_principal) == normalized
        ).first()
        if review is None:
            review = NewUserReview(user_principal=normalized)
            db.add(review)

        review.display_name = latest_signin.display_name
        review.status = "rejected"
        review.notes = notes
        review.first_seen = review.first_seen or latest_signin.timestamp
        review.last_seen = latest_signin.timestamp
        review.reviewed_by = reviewed_by
        review.reviewed_at = datetime.utcnow()

        db.commit()
        return {"status": "rejected", "user_principal": normalized}
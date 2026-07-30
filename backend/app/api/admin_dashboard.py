import uuid
from datetime import date, datetime, time as midnight_time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    subscription_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminPaymentOut(BaseModel):
    id: uuid.UUID
    user_email: str
    plan: str
    status: str
    amount_kobo: int
    currency: str
    created_at: datetime
    activated_at: Optional[datetime]


class AdminSummaryOut(BaseModel):
    total_students: int
    total_admins: int
    signups_today: int
    active_subscriptions: int
    total_revenue_kobo: int


@router.get("/users", response_model=list[AdminUserOut])
def list_recent_users(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).limit(limit).all()


@router.get("/payments", response_model=list[AdminPaymentOut])
def list_recent_payments(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rows = (
        db.query(Subscription, User.email)
        .join(User, User.id == Subscription.user_id)
        .order_by(Subscription.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        AdminPaymentOut(
            id=sub.id,
            user_email=email,
            plan=sub.plan,
            status=sub.status,
            amount_kobo=sub.amount_kobo,
            currency=sub.currency,
            created_at=sub.created_at,
            activated_at=sub.activated_at,
        )
        for sub, email in rows
    ]


@router.get("/summary", response_model=AdminSummaryOut)
def get_admin_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    since_midnight = datetime.combine(date.today(), midnight_time.min)
    total_students = db.query(User).filter(User.role == "student").count()
    total_admins = db.query(User).filter(User.role == "admin").count()
    signups_today = db.query(User).filter(User.created_at >= since_midnight).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.status == "active").count()
    total_revenue_kobo = (
        db.query(func.coalesce(func.sum(Subscription.amount_kobo), 0))
        .filter(Subscription.status == "active")
        .scalar()
    )
    return AdminSummaryOut(
        total_students=total_students,
        total_admins=total_admins,
        signups_today=signups_today,
        active_subscriptions=active_subscriptions,
        total_revenue_kobo=total_revenue_kobo,
    )

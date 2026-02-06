from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", dependencies=[Depends(require_role("USER", "DOCTOR"))])
def my_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
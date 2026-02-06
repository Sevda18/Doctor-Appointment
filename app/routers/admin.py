from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import require_role
from app.db import get_db
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/users/{user_id}/role/{role}")
def set_role(user_id: int, role: str, db: Session = Depends(get_db), admin=Depends(require_role("ADMIN"))):
    role = role.upper()
    if role not in ("USER", "DOCTOR", "ADMIN"):
        raise HTTPException(status_code=400, detail="Invalid role")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.role = role
    db.commit()
    return {"ok": True, "user_id": u.id, "role": u.role}

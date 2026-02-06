from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.favorite import Favorite
from app.models.doctor_profile import DoctorProfile
from app.models.specialty import Specialty

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/doctors/{doctor_id}", dependencies=[Depends(require_role("USER"))])
def add_favorite(doctor_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    exists = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.doctor_id == doctor_id
    ).first()
    if exists:
        return {"ok": True, "already_favorite": True}

    fav = Favorite(user_id=user.id, doctor_id=doctor_id)
    db.add(fav)
    db.commit()
    return {"ok": True, "doctor_id": doctor_id}

@router.get("", dependencies=[Depends(require_role("USER"))])
def list_favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Favorite, DoctorProfile, Specialty)
        .join(DoctorProfile, DoctorProfile.id == Favorite.doctor_id)
        .join(Specialty, Specialty.id == DoctorProfile.specialty_id)
        .filter(Favorite.user_id == user.id)
        .all()
    )

    return [
        {
            "doctor_id": doc.id,
            "doctor_name": doc.full_name,
            "specialty_id": spec.id,
            "specialty_name": spec.name,
        }
        for fav, doc, spec in rows
    ]

@router.delete("/doctors/{doctor_id}", dependencies=[Depends(require_role("USER"))])
def remove_favorite(doctor_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fav = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.doctor_id == doctor_id
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Not in favorites")

    db.delete(fav)
    db.commit()
    return {"ok": True, "doctor_id": doctor_id}
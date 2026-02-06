from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db import get_db
from app.core.auth import require_role, get_current_user

from app.models.user import User
from app.models.doctor_profile import DoctorProfile
from app.models.specialty import Specialty
from app.models.appointment import Appointment
from app.models.appointment_slot import AppointmentSlot
from app.models.review import Review
from app.models.favorite import Favorite 
from app.models.notification import Notification  

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", dependencies=[Depends(require_role("ADMIN"))])
def list_users(
    role: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            (User.email.ilike(pattern)) | (User.username.ilike(pattern))
        )
    return query.order_by(User.id.asc()).all()


@router.delete("/users/{user_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if u.role == "ADMIN":
        admins_count = db.query(func.count(User.id)).filter(User.role == "ADMIN").scalar() or 0
        if admins_count <= 1:
            raise HTTPException(status_code=409, detail="Cannot delete the last ADMIN")

    db.delete(u)
    db.commit()
    return {"ok": True}


@router.get("/specialties", dependencies=[Depends(require_role("ADMIN"))])
def list_specialties(db: Session = Depends(get_db)):
    return db.query(Specialty).order_by(Specialty.id.asc()).all()


@router.post("/specialties", dependencies=[Depends(require_role("ADMIN"))])
def create_specialty(name: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    exists = db.query(Specialty).filter(func.lower(Specialty.name) == name.strip().lower()).first()
    if exists:
        raise HTTPException(status_code=409, detail="Specialty already exists")

    sp = Specialty(name=name.strip())
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp


@router.put("/specialties/{specialty_id}", dependencies=[Depends(require_role("ADMIN"))])
def rename_specialty(
    specialty_id: int,
    name: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    sp = db.query(Specialty).filter(Specialty.id == specialty_id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="Specialty not found")

    sp.name = name.strip()
    db.commit()
    db.refresh(sp)
    return sp


@router.delete("/specialties/{specialty_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_specialty(specialty_id: int, db: Session = Depends(get_db)):
    sp = db.query(Specialty).filter(Specialty.id == specialty_id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="Specialty not found")

    used = db.query(func.count(DoctorProfile.id)).filter(DoctorProfile.specialty_id == specialty_id).scalar() or 0
    if used > 0:
        raise HTTPException(status_code=409, detail="Specialty is used by doctors")

    db.delete(sp)
    db.commit()
    return {"ok": True}

@router.get("/doctors", dependencies=[Depends(require_role("ADMIN"))])
def list_doctors(
    is_active: Optional[int] = Query(default=None, ge=0, le=1),
    specialty_id: Optional[int] = Query(default=None, ge=1),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(DoctorProfile)
        .options(joinedload(DoctorProfile.specialty))
        .order_by(DoctorProfile.id.asc())
    )

    if is_active is not None:
        query = query.filter(DoctorProfile.is_active == is_active)
    if specialty_id is not None:
        query = query.filter(DoctorProfile.specialty_id == specialty_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            (DoctorProfile.full_name.ilike(pattern)) |
            (DoctorProfile.clinic_name.ilike(pattern))
        )

    return query.all()


@router.patch("/doctors/{doctor_id}/active", dependencies=[Depends(require_role("ADMIN"))])
def set_doctor_active(
    doctor_id: int,
    is_active: int = Query(..., ge=0, le=1),
    db: Session = Depends(get_db),
):
    doc = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doc.is_active = is_active
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/doctors/{doctor_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_doctor_profile(doctor_id: int, db: Session = Depends(get_db)):
    doc = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db.delete(doc)
    db.commit()
    return {"ok": True}

@router.get("/doctors/{doctor_id}/slots", dependencies=[Depends(require_role("ADMIN"))])
def list_doctor_slots(
    doctor_id: int,
    only_available: Optional[int] = Query(default=None, ge=0, le=1),
    day: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(AppointmentSlot).filter(AppointmentSlot.doctor_id == doctor_id)

    if only_available is not None:
        q = q.filter(AppointmentSlot.is_available == only_available)

    if day is not None:
        start = datetime.combine(day, datetime.min.time())
        end = start + timedelta(days=1)
        q = q.filter(AppointmentSlot.start_at >= start, AppointmentSlot.start_at < end)

    return q.order_by(AppointmentSlot.start_at.asc()).all()


@router.delete("/slots/{slot_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    db.delete(slot)
    db.commit()
    return {"ok": True}

@router.get("/appointments", dependencies=[Depends(require_role("ADMIN"))])
def list_appointments(
    status: Optional[str] = Query(default=None),
    doctor_id: Optional[int] = Query(default=None, ge=1),
    patient_user_id: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    q = db.query(Appointment).order_by(Appointment.created_at.desc())

    if status:
        q = q.filter(Appointment.status == status)
    if doctor_id:
        q = q.filter(Appointment.doctor_id == doctor_id)
    if patient_user_id:
        q = q.filter(Appointment.patient_user_id == patient_user_id)

    return q.all()


@router.delete("/appointments/{appointment_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appt.slot_id).first()
    if slot:
        slot.is_available = 1

    db.delete(appt)
    db.commit()
    return {"ok": True}

@router.get("/reviews", dependencies=[Depends(require_role("ADMIN"))])
def list_reviews(
    doctor_id: Optional[int] = Query(default=None, ge=1),
    user_id: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    q = db.query(Review).order_by(Review.id.desc())
    if doctor_id:
        q = q.filter(Review.doctor_id == doctor_id)
    if user_id:
        q = q.filter(Review.user_id == user_id)
    return q.all()


@router.delete("/reviews/{review_id}", dependencies=[Depends(require_role("ADMIN"))])
def delete_review(review_id: int, db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(r)
    db.commit()
    return {"ok": True}
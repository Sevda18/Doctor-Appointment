from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.doctor_profile import DoctorProfile
from app.models.appointment_slot import AppointmentSlot
from app.schemas.slots import SlotCreate, SlotOut

router = APIRouter(prefix="/doctor/slots", tags=["doctor-slots"])

def _my_doctor_profile(db: Session, user: User) -> DoctorProfile:
    prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return prof

@router.post("", response_model=SlotOut, dependencies=[Depends(require_role("DOCTOR"))])
def create_slot(data: SlotCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.end_at <= data.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    doc = _my_doctor_profile(db, user)

    # overlap check
    overlap = db.query(AppointmentSlot).filter(
        AppointmentSlot.doctor_id == doc.id,
        AppointmentSlot.is_available == 1,
        and_(AppointmentSlot.start_at < data.end_at, AppointmentSlot.end_at > data.start_at)
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="Slot overlaps with existing slot")

    slot = AppointmentSlot(
        doctor_id=doc.id,
        start_at=data.start_at,
        end_at=data.end_at,
        is_available=1
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.get("", response_model=list[SlotOut], dependencies=[Depends(require_role("DOCTOR"))])
def list_my_slots(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = _my_doctor_profile(db, user)
    return db.query(AppointmentSlot).filter(AppointmentSlot.doctor_id == doc.id).order_by(AppointmentSlot.start_at).all()
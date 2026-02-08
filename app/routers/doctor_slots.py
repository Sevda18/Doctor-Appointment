from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.doctor_profile import DoctorProfile
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.schemas.slots import SlotCreate, SlotOut

router = APIRouter(tags=["slots"])


def _my_doctor_profile(db: Session, doctor_user: User) -> DoctorProfile:
    prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor profile missing")
    return prof


@router.post("/doctor/slots", response_model=SlotOut, dependencies=[Depends(require_role("DOCTOR"))])
def create_slot(
    data: SlotCreate,
    db: Session = Depends(get_db),
    doctor_user: User = Depends(get_current_user),
):
    if data.end_at <= data.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    prof = _my_doctor_profile(db, doctor_user)

    overlap = (
        db.query(AppointmentSlot)
        .filter(
            AppointmentSlot.doctor_id == prof.id,
            AppointmentSlot.start_at < data.end_at,
            AppointmentSlot.end_at > data.start_at,
        )
        .first()
    )
    if overlap:
        raise HTTPException(status_code=409, detail="Slot overlaps with existing slot")

    slot = AppointmentSlot(
        doctor_id=prof.id,
        start_at=data.start_at,
        end_at=data.end_at,
        is_available=1,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.get("/doctor/slots", response_model=List[SlotOut], dependencies=[Depends(require_role("DOCTOR"))])
def list_my_slots(
    db: Session = Depends(get_db),
    doctor_user: User = Depends(get_current_user),
):
    prof = _my_doctor_profile(db, doctor_user)

    return (
        db.query(AppointmentSlot)
        .filter(AppointmentSlot.doctor_id == prof.id)
        .order_by(AppointmentSlot.start_at.asc())
        .all()
    )


@router.delete("/doctor/slots/{slot_id}", dependencies=[Depends(require_role("DOCTOR"))])
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    doctor_user: User = Depends(get_current_user),
):
    prof = _my_doctor_profile(db, doctor_user)

    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.doctor_id != prof.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    has_appt = db.query(Appointment).filter(Appointment.slot_id == slot_id).first()
    if has_appt:
        raise HTTPException(status_code=409, detail="Slot has active appointment and cannot be deleted")
    db.delete(slot)
    db.commit()
    return {"ok": True, "deleted_slot_id": slot_id}
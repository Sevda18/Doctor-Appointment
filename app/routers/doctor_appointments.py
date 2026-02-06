from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.doctor_profile import DoctorProfile
from app.models.appointment import Appointment
from app.models.appointment_slot import AppointmentSlot
from app.schemas.appointments import AppointmentOut
from app.schemas.enums import AppointmentStatus
from app.services import notify, notify_doctor_and_patient

router = APIRouter(prefix="/doctor/appointments", tags=["doctor-appointments"])


def _my_doctor_id(db: Session, user: User) -> int:
    prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return prof.id


@router.get("", response_model=list[AppointmentOut], dependencies=[Depends(require_role("DOCTOR"))])
def list_received(
    status: Optional[AppointmentStatus] = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doctor_id = _my_doctor_id(db, user)

    q = db.query(Appointment).filter(Appointment.doctor_id == doctor_id)
    if status:
        q = q.filter(Appointment.status == status.value)

    return q.order_by(Appointment.created_at.desc()).all()


@router.post("/{appointment_id}/confirm", response_model=AppointmentOut, dependencies=[Depends(require_role("DOCTOR"))])
def confirm(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doctor_id = _my_doctor_id(db, user)

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if appt.status != "PENDING":
        raise HTTPException(status_code=409, detail="Only PENDING can be confirmed")

    appt.status = "CONFIRMED"
    db.commit()
    db.refresh(appt)
    notify_doctor_and_patient(db, appt, "Appointment confirmed")
    return appt


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut, dependencies=[Depends(require_role("DOCTOR"))])
def cancel_by_doctor(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doctor_id = _my_doctor_id(db, user)

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if appt.status not in ("PENDING", "CONFIRMED"):
        raise HTTPException(status_code=409, detail="Cannot cancel in current status")

    appt.status = "CANCELED"
    appt.canceled_by = "DOCTOR"
    notify_doctor_and_patient(db, appt, "Appointment canceled by doctor")

    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appt.slot_id).first()
    if slot:
        slot.is_available = 1

    db.commit()
    db.refresh(appt)
    return appt


@router.post("/{appointment_id}/complete", response_model=AppointmentOut, dependencies=[Depends(require_role("DOCTOR"))])
def complete(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doctor_id = _my_doctor_id(db, user)

    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if appt.status != "CONFIRMED":
        raise HTTPException(status_code=409, detail="Only CONFIRMED can be completed")

    appt.status = "COMPLETED"
    db.commit()
    db.refresh(appt)
    notify_doctor_and_patient(db, appt, "Appointment completed")
    return appt

@router.get("/upcoming", response_model=list[AppointmentOut], dependencies=[Depends(require_role("DOCTOR"))])
def upcoming(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doctor_id = _my_doctor_id(db, user)

    return (
        db.query(Appointment)
        .join(AppointmentSlot, AppointmentSlot.id == Appointment.slot_id)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "CONFIRMED",
            AppointmentSlot.start_at >= datetime.utcnow()
        )
        .order_by(AppointmentSlot.start_at.asc())
        .all()
    )
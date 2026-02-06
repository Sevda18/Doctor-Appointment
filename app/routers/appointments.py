from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.schemas.appointments import AppointmentCreate, AppointmentOut
from app.services.notifications import notify_doctor_and_patient

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentOut, dependencies=[Depends(require_role("USER"))])
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == data.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.is_available != 1:
        raise HTTPException(status_code=409, detail="Slot is not available")

    slot.is_available = 0

    appt = Appointment(
        doctor_id=slot.doctor_id,
        patient_user_id=user.id,
        slot_id=slot.id,
        status="PENDING",
        canceled_by=None,
        notes=data.notes or "",
    )

    db.add(appt)
    db.commit()
    db.refresh(appt)

    notify_doctor_and_patient(db, appt, "New appointment request (PENDING)")

    return appt


@router.get("/mine", response_model=list[AppointmentOut], dependencies=[Depends(require_role("USER"))])
def my_appointments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Appointment)
        .filter(Appointment.patient_user_id == user.id)
        .order_by(Appointment.created_at.desc())
        .all()
    )


@router.get("/history", response_model=list[AppointmentOut], dependencies=[Depends(require_role("USER"))])
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Appointment)
        .filter(
            Appointment.patient_user_id == user.id,
            Appointment.status.in_(["COMPLETED", "CANCELED"]),
        )
        .order_by(Appointment.created_at.desc())
        .all()
    )


@router.get("/{appointment_id}", response_model=AppointmentOut, dependencies=[Depends(require_role("USER"))])
def get_my_appointment(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.patient_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return appt


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut, dependencies=[Depends(require_role("USER"))])
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.patient_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if appt.status not in ("PENDING", "CONFIRMED"):
        raise HTTPException(status_code=409, detail="Cannot cancel in current status")

    appt.status = "CANCELED"
    appt.canceled_by = "USER"

    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appt.slot_id).first()
    if slot:
        slot.is_available = 1

    db.commit()
    db.refresh(appt)

    notify_doctor_and_patient(db, appt, "Appointment canceled by patient")

    return appt


@router.post("/{appointment_id}/reschedule", response_model=AppointmentOut, dependencies=[Depends(require_role("USER"))])
def reschedule(
    appointment_id: int,
    new_slot_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.patient_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if appt.status != "PENDING":
        raise HTTPException(status_code=409, detail="Only PENDING appointments can be rescheduled")

    new_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == new_slot_id).first()
    if not new_slot:
        raise HTTPException(status_code=404, detail="New slot not found")

    if new_slot.is_available != 1:
        raise HTTPException(status_code=409, detail="Slot not available")

    old_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appt.slot_id).first()
    if old_slot:
        old_slot.is_available = 1

    new_slot.is_available = 0
    appt.slot_id = new_slot_id

    db.commit()
    db.refresh(appt)

    notify_doctor_and_patient(db, appt, f"Appointment rescheduled to slot {new_slot_id}")

    return appt
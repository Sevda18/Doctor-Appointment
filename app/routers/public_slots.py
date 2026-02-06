from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.models.appointment_slot import AppointmentSlot
from app.schemas.slots import SlotOut

router = APIRouter(prefix="/doctors", tags=["public-slots"])

@router.get("/{doctor_id}/slots", response_model=list[SlotOut])
def list_available_slots(
    doctor_id: int,
    from_dt: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):

    q = (
        db.query(AppointmentSlot)
        .filter(
            AppointmentSlot.doctor_id == doctor_id,
            AppointmentSlot.is_available == 1
        )
    )

    if from_dt:
        try:
            dt = datetime.fromisoformat(from_dt)
        except ValueError:
            raise HTTPException(status_code=422, detail="from_dt must be ISO datetime like 2026-02-10T10:30:00")

        q = q.filter(AppointmentSlot.end_at > dt)

    return q.order_by(AppointmentSlot.start_at.asc()).all()
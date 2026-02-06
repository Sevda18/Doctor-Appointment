from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AppointmentCreate(BaseModel):
    doctor_id: int
    slot_id: int
    notes: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    created_at: datetime
    patient_user_id: int
    doctor_id: int
    slot_id: int
    status: str
    canceled_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
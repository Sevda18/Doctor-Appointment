from pydantic import BaseModel
from datetime import datetime

class SlotCreate(BaseModel):
    start_at: datetime
    end_at: datetime

class SlotOut(BaseModel):
    id: int
    doctor_id: int
    start_at: datetime
    end_at: datetime
    is_available: int

    class Config:
        from_attributes = True
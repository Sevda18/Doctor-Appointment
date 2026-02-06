from pydantic import BaseModel
from typing import Optional
from app.schemas.specialty import SpecialtyOut


class DoctorOut(BaseModel):
    id: int
    full_name: str
    bio: str
    clinic_name: str
    address: Optional[str] = None
    phone: str
    specialty_id: int
    specialty: SpecialtyOut
    avg_rating: float = 0.0
    reviews_count: int = 0
    is_active: int

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    full_name: str
    bio: str = ""
    clinic_name: str
    address: str
    phone: str
    specialty_id: int

from pydantic import BaseModel, Field
from typing import Optional

class DoctorRegisterRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(min_length=6)

    full_name: str
    bio: str = ""
    clinic_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    specialty_id: int

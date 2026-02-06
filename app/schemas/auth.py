from pydantic import BaseModel, Field
from typing import Optional

class RegisterClientRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(min_length=6)

class RegisterDoctorRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(min_length=6)

    full_name: str
    bio: str = ""
    clinic_name: str
    address: str
    phone: str
    specialty_id: int

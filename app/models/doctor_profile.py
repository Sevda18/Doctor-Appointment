from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from app.db import Base

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    full_name: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str] = mapped_column(Text, default="")
    clinic_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id"), nullable=False)
    specialty = relationship("Specialty")

    is_active: Mapped[int] = mapped_column(Integer, default=1)


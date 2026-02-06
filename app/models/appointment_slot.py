from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, Integer, Index

from app.db import Base

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctor_profiles.id"), nullable=False)

    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    is_available: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

Index("ix_appointment_slots_doctor_id", AppointmentSlot.doctor_id)
Index("ix_appointment_slots_start_at", AppointmentSlot.start_at)
Index("ix_appointment_slots_end_at", AppointmentSlot.end_at)
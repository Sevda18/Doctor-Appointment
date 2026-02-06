from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, DateTime
from datetime import datetime
from app.db import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "doctor_id", name="uq_favorites_user_doctor"),
    )
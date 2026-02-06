from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="USER")  # USER/DOCTOR/ADMIN
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

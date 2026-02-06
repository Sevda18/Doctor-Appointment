from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.db import Base

class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

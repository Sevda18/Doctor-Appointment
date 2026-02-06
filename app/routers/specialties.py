from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.models.specialty import Specialty
from app.schemas.specialty import SpecialtyOut
from app.core.auth import require_role  # ако така ти се казва зависимостта

router = APIRouter(prefix="/specialties", tags=["specialties"])

class SpecialtyCreate(BaseModel):
    name: str

@router.get("", response_model=list[SpecialtyOut])
def list_specialties(db: Session = Depends(get_db)):
    return db.query(Specialty).order_by(Specialty.name).all()

@router.post("", response_model=SpecialtyOut, dependencies=[Depends(require_role("ADMIN"))])
def create_specialty(data: SpecialtyCreate, db: Session = Depends(get_db)):
    exists = db.query(Specialty).filter(Specialty.name == data.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Specialty already exists")
    s = Specialty(name=data.name)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

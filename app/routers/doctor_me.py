from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import require_role
from app.db import get_db
from app.models.doctor_profile import DoctorProfile
from app.schemas.doctor import DoctorCreate, DoctorOut

router = APIRouter(prefix="/doctor", tags=["doctor"])

@router.get("/me", response_model=DoctorOut)
def get_my_profile(db: Session = Depends(get_db), doctor_user=Depends(require_role("DOCTOR"))):
    prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return prof

@router.post("/me", response_model=DoctorOut)
def create_or_update_my_profile(data: DoctorCreate, db: Session = Depends(get_db), doctor_user=Depends(require_role("DOCTOR"))):
    prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user.id).first()

    if not prof:
        prof = DoctorProfile(
            user_id=doctor_user.id,
            full_name=data.full_name,
            bio=data.bio,
            clinic_name=data.clinic_name,
            address=data.address,
            phone=data.phone,
            specialty_id=data.specialty_id,
            is_active=1,
        )
        db.add(prof)
    else:
        prof.full_name = data.full_name
        prof.bio = data.bio
        prof.clinic_name = data.clinic_name
        prof.address = data.address
        prof.phone = data.phone
        prof.specialty_id = data.specialty_id
        prof.is_active = 1

    db.commit()
    db.refresh(prof)
    return prof

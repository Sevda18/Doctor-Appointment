from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.deps import require_role
from app.db import get_db
from app.models.doctor_profile import DoctorProfile
from app.models.specialty import Specialty
from app.models.review import Review
from app.models.appointment import Appointment
from app.schemas.doctor import DoctorCreate, DoctorOut


router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("/me", response_model=dict)
def get_my_profile(
    db: Session = Depends(get_db),
    doctor_user=Depends(require_role("DOCTOR")),
):
    # 1) Load profile + specialty
    prof = (
        db.query(DoctorProfile)
        .options(joinedload(DoctorProfile.specialty))
        .filter(DoctorProfile.user_id == doctor_user.id)
        .first()
    )
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    # 2) Rating stats
    avg_rating = (
        db.query(func.coalesce(func.avg(Review.rating), 0.0))
        .filter(Review.doctor_id == prof.id)
        .scalar()
    ) or 0.0

    reviews_count = (
        db.query(func.count(Review.id))
        .filter(Review.doctor_id == prof.id)
        .scalar()
    ) or 0

    # 3) Appointment stats (optional but useful)
    pending_count = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.doctor_id == prof.id, Appointment.status == "PENDING")
        .scalar()
    ) or 0

    confirmed_count = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.doctor_id == prof.id, Appointment.status == "CONFIRMED")
        .scalar()
    ) or 0

    completed_count = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.doctor_id == prof.id, Appointment.status == "COMPLETED")
        .scalar()
    ) or 0

    canceled_count = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.doctor_id == prof.id, Appointment.status == "CANCELED")
        .scalar()
    ) or 0

    # 4) Return EVERYTHING
    return {
        "doctor_user": {
            "id": doctor_user.id,
            "email": getattr(doctor_user, "email", None),
            "username": getattr(doctor_user, "username", None),
            "role": getattr(doctor_user, "role", "DOCTOR"),
        },
        "profile": DoctorOut.model_validate(prof).model_dump(),
        "specialty": {
            "id": prof.specialty.id if prof.specialty else prof.specialty_id,
            "name": prof.specialty.name if prof.specialty else None,
        },
        "stats": {
            "avg_rating": round(float(avg_rating), 2),
            "reviews_count": int(reviews_count),
        },
    }


@router.post("/me", response_model=DoctorOut)
def create_or_update_my_profile(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    doctor_user=Depends(require_role("DOCTOR")),
):
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
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional
from datetime import date

from app.db import get_db
from app.models.doctor_profile import DoctorProfile
from app.models.specialty import Specialty
from app.models.review import Review
from app.models.appointment_slot import AppointmentSlot
from app.schemas.doctor import DoctorOut

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorOut])
def list_doctors(
    name: Optional[str] = Query(default=None, min_length=1),
    specialty_id: Optional[int] = Query(default=None, ge=1),
    specialty_name: Optional[str] = Query(default=None, min_length=1),
    is_active: Optional[int] = Query(default=None, ge=0, le=1),
    date_: Optional[date] = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
):
    ratings_sq = (
        db.query(
            Review.doctor_id.label("doctor_id"),
            func.coalesce(func.avg(Review.rating), 0.0).label("avg_rating"),
            func.count(Review.id).label("reviews_count"),
        )
        .group_by(Review.doctor_id)
        .subquery()
    )

    q = (
        db.query(
            DoctorProfile,
            func.coalesce(ratings_sq.c.avg_rating, 0.0).label("avg_rating"),
            func.coalesce(ratings_sq.c.reviews_count, 0).label("reviews_count"),
        )
        .join(Specialty, Specialty.id == DoctorProfile.specialty_id)
        .outerjoin(ratings_sq, ratings_sq.c.doctor_id == DoctorProfile.id)
        .options(joinedload(DoctorProfile.specialty))
    )

    if is_active is not None:
        q = q.filter(DoctorProfile.is_active == is_active)

    if specialty_id is not None:
        q = q.filter(DoctorProfile.specialty_id == specialty_id)

    if specialty_name:
        sp = f"%{specialty_name.strip()}%"
        q = q.filter(Specialty.name.ilike(sp))

    if name:
        pattern = f"%{name.strip()}%"
        q = q.filter(
            (DoctorProfile.full_name.ilike(pattern)) |
            (DoctorProfile.clinic_name.ilike(pattern))
        )

    if date_ is not None:
        q = (
            q.join(AppointmentSlot, AppointmentSlot.doctor_id == DoctorProfile.id)
            .filter(
                AppointmentSlot.is_available == 1,
                func.date(AppointmentSlot.start_at) == str(date_)  # <-- ако ти е друго име, смени тук
            )
            .distinct()
        )

    rows = q.order_by(DoctorProfile.id).all()

    result = []
    for doc, avg_rating, reviews_count in rows:
        d = DoctorOut.model_validate(doc).model_dump()
        d["avg_rating"] = round(float(avg_rating or 0.0), 2)
        d["reviews_count"] = int(reviews_count or 0)
        result.append(d)

    return result

@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doc = (
        db.query(DoctorProfile)
        .options(joinedload(DoctorProfile.specialty))
        .filter(DoctorProfile.id == doctor_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    avg_rating = (
        db.query(func.coalesce(func.avg(Review.rating), 0.0))
        .filter(Review.doctor_id == doctor_id)
        .scalar()
    )
    reviews_count = (
        db.query(func.count(Review.id))
        .filter(Review.doctor_id == doctor_id)
        .scalar()
    )

    out = DoctorOut.model_validate(doc)
    out.avg_rating = round(float(avg_rating or 0.0), 2)
    out.reviews_count = int(reviews_count or 0)
    return out
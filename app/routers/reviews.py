from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.core.auth import require_role, get_current_user
from app.models.user import User
from app.models.doctor_profile import DoctorProfile
from app.models.review import Review
from app.schemas.reviews import ReviewCreate, ReviewOut

router = APIRouter(prefix="/doctors", tags=["reviews"])


# Place the /mine route BEFORE dynamic routes to avoid path conflicts
@router.get("/mine", response_model=list[ReviewOut], dependencies=[Depends(require_role("USER"))])
def my_reviews(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Review)
        .filter(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.get("/{doctor_id:int}/reviews", response_model=list[ReviewOut])
def list_reviews(doctor_id: int, db: Session = Depends(get_db)):
    doc = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return (
        db.query(Review)
        .filter(Review.doctor_id == doctor_id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.post("/{doctor_id:int}/reviews", response_model=ReviewOut, dependencies=[Depends(require_role("USER"))])
def create_review(
    doctor_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    existing = (
        db.query(Review)
        .filter(Review.user_id == user.id, Review.doctor_id == doctor_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="You already reviewed this doctor")

    rev = Review(
        user_id=user.id,
        doctor_id=doctor_id,
        rating=data.rating,
        comment=(data.comment or None),
    )

    db.add(rev)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You already reviewed this doctor")

    db.refresh(rev)
    return rev
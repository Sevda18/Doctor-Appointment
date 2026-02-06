from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.specialty import Specialty
from app.db import get_db
from app.models.user import User
from app.models.doctor_profile import DoctorProfile

from app.schemas.auth import RegisterClientRequest, RegisterDoctorRequest
from app.schemas.token import TokenResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-client", response_model=TokenResponse)
def register_client(data: RegisterClientRequest, db: Session = Depends(get_db)):
    if not data.email and not data.username:
        raise HTTPException(status_code=400, detail="Provide email or username")

    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already used")
    if data.username and db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=409, detail="Username already used")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        role="USER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/register-doctor", response_model=TokenResponse)
def register_doctor(data: RegisterDoctorRequest, db: Session = Depends(get_db)):
    if not data.email and not data.username:
        raise HTTPException(status_code=400, detail="Provide email or username")

    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email already used")
    if data.username and db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=409, detail="Username already used")

    
    if data.specialty_id is None or data.specialty_id <= 0:
        raise HTTPException(status_code=400, detail="specialty_id must be a positive integer")

    spec = db.query(Specialty).filter(Specialty.id == data.specialty_id).first()
    if not spec:
        raise HTTPException(status_code=400, detail="Invalid specialty_id. Use GET /specialties to see available options.")
    
    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        role="DOCTOR",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    prof = DoctorProfile(
        user_id=user.id,
        full_name=data.full_name,
        bio=data.bio,
        clinic_name=data.clinic_name,
        address=data.address,
        phone=data.phone,
        specialty_id=data.specialty_id,
        is_active=1,
    )
    db.add(prof)
    db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    identifier = form_data.username  # може да е email или username
    password = form_data.password

    user = (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)

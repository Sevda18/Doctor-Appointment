from sqlalchemy.orm import Session

from app.models.user import User
from app.models.specialty import Specialty
from app.core.security import hash_password


SPECIALTIES = [
    "Cardiology", "Dermatology", "Pediatrics", "Neurology", "Orthopedics",
    "Endocrinology", "Otolaryngology (ENT)", "Ophthalmology", "Gastroenterology",
    "Gynecology", "Urology", "Pulmonology", "Nephrology", "Psychiatry", "Rheumatology",
]

def seed_admin(db: Session) -> None:
    email = "admin@local"
    username = "admin"
    password = "admin123"

    exists = db.query(User).filter(User.email == email).first()
    if not exists:
        admin = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            role="ADMIN",
        )
        db.add(admin)

def seed_specialties(db: Session) -> None:
    existing = {s.name for s in db.query(Specialty).all()}
    for name in SPECIALTIES:
        if name not in existing:
            db.add(Specialty(name=name))
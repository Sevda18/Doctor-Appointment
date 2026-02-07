# app/startup.py
import os
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.user import User
from app.models.specialty import Specialty

from app.seed import seed_admin
from app.seed import seed_specialties


def run_auto_seed():
    if os.getenv("AUTO_SEED", "1") in ("0", "false", "False", "no", "NO"):
        return

    db: Session = SessionLocal()
    try:
        has_users = db.query(User.id).first() is not None
        has_specialties = db.query(Specialty.id).first() is not None

        if not has_users:
            seed_admin(db)
        if not has_specialties:
            seed_specialties(db)

        db.commit()
    finally:
        db.close()
from app.db import SessionLocal
from app.models.specialty import Specialty

SPECIALTIES = [
    "Cardiology",
    "Dermatology",
    "Pediatrics",
    "Neurology",
    "Orthopedics",
    "Endocrinology",
    "Otolaryngology (ENT)",
    "Ophthalmology",
    "Gastroenterology",
    "Gynecology",
    "Urology",
    "Pulmonology",
    "Nephrology",
    "Psychiatry",
    "Rheumatology",
]

def main():
    db = SessionLocal()
    try:
        existing = {s.name for s in db.query(Specialty).all()}
        added = 0

        for name in SPECIALTIES:
            if name in existing:
                continue
            db.add(Specialty(name=name))
            added += 1

        db.commit()
        print(f"Seed specialties done. Added: {added}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

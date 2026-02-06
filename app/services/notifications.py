from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.doctor_profile import DoctorProfile


def notify(db: Session, user_id: int, message: str):
    n = Notification(user_id=user_id, message=message)
    db.add(n)
    db.commit()


def notify_doctor_and_patient(db: Session, appt, message: str):
    # notify patient
    notify(db, appt.patient_user_id, message)

    # find doctor user_id
    prof = db.query(DoctorProfile).filter(DoctorProfile.id == appt.doctor_id).first()
    if prof:
        notify(db, prof.user_id, message)
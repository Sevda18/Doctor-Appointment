from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.admin import router as admin_router
from app.routers.doctor_me import router as doctor_me_router
from app.routers.specialties import router as specialties_router
from app.routers.doctors import router as doctors_router
from app.routers.doctor_slots import router as slots_router
from app.routers.public_slots import router as public_slots_router
from app.routers.appointments import router as appointments_router
from app.routers.doctor_appointments import router as doctor_appointments_router
from app.routers.reviews import router as reviews_router
from app.routers.notifications import router as notifications_router
from app.routers import favorites

app = FastAPI(title="Doctors Booking API")

# auth + users
app.include_router(auth_router)
app.include_router(users_router)

# admin
app.include_router(admin_router)

# doctors
app.include_router(doctor_me_router)
# reviews_router must come BEFORE doctors_router to prevent /doctors/mine being matched by /doctors/{doctor_id}
app.include_router(reviews_router)
app.include_router(doctors_router)

# specialties
app.include_router(specialties_router)

# slots
app.include_router(slots_router)
app.include_router(public_slots_router)

# appointments
app.include_router(appointments_router)
app.include_router(doctor_appointments_router)

# notifications
app.include_router(notifications_router)

app.include_router(favorites.router)

@app.get("/health")
def health():
    return {"status": "ok"}
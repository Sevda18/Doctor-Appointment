"""
Pytest configuration and fixtures for the Doctor-Appointment tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.db import Base, get_db
from app.main import app
from app.models.user import User
from app.models.specialty import Specialty
from app.models.doctor_profile import DoctorProfile
from app.models.appointment_slot import AppointmentSlot
from app.models.appointment import Appointment
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.notification import Notification
from app.core.security import hash_password, create_access_token


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def specialty(db_session):
    """Create a test specialty."""
    spec = Specialty(name="Cardiology")
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)
    return spec


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        password_hash=hash_password("password123"),
        role="USER",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user):
    """Get auth token for test user."""
    return create_access_token(str(test_user.id))


@pytest.fixture
def auth_headers(test_user_token):
    """Get authorization headers for test user."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def doctor_user(db_session):
    """Create a doctor user."""
    user = User(
        email="doctor@example.com",
        username="doctor",
        password_hash=hash_password("doctor123"),
        role="DOCTOR",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def doctor_profile(db_session, doctor_user, specialty):
    """Create a doctor profile."""
    profile = DoctorProfile(
        user_id=doctor_user.id,
        full_name="Dr. John Smith",
        bio="Experienced cardiologist",
        clinic_name="Heart Clinic",
        address="123 Medical St",
        phone="555-1234",
        specialty_id=specialty.id,
        is_active=1,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def doctor_token(doctor_user):
    """Get auth token for doctor."""
    return create_access_token(str(doctor_user.id))


@pytest.fixture
def doctor_auth_headers(doctor_token):
    """Get authorization headers for doctor."""
    return {"Authorization": f"Bearer {doctor_token}"}


@pytest.fixture
def appointment_slot(db_session, doctor_profile):
    """Create an available appointment slot."""
    slot = AppointmentSlot(
        doctor_id=doctor_profile.id,
        start_at=datetime.utcnow() + timedelta(days=1),
        end_at=datetime.utcnow() + timedelta(days=1, hours=1),
        is_available=1,
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    return slot


@pytest.fixture
def appointment(db_session, doctor_profile, test_user, appointment_slot):
    """Create a test appointment."""
    appt = Appointment(
        doctor_id=doctor_profile.id,
        patient_user_id=test_user.id,
        slot_id=appointment_slot.id,
        status="PENDING",
        notes="Test appointment",
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    return appt


@pytest.fixture
def admin_user(db_session):
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("admin123"),
        role="ADMIN",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Get auth token for admin."""
    return create_access_token(str(admin_user.id))


@pytest.fixture
def admin_auth_headers(admin_token):
    """Get authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}

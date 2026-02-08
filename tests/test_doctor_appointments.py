"""
Unit tests for doctor appointment management endpoints.
"""
import pytest
from datetime import datetime, timedelta


class TestDoctorAppointmentsList:
    """Tests for doctor viewing appointments."""

    def test_list_received_appointments(self, client, doctor_auth_headers, doctor_profile, appointment):
        """Test doctor listing received appointments."""
        response = client.get("/doctor/appointments", headers=doctor_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_received_appointments_filter_status(self, client, doctor_auth_headers, doctor_profile, appointment):
        """Test filtering appointments by status."""
        response = client.get("/doctor/appointments?status=PENDING", headers=doctor_auth_headers)
        assert response.status_code == 200

    def test_list_received_appointments_no_profile(self, client, db_session):
        """Test doctor without profile gets 404."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        doc_user = User(
            email="noprofile@example.com",
            username="noprofile",
            password_hash=hash_password("password123"),
            role="DOCTOR",
        )
        db_session.add(doc_user)
        db_session.commit()

        token = create_access_token(str(doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/doctor/appointments", headers=headers)
        assert response.status_code == 404
        assert "profile not found" in response.json()["detail"]


class TestDoctorConfirmAppointment:
    """Tests for confirming appointments."""

    def test_confirm_appointment_success(self, client, doctor_auth_headers, doctor_profile, appointment):
        """Test doctor confirming an appointment."""
        response = client.post(f"/doctor/appointments/{appointment.id}/confirm", headers=doctor_auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "CONFIRMED"

    def test_confirm_appointment_not_found(self, client, doctor_auth_headers, doctor_profile):
        """Test confirming non-existent appointment."""
        response = client.post("/doctor/appointments/9999/confirm", headers=doctor_auth_headers)
        assert response.status_code == 404

    def test_confirm_appointment_forbidden(self, client, doctor_profile, appointment, db_session):
        """Test doctor cannot confirm another doctor's appointment."""
        from app.models.user import User
        from app.models.doctor_profile import DoctorProfile
        from app.models.specialty import Specialty
        from app.core.security import hash_password, create_access_token

        spec = Specialty(name="Other Specialty")
        db_session.add(spec)
        db_session.commit()

        other_doc_user = User(
            email="other_doc@example.com",
            username="otherdoc",
            password_hash=hash_password("password123"),
            role="DOCTOR",
        )
        db_session.add(other_doc_user)
        db_session.commit()

        other_profile = DoctorProfile(
            user_id=other_doc_user.id,
            full_name="Dr. Other",
            bio="Bio",
            clinic_name="Clinic",
            address="Address",
            phone="12345",
            specialty_id=spec.id,
            is_active=1,
        )
        db_session.add(other_profile)
        db_session.commit()

        token = create_access_token(str(other_doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(f"/doctor/appointments/{appointment.id}/confirm", headers=headers)
        assert response.status_code == 403

    def test_confirm_appointment_not_pending(self, client, doctor_auth_headers, doctor_profile, appointment, db_session):
        """Test cannot confirm non-pending appointment."""
        appointment.status = "CONFIRMED"
        db_session.commit()

        response = client.post(f"/doctor/appointments/{appointment.id}/confirm", headers=doctor_auth_headers)
        assert response.status_code == 409


class TestDoctorCancelAppointment:
    """Tests for doctor canceling appointments."""

    def test_cancel_by_doctor_success(self, client, doctor_auth_headers, doctor_profile, appointment):
        """Test doctor canceling an appointment."""
        response = client.post(f"/doctor/appointments/{appointment.id}/cancel", headers=doctor_auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELED"
        assert response.json()["canceled_by"] == "DOCTOR"

    def test_cancel_by_doctor_not_found(self, client, doctor_auth_headers, doctor_profile):
        """Test canceling non-existent appointment."""
        response = client.post("/doctor/appointments/9999/cancel", headers=doctor_auth_headers)
        assert response.status_code == 404

    def test_cancel_by_doctor_wrong_status(self, client, doctor_auth_headers, doctor_profile, appointment, db_session):
        """Test cannot cancel completed appointment."""
        appointment.status = "COMPLETED"
        db_session.commit()

        response = client.post(f"/doctor/appointments/{appointment.id}/cancel", headers=doctor_auth_headers)
        assert response.status_code == 409

    def test_cancel_by_doctor_forbidden(self, client, doctor_profile, appointment, db_session, specialty):
        """Test cannot cancel another doctor's appointment."""
        from app.models.user import User
        from app.models.doctor_profile import DoctorProfile
        from app.core.security import hash_password, create_access_token

        # Create another doctor
        other_user = User(
            email="cancel_test@example.com",
            username="canceltest",
            password_hash=hash_password("password123"),
            role="DOCTOR",
        )
        db_session.add(other_user)
        db_session.commit()

        other_profile = DoctorProfile(
            user_id=other_user.id,
            full_name="Dr. Cancel Test",
            bio="Bio",
            specialty_id=specialty.id,
            is_active=1,
        )
        db_session.add(other_profile)
        db_session.commit()

        token = create_access_token(str(other_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(f"/doctor/appointments/{appointment.id}/cancel", headers=headers)
        assert response.status_code == 403


class TestDoctorCompleteAppointment:
    """Tests for completing appointments."""

    def test_complete_appointment_success(self, client, doctor_auth_headers, doctor_profile, appointment, db_session):
        """Test doctor completing an appointment."""
        appointment.status = "CONFIRMED"
        db_session.commit()

        response = client.post(f"/doctor/appointments/{appointment.id}/complete", headers=doctor_auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

    def test_complete_appointment_not_found(self, client, doctor_auth_headers, doctor_profile):
        """Test completing non-existent appointment."""
        response = client.post("/doctor/appointments/9999/complete", headers=doctor_auth_headers)
        assert response.status_code == 404

    def test_complete_appointment_not_confirmed(self, client, doctor_auth_headers, doctor_profile, appointment):
        """Test cannot complete non-confirmed appointment."""
        response = client.post(f"/doctor/appointments/{appointment.id}/complete", headers=doctor_auth_headers)
        assert response.status_code == 409
        assert "CONFIRMED" in response.json()["detail"]

    def test_complete_appointment_forbidden(self, client, doctor_profile, appointment, db_session, specialty):
        """Test cannot complete another doctor's appointment."""
        from app.models.user import User
        from app.models.doctor_profile import DoctorProfile
        from app.core.security import hash_password, create_access_token

        # Create another doctor
        other_user = User(
            email="complete_test@example.com",
            username="completetest",
            password_hash=hash_password("password123"),
            role="DOCTOR",
        )
        db_session.add(other_user)
        db_session.commit()

        other_profile = DoctorProfile(
            user_id=other_user.id,
            full_name="Dr. Complete Test",
            bio="Bio",
            specialty_id=specialty.id,
            is_active=1,
        )
        db_session.add(other_profile)
        db_session.commit()

        token = create_access_token(str(other_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(f"/doctor/appointments/{appointment.id}/complete", headers=headers)
        assert response.status_code == 403


class TestDoctorUpcomingAppointments:
    """Tests for upcoming appointments."""

    def test_upcoming_appointments(self, client, doctor_auth_headers, doctor_profile, appointment, db_session):
        """Test getting upcoming confirmed appointments."""
        appointment.status = "CONFIRMED"
        db_session.commit()

        response = client.get("/doctor/appointments/upcoming", headers=doctor_auth_headers)
        assert response.status_code == 200

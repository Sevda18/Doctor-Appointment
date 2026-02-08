"""
Unit tests for appointment endpoints.
"""
import pytest


class TestCreateAppointment:
    """Tests for creating appointments."""

    def test_create_appointment_success(self, client, auth_headers, appointment_slot, doctor_profile):
        """Test creating a new appointment."""
        response = client.post("/appointments", json={
            "doctor_id": doctor_profile.id,
            "slot_id": appointment_slot.id,
            "notes": "Initial consultation"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["slot_id"] == appointment_slot.id
        assert data["status"] == "PENDING"
        assert data["notes"] == "Initial consultation"

    def test_create_appointment_invalid_slot(self, client, auth_headers):
        """Test creating appointment with invalid slot."""
        response = client.post("/appointments", json={
            "doctor_id": 1,
            "slot_id": 9999,
            "notes": "Test"
        }, headers=auth_headers)
        assert response.status_code == 404
        assert "Slot not found" in response.json()["detail"]

    def test_create_appointment_slot_unavailable(self, client, auth_headers, appointment_slot, doctor_profile, db_session):
        """Test creating appointment when slot is unavailable."""
        # Make slot unavailable
        appointment_slot.is_available = 0
        db_session.commit()

        response = client.post("/appointments", json={
            "doctor_id": doctor_profile.id,
            "slot_id": appointment_slot.id,
            "notes": "Test"
        }, headers=auth_headers)
        assert response.status_code == 409
        assert "Slot is not available" in response.json()["detail"]

    def test_create_appointment_unauthorized(self, client, appointment_slot):
        """Test creating appointment without authentication."""
        response = client.post("/appointments", json={
            "slot_id": appointment_slot.id,
            "notes": "Test"
        })
        assert response.status_code == 401


class TestGetAppointments:
    """Tests for getting appointments."""

    def test_get_my_appointments(self, client, auth_headers, appointment):
        """Test getting user's appointments."""
        response = client.get("/appointments/mine", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == appointment.id

    def test_get_my_appointments_empty(self, client, auth_headers):
        """Test getting appointments when user has none."""
        response = client.get("/appointments/mine", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_appointment_by_id(self, client, auth_headers, appointment):
        """Test getting a specific appointment."""
        response = client.get(f"/appointments/{appointment.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == appointment.id

    def test_get_appointment_not_found(self, client, auth_headers):
        """Test getting non-existent appointment."""
        response = client.get("/appointments/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_appointment_forbidden(self, client, appointment, db_session):
        """Test getting another user's appointment."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        # Create another user
        other_user = User(
            email="other@example.com",
            username="other",
            password_hash=hash_password("password123"),
            role="USER",
        )
        db_session.add(other_user)
        db_session.commit()

        other_token = create_access_token(str(other_user.id))
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = client.get(f"/appointments/{appointment.id}", headers=other_headers)
        assert response.status_code == 403


class TestCancelAppointment:
    """Tests for canceling appointments."""

    def test_cancel_appointment_success(self, client, auth_headers, appointment):
        """Test canceling an appointment."""
        response = client.post(f"/appointments/{appointment.id}/cancel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELED"
        assert data["canceled_by"] == "USER"

    def test_cancel_appointment_not_found(self, client, auth_headers):
        """Test canceling non-existent appointment."""
        response = client.post("/appointments/9999/cancel", headers=auth_headers)
        assert response.status_code == 404

    def test_cancel_already_canceled(self, client, auth_headers, appointment, db_session):
        """Test canceling an already canceled appointment."""
        appointment.status = "CANCELED"
        db_session.commit()

        response = client.post(f"/appointments/{appointment.id}/cancel", headers=auth_headers)
        assert response.status_code == 409

    def test_cancel_appointment_forbidden(self, client, appointment, db_session):
        """Test canceling another user's appointment."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        # Create another user
        other_user = User(
            email="other_cancel@example.com",
            username="othercancel",
            password_hash=hash_password("password123"),
            role="USER",
        )
        db_session.add(other_user)
        db_session.commit()

        token = create_access_token(str(other_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(f"/appointments/{appointment.id}/cancel", headers=headers)
        assert response.status_code == 403


class TestAppointmentHistory:
    """Tests for appointment history."""

    def test_get_history(self, client, auth_headers, appointment, db_session):
        """Test getting appointment history."""
        # Mark appointment as completed
        appointment.status = "COMPLETED"
        db_session.commit()

        response = client.get("/appointments/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "COMPLETED"

    def test_get_history_empty(self, client, auth_headers, appointment):
        """Test getting history when no completed/canceled appointments."""
        response = client.get("/appointments/history", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []


class TestRescheduleAppointment:
    """Tests for rescheduling appointments."""

    def test_reschedule_success(self, client, auth_headers, appointment, doctor_profile, db_session):
        """Test rescheduling an appointment."""
        from app.models.appointment_slot import AppointmentSlot
        from datetime import datetime, timedelta

        # Create a new slot
        new_slot = AppointmentSlot(
            doctor_id=doctor_profile.id,
            start_at=datetime.utcnow() + timedelta(days=3),
            end_at=datetime.utcnow() + timedelta(days=3, hours=1),
            is_available=1,
        )
        db_session.add(new_slot)
        db_session.commit()

        response = client.post(
            f"/appointments/{appointment.id}/reschedule?new_slot_id={new_slot.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["slot_id"] == new_slot.id

    def test_reschedule_not_found(self, client, auth_headers):
        """Test rescheduling non-existent appointment."""
        response = client.post("/appointments/9999/reschedule?new_slot_id=1", headers=auth_headers)
        assert response.status_code == 404

    def test_reschedule_forbidden(self, client, appointment, db_session):
        """Test rescheduling another user's appointment."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        other_user = User(
            email="other_resc@example.com",
            username="other_resc",
            password_hash=hash_password("password123"),
            role="USER",
        )
        db_session.add(other_user)
        db_session.commit()

        other_token = create_access_token(str(other_user.id))
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = client.post(f"/appointments/{appointment.id}/reschedule?new_slot_id=1", headers=other_headers)
        assert response.status_code == 403

    def test_reschedule_not_pending(self, client, auth_headers, appointment, db_session):
        """Test cannot reschedule non-pending appointment."""
        appointment.status = "CONFIRMED"
        db_session.commit()

        response = client.post(f"/appointments/{appointment.id}/reschedule?new_slot_id=1", headers=auth_headers)
        assert response.status_code == 409

    def test_reschedule_slot_not_found(self, client, auth_headers, appointment):
        """Test rescheduling to non-existent slot."""
        response = client.post(f"/appointments/{appointment.id}/reschedule?new_slot_id=9999", headers=auth_headers)
        assert response.status_code == 404
        assert "New slot not found" in response.json()["detail"]

    def test_reschedule_slot_not_available(self, client, auth_headers, appointment, doctor_profile, db_session):
        """Test rescheduling to unavailable slot."""
        from app.models.appointment_slot import AppointmentSlot
        from datetime import datetime, timedelta

        new_slot = AppointmentSlot(
            doctor_id=doctor_profile.id,
            start_at=datetime.utcnow() + timedelta(days=4),
            end_at=datetime.utcnow() + timedelta(days=4, hours=1),
            is_available=0,  # Not available
        )
        db_session.add(new_slot)
        db_session.commit()

        response = client.post(
            f"/appointments/{appointment.id}/reschedule?new_slot_id={new_slot.id}",
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "not available" in response.json()["detail"]

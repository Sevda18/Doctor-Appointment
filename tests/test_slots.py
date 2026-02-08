"""
Unit tests for appointment slots endpoints.
"""
import pytest
from datetime import datetime, timedelta


class TestDoctorSlots:
    """Tests for doctor slot management."""

    def test_create_slot_success(self, client, doctor_auth_headers, doctor_profile):
        """Test doctor creating a new slot."""
        start = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2, hours=1)).isoformat()

        response = client.post("/doctor/slots", json={
            "start_at": start,
            "end_at": end
        }, headers=doctor_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_available"] == 1
        assert data["doctor_id"] == doctor_profile.id

    def test_create_slot_end_before_start(self, client, doctor_auth_headers, doctor_profile):
        """Test creating slot with end before start fails."""
        start = (datetime.utcnow() + timedelta(days=2, hours=1)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2)).isoformat()

        response = client.post("/doctor/slots", json={
            "start_at": start,
            "end_at": end
        }, headers=doctor_auth_headers)
        assert response.status_code == 400
        assert "end_at must be after start_at" in response.json()["detail"]

    def test_create_slot_overlap(self, client, doctor_auth_headers, doctor_profile, appointment_slot):
        """Test creating overlapping slot fails."""
        # Try to create slot that overlaps with existing
        start = appointment_slot.start_at.isoformat()
        end = appointment_slot.end_at.isoformat()

        response = client.post("/doctor/slots", json={
            "start_at": start,
            "end_at": end
        }, headers=doctor_auth_headers)
        assert response.status_code == 409
        assert "overlaps" in response.json()["detail"]

    def test_create_slot_unauthorized(self, client, auth_headers):
        """Test creating slot without doctor privileges."""
        start = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2, hours=1)).isoformat()

        response = client.post("/doctor/slots", json={
            "start_at": start,
            "end_at": end
        }, headers=auth_headers)
        assert response.status_code == 403

    def test_list_my_slots(self, client, doctor_auth_headers, appointment_slot):
        """Test listing doctor's own slots."""
        response = client.get("/doctor/slots", headers=doctor_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == appointment_slot.id

    def test_list_my_slots_empty(self, client, doctor_auth_headers, doctor_profile):
        """Test listing slots when doctor has none."""
        # doctor_profile fixture is used but no slots created
        response = client.get("/doctor/slots", headers=doctor_auth_headers)
        assert response.status_code == 200
        # Note: appointment_slot fixture is not included, so should be empty


class TestDeleteSlot:
    """Tests for slot deletion."""

    def test_delete_slot_success(self, client, doctor_auth_headers, doctor_profile, db_session):
        """Test deleting a slot that has no appointments."""
        from app.models.appointment_slot import AppointmentSlot
        from datetime import datetime, timedelta

        # Create a slot with no appointments
        slot = AppointmentSlot(
            doctor_id=doctor_profile.id,
            start_at=datetime.utcnow() + timedelta(days=5),
            end_at=datetime.utcnow() + timedelta(days=5, hours=1),
            is_available=1
        )
        db_session.add(slot)
        db_session.commit()
        db_session.refresh(slot)
        slot_id = slot.id

        response = client.delete(f"/doctor/slots/{slot_id}", headers=doctor_auth_headers)
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert response.json()["deleted_slot_id"] == slot_id

    def test_delete_slot_not_found(self, client, doctor_auth_headers, doctor_profile):
        """Test deleting non-existent slot."""
        response = client.delete("/doctor/slots/99999", headers=doctor_auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_slot_forbidden(self, client, doctor_auth_headers, doctor_profile, db_session):
        """Test deleting slot owned by another doctor."""
        from app.models.appointment_slot import AppointmentSlot
        from app.models.doctor_profile import DoctorProfile
        from app.models.user import User
        from app.core.security import hash_password
        from datetime import datetime, timedelta

        # Create another doctor
        other_user = User(
            email="other.doctor@test.com",
            username="otherdoctor",
            password_hash=hash_password("Test1234!"),
            role="DOCTOR"
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_profile = DoctorProfile(
            user_id=other_user.id,
            specialty_id=doctor_profile.specialty_id,
            full_name="Other Doctor",
            bio="Another bio"
        )
        db_session.add(other_profile)
        db_session.commit()
        db_session.refresh(other_profile)

        # Create a slot owned by other doctor
        other_slot = AppointmentSlot(
            doctor_id=other_profile.id,
            start_at=datetime.utcnow() + timedelta(days=6),
            end_at=datetime.utcnow() + timedelta(days=6, hours=1),
            is_available=1
        )
        db_session.add(other_slot)
        db_session.commit()
        db_session.refresh(other_slot)

        # Try to delete with first doctor's auth
        response = client.delete(f"/doctor/slots/{other_slot.id}", headers=doctor_auth_headers)
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]

    def test_delete_slot_with_appointment(self, client, doctor_auth_headers, appointment):
        """Test deleting slot that has an appointment fails."""
        slot_id = appointment.slot_id

        response = client.delete(f"/doctor/slots/{slot_id}", headers=doctor_auth_headers)
        assert response.status_code == 409
        assert "active appointment" in response.json()["detail"]

    def test_delete_slot_unauthorized(self, client, auth_headers, appointment_slot):
        """Test non-doctor cannot delete slots."""
        response = client.delete(f"/doctor/slots/{appointment_slot.id}", headers=auth_headers)
        assert response.status_code == 403


class TestDoctorProfileMissing:
    """Tests for when doctor profile is missing."""

    def test_create_slot_no_profile(self, client, db_session):
        """Test creating slot when doctor has no profile."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token
        from datetime import datetime, timedelta

        # Create a doctor user without profile
        doc_user = User(
            email="noprofile@example.com",
            username="noprofile",
            password_hash=hash_password("password123"),
            role="DOCTOR"
        )
        db_session.add(doc_user)
        db_session.commit()

        token = create_access_token(str(doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        start = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2, hours=1)).isoformat()

        response = client.post("/doctor/slots", json={
            "start_at": start,
            "end_at": end
        }, headers=headers)
        assert response.status_code == 404
        assert "Doctor profile missing" in response.json()["detail"]

    def test_list_slots_no_profile(self, client, db_session):
        """Test listing slots when doctor has no profile."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        doc_user = User(
            email="noprofile2@example.com",
            username="noprofile2",
            password_hash=hash_password("password123"),
            role="DOCTOR"
        )
        db_session.add(doc_user)
        db_session.commit()

        token = create_access_token(str(doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/doctor/slots", headers=headers)
        assert response.status_code == 404

    def test_delete_slot_no_profile(self, client, db_session):
        """Test deleting slot when doctor has no profile."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        doc_user = User(
            email="noprofile3@example.com",
            username="noprofile3",
            password_hash=hash_password("password123"),
            role="DOCTOR"
        )
        db_session.add(doc_user)
        db_session.commit()

        token = create_access_token(str(doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.delete("/doctor/slots/1", headers=headers)
        assert response.status_code == 404

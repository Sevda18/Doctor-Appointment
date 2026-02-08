"""
Unit tests for doctor profile endpoints.
"""
import pytest


class TestDoctorProfile:
    """Tests for doctor profile management."""

    def test_get_my_profile(self, client, doctor_auth_headers, doctor_profile):
        """Test doctor getting their own profile."""
        response = client.get("/doctor/me", headers=doctor_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "doctor_user" in data
        assert "profile" in data
        assert "specialty" in data
        assert "stats" in data
        assert data["profile"]["full_name"] == "Dr. John Smith"

    def test_get_my_profile_not_found(self, client, db_session):
        """Test doctor without profile."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        doc_user = User(
            email="noprofile_doc@example.com",
            username="noprofile_doc",
            password_hash=hash_password("password123"),
            role="DOCTOR",
        )
        db_session.add(doc_user)
        db_session.commit()

        token = create_access_token(str(doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/doctor/me", headers=headers)
        assert response.status_code == 404

    def test_create_profile(self, client, specialty, db_session):
        """Test creating a doctor profile."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        doc_user = User(
            email="newdoc@example.com",
            username="newdoc",
            password_hash=hash_password("password123"),
            role="DOCTOR",
        )
        db_session.add(doc_user)
        db_session.commit()

        token = create_access_token(str(doc_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/doctor/me", json={
            "full_name": "Dr. New Doctor",
            "bio": "New bio",
            "clinic_name": "New Clinic",
            "address": "New Address",
            "phone": "555-NEW",
            "specialty_id": specialty.id
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Dr. New Doctor"

    def test_update_profile(self, client, doctor_auth_headers, doctor_profile, specialty):
        """Test updating an existing doctor profile."""
        response = client.post("/doctor/me", json={
            "full_name": "Dr. Updated Name",
            "bio": "Updated bio",
            "clinic_name": "Updated Clinic",
            "address": "Updated Address",
            "phone": "555-UPD",
            "specialty_id": specialty.id
        }, headers=doctor_auth_headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Dr. Updated Name"

    def test_get_profile_unauthorized(self, client):
        """Test accessing doctor profile without auth."""
        response = client.get("/doctor/me")
        assert response.status_code == 401

    def test_get_profile_as_user(self, client, auth_headers):
        """Test regular user cannot access doctor profile."""
        response = client.get("/doctor/me", headers=auth_headers)
        assert response.status_code == 403

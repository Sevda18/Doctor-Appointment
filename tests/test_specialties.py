"""
Unit tests for specialty endpoints.
"""
import pytest


class TestListSpecialties:
    """Tests for listing specialties."""

    def test_list_specialties_empty(self, client):
        """Test listing specialties when none exist."""
        response = client.get("/specialties")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_specialties(self, client, specialty):
        """Test listing all specialties."""
        response = client.get("/specialties")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Cardiology"

    def test_list_specialties_sorted(self, client, db_session):
        """Test specialties are sorted by name."""
        from app.models.specialty import Specialty

        spec1 = Specialty(name="Neurology")
        spec2 = Specialty(name="Cardiology")
        spec3 = Specialty(name="Dermatology")
        db_session.add_all([spec1, spec2, spec3])
        db_session.commit()

        response = client.get("/specialties")
        assert response.status_code == 200
        data = response.json()
        names = [s["name"] for s in data]
        assert names == sorted(names)


class TestCreateSpecialty:
    """Tests for creating specialties (admin only)."""

    def test_create_specialty_success(self, client, admin_auth_headers):
        """Test admin creating a specialty."""
        response = client.post("/specialties", json={
            "name": "Neurology"
        }, headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Neurology"

    def test_create_specialty_duplicate(self, client, admin_auth_headers, specialty):
        """Test creating duplicate specialty fails."""
        response = client.post("/specialties", json={
            "name": "Cardiology"
        }, headers=admin_auth_headers)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_specialty_unauthorized(self, client):
        """Test creating specialty without authentication."""
        response = client.post("/specialties", json={
            "name": "Neurology"
        })
        assert response.status_code == 401

    def test_create_specialty_user_forbidden(self, client, auth_headers):
        """Test regular user cannot create specialty."""
        response = client.post("/specialties", json={
            "name": "Neurology"
        }, headers=auth_headers)
        assert response.status_code == 403

    def test_create_specialty_doctor_forbidden(self, client, doctor_auth_headers):
        """Test doctor cannot create specialty."""
        response = client.post("/specialties", json={
            "name": "Neurology"
        }, headers=doctor_auth_headers)
        assert response.status_code == 403

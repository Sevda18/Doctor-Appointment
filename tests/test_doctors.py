"""
Unit tests for doctor endpoints.
"""
import pytest


class TestListDoctors:
    """Tests for listing doctors."""

    def test_list_doctors_empty(self, client):
        """Test listing doctors when none exist."""
        response = client.get("/doctors")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_doctors(self, client, doctor_profile):
        """Test listing all doctors."""
        response = client.get("/doctors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["full_name"] == "Dr. John Smith"

    def test_filter_doctors_by_specialty_id(self, client, doctor_profile, specialty):
        """Test filtering doctors by specialty_id."""
        response = client.get(f"/doctors?specialty_id={specialty.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["specialty"]["id"] == specialty.id

    def test_filter_doctors_by_specialty_name(self, client, doctor_profile):
        """Test filtering doctors by specialty name."""
        response = client.get("/doctors?specialty_name=Cardiology")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_filter_doctors_by_name(self, client, doctor_profile):
        """Test filtering doctors by name."""
        response = client.get("/doctors?name=John")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "John" in data[0]["full_name"]

    def test_filter_doctors_by_name_no_match(self, client, doctor_profile):
        """Test filtering doctors by name with no matches."""
        response = client.get("/doctors?name=NonExistent")
        assert response.status_code == 200
        assert response.json() == []

    def test_filter_doctors_by_active_status(self, client, doctor_profile):
        """Test filtering doctors by active status."""
        response = client.get("/doctors?is_active=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_filter_doctors_by_date(self, client, doctor_profile, appointment_slot):
        """Test filtering doctors by available date."""
        from datetime import datetime, timedelta
        # appointment_slot is already in the future
        date_str = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.get(f"/doctors?date={date_str}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == doctor_profile.id

    def test_filter_doctors_by_date_no_slots(self, client, doctor_profile):
        """Test filtering by date with no available slots."""
        from datetime import datetime, timedelta
        future_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
        response = client.get(f"/doctors?date={future_date}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGetDoctor:
    """Tests for getting a specific doctor."""

    def test_get_doctor_by_id(self, client, doctor_profile):
        """Test getting a specific doctor."""
        response = client.get(f"/doctors/{doctor_profile.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doctor_profile.id
        assert data["full_name"] == "Dr. John Smith"
        assert "avg_rating" in data
        assert "reviews_count" in data

    def test_get_doctor_not_found(self, client):
        """Test getting non-existent doctor."""
        response = client.get("/doctors/9999")
        assert response.status_code == 404
        assert "Doctor not found" in response.json()["detail"]

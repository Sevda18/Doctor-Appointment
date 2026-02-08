"""
Unit tests for public slots endpoints.
"""
import pytest
from datetime import datetime, timedelta


class TestPublicSlots:
    """Tests for public slot viewing."""

    def test_list_available_slots(self, client, doctor_profile, appointment_slot):
        """Test listing available slots for a doctor."""
        response = client.get(f"/doctors/{doctor_profile.id}/slots")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_available_slots_empty(self, client, doctor_profile):
        """Test listing slots when none available."""
        response = client.get(f"/doctors/{doctor_profile.id}/slots")
        assert response.status_code == 200

    def test_list_available_slots_with_from_dt(self, client, doctor_profile, appointment_slot):
        """Test filtering slots with from_dt parameter."""
        from_dt = datetime.utcnow().isoformat()
        response = client.get(f"/doctors/{doctor_profile.id}/slots?from_dt={from_dt}")
        assert response.status_code == 200

    def test_list_available_slots_invalid_from_dt(self, client, doctor_profile):
        """Test invalid from_dt format."""
        response = client.get(f"/doctors/{doctor_profile.id}/slots?from_dt=invalid")
        assert response.status_code == 422
        assert "ISO datetime" in response.json()["detail"]

    def test_list_available_slots_unavailable_not_shown(self, client, doctor_profile, appointment_slot, db_session):
        """Test unavailable slots are not shown."""
        appointment_slot.is_available = 0
        db_session.commit()

        response = client.get(f"/doctors/{doctor_profile.id}/slots")
        assert response.status_code == 200
        data = response.json()
        # The unavailable slot should not appear
        assert all(s["is_available"] == 1 for s in data)

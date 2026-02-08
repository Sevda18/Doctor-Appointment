"""
Unit tests for notification endpoints.
"""
import pytest


class TestNotificationEndpoints:
    """Tests for notification routes."""

    def test_get_user_notifications_empty(self, client, auth_headers):
        """Test getting notifications when none exist."""
        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_user_notifications(self, client, auth_headers, test_user, db_session):
        """Test getting user's notifications."""
        from app.models.notification import Notification

        notif = Notification(
            user_id=test_user.id,
            message="Your appointment has been confirmed"
        )
        db_session.add(notif)
        db_session.commit()

        response = client.get("/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "confirmed" in data[0]["message"]

    def test_get_doctor_notifications(self, client, doctor_auth_headers, doctor_user, db_session):
        """Test doctor can get notifications."""
        from app.models.notification import Notification

        notif = Notification(
            user_id=doctor_user.id,
            message="New appointment request"
        )
        db_session.add(notif)
        db_session.commit()

        response = client.get("/notifications", headers=doctor_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_notifications_unauthorized(self, client):
        """Test accessing notifications without authentication."""
        response = client.get("/notifications")
        assert response.status_code == 401

"""
Unit tests for user endpoints.
"""
import pytest


class TestUserEndpoints:
    """Tests for user routes."""

    def test_get_current_user(self, client, auth_headers, test_user):
        """Test getting current user profile."""
        response = client.get("/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username

    def test_get_user_unauthorized(self, client):
        """Test accessing user endpoint without authentication."""
        response = client.get("/me")
        assert response.status_code == 401

    def test_get_user_invalid_token(self, client):
        """Test accessing user endpoint with invalid token."""
        response = client.get("/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

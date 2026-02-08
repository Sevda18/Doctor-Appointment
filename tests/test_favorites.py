"""
Unit tests for favorites endpoints.
"""
import pytest


class TestAddFavorite:
    """Tests for adding favorite doctors."""

    def test_add_favorite_doctor(self, client, auth_headers, doctor_profile):
        """Test adding a doctor to favorites."""
        response = client.post(
            f"/favorites/doctors/{doctor_profile.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["doctor_id"] == doctor_profile.id

    def test_add_favorite_duplicate(self, client, auth_headers, doctor_profile, test_user, db_session):
        """Test adding same doctor again returns already_favorite."""
        from app.models.favorite import Favorite

        # Create existing favorite
        fav = Favorite(user_id=test_user.id, doctor_id=doctor_profile.id)
        db_session.add(fav)
        db_session.commit()

        response = client.post(
            f"/favorites/doctors/{doctor_profile.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["already_favorite"] is True

    def test_add_favorite_doctor_not_found(self, client, auth_headers):
        """Test adding non-existent doctor to favorites."""
        response = client.post("/favorites/doctors/9999", headers=auth_headers)
        assert response.status_code == 404
        assert "Doctor not found" in response.json()["detail"]

    def test_add_favorite_unauthorized(self, client, doctor_profile):
        """Test adding favorite without authentication."""
        response = client.post(f"/favorites/doctors/{doctor_profile.id}")
        assert response.status_code == 401


class TestListFavorites:
    """Tests for listing favorite doctors."""

    def test_get_favorite_doctors_empty(self, client, auth_headers):
        """Test getting favorites when none exist."""
        response = client.get("/favorites", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_favorite_doctors(self, client, auth_headers, doctor_profile, test_user, db_session):
        """Test getting user's favorite doctors."""
        from app.models.favorite import Favorite

        fav = Favorite(user_id=test_user.id, doctor_id=doctor_profile.id)
        db_session.add(fav)
        db_session.commit()

        response = client.get("/favorites", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["doctor_id"] == doctor_profile.id
        assert data[0]["doctor_name"] == "Dr. John Smith"
        assert data[0]["specialty_name"] == "Cardiology"

    def test_get_favorites_unauthorized(self, client):
        """Test getting favorites without authentication."""
        response = client.get("/favorites")
        assert response.status_code == 401


class TestRemoveFavorite:
    """Tests for removing favorite doctors."""

    def test_remove_favorite_doctor(self, client, auth_headers, doctor_profile, test_user, db_session):
        """Test removing a doctor from favorites."""
        from app.models.favorite import Favorite

        # Create favorite first
        fav = Favorite(user_id=test_user.id, doctor_id=doctor_profile.id)
        db_session.add(fav)
        db_session.commit()

        response = client.delete(
            f"/favorites/doctors/{doctor_profile.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["doctor_id"] == doctor_profile.id

    def test_remove_favorite_not_in_favorites(self, client, auth_headers, doctor_profile):
        """Test removing doctor that is not in favorites."""
        response = client.delete(
            f"/favorites/doctors/{doctor_profile.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "Not in favorites" in response.json()["detail"]

    def test_remove_favorite_unauthorized(self, client, doctor_profile):
        """Test removing favorite without authentication."""
        response = client.delete(f"/favorites/doctors/{doctor_profile.id}")
        assert response.status_code == 401

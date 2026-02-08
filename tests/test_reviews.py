"""
Unit tests for review endpoints.
"""
import pytest


class TestListReviews:
    """Tests for listing doctor reviews."""

    def test_list_reviews_empty(self, client, doctor_profile):
        """Test listing reviews when none exist."""
        response = client.get(f"/doctors/{doctor_profile.id}/reviews")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_reviews(self, client, doctor_profile, test_user, db_session):
        """Test listing reviews for a doctor."""
        from app.models.review import Review

        review = Review(
            user_id=test_user.id,
            doctor_id=doctor_profile.id,
            rating=5,
            comment="Excellent doctor!"
        )
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/doctors/{doctor_profile.id}/reviews")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rating"] == 5
        assert data[0]["comment"] == "Excellent doctor!"

    def test_list_reviews_doctor_not_found(self, client):
        """Test listing reviews for non-existent doctor."""
        response = client.get("/doctors/9999/reviews")
        assert response.status_code == 404


class TestCreateReview:
    """Tests for creating reviews."""

    def test_create_review_success(self, client, auth_headers, doctor_profile):
        """Test creating a review for a doctor."""
        response = client.post(f"/doctors/{doctor_profile.id}/reviews", json={
            "rating": 5,
            "comment": "Great experience!"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Great experience!"

    def test_create_review_without_comment(self, client, auth_headers, doctor_profile):
        """Test creating a review without comment."""
        response = client.post(f"/doctors/{doctor_profile.id}/reviews", json={
            "rating": 4
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4

    def test_create_review_duplicate(self, client, auth_headers, doctor_profile, test_user, db_session):
        """Test creating duplicate review fails."""
        from app.models.review import Review

        # Create existing review
        review = Review(
            user_id=test_user.id,
            doctor_id=doctor_profile.id,
            rating=4,
            comment="Good"
        )
        db_session.add(review)
        db_session.commit()

        response = client.post(f"/doctors/{doctor_profile.id}/reviews", json={
            "rating": 5,
            "comment": "Another review"
        }, headers=auth_headers)
        assert response.status_code == 409
        assert "already reviewed" in response.json()["detail"]

    def test_create_review_doctor_not_found(self, client, auth_headers):
        """Test creating review for non-existent doctor."""
        response = client.post("/doctors/9999/reviews", json={
            "rating": 5,
            "comment": "Test"
        }, headers=auth_headers)
        assert response.status_code == 404

    def test_create_review_unauthorized(self, client, doctor_profile):
        """Test creating review without authentication."""
        response = client.post(f"/doctors/{doctor_profile.id}/reviews", json={
            "rating": 5,
            "comment": "Test"
        })
        assert response.status_code == 401

    def test_create_review_invalid_rating(self, client, auth_headers, doctor_profile):
        """Test creating review with invalid rating."""
        response = client.post(f"/doctors/{doctor_profile.id}/reviews", json={
            "rating": 10,
            "comment": "Test"
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_create_review_integrity_error(self, client, auth_headers, doctor_profile, test_user, db_session):
        """Test IntegrityError handling when duplicate review created concurrently."""
        from unittest.mock import patch
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy.orm import Session

        # Mock commit to raise IntegrityError
        original_commit = Session.commit

        call_count = [0]
        def mock_commit(self):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call succeeds normally (for adding the review)
                raise IntegrityError("duplicate key", None, None)
            return original_commit(self)

        with patch.object(Session, 'commit', mock_commit):
            response = client.post(f"/doctors/{doctor_profile.id}/reviews", json={
                "rating": 5,
                "comment": "Test review"
            }, headers=auth_headers)
            assert response.status_code == 409
            assert "already reviewed" in response.json()["detail"]


class TestMyReviews:
    """Tests for user's own reviews."""

    def test_my_reviews_empty(self, client, auth_headers):
        """Test getting own reviews when none exist."""
        response = client.get("/doctors/mine", headers=auth_headers)
        assert response.status_code == 200

    def test_my_reviews(self, client, auth_headers, doctor_profile, test_user, db_session):
        """Test getting user's own reviews."""
        from app.models.review import Review

        review = Review(
            user_id=test_user.id,
            doctor_id=doctor_profile.id,
            rating=5,
            comment="My review"
        )
        db_session.add(review)
        db_session.commit()

        response = client.get("/doctors/mine", headers=auth_headers)
        assert response.status_code == 200

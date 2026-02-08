"""
Unit tests for core security and authentication modules.
"""
import pytest


class TestSecurity:
    """Tests for security functions."""

    def test_hash_password(self):
        """Test password hashing."""
        from app.core.security import hash_password
        hashed = hash_password("testpassword")
        assert hashed != "testpassword"
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        from app.core.security import hash_password, verify_password
        hashed = hash_password("testpassword")
        assert verify_password("testpassword", hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        from app.core.security import hash_password, verify_password
        hashed = hash_password("testpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        """Test creating access token."""
        from app.core.security import create_access_token
        token = create_access_token("123")
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test decoding access token."""
        from app.core.security import create_access_token, decode_access_token
        token = create_access_token("456")
        subject = decode_access_token(token)
        assert subject == "456"

    def test_decode_access_token_invalid(self):
        """Test decoding invalid token returns None."""
        from app.core.security import decode_access_token
        subject = decode_access_token("invalid_token")
        assert subject is None


class TestAuth:
    """Tests for auth module."""

    def test_get_current_user_invalid_token(self, client):
        """Test invalid token returns 401."""
        response = client.get("/me", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401

    def test_get_current_user_no_token(self, client):
        """Test missing token returns 401."""
        response = client.get("/me")
        assert response.status_code == 401

    def test_get_current_user_user_not_found(self, client, db_session):
        """Test token for deleted user returns 401."""
        from app.core.security import create_access_token

        # Create token for non-existent user
        token = create_access_token("99999")
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_get_current_user_missing_sub(self, client, db_session):
        """Test token without sub claim returns 401."""
        from jose import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        from datetime import datetime, timedelta

        # Create token without 'sub' claim
        payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_appointments_invalid_token(self, client, db_session):
        """Test appointments endpoint with invalid token returns 401."""
        response = client.get("/appointments/mine", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

    def test_appointments_user_not_found(self, client, db_session):
        """Test appointments endpoint with token for deleted user returns 401."""
        from app.core.security import create_access_token

        # Create token for non-existent user
        token = create_access_token("99999")
        response = client.get("/appointments/mine", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


class TestRoleRequirement:
    """Tests for role-based access control."""

    def test_require_role_admin_success(self, client, admin_auth_headers):
        """Test admin can access admin endpoints."""
        response = client.get("/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_require_role_admin_forbidden_for_user(self, client, auth_headers):
        """Test regular user cannot access admin endpoints."""
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 403

    def test_require_role_doctor_success(self, client, doctor_auth_headers, doctor_profile):
        """Test doctor can access doctor endpoints."""
        response = client.get("/doctor/me", headers=doctor_auth_headers)
        assert response.status_code == 200

    def test_require_role_doctor_forbidden_for_user(self, client, auth_headers):
        """Test regular user cannot access doctor endpoints."""
        response = client.get("/doctor/me", headers=auth_headers)
        assert response.status_code == 403

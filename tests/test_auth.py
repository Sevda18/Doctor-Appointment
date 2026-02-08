"""
Unit tests for authentication endpoints.
"""
import pytest


class TestRegisterClient:
    """Tests for client registration."""

    def test_register_client_with_email(self, client):
        """Test successful client registration with email."""
        response = client.post("/auth/register-client", json={
            "email": "newuser@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_register_client_with_username(self, client):
        """Test successful client registration with username."""
        response = client.post("/auth/register-client", json={
            "username": "newuser",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_register_client_no_email_or_username(self, client):
        """Test registration fails without email or username."""
        response = client.post("/auth/register-client", json={
            "password": "password123"
        })
        assert response.status_code == 400
        assert "Provide email or username" in response.json()["detail"]

    def test_register_client_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        response = client.post("/auth/register-client", json={
            "email": "testuser@example.com",
            "password": "password123"
        })
        assert response.status_code == 409
        assert "Email already used" in response.json()["detail"]

    def test_register_client_duplicate_username(self, client, test_user):
        """Test registration with duplicate username fails."""
        response = client.post("/auth/register-client", json={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 409
        assert "Username already used" in response.json()["detail"]

    def test_register_client_short_password(self, client):
        """Test registration with short password fails."""
        response = client.post("/auth/register-client", json={
            "email": "user@example.com",
            "password": "12345"
        })
        assert response.status_code == 422


class TestRegisterDoctor:
    """Tests for doctor registration."""

    def test_register_doctor_success(self, client, specialty):
        """Test successful doctor registration."""
        response = client.post("/auth/register-doctor", json={
            "email": "newdoctor@example.com",
            "password": "password123",
            "full_name": "Dr. Jane Doe",
            "bio": "Specialist in cardiology",
            "clinic_name": "Heart Center",
            "address": "456 Health Ave",
            "phone": "555-9999",
            "specialty_id": specialty.id
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_register_doctor_invalid_specialty(self, client):
        """Test doctor registration with invalid specialty fails."""
        response = client.post("/auth/register-doctor", json={
            "email": "newdoctor@example.com",
            "password": "password123",
            "full_name": "Dr. Jane Doe",
            "bio": "Specialist",
            "clinic_name": "Clinic",
            "address": "Address",
            "phone": "555-0000",
            "specialty_id": 9999
        })
        assert response.status_code == 400
        assert "Invalid specialty_id" in response.json()["detail"]

    def test_register_doctor_no_specialty(self, client):
        """Test doctor registration without specialty fails."""
        response = client.post("/auth/register-doctor", json={
            "email": "newdoctor@example.com",
            "password": "password123",
            "full_name": "Dr. Jane Doe",
            "bio": "Specialist",
            "clinic_name": "Clinic",
            "address": "Address",
            "phone": "555-0000",
            "specialty_id": 0
        })
        assert response.status_code == 400

    def test_register_doctor_no_email_or_username(self, client, specialty):
        """Test doctor registration without email or username fails."""
        response = client.post("/auth/register-doctor", json={
            "password": "password123",
            "full_name": "Dr. Jane Doe",
            "bio": "Specialist",
            "clinic_name": "Clinic",
            "address": "Address",
            "phone": "555-0000",
            "specialty_id": specialty.id
        })
        assert response.status_code == 400
        assert "Provide email or username" in response.json()["detail"]

    def test_register_doctor_duplicate_email(self, client, specialty, doctor_user):
        """Test doctor registration with duplicate email fails."""
        response = client.post("/auth/register-doctor", json={
            "email": "doctor@example.com",
            "password": "password123",
            "full_name": "Dr. Jane Doe",
            "bio": "Specialist",
            "clinic_name": "Clinic",
            "address": "Address",
            "phone": "555-0000",
            "specialty_id": specialty.id
        })
        assert response.status_code == 409
        assert "Email already used" in response.json()["detail"]

    def test_register_doctor_duplicate_username(self, client, specialty, doctor_user):
        """Test doctor registration with duplicate username fails."""
        response = client.post("/auth/register-doctor", json={
            "username": "doctor",
            "password": "password123",
            "full_name": "Dr. Jane Doe",
            "bio": "Specialist",
            "clinic_name": "Clinic",
            "address": "Address",
            "phone": "555-0000",
            "specialty_id": specialty.id
        })
        assert response.status_code == 409
        assert "Username already used" in response.json()["detail"]


class TestLogin:
    """Tests for login endpoint."""

    def test_login_with_email_success(self, client, test_user):
        """Test successful login with email."""
        response = client.post("/auth/login", data={
            "username": "testuser@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_with_username_success(self, client, test_user):
        """Test successful login with username."""
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post("/auth/login", data={
            "username": "testuser@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post("/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "password123"
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

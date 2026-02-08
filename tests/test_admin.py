"""
Unit tests for admin endpoints.
"""
import pytest


class TestAdminUsers:
    """Tests for admin user management."""

    def test_list_users(self, client, admin_auth_headers, test_user):
        """Test listing all users."""
        response = client.get("/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_users_filter_by_role(self, client, admin_auth_headers, test_user):
        """Test filtering users by role."""
        response = client.get("/admin/users?role=USER", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(u["role"] == "USER" for u in data)

    def test_list_users_search(self, client, admin_auth_headers, test_user):
        """Test searching users by email/username."""
        response = client.get("/admin/users?q=testuser", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_delete_user(self, client, admin_auth_headers, test_user):
        """Test deleting a user."""
        response = client.delete(f"/admin/users/{test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_delete_user_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent user."""
        response = client.delete("/admin/users/9999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_last_admin(self, client, admin_auth_headers, admin_user):
        """Test cannot delete the last admin."""
        response = client.delete(f"/admin/users/{admin_user.id}", headers=admin_auth_headers)
        assert response.status_code == 409
        assert "last ADMIN" in response.json()["detail"]

    def test_list_users_unauthorized(self, client, auth_headers):
        """Test regular user cannot access admin endpoints."""
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == 403


class TestAdminSpecialties:
    """Tests for admin specialty management."""

    def test_list_specialties_admin(self, client, admin_auth_headers, specialty):
        """Test admin listing specialties."""
        response = client.get("/admin/specialties", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_create_specialty_admin(self, client, admin_auth_headers):
        """Test admin creating specialty via admin endpoint."""
        response = client.post("/admin/specialties?name=Dermatology", headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Dermatology"

    def test_create_specialty_duplicate_admin(self, client, admin_auth_headers, specialty):
        """Test creating duplicate specialty."""
        response = client.post("/admin/specialties?name=Cardiology", headers=admin_auth_headers)
        assert response.status_code == 409

    def test_rename_specialty(self, client, admin_auth_headers, specialty):
        """Test renaming a specialty."""
        response = client.put(
            f"/admin/specialties/{specialty.id}?name=Heart Medicine",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Heart Medicine"

    def test_rename_specialty_not_found(self, client, admin_auth_headers):
        """Test renaming non-existent specialty."""
        response = client.put("/admin/specialties/9999?name=Test", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_specialty_admin(self, client, admin_auth_headers, db_session):
        """Test admin deleting specialty."""
        from app.models.specialty import Specialty
        spec = Specialty(name="ToDelete")
        db_session.add(spec)
        db_session.commit()

        response = client.delete(f"/admin/specialties/{spec.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_specialty_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent specialty."""
        response = client.delete("/admin/specialties/9999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_specialty_in_use(self, client, admin_auth_headers, specialty, doctor_profile):
        """Test cannot delete specialty used by doctors."""
        response = client.delete(f"/admin/specialties/{specialty.id}", headers=admin_auth_headers)
        assert response.status_code == 409
        assert "used by doctors" in response.json()["detail"]


class TestAdminDoctors:
    """Tests for admin doctor management."""

    def test_list_doctors_admin(self, client, admin_auth_headers, doctor_profile):
        """Test admin listing doctors."""
        response = client.get("/admin/doctors", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_doctors_filter_active(self, client, admin_auth_headers, doctor_profile):
        """Test filtering doctors by active status."""
        response = client.get("/admin/doctors?is_active=1", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_list_doctors_filter_specialty(self, client, admin_auth_headers, doctor_profile, specialty):
        """Test filtering doctors by specialty."""
        response = client.get(f"/admin/doctors?specialty_id={specialty.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_list_doctors_search(self, client, admin_auth_headers, doctor_profile):
        """Test searching doctors."""
        response = client.get("/admin/doctors?q=John", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_set_doctor_active(self, client, admin_auth_headers, doctor_profile):
        """Test setting doctor active status."""
        response = client.patch(
            f"/admin/doctors/{doctor_profile.id}/active?is_active=0",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["is_active"] == 0

    def test_set_doctor_active_not_found(self, client, admin_auth_headers):
        """Test setting active for non-existent doctor."""
        response = client.patch("/admin/doctors/9999/active?is_active=1", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_delete_doctor_admin(self, client, admin_auth_headers, doctor_profile):
        """Test admin deleting doctor profile."""
        response = client.delete(f"/admin/doctors/{doctor_profile.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_doctor_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent doctor."""
        response = client.delete("/admin/doctors/9999", headers=admin_auth_headers)
        assert response.status_code == 404


class TestAdminSlots:
    """Tests for admin slot management."""

    def test_list_doctor_slots_admin(self, client, admin_auth_headers, doctor_profile, appointment_slot):
        """Test admin listing doctor's slots."""
        response = client.get(f"/admin/doctors/{doctor_profile.id}/slots", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_doctor_slots_filter_available(self, client, admin_auth_headers, doctor_profile, appointment_slot):
        """Test filtering slots by availability."""
        response = client.get(
            f"/admin/doctors/{doctor_profile.id}/slots?only_available=1",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    def test_list_doctor_slots_filter_day(self, client, admin_auth_headers, doctor_profile, appointment_slot):
        """Test filtering slots by day."""
        from datetime import datetime, timedelta
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.get(
            f"/admin/doctors/{doctor_profile.id}/slots?day={tomorrow}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    def test_delete_slot_admin(self, client, admin_auth_headers, appointment_slot):
        """Test admin deleting a slot."""
        response = client.delete(f"/admin/slots/{appointment_slot.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_slot_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent slot."""
        response = client.delete("/admin/slots/9999", headers=admin_auth_headers)
        assert response.status_code == 404


class TestAdminAppointments:
    """Tests for admin appointment management."""

    def test_list_appointments_admin(self, client, admin_auth_headers, appointment):
        """Test admin listing appointments."""
        response = client.get("/admin/appointments", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_appointments_filter_status(self, client, admin_auth_headers, appointment):
        """Test filtering appointments by status."""
        response = client.get("/admin/appointments?status=PENDING", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_list_appointments_filter_doctor(self, client, admin_auth_headers, appointment, doctor_profile):
        """Test filtering appointments by doctor."""
        response = client.get(
            f"/admin/appointments?doctor_id={doctor_profile.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    def test_list_appointments_filter_patient(self, client, admin_auth_headers, appointment, test_user):
        """Test filtering appointments by patient."""
        response = client.get(
            f"/admin/appointments?patient_user_id={test_user.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200

    def test_delete_appointment_admin(self, client, admin_auth_headers, appointment):
        """Test admin deleting an appointment."""
        response = client.delete(f"/admin/appointments/{appointment.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_appointment_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent appointment."""
        response = client.delete("/admin/appointments/9999", headers=admin_auth_headers)
        assert response.status_code == 404


class TestAdminReviews:
    """Tests for admin review management."""

    def test_list_reviews_admin(self, client, admin_auth_headers, doctor_profile, test_user, db_session):
        """Test admin listing reviews."""
        from app.models.review import Review
        review = Review(user_id=test_user.id, doctor_id=doctor_profile.id, rating=5, comment="Great")
        db_session.add(review)
        db_session.commit()

        response = client.get("/admin/reviews", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_reviews_filter_doctor(self, client, admin_auth_headers, doctor_profile, test_user, db_session):
        """Test filtering reviews by doctor."""
        from app.models.review import Review
        review = Review(user_id=test_user.id, doctor_id=doctor_profile.id, rating=4)
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/admin/reviews?doctor_id={doctor_profile.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_list_reviews_filter_user(self, client, admin_auth_headers, doctor_profile, test_user, db_session):
        """Test filtering reviews by user."""
        from app.models.review import Review
        review = Review(user_id=test_user.id, doctor_id=doctor_profile.id, rating=3)
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/admin/reviews?user_id={test_user.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_review_admin(self, client, admin_auth_headers, doctor_profile, test_user, db_session):
        """Test admin deleting a review."""
        from app.models.review import Review
        review = Review(user_id=test_user.id, doctor_id=doctor_profile.id, rating=2)
        db_session.add(review)
        db_session.commit()

        response = client.delete(f"/admin/reviews/{review.id}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_delete_review_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent review."""
        response = client.delete("/admin/reviews/9999", headers=admin_auth_headers)
        assert response.status_code == 404

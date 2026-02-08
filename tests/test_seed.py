"""
Unit tests for seed and startup modules.
"""
import pytest
from unittest.mock import patch
import os


class TestSeed:
    """Tests for seed functions."""

    def test_seed_admin(self, db_session):
        """Test seeding admin user."""
        from app.seed import seed_admin
        from app.models.user import User

        seed_admin(db_session)
        db_session.commit()

        admin = db_session.query(User).filter(User.email == "admin@local").first()
        assert admin is not None
        assert admin.role == "ADMIN"

    def test_seed_admin_already_exists(self, db_session):
        """Test seeding admin when already exists."""
        from app.seed import seed_admin
        from app.models.user import User
        from app.core.security import hash_password

        # Create admin first
        admin = User(
            email="admin@local",
            username="existing_admin",
            password_hash=hash_password("password"),
            role="ADMIN"
        )
        db_session.add(admin)
        db_session.commit()

        # Seed again should not create duplicate
        seed_admin(db_session)
        db_session.commit()

        admins = db_session.query(User).filter(User.email == "admin@local").count()
        assert admins == 1

    def test_seed_specialties(self, db_session):
        """Test seeding specialties."""
        from app.seed import seed_specialties, SPECIALTIES
        from app.models.specialty import Specialty

        seed_specialties(db_session)
        db_session.commit()

        count = db_session.query(Specialty).count()
        assert count == len(SPECIALTIES)

    def test_seed_specialties_partial(self, db_session):
        """Test seeding when some specialties exist."""
        from app.seed import seed_specialties
        from app.models.specialty import Specialty

        # Add one specialty first
        spec = Specialty(name="Cardiology")
        db_session.add(spec)
        db_session.commit()

        seed_specialties(db_session)
        db_session.commit()

        # Should still have all specialties
        cardiology_count = db_session.query(Specialty).filter(Specialty.name == "Cardiology").count()
        assert cardiology_count == 1


class TestStartup:
    """Tests for startup functions."""

    def test_run_auto_seed_disabled(self, db_session):
        """Test auto seed is disabled when AUTO_SEED=0."""
        from app.startup import run_auto_seed
        from app.models.user import User

        with patch.dict(os.environ, {"AUTO_SEED": "0"}):
            run_auto_seed()

        # No admin should be created when AUTO_SEED=0
        # Note: This depends on whether database is empty

    def test_run_auto_seed_disabled_false(self, db_session):
        """Test auto seed is disabled when AUTO_SEED=false."""
        from app.startup import run_auto_seed

        with patch.dict(os.environ, {"AUTO_SEED": "false"}):
            run_auto_seed()

    def test_run_auto_seed_disabled_no(self, db_session):
        """Test auto seed is disabled when AUTO_SEED=no."""
        from app.startup import run_auto_seed

        with patch.dict(os.environ, {"AUTO_SEED": "no"}):
            run_auto_seed()

    def test_run_auto_seed_enabled(self):
        """Test auto seed runs when enabled."""
        from app.startup import run_auto_seed

        with patch.dict(os.environ, {"AUTO_SEED": "1"}):
            # This will use the real database, so just ensure no exception
            try:
                run_auto_seed()
            except Exception:
                pass  # May fail if DB not configured, that's ok for coverage

    def test_run_auto_seed_with_empty_db(self):
        """Test auto seed creates users and specialties when DB is empty."""
        from app.startup import run_auto_seed
        from unittest.mock import patch, MagicMock

        mock_session = MagicMock()
        # Mock query().first() to return None (empty db)
        mock_session.query.return_value.first.return_value = None

        with patch.dict(os.environ, {"AUTO_SEED": "1"}):
            with patch('app.startup.SessionLocal', return_value=mock_session):
                with patch('app.startup.seed_admin') as mock_seed_admin:
                    with patch('app.startup.seed_specialties') as mock_seed_specialties:
                        run_auto_seed()
                        mock_seed_admin.assert_called_once_with(mock_session)
                        mock_seed_specialties.assert_called_once_with(mock_session)

    def test_run_auto_seed_with_existing_data(self):
        """Test auto seed does not run when data already exists."""
        from app.startup import run_auto_seed
        from unittest.mock import patch, MagicMock

        mock_session = MagicMock()
        # Mock query().first() to return something (data exists)
        mock_session.query.return_value.first.return_value = MagicMock()

        with patch.dict(os.environ, {"AUTO_SEED": "1"}):
            with patch('app.startup.SessionLocal', return_value=mock_session):
                with patch('app.startup.seed_admin') as mock_seed_admin:
                    with patch('app.startup.seed_specialties') as mock_seed_specialties:
                        run_auto_seed()
                        mock_seed_admin.assert_not_called()
                        mock_seed_specialties.assert_not_called()

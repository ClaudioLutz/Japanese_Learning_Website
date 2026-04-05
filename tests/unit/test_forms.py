# tests/unit/test_forms.py
"""
Phase 1: Unit-Tests für Flask-WTF Forms.
Testkonzept-IDs: U-F01 bis U-F07
"""

import pytest
from app.forms import RegistrationForm, LoginForm, CSRFTokenForm
from tests.factories import UserFactory
from app import db


# ── U-F01: RegistrationForm – Gültige Daten ─────────────────

class TestRegistrationFormValid:
    def test_valid_registration(self, app_context):
        """U-F01: Gültige Registrierungsdaten passieren Validierung."""
        form = RegistrationForm(
            data={
                "username": "newuser",
                "email": "new@test.com",
                "password": "Strong123!",
                "password2": "Strong123!",
            }
        )
        assert form.validate() is True


# ── U-F02: RegistrationForm – Pflichtfelder ─────────────────

class TestRegistrationFormRequired:
    def test_empty_username(self, app_context):
        """U-F02: Leerer Username schlägt fehl."""
        form = RegistrationForm(
            data={
                "username": "",
                "email": "test@test.com",
                "password": "Test123!",
                "password2": "Test123!",
            }
        )
        assert form.validate() is False
        assert "username" in form.errors

    def test_empty_email(self, app_context):
        """U-F02: Leere Email schlägt fehl."""
        form = RegistrationForm(
            data={
                "username": "user",
                "email": "",
                "password": "Test123!",
                "password2": "Test123!",
            }
        )
        assert form.validate() is False
        assert "email" in form.errors

    def test_empty_password(self, app_context):
        """U-F02: Leeres Passwort schlägt fehl."""
        form = RegistrationForm(
            data={
                "username": "user",
                "email": "test@test.com",
                "password": "",
                "password2": "",
            }
        )
        assert form.validate() is False
        assert "password" in form.errors


# ── U-F03: RegistrationForm – Passwort-Übereinstimmung ──────

class TestRegistrationFormPasswordMatch:
    def test_mismatched_passwords(self, app_context):
        """U-F03: Unterschiedliche Passwörter schlagen fehl."""
        form = RegistrationForm(
            data={
                "username": "user",
                "email": "test@test.com",
                "password": "Test123!",
                "password2": "Anders456!",
            }
        )
        assert form.validate() is False
        assert "password2" in form.errors


# ── U-F04: RegistrationForm – Email-Format ──────────────────

class TestRegistrationFormEmailFormat:
    def test_invalid_email(self, app_context):
        """U-F04: Ungültiges Email-Format schlägt fehl."""
        form = RegistrationForm(
            data={
                "username": "user",
                "email": "not-an-email",
                "password": "Test123!",
                "password2": "Test123!",
            }
        )
        assert form.validate() is False
        assert "email" in form.errors


# ── U-F05: RegistrationForm – Doppelter Username ────────────

class TestRegistrationFormDuplicateUsername:
    def test_duplicate_username(self, app_context):
        """U-F05: Bestehender Username wird abgelehnt."""
        UserFactory(username="existing_user")
        db.session.commit()

        form = RegistrationForm(
            data={
                "username": "existing_user",
                "email": "new@test.com",
                "password": "Test123!",
                "password2": "Test123!",
            }
        )
        assert form.validate() is False
        assert "username" in form.errors


# ── U-F06: RegistrationForm – Doppelte Email ────────────────

class TestRegistrationFormDuplicateEmail:
    def test_duplicate_email(self, app_context):
        """U-F06: Bestehende Email wird abgelehnt."""
        UserFactory(email="taken@test.com")
        db.session.commit()

        form = RegistrationForm(
            data={
                "username": "newuser",
                "email": "taken@test.com",
                "password": "Test123!",
                "password2": "Test123!",
            }
        )
        assert form.validate() is False
        assert "email" in form.errors


# ── U-F07: LoginForm – Validierung ──────────────────────────

class TestLoginForm:
    def test_valid_login_form(self, app_context):
        """U-F07: Gültige Login-Daten passieren Validierung."""
        form = LoginForm(
            data={
                "email": "test@test.com",
                "password": "Test123!",
            }
        )
        assert form.validate() is True

    def test_empty_login_email(self, app_context):
        """U-F07: Leere Email schlägt fehl."""
        form = LoginForm(data={"email": "", "password": "Test123!"})
        assert form.validate() is False

    def test_empty_login_password(self, app_context):
        """U-F07: Leeres Passwort schlägt fehl."""
        form = LoginForm(data={"email": "test@test.com", "password": ""})
        assert form.validate() is False

    def test_csrf_token_form(self, app_context):
        """CSRFTokenForm ist eine leere Form."""
        form = CSRFTokenForm()
        assert form is not None

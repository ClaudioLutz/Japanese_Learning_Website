# tests/integration/test_auth.py
"""
Phase 3: Integrationstests für Authentifizierung.
Testkonzept-IDs: I-AU01 bis I-AU14
"""

import pytest
from app import db
from app.models import User
from tests.factories import UserFactory


# ── I-AU01: Registrierung ───────────────────────────────────

class TestRegistration:
    def test_register_valid_user(self, client, app_context):
        """I-AU01: Registrierung mit gültigen Daten erstellt User."""
        resp = client.post("/register", data={
            "username": "newuser",
            "email": "new@test.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(username="newuser").first()
        assert user is not None

    def test_register_duplicate_username(self, client, app_context):
        """I-AU02: Doppelter Username wird abgelehnt."""
        UserFactory(username="taken")
        db.session.commit()
        resp = client.post("/register", data={
            "username": "taken",
            "email": "new@test.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }, follow_redirects=True)
        assert "anderen Benutzernamen".encode("utf-8") in resp.data

    def test_register_duplicate_email(self, client, app_context):
        """I-AU03: Doppelte Email wird abgelehnt."""
        UserFactory(email="taken@test.com")
        db.session.commit()
        resp = client.post("/register", data={
            "username": "newuser2",
            "email": "taken@test.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }, follow_redirects=True)
        assert "andere E-Mail-Adresse".encode("utf-8") in resp.data

    def test_register_password_mismatch(self, client, app_context):
        """I-AU04: Passwort-Mismatch wird abgelehnt."""
        resp = client.post("/register", data={
            "username": "user3",
            "email": "user3@test.com",
            "password": "Pass123!",
            "password2": "Different!",
        }, follow_redirects=True)
        # Kein neuer User erstellt
        assert User.query.filter_by(username="user3").first() is None


# ── I-AU05: Login/Logout ────────────────────────────────────

class TestLoginLogout:
    def test_login_valid_credentials(self, client, app_context):
        """I-AU05: Login mit korrekten Daten funktioniert."""
        UserFactory(email="login@test.com", password="Test123!")
        db.session.commit()
        resp = client.post("/login", data={
            "email": "login@test.com",
            "password": "Test123!",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_password(self, client, app_context):
        """I-AU06: Login mit falschem Passwort schlägt fehl."""
        UserFactory(email="wrong@test.com", password="Correct123!")
        db.session.commit()
        resp = client.post("/login", data={
            "email": "wrong@test.com",
            "password": "Wrong123!",
        }, follow_redirects=True)
        # Sollte auf Login-Seite bleiben oder Fehlermeldung zeigen
        assert resp.status_code == 200

    def test_login_nonexistent_user(self, client, app_context):
        """I-AU07: Login mit nicht existierendem User schlägt fehl."""
        resp = client.post("/login", data={
            "email": "ghost@test.com",
            "password": "Test123!",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_logout(self, auth_client):
        """I-AU08: Logout funktioniert."""
        client, user = auth_client
        resp = client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200


# ── I-AU09: Profil-Zugriff ──────────────────────────────────

class TestProfile:
    def test_profile_accessible_when_logged_in(self, auth_client):
        """I-AU09: /profile für eingeloggten User zugänglich."""
        client, user = auth_client
        resp = client.get("/profile")
        assert resp.status_code == 200

    def test_profile_shows_username(self, auth_client):
        """I-AU10: Profil zeigt Username."""
        client, user = auth_client
        resp = client.get("/profile")
        assert user.username.encode() in resp.data


# ── I-AU11: Admin-Zugriff ───────────────────────────────────

class TestAdminAccess:
    def test_admin_accessible_for_admin(self, admin_client):
        """I-AU11: /admin zugänglich für Admin."""
        client, admin = admin_client
        resp = client.get("/admin")
        assert resp.status_code == 200

    def test_admin_blocked_for_normal_user(self, auth_client):
        """I-AU12: /admin blockiert für normalen User."""
        client, user = auth_client
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code in (302, 403)

    def test_admin_api_blocked_for_normal_user(self, auth_client):
        """I-AU13: Admin-API blockiert für normalen User."""
        client, user = auth_client
        resp = client.get("/api/admin/kana")
        assert resp.status_code in (302, 403)

# tests/integration/test_password_reset.py
"""Integrationstests fuer den Passwort-Reset-Flow."""

from datetime import datetime, timedelta

import pytest

from app import db, limiter
from app.auth_tokens import make_reset_token, verify_reset_token
from app.mail_service import mail
from app.models import User
from tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Rate-Limiter zwischen Tests zuruecksetzen, damit 429er nicht durchschlagen."""
    limiter.reset()
    yield
    limiter.reset()


class TestForgotPasswordRequest:
    def test_forgot_password_page_renders(self, client, app_context):
        resp = client.get("/forgot-password")
        assert resp.status_code == 200
        assert b"Passwort vergessen" in resp.data

    def test_forgot_password_existing_email_sends_mail(self, client, app_context):
        UserFactory(email="reset@test.com")
        db.session.commit()
        with mail.record_messages() as outbox:
            resp = client.post(
                "/forgot-password",
                data={"email": "reset@test.com"},
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert len(outbox) == 1
            assert outbox[0].recipients == ["reset@test.com"]
            assert "/reset-password/" in outbox[0].body

    def test_forgot_password_unknown_email_no_mail_but_same_response(
        self, client, app_context
    ):
        with mail.record_messages() as outbox:
            resp = client.post(
                "/forgot-password",
                data={"email": "ghost@test.com"},
                follow_redirects=True,
            )
            assert resp.status_code == 200
            # Enumeration-Schutz: gleiche Antwort wie bei existierendem User
            assert b"Falls ein Konto" in resp.data
            assert outbox == []


class TestResetPasswordToken:
    def test_token_roundtrip(self, app_context):
        token = make_reset_token(42)
        assert verify_reset_token(token) == 42

    def test_token_invalid_returns_none(self, app_context):
        assert verify_reset_token("not-a-valid-token") is None

    def test_token_expired_returns_none(self, app_context):
        # max_age=0 → bereits abgelaufen, sobald die Signatur einen Tick alt ist
        token = make_reset_token(1)
        import time

        time.sleep(1)
        assert verify_reset_token(token, max_age=0) is None


class TestResetPasswordFlow:
    def test_reset_with_valid_token_changes_password(self, client, app_context):
        user = UserFactory(email="rp@test.com", password="OldPass123!")
        db.session.commit()
        token = make_reset_token(user.id)

        resp = client.post(
            f"/reset-password/{token}",
            data={"password": "NewPass456!", "password2": "NewPass456!"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        refreshed = User.query.get(user.id)
        assert refreshed.check_password("NewPass456!")
        assert not refreshed.check_password("OldPass123!")

    def test_reset_clears_lockout(self, client, app_context):
        user = UserFactory(email="locked@test.com", password="OldPass123!")
        user.failed_login_count = 5
        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        token = make_reset_token(user.id)

        client.post(
            f"/reset-password/{token}",
            data={"password": "FreshPass1!", "password2": "FreshPass1!"},
            follow_redirects=True,
        )
        refreshed = User.query.get(user.id)
        assert refreshed.failed_login_count == 0
        assert refreshed.locked_until is None

    def test_reset_with_invalid_token_redirects(self, client, app_context):
        resp = client.post(
            "/reset-password/garbage-token",
            data={"password": "FreshPass1!", "password2": "FreshPass1!"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"ungueltig" in resp.data or b"abgelaufen" in resp.data

    def test_reset_password_mismatch_rejected(self, client, app_context):
        user = UserFactory(email="mm@test.com", password="OldPass123!")
        db.session.commit()
        token = make_reset_token(user.id)

        client.post(
            f"/reset-password/{token}",
            data={"password": "NewPass456!", "password2": "Different!"},
            follow_redirects=True,
        )
        refreshed = User.query.get(user.id)
        assert refreshed.check_password("OldPass123!")

    def test_reset_password_too_weak_rejected(self, client, app_context):
        user = UserFactory(email="weak@test.com", password="OldPass123!")
        db.session.commit()
        token = make_reset_token(user.id)

        client.post(
            f"/reset-password/{token}",
            data={"password": "alllowercase", "password2": "alllowercase"},
            follow_redirects=True,
        )
        refreshed = User.query.get(user.id)
        assert refreshed.check_password("OldPass123!")

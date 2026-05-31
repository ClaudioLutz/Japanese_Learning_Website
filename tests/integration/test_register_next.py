# tests/integration/test_register_next.py
"""Integrationstests fuer D1: register() liest `next`, loggt automatisch ein
und schuetzt gegen Open-Redirects.

Vorher (Bug): register() ignorierte `next` und leitete auf /login um — am
teuersten Funnel-Moment (Registrierung von einer Paywall) musste sich der
Nutzer ein zweites Mal anmelden und verlor sein Ziel.
"""
from app.models import User


_VALID = {
    "username": "nextuser",
    "email": "next@test.com",
    "password": "StrongPass123!",
    "password2": "StrongPass123!",
}


class TestRegisterNext:
    def test_register_with_next_redirects_there_and_logs_in(self, client, app_context):
        """POST /register?next=/lessons → User eingeloggt + Redirect-Location == /lessons,
        NICHT auf /login."""
        resp = client.post(
            "/register?next=/lessons",
            data=_VALID,
            follow_redirects=False,
        )
        assert resp.status_code == 302
        location = resp.headers["Location"]
        assert location.endswith("/lessons"), location
        assert "/login" not in location

        # User wurde tatsaechlich angelegt …
        user = User.query.filter_by(username="nextuser").first()
        assert user is not None
        # … und ist eingeloggt: ein Folge-Request auf eine geschuetzte Seite
        # wird NICHT auf /login umgeleitet.
        follow = client.get("/my-lessons", follow_redirects=False)
        assert follow.status_code == 200 or "/login" not in follow.headers.get("Location", "")

    def test_register_with_next_via_form_field(self, client, app_context):
        """`next` darf auch aus dem Formular-Body kommen (hidden field)."""
        data = dict(_VALID)
        data["username"] = "formnext"
        data["email"] = "formnext@test.com"
        data["next"] = "/lessons"
        resp = client.post("/register", data=data, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/lessons")

    def test_register_rejects_protocol_relative_open_redirect(self, client, app_context):
        """next=//evil.com (Open-Redirect) wird abgewiesen → kein Redirect auf evil.com."""
        data = dict(_VALID)
        data["username"] = "eviluser"
        data["email"] = "evil@test.com"
        resp = client.post(
            "/register?next=//evil.com",
            data=data,
            follow_redirects=False,
        )
        assert resp.status_code == 302
        location = resp.headers["Location"]
        assert "evil.com" not in location, location
        # User wurde trotzdem angelegt + eingeloggt; Redirect geht auf einen
        # sicheren internen Fallback (erste Lektion bzw. Startseiten-Lernpfad).
        assert User.query.filter_by(username="eviluser").first() is not None

    def test_register_rejects_absolute_external_url(self, client, app_context):
        """next=https://evil.com (absolute URL) wird ebenfalls abgewiesen."""
        data = dict(_VALID)
        data["username"] = "evil2"
        data["email"] = "evil2@test.com"
        resp = client.post(
            "/register?next=https://evil.com/phish",
            data=data,
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "evil.com" not in resp.headers["Location"]

    def test_register_without_next_falls_back_internally(self, client, app_context):
        """Ohne next → sicherer interner Fallback (kein /login-Redirect)."""
        data = dict(_VALID)
        data["username"] = "plainuser"
        data["email"] = "plain@test.com"
        resp = client.post("/register", data=data, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" not in resp.headers["Location"]

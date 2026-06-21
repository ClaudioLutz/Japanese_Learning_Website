"""Integrationstests fuer den Uebungs-Hub (/ueben) + Login-Landing auf „Mein Lernen".

Der Hub buendelt Wiederholen (JP->DE / DE->JP), Kana und Pruefen unter einem Dach,
OHNE einen Modus zu verstecken — jeder bleibt einzeln direkt verlinkt. Muster
gespiegelt von TestDashboardPage (test_dashboard_page.py).
"""
from flask import url_for

from app import db
from tests.factories import UserFactory


class TestUebenHub:
    def test_route_resolves(self, app):
        """url_for('srs.ueben_page') loest auf /ueben auf."""
        with app.test_request_context():
            assert url_for('srs.ueben_page') == '/ueben'

    def test_guest_renders(self, client):
        """Hub ist auch fuer Gaeste erreichbar (Kana/Pruefen offen) — kein 500."""
        resp = client.get('/ueben')
        assert resp.status_code == 200

    def test_authenticated_links_all_modes(self, auth_client):
        """Eingeloggt -> alle vier Uebungs-Modi sind direkt verlinkt (keine Funktion versteckt)."""
        client, _user = auth_client
        resp = client.get('/ueben')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert '/review' in html             # Wiederholen JP->DE
        assert '/review/produktion' in html  # Produktion DE->JP
        assert '/practice/kana' in html      # Kana
        assert '/pruefen' in html            # Pruefen
        # Sekundaer-Wege bleiben vom Hub aus erreichbar (re-home, nicht loeschen):
        assert '/review/browse' in html      # Karten verwalten
        assert '/review/stats' in html       # Statistik


class TestLoginLandsOnHub:
    def test_login_redirects_to_hub(self, client, app_context):
        """Normaler Login (ohne next) landet auf der Lern-Heimat /mein-lernen."""
        UserFactory(email="hub@test.com", password="Test123!")
        db.session.commit()
        resp = client.post("/login", data={
            "email": "hub@test.com",
            "password": "Test123!",
        })
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/mein-lernen")

    def test_login_honours_next_param(self, client, app_context):
        """next hat Vorrang vor der Hub-Landing (Open-Redirect-Schutz bleibt)."""
        UserFactory(email="nexthub@test.com", password="Test123!")
        db.session.commit()
        resp = client.post("/login?next=/review", data={
            "email": "nexthub@test.com",
            "password": "Test123!",
        })
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/review")

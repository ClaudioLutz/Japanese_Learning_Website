"""Integrationstests fuer die Üben-Navigation (Dropdown + Bottom-Sheet) statt der
frueheren eigenstaendigen /ueben-Hub-Seite, plus Login-Landing auf „Mein Lernen".

Der Hub ist zu einem Dropdown (Desktop) bzw. Bottom-Sheet (Mobile) in der
Navigation geworden; /ueben selbst leitet jetzt 301 auf die primaere Wiederholung.
Kein Modus ist versteckt — alle vier sind direkt in der Nav verlinkt. Die zwei
Richtungen heissen jetzt „Verstehen" (JP->DE) und „Sprechen" (DE->JP).
"""
from flask import url_for

from app import db
from tests.factories import UserFactory


class TestUebenRedirect:
    def test_route_resolves(self, app):
        """url_for('srs.ueben_page') loest weiterhin auf /ueben auf (Redirect-Stub)."""
        with app.test_request_context():
            assert url_for('srs.ueben_page') == '/ueben'

    def test_ueben_redirects_to_review(self, client):
        """/ueben ist keine Seite mehr → 301 auf die primaere Wiederholung."""
        resp = client.get('/ueben')
        assert resp.status_code == 301
        assert resp.headers['Location'].endswith('/review')


class TestUebenNav:
    """Die Nav (base.html) verlinkt eingeloggt alle Modi direkt — Dropdown/Sheet."""

    def test_nav_links_all_modes(self, auth_client):
        client, _user = auth_client
        resp = client.get('/mein-lernen')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert '/review' in html              # Verstehen JP->DE
        assert '/review/produktion' in html   # Sprechen DE->JP
        assert '/practice/kana' in html       # Kana
        assert '/pruefen' in html             # Pruefen

    def test_nav_uses_new_labels(self, auth_client):
        """Richtungs-Labels heissen jetzt „Verstehen" / „Sprechen"."""
        client, _user = auth_client
        html = client.get('/mein-lernen').get_data(as_text=True)
        assert 'Verstehen' in html
        assert 'Sprechen' in html

    def test_no_standalone_hub_link(self, auth_client):
        """Kein Nav-Link mehr direkt auf die abgeschaffte /ueben-Seite."""
        client, _user = auth_client
        html = client.get('/mein-lernen').get_data(as_text=True)
        assert 'href="/ueben"' not in html


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

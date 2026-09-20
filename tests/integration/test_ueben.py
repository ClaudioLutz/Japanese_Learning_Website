"""Integrationstests fuer die Üben-Navigation (Dropdown + Bottom-Sheet) statt der
frueheren eigenstaendigen /ueben-Hub-Seite, plus Login-Landing auf „Mein Lernen".

Der Hub ist zu einem Dropdown (Desktop) bzw. Bottom-Sheet (Mobile) in der
Navigation geworden; /ueben selbst leitet jetzt 301 auf die primaere Wiederholung.
Kein Modus ist versteckt — alle vier sind direkt in der Nav verlinkt. Beide
Richtungen heissen jetzt „Wiederholen" (JP->DE bzw. DE->JP) — „Verstehen"/
„Sprechen" fanden Nutzer nicht als Wiederholung wieder.
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
        assert '/review' in html              # Wiederholen JP->DE
        assert '/review/produktion' in html   # Wiederholen DE->JP
        assert '/practice/kana' in html       # Kana
        assert '/pruefen' in html             # Pruefen

    def test_nav_uses_new_labels(self, auth_client):
        """Beide Richtungs-Items heissen „Wiederholen" (JP→DE / DE→JP)."""
        client, _user = auth_client
        html = client.get('/mein-lernen').get_data(as_text=True)
        # Desktop-Dropdown UND Mobile-Bottom-Sheet tragen beide Richtungen.
        assert html.count('Wiederholen <small>JP&#8594;DE</small>') == 2             or html.count('Wiederholen <small>JP→DE</small>') == 2
        assert html.count('Wiederholen <small>DE&#8594;JP</small>') == 2             or html.count('Wiederholen <small>DE→JP</small>') == 2
        # Die alten, nicht wiedererkannten Labels sind weg.
        assert '>Verstehen <small>' not in html
        assert '>Sprechen <small>' not in html

    def test_nav_has_aggregate_due_badge_on_ueben(self, auth_client):
        """Der Top-Level-Eintrag „Üben" traegt eine Summen-Badge (.nav-due-badge)."""
        client, _user = auth_client
        html = client.get('/mein-lernen').get_data(as_text=True)
        assert 'id="uebenBadgeDesktop"' in html   # Desktop-Trigger
        assert 'id="uebenBadge"' in html          # Mobile-Bottom-Nav-Tab
        assert 'nav-due-badge' in html

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

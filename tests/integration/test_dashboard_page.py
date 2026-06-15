"""Integrationstests fuer die „Mein Lernen"-Dashboard-Seite (/mein-lernen).

Spine-Abdeckung: Route aufloesbar, eingeloggt rendert das Dashboard, Gast bekommt
die weiche Teaser-Landing (kein harter Redirect) und KEINE echten Nutzerdaten.
Muster gespiegelt von TestSRSPages / TestReviewTeaser (test_srs_routes.py).
"""
from flask import url_for


class TestDashboardPage:
    def test_route_resolves(self, app):
        """url_for('dashboard.index') loest auf /mein-lernen auf."""
        with app.test_request_context():
            assert url_for('dashboard.index') == '/mein-lernen'

    def test_authenticated_renders_dashboard(self, auth_client):
        """Eingeloggt -> 200 + Dashboard-Marker (Komponente, Kompass, Wrapper, Name)."""
        client, user = auth_client
        resp = client.get('/mein-lernen')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'dashboard()' in html              # Alpine-Komponente eingebunden
        assert 'mein-lernen wrap' in html          # gescopter Wrapper
        assert 'N5-Kompass' in html                # Kompass-Sektion
        assert 'Heute' in html                     # Heute-Hero
        assert user.username in html               # echter Name verdrahtet
        # Alpine-Plugins muessen OHNE defer geladen sein (vor dem deferred Core):
        assert '@alpinejs/collapse' in html
        assert '@alpinejs/intersect' in html
        # privates Dashboard nicht indexieren
        assert 'noindex' in html

    def test_guest_gets_teaser_not_redirect(self, client):
        """Gast -> 200 Teaser (kein 302), Register-CTA mit next, noindex."""
        resp = client.get('/mein-lernen')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Mein Lernen' in body
        assert 'Kostenlos Konto erstellen' in body
        assert 'next=/mein-lernen' in body
        assert 'noindex' in body

    def test_guest_sees_no_dashboard_internals(self, client):
        """Teaser leakt KEINE echte Dashboard-Sektion (Komponente/Kompass)."""
        body = client.get('/mein-lernen').get_data(as_text=True)
        assert 'Konto erstellen' in body
        assert 'dashboard()' not in body
        assert 'N5-Kompass' not in body

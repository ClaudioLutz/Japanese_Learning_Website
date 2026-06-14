"""Integrationstests fuer den globalen Context-Processor (app/__init__.py)."""

from flask import template_rendered


def _capture_context(app, client, url):
    """Rendert `url` und faengt den Template-Context per Signal ein."""
    captured = []

    def _record(sender, template, context, **extra):
        captured.append(context)

    template_rendered.connect(_record, app)
    try:
        client.get(url)
    finally:
        template_rendered.disconnect(_record, app)
    return captured


class TestShowBundleHintFailClosed:
    def test_show_bundle_hint_fail_closed_on_service_error(
        self, app, client, monkeypatch
    ):
        """Punkt 10.2: Kippt der bundle_service, ist show_bundle_hint=False.

        Fail-closed: lieber keinen Kauf-CTA zeigen als zahlende
        Bundle-Besitzer mit dem CHF-9.90-Hinweis penetrieren.
        """
        def _boom(_user):
            raise RuntimeError("bundle_service kaputt")

        monkeypatch.setattr(
            "app.services.bundle_service.user_needs_bundle_hint", _boom
        )

        contexts = _capture_context(app, client, "/")
        assert contexts, "Kein Template gerendert — Signal nicht ausgeloest"
        # Mindestens ein gerendertes Template muss den Flag fail-closed liefern.
        bundle_flags = [
            c["show_bundle_hint"] for c in contexts if "show_bundle_hint" in c
        ]
        assert bundle_flags, "show_bundle_hint nicht im Context"
        assert all(flag is False for flag in bundle_flags)

    def test_show_bundle_hint_normal_guest_true(self, app, client):
        """Ohne Fehler sieht ein Gast den Hint normal (True) — Regression-Schutz."""
        contexts = _capture_context(app, client, "/")
        bundle_flags = [
            c["show_bundle_hint"] for c in contexts if "show_bundle_hint" in c
        ]
        assert bundle_flags
        assert all(flag is True for flag in bundle_flags)

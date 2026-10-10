"""Rechtstexte im Gratis-Modus (FREE_MODE).

Die Datenschutzerklärung folgt dem Muster der AGB: Im Gratis-Modus nennt sie
Payrexx nur als künftige Option ("derzeit keine Zahlungen"), ohne Gratis-Modus
bleibt der bisherige Text stehen. So bleibt FREE_MODE umkehrbar, ohne dass
jemand die Rechtstexte von Hand zurückbauen muss.
"""
import pytest


@pytest.fixture
def free_mode(app):
    prev = app.config.get("FREE_MODE", False)
    app.config["FREE_MODE"] = True
    yield
    app.config["FREE_MODE"] = prev


def _datenschutz(client) -> str:
    resp = client.get("/legal/datenschutz")
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def test_datenschutz_gratis_modus_nennt_payrexx_nur_kuenftig(client, free_mode):
    body = _datenschutz(client)
    assert "Derzeit sind alle Inhalte kostenlos" in body
    assert "Sollten künftig kostenpflichtige Inhalte angeboten werden" in body
    assert "Derzeit werden keine Daten an Payrexx übermittelt" in body
    # Die unbedingten Kauf-Formulierungen dürfen im Gratis-Modus nicht stehen.
    assert "Bei Käufen werden Vor-/Nachname" not in body
    assert "<li>Abwicklung von Käufen über Payrexx.</li>" not in body
    assert "— Zahlungsabwicklung.</li>" not in body


def test_datenschutz_ohne_gratis_modus_unveraendert(client):
    body = _datenschutz(client)
    assert "Bei Käufen werden Vor-/Nachname" in body
    assert "<li>Abwicklung von Käufen über Payrexx.</li>" in body
    assert "— Zahlungsabwicklung.</li>" in body
    assert "Derzeit sind alle Inhalte kostenlos" not in body
    assert "Derzeit werden keine Daten an Payrexx übermittelt" not in body


def test_agb_und_datenschutz_sagen_im_gratis_modus_dasselbe(client, free_mode):
    agb = client.get("/legal/agb").get_data(as_text=True)
    assert "Derzeit sind alle Inhalte von japanese-learning.ch kostenlos" in agb
    assert "Sollten künftig kostenpflichtige Inhalte angeboten werden" in agb
    assert "Sollten künftig kostenpflichtige Inhalte angeboten werden" in _datenschutz(client)

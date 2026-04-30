# tests/integration/test_tts_routes.py
"""
Pflicht-Tests fuer /api/tts: Sprache muss explizit gesetzt UND skript-konsistent
sein. Verhindert peinliche Mismatches (japanische Voice spricht Deutsch usw.).
"""

import base64
from unittest.mock import patch

import pytest


class _FakeResponse:
    """Minimaler Stub fuer requests.post-Antwort."""

    def __init__(self, audio_b64="UklGRg==", status_code=200):
        self._json = {"audioContent": audio_b64}
        self.status_code = status_code

    def json(self):
        return self._json


@pytest.fixture
def tts_app(app, monkeypatch, tmp_path):
    """App-Fixture mit gesetztem Google-TTS-Key + isoliertem Cache-Verzeichnis."""
    monkeypatch.setenv("GOOGLE_TTS_API_KEY", "test-key")
    # Cache in tmp_path, damit Tests sich nicht gegenseitig beeinflussen.
    cache_root = tmp_path / "static"
    (cache_root / "cache" / "tts").mkdir(parents=True)
    app.static_folder = str(cache_root)
    yield app


@pytest.fixture
def post_tts(client, tts_app):
    def _post(payload):
        return client.post("/api/tts", json=payload)
    return _post


def test_lang_pflicht(post_tts):
    """Ohne lang → 400, kein Raten."""
    resp = post_tts({"text": "こんにちは"})
    assert resp.status_code == 400
    assert b"lang" in resp.data


def test_lang_ungueltig(post_tts):
    """lang=en oder anderes → 400."""
    resp = post_tts({"text": "Hallo", "lang": "en"})
    assert resp.status_code == 400


def test_text_fehlt(post_tts):
    resp = post_tts({"lang": "ja"})
    assert resp.status_code == 400


def test_mismatch_ja_aber_deutsch(post_tts):
    """lang=ja, aber Text ist rein deutsch → 400 (kein Mismatch zulassen)."""
    resp = post_tts({"text": "Ich komme aus der Schweiz", "lang": "ja"})
    assert resp.status_code == 400
    assert b"japanisch" in resp.data.lower()


def test_mismatch_de_aber_japanisch(post_tts):
    """lang=de, aber Text enthaelt japanische Zeichen → 400."""
    resp = post_tts({"text": "Hallo こんにちは", "lang": "de"})
    assert resp.status_code == 400
    assert b"japanisch" in resp.data.lower()


def test_japanisch_korrekt(post_tts):
    """lang=ja + japanischer Text → 200, Voice ist ja-JP."""
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["payload"] = json
        return _FakeResponse(audio_b64=base64.b64encode(b"FAKEMP3").decode())

    with patch("requests.post", side_effect=fake_post):
        resp = post_tts({"text": "こんにちは", "lang": "ja"})

    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "audio/mpeg"
    assert captured["payload"]["voice"]["languageCode"] == "ja-JP"
    assert captured["payload"]["voice"]["name"].startswith("ja-JP-")


def test_deutsch_korrekt(post_tts):
    """lang=de + deutscher Text → 200, Voice ist de-DE."""
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["payload"] = json
        return _FakeResponse(audio_b64=base64.b64encode(b"FAKEMP3").decode())

    with patch("requests.post", side_effect=fake_post):
        resp = post_tts({"text": "Ich komme aus der Schweiz", "lang": "de"})

    assert resp.status_code == 200
    assert captured["payload"]["voice"]["languageCode"] == "de-DE"
    assert captured["payload"]["voice"]["name"].startswith("de-DE-")


def test_text_zu_lang(post_tts):
    """Text > 500 Zeichen → 400."""
    resp = post_tts({"text": "あ" * 501, "lang": "ja"})
    assert resp.status_code == 400


def test_kein_api_key(client, app, monkeypatch):
    """Wenn kein Google-Key konfiguriert → 503."""
    monkeypatch.delenv("GOOGLE_TTS_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    app.config.pop("GOOGLE_TTS_API_KEY", None)
    resp = client.post("/api/tts", json={"text": "こんにちは", "lang": "ja"})
    assert resp.status_code == 503

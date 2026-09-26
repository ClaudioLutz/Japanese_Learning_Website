"""/api/tts: optionaler Parameter voice_gender (Rollenspiel-Figuren).

Serverseitige Whitelist: nur 'm' | 'f'; der Client kann nie einen Stimmennamen
waehlen. Primaerstimme Neural2 (B = weiblich, D = maennlich), bei Fehler
Chirp3-HD desselben Geschlechts. Ohne Parameter bleibt alles wie bisher.
"""
import base64
from unittest.mock import patch

import pytest

from app.routes import _TTS_GENDER_VOICES
from tests.test_tts_voice_gender import KNOWN_VOICE_GENDER


class _Resp:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def json(self):
        return {"audioContent": base64.b64encode(b"FAKEMP3").decode()}


@pytest.fixture
def tts_client(client, app, monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_TTS_API_KEY", "test-key")
    root = tmp_path / "static"
    (root / "cache" / "tts").mkdir(parents=True)
    old = app.static_folder
    app.static_folder = str(root)
    yield client
    app.static_folder = old


def _capture(status_codes=(200,)):
    calls = []
    codes = list(status_codes)

    def fake_post(url, json=None, timeout=None):
        calls.append(json)
        return _Resp(codes.pop(0) if codes else 200)
    return calls, fake_post


@pytest.mark.parametrize("gender,expected", [("m", "ja-JP-Neural2-D"), ("f", "ja-JP-Neural2-B")])
def test_gender_waehlt_whitelist_stimme(tts_client, gender, expected):
    calls, fake = _capture()
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": "いらっしゃいませ。", "lang": "ja", "voice_gender": gender})
    assert resp.status_code == 200
    assert calls[0]["voice"] == {"languageCode": "ja-JP", "name": expected}
    # Neural2 → SSML-Pfad
    assert "ssml" in calls[0]["input"]


@pytest.mark.parametrize("bad", ["x", "male", "ja-JP-Wavenet-A", 1, ["m"]])
def test_ungueltiger_wert_400(tts_client, bad):
    with patch("requests.post", side_effect=AssertionError("kein TTS-Call erwartet")):
        resp = tts_client.post("/api/tts", json={"text": "はい", "lang": "ja", "voice_gender": bad})
    assert resp.status_code == 400
    assert b"voice_gender" in resp.data


def test_stimmenname_vom_client_wird_ignoriert(tts_client):
    """Ein mitgeschickter 'voice'-Name aendert nichts an der Whitelist-Stimme."""
    calls, fake = _capture()
    with patch("requests.post", side_effect=fake):
        tts_client.post("/api/tts", json={"text": "はい", "lang": "ja", "voice_gender": "f",
                                          "voice": "ja-JP-Wavenet-D"})
    assert calls[0]["voice"]["name"] == "ja-JP-Neural2-B"


def test_ohne_gender_standardstimme(tts_client):
    calls, fake = _capture()
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": "はい", "lang": "ja"})
    assert resp.status_code == 200
    assert calls[0]["voice"]["name"] == "ja-JP-Chirp3-HD-Leda"


def test_leerer_gender_standardstimme(tts_client):
    calls, fake = _capture()
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": "はい", "lang": "ja", "voice_gender": ""})
    assert resp.status_code == 200
    assert calls[0]["voice"]["name"] == "ja-JP-Chirp3-HD-Leda"


def test_fallback_chirp_gleiches_geschlecht(tts_client):
    calls, fake = _capture(status_codes=(500, 200))
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": "こんにちは。", "lang": "ja", "voice_gender": "m"})
    assert resp.status_code == 200
    assert [c["voice"]["name"] for c in calls] == ["ja-JP-Neural2-D", "ja-JP-Chirp3-HD-Charon"]
    assert "text" in calls[1]["input"]  # Chirp: kein SSML


def test_beide_stimmen_fehlgeschlagen_502(tts_client):
    calls, fake = _capture(status_codes=(500, 500))
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": "こんにちは。", "lang": "ja", "voice_gender": "f"})
    assert resp.status_code == 502
    assert len(calls) == 2


def test_gender_bei_deutsch_ignoriert(tts_client):
    calls, fake = _capture()
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": "Hallo", "lang": "de", "voice_gender": "m"})
    assert resp.status_code == 200
    assert calls[0]["voice"]["languageCode"] == "de-DE"


def test_gender_ueberspringt_vorgeneriertes_gemini(tts_client, app):
    """Vorgeneriertes Gemini-Audio ist Leda (weiblich) → bei voice_gender nicht nutzen."""
    from app.routes import _maybe_spell_out_kana_row, pregenerated_ja_audio_file
    text = "これはほんです。"
    with app.app_context():
        path = pregenerated_ja_audio_file(_maybe_spell_out_kana_row(text))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"PREGEN")
    calls, fake = _capture()
    with patch("requests.post", side_effect=fake):
        resp = tts_client.post("/api/tts", json={"text": text, "lang": "ja", "voice_gender": "m"})
    assert resp.status_code == 200
    assert resp.data != b"PREGEN"
    assert calls[0]["voice"]["name"] == "ja-JP-Neural2-D"


def test_whitelist_geschlechter_stimmen():
    """Primaer- und Fallback-Stimme passen zum Geschlecht (Voices-API-Stand)."""
    chirp_gender = {"ja-JP-Chirp3-HD-Leda": "female", "ja-JP-Chirp3-HD-Charon": "male"}
    known = {**KNOWN_VOICE_GENDER, **chirp_gender}
    for key, want in (("f", "female"), ("m", "male")):
        primary, fallback = _TTS_GENDER_VOICES[key]
        assert known[primary] == want
        assert known[fallback] == want
    assert set(_TTS_GENDER_VOICES) == {"m", "f"}

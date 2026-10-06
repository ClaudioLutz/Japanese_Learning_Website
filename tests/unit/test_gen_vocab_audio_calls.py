"""scripts/gen_vocab_audio.py: Obergrenze der Gemini-Aufrufe pro Eintrag (Befund 5).

Frueher lag der robuste Pfad (nackt + 3 Prompts, je 1 Retry) in einer aeusseren
4er-Schleife → bis 32 Quota-Aufrufe pro Eintrag. Jetzt genau ein robuster
Durchlauf, hoechstens MAX_GEMINI_CALLS_PER_ENTRY Aufrufe.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services import tts_client

gva = pytest.importorskip("scripts.gen_vocab_audio")

KEY = "AIzaSyFAKE_testkey_0123456789abcdefghijk"


def _empty():
    return SimpleNamespace(candidates=[SimpleNamespace(content=None, finish_reason="OTHER")])


def _audio():
    part = SimpleNamespace(inline_data=SimpleNamespace(data=b"\x00\x00" * 12000))
    return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))])


@pytest.fixture
def static_tmp(app, tmp_path):
    old = app.static_folder
    app.static_folder = str(tmp_path)
    yield tmp_path
    app.static_folder = old


def _synth(app, client, text="ちち"):
    with patch("app.services.tts_client.make_gemini_client", return_value=client):
        return gva.synth_one(app, text, force=True)


def test_konstante():
    assert gva.MAX_GEMINI_CALLS_PER_ENTRY == tts_client.GEMINI_MAX_CALLS_ROBUST == 8


@pytest.mark.parametrize("side_effect", [
    TimeoutError("hang"),
    RuntimeError("429 RESOURCE_EXHAUSTED"),
])
def test_dauerfehler_hoechstens_max_calls(app, static_tmp, side_effect):
    client = MagicMock()
    client.models.generate_content.side_effect = side_effect
    status, _ = _synth(app, client)
    assert status.startswith("FAIL")
    assert 1 <= client.models.generate_content.call_count <= gva.MAX_GEMINI_CALLS_PER_ENTRY


def test_immer_leer_hoechstens_max_calls(app, static_tmp):
    client = MagicMock()
    client.models.generate_content.return_value = _empty()
    status, _ = _synth(app, client)
    assert status.startswith("FAIL")
    assert client.models.generate_content.call_count <= gva.MAX_GEMINI_CALLS_PER_ENTRY


def test_erfolg_schreibt_wav(app, static_tmp):
    client = MagicMock()
    client.models.generate_content.return_value = _audio()
    status, _ = _synth(app, client)
    assert status == "ok"
    assert list((static_tmp / "uploads" / "tts_gemini").glob("*.wav"))


def test_fail_meldung_ohne_key(app, static_tmp):
    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError(f"403 url ?key={KEY}")
    status, _ = _synth(app, client)
    assert KEY not in status

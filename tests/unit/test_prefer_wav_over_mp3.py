"""scripts/prefer_wav_over_mp3.py: .wav ist nicht automatisch Gemini (Befund 4)."""
import pytest

pw = pytest.importorskip("scripts.prefer_wav_over_mp3")

BASE = "/static/uploads/lessons/inline_audio/"


def _html(*hashes):
    return "".join(f'<p data-audio-url="{BASE}{h}.mp3">ちち</p>' for h in hashes)


def test_engine_aus_manifest_sonst_unbekannt(tmp_path):
    for h in ("aaa111", "bbb222"):
        (tmp_path / f"{h}.wav").write_bytes(b"RIFF")
    html, engines = pw.switch_html(
        _html("aaa111", "bbb222", "ccc333"), tmp_path, {"aaa111": "chirp"},
    )
    assert f'{BASE}aaa111.wav' in html and 'data-audio-engine="chirp"' in html
    assert f'{BASE}bbb222.wav' in html
    assert f'{BASE}ccc333.mp3' in html  # keine WAV → bleibt
    assert html.count("data-audio-engine") == 1  # bbb222 unbekannt → kein Attribut
    assert engines == {"chirp": 1, "unknown": 1}


def test_ohne_wav_unveraendert(tmp_path):
    src = _html("ddd444")
    html, engines = pw.switch_html(src, tmp_path, {})
    assert html == src and not engines

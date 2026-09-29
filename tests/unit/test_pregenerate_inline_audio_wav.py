"""scripts/pregenerate_inline_audio.py: Chirp-Fallback schreibt .wav (nicht .mp3).

Seit 29.09.2026 liefert der Chirp-Fallback LINEAR16/WAV → der Hash-Dateiname
und die URL im augmented_html sind identisch mit dem Gemini-Pfad.
"""
from unittest.mock import patch

import pytest

from app.services.tts_client import GeminiEmptyAudioError, pcm_to_wav

pia = pytest.importorskip("scripts.pregenerate_inline_audio")

WAV = pcm_to_wav(b"\x00\x00" * 2400)


@pytest.fixture
def lesson_with_text(app_context):
    from app import db
    from app.models import Lesson, LessonContent

    lesson = Lesson(title="Familie", lesson_type="free", is_published=True, order_index=1)
    db.session.add(lesson)
    db.session.flush()
    lc = LessonContent(
        lesson_id=lesson.id, content_type="text", title="Wörter",
        content_text="- 「ちち」 — Vater\n- 「はは」 — Mutter",
        page_number=1, order_index=1,
    )
    db.session.add(lc)
    db.session.commit()
    return lesson, lc


def _run(lesson_id, tmp_path, *, gemini, chirp, **kwargs):
    with patch.object(pia, "OUT_DIR", tmp_path), \
            patch.object(pia, "make_gemini_client", return_value=object()), \
            patch.object(pia, "synth_gemini_wav", side_effect=gemini), \
            patch.object(pia, "synth_chirp_fallback_wav", side_effect=chirp) as chirp_mock:
        n = pia.process_lesson(lesson_id, **kwargs)
    return n, chirp_mock


def test_chirp_fallback_schreibt_wav_und_wav_url(lesson_with_text, tmp_path):
    lesson, lc = lesson_with_text

    def gemini(_client, _text):
        raise GeminiEmptyAudioError("Gemini leer (finish=OTHER)")

    n, chirp_mock = _run(lesson.id, tmp_path, gemini=gemini, chirp=lambda _t: WAV)

    assert n == 2
    assert chirp_mock.call_count == 2
    assert sorted(p.suffix for p in tmp_path.iterdir()) == [".wav", ".wav"]
    html = lc.ai_generation_details["augmented_html"]
    assert ".mp3" not in html
    assert html.count("/static/uploads/lessons/inline_audio/") == 2
    assert html.count('.wav"') == 2


def test_gemini_und_chirp_ergeben_dieselbe_url(lesson_with_text, tmp_path):
    lesson, lc = lesson_with_text
    _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    html_gemini = lc.ai_generation_details["augmented_html"]

    def gemini_leer(_client, _text):
        raise GeminiEmptyAudioError("leer")

    _run(lesson.id, tmp_path, gemini=gemini_leer, chirp=lambda _t: WAV, force=True)
    assert lc.ai_generation_details["augmented_html"] == html_gemini


def test_replace_mp3_rendert_nur_mp3_altbestand(lesson_with_text, tmp_path):
    lesson, lc = lesson_with_text
    # Erst normal rendern, um die Hashes zu kennen
    _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    wavs = sorted(tmp_path.glob("*.wav"))
    # Altbestand simulieren: erste Datei nur als Chirp-MP3 vorhanden
    legacy = wavs[0].with_suffix(".mp3")
    wavs[0].rename(legacy)

    # Ohne Flag: MP3 wird weiterverwendet, nichts neu gerendert
    n, _ = _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    assert n == 0
    assert legacy.stem + ".mp3" in lc.ai_generation_details["augmented_html"]

    # Mit --replace-mp3: genau dieser eine Eintrag neu als WAV
    calls = []

    def gemini(_client, text):
        calls.append(text)
        return WAV

    n, _ = _run(lesson.id, tmp_path, gemini=gemini, chirp=lambda _t: WAV, replace_mp3=True)
    assert n == 1 and len(calls) == 1
    assert (tmp_path / f"{legacy.stem}.wav").exists()
    assert legacy.exists()  # Alt-MP3 bleibt fuer andere Verweise liegen
    assert ".mp3" not in lc.ai_generation_details["augmented_html"]


def test_beide_fehlgeschlagen_kein_audio_tag(lesson_with_text, tmp_path):
    lesson, lc = lesson_with_text

    def boom(*_a):
        raise RuntimeError("down")

    n, _ = _run(lesson.id, tmp_path, gemini=boom, chirp=boom)
    assert n == 0
    assert list(tmp_path.iterdir()) == []

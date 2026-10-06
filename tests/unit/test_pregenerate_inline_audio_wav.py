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


def _audio_files(directory):
    """Audio-Dateien ohne das Engine-Manifest."""
    return [p for p in directory.iterdir() if p.suffix in (".wav", ".mp3")]


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
    assert sorted(p.suffix for p in _audio_files(tmp_path)) == [".wav", ".wav"]
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
    html_chirp = lc.ai_generation_details["augmented_html"]
    assert _urls(html_chirp) == _urls(html_gemini)
    # Engine bleibt unterscheidbar (Befund 4), die URL nicht
    assert html_gemini.count('data-audio-engine="gemini"') == 2
    assert html_chirp.count('data-audio-engine="chirp"') == 2
    assert lc.ai_generation_details["augmented_voice"] == "ja-JP-Chirp3-HD-Leda"


def _urls(html):
    from bs4 import BeautifulSoup
    return [el["data-audio-url"] for el in
            BeautifulSoup(html, "html.parser").find_all(attrs={"data-audio-url": True})]


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


# ---------------------------------------------------------------------------
# Review-Befunde 06.10.2026
# ---------------------------------------------------------------------------
def _boom(*_a):
    raise RuntimeError("down")


def _leer(*_a):
    raise GeminiEmptyAudioError("leer")


def test_force_beide_scheitern_behaelt_bestehende_wav(lesson_with_text, tmp_path):
    """Befund 2: --force verliert kein funktionierendes Audio."""
    lesson, lc = lesson_with_text
    _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    vorher = _urls(lc.ai_generation_details["augmented_html"])

    n, _ = _run(lesson.id, tmp_path, gemini=_boom, chirp=_boom, force=True)
    assert n == 0
    assert _urls(lc.ai_generation_details["augmented_html"]) == vorher
    assert all(p.stat().st_size == len(WAV) for p in _audio_files(tmp_path))


def test_replace_mp3_beide_scheitern_behaelt_mp3(lesson_with_text, tmp_path):
    lesson, lc = lesson_with_text
    _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    for wav in tmp_path.glob("*.wav"):
        wav.rename(wav.with_suffix(".mp3"))

    _run(lesson.id, tmp_path, gemini=_boom, chirp=_boom, replace_mp3=True)
    urls = _urls(lc.ai_generation_details["augmented_html"])
    assert len(urls) == 2 and all(u.endswith(".mp3") for u in urls)


def test_alte_url_aus_augmented_html_als_fallback(lesson_with_text, tmp_path):
    lesson, lc = lesson_with_text
    _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    vorher = _urls(lc.ai_generation_details["augmented_html"])
    for p in _audio_files(tmp_path):
        p.unlink()  # Dateien weg (z.B. anderes Volume), alte URLs im HTML

    _run(lesson.id, tmp_path, gemini=_boom, chirp=_boom)
    assert _urls(lc.ai_generation_details["augmented_html"]) == vorher


def test_nie_weniger_audios_als_vorher(lesson_with_text, tmp_path):
    from app import db

    lesson, lc = lesson_with_text
    _run(lesson.id, tmp_path, gemini=lambda _c, _t: WAV, chirp=lambda _t: WAV)
    details = dict(lc.ai_generation_details)
    extra = '<p data-audio-url="/static/uploads/lessons/inline_audio/abc123abc123.wav">いぬ</p>'
    details["augmented_html"] = details["augmented_html"] + extra
    lc.ai_generation_details = details
    db.session.commit()
    for p in _audio_files(tmp_path):
        p.unlink()
    html_vorher = lc.ai_generation_details["augmented_html"]

    # Neu nur 2 Elemente (alte URLs), vorher 3, dazu Fehler → nicht speichern
    _run(lesson.id, tmp_path, gemini=_boom, chirp=_boom, force=True)
    assert lc.ai_generation_details["augmented_html"] == html_vorher


def test_engine_manifest_wird_geschrieben(lesson_with_text, tmp_path):
    """Befund 4: Engine pro Datei im Sidecar-Manifest."""
    from app.services.audio_engine_manifest import MANIFEST_NAME, load_manifest

    lesson, lc = lesson_with_text
    calls = {"n": 0}

    def gemini_einmal(_c, _t):
        calls["n"] += 1
        if calls["n"] == 1:
            return WAV
        raise GeminiEmptyAudioError("leer")

    _run(lesson.id, tmp_path, gemini=gemini_einmal, chirp=lambda _t: WAV)
    assert (tmp_path / MANIFEST_NAME).exists()
    manifest = load_manifest(tmp_path)
    assert sorted(manifest.values()) == ["chirp", "gemini"]
    details = lc.ai_generation_details
    assert details["augmented_voice"] == "mixed"
    assert details["augmented_engines"] == {"chirp": 1, "gemini": 1}


def test_upgrade_chirp_rendert_nur_chirp_eintraege(lesson_with_text, tmp_path):
    from app.services.audio_engine_manifest import load_manifest

    lesson, lc = lesson_with_text
    calls = {"n": 0}

    def gemini_einmal(_c, _t):
        calls["n"] += 1
        if calls["n"] == 1:
            return WAV
        raise GeminiEmptyAudioError("leer")

    _run(lesson.id, tmp_path, gemini=gemini_einmal, chirp=lambda _t: WAV)
    chirp_hash = next(h for h, e in load_manifest(tmp_path).items() if e == "chirp")

    # Ohne Flag: nichts neu
    seen = []
    n, _ = _run(lesson.id, tmp_path, gemini=lambda _c, t: seen.append(t) or WAV,
                chirp=lambda _t: WAV)
    assert n == 0 and seen == []

    # --upgrade-chirp: genau der Chirp-Eintrag, danach Gemini
    n, chirp_mock = _run(lesson.id, tmp_path, gemini=lambda _c, t: seen.append(t) or WAV,
                         chirp=lambda _t: WAV, upgrade_chirp=True)
    assert n == 1 and len(seen) == 1
    assert chirp_mock.call_count == 0
    assert load_manifest(tmp_path)[chirp_hash] == "gemini"
    assert lc.ai_generation_details["augmented_voice"] == "gemini-2.5-pro:Leda"


def test_upgrade_chirp_ohne_gemini_bleibt_chirp_ohne_neuen_chirp_call(lesson_with_text, tmp_path):
    from app.services.audio_engine_manifest import load_manifest

    lesson, lc = lesson_with_text
    _run(lesson.id, tmp_path, gemini=_leer, chirp=lambda _t: WAV)
    vorher = _urls(lc.ai_generation_details["augmented_html"])

    n, chirp_mock = _run(lesson.id, tmp_path, gemini=_leer, chirp=lambda _t: WAV,
                         upgrade_chirp=True)
    assert n == 0 and chirp_mock.call_count == 0
    assert set(load_manifest(tmp_path).values()) == {"chirp"}
    assert _urls(lc.ai_generation_details["augmented_html"]) == vorher


def test_fehlermeldung_ohne_key(lesson_with_text, tmp_path, capsys):
    """Befund 1: [ERR]-Zeile enthaelt nie den API-Key."""
    lesson, _lc = lesson_with_text
    key = "AIzaSyFAKE_testkey_0123456789abcdefghijk"

    def leak(*_a):
        raise RuntimeError(f"403 Forbidden for url: https://x/v1/text:synthesize?key={key}")

    _run(lesson.id, tmp_path, gemini=leak, chirp=leak)
    out = capsys.readouterr().out
    assert "[ERR]" in out and key not in out
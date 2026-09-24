# tests/integration/test_lesson_audio_lazy.py
"""Lektionsseite laedt Block-Player-Audio erst beim Play-Klick.

Befund 24.09.2026: Beim blossen Aufruf einer Lektion hat der Custom-Audio-Player
per ``new Audio(src)`` + ``preload='metadata'`` alle Block-Player-WAVs einer
Lektion angefordert (Lektion 148: 8 Dateien, bis 11 MB je Datei). Seither:
``preload="none"`` im Markup und ``src`` erst in ``ensureSrc()`` beim ersten Play.
Ausserdem: canvas-confetti nur einmal (base.html), Kana-Grid ohne doppeltes init().
"""

import re

from app import db
from app.models import LessonContent
from tests.factories import LessonFactory


def _render_lesson(client, contents: list[dict]) -> str:
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    for idx, kwargs in enumerate(contents):
        db.session.add(LessonContent(lesson_id=lesson.id, order_index=idx, page_number=1, **kwargs))
    db.session.commit()
    resp = client.get(f"/lessons/{lesson.id}")
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def test_block_player_audio_has_preload_none(client, app_context):
    """Jedes gerenderte <audio controls> darf ohne Klick nichts vorladen."""
    html = _render_lesson(client, [
        {
            "content_type": "text",
            "title": "Text mit Block-Audio",
            "content_text": "<p>Hallo</p>",
            "media_url": "/uploads/lessons/text_audio/lesson_1/page_1_content_1.wav",
            "file_type": "audio/wav",
        },
        {
            "content_type": "audio",
            "title": "Reines Audio",
            "media_url": "/uploads/lessons/audio/x.mp3",
        },
    ])
    audio_tags = re.findall(r"<audio\b[^>]*>", html)
    controls_tags = [t for t in audio_tags if "controls" in t]
    assert len(controls_tags) >= 2, audio_tags
    for tag in controls_tags:
        assert 'preload="none"' in tag, tag
    assert 'class="text-audio-player' in html


def test_custom_player_sets_src_only_on_play(client, app_context):
    """Der Custom-Player erzeugt das Audio-Objekt ohne src; src kommt erst im Klick."""
    html = _render_lesson(client, [{"content_type": "text", "title": "T", "content_text": "<p>x</p>"}])
    assert "new Audio(src)" not in html
    assert "newAudio.preload = 'none'" in html
    # ensureSrc() wird im Play-Handler aufgerufen, bevor play() startet
    assert re.search(r"ensureSrc\(\);\s*newAudio\.play\(\)", html)


def test_confetti_loaded_once(client, app_context):
    html = _render_lesson(client, [{"content_type": "text", "title": "T", "content_text": "<p>x</p>"}])
    assert html.count("canvas-confetti@") == 1


def test_kana_grid_game_without_duplicate_init(client, app_context):
    """Alpine ruft init() automatisch; ein zusaetzliches x-init="init()" loeste
    /api/kana-grid/<id>/config doppelt aus."""
    html = _render_lesson(client, [{"content_type": "kana_grid_game", "title": "Kana-Grid"}])
    assert 'x-data="kanaGridGame(' in html
    block = html[html.index('x-data="kanaGridGame('):]
    block = block[: block.index(">")]
    assert 'x-init="init()"' not in block

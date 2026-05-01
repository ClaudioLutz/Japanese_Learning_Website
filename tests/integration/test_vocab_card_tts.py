# tests/integration/test_vocab_card_tts.py
"""Sicherstellen, dass Vokabel-Karten den JP-Beispielsatz auf der Vorderseite
rendern und der Audio-Button diesen Satz vorliest — nicht nur das Wort.
"""

from app import db
from app.models import LessonContent
from tests.factories import LessonFactory, VocabularyFactory


def _make_vocab_lesson(example_jp: str | None) -> int:
    vocab = VocabularyFactory(
        word="先生",
        reading="せんせい",
        meaning="teacher",
        meaning_de="Lehrer",
        example_sentence_japanese=example_jp,
    )
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    db.session.add(LessonContent(
        lesson_id=lesson.id,
        content_type="vocabulary",
        content_id=vocab.id,
        order_index=0,
        page_number=1,
    ))
    db.session.commit()
    return lesson.id


def test_vocab_card_audio_button_uses_example_sentence(client, app_context):
    """Audio-Button traegt den JP-Beispielsatz, nicht nur das Wort."""
    lesson_id = _make_vocab_lesson("せんせいは やさしいです。")
    resp = client.get(f"/lessons/{lesson_id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Beispielsatz wird auf der Vorderseite angezeigt
    assert "せんせいは やさしいです。" in html
    # Audio-Button traegt diesen Satz UND ist explizit als Japanisch markiert
    assert 'data-tts-text="せんせいは やさしいです。"' in html
    assert 'data-tts-lang="ja"' in html
    # Front-Klasse fuer den TTS-Beispielsatz ist da (Hairline-Style)
    assert 'class="vocab-tts-example"' in html


def test_vocab_card_falls_back_to_word_when_example_empty(client, app_context):
    """Ohne example_sentence_japanese greift Fallback auf das Wort."""
    lesson_id = _make_vocab_lesson(None)
    resp = client.get(f"/lessons/{lesson_id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'data-tts-text="先生"' in html
    assert 'data-tts-lang="ja"' in html
    # Beispielsatz-Container darf NICHT gerendert werden
    assert 'class="vocab-tts-example"' not in html

# tests/integration/test_srs_review_audio_payload.py
"""Sicherstellen, dass die /api/srs/due-Payload alle Felder enthaelt, die der
Audio-Button im Review-UI braucht — vor allem `tts_example_jp` fuer Grammar
und `example_jp` fuer Vocabulary, sonst kann der Button nichts vorlesen.
"""

from app import db
from app.models import LessonContent
from app.srs_service import get_content_data_for_review
from tests.factories import GrammarFactory, LessonFactory, VocabularyFactory


def _content_for(content_type: str, **kwargs) -> LessonContent:
    if content_type == "grammar":
        ref = GrammarFactory(**kwargs)
    else:
        ref = VocabularyFactory(**kwargs)
    lesson = LessonFactory()
    db.session.flush()
    lc = LessonContent(
        lesson_id=lesson.id,
        content_type=content_type,
        content_id=ref.id,
        order_index=0,
        page_number=1,
    )
    db.session.add(lc)
    db.session.commit()
    return lc


def test_grammar_review_payload_includes_tts_example_jp(app_context):
    """Audio-Button auf Grammar-Karte braucht reinen JP-Beispielsatz."""
    lc = _content_for("grammar", tts_example_jp="きょうは月曜日です。")
    data = get_content_data_for_review(lc)
    assert data["details"]["tts_example_jp"] == "きょうは月曜日です。"


def test_grammar_review_payload_empty_tts_when_unset(app_context):
    """Ohne tts_example_jp liefert das Service leeren String — Frontend
    rendert dann KEINEN Audio-Button (kein Fallback auf Title, der oft
    Romaji enthaelt)."""
    lc = _content_for("grammar", tts_example_jp=None)
    data = get_content_data_for_review(lc)
    assert data["details"]["tts_example_jp"] == ""


def test_vocabulary_review_payload_includes_example_jp(app_context):
    """Audio-Button auf Vokabel-Karte nutzt example_jp wenn vorhanden,
    sonst das Wort selbst — beide Felder muessen im Payload sein."""
    lc = _content_for(
        "vocabulary",
        word="先生",
        reading="せんせい",
        example_sentence_japanese="せんせいは やさしいです。",
    )
    data = get_content_data_for_review(lc)
    assert data["front"] == "先生"
    assert data["details"]["example_jp"] == "せんせいは やさしいです。"

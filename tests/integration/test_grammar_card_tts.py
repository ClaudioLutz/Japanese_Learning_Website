# tests/integration/test_grammar_card_tts.py
"""Sicherstellen, dass Grammatik-Karten den TTS-Beispielsatz rendern und der
Audio-Button explizit auf Japanisch zeigt — keine Mismatches mit der JP-Voice.
"""

from app import db
from app.models import Grammar, LessonContent
from tests.factories import GrammarFactory, LessonFactory


def _make_grammar_lesson(tts_example_jp: str | None) -> int:
    grammar = GrammarFactory(
        title="Topic-Partikel は",
        structure="N は N です。",
        example_sentences="わたしは学生です。",
        tts_example_jp=tts_example_jp,
    )
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    db.session.add(LessonContent(
        lesson_id=lesson.id,
        content_type="grammar",
        content_id=grammar.id,
        order_index=0,
        page_number=1,
    ))
    db.session.commit()
    return lesson.id


def test_grammar_card_audio_button_uses_tts_example_jp(client, app_context):
    """Audio-Button trägt den JP-Beispielsatz, nicht den (gemischten) Titel."""
    lesson_id = _make_grammar_lesson("きょうは月曜日です。")
    resp = client.get(f"/lessons/{lesson_id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Beispielsatz wird auf der Karte angezeigt
    assert "きょうは月曜日です。" in html
    # Audio-Button trägt diesen Satz UND ist explizit als Japanisch markiert
    assert 'data-tts-text="きょうは月曜日です。"' in html
    assert 'data-tts-lang="ja"' in html


def test_grammar_card_falls_back_to_title_when_tts_empty(client, app_context):
    """Ohne tts_example_jp greift Fallback auf Titel — der Button bleibt
    aber ja-markiert (Server lehnt deutschen Text dann eh ab)."""
    lesson_id = _make_grammar_lesson(None)
    resp = client.get(f"/lessons/{lesson_id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'data-tts-text="Topic-Partikel は"' in html
    assert 'data-tts-lang="ja"' in html


def test_grammar_model_has_tts_example_jp_column(app_context):
    """Schema-Sanity: das Feld existiert und ist nullable."""
    g = Grammar(
        title="Sanity",
        explanation="x",
        tts_example_jp="これはテストです。",
    )
    db.session.add(g)
    db.session.commit()
    assert g.tts_example_jp == "これはテストです。"

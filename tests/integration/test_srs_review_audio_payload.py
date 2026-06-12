# tests/integration/test_srs_review_audio_payload.py
"""Sicherstellen, dass die /api/srs/due-Payload alle Felder enthaelt, die der
Audio-Button im Review-UI braucht — vor allem `tts_example_jp` fuer Grammar
und `example_jp` fuer Vocabulary, sonst kann der Button nichts vorlesen.
"""

from app import db
from app.models import LessonContent
from app.srs_service import get_content_data_for_review
from tests.factories import (
    GrammarFactory,
    KanaFactory,
    LessonFactory,
    VocabularyFactory,
)


def _content_for(content_type: str, **kwargs) -> LessonContent:
    if content_type == "grammar":
        ref = GrammarFactory(**kwargs)
    elif content_type == "kana":
        ref = KanaFactory(**kwargs)
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


def test_grammar_review_payload_includes_examples_list(app_context):
    """Karten-Rückseite zeigt mehrere Beispielsätze — das Payload liefert die
    normalisierte Liste {japanese, romaji, translation} aus example_sentences."""
    lc = _content_for(
        "grammar",
        tts_example_jp="わたしは 学生です。",
        example_sentences=(
            "① わたしは 学生です。\n  (Watashi wa gakusei desu.)\n  — Ich bin Student.\n"
            "② あれは 本です。\n  (Are wa hon desu.)\n  — Das ist ein Buch.\n"
        ),
    )
    data = get_content_data_for_review(lc)
    examples = data["details"]["examples_list"]
    assert isinstance(examples, list) and len(examples) == 2
    assert examples[0] == {
        "japanese": "わたしは 学生です。",
        "romaji": "Watashi wa gakusei desu.",
        "translation": "Ich bin Student.",
    }
    assert examples[1]["japanese"] == "あれは 本です。"


def test_grammar_review_payload_includes_cloze(app_context):
    """Cloze-Review: Payload liefert Lückentext-Daten (Marker ausgeblendet)."""
    lc = _content_for(
        "grammar",
        structure="N も (mo)",
        tts_example_jp="グプタさんも 会社員です。",
        example_sentences=(
            "① グプタさんも 会社員です。\n  (Guputa-san mo kaishain desu.)\n"
            "  — Auch Herr Gupta ist Angestellter."
        ),
    )
    data = get_content_data_for_review(lc)
    cloze = data["details"]["cloze"]
    assert cloze is not None
    assert cloze["answer"] == "も"
    assert cloze["before"] == "グプタさん"


def test_grammar_review_payload_includes_nuance(app_context):
    """Kuratierte Nuance-Notiz fließt ins Review-Payload (oder leer)."""
    lc = _content_for("grammar", nuance="は markiert das Thema, が das Subjekt.")
    data = get_content_data_for_review(lc)
    assert data["details"]["nuance"] == "は markiert das Thema, が das Subjekt."


def test_kana_review_payload_includes_mnemonic_and_stroke_info(app_context):
    """Merkhilfe-Sektion auf der Kana-Rückseite: mnemonic (Eselsbrücke) und
    stroke_order_info (Strichfolge-Fallback) müssen im Payload sein."""
    lc = _content_for(
        "kana",
        mnemonic="Sieht aus wie ein Apfel-Männchen.",
        stroke_order_info="3 Striche: quer, senkrecht, Bogen.",
    )
    data = get_content_data_for_review(lc)
    assert data["details"]["mnemonic"] == "Sieht aus wie ein Apfel-Männchen."
    assert data["details"]["stroke_order_info"] == "3 Striche: quer, senkrecht, Bogen."


def test_kana_review_payload_empty_memo_fields_when_unset(app_context):
    """Ohne gepflegte Merkhilfe liefert das Service leere Strings — das
    Frontend rendert die Sektion dann gar nicht."""
    lc = _content_for("kana", mnemonic=None, stroke_order_info=None)
    data = get_content_data_for_review(lc)
    assert data["details"]["mnemonic"] == ""
    assert data["details"]["stroke_order_info"] == ""


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

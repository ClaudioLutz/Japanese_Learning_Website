# tests/unit/test_lesson_progress_visibility.py
"""Sicherstellen, dass UI-unsichtbare LessonContent-Items nicht in den
Progress einfliessen — sonst koennen User keine 100% erreichen.

Konkret: 'audio'-Items werden im Lesson-View ausgeblendet, wenn auf der
gleichen Page ein 'dialog_slideshow' steht. Solche Items duerfen daher
nicht im progress_percentage zaehlen.
"""

from __future__ import annotations

from app import db
from app.models import LessonContent, UserLessonProgress
from tests.factories import (
    CardReviewStateFactory,
    LessonFactory,
    UserFactory,
)


def _add(lesson_id, content_type, page_number, order_index=0, content_id=1,
         is_optional=False, media_url=None):
    """Hilfs-Helper fuer LessonContent ohne Referenz-Validation."""
    lc = LessonContent(
        lesson_id=lesson_id,
        content_type=content_type,
        content_id=content_id,
        order_index=order_index,
        page_number=page_number,
        is_optional=is_optional,
        media_url=media_url,
    )
    db.session.add(lc)
    return lc


def test_audio_on_slideshow_page_excluded_from_visible(app_context):
    """audio + slideshow auf gleicher Page → audio gilt als unsichtbar."""
    lesson = LessonFactory()
    db.session.flush()
    text = _add(lesson.id, 'text', page_number=1)
    audio = _add(lesson.id, 'audio', page_number=2)
    slideshow = _add(lesson.id, 'dialog_slideshow', page_number=2)
    db.session.commit()

    visible = lesson.progress_visible_content_items
    assert text in visible
    assert slideshow in visible
    assert audio not in visible, "audio auf Slideshow-Page sollte nicht zaehlen"


def test_audio_on_normal_page_still_visible(app_context):
    """audio ohne Slideshow auf gleicher Page → bleibt sichtbar (zaehlt)."""
    lesson = LessonFactory()
    db.session.flush()
    audio = _add(lesson.id, 'audio', page_number=1)
    db.session.commit()

    visible = lesson.progress_visible_content_items
    assert audio in visible


def test_progress_reaches_100_when_all_visible_completed(app_context, client):
    """Genau das Lesson-159-Szenario: 31 Items, davon 1 audio auf Slideshow-Page.
    User completed 30 (alle sichtbaren) → progress soll 100% sein, nicht 96%."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()

    items = []
    # 30 Items auf Pages 1-4 (alle sichtbar)
    for i in range(30):
        items.append(_add(lesson.id, 'text', page_number=(i // 8) + 1, order_index=i, content_id=i + 1))
    # Page 5: dialog_slideshow + audio (audio ist UI-unsichtbar)
    slideshow = _add(lesson.id, 'dialog_slideshow', page_number=5, order_index=0, content_id=100)
    audio = _add(lesson.id, 'audio', page_number=5, order_index=1, content_id=101)
    db.session.commit()

    progress = UserLessonProgress(
        user_id=user.id,
        lesson_id=lesson.id,
        content_progress='{}',
    )
    db.session.add(progress)
    # User markiert alle SICHTBAREN als done (30 text + slideshow = 31).
    cp = {str(i.id): True for i in items + [slideshow]}
    progress.set_content_progress(cp)
    progress.update_progress_percentage()

    assert progress.progress_percentage == 100, (
        f"Erwartet 100%, bekam {progress.progress_percentage}% — "
        f"audio-Item zaehlt faelschlich mit"
    )
    assert progress.is_completed is True


def test_progress_below_100_when_visible_item_missing(app_context):
    """Sanity: wenn ein sichtbares Item fehlt, ist Progress < 100%."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    a = _add(lesson.id, 'text', page_number=1, content_id=1)
    b = _add(lesson.id, 'text', page_number=1, content_id=2)
    db.session.commit()

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    progress.set_content_progress({str(a.id): True})  # nur 1 von 2
    progress.update_progress_percentage()

    assert progress.progress_percentage == 50
    assert progress.is_completed is False


def test_optional_items_excluded_from_progress(app_context):
    """Dekorative Seitenbilder (image + is_optional) zaehlen nicht zum
    Fortschritt: 100% muss ohne sie erreichbar sein (Lektionsbilder 2026-06)."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    text = _add(lesson.id, 'text', page_number=1, content_id=1)
    page_image = _add(
        lesson.id, 'image', page_number=1, order_index=0, content_id=None,
        is_optional=True,
        media_url='/uploads/lessons/page_images/lesson_1/page_1.webp',
    )
    db.session.commit()

    visible = lesson.progress_visible_content_items
    assert text in visible
    assert page_image not in visible, "optionales Seitenbild darf nicht zaehlen"

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()
    progress.set_content_progress({str(text.id): True})  # Bild NICHT markiert
    progress.update_progress_percentage()

    assert progress.progress_percentage == 100, (
        f"Erwartet 100% ohne Seitenbild-Klick, bekam {progress.progress_percentage}%"
    )
    assert progress.is_completed is True


def test_lesson_174_pattern_passive_outro_blocks_100(app_context):
    """Lesson-174-Regression: 30 Items (Vokabeln + Grammatik + Slideshow +
    interaktiver Text + Outro-Text). Wenn der User den Outro-Text NICHT
    explizit auf erledigt setzt, bleibt der Backend-Progress bei 96%
    (29/30). Das soll der Frontend-Auto-Complete-on-Page-Leave kuenftig
    verhindern; der Backend-Test stellt sicher, dass die Mathematik
    unveraendert ist und das Item korrekt zaehlt.
    """
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()

    items = []
    for i in range(27):
        items.append(_add(
            lesson.id, 'vocabulary', page_number=(i // 9) + 1,
            order_index=i, content_id=i + 1,
        ))
    slideshow = _add(lesson.id, 'dialog_slideshow', page_number=5, order_index=0, content_id=200)
    interactive_quiz_text = _add(lesson.id, 'text', page_number=6, order_index=0, content_id=201)
    outro = _add(lesson.id, 'text', page_number=7, order_index=0, content_id=202)
    db.session.commit()

    progress = UserLessonProgress(
        user_id=user.id, lesson_id=lesson.id, content_progress='{}',
    )
    db.session.add(progress)

    # Realistisches User-Verhalten: alle Vocab + Slideshow + Quiz-Text done,
    # aber Outro nicht angeklickt.
    cp = {str(i.id): True for i in items}
    cp[str(slideshow.id)] = True
    cp[str(interactive_quiz_text.id)] = True
    progress.set_content_progress(cp)
    progress.update_progress_percentage()

    assert progress.progress_percentage == 96, (
        f"Erwartet 96% (29/30 ohne Outro), bekam {progress.progress_percentage}%"
    )
    assert progress.is_completed is False

    # Sobald Outro auch completed (sei es via User-Klick oder Auto-Complete
    # beim Page-Verlassen), muss der Progress auf 100% springen.
    cp[str(outro.id)] = True
    progress.set_content_progress(cp)
    progress.update_progress_percentage()
    assert progress.progress_percentage == 100
    assert progress.is_completed is True


def _add_interactive(lesson_id, content_type, page_number, order_index=0, content_id=1):
    """LessonContent als interaktives Item (Quiz/Game) anlegen."""
    lc = LessonContent(
        lesson_id=lesson_id,
        content_type=content_type,
        content_id=content_id,
        order_index=order_index,
        page_number=page_number,
        is_interactive=True,
    )
    db.session.add(lc)
    return lc


def test_mark_passive_items_completed_excludes_interactive(app_context):
    """mark_passive_items_completed markiert passive Items ALLER Typen (auch
    solche ohne Erledigt-Button: dialog_slideshow, standalone audio), laesst aber
    interaktive Items (Quiz via is_interactive, kana_grid_game) unberuehrt."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    text = _add(lesson.id, 'text', page_number=1, content_id=1)
    slideshow = _add(lesson.id, 'dialog_slideshow', page_number=2, content_id=2)
    audio = _add(lesson.id, 'audio', page_number=3, content_id=3)  # standalone -> sichtbar
    quiz = _add_interactive(lesson.id, 'text', page_number=4, content_id=4)
    game = _add(lesson.id, 'kana_grid_game', page_number=5, content_id=5)
    db.session.commit()

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()

    changed = progress.mark_passive_items_completed()
    assert changed is True

    cp = progress.get_content_progress()
    # Passive Items markiert
    assert cp.get(str(text.id)) is True
    assert cp.get(str(slideshow.id)) is True
    assert cp.get(str(audio.id)) is True
    # Interaktive Items NICHT markiert
    assert cp.get(str(quiz.id)) is not True
    assert cp.get(str(game.id)) is not True
    # Quiz + Game blockieren den Abschluss noch (3 von 5 sichtbar)
    assert progress.progress_percentage == 60
    assert progress.is_completed is False

    # Quiz + Game ueber den interaktiven Pfad erledigen -> 100%
    progress.mark_content_completed(quiz.id)
    progress.mark_content_completed(game.id)
    assert progress.progress_percentage == 100
    assert progress.is_completed is True


def test_mark_passive_items_completed_full_passive_lesson(app_context):
    """Reine Passiv-Lektion (Slideshow + Text, kein Quiz) erreicht via
    mark_passive_items_completed direkt 100% — solche Lektionen konnten frueher
    NIE abgeschlossen werden (Slideshow ohne Erledigt-Pfad)."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    _add(lesson.id, 'dialog_slideshow', page_number=1, content_id=1)
    _add(lesson.id, 'text', page_number=1, order_index=1, content_id=2)
    db.session.commit()

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()

    progress.mark_passive_items_completed()
    assert progress.progress_percentage == 100
    assert progress.is_completed is True


def test_mark_passive_items_completed_excludes_flip_cards(app_context):
    """Regression Deck-Bug 2026-06-21 (Lektion 205): Flip-Card-Referenztypen
    (grammar/vocabulary/kanji/kana) haben einen EIGENEN Abschluss-Pfad (Deck-SRS-
    Rating) und duerfen vom passiven End-of-Lesson-Netz NICHT abgeraeumt werden —
    sonst gilt die Lektion als fertig, obwohl der User die Karten nie bewertet hat.

    Passive Items (Text/Slideshow) werden weiterhin abgeraeumt.
    """
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    text = _add(lesson.id, 'text', page_number=1, content_id=1)
    # Grammatik-Deck (2 Karten auf einer Seite) — wie Lektion 205 Seite 4
    gram1 = _add(lesson.id, 'grammar', page_number=2, order_index=0, content_id=2)
    gram2 = _add(lesson.id, 'grammar', page_number=2, order_index=1, content_id=3)
    # Vokabel-Deck
    vocab = _add(lesson.id, 'vocabulary', page_number=3, content_id=4)
    db.session.commit()

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()

    progress.mark_passive_items_completed()

    cp = progress.get_content_progress()
    # Passives Text-Item: abgeraeumt
    assert cp.get(str(text.id)) is True
    # Flip-Card-Deck-Karten: NICHT abgeraeumt
    assert cp.get(str(gram1.id)) is not True
    assert cp.get(str(gram2.id)) is not True
    assert cp.get(str(vocab.id)) is not True
    # Deck-Karten blockieren den Abschluss (1 von 4 sichtbar)
    assert progress.progress_percentage == 25
    assert progress.is_completed is False

    # Deck-Karten ueber ihren eigenen Pfad (Rating>=2 -> markContentComplete) erledigen
    progress.mark_content_completed(gram1.id)
    progress.mark_content_completed(gram2.id)
    progress.mark_content_completed(vocab.id)
    assert progress.progress_percentage == 100
    assert progress.is_completed is True


def test_globally_rated_flip_card_counts_toward_completion(app_context):
    """Entscheidung 2026-06-22: Eine Flip-Card gilt fuer den Lektionsabschluss als
    erledigt, sobald sie GLOBAL mindestens einmal bewertet wurde (card_review_state
    existiert) — auch ohne Deck-Rating in genau dieser Lektion. Behebt Mischzustaende
    (Karte global gemeistert, Lektion haengt unter 100%), z.B. Lektion 162."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    text = _add(lesson.id, 'text', page_number=1, content_id=1)
    vocab1 = _add(lesson.id, 'vocabulary', page_number=2, order_index=0, content_id=2)
    vocab2 = _add(lesson.id, 'vocabulary', page_number=2, order_index=1, content_id=3)
    db.session.commit()

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()

    # Passives Netz raeumt nur den Text ab; Flip-Cards bleiben offen.
    progress.mark_passive_items_completed()
    assert progress.get_content_progress().get(str(text.id)) is True
    assert progress.progress_percentage == 33  # 1 von 3 (Text)
    assert progress.is_completed is False

    # vocab1 wurde global (z.B. im /review) bewertet -> card_review_state existiert,
    # OHNE content_progress-Eintrag fuer diese Lektion.
    CardReviewStateFactory(user_id=user.id, content_id=vocab1.id)
    db.session.flush()
    progress.update_progress_percentage()
    assert progress.progress_percentage == 66  # Text + vocab1 (global)
    assert progress.is_completed is False

    # zweite Karte ebenfalls global gemeistert -> Lektion 100% / abgeschlossen.
    CardReviewStateFactory(user_id=user.id, content_id=vocab2.id)
    db.session.flush()
    progress.update_progress_percentage()
    assert progress.progress_percentage == 100
    assert progress.is_completed is True


def test_unrated_flip_card_still_blocks_completion(app_context):
    """Gegenprobe: eine Flip-Card OHNE jede Bewertung (kein card_review_state,
    kein content_progress) blockiert den Abschluss weiterhin — der globale
    Lernstand-Bonus greift nur fuer tatsaechlich bewertete Karten."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    _add(lesson.id, 'text', page_number=1, content_id=1)
    _add(lesson.id, 'vocabulary', page_number=2, content_id=2)
    db.session.commit()

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()

    progress.mark_passive_items_completed()
    # Text erledigt, Vokabel weder im Deck noch global bewertet -> 50%, nicht fertig.
    assert progress.progress_percentage == 50
    assert progress.is_completed is False
    # andere Karte (anderer content_id) bewertet -> zaehlt NICHT fuer diese Vokabel
    CardReviewStateFactory(user_id=user.id, content_id=99999)
    db.session.flush()
    progress.update_progress_percentage()
    assert progress.progress_percentage == 50
    assert progress.is_completed is False


def test_zero_visible_items_marks_completed(app_context):
    """Lektion ohne sichtbare Items (nur dekorative is_optional-Bilder) gilt als
    100% UND is_completed=True. Regression: frueher setzte update_progress_percentage
    bei 0 Items zwar 100%, kehrte aber VOR dem is_completed-Block zurueck."""
    user = UserFactory()
    lesson = LessonFactory()
    db.session.flush()
    _add(lesson.id, 'image', page_number=1, content_id=None, is_optional=True,
         media_url='/uploads/deco.webp')
    db.session.commit()

    assert lesson.progress_visible_content_items == []

    progress = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, content_progress='{}')
    db.session.add(progress)
    db.session.flush()
    progress.update_progress_percentage()

    assert progress.progress_percentage == 100
    assert progress.is_completed is True

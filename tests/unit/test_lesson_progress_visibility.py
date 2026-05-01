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
from tests.factories import LessonFactory, UserFactory


def _add(lesson_id, content_type, page_number, order_index=0, content_id=1):
    """Hilfs-Helper fuer LessonContent ohne Referenz-Validation."""
    lc = LessonContent(
        lesson_id=lesson_id,
        content_type=content_type,
        content_id=content_id,
        order_index=order_index,
        page_number=page_number,
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

# tests/integration/test_layout_lesson_view.py
"""Schablone D „Lektion" (docs/layout-standard.md §4 D) für /lessons/<id>.

- Hülle .page.lv-page mit Seitenkopf (Kennzeile, Titel, Untertitel) oben,
  Fortschrittsleiste „Seite N von M" und Seitenleiste (Seiten, Meta, Aktionen).
- Mobil: Seiten als Chip-Zeile, jede Seite ein Chip.
- Keine Header-/Inhalts-Karte mehr (Karten nur für echte Einheiten).
- „Weiter bei Seite N" nur, wenn last_page > 1.
- Sprunganker: scroll-margin-top unter Nav + Leiste.
- Deck-Invariante: die Lektions-Styles setzen nie display auf .content-item.
"""
import re

from app import db
from app.models import LessonContent, UserLessonProgress
from tests.factories import LessonCategoryFactory, LessonFactory


def _lesson(pages=3, **kw):
    cat = LessonCategoryFactory(name='N5 · Alltag', jlpt_level=5)
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True,
                           category_id=cat.id, title='Im Café', description='Getränke bestellen.',
                           estimated_duration=15, **kw)
    db.session.flush()
    for n in range(1, pages + 1):
        db.session.add(LessonContent(lesson_id=lesson.id, content_type='text', title=f'Teil {n}',
                                     content_text=f'<p>Seite {n}</p>', page_number=n, order_index=0))
    db.session.commit()
    return lesson


class TestLessonShell:
    def test_page_shell_head_bar_and_aside(self, client, app_context):
        lesson = _lesson(pages=3)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'class="page lv-page lv-page--paged"' in html
        assert '<h1 class="page-head__title" id="page-title">Im Café</h1>' in html
        assert 'class="page-head__eyebrow">N5 · Alltag<' in html
        assert 'id="lessonHeroIntro">Getränke bestellen.</p>' in html
        # Fortschrittsleiste + Zähler
        assert 'class="lv-bar"' in html and 'id="pageCounterBar">Seite 1 von 3<' in html
        # Seitenleiste: jede Seite ein Eintrag, Meta mit Dauer
        assert html.count('class="sidebar-page-item') == 3
        assert '<dt>Dauer</dt><dd>15 Min.</dd>' in html
        # mobil: Chip-Zeile
        assert len(re.findall(r'class="lv-chip(?: is-active)?"', html)) == 3
        # alte Karten-Hüllen sind weg
        assert 'lesson-header-card' not in html
        assert 'class="card lesson-content-card"' not in html
        assert 'class="lesson-content-card lv-read"' in html

    def test_single_page_lesson_without_bar_and_chips(self, client, app_context):
        lesson = _lesson(pages=1)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'class="page lv-page"' in html
        assert 'class="lv-bar"' not in html
        assert 'class="lv-chips"' not in html

    def test_guest_nudge_in_aside(self, client, app_context):
        lesson = _lesson(pages=2)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'id="lessonGuestNudge"' in html
        assert html.index('class="lv-aside"') < html.index('id="lessonGuestNudge"')


class TestResumeAction:
    def _progress(self, user, lesson, last_page):
        pr = UserLessonProgress(user_id=user.id, lesson_id=lesson.id, progress_percentage=30)
        pr.last_page = last_page
        db.session.add(pr)
        db.session.commit()

    def test_resume_button_when_last_page_beyond_first(self, auth_client):
        client, user = auth_client
        lesson = _lesson(pages=4)
        self._progress(user, lesson, 3)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'id="lessonResumeBtn"' in html
        assert 'onclick="goToPage(2)"' in html
        assert 'Weiter bei Seite 3' in html
        # Fortschritt + Wiederholen-Aktion in der Seitenleiste
        assert 'id="lessonProgressBlock"' in html and 'id="lessonProgressPct">30%<' in html
        assert 'href="/review"' in html

    def test_no_resume_on_first_page(self, auth_client):
        client, user = auth_client
        lesson = _lesson(pages=4)
        self._progress(user, lesson, 1)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'id="lessonResumeBtn"' not in html


class TestLessonStyles:
    def test_anchor_scroll_margin_below_sticky_bar(self, client, app_context):
        lesson = _lesson(pages=2)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert re.search(r'\.lv-page #lessonCarousel,[^{]*\{\s*scroll-margin-top: calc\(var\(--lv-sticky\)', html)
        assert re.search(r'\.lv-bar \{[^}]*position: sticky;[^}]*top: var\(--lv-nav-h\)', html)

    def test_lesson_styles_never_toggle_content_item_display(self, client, app_context):
        """Deck-Karussell: nur custom.css (.content-item.in-deck) blendet Karten aus."""
        lesson = _lesson(pages=2)
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        start = html.index('Schablone D „Lektion"')
        block = html[start:html.index('</style>', start)]
        for sel, body in re.findall(r'([^{}]*\.content-item[^{}]*)\{([^}]*)\}', block):
            assert 'display' not in body, sel

"""Deck-Karten-Filter: Karten tragen einen data-card-type (inkl. Hiragana/
Katakana-Unterscheidung), und das Filter-Gerüst wird ins HTML gerendert.

Hinweis: Die lokale Config erzwingt HTTPS (FLASK_ENV=production), daher werden
Requests mit base_url='https://localhost' gestellt, sonst 302 (HTTP→HTTPS).
"""

from app import db
from app.models import LessonContent
from tests.factories import LessonFactory, KanaFactory, VocabularyFactory

HTTPS = "https://localhost"


def _kana_lesson():
    hira = KanaFactory(character="あ", romanization="a", type="hiragana")
    kata = KanaFactory(character="ア", romanization="a", type="katakana")
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    for i, kana in enumerate((hira, kata)):
        db.session.add(LessonContent(
            lesson_id=lesson.id, content_type="kana", content_id=kana.id,
            order_index=i, page_number=1,
        ))
    db.session.commit()
    return lesson.id


def test_kana_cards_distinguish_hiragana_and_katakana(admin_client):
    client, _admin = admin_client
    lesson_id = _kana_lesson()

    resp = client.get(f"/lessons/{lesson_id}", base_url=HTTPS)
    assert resp.status_code == 200, resp.status_code
    html = resp.get_data(as_text=True)

    # Kana wird in Hiragana vs. Katakana aufgeschlüsselt (nicht nur "kana")
    assert 'data-card-type="hiragana"' in html
    assert 'data-card-type="katakana"' in html


def test_vocabulary_card_type(admin_client):
    client, _admin = admin_client
    vocab = VocabularyFactory(word="先生", reading="せんせい", meaning="teacher")
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    db.session.add(LessonContent(
        lesson_id=lesson.id, content_type="vocabulary", content_id=vocab.id,
        order_index=0, page_number=1,
    ))
    db.session.commit()

    resp = client.get(f"/lessons/{lesson.id}", base_url=HTTPS)
    assert resp.status_code == 200
    assert 'data-card-type="vocabulary"' in resp.get_data(as_text=True)


def test_deck_filter_scaffolding_present(admin_client):
    client, _admin = admin_client
    lesson_id = _kana_lesson()

    resp = client.get(f"/lessons/{lesson_id}", base_url=HTTPS)
    html = resp.get_data(as_text=True)

    # Filter-UI-Container + JS-Logik sind eingebunden
    assert "deck-filter-bar" in html
    assert "renderFilterBar" in html
    assert "TYPE_LABELS" in html


def test_review_page_filter_scaffolding_present(admin_client):
    """Die Wiederhol-Seite (/review) bindet die Typ-Filter-Logik ein.

    Die Pills selbst werden client-seitig aus den geladenen Karten erzeugt;
    serverseitig prüfen wir Container + JS-Funktionen.
    """
    client, _admin = admin_client

    resp = client.get("/review", base_url=HTTPS)
    assert resp.status_code == 200, resp.status_code
    html = resp.get_data(as_text=True)

    assert 'id="reviewFilterBar"' in html          # Filter-Leiste
    assert 'id="reviewFilterEmpty"' in html         # Filter-Leer-Status
    assert "function renderFilterBar" in html       # Pill-Rendering
    assert "function rebuildQueue" in html          # gefilterte Queue
    assert "function ftype" in html                 # Hiragana/Katakana-Split
    # Filter-Pills nutzen dieselben Styles wie das Lektions-Deck
    assert "deck-filter-pill" in html


def test_review_page_category_filter_present(admin_client):
    """Die Wiederhol-Seite bietet zusätzlich einen Gruppen-(Kategorie-)Filter."""
    client, _admin = admin_client

    resp = client.get("/review", base_url=HTTPS)
    assert resp.status_code == 200, resp.status_code
    html = resp.get_data(as_text=True)

    assert 'id="categorySelect"' in html             # Gruppen-Dropdown
    assert 'id="reviewFilters"' in html              # gemeinsames Filter-Panel
    assert "function renderCategorySelect" in html    # Optionen aus Fällig-Set
    assert "function matchesFilter" in html           # Typ UND Gruppe kombiniert
    assert "category-select" in html                  # gestyltes Select
    assert "card.category_id" in html                 # Karten-Filter nutzt Gruppen-ID


def test_review_page_locked_viewport_layout(admin_client):
    """Die Wiederhol-Seite ist auf die Bildschirmhöhe gesperrt (kein Page-Scroll).

    Karte = flexibler Restplatz, Bewertungs-Buttons gepinnt, Stats + Filter im
    Sheet hinter dem Einstellungs-Button, Footer/Impressum ausgeblendet.
    """
    client, _admin = admin_client

    resp = client.get("/review", base_url=HTTPS)
    assert resp.status_code == 200, resp.status_code
    html = resp.get_data(as_text=True)

    # Body-Klasse schaltet den Viewport-Lock scharf (overflow:hidden + 100dvh)
    assert "review-locked" in html
    assert "100dvh" in html
    # Gesperrte Bühne + kompakte Kopfzeile statt gestapelter Blöcke
    assert "review-screen" in html
    assert "review-topbar" in html
    # Übersicht (Stats) + Filter liegen im Slide-up-Sheet
    assert 'id="reviewSheet"' in html
    assert 'id="reviewSettingsBtn"' in html
    assert "function openSheet" in html
    # sessionTime-Element muss erhalten bleiben (JS schreibt hinein)
    assert 'id="sessionTime"' in html

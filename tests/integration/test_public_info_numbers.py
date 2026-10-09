"""Kennzahlen auf den oeffentlichen Infoseiten kommen aus EINER Quelle.

Hintergrund (09.10.2026): /jlpt-n5-schweiz nannte noch „473 Vokabeln" und
„55 Kanji" (auch im JSON-LD), /ueber „31 Lektionen" und „~50 Lektionen geplant",
/learn/n5 sprach im Gratis-Modus vom „Lifetime-Zugang". Die Zahlen standen fest
im Template und veralteten mit jeder neuen Lektion.

Jetzt liefert coverage_service.get_public_stats() (gecachte Fassung von
get_level_showcase, nur publizierte Inhalte) die Zahlen fuer Text,
Meta-Description und JSON-LD. Diese Tests sichern:
  * Seite + Meta-Description zeigen die Werte der gemeinsamen Quelle,
  * keine anderen Zaehl-Zahlen (feste Altwerte) stehen auf den Seiten,
  * ohne Kennzahlen rendern die Seiten weiter (Formulierungen ohne Zahlen),
  * im Gratis-Modus nichts, was nach Bezahlinhalt klingt,
  * der Rollenspiel-Tutor wird beschrieben, wie er ist (Konto, Tageslimit).
"""
import html
import json
import re
from unittest.mock import patch

import pytest

from app.services import coverage_service
from tests.factories import (
    KanjiFactory,
    LessonCategoryFactory,
    LessonContentFactory,
    LessonFactory,
    VocabularyFactory,
)

# Bewusst ungewoehnliche Werte: kommen sie auf der Seite vor, stammen sie aus
# der gemeinsamen Quelle und nicht aus einem zufaellig passenden Festwert.
FAKE_STATS = {
    "level": 5,
    "lessons": 4321,
    "modules": 17,
    "vocab": 1234,
    "grammar": 321,
    "kanji": 76,
    "kanji_total": 80,
    "scenes": 43,
    "quiz_questions": 2345,
    "vocab_pct": 97.6,
    "kanji_pct": 95.0,
    "vocab_covered": 706,
    "vocab_total": 723,
}

PAGES = ("/jlpt-n5-schweiz", "/ueber", "/learn/n5")

# Zaehl-Zahlen vor einem dieser Woerter muessen aus der Quelle stammen.
COUNT_RE = re.compile(
    r"(\d[\d']*)\+?\s+(?:N5-)?(Lektionen|Lektion|Vokabeln|Kanji|Module|Modulen|"
    r"Grammatikpunkte|Grammatikpunkten|Dialogszenen|Gesprächsszenen|Gespräche)\b"
)
# JLPT-Fakten (Pruefungsumfang N5/N4), keine Inhaltszahlen dieser Plattform.
JLPT_FACTS = {"700", "80", "1500", "300"}


@pytest.fixture
def free_mode(app, monkeypatch):
    monkeypatch.setitem(app.config, "FREE_MODE", True)
    return app


@pytest.fixture
def roleplay_on(app, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setitem(app.config, "ROLEPLAY_LIMIT_SESSIONS_PER_DAY", 7)
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    return app


@pytest.fixture
def fake_stats():
    with patch.object(coverage_service, "get_public_stats", return_value=dict(FAKE_STATS)) as m:
        yield m


def _text(body: str) -> str:
    """Sichtbarer Text + Meta/JSON-LD als ein String (Tags weg, Entities aufgeloest)."""
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(body))


def _meta_description(body: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', body)
    assert m, "Meta-Description fehlt"
    return html.unescape(m.group(1))


def _course_description(body: str) -> str:
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, flags=re.S):
        data = json.loads(html.unescape(block))
        for node in data.get("@graph", []):
            if node.get("@type") == "Course":
                return node["description"]
    raise AssertionError("Course-JSON-LD fehlt")


def _allowed_numbers(stats: dict, live: set[str]) -> set[str]:
    values = {stats[k] for k in ("lessons", "modules", "vocab", "grammar", "kanji",
                                 "kanji_total", "scenes", "vocab_covered", "vocab_total")}
    allowed = {str(v) for v in values} | {f"{v:,}".replace(",", "'") for v in values}
    return allowed | live | {"7"} | JLPT_FACTS


def _live_counts(client) -> set[str]:
    """Zahlen, die die Seiten unabhaengig von get_public_stats live zaehlen:
    Gast-Lektionen (n5_free_lesson_count) und N5-Module (Lernpfad)."""
    with client.application.app_context():
        from app.models import Lesson, LessonCategory
        guest = Lesson.query.filter_by(
            is_published=True, allow_guest_access=True, lesson_type="free"
        ).count()
        modules = LessonCategory.query.filter_by(jlpt_level=5).count()
    return {str(guest), str(modules)}


class TestNumbersFromSharedSource:
    @pytest.mark.parametrize("path", PAGES)
    def test_only_source_numbers_on_page(self, client, db, free_mode, roleplay_on, fake_stats, path):
        body = client.get(path).get_data(as_text=True)
        allowed = _allowed_numbers(FAKE_STATS, _live_counts(client))
        found = {m.group(1) for m in COUNT_RE.finditer(_text(body))}
        stray = found - allowed
        assert not stray, f"{path}: feste/fremde Zahlen auf der Seite: {sorted(stray)}"

    def test_jlpt_schweiz_page_meta_and_jsonld_use_source(self, client, db, free_mode, fake_stats):
        body = client.get("/jlpt-n5-schweiz").get_data(as_text=True)
        meta = _meta_description(body)
        assert "4321 Lektionen" in meta
        assert "1'234 Vokabeln" in meta
        assert "76 der 80 N5-Kanji" in meta
        assert "komplett kostenlos" in meta
        course = _course_description(body)
        assert "4321 Lektionen" in course
        assert "1234 Vokabeln" in course
        assert "321 Grammatikpunkte" in course
        text = _text(body)
        assert "17 Module mit 4321 Lektionen" in text
        assert "Alle 4321 Lektionen kostenlos" in text

    def test_learn_n5_meta_and_coverage_use_source(self, client, db, free_mode, fake_stats):
        body = client.get("/learn/n5").get_data(as_text=True)
        assert "4321 Lektionen" in _meta_description(body)
        text = _text(body)
        assert "706 von 723 N5-Vokabeln" in text
        assert "76 von 80 N5-Kanji" in text

    def test_ueber_stand_heute_uses_source(self, client, db, free_mode, fake_stats):
        text = _text(client.get("/ueber").get_data(as_text=True))
        assert "Stand heute: 4321 Lektionen in 17 Modulen" in text
        assert "1'234 Vokabeln" in text
        assert "76 von 80 N5-Kanji" in text
        assert "321 Grammatikpunkten und 43 Dialogszenen" in text

    def test_all_kanji_phrase_when_complete(self, client, db, free_mode):
        stats = dict(FAKE_STATS, kanji=80)
        with patch.object(coverage_service, "get_public_stats", return_value=stats):
            body = client.get("/jlpt-n5-schweiz").get_data(as_text=True)
        assert "alle 80 N5-Kanji" in _meta_description(body)

    def test_real_db_numbers_reach_page(self, client, db, free_mode):
        """Ohne Mock: zwei publizierte N5-Lektionen, eine unpublizierte zaehlt nicht."""
        cat = LessonCategoryFactory(jlpt_level=5)
        published = [LessonFactory(category_id=None, is_published=True) for _ in range(2)]
        hidden = LessonFactory(category_id=None, is_published=False)
        db.session.flush()
        for lesson in (*published, hidden):
            lesson.category_id = cat.id
        vocab = [VocabularyFactory() for _ in range(3)]
        KanjiFactory(character="大")
        db.session.flush()
        LessonContentFactory(lesson_id=published[0].id, content_type="vocabulary", content_id=vocab[0].id)
        LessonContentFactory(lesson_id=published[1].id, content_type="vocabulary", content_id=vocab[1].id)
        LessonContentFactory(lesson_id=hidden.id, content_type="vocabulary", content_id=vocab[2].id)
        db.session.commit()

        stats = coverage_service.get_level_showcase(5)
        assert stats["lessons"] == 2 and stats["vocab"] == 2
        body = client.get("/jlpt-n5-schweiz").get_data(as_text=True)
        meta = _meta_description(body)
        assert f"{stats['lessons']} Lektionen, {stats['vocab']} Vokabeln" in meta
        body = client.get("/ueber").get_data(as_text=True)
        assert f"Stand heute: {stats['lessons']} Lektionen in {stats['modules']} Modulen" in _text(body)


class TestStaleWordingGone:
    STALE = (
        "473", "55 N5-Kanji", "55 zentrale", "55 Kanji", "30+ Lektionen", "9 Module",
        "31 Lektionen", "~50 Lektionen", "Konversations-Trainings mit MP3",
        "Strichreihenfolge", "105 Minuten", "Anmeldung öffnet im Sommer 2026",
        "im Verlauf des Jahres publiziert",
    )

    @pytest.mark.parametrize("path", PAGES)
    def test_no_stale_fixed_values(self, client, db, free_mode, roleplay_on, fake_stats, path):
        body = client.get(path).get_data(as_text=True)
        for stale in self.STALE:
            assert stale not in body, f"{path}: veraltete Angabe {stale!r} steht noch auf der Seite"

    @pytest.mark.parametrize("path", PAGES + ("/lernmethode",))
    def test_free_mode_has_no_paid_wording(self, client, db, free_mode, roleplay_on, fake_stats, path):
        text = _text(client.get(path).get_data(as_text=True))
        for paid in ("Lifetime", "lifetime", "CHF 9.90", "Geld zurück", "Premium", "Gratis-Lektionen"):
            assert paid not in text, f"{path}: {paid!r} klingt im Gratis-Modus nach Bezahlinhalt"


class TestRoleplayDescription:
    def test_jlpt_schweiz_describes_tutor_honestly(self, client, db, free_mode, roleplay_on, fake_stats):
        text = _text(client.get("/jlpt-n5-schweiz").get_data(as_text=True))
        assert "keine Konversation" not in text
        assert "das gibt es bei uns nicht" not in text
        assert "Rollenspiel-Tutor" in text
        assert "kein Aussprache-Feedback" in text
        assert "kostenloses Konto" in text
        assert "pro Tag sind 7 Gespräche möglich" in text   # Limit aus der Konfiguration

    def test_ueber_mentions_tutor_as_existing(self, client, db, free_mode, roleplay_on, fake_stats):
        text = _text(client.get("/ueber").get_data(as_text=True))
        assert "Gesprächstraining gibt es inzwischen" in text
        assert "pro Tag sind 7 Gespräche möglich" in text

    def test_without_roleplay_no_tutor_claims(self, client, db, free_mode, fake_stats):
        text = _text(client.get("/jlpt-n5-schweiz").get_data(as_text=True))
        assert "Rollenspiel-Tutor" not in text
        assert "keine Konversation" in text
        assert "Gesprächstraining gibt es inzwischen" not in _text(client.get("/ueber").get_data(as_text=True))


class TestFallbackWithoutStats:
    @pytest.mark.parametrize("path", PAGES)
    def test_pages_render_without_numbers(self, client, db, free_mode, path):
        with patch.object(coverage_service, "get_public_stats", side_effect=RuntimeError("DB weg")):
            resp = client.get(path)
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert _meta_description(body)
        found = {m.group(1) for m in COUNT_RE.finditer(_text(body))}
        allowed = _live_counts(client) | JLPT_FACTS
        assert found <= allowed, f"{path}: Zahlen ohne Quelle im Fallback: {sorted(found - allowed)}"


class TestPublicStatsCache:
    def test_cache_reuses_value_within_ttl(self, app, monkeypatch):
        monkeypatch.setitem(app.config, "PUBLIC_STATS_CACHE_SECONDS", 60)
        coverage_service.clear_public_stats_cache()
        with app.app_context(), patch.object(
            coverage_service, "get_level_showcase", return_value={"lessons": 1}
        ) as showcase:
            assert coverage_service.get_public_stats(5) == {"lessons": 1}
            assert coverage_service.get_public_stats(5) == {"lessons": 1}
            assert showcase.call_count == 1
            coverage_service.clear_public_stats_cache()
            coverage_service.get_public_stats(5)
            assert showcase.call_count == 2
        coverage_service.clear_public_stats_cache()

    def test_ttl_zero_disables_cache(self, app):
        assert app.config["PUBLIC_STATS_CACHE_SECONDS"] == 0
        with app.app_context(), patch.object(
            coverage_service, "get_level_showcase", return_value={"lessons": 1}
        ) as showcase:
            coverage_service.get_public_stats(5)
            coverage_service.get_public_stats(5)
            assert showcase.call_count == 2

"""Unit-Tests fuer den Neuigkeiten-Parser (app/news_service.py)."""
from datetime import date

from app import news_service
from app.news_service import group_by_day, parse_news

SAMPLE = """# Neuigkeiten

<!--
## 2099-01-01 | Kommentar-Eintrag darf nicht zaehlen
-->

## 2026-09-22 | Aelter
Ein Satz.

## 2026-09-24 | Erster am Tag
Zwei Saetze. Noch einer.
Link: /review

## 2026-09-24 | Zweiter am Tag
Text mit **fett**.

## kaputt ohne Datum
wird uebersprungen
"""


def test_parse_basic_fields_and_order():
    entries = parse_news(SAMPLE)
    assert [e.title for e in entries] == ['Erster am Tag', 'Zweiter am Tag', 'Aelter']
    first = entries[0]
    assert first.day == date(2026, 9, 24)
    assert first.link == '/review'
    assert first.body == 'Zwei Saetze. Noch einer.'
    assert entries[1].link is None


def test_comments_and_broken_headers_ignored():
    titles = [e.title for e in parse_news(SAMPLE)]
    assert 'Kommentar-Eintrag darf nicht zaehlen' not in titles
    assert not any('kaputt' in t for t in titles)
    # Text nach kaputter Kopfzeile landet NICHT im vorherigen Eintrag.
    assert all('uebersprungen' not in e.body for e in parse_news(SAMPLE))


def test_invalid_date_skipped():
    assert parse_news('## 2026-13-40 | Unmoeglich\nText') == []


def test_empty_input():
    assert parse_news('') == []
    assert parse_news(None) == []


def test_group_by_day():
    groups = group_by_day(parse_news(SAMPLE))
    assert [d for d, _ in groups] == [date(2026, 9, 24), date(2026, 9, 22)]
    assert len(groups[0][1]) == 2


def test_day_de_format():
    assert news_service.format_day_de(date(2026, 9, 4)) == '4. September 2026'


def test_repo_file_parses_and_has_week_entries():
    """Die echte Datei ist lesbar, hat Eintraege und nutzt keine Commit-Hashes."""
    entries = news_service.load_news(news_service.NEWS_PATH)
    assert len(entries) >= 10
    assert entries[0].day >= date(2026, 9, 24)
    for e in entries:
        assert e.title and e.body
        assert 'Mayuko' not in e.body and 'Mayuko' not in e.title
        if e.link:
            assert e.link.startswith('/')


def test_missing_file_returns_empty(tmp_path):
    assert news_service.load_news(tmp_path / 'fehlt.md') == []

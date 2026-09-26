"""Neuigkeiten für Lernende: Parser für app/data/neuigkeiten.md + „seit letztem Besuch"-Zähler.

Die Datei ist die EINZIGE Quelle für die öffentliche Seite /neu und für die
Zeile „Seit deinem letzten Besuch neu: …" im Willkommen-zurück-Dialog.

Format je Eintrag (neueste zuerst, HTML-Kommentare und die H1 werden ignoriert):

    ## 2026-09-24 | Titel
    1–3 Sätze Markdown.
    Link: /pfad        (optional)

Einträge tragen nur ein Datum (keine Uhrzeit). Als „neu seit X" zählt ein Eintrag,
wenn sein Datum NACH dem CH-Kalendertag von X liegt — am selben Tag Gesehenes
wird so nicht doppelt gemeldet.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

NEWS_PATH = Path(__file__).resolve().parent / 'data' / 'neuigkeiten.md'
PREV_LOGIN_SESSION_KEY = 'wb_prev_login'

_HEADER_RE = re.compile(r'^##\s+(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*$')
_LINK_RE = re.compile(r'^Link:\s*(\S+)\s*$', re.IGNORECASE)
_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

_MONTHS_DE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
              'August', 'September', 'Oktober', 'November', 'Dezember']
_UTC = ZoneInfo('UTC')
_CH = ZoneInfo('Europe/Zurich')


@dataclass(frozen=True)
class NewsEntry:
    day: date
    title: str
    body: str
    link: str | None = None

    @property
    def day_de(self) -> str:
        return format_day_de(self.day)


def format_day_de(d: date) -> str:
    return f'{d.day}. {_MONTHS_DE[d.month]} {d.year}'


def parse_news(text: str) -> list[NewsEntry]:
    """Markdown-Text → Einträge, neueste zuerst (innerhalb eines Tages Dateireihenfolge).

    Kaputte Kopfzeilen (falsches Datum) werden geloggt und übersprungen — die
    Seite soll wegen eines Tippfehlers nie ausfallen.
    """
    text = _COMMENT_RE.sub('', text or '')
    entries: list[NewsEntry] = []
    current: dict | None = None

    def flush():
        if current is not None:
            body = '\n'.join(current['lines']).strip()
            entries.append(NewsEntry(current['day'], current['title'], body, current['link']))

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith('## '):
            flush()
            current = None
            m = _HEADER_RE.match(line)
            if not m:
                logger.warning('Neuigkeiten: Kopfzeile nicht lesbar: %r', line)
                continue
            try:
                day = date.fromisoformat(m.group(1))
            except ValueError:
                logger.warning('Neuigkeiten: ungültiges Datum: %r', line)
                continue
            current = {'day': day, 'title': m.group(2), 'lines': [], 'link': None}
            continue
        if current is None:
            continue  # H1, Vorspann
        lm = _LINK_RE.match(line.strip())
        if lm:
            current['link'] = lm.group(1)
            continue
        current['lines'].append(line)
    flush()
    # sorted() ist stabil → Dateireihenfolge innerhalb eines Tages bleibt.
    return sorted(entries, key=lambda e: e.day, reverse=True)


_cache: dict = {'mtime': None, 'entries': []}


def load_news(path: Path | None = None) -> list[NewsEntry]:
    """Einträge aus der Datei (mtime-gecacht). Fehlt die Datei → leere Liste."""
    p = path or NEWS_PATH
    try:
        mtime = p.stat().st_mtime
    except OSError:
        logger.warning('Neuigkeiten-Datei fehlt: %s', p)
        return []
    if path is None and _cache['mtime'] == mtime:
        return _cache['entries']
    entries = parse_news(p.read_text(encoding='utf-8'))
    if path is None:
        _cache.update(mtime=mtime, entries=entries)
    return entries


def group_by_day(entries: list[NewsEntry]) -> list[tuple[date, list[NewsEntry]]]:
    groups: list[tuple[date, list[NewsEntry]]] = []
    for e in entries:
        if groups and groups[-1][0] == e.day:
            groups[-1][1].append(e)
        else:
            groups.append((e.day, [e]))
    return groups


# ── „Seit deinem letzten Besuch" ────────────────────────────────────────────

def remember_prev_login(prev_login: datetime | None) -> None:
    """Beim Login den last_login-Wert VOR dem Login in der Session festhalten.

    Der Login überschreibt last_login mit „jetzt" — der Dialog braucht aber den
    vorletzten Login als Referenz. None (erster Login) wird ebenfalls gemerkt.
    """
    from flask import session

    session[PREV_LOGIN_SESSION_KEY] = prev_login.isoformat() if prev_login else None


def since_reference(user, prev_activity: str | None) -> datetime | None:
    """Referenzzeitpunkt (UTC, naiv) für „seit deinem letzten Besuch".

    Basis ist der vorletzte Login: nach frischem Login aus der Session, sonst
    (Remember-Cookie, kein neuer Login) user.last_login. Weil ein Remember-Login
    Wochen alt sein kann, gilt zusätzlich der Beginn des letzten aktiven Tages
    (prev_activity, ISO-Datum) als Untergrenze — es zählt der spätere Wert.
    """
    from flask import has_request_context, session

    base = None
    if has_request_context() and PREV_LOGIN_SESSION_KEY in session:
        raw = session.get(PREV_LOGIN_SESSION_KEY)
        if raw:
            try:
                base = datetime.fromisoformat(raw)
            except ValueError:
                base = None
    else:
        base = getattr(user, 'last_login', None)

    act = None
    if prev_activity:
        from app.time_utils import ch_day_start_utc
        try:
            act = ch_day_start_utc(date.fromisoformat(prev_activity))
        except ValueError:
            act = None

    candidates = [c for c in (base, act) if c is not None]
    return max(candidates) if candidates else None


def _ch_date(utc_naive: datetime) -> date:
    return utc_naive.replace(tzinfo=_UTC).astimezone(_CH).date()


def news_since(since: datetime | None, languages: list[str] | None = None) -> dict:
    """Neue publizierte Lektionen + neue Neuigkeiten-Einträge seit `since`.

    Lektionen: kein eigener Publikations-Zeitstempel im Modell → Lesson.created_at
    (UTC) bei is_published. Ohne Referenz (Erstbesuch) alles 0.
    """
    result = {'lessons': 0, 'updates': 0, 'total': 0, 'url': '/neu'}
    if since is None:
        return result

    from app.models import Lesson

    q = Lesson.query.filter(Lesson.is_published.is_(True), Lesson.created_at > since)
    if languages:
        q = q.filter(Lesson.instruction_language.in_(languages))
    result['lessons'] = q.count()

    since_day = _ch_date(since)
    result['updates'] = sum(1 for e in load_news() if e.day > since_day)
    result['total'] = result['lessons'] + result['updates']
    return result

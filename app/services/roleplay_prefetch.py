"""Vorausberechnung der Bot-Antworten auf die drei Antwortvorschlaege.

Sobald ein Bot-Zug mit Vorschlaegen steht, rechnet der Server im Hintergrund
(Thread-Pool im Gunicorn-Prozess) fuer jeden Vorschlag die Antwort des
Gespraechspartners vor und legt sie in ``roleplay_prefetch`` ab. Die Tabelle
ist worker-uebergreifend: jeder Gunicorn-Worker findet die Ergebnisse.

Waehlt der Nutzer einen Vorschlag (Text stimmt nach Normalisierung ueberein),
kommt die Antwort ohne neuen Modell-Aufruf; laeuft die Vorausberechnung noch,
wartet der Zug auf sie statt einen zweiten Aufruf zu starten. Sonst: normaler
Modell-Aufruf.

Kosten/Limits:
- Vorausberechnungen zaehlen NICHT gegen Nutzerlimits, wohl aber gegen die
  globale Tageskappe (roleplay_service.model_replies_today zaehlt alle Zeilen
  ausser ``used`` — die uebernommene Antwort zaehlt schon als Bot-Zug).
- Kein Vorausrechnen, wenn die Kappe damit ueberschritten wuerde.
- Zeilen aelter als 24 h loescht cleanup_old() (laeuft bei jedem Gespraechsstart).

Gast-Demo: gleiche Tabelle, Schluessel demo_key = Hash des Demo-Tokens,
session_id NULL. Gespeichert werden nur vom Server/Modell verfasste Vorschlaege
und Antworten, nie Freitext eines Gastes; nach dem Zug wird response_json geleert.

Zweiter Aufruf des zweigeteilten Zugs (roleplay_service.split_enabled): Die
Lernhilfen zur schon gesendeten Bot-Zeile (Lesung, Uebersetzung, Vorschlaege,
Tipp) rechnet ein eigener kleiner Thread-Pool (2 Threads, damit sie nie hinter
Vorausberechnungen warten). Buchfuehrung in derselben Tabelle: Zeile mit
leerem norm_text (= Details, nie ein Vorschlags-Treffer), turn_index = Zahl der
Nutzerzuege danach. Sie zaehlt wie jede Zeile als eigener Modell-Aufruf gegen
die globale Tageskappe. Eingeloggt landen die Texte im RoleplayTurn, in der
Demo in response_json (wird beim naechsten Zug geleert). Erst wenn die Details
stehen, startet die Vorausberechnung der drei Vorschlaege.

Schalter (app.config/Env): ROLEPLAY_PREFETCH (Default an, in Tests aus),
ROLEPLAY_PREFETCH_SYNC (Tests: synchron statt Thread), ROLEPLAY_PREFETCH_THREADS (3).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator

from flask import current_app
from sqlalchemy import func, update

from app import db
from app.models import LessonContent, RoleplayPrefetch, RoleplaySession
from app.services import roleplay_service as svc

logger = logging.getLogger(__name__)

MAX_AGE_H = 24              # Aufraeumen: Zeilen aelter als das
WAIT_PENDING_S = 25.0       # so lange wartet ein Zug auf eine laufende Vorausberechnung
PENDING_STALE_S = 70.0      # aeltere pending-Zeilen gelten als verwaist (Worker-Neustart)
POLL_S = 0.2
DEFAULT_THREADS = 3

_NORM_RE = re.compile(r'[\s。．.、，,！!？?「」『』（）()・…〜~\'"“”„]')

DETAILS_THREADS = 2
DETAILS_MARK = ''            # norm_text der Details-Zeilen (Vorschlaege haben nie einen leeren)

_executor: ThreadPoolExecutor | None = None
_details_executor: ThreadPoolExecutor | None = None
_executor_lock = threading.Lock()


# ── Konfiguration ────────────────────────────────────────────────────────

def _flag(name: str) -> bool | None:
    raw = svc._setting(name).lower()
    if not raw:
        return None
    return raw in ('1', 'true', 'yes', 'on')


def enabled() -> bool:
    """Default an; in Tests (app.testing) aus, solange nicht ausdruecklich gesetzt."""
    val = _flag('ROLEPLAY_PREFETCH')
    if val is None:
        return not current_app.testing
    return val


def _sync() -> bool:
    return bool(_flag('ROLEPLAY_PREFETCH_SYNC'))


def _threads() -> int:
    try:
        return max(1, int(svc._setting('ROLEPLAY_PREFETCH_THREADS') or DEFAULT_THREADS))
    except ValueError:
        return DEFAULT_THREADS


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=_threads(), thread_name_prefix='rp-prefetch')
        return _executor


def _get_details_executor() -> ThreadPoolExecutor:
    global _details_executor
    with _executor_lock:
        if _details_executor is None:
            _details_executor = ThreadPoolExecutor(max_workers=DETAILS_THREADS, thread_name_prefix='rp-details')
        return _details_executor


# ── Hilfen ───────────────────────────────────────────────────────────────

def normalize(text: str | None) -> str:
    """Vergleichsform: NFKC, ohne Leerraum und Satzzeichen."""
    return _NORM_RE.sub('', unicodedata.normalize('NFKC', text or ''))[:400]


def demo_key(token: str) -> str:
    return hashlib.sha256((token or '').encode()).hexdigest()[:40]


def _key_filter(query, session_id: int | None, demo: str | None):
    if session_id is not None:
        return query.filter(RoleplayPrefetch.session_id == session_id)
    return query.filter(RoleplayPrefetch.session_id.is_(None), RoleplayPrefetch.demo_key == demo)


def count_today() -> int:
    """Modell-Aufrufe durch Vorausberechnung heute (ohne uebernommene Antworten)."""
    return RoleplayPrefetch.query.filter(
        RoleplayPrefetch.created_at >= svc._day_start(),
        RoleplayPrefetch.status != 'used',
    ).count()


def cost_today() -> float:
    val = db.session.query(func.coalesce(func.sum(RoleplayPrefetch.cost_usd), 0.0)).filter(
        RoleplayPrefetch.created_at >= svc._day_start(),
    ).scalar()
    return float(val or 0.0)


def cleanup_old(hours: int = MAX_AGE_H) -> int:
    """Loescht Vorausberechnungen aelter als `hours` (abgebrochene Gespraeche). Committet."""
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        n = RoleplayPrefetch.query.filter(RoleplayPrefetch.created_at < cutoff).delete(
            synchronize_session=False)
        db.session.commit()
        if n:
            logger.info('Rollenspiel-Prefetch: %d alte Zeilen geloescht', n)
        return int(n or 0)
    except Exception:  # Aufraeumen darf nie einen Start verhindern
        db.session.rollback()
        logger.exception('Rollenspiel-Prefetch: Aufraeumen fehlgeschlagen')
        return 0


def _capacity_ok(n: int) -> bool:
    try:
        return (svc.model_replies_today() + n <= svc.limit_value('ROLEPLAY_DAILY_MESSAGE_CAP')
                and svc.cost_today() < svc.daily_cost_cap())
    except Exception:
        logger.exception('Rollenspiel-Prefetch: Kappenpruefung fehlgeschlagen')
        return False


# ── Nachschlagen ─────────────────────────────────────────────────────────

def take(*, turn_index: int, text: str, session_id: int | None = None, demo: str | None = None,
         wait_s: float = WAIT_PENDING_S) -> dict[str, Any] | None:
    """Vorausberechnete Antwort fuer `text` holen und als ``used`` markieren.

    Wartet auf eine noch laufende Vorausberechnung (hoechstens wait_s). Liefert
    die validierten Zugdaten oder None (kein Treffer → normaler Modell-Aufruf).
    Committet nicht — der Aufrufer verbucht den Zug in derselben Transaktion.
    """
    norm = normalize(text)
    if not norm or (session_id is None and not demo):
        return None
    query = _key_filter(RoleplayPrefetch.query, session_id, demo).filter(
        RoleplayPrefetch.turn_index == turn_index,
        RoleplayPrefetch.norm_text == norm,
        RoleplayPrefetch.norm_text != DETAILS_MARK,
    ).order_by(RoleplayPrefetch.id.desc())
    row = query.first()
    if row is None:
        return None
    if row.status == 'pending':
        fresh = row.created_at and row.created_at > datetime.utcnow() - timedelta(seconds=PENDING_STALE_S)
        deadline = time.monotonic() + (wait_s if fresh else 0)
        while row.status == 'pending' and time.monotonic() < deadline:
            time.sleep(POLL_S)
            db.session.refresh(row)
    if row.status != 'ready' or not row.response_json:
        return None
    try:
        data = json.loads(row.response_json)
    except (TypeError, ValueError):
        return None
    tbl = RoleplayPrefetch.__table__
    res = db.session.execute(
        update(tbl).where(tbl.c.id == row.id, tbl.c.status == 'ready').values(status='used'))
    if res.rowcount != 1:  # type: ignore[attr-defined]
        return None
    return data if isinstance(data, dict) else None


def consume(*, turn_index: int, session_id: int | None = None, demo: str | None = None) -> None:
    """Nach dem Zug: uebrige Vorausberechnungen dieses Zugs verfallen lassen
    (Antworttext leeren, Zeile bleibt fuer die Tageskappe). Committet nicht."""
    if session_id is None and not demo:
        return
    base = _key_filter(RoleplayPrefetch.query, session_id, demo).filter(
        RoleplayPrefetch.turn_index <= turn_index)
    base.filter(RoleplayPrefetch.status.in_(('pending', 'ready', 'failed'))).update(
        {'status': 'stale'}, synchronize_session=False)
    # Antworttexte nicht aufbewahren (die uebernommene steckt schon im Bot-Zug).
    base.filter(RoleplayPrefetch.response_json.isnot(None)).update(
        {'response_json': None}, synchronize_session=False)


# ── Planen + Hintergrundlauf ─────────────────────────────────────────────

def _new_rows(suggestions: list[dict[str, Any]], turn_index: int, *, session_id: int | None,
              demo: str | None) -> list[RoleplayPrefetch]:
    rows: list[RoleplayPrefetch] = []
    seen: set[str] = set()
    for s in suggestions or []:
        text = str((s or {}).get('jp') or '').strip()
        norm = normalize(text)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        rows.append(RoleplayPrefetch(session_id=session_id, demo_key=demo, turn_index=turn_index,
                                     user_text=text[:300], norm_text=norm, status='pending',
                                     created_at=datetime.utcnow()))
    return rows


def _submit(fn: Callable[..., None], *args: Any, details: bool = False) -> None:
    app = current_app._get_current_object()  # type: ignore[attr-defined]
    if _sync():
        fn(app, True, *args)
    else:
        (_get_details_executor() if details else _get_executor()).submit(fn, app, False, *args)


@contextmanager
def _job_context(app, sync: bool) -> Iterator[None]:
    if sync:
        yield
        return
    with app.app_context():
        try:
            yield
        finally:
            db.session.remove()


def _provider() -> svc.RoleplayProvider:
    provider = svc.get_provider()
    try:
        provider.priority = 'low'   # Bridge: Vorausberechnung laesst einen Platz fuer Live-Zuege frei
    except AttributeError:
        pass
    return provider


def _finish(row_id: int, data: dict[str, Any] | None, usage: svc.Usage, keep_text: bool = True) -> None:
    tbl = RoleplayPrefetch.__table__
    values: dict[str, Any] = {
        'status': 'ready' if data is not None else 'failed',
        'tokens_in': usage.tokens_in, 'tokens_out': usage.tokens_out, 'cost_usd': usage.cost_usd,
    }
    if data is not None and keep_text:
        values['response_json'] = json.dumps(data, ensure_ascii=False)
    res = db.session.execute(update(tbl).where(tbl.c.id == row_id, tbl.c.status == 'pending').values(**values))
    if res.rowcount != 1:  # type: ignore[attr-defined]
        # Zug schon weiter (stale): nur die Kosten nachtragen (Kostenkappe ehrlich).
        db.session.execute(update(tbl).where(tbl.c.id == row_id).values(
            tokens_in=usage.tokens_in, tokens_out=usage.tokens_out, cost_usd=usage.cost_usd))
    db.session.commit()


def _run(row_id: int, compute: Callable[[RoleplayPrefetch], svc.TurnResult | None]) -> None:
    row = db.session.get(RoleplayPrefetch, row_id)
    if row is None or row.status != 'pending':
        return
    started = time.monotonic()
    try:
        result = compute(row)
    except svc.UpstreamError as exc:
        logger.info('Rollenspiel-Prefetch %s: Upstream-Fehler', row_id)
        _finish(row_id, None, exc.usage)
        return
    except Exception:
        db.session.rollback()
        logger.exception('Rollenspiel-Prefetch %s: Fehler', row_id)
        _finish(row_id, None, svc.Usage())
        return
    if result is None:
        db.session.execute(update(RoleplayPrefetch.__table__).where(
            RoleplayPrefetch.__table__.c.id == row_id).values(status='stale'))
        db.session.commit()
        return
    _finish(row_id, result.data, result.usage)
    logger.info('Rollenspiel-Prefetch %s: fertig in %.1fs', row_id, time.monotonic() - started)


def _session_job(app, sync: bool, row_id: int) -> None:
    with _job_context(app, sync):
        def compute(row: RoleplayPrefetch) -> svc.TurnResult | None:
            session = db.session.get(RoleplaySession, row.session_id)
            if session is None or session.status != 'active' or (session.turn_count or 0) != row.turn_index:
                return None
            system, status, messages, last, _after = svc.prepare_turn(session, row.user_text)
            return svc.call_turn(system, status, messages, force_done=last, provider=_provider())
        _run(row_id, compute)


def _demo_job(app, sync: bool, row_id: int, history: list) -> None:
    with _job_context(app, sync):
        from app.services import roleplay_demo as demo

        def compute(row: RoleplayPrefetch) -> svc.TurnResult | None:
            content = demo.demo_content()
            if content is None:
                return None
            return demo.demo_call(content, history, row.user_text, row.turn_index + 1, provider=_provider())
        _run(row_id, compute)


def schedule_session(session: RoleplaySession) -> int:
    """Vorausberechnung fuer die Vorschlaege des letzten Bot-Zugs starten.

    Aufruf NACH dem Commit des Bot-Zugs. Liefert die Zahl geplanter Aufrufe.
    Fehler hier duerfen den Zug nie scheitern lassen.
    """
    try:
        if not enabled() or session.status != 'active':
            return 0
        if (session.turn_count or 0) >= svc.MAX_USER_TURNS:
            return 0
        bot = next((t for t in reversed(session.turns or []) if t.speaker == 'bot'), None)
        suggestions = json.loads(bot.suggestions_json or '[]') if bot is not None else []
        rows = _new_rows(suggestions, session.turn_count or 0, session_id=session.id, demo=None)
        if not rows or not _capacity_ok(len(rows)):
            return 0
        if db.session.get(LessonContent, session.lesson_content_id) is None:
            return 0
        db.session.add_all(rows)
        db.session.commit()
        for row in rows:
            _submit(_session_job, row.id)
        return len(rows)
    except Exception:
        db.session.rollback()
        logger.exception('Rollenspiel-Prefetch: Planen fehlgeschlagen (session=%s)', session.id)
        return 0


def schedule_demo(token: str, turn_index: int, history: list, suggestions: list[dict[str, Any]]) -> int:
    """Wie schedule_session, fuer die Gast-Demo (Schluessel = Token-Hash)."""
    try:
        if not enabled() or not token:
            return 0
        rows = _new_rows(suggestions, turn_index, session_id=None, demo=demo_key(token))
        if not rows or not _capacity_ok(len(rows)):
            return 0
        db.session.add_all(rows)
        db.session.commit()
        snapshot = json.loads(json.dumps(history))
        for row in rows:
            _submit(_demo_job, row.id, snapshot)
        return len(rows)
    except Exception:
        db.session.rollback()
        logger.exception('Rollenspiel-Prefetch: Planen (Demo) fehlgeschlagen')
        return 0


# ── Zweiter Aufruf: Lernhilfen zur schon gesendeten Bot-Zeile ────────────

def _details_row(turn_index: int, *, session_id: int | None, demo: str | None) -> RoleplayPrefetch:
    return RoleplayPrefetch(session_id=session_id, demo_key=demo, turn_index=turn_index,
                            user_text='', norm_text=DETAILS_MARK, status='pending',
                            created_at=datetime.utcnow())


def _details_provider() -> svc.RoleplayProvider:
    # 'high': der Nutzer wartet auf die Vorschlaege (nicht hinter Vorausberechnungen).
    return svc.get_provider()


def schedule_details_session(session: RoleplaySession, bot_turn: Any) -> bool:
    """Zweiten Aufruf fuer `bot_turn` planen (NACH dem Commit des Zugs). Scheitert das
    Planen, gilt der Zug als ohne Vorschlaege (Freitext bleibt moeglich)."""
    try:
        row = _details_row(session.turn_count or 0, session_id=session.id, demo=None)
        db.session.add(row)
        db.session.commit()
        _submit(_details_session_job, row.id, bot_turn.id, details=True)
        return True
    except Exception:
        db.session.rollback()
        logger.exception('Rollenspiel-Details: Planen fehlgeschlagen (session=%s)', session.id)
        try:
            svc.apply_details(session, bot_turn, None)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return False


def _details_session_job(app, sync: bool, row_id: int, turn_id: int) -> None:
    from app.models import RoleplayTurn
    with _job_context(app, sync):
        row = db.session.get(RoleplayPrefetch, row_id)
        if row is None or row.status != 'pending':
            return
        turn = db.session.get(RoleplayTurn, turn_id)
        session = db.session.get(RoleplaySession, row.session_id)
        if (turn is None or session is None or turn.suggestions_json is not None
                or not session.turns or session.turns[-1].id != turn.id):
            # Nutzer ist schon weiter (oder Zug weg): Details lohnen nicht mehr.
            db.session.execute(update(RoleplayPrefetch.__table__).where(
                RoleplayPrefetch.__table__.c.id == row_id).values(status='stale'))
            db.session.commit()
            return
        started = time.monotonic()
        data: dict[str, Any] | None = None
        usage = svc.Usage()
        try:
            system, status, messages = svc.prepare_details(session, turn)
            result = svc.call_details(system, status, messages, turn.text_jp, done=False,
                                      provider=_details_provider())
            data, usage = result.data, result.usage
        except svc.UpstreamError as exc:
            usage = exc.usage
            logger.info('Rollenspiel-Details %s: Upstream-Fehler', row_id)
        except Exception:
            db.session.rollback()
            logger.exception('Rollenspiel-Details %s: Fehler', row_id)
            turn = db.session.get(RoleplayTurn, turn_id)
            session = db.session.get(RoleplaySession, row.session_id)
            if turn is None or session is None:
                return
        svc.apply_details(session, turn, data, usage)
        _finish(row_id, data, usage, keep_text=False)   # committet (Texte stehen im Bot-Zug)
        logger.info('Rollenspiel-Details %s: %s in %.1fs', row_id, 'fertig' if data else 'gescheitert',
                    time.monotonic() - started)
        if data is not None:
            schedule_session(session)


def schedule_details_demo(token: str, turn_index: int, history: list, bot_line_jp: str,
                          prefetch_after: bool) -> bool:
    """Wie schedule_details_session fuer die Gast-Demo (Schluessel = Hash des neuen Tokens).
    `history` endet mit der Bot-Zeile."""
    try:
        row = _details_row(turn_index, session_id=None, demo=demo_key(token))
        db.session.add(row)
        db.session.commit()
        snapshot = json.loads(json.dumps(history))
        _submit(_details_demo_job, row.id, token, snapshot, bot_line_jp, prefetch_after, details=True)
        return True
    except Exception:
        db.session.rollback()
        logger.exception('Rollenspiel-Details: Planen (Demo) fehlgeschlagen')
        return False


def _details_demo_job(app, sync: bool, row_id: int, token: str, history: list, bot_line_jp: str,
                      prefetch_after: bool) -> None:
    with _job_context(app, sync):
        from app.services import roleplay_demo as demo

        row = db.session.get(RoleplayPrefetch, row_id)
        if row is None or row.status != 'pending':
            return
        data: dict[str, Any] | None = None
        usage = svc.Usage()
        try:
            content = demo.demo_content()
            if content is not None:
                result = demo.demo_details_call(content, history, bot_line_jp, row.turn_index,
                                                provider=_details_provider())
                data, usage = result.data, result.usage
        except svc.UpstreamError as exc:
            usage = exc.usage
            logger.info('Rollenspiel-Details (Demo) %s: Upstream-Fehler', row_id)
        except Exception:
            db.session.rollback()
            logger.exception('Rollenspiel-Details (Demo) %s: Fehler', row_id)
        _finish(row_id, data, usage)
        if data is not None and prefetch_after:
            schedule_demo(token, row.turn_index, history, data['suggestions'])


def details_for_demo(token: str, turn_index: int) -> tuple[str, dict[str, Any] | None]:
    """('ready'|'pending'|'failed', Zugdaten) der Details zu diesem Demo-Token."""
    row = RoleplayPrefetch.query.filter(
        RoleplayPrefetch.session_id.is_(None), RoleplayPrefetch.demo_key == demo_key(token),
        RoleplayPrefetch.turn_index == turn_index, RoleplayPrefetch.norm_text == DETAILS_MARK,
    ).order_by(RoleplayPrefetch.id.desc()).first()
    if row is None:
        return 'failed', None
    if row.status == 'pending':
        fresh = row.created_at and row.created_at > datetime.utcnow() - timedelta(seconds=svc.DETAILS_STALE_S)
        return ('pending' if fresh else 'failed'), None
    if row.status == 'ready' and row.response_json:
        try:
            data = json.loads(row.response_json)
        except (TypeError, ValueError):
            return 'failed', None
        return ('ready', data) if isinstance(data, dict) else ('failed', None)
    return 'failed', None

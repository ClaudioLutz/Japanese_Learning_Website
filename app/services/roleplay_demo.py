"""Gast-Demo des Rollenspiels (Startseite, ohne Login).

Eine feste Szene („Im Café", Dialog der Gast-Lektion „Alltag & Essen 2"),
feste Rolle (Lernender = Lisa, Bot = Tanaka), hoechstens DEMO_MAX_USER_TURNS
Nutzerzuege, danach Abschluss mit Korrektur.

Datenschutz/Kosten:
- KEIN Schreiben von Gespraechstexten: der Gespraechszustand (Zughistorie)
  reist als signiertes, 30 Minuten gueltiges Token (itsdangerous) mit dem
  Client hin und her. Keine Mitschnitte, keine Rohtexte in Logs.
- Einziger DB-Zugriff schreibend: Tageszaehler guest_demo_counter
  (gehashte IP, pro Worker konsistent) — Limit pro IP und globale Gast-Kappe.
- Die Eroeffnungszeile ist statisch (kein Modell-Aufruf beim Start); nur
  Nutzerzuege kosten einen Modell-Aufruf und zaehlen gegen die Limits.
- Provider + Prompt aus roleplay_service (ohne Nutzerkontext).
- Antworten auf die drei Vorschlaege rechnet der Server vor
  (roleplay_prefetch, Schluessel = Token-Hash); ein gewaehlter Vorschlag kommt
  ohne Modell-Aufruf, zaehlt aber normal gegen IP-Limit und Gast-Kappe.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import GuestDemoCounter, Lesson, LessonContent
from app.services import roleplay_prefetch as prefetch
from app.services import roleplay_service as svc
from app.time_utils import ch_today

logger = logging.getLogger(__name__)

# ── Szene ────────────────────────────────────────────────────────────────

# LessonContent.id des Dialogs (Prod: Lektion 157 „N5 Alltag & Essen 2 — Was
# möchtest du essen?", Gast-Lektion). Per Env/Config ROLEPLAY_DEMO_CONTENT_ID
# ueberschreibbar; der Dialog muss die Sprecher DEMO_ROLE_USER + DEMO_ROLE_BOT haben.
DEMO_CONTENT_ID_DEFAULT = 6563
DEMO_ROLE_USER = 'Lisa'
DEMO_ROLE_BOT = 'Tanaka'
DEMO_TITLE = 'Im Café'
DEMO_SCENE_DE = (
    'Szene: Im Café. Lisa und ihr Freund Tanaka sitzen im Café und überlegen, '
    'was sie trinken und essen möchten.'
)
DEMO_GOAL = 'Sag Tanaka, was du im Café trinken und essen möchtest.'

DEMO_MAX_USER_TURNS = 3
DEMO_TEXT_MAX = 200
TOKEN_MAX_AGE_S = 30 * 60
TOKEN_SALT = 'roleplay-guest-demo-v1'

IP_DAILY_LIMIT = 9                 # Gast-Zuege pro IP und CH-Tag
GUEST_DAILY_CAP_DEFAULT = 100      # Gast-Zuege aller Gaeste pro CH-Tag
GLOBAL_KEY = '*'

CAP_MESSAGE = 'Demo für heute ausgeschöpft, mit Konto geht es weiter.'

# Statische Eroeffnung (von Claude verfasst, N5): Tanakas erste Dialogzeile.
DEMO_OPENING: dict[str, Any] = {
    'jp': 'リサさん、なにが のみたいですか？',
    'reading_kana': 'リサさん、なにが のみたいですか？',
    'de': 'Lisa, was möchtest du trinken?',
    'hint_de': 'Nenne ein Getränk: „… が のみたいです“.',
    'suggestions': [
        {'jp': 'こうちゃが のみたいです。', 'de': 'Ich möchte Schwarztee trinken.'},
        {'jp': 'わたしは コーヒーが いいです。', 'de': 'Ich nehme gern einen Kaffee.'},
        {'jp': 'つめたい みずが のみたいです。', 'de': 'Ich möchte kaltes Wasser trinken.'},
    ],
}


class DemoError(svc.RoleplayError):
    code = 'invalid_request'
    http_status = 400


def _setting(name: str) -> str:
    val = current_app.config.get(name)
    if val is None:
        val = os.environ.get(name)
    return str(val).strip() if val is not None else ''


def demo_content_id() -> int:
    raw = _setting('ROLEPLAY_DEMO_CONTENT_ID')
    try:
        return int(raw) if raw else DEMO_CONTENT_ID_DEFAULT
    except ValueError:
        return DEMO_CONTENT_ID_DEFAULT


def guest_daily_cap() -> int:
    raw = _setting('ROLEPLAY_GUEST_DAILY_CAP')
    try:
        return int(raw) if raw else GUEST_DAILY_CAP_DEFAULT
    except ValueError:
        return GUEST_DAILY_CAP_DEFAULT


def demo_content() -> LessonContent | None:
    """Dialog der Demo — nur wenn publiziert, gastzugaenglich und mit beiden Rollen."""
    content = db.session.get(LessonContent, demo_content_id())
    if content is None or content.content_type != 'dialog_slideshow':
        return None
    lesson = db.session.get(Lesson, content.lesson_id)
    if lesson is None or not lesson.is_published or not lesson.allow_guest_access:
        return None
    speakers = {ln['speaker'] for ln in svc.parse_slides(content)}
    if not {DEMO_ROLE_USER, DEMO_ROLE_BOT} <= speakers:
        return None
    return content


def demo_scene(content: LessonContent) -> dict[str, Any]:
    scene = svc.build_scene(content)
    scene['title'] = DEMO_TITLE
    scene['scene_de'] = DEMO_SCENE_DE
    return scene


def scene_count() -> int:
    """Anzahl Dialogszenen (dialog_slideshow) publizierter Lektionen."""
    return (
        LessonContent.query.join(Lesson, Lesson.id == LessonContent.lesson_id)
        .filter(LessonContent.content_type == 'dialog_slideshow', Lesson.is_published.is_(True))
        .count()
    )


def hero_context() -> dict[str, Any] | None:
    """Daten fuer den Gast-Hero der Startseite (None = Demo nicht verfuegbar)."""
    content = demo_content()
    if content is None:
        return None
    return {
        'title': DEMO_TITLE,
        'role_user': DEMO_ROLE_USER,
        'role_bot': DEMO_ROLE_BOT,
        'max_user_turns': DEMO_MAX_USER_TURNS,
        'text_max': DEMO_TEXT_MAX,
    }


def _session_dict(user_turns: int, done: bool = False) -> dict[str, Any]:
    return {
        'id': None,
        'demo': True,
        'status': 'completed' if done else 'active',
        'role_user': DEMO_ROLE_USER,
        'role_bot': DEMO_ROLE_BOT,
        'goal_de': DEMO_GOAL,
        'turn_count': user_turns,
        'min_user_turns': DEMO_MAX_USER_TURNS,
        'max_user_turns': DEMO_MAX_USER_TURNS,
        'xp_awarded': 0,
    }


def _roles(scene: dict[str, Any]) -> list[dict[str, Any]]:
    return [{'name': r['name'], 'gender': r['gender']} for r in scene['roles']]


# ── Token ────────────────────────────────────────────────────────────────

def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.secret_key, salt=TOKEN_SALT)


def issue_token(state: dict[str, Any]) -> str:
    return _serializer().dumps(state)


def read_token(token: Any, max_age: int = TOKEN_MAX_AGE_S) -> dict[str, Any]:
    """Token → Zustand. Abgelaufen/ungueltig → DemoError (400)."""
    if not isinstance(token, str) or not token or len(token) > 20000:
        raise DemoError('Die Demo ist nicht mehr gültig. Bitte starte sie neu.', code='demo_invalid')
    try:
        state = _serializer().loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise DemoError('Die Demo ist abgelaufen (30 Minuten). Bitte starte sie neu.',
                        code='demo_expired') from exc
    except BadSignature as exc:
        raise DemoError('Die Demo ist nicht mehr gültig. Bitte starte sie neu.', code='demo_invalid') from exc
    if (not isinstance(state, dict) or state.get('v') != 1 or not isinstance(state.get('h'), list)
            or not isinstance(state.get('n'), int) or state.get('c') != demo_content_id()):
        raise DemoError('Die Demo ist nicht mehr gültig. Bitte starte sie neu.', code='demo_invalid')
    return state


# ── Zaehler (DB, ueber alle Worker konsistent) ───────────────────────────

def ip_hash(ip: str) -> str:
    """Gehashte IP (mit App-Secret gesalzen) — die Roh-IP wird nie gespeichert."""
    secret = str(current_app.secret_key or '')
    return hashlib.sha256(f'{secret}|{ip}'.encode()).hexdigest()[:32]


def _reserve(key: str, limit: int) -> bool:
    """Zaehler (heute, key) atomar um 1 erhoehen, falls < limit. True = reserviert."""
    if limit <= 0:
        return False
    tbl = GuestDemoCounter.__table__
    day = ch_today()
    for _ in range(2):
        res = db.session.execute(
            update(tbl)
            .where(tbl.c.day == day, tbl.c.ip_hash == key, tbl.c.count < limit)
            .values(count=tbl.c.count + 1)
        )
        if res.rowcount == 1:  # type: ignore[attr-defined]
            db.session.commit()
            return True
        exists = db.session.execute(
            select(tbl.c.count).where(tbl.c.day == day, tbl.c.ip_hash == key)
        ).first()
        if exists is not None:
            db.session.rollback()
            return False
        try:
            db.session.execute(insert(tbl).values(day=day, ip_hash=key, count=1))
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()   # parallel angelegt → nochmal per UPDATE
    return False


def _release(key: str) -> None:
    tbl = GuestDemoCounter.__table__
    db.session.execute(
        update(tbl)
        .where(tbl.c.day == ch_today(), tbl.c.ip_hash == key, tbl.c.count > 0)
        .values(count=tbl.c.count - 1)
    )
    db.session.commit()


def count_for(key: str) -> int:
    row = db.session.get(GuestDemoCounter, (ch_today(), key))
    return int(row.count) if row else 0


def reserve_turn(ip: str) -> str:
    """Einen Gast-Zug reservieren (IP-Limit + globale Gast-Kappe). Liefert den IP-Key."""
    key = ip_hash(ip)
    if not _reserve(key, IP_DAILY_LIMIT):
        raise svc.LimitReached(CAP_MESSAGE)
    if not _reserve(GLOBAL_KEY, guest_daily_cap()):
        _release(key)
        raise svc.CostCapReached(CAP_MESSAGE)
    return key


def release_turn(key: str) -> None:
    _release(key)
    _release(GLOBAL_KEY)


# ── Ablauf ───────────────────────────────────────────────────────────────

def _opening_turn() -> dict[str, Any]:
    return {'turn_index': 0, 'speaker': 'bot', **json.loads(json.dumps(DEMO_OPENING))}


def _guest_has_turns(ip: str | None) -> bool:
    """Hat dieser Gast (und die Gast-Kappe) heute noch Zuege? Sonst lohnt Vorausrechnen nicht."""
    if ip is None:
        return True
    return count_for(ip_hash(ip)) < IP_DAILY_LIMIT and count_for(GLOBAL_KEY) < guest_daily_cap()


def start_demo(ip: str | None = None) -> dict[str, Any]:
    """Demo starten: statische Eroeffnung, kein Modell-Aufruf fuer den Start, kein Zaehler.
    Die Antworten auf die drei Eroeffnungs-Vorschlaege werden vorausberechnet."""
    content = demo_content()
    if content is None:
        raise svc.RoleplayError('Die Demo ist gerade nicht verfügbar.', code='not_found', http_status=404)
    scene = demo_scene(content)
    state = {'v': 1, 'c': content.id, 'n': 0, 'h': [['b', DEMO_OPENING['jp']]]}
    token = issue_token(state)
    if prefetch.enabled() and _guest_has_turns(ip):
        prefetch.cleanup_old()
        prefetch.schedule_demo(token, 0, state['h'], DEMO_OPENING['suggestions'])
    return {
        'token': token,
        'session': _session_dict(0),
        'bot_turn': _opening_turn(),
        'scene': {'title': DEMO_TITLE, 'scene_de': DEMO_SCENE_DE, 'roles': _roles(scene)},
    }


def build_demo_messages(history: list, new_user_text: str) -> list[dict[str, Any]]:
    """Verlauf aus dem Token → Messages. Nutzertexte NUR als user-Turns."""
    messages: list[dict[str, Any]] = [{'role': 'user', 'content': svc.OPENING_USER_TEXT}]
    for item in history:
        if not (isinstance(item, list) and len(item) == 2 and isinstance(item[1], str)):
            raise DemoError('Die Demo ist nicht mehr gültig. Bitte starte sie neu.', code='demo_invalid')
        messages.append({'role': 'assistant' if item[0] == 'b' else 'user', 'content': item[1]})
    messages.append({'role': 'user', 'content': new_user_text})
    return messages


def demo_call(content: LessonContent, history: list, text: str, user_turns_after: int,
              provider: svc.RoleplayProvider | None = None) -> svc.TurnResult:
    """Ein Modell-Zug der Demo (Live-Zug und Vorausberechnung)."""
    messages = build_demo_messages(history, text)
    last = user_turns_after >= DEMO_MAX_USER_TURNS
    scene = demo_scene(content)
    lesson = db.session.get(Lesson, content.lesson_id)
    system = svc.build_system_prompt(
        scene, DEMO_ROLE_USER, DEMO_ROLE_BOT, DEMO_GOAL,
        svc.vocab_pool(lesson) if lesson else [], svc.n5_kanji(),
        min_turns=DEMO_MAX_USER_TURNS, max_turns=DEMO_MAX_USER_TURNS,
    )
    return svc.call_turn(
        system, svc._status_block('turn', user_turns_after, max_turns=DEMO_MAX_USER_TURNS),
        messages, force_done=last, provider=provider,
    )


def demo_turn(token: Any, text: Any, ip: str,
              provider: svc.RoleplayProvider | None = None) -> dict[str, Any]:
    state = read_token(token)
    if state.get('done') or state['n'] >= DEMO_MAX_USER_TURNS:
        raise svc.RoleplayError('Die Demo ist schon beendet.', code='session_finished', http_status=409)
    if not isinstance(text, str) or not text.strip():
        raise DemoError('Bitte schreib zuerst etwas.')
    text = text.strip()
    if len(text) > DEMO_TEXT_MAX:
        raise DemoError(f'Bitte höchstens {DEMO_TEXT_MAX} Zeichen pro Nachricht.')
    content = demo_content()
    if content is None:
        raise svc.RoleplayError('Die Demo ist gerade nicht verfügbar.', code='not_found', http_status=404)

    build_demo_messages(state['h'], text)   # prueft die Historie im Token
    dkey = prefetch.demo_key(token)
    user_turns_after = state['n'] + 1
    last = user_turns_after >= DEMO_MAX_USER_TURNS
    key = reserve_turn(ip)
    data = prefetch.take(demo=dkey, turn_index=state['n'], text=text)
    if data is None:
        try:
            svc.check_cost_cap()
        except svc.CostCapReached as exc:
            release_turn(key)
            raise svc.CostCapReached(CAP_MESSAGE) from exc
        try:
            data = demo_call(content, state['h'], text, user_turns_after, provider=provider).data
        except svc.UpstreamError:
            release_turn(key)   # Fehlversuch zaehlt nicht
            raise
    prefetch.consume(demo=dkey, turn_index=state['n'])
    db.session.commit()
    if data['done'] and not last:
        # Zu frueh beendet: Demo laeuft bis zum letzten Zug weiter.
        data['done'] = False
        data['correction'] = []
    done = bool(data['done'])
    logger.info('Gast-Demo: Zug %d/%d (ip=%s…)', user_turns_after, DEMO_MAX_USER_TURNS, key[:8])

    new_token = None
    if not done:
        new_state = {
            'v': 1, 'c': state['c'], 'n': user_turns_after,
            'h': state['h'] + [['u', text], ['b', data['bot_line_jp']]],
        }
        new_token = issue_token(new_state)
        if user_turns_after < DEMO_MAX_USER_TURNS:
            prefetch.schedule_demo(new_token, user_turns_after, new_state['h'], data['suggestions'])
    return {
        'token': new_token,
        'session': _session_dict(user_turns_after, done=done),
        'bot_turn': {
            'turn_index': len(state['h']) + 1,
            'speaker': 'bot',
            'jp': data['bot_line_jp'],
            'reading_kana': data['reading_kana'],
            'de': data['de'],
            'suggestions': data['suggestions'],
            'hint_de': data['hint_de'],
        },
        'done': done,
        'correction': data['correction'] if done else [],
        'xp_awarded': 0,
    }

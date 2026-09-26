"""Uebersichten rund um den Rollenspiel-Tutor (SSR-Seiten + Dashboard).

- /sprechen: alle Dialogszenen (dialog_slideshow publizierter, zugaenglicher
  Lektionen) gruppiert nach Modul, mit Zustand „bereit" (Lektion abgeschlossen)
  oder „noch nicht gelernt".
- /sprechen/verlauf: eigene Gespraeche (RoleplaySession), neueste zuerst.
- /mein-lernen: Kachel „Heute sprechen" (Szenen-Vorschlag) + drei Kennzahlen.

Reine Lese-Logik ohne Modell-Aufrufe. Die Auswahl des Vorschlags steckt in
der reinen Funktion pick_suggestion() (Unit-testbar ohne DB).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from flask import current_app

from app import db
from app.models import (
    AccessContext, Lesson, LessonCategory, LessonContent, RoleplaySession, UserLessonProgress,
)
from app.services import roleplay_service as svc

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 50
STATS_LAST_N = 5
OTHER_MODULE = 'Weitere Lektionen'
_UTC = ZoneInfo('UTC')
_CH = ZoneInfo('Europe/Zurich')
_MONTHS_DE = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
              'August', 'September', 'Oktober', 'November', 'Dezember']
STATUS_LABEL = {'completed': 'abgeschlossen', 'abandoned': 'vorzeitig beendet', 'active': 'nicht beendet'}


def ch_label(dt: datetime | None) -> str:
    """UTC-naive DB-Zeit → „26. September 2026, 14:05“ (Schweizer Zeit)."""
    if dt is None:
        return ''
    local = dt.replace(tzinfo=_UTC).astimezone(_CH)
    return f'{local.day}. {_MONTHS_DE[local.month]} {local.year}, {local:%H:%M}'


def _first_slide_image(content: LessonContent) -> str | None:
    try:
        data = json.loads(content.content_text or '')
    except (TypeError, ValueError):
        return None
    slides = data.get('slides') if isinstance(data, dict) else data
    if not isinstance(slides, list):
        return None
    for s in slides:
        if isinstance(s, dict) and isinstance(s.get('image'), str) and s['image'].strip():
            return s['image'].strip()
    return None


def _lesson_image(lesson: Lesson) -> str | None:
    try:
        return lesson.get_thumbnail_url() or None
    except Exception:  # noqa: BLE001 — Bild ist Deko, darf die Seite nie brechen
        return None


def _module_sort_key(cat: LessonCategory | None) -> tuple:
    if cat is None:
        return (1, 0, 0, 0)
    # N5 zuerst (hoehere Zahl = leichter), dann Modulreihenfolge.
    return (0, -(cat.jlpt_level or 0), cat.display_order or 0, cat.id)


def list_scenes(user) -> list[dict[str, Any]]:
    """Alle spielbaren Dialogszenen fuer `user`, in Modul- und Lektionsreihenfolge.

    Nur publizierte Lektionen in den sichtbaren Inhaltssprachen, auf die der
    Nutzer Zugang hat, und nur Dialoge mit zwei Rollen (build_scene).
    """
    langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])
    rows = (
        db.session.query(LessonContent, Lesson)
        .join(Lesson, LessonContent.lesson_id == Lesson.id)
        .filter(
            LessonContent.content_type == 'dialog_slideshow',
            Lesson.is_published.is_(True),
            Lesson.instruction_language.in_(langs),
        )
        .all()
    )
    if not rows:
        return []
    lessons = {lesson.id: lesson for _, lesson in rows}
    ctx = AccessContext.build_for_user(user, lessons.values())
    completed = dict(
        db.session.query(UserLessonProgress.lesson_id, UserLessonProgress.completed_at)
        .filter(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id.in_(list(lessons)),
            UserLessonProgress.is_completed.is_(True),
        )
        .all()
    )
    access_ok: dict[int, bool] = {}
    scenes: list[dict[str, Any]] = []
    for content, lesson in rows:
        if lesson.id not in access_ok:
            access_ok[lesson.id] = lesson.access_check(user, ctx).accessible
        if not access_ok[lesson.id]:
            continue
        try:
            scene = svc.build_scene(content)
        except svc.RoleplayError:
            continue
        cat = lesson.category
        roles = scene['roles']
        goal_role = roles[1]['name'] if len(roles) > 1 else roles[0]['name']
        scenes.append({
            'content_id': content.id,
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'title': scene['title'] or lesson.title,
            'roles': [{'name': r['name'], 'gender': r.get('gender')} for r in roles],
            'goal_de': scene['goal_suggestions'].get(goal_role, ''),
            'scene_de': scene['scene_de'],
            'image': _first_slide_image(content) or _lesson_image(lesson),
            'ready': lesson.id in completed,
            'completed_at': completed.get(lesson.id),
            'module_id': cat.id if cat else None,
            'module_name': cat.name if cat else OTHER_MODULE,
            '_sort': (_module_sort_key(cat), lesson.order_index or 0, lesson.id,
                      content.page_number or 0, content.order_index or 0, content.id),
        })
    scenes.sort(key=lambda s: s['_sort'])
    for s in scenes:
        s.pop('_sort', None)
    return scenes


def group_by_module(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """[{module_id, name, scenes, ready_count}] in der Reihenfolge der Szenen."""
    groups: list[dict[str, Any]] = []
    index: dict[Any, dict[str, Any]] = {}
    for s in scenes:
        key = s['module_id']
        if key not in index:
            index[key] = {'module_id': key, 'name': s['module_name'], 'scenes': [], 'ready_count': 0}
            groups.append(index[key])
        index[key]['scenes'].append(s)
        if s['ready']:
            index[key]['ready_count'] += 1
    return groups


# ── Verlauf ──────────────────────────────────────────────────────────────

def _played_sessions_query(user_id: int):
    return RoleplaySession.query.filter(
        RoleplaySession.user_id == user_id,
        RoleplaySession.turn_count >= 1,
    )


def history(user_id: int, limit: int = HISTORY_LIMIT) -> list[dict[str, Any]]:
    """Eigene Gespraeche mit mind. einem Nutzerzug, neueste zuerst."""
    sessions = (
        _played_sessions_query(user_id)
        .order_by(RoleplaySession.started_at.desc(), RoleplaySession.id.desc())
        .limit(limit)
        .all()
    )
    content_ids = {s.lesson_content_id for s in sessions}
    titles: dict[int, str] = {}
    if content_ids:
        for cid, title in (
            db.session.query(LessonContent.id, Lesson.title)
            .join(Lesson, LessonContent.lesson_id == Lesson.id)
            .filter(LessonContent.id.in_(content_ids))
            .all()
        ):
            titles[cid] = title
    return [{
        'id': s.id,
        'content_id': s.lesson_content_id,
        'lesson_title': titles.get(s.lesson_content_id, 'Dialog'),
        'role_user': s.role_user,
        'role_bot': s.role_bot,
        'started_at': s.started_at,
        'started_label': ch_label(s.started_at),
        'status': s.status,
        'status_label': STATUS_LABEL.get(s.status, s.status),
        'turns': s.turn_count or 0,
        'xp': s.xp_awarded or 0,
        'corrections': svc.correction_count(s),
    } for s in sessions]


def session_detail(session: RoleplaySession) -> dict[str, Any]:
    """Ganzer Gespraechsverlauf + Korrekturen fuer die Detailansicht."""
    content = db.session.get(LessonContent, session.lesson_content_id)
    lesson = db.session.get(Lesson, content.lesson_id) if content else None
    lines = []
    for t in session.turns:
        if t.speaker == 'bot':
            lines.append({'who': 'bot', 'name': session.role_bot, 'jp': t.text_jp or '',
                          'reading': t.reading_kana or '', 'de': t.text_de or ''})
        else:
            lines.append({'who': 'user', 'name': session.role_user, 'jp': t.text_jp or '',
                          'reading': '', 'de': ''})
    corrections = svc.session_corrections(session)
    return {
        'id': session.id,
        'content_id': session.lesson_content_id,
        'lesson_id': lesson.id if lesson else None,
        'lesson_title': lesson.title if lesson else 'Dialog',
        'role_user': session.role_user,
        'role_bot': session.role_bot,
        'goal_de': session.goal_de,
        'status': session.status,
        'status_label': STATUS_LABEL.get(session.status, session.status),
        'started_at': session.started_at,
        'started_label': ch_label(session.started_at),
        'turns': session.turn_count or 0,
        'xp': session.xp_awarded or 0,
        'lines': lines,
        'corrections': [dict(c, praise=svc.is_praise(c)) for c in corrections],
        'correction_count': sum(1 for c in corrections if not svc.is_praise(c)),
    }


# ── Dashboard: Vorschlag + Kennzahlen ────────────────────────────────────

def pick_suggestion(
    scenes: list[dict[str, Any]],
    played_content_ids: set[int],
    last_corrections: dict[int, int],
) -> dict[str, Any]:
    """Waehlt die Szene fuer „Heute sprechen" (rein, ohne DB).

    Reihenfolge:
    1. bereite Szene der zuletzt abgeschlossenen Lektion ohne gespieltes Gespraech
       (neueste Abschluesse zuerst),
    2. sonst die bereite Szene mit den meisten Korrekturen beim letzten Mal (> 0),
    3. sonst die erste bereite Szene (Modulreihenfolge),
    4. ohne bereite Szene: Hinweis auf die erste Lektion mit Dialog (kind='none').
    `scenes` in Modulreihenfolge (wie list_scenes).
    """
    ready = [s for s in scenes if s.get('ready')]
    if not ready:
        return {'kind': 'none', 'scene': scenes[0] if scenes else None}

    fresh = [s for s in ready if s['content_id'] not in played_content_ids]
    if fresh:
        # Stabil sortieren: neuester Abschluss zuerst, sonst Modulreihenfolge.
        order = {s['content_id']: i for i, s in enumerate(ready)}
        def _key(s: dict[str, Any]) -> tuple:
            done_at = s.get('completed_at')
            return ((0, -done_at.timestamp()) if isinstance(done_at, datetime) else (1, 0.0),
                    order[s['content_id']])
        fresh.sort(key=_key)
        return {'kind': 'new', 'scene': fresh[0]}

    retry = [s for s in ready if last_corrections.get(s['content_id'], 0) > 0]
    if retry:
        best = max(retry, key=lambda s: last_corrections[s['content_id']])
        return {'kind': 'retry', 'scene': best, 'corrections': last_corrections[best['content_id']]}

    return {'kind': 'ready', 'scene': ready[0]}


def _last_finished_by_content(user_id: int) -> list[RoleplaySession]:
    return (
        _played_sessions_query(user_id)
        .filter(RoleplaySession.status != 'active')
        .order_by(RoleplaySession.started_at.desc(), RoleplaySession.id.desc())
        .all()
    )


def speaking_tile(user) -> dict[str, Any]:
    """Daten der Kachel „Heute sprechen"."""
    scenes = list_scenes(user)
    played = {
        cid for (cid,) in db.session.query(RoleplaySession.lesson_content_id)
        .filter(RoleplaySession.user_id == user.id, RoleplaySession.turn_count >= 1)
        .distinct().all()
    }
    last_corr: dict[int, int] = {}
    for s in _last_finished_by_content(user.id):
        if s.lesson_content_id not in last_corr:
            last_corr[s.lesson_content_id] = svc.correction_count(s)
    return pick_suggestion(scenes, played, last_corr)


def speaking_stats(user_id: int) -> dict[str, Any]:
    """Gespraeche, Zuege, Korrekturen pro Gespraech (Mittel der letzten 5 beendeten)."""
    played = _played_sessions_query(user_id)
    conversations = played.count()
    turns = (
        db.session.query(db.func.coalesce(db.func.sum(RoleplaySession.turn_count), 0))
        .filter(RoleplaySession.user_id == user_id, RoleplaySession.turn_count >= 1)
        .scalar()
    ) or 0
    recent = _last_finished_by_content(user_id)[:STATS_LAST_N]
    avg = None
    if recent:
        avg = round(sum(svc.correction_count(s) for s in recent) / len(recent), 1)
    return {'conversations': conversations, 'turns': int(turns),
            'corrections_avg': avg, 'avg_basis': len(recent)}

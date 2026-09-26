"""JSON-APIs fuer den Rollenspiel-Tutor am Lektionsdialog + „Frag zur Seite".

Alle Routen:
- 404, solange ROLEPLAY_ENABLED aus ist oder kein Provider konfiguriert ist
  (before_request, greift auch vor dem Login-Check),
- @login_required, Rate-Limit pro Nutzer,
- CSRF wie die uebrigen JSON-APIs: Header X-CSRFToken (Meta-Tag csrf-token).
Fehler immer als JSON {error, message} mit deutschem Klartext, nie 500.
API-Vertrag: docs/roleplay-api.md.
"""
import logging

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from app import db, limiter
from app.models import Lesson, LessonContent, RoleplaySession
from app.services import roleplay_demo as demo
from app.services import roleplay_service as svc

logger = logging.getLogger(__name__)

roleplay_bp = Blueprint('roleplay', __name__)

RATE_LIMIT = '20 per minute'


def _user_or_ip() -> str:
    if current_user.is_authenticated:
        return f'user:{current_user.id}'
    from app import client_ip
    return client_ip()


@roleplay_bp.before_request
def _feature_gate():
    if not svc.is_enabled():
        abort(404)


def _error(code: str, message: str, status: int):
    return jsonify({'error': code, 'message': message}), status


def _from_exc(exc: svc.RoleplayError):
    return _error(exc.code, exc.message, exc.http_status)


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _lesson_access_error(lesson: Lesson | None):
    """None = Zugriff ok, sonst Fehler-Response."""
    if lesson is None or (not lesson.is_published and not getattr(current_user, 'is_admin', False)):
        return _error('not_found', 'Diese Lektion gibt es nicht.', 404)
    result = lesson.access_check(current_user)
    if not result.accessible:
        return _error('no_access', 'Du hast noch keinen Zugang zu dieser Lektion.', 403)
    return None


def _load_dialog(content_id):
    """(content, error_response)."""
    content = db.session.get(LessonContent, content_id) if content_id else None
    if content is None or content.content_type != 'dialog_slideshow':
        return None, _error('not_found', 'Diesen Dialog gibt es nicht.', 404)
    err = _lesson_access_error(db.session.get(Lesson, content.lesson_id))
    if err is not None:
        return None, err
    return content, None


def _own_session(session_id: int):
    session = db.session.get(RoleplaySession, session_id)
    if session is None or session.user_id != current_user.id:
        return None, _error('not_found', 'Dieses Gespräch gibt es nicht.', 404)
    return session, None


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@roleplay_bp.route('/api/roleplay/scene/<int:content_id>', methods=['GET'])
@login_required
@limiter.limit(RATE_LIMIT, key_func=_user_or_ip)
def scene(content_id):
    content, err = _load_dialog(content_id)
    if err is not None:
        return err
    try:
        data = svc.build_scene(content)
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    data.pop('lines', None)
    data['limits'] = svc.limits_status(current_user.id)
    return jsonify(data)


@roleplay_bp.route('/api/roleplay/start', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMIT, key_func=_user_or_ip)
def start():
    body = _json_body()
    content, err = _load_dialog(_as_int(body.get('content_id')))
    if err is not None:
        return err
    role_user = body.get('role_user')
    goal = body.get('goal')
    if not isinstance(role_user, str) or not role_user.strip():
        return _error('invalid_request', 'Bitte wähle eine Rolle.', 400)
    if goal is not None and not isinstance(goal, str):
        return _error('invalid_request', 'Das Ziel muss ein Text sein.', 400)
    try:
        session, bot_turn = svc.start_session(current_user, content, role_user.strip(), goal)
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    return jsonify({
        'session': svc.serialize_session(session),
        'bot_turn': svc.serialize_bot_turn(bot_turn),
        'limits': svc.limits_status(current_user.id),
    }), 201


@roleplay_bp.route('/api/roleplay/<int:session_id>/turn', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMIT, key_func=_user_or_ip)
def turn(session_id):
    session, err = _own_session(session_id)
    if err is not None:
        return err
    text = _json_body().get('text')
    if not isinstance(text, str):
        return _error('invalid_request', 'Bitte schreib zuerst etwas.', 400)
    try:
        bot_turn, info = svc.user_turn(session, text)
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    return jsonify({
        'session': svc.serialize_session(session),
        'bot_turn': svc.serialize_bot_turn(bot_turn),
        'done': info['done'],
        'correction': info['correction'],
        'xp_awarded': info['xp_awarded'],
        'limits': svc.limits_status(current_user.id),
    })


@roleplay_bp.route('/api/roleplay/<int:session_id>/end', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMIT, key_func=_user_or_ip)
def end(session_id):
    session, err = _own_session(session_id)
    if err is not None:
        return err
    try:
        result = svc.end_session(session)
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    return jsonify({
        'session': svc.serialize_session(session),
        'farewell': result['farewell'],
        'correction': result['correction'],
        'correction_unavailable': result['correction_unavailable'],
        'xp_awarded': result['xp_awarded'],
        'total_xp': current_user.total_xp or 0,
        'level': current_user.level or 1,
    })


@roleplay_bp.route('/api/roleplay/tutor', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMIT, key_func=_user_or_ip)
def tutor():
    body = _json_body()
    lesson_id = _as_int(body.get('lesson_id'))
    page = _as_int(body.get('page'))
    question = body.get('question')
    if lesson_id is None or page is None or not isinstance(question, str):
        return _error('invalid_request', 'Bitte gib Lektion, Seite und Frage an.', 400)
    lesson = db.session.get(Lesson, lesson_id)
    err = _lesson_access_error(lesson)
    if err is not None:
        return err
    if not svc.page_exists(lesson, page):
        return _error('not_found', 'Diese Seite gibt es nicht.', 404)
    try:
        tq = svc.ask_tutor(current_user, lesson, page, question)
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    return jsonify({
        'id': tq.id,
        'lesson_id': lesson.id,
        'page': page,
        'answer': tq.answer,
        'limits': svc.limits_status(current_user.id),
    })


# ── Gast-Demo (Startseite, ohne Login) ───────────────────────────────────
# Feste Szene, max. 3 Nutzerzuege, Zustand als signiertes Token im JSON-Body
# (kein DB-Schreiben ausser dem Tageszaehler). Token bewusst NICHT im Pfad:
# es waechst mit der Zughistorie, Gunicorn begrenzt die Request-Zeile auf 4 KB.
# CSRF wie die uebrigen JSON-APIs (Gaeste haben Session + Meta-Tag csrf-token).
# Details: app/services/roleplay_demo.py, docs/roleplay-api.md.

DEMO_RATE_LIMIT = '6 per minute'


def _client_ip() -> str:
    from app import client_ip
    return client_ip()


def _demo_honeypot(body: dict):
    """Honeypot-Feld `website` (wie /register): ausgefuellt → still ablehnen."""
    if str(body.get('website') or '').strip():
        logger.warning('Honeypot ausgeloest auf Gast-Demo (IP-Hash %s…)',
                       demo.ip_hash(_client_ip())[:8])
        return _error('invalid_request',
                      'Die Demo konnte nicht gestartet werden. Bitte versuche es später erneut.', 400)
    return None


@roleplay_bp.route('/api/roleplay/demo/start', methods=['POST'])
@limiter.limit(DEMO_RATE_LIMIT, key_func=_client_ip)
def demo_start():
    err = _demo_honeypot(_json_body())
    if err is not None:
        return err
    try:
        data = demo.start_demo(_client_ip())
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    return jsonify(data), 201


@roleplay_bp.route('/api/roleplay/demo/turn', methods=['POST'])
@limiter.limit(DEMO_RATE_LIMIT, key_func=_client_ip)
def demo_turn():
    body = _json_body()
    err = _demo_honeypot(body)
    if err is not None:
        return err
    try:
        data = demo.demo_turn(body.get('token'), body.get('text'), _client_ip())
    except svc.RoleplayError as exc:
        return _from_exc(exc)
    return jsonify(data)

"""Seiten „Sprechen" (SSR): Szenenwahl, Rollenspiel ohne Lektionsseite, Verlauf.

- GET /sprechen                      alle Dialogszenen nach Modul
- GET /sprechen/<content_id>         Rollenspiel-Panel direkt (ohne Lektionsseite)
- GET /sprechen/verlauf              eigene Gespraeche, neueste zuerst
- GET /sprechen/verlauf/<session_id> ganzer Verlauf + Korrekturen (fremd → 404)

Wie /api/roleplay/*: 404, solange das Feature aus ist (vor dem Login-Check),
sonst login-pflichtig. Nicht in der Sitemap (privat, noindex).
"""
from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Lesson, LessonContent, RoleplaySession
from app.services import roleplay_overview as overview
from app.services import roleplay_service as svc

sprechen_bp = Blueprint('sprechen', __name__)


@sprechen_bp.before_request
def _feature_gate():
    if not svc.is_enabled():
        abort(404)


@sprechen_bp.route('/sprechen')
@login_required
def index():
    scenes = overview.list_scenes(current_user)
    groups = overview.group_by_module(scenes)
    return render_template(
        'sprechen/index.html',
        groups=groups,
        scene_count=len(scenes),
        ready_count=sum(1 for s in scenes if s['ready']),
        history_count=len(overview.history(current_user.id, limit=1)),
    )


@sprechen_bp.route('/sprechen/<int:content_id>')
@login_required
def play(content_id):
    content = db.session.get(LessonContent, content_id)
    if content is None or content.content_type != 'dialog_slideshow':
        abort(404)
    lesson = db.session.get(Lesson, content.lesson_id)
    if lesson is None or (not lesson.is_published and not getattr(current_user, 'is_admin', False)):
        abort(404)
    if not lesson.access_check(current_user).accessible:
        # Die Lektionsseite erklaert den Grund (Voraussetzung/Kauf) selbst.
        return redirect(url_for('routes.view_lesson', lesson_id=lesson.id))
    try:
        scene = svc.build_scene(content)
    except svc.RoleplayError:
        abort(404)
    ready = any(
        p.user_id == current_user.id and p.is_completed for p in lesson.user_progress
    )
    return render_template(
        'sprechen/play.html',
        content=content,
        lesson=lesson,
        scene=scene,
        ready=ready,
    )


@sprechen_bp.route('/sprechen/verlauf')
@login_required
def history():
    return render_template('sprechen/history.html', sessions=overview.history(current_user.id))


@sprechen_bp.route('/sprechen/verlauf/<int:session_id>')
@login_required
def history_detail(session_id):
    session = db.session.get(RoleplaySession, session_id)
    if session is None or session.user_id != current_user.id:
        abort(404)
    return render_template('sprechen/history_detail.html', s=overview.session_detail(session))

"""Oeffentliches Hinweis-/Feedback-Board ("Issues") fuer japanese-learning.ch.

Content-verankertes Feedback zu Lektionen/Karten. LESEN ist OEFFENTLICH (kein
Login) — bewusst anders als das Forum. SCHREIBEN braucht ein Konto (Spam-
Barriere; Pseudonym erlaubt). Status open/resolved; Maintainer (Admin)
beantwortet, fixt den Inhalt und setzt erledigt — dabei wird der Melder per
Mail benachrichtigt (Konto -> E-Mail vorhanden). Eigenes Blueprint, NICHT
csrf-exempt. Konzept/Entscheidungen: Memory project_forum_gap_analyse.
"""
import logging
from datetime import datetime

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, url_for,
)
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app import db, limiter
from app.forms import ContentIssueForm, IssueCommentForm
from app.mail_service import send_issue_resolved_email, send_new_issue_admin_email
from app.models import (
    ContentIssue, ContentIssueComment, Lesson, LessonContent, User,
)
from app.routes import admin_required

logger = logging.getLogger(__name__)

issue_bp = Blueprint('issues', __name__, url_prefix='/feedback')

ISSUES_PER_PAGE = 20
ALLOWED_CONTENT_TYPES = {'lesson', 'lesson_content'}


def _user_or_ip() -> str:
    """Rate-Limit-Key: an die User-ID binden, wenn eingeloggt (Cloudflare
    kollabiert IPs). Schreiben ist ohnehin login-pflichtig."""
    if current_user.is_authenticated:
        return f'user:{current_user.id}'
    return get_remote_address()


def _resolve_content_ref(content_type, content_id):
    """(label, url) fuer den Rueckverweis auf den verankerten Inhalt — oder
    (None, None), wenn nicht verankert / Ziel nicht (mehr) vorhanden."""
    if not content_type or not content_id:
        return None, None
    if content_type == 'lesson':
        lesson = Lesson.query.get(content_id)
        if lesson:
            return f'Lektion: {lesson.title}', f'/lessons/{lesson.id}'
    elif content_type == 'lesson_content':
        lc = LessonContent.query.get(content_id)
        if lc:
            label = lc.title or (lc.content_type or 'Inhalt')
            return f'Karte/Inhalt: {label}', f'/lessons/{lc.lesson_id}#content-{lc.id}'
    return None, None


def _valid_anchor(content_type, content_id):
    """Verankerung nur uebernehmen, wenn Typ erlaubt UND Ziel existiert —
    sonst (None, None) (wird als generelles Feedback gespeichert)."""
    if content_type not in ALLOWED_CONTENT_TYPES or not content_id:
        return None, None
    _, url = _resolve_content_ref(content_type, content_id)
    if url is None:
        return None, None
    return content_type, content_id


# ── Lesen (oeffentlich) ─────────────────────────────────────────────────────

@issue_bp.route('/')
def index():
    """Oeffentliche Liste der Hinweise (Filter offen/erledigt/alle)."""
    status = request.args.get('status', 'open')
    if status not in ('open', 'resolved', 'all'):
        status = 'open'

    query = (
        ContentIssue.query
        .options(joinedload(ContentIssue.author))
        .filter_by(is_deleted=False)
    )
    if status == 'open':
        query = query.filter_by(status='open')
    elif status == 'resolved':
        query = query.filter_by(status='resolved')

    page = request.args.get('page', 1, type=int)
    pagination = (
        query.order_by(ContentIssue.created_at.desc())
        .paginate(page=page, per_page=ISSUES_PER_PAGE, error_out=False)
    )

    open_count = ContentIssue.query.filter_by(is_deleted=False, status='open').count()
    resolved_count = ContentIssue.query.filter_by(is_deleted=False, status='resolved').count()

    return render_template(
        'issues/index.html',
        pagination=pagination, issues=pagination.items, status=status,
        open_count=open_count, resolved_count=resolved_count,
    )


@issue_bp.route('/<int:issue_id>')
@issue_bp.route('/<int:issue_id>/<slug>')
def view_issue(issue_id, slug=None):
    """Einzelner Hinweis + Antworten (oeffentlich lesbar)."""
    issue = ContentIssue.query.filter_by(id=issue_id, is_deleted=False).first_or_404()
    comments = (
        ContentIssueComment.query
        .options(joinedload(ContentIssueComment.author))
        .filter_by(issue_id=issue.id)
        .order_by(ContentIssueComment.created_at.asc())
        .all()
    )
    content_label, content_url = _resolve_content_ref(issue.content_type, issue.content_id)
    return render_template(
        'issues/issue.html',
        issue=issue, comments=comments,
        content_label=content_label, content_url=content_url,
        form=IssueCommentForm(),
    )


# ── Schreiben (Konto noetig) ────────────────────────────────────────────────

@issue_bp.route('/new', methods=['GET', 'POST'])
@login_required
@limiter.limit('5 per hour', key_func=_user_or_ip, methods=['POST'])
def new_issue():
    """Neuen Hinweis anlegen. Verankerung kommt aus ?content_type&content_id
    (GET) bzw. den Hidden-Feldern (POST) und wird serverseitig validiert."""
    form = ContentIssueForm()
    raw_type = (request.values.get('content_type') or '').strip() or None
    raw_id = request.values.get('content_id', type=int)
    anchor_type, anchor_id = _valid_anchor(raw_type, raw_id)
    anchor_label, _ = _resolve_content_ref(anchor_type, anchor_id)

    if request.method == 'GET' and not form.title.data and anchor_label:
        form.title.data = f'Hinweis zu {anchor_label}'

    if form.validate_on_submit():
        issue = ContentIssue(
            content_type=anchor_type, content_id=anchor_id,
            title=form.title.data.strip(), body=form.body.data,
            author_id=current_user.id, status='open',
            created_at=datetime.utcnow(),
        )
        db.session.add(issue)
        db.session.commit()
        # Team benachrichtigen (best effort) — nur wenn der Melder kein Admin ist.
        if not current_user.is_admin:
            _notify_admins_new_issue(issue)
        flash('Danke! Dein Hinweis ist eingegangen.', 'success')
        return redirect(url_for('issues.view_issue', issue_id=issue.id, slug=issue.build_slug()))

    return render_template(
        'issues/new.html', form=form,
        content_type=anchor_type, content_id=anchor_id, anchor_label=anchor_label,
    )


@issue_bp.route('/<int:issue_id>/comment', methods=['POST'])
@login_required
@limiter.limit('20 per hour', key_func=_user_or_ip)
def comment(issue_id):
    """Antwort/Kommentar zu einem Hinweis (Konto noetig)."""
    issue = ContentIssue.query.filter_by(id=issue_id, is_deleted=False).first_or_404()
    form = IssueCommentForm()
    if form.validate_on_submit():
        c = ContentIssueComment(
            issue_id=issue.id, author_id=current_user.id, body=form.body.data,
            is_maintainer_reply=bool(current_user.is_admin),
            created_at=datetime.utcnow(),
        )
        db.session.add(c)
        db.session.commit()
        flash('Antwort gespeichert.', 'success')
    else:
        for errors in form.errors.values():
            for err in errors:
                flash(err, 'danger')
    return redirect(
        url_for('issues.view_issue', issue_id=issue.id, slug=issue.build_slug()) + '#comments'
    )


# ── Maintainer (Admin) ──────────────────────────────────────────────────────

@issue_bp.route('/<int:issue_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_issue(issue_id):
    """Erledigt/wieder-offen umschalten. Beim Uebergang open->resolved wird der
    Melder benachrichtigt (nur dann, nicht bei jedem Toggle)."""
    issue = ContentIssue.query.filter_by(id=issue_id, is_deleted=False).first_or_404()
    if issue.status != 'resolved':
        issue.status = 'resolved'
        issue.resolved_at = datetime.utcnow()
        issue.resolved_by_id = current_user.id
        db.session.commit()
        _notify_reporter_resolved(issue)  # nur beim Uebergang open->resolved
        flash('Als erledigt markiert. Der Melder wurde benachrichtigt.', 'success')
    else:
        issue.status = 'open'
        issue.resolved_at = None
        issue.resolved_by_id = None
        db.session.commit()
        flash('Hinweis wieder geöffnet.', 'success')
    return redirect(url_for('issues.view_issue', issue_id=issue.id, slug=issue.build_slug()))


@issue_bp.route('/<int:issue_id>/delete', methods=['POST'])
@login_required
def delete_issue(issue_id):
    """Hinweis soft-loeschen (Autor oder Admin)."""
    issue = ContentIssue.query.filter_by(id=issue_id, is_deleted=False).first_or_404()
    if not issue.can_edit(current_user):
        abort(403)
    issue.is_deleted = True
    issue.deleted_at = datetime.utcnow()
    issue.deleted_by_id = current_user.id
    db.session.commit()
    flash('Hinweis gelöscht.', 'success')
    return redirect(url_for('issues.index'))


@issue_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Antwort soft-loeschen (Autor oder Admin)."""
    c = ContentIssueComment.query.filter_by(id=comment_id, is_deleted=False).first_or_404()
    if not c.can_edit(current_user):
        abort(403)
    issue = c.issue
    c.is_deleted = True
    c.deleted_at = datetime.utcnow()
    c.deleted_by_id = current_user.id
    db.session.commit()
    flash('Antwort gelöscht.', 'success')
    return redirect(
        url_for('issues.view_issue', issue_id=issue.id, slug=issue.build_slug()) + '#comments'
    )


# ── Mail-Helfer (best effort, duerfen den Request nie crashen) ──────────────

def _abs_issue_url(issue) -> str:
    try:
        return url_for(
            'issues.view_issue', issue_id=issue.id, slug=issue.build_slug(), _external=True,
        )
    except Exception:
        base = (current_app.config.get('SITE_URL') or '').rstrip('/')
        return f'{base}/feedback/{issue.id}'


def _notify_admins_new_issue(issue):
    try:
        admin_emails = [u.email for u in User.query.filter_by(is_admin=True).all() if u.email]
        label, _ = _resolve_content_ref(issue.content_type, issue.content_id)
        reporter = issue.author.username if issue.author else 'Unbekannt'
        send_new_issue_admin_email(
            admin_emails, issue.title, _abs_issue_url(issue), reporter, label,
        )
    except Exception:
        logger.exception('Admin-Benachrichtigung fuer Issue %s fehlgeschlagen', issue.id)


def _notify_reporter_resolved(issue):
    try:
        reporter = issue.author
        if not reporter or not reporter.email:
            return
        if issue.resolved_by_id and reporter.id == issue.resolved_by_id:
            return  # sich selbst nicht benachrichtigen
        last_reply = (
            ContentIssueComment.query
            .filter_by(issue_id=issue.id, is_maintainer_reply=True, is_deleted=False)
            .order_by(ContentIssueComment.created_at.desc())
            .first()
        )
        send_issue_resolved_email(
            reporter.email, issue.title, _abs_issue_url(issue),
            reply_text=last_reply.body if last_reply else None,
            username=reporter.username,
        )
    except Exception:
        logger.exception('Reporter-Benachrichtigung fuer Issue %s fehlgeschlagen', issue.id)

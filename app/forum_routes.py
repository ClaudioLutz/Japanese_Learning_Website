"""Benutzer-Forum (japanese-learning.ch).

Leichtgewichtiges, login-pflichtiges Forum: Kategorie → Topic → Post. Der erste
Post (is_op) ist der Thread-Body — ein einziger Edit-/Delete-/Render-Pfad.
Soft-Delete ueberall. Eigenes Blueprint (NICHT csrf-exempt), damit routes.py
nicht weiter waechst. Konzept: docs/forum-konzept.md.
"""
import logging
from datetime import datetime

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required
from flask_limiter.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db, limiter
from app.forms import PostForm, TopicForm
from app.models import ForumCategory, ForumPost, ForumTopic
from app.routes import admin_required

logger = logging.getLogger(__name__)

forum_bp = Blueprint('forum', __name__, url_prefix='/forum')

TOPICS_PER_PAGE = 20
POSTS_PER_PAGE = 15


def _user_or_ip() -> str:
    """Rate-Limit-Key: an die User-ID binden (Cloudflare kollabiert IPs auf eine)."""
    if current_user.is_authenticated:
        return f'user:{current_user.id}'
    return get_remote_address()


def _require_post_author_or_admin(post: ForumPost):
    """403, wenn weder Autor noch Admin."""
    if not post.can_edit(current_user):
        abort(403)


# ── Lesen ───────────────────────────────────────────────────────────────

@forum_bp.route('/')
@login_required
def index():
    """Forum-Startseite: aktive Kategorien + Topic-Zahl + letztes Thema."""
    categories = (
        ForumCategory.query
        .filter_by(is_active=True)
        .order_by(ForumCategory.display_order.asc(), ForumCategory.id.asc())
        .all()
    )

    # Topic-Zahlen je Kategorie in EINER gruppierten Query (kein N+1).
    count_rows = (
        db.session.query(ForumTopic.category_id, func.count(ForumTopic.id))
        .filter(ForumTopic.is_deleted.is_(False))
        .group_by(ForumTopic.category_id)
        .all()
    )
    topic_counts = {cat_id: n for cat_id, n in count_rows}

    # Letztes Thema je Kategorie (wenige Kategorien → guenstige Einzelqueries).
    latest = {}
    for cat in categories:
        latest[cat.id] = (
            ForumTopic.query
            .filter_by(category_id=cat.id, is_deleted=False)
            .order_by(ForumTopic.last_activity_at.desc())
            .first()
        )

    return render_template(
        'forum/index.html',
        categories=categories,
        topic_counts=topic_counts,
        latest=latest,
    )


@forum_bp.route('/<category_slug>')
@login_required
def category(category_slug):
    """Topic-Liste einer Kategorie (paginiert, angepinnte zuerst)."""
    cat = ForumCategory.query.filter_by(
        slug=category_slug, is_active=True,
    ).first_or_404()

    page = request.args.get('page', 1, type=int)
    pagination = (
        ForumTopic.query
        .options(joinedload(ForumTopic.author))
        .filter_by(category_id=cat.id, is_deleted=False)
        .order_by(
            ForumTopic.is_pinned.desc(),
            ForumTopic.last_activity_at.desc(),
        )
        .paginate(page=page, per_page=TOPICS_PER_PAGE, error_out=False)
    )

    return render_template(
        'forum/category.html',
        category=cat,
        pagination=pagination,
        topics=pagination.items,
        can_post=cat.can_post(current_user),
    )


@forum_bp.route('/topic/<int:topic_id>')
@forum_bp.route('/topic/<int:topic_id>/<slug>')
@login_required
def view_topic(topic_id, slug=None):
    """Thema mit allen (paginierten) Beitraegen + Antwort-Formular."""
    topic = ForumTopic.query.filter_by(
        id=topic_id, is_deleted=False,
    ).first_or_404()

    # View-Zaehler (best effort, simpel: pro GET +1).
    topic.view_count = (topic.view_count or 0) + 1
    db.session.commit()

    page = request.args.get('page', 1, type=int)
    pagination = (
        ForumPost.query
        .options(joinedload(ForumPost.author))
        .filter_by(topic_id=topic.id)
        .order_by(ForumPost.created_at.asc(), ForumPost.id.asc())
        .paginate(page=page, per_page=POSTS_PER_PAGE, error_out=False)
    )

    return render_template(
        'forum/topic.html',
        topic=topic,
        category=topic.category,
        pagination=pagination,
        posts=pagination.items,
        form=PostForm(),
    )


# ── Schreiben ─────────────────────────────────────────────────────────────

@forum_bp.route('/<category_slug>/new', methods=['GET', 'POST'])
@login_required
@limiter.limit('3 per hour', key_func=_user_or_ip, methods=['POST'])
def new_topic(category_slug):
    """Neues Thema anlegen (Topic + Eroeffnungsbeitrag in einer Transaktion)."""
    cat = ForumCategory.query.filter_by(
        slug=category_slug, is_active=True,
    ).first_or_404()

    # Ankuendigungen o.ae.: nur Admins duerfen hier posten — serverseitig.
    if not cat.can_post(current_user):
        abort(403)

    form = TopicForm()
    if form.validate_on_submit():
        topic = ForumTopic(
            category_id=cat.id,
            author_id=current_user.id,
            title=form.title.data.strip(),
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
        )
        db.session.add(topic)
        db.session.flush()  # ID zuweisen, damit der Slug eindeutig wird
        topic.slug = topic.build_slug()

        op = ForumPost(
            topic_id=topic.id,
            author_id=current_user.id,
            body=form.body.data,
            is_op=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(op)
        db.session.commit()
        flash('Thema erstellt.', 'success')
        return redirect(url_for('forum.view_topic', topic_id=topic.id, slug=topic.slug))

    return render_template('forum/new_topic.html', category=cat, form=form)


@forum_bp.route('/topic/<int:topic_id>/reply', methods=['POST'])
@login_required
@limiter.limit('10 per hour', key_func=_user_or_ip)
def reply(topic_id):
    """Antwort auf ein Thema."""
    topic = ForumTopic.query.filter_by(
        id=topic_id, is_deleted=False,
    ).first_or_404()

    if topic.is_locked and not current_user.is_admin:
        flash('Dieses Thema ist gesperrt — keine neuen Antworten möglich.', 'warning')
        return redirect(url_for('forum.view_topic', topic_id=topic.id, slug=topic.slug))

    form = PostForm()
    if form.validate_on_submit():
        post = ForumPost(
            topic_id=topic.id,
            author_id=current_user.id,
            body=form.body.data,
            is_op=False,
            created_at=datetime.utcnow(),
        )
        db.session.add(post)
        # Denormalisierte Zaehler atomar im selben Commit pflegen.
        topic.reply_count = (topic.reply_count or 0) + 1
        topic.last_activity_at = datetime.utcnow()
        db.session.commit()
        flash('Antwort gespeichert.', 'success')
    else:
        for errors in form.errors.values():
            for err in errors:
                flash(err, 'danger')

    # Auf die letzte Seite springen, damit die neue Antwort sichtbar ist.
    # Aus DERSELBEN Menge ableiten, die view_topic paginiert (alle Posts inkl.
    # OP + Soft-Delete-Tombstones) — reply_count allein weicht ab, sobald
    # geloeschte Beitraege Seitenplaetze belegen.
    total_posts = ForumPost.query.filter_by(topic_id=topic.id).count()
    last_page = max(1, (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)
    return redirect(
        url_for('forum.view_topic', topic_id=topic.id, slug=topic.slug, page=last_page)
        + '#beitraege'
    )


@forum_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@limiter.limit('20 per hour', key_func=_user_or_ip, methods=['POST'])
def edit_post(post_id):
    """Eigenen Beitrag bearbeiten (Admin darf jeden)."""
    post = ForumPost.query.filter_by(id=post_id, is_deleted=False).first_or_404()
    _require_post_author_or_admin(post)

    # In gesperrtem Thema kann nur ein Admin bearbeiten.
    if post.topic.is_locked and not current_user.is_admin:
        abort(403)

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.body = form.body.data
        post.edited_at = datetime.utcnow()
        db.session.commit()
        flash('Beitrag aktualisiert.', 'success')
        return redirect(
            url_for('forum.view_topic', topic_id=post.topic_id, slug=post.topic.slug)
            + f'#post-{post.id}'
        )

    return render_template('forum/edit_post.html', post=post, form=form, topic=post.topic)


@forum_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Beitrag soft-loeschen (Autor oder Admin). Zeile bleibt, Flag gesetzt."""
    post = ForumPost.query.filter_by(id=post_id, is_deleted=False).first_or_404()
    _require_post_author_or_admin(post)

    # In gesperrtem Thema kann nur ein Admin loeschen (symmetrisch zu edit_post).
    if post.topic.is_locked and not current_user.is_admin:
        abort(403)

    topic = post.topic
    post.is_deleted = True
    post.deleted_at = datetime.utcnow()
    post.deleted_by_id = current_user.id
    # Sichtbare-Antworten-Zaehler korrigieren (OP zaehlt nicht als Antwort).
    if not post.is_op:
        topic.reply_count = max(0, (topic.reply_count or 0) - 1)
    db.session.commit()
    flash('Beitrag gelöscht.', 'success')
    return redirect(url_for('forum.view_topic', topic_id=topic.id, slug=topic.slug))


# ── Moderation (nur Admin) ──────────────────────────────────────────────────

@forum_bp.route('/topic/<int:topic_id>/pin', methods=['POST'])
@login_required
@admin_required
def pin_topic(topic_id):
    """Thema anpinnen/loesen (Toggle)."""
    topic = ForumTopic.query.filter_by(id=topic_id, is_deleted=False).first_or_404()
    topic.is_pinned = not topic.is_pinned
    db.session.commit()
    flash('Thema angepinnt.' if topic.is_pinned else 'Thema losgelöst.', 'success')
    return redirect(url_for('forum.view_topic', topic_id=topic.id, slug=topic.slug))


@forum_bp.route('/topic/<int:topic_id>/lock', methods=['POST'])
@login_required
@admin_required
def lock_topic(topic_id):
    """Thema sperren/entsperren (Toggle)."""
    topic = ForumTopic.query.filter_by(id=topic_id, is_deleted=False).first_or_404()
    topic.is_locked = not topic.is_locked
    db.session.commit()
    flash('Thema gesperrt.' if topic.is_locked else 'Thema entsperrt.', 'success')
    return redirect(url_for('forum.view_topic', topic_id=topic.id, slug=topic.slug))


@forum_bp.route('/topic/<int:topic_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_topic(topic_id):
    """Ganzes Thema soft-loeschen (nur Admin)."""
    topic = ForumTopic.query.filter_by(id=topic_id, is_deleted=False).first_or_404()
    category_slug = topic.category.slug
    topic.is_deleted = True
    topic.deleted_at = datetime.utcnow()
    topic.deleted_by_id = current_user.id
    db.session.commit()
    flash('Thema gelöscht.', 'success')
    return redirect(url_for('forum.category', category_slug=category_slug))

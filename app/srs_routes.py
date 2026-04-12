# app/srs_routes.py
"""API-Endpoints fuer das Spaced Repetition System (FSRS)."""
import logging
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app import srs_service

logger = logging.getLogger(__name__)

srs_bp = Blueprint('srs', __name__)


# ── API Endpoints ──────────────────────────────────────────────


@srs_bp.route('/api/srs/rate', methods=['POST'])
@login_required
def api_rate_card():
    """Bewertet eine Karte und berechnet den neuen FSRS-State."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Keine Daten'}), 400

    content_id = data.get('content_id')
    rating = data.get('rating')
    time_taken_ms = data.get('time_taken_ms')

    if not content_id or not rating:
        return jsonify({'error': 'content_id und rating erforderlich'}), 400

    if rating not in (1, 2, 3, 4):
        return jsonify({'error': 'rating muss 1-4 sein'}), 400

    try:
        result = srs_service.rate_card(
            user_id=current_user.id,
            content_id=int(content_id),
            rating_int=int(rating),
            time_taken_ms=int(time_taken_ms) if time_taken_ms else None,
        )

        # Streak aktualisieren
        current_user.update_streak()
        from app import db
        db.session.commit()

        # Verbleibende faellige Karten zaehlen
        result['cards_remaining'] = srs_service.get_due_count(current_user.id)

        return jsonify(result)
    except Exception as e:
        logger.error(f'Fehler bei rate_card: {e}')
        return jsonify({'error': 'Interner Fehler'}), 500


@srs_bp.route('/api/srs/due')
@login_required
def api_due_cards():
    """Holt alle faelligen Karten fuer den aktuellen User."""
    limit = request.args.get('limit', 50, type=int)
    lesson_id = request.args.get('lesson_id', type=int)
    content_type = request.args.get('content_type')

    due_states = srs_service.get_due_cards(
        user_id=current_user.id,
        limit=limit,
        lesson_id=lesson_id,
        content_type=content_type,
    )

    cards = []
    for state in due_states:
        content = state.content
        if not content:
            continue
        card_data = srs_service.get_content_data_for_review(content)
        card_data['due_date'] = state.due_date.isoformat()
        card_data['status'] = state.status
        card_data['reps'] = state.reps
        card_data['lapses'] = state.lapses
        cards.append(card_data)

    total_due = srs_service.get_due_count(current_user.id)

    return jsonify({
        'cards': cards,
        'total_due': total_due,
    })


@srs_bp.route('/api/srs/preview')
@login_required
def api_interval_preview():
    """Zeigt voraussichtliche Intervalle fuer alle 4 Ratings."""
    content_id = request.args.get('content_id', type=int)
    if not content_id:
        return jsonify({'error': 'content_id erforderlich'}), 400

    previews = srs_service.get_interval_preview(current_user.id, content_id)
    return jsonify(previews)


@srs_bp.route('/api/srs/reviewed-ids')
@login_required
def api_reviewed_ids():
    """Gibt alle Content-IDs zurueck, die der User bereits bewertet hat (fuer Deck-Init)."""
    from app.models import CardReviewState
    lesson_id = request.args.get('lesson_id', type=int)

    query = CardReviewState.query.filter(
        CardReviewState.user_id == current_user.id,
    )
    if lesson_id:
        from app.models import LessonContent
        query = query.join(LessonContent).filter(LessonContent.lesson_id == lesson_id)

    ids = [r.content_id for r in query.all()]
    return jsonify({'reviewed_ids': ids})


@srs_bp.route('/api/srs/stats')
@login_required
def api_stats():
    """Basis-Statistiken fuer den aktuellen User."""
    stats = srs_service.get_user_stats(current_user.id)
    stats['current_streak'] = current_user.current_streak or 0
    stats['longest_streak'] = current_user.longest_streak or 0
    return jsonify(stats)


# ── Seiten ─────────────────────────────────────────────────────


@srs_bp.route('/review')
@login_required
def review_page():
    """Taegliche Wiederholungs-Seite."""
    stats = srs_service.get_user_stats(current_user.id)
    stats['current_streak'] = current_user.current_streak or 0
    stats['longest_streak'] = current_user.longest_streak or 0
    return render_template('review.html', stats=stats)

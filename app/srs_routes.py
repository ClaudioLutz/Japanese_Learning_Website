# app/srs_routes.py
"""API-Endpoints fuer das Spaced Repetition System (FSRS)."""
import csv
import io
import logging

from flask import Blueprint, jsonify, make_response, render_template, request
from flask_login import current_user, login_required

from app import db, srs_service
from app.achievements import ACHIEVEMENTS, check_achievements
from app.gamification_service import XP_STREAK_DAY
from app.models import UserAchievement

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
        old_streak = current_user.current_streak or 0

        result = srs_service.rate_card(
            user_id=current_user.id,
            content_id=int(content_id),
            rating_int=int(rating),
            time_taken_ms=int(time_taken_ms) if time_taken_ms else None,
        )

        # Streak aktualisieren
        current_user.update_streak()

        # Streak-Tag-XP (wenn Streak gerade inkrementiert wurde)
        new_streak = current_user.current_streak or 0
        if new_streak > old_streak:
            current_user.add_xp(XP_STREAK_DAY)

        # Achievement-Check
        new_achievements = check_achievements(current_user)
        db.session.commit()

        result['new_achievements'] = new_achievements
        result['cards_remaining'] = srs_service.get_due_count(current_user.id)
        result['current_streak'] = new_streak

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
    from app.models import CardReviewState, LessonContent
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


# ── Phase 6: Statistik-Endpoints ─────────────────────────────


@srs_bp.route('/api/srs/stats/heatmap')
@login_required
def api_stats_heatmap():
    """365-Tage Review-Heatmap-Daten."""
    data = srs_service.get_heatmap_data(current_user.id)
    return jsonify({'data': data})


@srs_bp.route('/api/srs/stats/retention')
@login_required
def api_stats_retention():
    """Retention nach Intervall-Bereichen."""
    settings = current_user.srs_settings
    desired = settings.desired_retention if settings else 0.9
    data = srs_service.get_retention_by_interval(current_user.id)
    return jsonify({'data': data, 'desired_retention': desired * 100})


@srs_bp.route('/api/srs/stats/forecast')
@login_required
def api_stats_forecast():
    """30-Tage Review-Forecast."""
    days = request.args.get('days', 30, type=int)
    data = srs_service.get_review_forecast(current_user.id, min(days, 90))
    return jsonify({'data': data})


@srs_bp.route('/api/srs/stats/maturity')
@login_required
def api_stats_maturity():
    """Karten-Verteilung nach Reifestufe."""
    data = srs_service.get_maturity_distribution(current_user.id)
    return jsonify(data)


@srs_bp.route('/api/srs/stats/content-type')
@login_required
def api_stats_content_type():
    """Performance pro Content-Typ."""
    data = srs_service.get_performance_by_type(current_user.id)
    return jsonify({'data': data})


@srs_bp.route('/api/srs/stats/leeches')
@login_required
def api_stats_leeches():
    """Problematische Karten (Leeches)."""
    settings = current_user.srs_settings
    threshold = settings.leech_threshold if settings else 8
    data = srs_service.get_leeches(current_user.id, threshold)
    return jsonify({'data': data})


@srs_bp.route('/api/srs/stats/response-times')
@login_required
def api_stats_response_times():
    """Antwortzeit-Histogramm."""
    data = srs_service.get_response_time_histogram(current_user.id)
    return jsonify({'data': data})


@srs_bp.route('/review/stats')
@login_required
def stats_page():
    """Erweiterte Statistiken-Seite."""
    stats = srs_service.get_user_stats(current_user.id)
    stats['current_streak'] = current_user.current_streak or 0
    stats['longest_streak'] = current_user.longest_streak or 0
    stats['level'] = current_user.level or 1
    stats['total_xp'] = current_user.total_xp or 0
    stats['level_title'] = current_user.level_title
    return render_template('stats.html', stats=stats)


# ── Phase 6: Karten-Browser ──────────────────────────────────


@srs_bp.route('/api/srs/browse')
@login_required
def api_browse_cards():
    """Karten-Browser mit Filter, Suche, Pagination."""
    filters = {
        'status': request.args.get('status'),
        'content_type': request.args.get('content_type'),
        'lesson_id': request.args.get('lesson_id', type=int),
        'leech': request.args.get('leech', '').lower() == 'true',
        'due_today': request.args.get('due_today', '').lower() == 'true',
        'search': request.args.get('q', ''),
        'sort': request.args.get('sort', 'due_date'),
        'sort_dir': request.args.get('order', 'asc'),
        'page': request.args.get('page', 1, type=int),
        'per_page': request.args.get('per_page', 50, type=int),
    }
    result = srs_service.browse_cards(current_user.id, filters)
    return jsonify(result)


@srs_bp.route('/api/srs/card/<int:content_id>/detail')
@login_required
def api_card_detail(content_id):
    """Detaillierte Karten-Info inkl. Review-History."""
    data = srs_service.get_card_detail(current_user.id, content_id)
    if not data:
        return jsonify({'error': 'Karte nicht gefunden'}), 404
    return jsonify(data)


@srs_bp.route('/api/srs/card/suspend', methods=['POST'])
@login_required
def api_card_suspend():
    """Karte suspendieren."""
    data = request.get_json()
    content_id = data.get('content_id') if data else None
    if not content_id:
        return jsonify({'error': 'content_id erforderlich'}), 400
    ok = srs_service.suspend_card(current_user.id, int(content_id))
    return jsonify({'success': ok})


@srs_bp.route('/api/srs/card/unsuspend', methods=['POST'])
@login_required
def api_card_unsuspend():
    """Karte reaktivieren."""
    data = request.get_json()
    content_id = data.get('content_id') if data else None
    if not content_id:
        return jsonify({'error': 'content_id erforderlich'}), 400
    ok = srs_service.unsuspend_card(current_user.id, int(content_id))
    return jsonify({'success': ok})


@srs_bp.route('/api/srs/card/reset', methods=['POST'])
@login_required
def api_card_reset():
    """FSRS-State einer Karte zuruecksetzen."""
    data = request.get_json()
    content_id = data.get('content_id') if data else None
    if not content_id:
        return jsonify({'error': 'content_id erforderlich'}), 400
    ok = srs_service.reset_card(current_user.id, int(content_id))
    return jsonify({'success': ok})


@srs_bp.route('/api/srs/bulk-action', methods=['POST'])
@login_required
def api_bulk_action():
    """Bulk-Aktion auf mehrere Karten (max 100)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Keine Daten'}), 400

    action = data.get('action')
    content_ids = data.get('content_ids', [])

    if action not in ('suspend', 'unsuspend', 'reset'):
        return jsonify({'error': 'Ungueltige Aktion'}), 400
    if not content_ids or len(content_ids) > 100:
        return jsonify({'error': 'content_ids: 1-100 erforderlich'}), 400

    action_map = {
        'suspend': srs_service.suspend_card,
        'unsuspend': srs_service.unsuspend_card,
        'reset': srs_service.reset_card,
    }
    fn = action_map[action]
    affected = sum(1 for cid in content_ids if fn(current_user.id, int(cid)))

    return jsonify({'affected': affected, 'total': len(content_ids)})


@srs_bp.route('/api/srs/browse/export')
@login_required
def api_browse_export():
    """Exportiert Karten als CSV."""
    filters = {
        'status': request.args.get('status'),
        'content_type': request.args.get('content_type'),
        'lesson_id': request.args.get('lesson_id', type=int),
        'leech': request.args.get('leech', '').lower() == 'true',
        'due_today': request.args.get('due_today', '').lower() == 'true',
        'search': request.args.get('q', ''),
        'sort': request.args.get('sort', 'due_date'),
        'sort_dir': request.args.get('order', 'asc'),
        'page': 1,
        'per_page': 1000,
    }
    result = srs_service.browse_cards(current_user.id, filters)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Content-ID', 'Typ', 'Karte', 'Status', 'Stufe', 'Faellig', 'Reps', 'Lapses', 'Lektion'])

    for card in result['cards']:
        writer.writerow([
            card['content_id'], card['content_type'], card['front'],
            card['status'], card['stage_name'], card.get('due_date', ''),
            card['reps'], card['lapses'], card.get('lesson_title', ''),
        ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = 'attachment; filename=karten_export.csv'
    return resp


@srs_bp.route('/review/browse')
@login_required
def browse_page():
    """Karten-Browser-Seite."""
    from app.models import Lesson
    lessons = Lesson.query.filter_by(is_published=True).order_by(Lesson.title).all()
    return render_template('browse.html', lessons=lessons)


# ── Phase 6: Gamification-Endpoints ──────────────────────────


@srs_bp.route('/api/srs/achievements')
@login_required
def api_achievements():
    """Alle Achievements mit Unlock-Status."""
    unlocked = {a.achievement_key: a for a in
                UserAchievement.query.filter_by(user_id=current_user.id).all()}

    result = {'unlocked': [], 'locked': [], 'new': []}

    for key, defn in ACHIEVEMENTS.items():
        entry = {
            'key': key,
            'name': defn['name'],
            'description': defn['description'],
            'icon': defn['icon'],
            'category': defn['category'],
            'rarity': defn.get('rarity', 'common'),
        }
        if key in unlocked:
            entry['unlocked_at'] = unlocked[key].unlocked_at.isoformat()
            if not unlocked[key].notified:
                result['new'].append(entry)
            result['unlocked'].append(entry)
        else:
            result['locked'].append(entry)

    return jsonify(result)


@srs_bp.route('/api/srs/achievements/notify', methods=['POST'])
@login_required
def api_achievements_notify():
    """Markiert Achievements als gesehen (notified=True)."""
    data = request.get_json()
    keys = data.get('achievement_keys', []) if data else []

    updated = 0
    for key in keys:
        ach = UserAchievement.query.filter_by(
            user_id=current_user.id, achievement_key=key
        ).first()
        if ach and not ach.notified:
            ach.notified = True
            updated += 1

    db.session.commit()
    return jsonify({'updated': updated})


@srs_bp.route('/api/srs/jlpt-progress')
@login_required
def api_jlpt_progress():
    """JLPT N5-N1 Fortschritt."""
    data = srs_service.get_jlpt_progress(current_user.id)
    return jsonify(data)

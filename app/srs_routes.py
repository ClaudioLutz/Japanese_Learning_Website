# app/srs_routes.py
"""API-Endpoints fuer das Spaced Repetition System (FSRS)."""
import csv
import io
import logging

from flask import Blueprint, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db, srs_service
from app.achievements import ACHIEVEMENTS, check_achievements
from app.gamification_service import (
    XP_STREAK_DAY,
    XP_STORM_BASE,
    XP_STORM_PER_HIT,
    XP_STORM_RUN_BONUS_CAP,
    XP_STORM_DAILY_CAP,
    compute_kana_mastery_context,
)
from app.models import KanaStormScore, UserAchievement

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
    # Lernrichtung (Default forward) — Deck + Kana-Grid senden keine, bleiben forward.
    direction = data.get('direction', 'forward')
    # Kana-Grid-Spiel-Kontext (optional, vom Frontend gesetzt)
    grid_ctx = data.get('grid_context') or {}

    if not content_id or not rating:
        return jsonify({'error': 'content_id und rating erforderlich'}), 400

    if rating not in (1, 2, 3, 4):
        return jsonify({'error': 'rating muss 1-4 sein'}), 400

    if direction not in ('forward', 'reverse'):
        return jsonify({'error': "direction muss 'forward' oder 'reverse' sein"}), 400

    try:
        old_streak = current_user.current_streak or 0

        result = srs_service.rate_card(
            user_id=current_user.id,
            content_id=int(content_id),
            rating_int=int(rating),
            time_taken_ms=int(time_taken_ms) if time_taken_ms else None,
            direction=direction,
        )

        # Streak aktualisieren
        current_user.update_streak()

        # Streak-Tag-XP (wenn Streak gerade inkrementiert wurde)
        new_streak = current_user.current_streak or 0
        if new_streak > old_streak:
            current_user.add_xp(XP_STREAK_DAY)

        # Achievement-Check inkl. Kana-Mastery + Grid-Spiel-Kontext
        ach_ctx = {}
        ach_ctx.update(compute_kana_mastery_context(current_user.id))
        if isinstance(grid_ctx, dict):
            ach_ctx.update(grid_ctx)
        new_achievements = check_achievements(current_user, context=ach_ctx)
        db.session.commit()

        result['new_achievements'] = new_achievements
        # Rest-Zaehler der jeweiligen Queue (Produktion hat eigenen Zaehler).
        result['cards_remaining'] = (
            srs_service.get_production_due_count(current_user.id)
            if direction == 'reverse'
            else srs_service.get_due_count(current_user.id)
        )
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

    direction = request.args.get('direction', 'forward')
    if direction not in ('forward', 'reverse'):
        direction = 'forward'
    previews = srs_service.get_interval_preview(current_user.id, content_id, direction=direction)
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
    # Produktions-Faelligkeit (DE->JP) fuers Nav-Segment-Badge (eigener Zaehler).
    stats['production_due_count'] = srs_service.get_production_due_count(current_user.id)
    return jsonify(stats)


# ── Seiten ─────────────────────────────────────────────────────


@srs_bp.route('/review')
def review_page():
    """Taegliche Wiederholungs-Seite.

    10.6: Gaeste sehen eine weiche Teaser-Landing (Nutzen + Register/Login mit
    next), keinen harten Login-Redirect. Eingeloggt = normale Seite.
    """
    if not current_user.is_authenticated:
        return render_template('review_teaser.html', teaser_page='review')
    stats = srs_service.get_user_stats(current_user.id)
    stats['current_streak'] = current_user.current_streak or 0
    stats['longest_streak'] = current_user.longest_streak or 0
    return render_template('review.html', stats=stats)


# ── Produktion (DE->JP): eigene Seite + Queue ────────────────


@srs_bp.route('/review/produktion')
def production_page():
    """Produktions-Seite (DE->JP): eigene, immer verfuegbare Queue.

    Zeigt rezeptiv gefestigte Vokabeln (forward-Stage>=3) in umgekehrter Richtung —
    deutscher Cue vorne, japanisches Wort + Lesung als Antwort. Die reverse-Karte
    entsteht on-the-fly beim ersten Rating. Gaeste: weiche Teaser-Landing.
    """
    if not current_user.is_authenticated:
        return render_template('review_teaser.html', teaser_page='review')
    overview = srs_service.get_production_overview(current_user.id)
    overview['current_streak'] = current_user.current_streak or 0
    overview['longest_streak'] = current_user.longest_streak or 0
    return render_template('review_produktion.html', overview=overview)


@srs_bp.route('/api/srs/production/queue')
@login_required
def api_production_queue():
    """Produktions-Queue: faellige reverse-Karten + produktiv neue Vokabeln.

    Beide werden identisch gerendert (Front = deutscher Cue). Neue Items haben
    noch keinen reverse-State (is_new=True) — er entsteht beim ersten Rating.
    """
    limit = request.args.get('limit', 30, type=int)
    limit = max(1, min(limit, 50))
    cards = []
    seen = set()

    for state in srs_service.get_production_due_cards(current_user.id, limit=limit):
        content = state.content
        if not content or content.id in seen:
            continue
        seen.add(content.id)
        cd = srs_service.get_content_data_for_review(content)
        cd['direction'] = 'reverse'
        cd['is_new'] = False
        cd['due_date'] = state.due_date.isoformat()
        cd['status'] = state.status
        cd['reps'] = state.reps
        cd['lapses'] = state.lapses
        cards.append(cd)

    # Neue Karten nur bis zum Tageslimit nachfuellen (Backlog-Flut bremsen).
    remaining = max(0, limit - len(cards))
    allowance = srs_service.get_production_new_allowance(current_user.id)
    new_to_fetch = min(remaining, allowance)
    if new_to_fetch:
        for lc in srs_service.get_production_new_cards(current_user.id, limit=new_to_fetch):
            if lc.id in seen:
                continue
            seen.add(lc.id)
            cd = srs_service.get_content_data_for_review(lc)
            cd['direction'] = 'reverse'
            cd['is_new'] = True
            cd['status'] = 'new'
            cd['reps'] = 0
            cd['lapses'] = 0
            cards.append(cd)

    return jsonify({
        'cards': cards,
        'overview': srs_service.get_production_overview(current_user.id),
    })


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
def stats_page():
    """Erweiterte Statistiken-Seite.

    10.6: Gaeste sehen die weiche Teaser-Landing statt eines Login-Redirects.
    """
    if not current_user.is_authenticated:
        return render_template('review_teaser.html', teaser_page='stats')
    stats = srs_service.get_user_stats(current_user.id)
    stats['current_streak'] = current_user.current_streak or 0
    stats['longest_streak'] = current_user.longest_streak or 0
    level = current_user.level or 1
    total_xp = current_user.total_xp or 0
    stats['level'] = level
    stats['total_xp'] = total_xp
    stats['level_title'] = current_user.level_title

    # Level-Fortschritt: total_xp ist KUMULATIV (wird beim Level-Up nicht
    # zurueckgesetzt), xp_for_next_level ist die ABSOLUTE Schwelle des
    # naechsten Levels. Fuer einen Pro-Level-Balken den Boden des aktuellen
    # Levels abziehen, sonst uebertreibt der Anteil bei hoeheren Levels.
    xp_next = current_user.xp_for_next_level
    xp_floor = int(100 * ((level - 1) ** 1.5))
    span = max(1, xp_next - xp_floor)
    in_level = max(0, total_xp - xp_floor)
    stats['xp_next_level'] = xp_next
    stats['xp_to_next'] = max(0, xp_next - total_xp)
    stats['level_progress_pct'] = max(0, min(100, round(in_level / span * 100)))
    # Persoenliche Kana-Storm-Statistik (nur fuer eingeloggte Spieler befuellt).
    stats['storm'] = srs_service.get_kana_storm_stats(current_user.id)
    # Produktions-Spur (DE->JP, reverse) — Sektion erscheint erst ab 1 Karte.
    stats['production'] = srs_service.get_production_stats(current_user.id)
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
    writer.writerow(['Content-ID', 'Typ', 'Karte', 'Lesung', 'Bedeutung', 'Status', 'Stufe', 'Faellig', 'Reps', 'Lapses', 'Lektion'])

    for card in result['cards']:
        d = card.get('details') or {}
        ct = card['content_type']
        if ct == 'vocabulary':
            reading = d.get('reading') or ''
            meaning = d.get('meaning_de') or d.get('meaning') or ''
        elif ct == 'kanji':
            reading = ' / '.join(p for p in [d.get('onyomi'), d.get('kunyomi')] if p)
            meaning = d.get('meaning') or ''
        elif ct == 'kana':
            reading = d.get('romanization') or ''
            meaning = ''
        elif ct == 'grammar':
            reading = d.get('romaji') or ''
            meaning = d.get('explanation') or ''
        else:
            reading = ''
            meaning = ''
        writer.writerow([
            card['content_id'], ct, card['front'], reading, meaning,
            card['status'], card['stage_name'], card.get('due_date', ''),
            card['reps'], card['lapses'], card.get('lesson_title', ''),
        ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = 'attachment; filename=karten_export.csv'
    return resp


@srs_bp.route('/review/browse')
def browse_page():
    """Karten-Browser-Seite.

    10.6: Gaeste sehen die weiche Teaser-Landing statt eines Login-Redirects.
    """
    if not current_user.is_authenticated:
        return render_template('review_teaser.html', teaser_page='browse')
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


# ── Kana-Statistik (Phase 2) ──────────────────────────────────


@srs_bp.route('/api/srs/stats/kana-heatmap')
@login_required
def api_kana_heatmap():
    """Pro-Zeichen-Statistik fuer Hiragana/Katakana.

    Liefert fuer jeden Kana, fuer den der User mind. 1 Review hat:
    {id, character, romanization, type, row, stage_idx, stage_name,
     stage_color, accuracy (0-100), total_reps, lapses}
    """
    from app.models import CardReviewState, Kana, LessonContent, ReviewLog
    from app.services.kana_rows import row_for_kana
    from app.gamification_service import get_card_stage
    from sqlalchemy import case, func

    # 1) Alle CardReviewStates des Users zu kana-Content-Items
    states = (
        db.session.query(CardReviewState, LessonContent, Kana)
        .join(LessonContent, CardReviewState.content_id == LessonContent.id)
        .join(Kana, LessonContent.content_id == Kana.id)
        .filter(
            CardReviewState.user_id == current_user.id,
            LessonContent.content_type == 'kana',
        )
        .all()
    )

    # 2) Accuracy pro content_id ueber ReviewLog (alle Ratings >=3 = correct)
    accuracy_rows = (
        db.session.query(
            ReviewLog.content_id,
            func.count(ReviewLog.id).label('total'),
            func.sum(case((ReviewLog.rating >= 3, 1), else_=0)).label('correct'),
        )
        .filter(ReviewLog.user_id == current_user.id)
        .group_by(ReviewLog.content_id)
        .all()
    )
    accuracy_by_content = {
        r.content_id: (int(r.correct or 0) / int(r.total or 1) * 100)
        for r in accuracy_rows
    }

    result = []
    for state, lc, kana in states:
        stage_idx, stage_name, stage_color = get_card_stage(state.fsrs_card_state)
        result.append({
            'kana_id': kana.id,
            'lesson_content_id': lc.id,
            'character': kana.character,
            'romanization': kana.romanization,
            'type': kana.type,
            'row': row_for_kana(kana.character),
            'stage_idx': stage_idx,
            'stage_name': stage_name,
            'stage_color': stage_color,
            'accuracy': round(accuracy_by_content.get(lc.id, 0), 1),
            'total_reps': state.reps,
            'lapses': state.lapses,
        })

    return jsonify({'data': result, 'count': len(result)})


@srs_bp.route('/api/srs/stats/kana-weak')
@login_required
def api_kana_weak():
    """Top-N schwaechste Kana (sortiert nach lapses DESC, accuracy ASC).

    Query-Param: limit (default 5, max 20)
    """
    from app.models import CardReviewState, Kana, LessonContent, ReviewLog
    from sqlalchemy import case, func

    limit = min(request.args.get('limit', 5, type=int), 20)

    # Subquery: Accuracy + Total Reviews pro content_id
    acc_sub = (
        db.session.query(
            ReviewLog.content_id.label('content_id'),
            func.count(ReviewLog.id).label('total'),
            func.sum(case((ReviewLog.rating >= 3, 1), else_=0)).label('correct'),
        )
        .filter(ReviewLog.user_id == current_user.id)
        .group_by(ReviewLog.content_id)
        .subquery()
    )

    states = (
        db.session.query(CardReviewState, LessonContent, Kana, acc_sub.c.total, acc_sub.c.correct)
        .join(LessonContent, CardReviewState.content_id == LessonContent.id)
        .join(Kana, LessonContent.content_id == Kana.id)
        .outerjoin(acc_sub, acc_sub.c.content_id == CardReviewState.content_id)
        .filter(
            CardReviewState.user_id == current_user.id,
            LessonContent.content_type == 'kana',
            CardReviewState.reps > 0,
        )
        .all()
    )

    # Sortier-Score: (lapses, -accuracy, -reps)
    def weakness(item):
        state, _lc, _k, total, correct = item
        acc = (int(correct or 0) / int(total or 1)) if total else 0
        return (-state.lapses, acc, -state.reps)

    states.sort(key=weakness)
    weakest = states[:limit]

    result = []
    for state, lc, kana, total, correct in weakest:
        acc = (int(correct or 0) / int(total or 1) * 100) if total else 0
        result.append({
            'kana_id': kana.id,
            'lesson_content_id': lc.id,
            'character': kana.character,
            'romanization': kana.romanization,
            'type': kana.type,
            'lapses': state.lapses,
            'reps': state.reps,
            'accuracy': round(acc, 1),
        })
    return jsonify({'data': result, 'count': len(result)})


# 10.12: Web-Push war kompletter Totcode (keine Subscribe-UI, keine VAPID-Keys,
# kein Versandpfad, nur-Push-Service-Worker ohne Caching). Endpoints
# /api/user/push-subscribe + /push-unsubscribe + die SW-Registrierung +
# app/static/sw.js entfernt. Das Modellfeld User.push_subscription bleibt dormant
# (harmlos, ungenutzt) und kann spaeter separat per Migration entfernt werden.


# ── Practice / Daily Challenge (Phase 3) ─────────────────────


def _user_unlocked_kana_ids(user_id, include_locked=False):
    """Gibt die LessonContent-IDs aller Kana zurueck, die der User freigeschaltet hat.

    Freigeschaltet = Lesson abgeschlossen (UserLessonProgress.is_completed=True).
    Bei include_locked=True werden auch nicht abgeschlossene Lessons mitgezaehlt
    — sinnvoll fuer Admin/Premium-User, die alles ueben duerfen.
    """
    from app.models import LessonContent, UserLessonProgress

    if include_locked:
        return (
            db.session.query(LessonContent.id)
            .filter(LessonContent.content_type == 'kana')
            .all()
        )

    completed_lesson_ids = (
        db.session.query(UserLessonProgress.lesson_id)
        .filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.is_completed.is_(True),
        )
        .subquery()
    )
    return (
        db.session.query(LessonContent.id)
        .filter(
            LessonContent.content_type == 'kana',
            LessonContent.lesson_id.in_(completed_lesson_ids),
        )
        .all()
    )


# ── Gast-Modus (ohne Login) ───────────────────────────────────
# Kana-Referenzdaten sind oeffentlich: Gaeste duerfen ALLES ueben (Hiragana,
# Katakana, beide Schriften, einzelne Reihen, Dakuten/Handakuten, alle Modi).
# Login-pflichtig bleiben nur Persistenz + Analysen (SRS/XP/Streak, "Nur
# schwache Karten", Verwechslungs-Statistik). Quelle ist bewusst NICHT die
# Freischaltung eines Users, sondern die kanonischen Gojuon-Reihen.
_GUEST_BASE_ROW_KEYS = ('vowels', 'k', 's', 't', 'n', 'h', 'm', 'y', 'r', 'w', 'n_kons')
_GUEST_DAKUTEN_ROW_KEYS = ('g', 'z', 'd', 'b', 'p')


def _guest_kana_chars(schrift='hiragana', rows_filter=None, include_dakuten=False):
    """(zeichen, typ)-Tupel des Gast-Scopes in kanonischer Gojuon-Reihenfolge.

    schrift: 'hiragana' | 'katakana' | 'both'
    rows_filter: Iterable von Reihen-Keys (None/leer = alle erlaubten Reihen)
    include_dakuten: Dakuten/Handakuten-Reihen (g/z/d/b/p) einschliessen
    """
    from app.services.kana_rows import HIRAGANA_ROWS, KATAKANA_ROWS
    if rows_filter:
        # Explizite Reihen-Wahl uebersteuert den Dakuten-Schalter — wer den
        # G-Chip anklickt, will die G-Reihe ueben (sonst liefe die Auswahl bei
        # ausgeschaltetem Dakuten-Schalter stumm ins Leere).
        wanted = set(rows_filter)
        row_keys = [key for key in (*_GUEST_BASE_ROW_KEYS, *_GUEST_DAKUTEN_ROW_KEYS)
                    if key in wanted]
    else:
        row_keys = list(_GUEST_BASE_ROW_KEYS)
        if include_dakuten:
            row_keys += list(_GUEST_DAKUTEN_ROW_KEYS)
    scripts = []
    if schrift in ('hiragana', 'both'):
        scripts.append(('hiragana', HIRAGANA_ROWS))
    if schrift in ('katakana', 'both'):
        scripts.append(('katakana', KATAKANA_ROWS))
    pairs = []
    for type_name, table in scripts:
        for key in row_keys:
            pairs.extend((ch, type_name) for ch in table[key])
    return pairs


def _guest_kana_rows(schrift='hiragana', rows_filter=None, include_dakuten=False):
    """(lesson_content_id, Kana)-Tupel fuer anonyme Gaeste.

    Default (ohne Argumente) = komplettes Grund-Hiragana — so nutzen es das
    Startseiten-Embed und die Tages-Challenge. Mit Argumenten liefert sie den
    vollen Gast-Scope (Katakana/beide, Reihen-Auswahl, Dakuten).

    lesson_content_id ist immer None: Gaeste raten nicht ans SRS, die ID wird
    nur fuer Rating-Calls gebraucht (die fuer Gaeste ohnehin uebersprungen
    werden). Reihenfolge folgt der Gojuon-Tabelle (didaktisch sinnvoll fuers
    Gitter).
    """
    from app.models import Kana
    pairs = _guest_kana_chars(schrift, rows_filter, include_dakuten)
    if not pairs:
        return []
    types = {t for _ch, t in pairs}
    kana_by_key = {
        (k.character, k.type): k
        for k in Kana.query.filter(
            Kana.type.in_(types), Kana.character.in_([ch for ch, _t in pairs])
        ).all()
    }
    missing = sum(1 for key in pairs if key not in kana_by_key)
    if missing:
        logger.warning(
            'Gast-Kana: %d von %d Zeichen fehlen in der DB — '
            'Gast-Spiel zeigt evtl. ein leeres/unvollstaendiges Set.',
            missing, len(pairs),
        )
    return [(None, kana_by_key[key]) for key in pairs if key in kana_by_key]


def _kana_item(lesson_content_id, kana, row_key=None, *, with_extras=True):
    """Baut das JSON-Item einer Kana-Karte fuer das Spiel.

    row_key: vorgegebener Reihen-Schluessel (z.B. Confusion-Cluster 'cf_0');
        None -> automatisch via row_for_kana bestimmt.
    with_extras: stroke_order_info + mnemonic mitliefern (Daily braucht sie nicht).
    """
    from app.services.kana_rows import row_for_kana
    item = {
        'kana_id': kana.id,
        'lesson_content_id': lesson_content_id,
        'character': kana.character,
        'romanization': kana.romanization,
        'type': kana.type,
        'row': row_key if row_key is not None else row_for_kana(kana.character),
    }
    if with_extras:
        item['stroke_order_info'] = kana.stroke_order_info
        item['mnemonic'] = kana.mnemonic
    return item


def _parse_limit(default=None, cap=200):
    """limit-Query-Param lesen: None/fehlend/<1 = "alles Gewaehlte".

    Die Anzahl richtet sich nach der Auswahl (Reihen x Schrift) — ein Limit
    ist nur noch ein optionaler API-Parameter, kein UI-Konzept mehr. Cap als
    Schutz gegen Unsinn (mehr als 142 Kana gibt es ohnehin nicht).
    """
    limit = request.args.get('limit', type=int)
    if limit is None or limit < 1:
        return default
    return min(limit, cap)


def _subset_in_order(rows_data, limit):
    """Zufaelliges Teilset der Groesse limit, Original-Reihenfolge erhalten.

    limit=None = kein Teilset (alles Gewaehlte). Statt stumpfem Gojuon-Prefix
    (sonst saehe man bei Limit 20 immer dieselben ersten 20 Zeichen, a- bis
    t-Reihe) — die Gojuon-REIHENFOLGE des gezogenen Teilsets bleibt erhalten
    (das Grid gruppiert didaktisch nach Reihen).
    """
    if limit is None or limit <= 0 or len(rows_data) <= limit:
        return rows_data
    import random as _random
    picked_idx = sorted(_random.sample(range(len(rows_data)), limit))
    return [rows_data[i] for i in picked_idx]


def _guest_scope_payload(mode, schrift, rows_filter, include_dakuten, limit):
    """Antwort-Payload aus dem Gast-Referenz-Scope (volle Gojuon-Tabelle).

    Gemeinsamer Baustein fuer (a) anonyme Gaeste und (b) frisch registrierte
    Konten ohne abgeschlossene Lessons — Registrieren darf den spielbaren
    Umfang nie verkleinern (lesson_content_id=None -> kein SRS-Rating).
    """
    rows_data = _guest_kana_rows(
        schrift=schrift, rows_filter=rows_filter or None, include_dakuten=include_dakuten
    )
    rows_data = _subset_in_order(rows_data, limit)
    items = [_kana_item(lc_id, kana) for lc_id, kana in rows_data]
    payload = {
        'kana': items,
        'count': len(items),
        'mode': mode,
        'filters': {
            'schrift': schrift,
            'rows': rows_filter or [],
            'dakuten': include_dakuten,
            'weak_only': False,
        },
    }
    if not items:
        if rows_filter:
            # Leere Auswahl (z.B. unbekannte Reihen-Keys) — kein DB-Problem.
            payload['message'] = 'Keine Kana für diese Auswahl gefunden — wähle andere Reihen.'
        else:
            # Sollte in Produktion nie passieren (Gojuon-Kana vorhanden) — aber
            # bei leerer/uninitialisierter DB einen verstaendlichen Hinweis liefern,
            # statt den Gast vor einer stummen leeren Buehne stehen zu lassen.
            payload['message'] = ('Die Kana sind gerade nicht verfügbar — bitte lade '
                                  'die Seite neu oder versuche es später erneut.')
    return payload


# ── Kana-Schreibspiel (Tile-fuer-Tile Woerter buchstabieren) ──────────────────
# Drittes Kana-Spiel auf /practice/kana: aus dem gewaehlten Reihen-Scope werden
# REINE Kana-Woerter (Schriftform komplett Kana, KEIN Kanji) freigeschaltet und
# einzeln zufaellig abgefragt. Schreibspiel-spezifisch: Dakuten-Reihen werden MIT
# ihrer Grundreihe freigeschaltet (wer か lernt, kann auch が schreiben) — sonst
# stauten sich ~40% der Woerter erst am Schluss ("Dakuten-Klippe").
_SPELL_DAKUTEN_OF = {'k': ('g',), 's': ('z',), 't': ('d',), 'h': ('b', 'p')}
_SPELL_MIN_LEN = 2   # Ein-Mora-Woerter sind trivial
_SPELL_MAX_LEN = 6   # laengere Gruss-/Setzphrasen ueberladen die Tile-Reihe
_SPELL_WORDS_CAP = 200  # Antwort-Obergrenze (count meldet die WAHRE Gesamtzahl)


def _spell_tables(schrift):
    """Reihen-Tabellen (HIRAGANA/KATAKANA) fuer die gewaehlte Schrift."""
    from app.services.kana_rows import HIRAGANA_ROWS, KATAKANA_ROWS
    tables = []
    if schrift in ('hiragana', 'both'):
        tables.append(HIRAGANA_ROWS)
    if schrift in ('katakana', 'both'):
        tables.append(KATAKANA_ROWS)
    return tables


def _spell_allowed_chars(schrift, rows_filter):
    """Menge erlaubter Kana-Tiles fuer den Scope — mit Dakuten-Buendelung.

    rows_filter leer = alle Basis-Reihen. Fuer jede gewaehlte Grundreihe kommt
    ihre Dakuten-/Handakuten-Reihe automatisch dazu (k->g, s->z, t->d, h->b,p),
    damit die Freischalt-Kurve glatt waechst statt am Schluss zu klippen.
    """
    base = list(rows_filter) if rows_filter else list(_GUEST_BASE_ROW_KEYS)
    keys = set(base)
    for r in base:
        keys.update(_SPELL_DAKUTEN_OF.get(r, ()))
    chars = set()
    for table in _spell_tables(schrift):
        for key in keys:
            chars.update(table.get(key, ()))
    return chars


def _spell_typeable_chars(schrift):
    """Alle mit der Schrift tippbaren Kana (alle Reihen inkl. Dakuten) — fuer den
    'alle Woerter'-Modus (Reihen-Auswahl ignoriert, nur die Schrift zaehlt)."""
    chars = set()
    for table in _spell_tables(schrift):
        for chs in table.values():
            chars.update(chs)
    return chars


def _spell_word_pool(schrift, source, rows_filter):
    """Reine Kana-Woerter (N5, approved), deren SCHRIFTFORM komplett aus den
    erlaubten Kana besteht.

    Gefiltert auf `word` (NICHT `reading`): so fallen Kanji-Woerter (私) UND
    Woerter mit Klein-Kana/Chōonpu (ょ/っ/ー — nicht in den Reihen-Tabellen) in
    EINEM Praedikat raus. Fuer reine Kana-Woerter ist `word` zugleich das
    Buchstabier-Ziel.
    """
    from app.models import Vocabulary
    allowed = (_spell_typeable_chars(schrift) if source == 'all'
               else _spell_allowed_chars(schrift, rows_filter))
    if not allowed:
        return []
    rows = (
        Vocabulary.query
        .filter(Vocabulary.jlpt_level == 5, Vocabulary.status == 'approved')
        .with_entities(Vocabulary.word, Vocabulary.reading, Vocabulary.romaji,
                       Vocabulary.meaning_de, Vocabulary.audio_url)
        .all()
    )
    pool = []
    for word, reading, romaji, meaning_de, audio_url in rows:
        w = (word or '').strip()
        if not (_SPELL_MIN_LEN <= len(w) <= _SPELL_MAX_LEN):
            continue
        if any(ch not in allowed for ch in w):
            continue
        pool.append({
            'word': w,
            'reading': (reading or '').strip(),
            'romaji': (romaji or '').strip(),
            'meaning_de': (meaning_de or '').strip(),
            'audio_url': audio_url or '',
        })
    return pool


@srs_bp.route('/ueben')
def ueben_page():
    """Frueher der eigenstaendige Uebungs-Hub. Die vier Modi (Verstehen JP->DE,
    Sprechen DE->JP, Kana, Pruefen) leben jetzt direkt im „Üben"-Dropdown
    (Desktop) bzw. Bottom-Sheet (Mobile) der Navigation — keine eigene Seite mehr.
    Alte Links/Bookmarks landen per 301 auf der primaeren Wiederholung."""
    return redirect(url_for('srs.review_page'), code=301)


@srs_bp.route('/practice/kana')
def practice_kana_page():
    """Schritt 1: Einstellungs-Seite fuer das Kana-Spiel (Viewport-gesperrt).

    Sammelt die Filter und verlinkt mit den gewaehlten Werten als Query-Params
    auf die Spiel-Seite (practice_kana_game_page). Auch fuer Gaeste offen — der
    Score wird aber nur fuer eingeloggte User gespeichert (siehe /api/srs/rate).
    """
    return render_template('practice_kana.html')


@srs_bp.route('/practice/kana/spiel')
def practice_kana_game_page():
    """Schritt 2: Spiel-Seite (Viewport-gesperrt, sichtbarer Timer).

    Liest die Einstellungen client-seitig aus den Query-Params und baut die
    Session ueber /api/practice/kana/session bzw. /daily-challenge. Auch fuer
    Gaeste offen (Gast-Session via /api/practice/kana/session/public).
    """
    return render_template('practice_kana_game.html')


@srs_bp.route('/practice/kana/storm')
def practice_kana_storm_page():
    """Kana Storm: endloser Arcade-Loop gegen die Uhr (keyboard-first).

    Eigenstaendiger Spielmodus NEBEN dem Matching-Spiel (das unangetastet
    bleibt). Vollbild-Seite, viewport-gesperrt; die Komponente kanaStormGame()
    (static/js/kana_storm.js) laeuft inline (kein iframe) und zieht die Kana
    ueber den bestehenden Gast-Endpoint /api/practice/kana/session/public —
    also ohne Login spielbar, kein zweites Kana-Dataset. Bestscore lebt rein
    im localStorage des Browsers.
    """
    return render_template('practice_kana_storm.html')


@srs_bp.route('/daily')
def daily_landing():
    """Teilbare Kurz-URL fuer die Kana-Daily (aus dem geteilten Wordle-Block).

    Landet auf der Storm-Vollbildseite mit aktivem Daily-Tab. Die Frontend-
    Komponente liest `kstorm_initial_tab` aus und oeffnet den Daily-Tab.
    """
    return render_template('practice_kana_storm.html', kstorm_initial_tab='daily')


@srs_bp.route('/practice/kana/embed')
def practice_kana_embed():
    """Schlanke Embed-Variante des Spiels fuer das <iframe> auf der Startseite.

    Bewusst ohne base.html-Chrome (keine Top-Nav/Footer) und ohne Login: laeuft
    immer im Gast-Modus (kein Score-Speichern). Die Spielart waehlt der Host
    per Query-Param (?schrift=hiragana|katakana bzw. ?challenge=daily) — initView()
    in kana_grid_game.js liest sie aus und nutzt den public- bzw. Daily-Endpoint.
    Die Konto-CTA nach dem Spiel steuert die Eltern-Seite per postMessage.
    """
    return render_template('_kana_game_embed_layout.html')


@srs_bp.route('/api/practice/kana/session')
@login_required
def api_practice_session():
    """Baut on-the-fly eine Spiel-Session aus den Filtern.

    Query-Params:
        mode: 'schreiben' | 'lesen' (default 'schreiben')
        schrift: 'hiragana' | 'katakana' | 'both' (default 'both')
        rows: comma-separated row-keys (z.B. 'vowels,k,s') — leer = alle
        dakuten: 'true' | 'false' — Dakuten/Handakuten einschliessen
        yoon: 'true' | 'false' (placeholder, Yoon noch nicht im Schema)
        weak_only: 'true' — nur User-Leeches (lapses>0)
        ids: comma-separated kana-IDs — explizite Auswahl ueberschreibt andere
        limit: max Anzahl (default 20, max 50)
    """
    from app.models import CardReviewState, Kana, LessonContent

    mode = request.args.get('mode', 'schreiben')
    if mode not in ('schreiben', 'lesen'):
        mode = 'schreiben'
    schrift = request.args.get('schrift', 'both')
    if schrift not in ('hiragana', 'katakana', 'both'):
        schrift = 'both'
    rows_filter = [r.strip() for r in (request.args.get('rows', '') or '').split(',') if r.strip()]
    include_dakuten = (request.args.get('dakuten', 'true').lower() == 'true')
    weak_only = (request.args.get('weak_only', 'false').lower() == 'true')
    ids_param = request.args.get('ids', '')
    # Kein Slider mehr im UI: die Anzahl richtet sich nach der Auswahl.
    limit = _parse_limit()

    if ids_param:
        try:
            wanted_kana_ids = [int(x) for x in ids_param.split(',') if x.strip()]
        except ValueError:
            wanted_kana_ids = []
    else:
        wanted_kana_ids = None  # via Filter herauskristallisieren

    # Welche Kana darf der User ueben?
    include_locked = bool(getattr(current_user, 'is_admin', False))
    unlocked_lc_rows = _user_unlocked_kana_ids(current_user.id, include_locked=include_locked)
    unlocked_lc_ids = [r[0] for r in unlocked_lc_rows]
    if not unlocked_lc_ids and wanted_kana_ids is None:
        if weak_only:
            # weak_only braucht User-State — ohne Reviews gibt es nichts Schwaches.
            return jsonify({
                'kana': [], 'count': 0, 'mode': mode,
                'message': 'Noch keine schwachen Karten — spiel erst ein paar Runden.',
            })
        # Neukonto (0 abgeschlossene Lessons): voller Gast-Referenz-Scope statt
        # leerer Buehne. Gaeste duerfen ALLES ueben — Registrieren (der Haupt-
        # Conversion-Pfad der Startseite!) darf den spielbaren Umfang nie
        # verkleinern. lesson_content_id=None -> rateCell() skippt, kein SRS.
        payload = _guest_scope_payload(mode, schrift, rows_filter, include_dakuten, limit)
        return jsonify(payload)

    # Mapping LC-ID -> Kana
    q = (
        db.session.query(LessonContent.id, Kana)
        .join(Kana, LessonContent.content_id == Kana.id)
        .filter(LessonContent.content_type == 'kana')
        .filter(LessonContent.id.in_(unlocked_lc_ids) if unlocked_lc_ids else False)
    )
    if schrift != 'both':
        q = q.filter(Kana.type == schrift)
    if wanted_kana_ids is not None:
        q = q.filter(Kana.id.in_(wanted_kana_ids))
    rows_data = q.all()

    from app.services.kana_rows import row_for_kana
    DAKUTEN_ROWS = {'g', 'z', 'd', 'b', 'p'}

    items = []
    for lc_id, kana in rows_data:
        row_key = row_for_kana(kana.character)
        if rows_filter:
            # Explizite Reihen-Wahl uebersteuert den Dakuten-Schalter (Paritaet
            # zu _guest_kana_chars): wer G waehlt, will die G-Reihe ueben.
            if row_key not in rows_filter:
                continue
        elif not include_dakuten and row_key in DAKUTEN_ROWS:
            continue
        items.append({
            'kana_id': kana.id,
            'lesson_content_id': lc_id,
            'character': kana.character,
            'romanization': kana.romanization,
            'type': kana.type,
            'row': row_key,
            'stroke_order_info': kana.stroke_order_info,
            'mnemonic': kana.mnemonic,
        })

    # weak_only-Filter: nur Kana mit lapses > 0
    if weak_only and items:
        lc_ids = [i['lesson_content_id'] for i in items]
        states = (
            db.session.query(CardReviewState.content_id, CardReviewState.lapses)
            .filter(
                CardReviewState.user_id == current_user.id,
                CardReviewState.content_id.in_(lc_ids),
                CardReviewState.lapses > 0,
            )
            .all()
        )
        weak_lc = {s.content_id for s in states}
        items = [i for i in items if i['lesson_content_id'] in weak_lc]

    # Deduplizieren auf Kana-ID (selber Kana kann in mehreren Lessons sein)
    seen = set()
    deduped = []
    for it in items:
        if it['kana_id'] in seen:
            continue
        seen.add(it['kana_id'])
        deduped.append(it)
    items = deduped

    # Sortieren: faellige Karten zuerst, dann nach due_date asc
    if items:
        lc_ids = [i['lesson_content_id'] for i in items]
        states = (
            db.session.query(CardReviewState.content_id, CardReviewState.due_date)
            .filter(
                CardReviewState.user_id == current_user.id,
                CardReviewState.content_id.in_(lc_ids),
            )
            .all()
        )
        due_map = {s.content_id: s.due_date for s in states}
        from datetime import datetime
        far_future = datetime(2999, 1, 1)
        items.sort(key=lambda x: due_map.get(x['lesson_content_id'], far_future))

    items = items[:limit]
    return jsonify({
        'kana': items,
        'count': len(items),
        'mode': mode,
        'filters': {
            'schrift': schrift,
            'rows': rows_filter,
            'dakuten': include_dakuten,
            'weak_only': weak_only,
        },
    })


@srs_bp.route('/api/practice/kana/session/public')
def api_practice_session_public():
    """Gast-Variante der Kana-Session (Startseiten-Embed + /practice/kana ohne Login).

    Bewusst NICHT @login_required: anonyme Besucher sollen das Spiel ohne Konto
    starten koennen — mit dem vollen Uebungs-Scope (Hiragana/Katakana/beide,
    Reihen, Dakuten, alle Modi). Kein User-State: weak_only und Faelligkeits-
    Sortierung gibt es hier nicht, geschrieben wird NICHTS in die DB.
    Eingeloggte nutzen weiterhin /api/practice/kana/session (mit ihren
    freigeschalteten Kana + SRS-Sortierung). Score-Speichern laeuft ueber
    /api/srs/rate und bleibt login-pflichtig.

    Query-Params:
        mode: 'schreiben' | 'lesen' (default 'schreiben')
        schrift: 'hiragana' | 'katakana' | 'both' (default 'hiragana')
        rows: comma-separated row-keys (z.B. 'vowels,k,s') — leer = alle
        dakuten: 'true' | 'false' (default 'false')
        limit: max Anzahl (default 50, max 50 — Parity mit der Login-API)
    """
    mode = request.args.get('mode', 'schreiben')
    if mode not in ('schreiben', 'lesen'):
        mode = 'schreiben'
    schrift = request.args.get('schrift', 'hiragana')
    if schrift not in ('hiragana', 'katakana', 'both'):
        schrift = 'hiragana'
    rows_filter = [r.strip() for r in (request.args.get('rows', '') or '').split(',') if r.strip()]
    include_dakuten = (request.args.get('dakuten', 'false').lower() == 'true')
    # Default None = alles Gewaehlte; <1/fehlend faellt sicher dorthin zurueck
    # (random.sample mit negativem k waere sonst ein 500 auf public).
    limit = _parse_limit()

    payload = _guest_scope_payload(mode, schrift, rows_filter, include_dakuten, limit)
    payload['guest'] = True
    return jsonify(payload)


@srs_bp.route('/api/practice/kana/spell/words')
def api_practice_spell_words():
    """Wort-Pool fuers Kana-Schreibspiel (dritter Tab, ohne Login spielbar).

    Liefert reine Kana-Woerter, deren Schriftform mit den erlaubten Kana
    schreibbar ist. `source=all` (Default) = alle tippbaren Woerter der Schrift
    (Reihen-Auswahl ignoriert, nur Schrift zaehlt); `source=unlocked` = nur die
    mit den gewaehlten Reihen schreibbaren. `count` ist immer die WAHRE Gesamt-
    zahl (fuer den Live-Wortzaehler), `words` ein gedeckeltes Zufalls-Sample.
    Geschrieben wird NICHTS in die DB — Persistenz laeuft ueber /spell-finish.
    """
    import random as _random
    schrift = request.args.get('schrift', 'hiragana')
    if schrift not in ('hiragana', 'katakana', 'both'):
        schrift = 'hiragana'
    source = request.args.get('source', 'all')
    if source not in ('all', 'unlocked'):
        source = 'all'
    rows_filter = [r.strip() for r in (request.args.get('rows', '') or '').split(',') if r.strip()]

    pool = _spell_word_pool(schrift, source, rows_filter)
    total = len(pool)
    words = pool
    if total > _SPELL_WORDS_CAP:
        words = _random.sample(pool, _SPELL_WORDS_CAP)

    payload = {
        'words': words,
        'count': total,
        'source': source,
        'schrift': schrift,
        'guest': not current_user.is_authenticated,
    }
    if not pool:
        if source == 'unlocked':
            payload['message'] = ('Mit diesen Reihen lässt sich noch kein Wort '
                                  'schreiben — wähle mehr Reihen oder „alle Wörter".')
        else:
            payload['message'] = ('Gerade sind keine Wörter verfügbar — bitte '
                                  'später erneut versuchen.')
    return jsonify(payload)


@srs_bp.route('/api/practice/kana/daily-challenge')
def api_practice_daily_challenge():
    """Taegliche Challenge: 10 zufaellige Kana, deterministisch pro Tag.

    Eingeloggt: Seed pro (user_id, date), Quelle = freigeschaltete Kana, Bonus-XP
    bei perfektem Abschluss. Gast (ohne Login): Seed nur pro Datum, Quelle =
    komplettes Grund-Hiragana, kein Bonus-XP (kein Konto zum Gutschreiben).
    """
    import hashlib
    import random as _random
    from app.models import Kana, LessonContent
    from app.time_utils import ch_today

    # 10.8: Tagesgrenze in Europe/Zurich (der Tag, den der Nutzer sieht) —
    # konsistent mit Streak/DailyAggregate/Storm-Daily/XP-Cap. FSRS-Scheduling
    # bleibt UTC (hier irrelevant: reiner Kalendertag-Seed, kein due-Vergleich).
    today = ch_today().isoformat()

    if current_user.is_authenticated:
        seed_raw = f'{current_user.id}-{today}-daily-kana'
        include_locked = bool(getattr(current_user, 'is_admin', False))
        unlocked_lc_rows = _user_unlocked_kana_ids(current_user.id, include_locked=include_locked)
        unlocked_lc_ids = [r[0] for r in unlocked_lc_rows]
        if not unlocked_lc_ids:
            # Neukonto (0 abgeschlossene Lessons): Gast-Referenz-Scope statt
            # leerer Challenge — Registrieren darf nichts wegnehmen. Bonus-XP
            # bleibt 0 (lesson_content_id=None -> Rating/Gutschrift entfaellt,
            # ein angezeigter Bonus waere ein leeres Versprechen).
            rows = _guest_kana_rows()
            bonus_xp = 0
        else:
            rows = (
                db.session.query(LessonContent.id, Kana)
                .join(Kana, LessonContent.content_id == Kana.id)
                .filter(LessonContent.id.in_(unlocked_lc_ids))
                .all()
            )
            bonus_xp = 25  # bei perfektem Abschluss
    else:
        seed_raw = f'guest-{today}-daily-kana'
        rows = _guest_kana_rows()
        bonus_xp = 0

    # Deterministisch shufflen
    seed = int(hashlib.sha256(seed_raw.encode()).hexdigest()[:16], 16)
    rng = _random.Random(seed)
    rows = list(rows)
    rng.shuffle(rows)
    # Auf kana_id deduplizieren: dieselbe Kana kann in mehreren Lessons liegen
    # (mehrere lesson_content_ids). Zwei Felder mit derselben Kana teilen sich im
    # Grid die cell-id (`cell-<kana_id>`) -> Alpine-:key-Kollision + DOM-Konflikt,
    # eines der Doppelfelder ist dann nicht bespielbar. Vor dem Picken entdoppeln.
    seen_kana = set()
    deduped = []
    for lc_id, kana in rows:
        if kana.id in seen_kana:
            continue
        seen_kana.add(kana.id)
        deduped.append((lc_id, kana))
    picked = deduped[:10]

    # with_extras=True: mnemonic + stroke_order_info mitliefern, damit der
    # korrektive Fehler-Hinweis auch in der taeglich beworbenen Mini-Runde greift.
    items = [_kana_item(lc_id, kana, with_extras=True) for lc_id, kana in picked]

    return jsonify({
        'kana': items,
        'count': len(items),
        'bonus_xp': bonus_xp,
        'date': today,
    })


@srs_bp.route('/api/practice/kana/storm-daily')
def api_practice_storm_daily():
    """Kana-Storm-Tagesbrett: 10 Kana, pro Tag fix und fuer ALLE identisch.

    Anders als /daily-challenge (eingeloggt personalisiert) ist dieses Brett
    bewusst GLOBAL — der Seed haengt nur am Datum (nie an user_id), Quelle ist
    immer das komplette Grund-Hiragana. Nur so ist der geteilte Wordle-Vergleich
    ("ein Brett, fuer alle gleich") sinnvoll. Kein Login noetig, kein DB-Write.

    Tagesgrenze: ch_today() = Kalendertag in Europe/Zurich, konsistent mit
    /daily-challenge, dem Streak und dem XP-Cap. Das Brett wechselt fuer alle
    gleichzeitig zu CH-Mitternacht (10.8).
    """
    import hashlib
    import random as _random
    from datetime import date
    from app.time_utils import ch_today
    today = ch_today()
    today_iso = today.isoformat()
    seed = int(hashlib.sha256(f'storm-daily-{today_iso}'.encode()).hexdigest()[:16], 16)
    rng = _random.Random(seed)
    rows = list(_guest_kana_rows())  # komplettes Grund-Hiragana, global (kein user_id)
    rng.shuffle(rows)
    # Auf kana_id deduplizieren (dieselbe Kana kann in mehreren Lessons liegen).
    seen_kana = set()
    deduped = []
    for lc_id, kana in rows:
        if kana.id in seen_kana:
            continue
        seen_kana.add(kana.id)
        deduped.append((lc_id, kana))
    picked = deduped[:10]
    items = [_kana_item(lc_id, kana, with_extras=False) for lc_id, kana in picked]
    # Fortlaufende Nummer ("Kana Daily #N") ab einem fixen Stichtag — fuer alle gleich.
    # max(1, ...) verhindert 0/negative Nummern vor dem Stichtag (Tests/Server-Uhr).
    day_number = max(1, (today - date(2026, 6, 1)).days + 1)
    return jsonify({
        'kana': items,
        'count': len(items),
        'date': today_iso,
        'day_number': day_number,
    })


# ── Kana Storm: Runden-Ergebnis speichern (eingeloggt) + XP ────

_STORM_MODES = ('storm', 'daily')
_STORM_SCHRIFT = ('hiragana', 'katakana', 'both')


def _storm_clamp_int(value, lo, hi, default=0):
    """Clamped einen (vom Client gelieferten) Int-Wert hart in [lo, hi]."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


@srs_bp.route('/api/practice/kana/storm-finish', methods=['POST'])
@login_required
def api_storm_finish():
    """Persistiert eine beendete Kana-Storm-Runde + vergibt grind-sichere XP.

    Nur fuer eingeloggte Nutzer (das Frontend postet ausschliesslich, wenn
    loggedIn) — @login_required ist die harte Absicherung; Gaeste bleiben rein
    clientseitig (localStorage). score/combo/counts kommen vom Client und sind
    NICHT vertrauenswuerdig: alles wird serverseitig geclamped, und die XP
    haengen an der geclampten Trefferzahl (nicht am rohen Score), mit Per-Run-
    UND Tages-Cap (XP_STORM_*). KEIN update_daily_aggregate-Aufruf — der wuerde
    die review-semantischen Zaehler (Heatmap/Accuracy) verschmutzen.
    """
    from datetime import date
    from app.time_utils import ch_day_start_utc, ch_today

    data = request.get_json(silent=True) or {}

    mode = data.get('mode') if data.get('mode') in _STORM_MODES else 'storm'
    schrift = data.get('schrift') if data.get('schrift') in _STORM_SCHRIFT else 'hiragana'
    score = _storm_clamp_int(data.get('score'), 0, 100000)
    correct = _storm_clamp_int(data.get('correct'), 0, 2000)
    misses = _storm_clamp_int(data.get('misses'), 0, 2000)
    # Combo kann nie groesser als Treffer + 1 sein.
    best_combo = _storm_clamp_int(data.get('best_combo'), 1, correct + 1, default=1)
    duration = _storm_clamp_int(data.get('duration'), 0, 7200)

    daily_date = None
    if mode == 'daily':
        raw = (data.get('daily_date') or '').strip()
        try:
            # 10.8: Default = CH-Kalendertag (konsistent mit dem storm-daily-Brett)
            daily_date = date.fromisoformat(raw) if raw else ch_today()
        except ValueError:
            daily_date = ch_today()

    # ── XP: Basis + gedeckelter Hit-Bonus, dann harter Tages-Cap ──
    run_xp = XP_STORM_BASE + min(correct * XP_STORM_PER_HIT, XP_STORM_RUN_BONUS_CAP)
    # 10.8: Tages-Cap-Fenster = Beginn des heutigen CH-Tages, in UTC ausgedrueckt
    # (KanaStormScore.created_at wird in UTC gespeichert). So zaehlt der Cap den
    # Kalendertag, den der Nutzer sieht — nicht den UTC-Tag.
    today_start = ch_day_start_utc()
    spent_today = db.session.query(
        db.func.coalesce(db.func.sum(KanaStormScore.xp_awarded), 0)
    ).filter(
        KanaStormScore.user_id == current_user.id,
        KanaStormScore.created_at >= today_start,
    ).scalar() or 0
    granted = max(0, min(run_xp, XP_STORM_DAILY_CAP - int(spent_today)))

    db.session.add(KanaStormScore(
        user_id=current_user.id, mode=mode, schrift=schrift, duration=duration,
        score=score, best_combo=best_combo, correct_count=correct,
        miss_count=misses, xp_awarded=granted, daily_date=daily_date,
    ))
    if granted > 0:
        current_user.add_xp(granted)
    db.session.commit()

    storm_stats = srs_service.get_kana_storm_stats(current_user.id)
    return jsonify({
        'saved': True,
        'xp_awarded': granted,
        'total_xp': current_user.total_xp,
        'level': current_user.level,
        'best_score': storm_stats['best_score'],
        'best_kpm': storm_stats['best_kpm'],
        'games': storm_stats['games'],
    })


_SPELL_SOURCES = ('all', 'unlocked')
_SPELL_CUES = ('bedeutung', 'romaji', 'audio')


@srs_bp.route('/api/practice/kana/spell-finish', methods=['POST'])
@login_required
def api_spell_finish():
    """Persistiert eine beendete Kana-Schreibspiel-Runde + vergibt grind-sichere XP.

    Nur eingeloggt (das Frontend postet nur dann; @login_required ist die harte
    Absicherung). score/streak/counts kommen vom Client und werden geclamped; die
    XP haengen an der geclampten Trefferzahl mit Per-Run- UND Tages-Cap (eigenes
    Budget ueber KanaSpellScore — getrennt vom Storm-Budget). KEIN
    update_daily_aggregate — Heatmap/Accuracy + DE->JP-Produktion bleiben unberuehrt.
    """
    from app.time_utils import ch_day_start_utc
    from app.models import KanaSpellScore

    data = request.get_json(silent=True) or {}
    schrift = data.get('schrift') if data.get('schrift') in _STORM_SCHRIFT else 'hiragana'
    source = data.get('source') if data.get('source') in _SPELL_SOURCES else 'all'
    cue = data.get('cue') if data.get('cue') in _SPELL_CUES else 'bedeutung'
    score = _storm_clamp_int(data.get('score'), 0, 100000)
    correct = _storm_clamp_int(data.get('correct'), 0, 2000)
    misses = _storm_clamp_int(data.get('misses'), 0, 2000)
    best_streak = _storm_clamp_int(data.get('best_streak'), 0, correct, default=0)

    # ── XP: Basis + gedeckelter Hit-Bonus, dann harter Tages-Cap (eigene Summe) ──
    run_xp = XP_STORM_BASE + min(correct * XP_STORM_PER_HIT, XP_STORM_RUN_BONUS_CAP)
    today_start = ch_day_start_utc()
    spent_today = db.session.query(
        db.func.coalesce(db.func.sum(KanaSpellScore.xp_awarded), 0)
    ).filter(
        KanaSpellScore.user_id == current_user.id,
        KanaSpellScore.created_at >= today_start,
    ).scalar() or 0
    granted = max(0, min(run_xp, XP_STORM_DAILY_CAP - int(spent_today)))

    db.session.add(KanaSpellScore(
        user_id=current_user.id, schrift=schrift, source=source, cue=cue,
        score=score, best_streak=best_streak, correct_count=correct,
        miss_count=misses, xp_awarded=granted,
    ))
    if granted > 0:
        current_user.add_xp(granted)
    db.session.commit()

    spell_stats = srs_service.get_kana_spell_stats(current_user.id)
    return jsonify({
        'saved': True,
        'xp_awarded': granted,
        'total_xp': current_user.total_xp,
        'level': current_user.level,
        'best_score': spell_stats['best_score'],
        'best_streak': spell_stats['best_streak'],
        'games': spell_stats['games'],
    })


# ── Verwechslungs-Signal + Drill (Kana) ───────────────────────


def _record_kana_confusions(user_id, pairs):
    """Upsert des Verwechslungs-Zaehlers.

    Args:
        user_id: User-ID
        pairs: Liste von (target_kana_id, confused_kana_id)-Tupeln.

    Returns:
        Anzahl verarbeiteter Paare. Self-Confusion (target == confused) wird
        uebersprungen. Commit erfolgt durch den Aufrufer.
    """
    from datetime import datetime
    from app.models import KanaConfusion

    recorded = 0
    for target_id, confused_id in pairs:
        if not target_id or not confused_id or target_id == confused_id:
            continue
        row = KanaConfusion.query.filter_by(
            user_id=user_id, target_kana_id=target_id, confused_kana_id=confused_id
        ).first()
        if row:
            row.count = (row.count or 0) + 1
            row.last_seen = datetime.utcnow()
        else:
            db.session.add(KanaConfusion(
                user_id=user_id,
                target_kana_id=target_id,
                confused_kana_id=confused_id,
                count=1,
            ))
        recorded += 1
    return recorded


@srs_bp.route('/api/srs/kana-confusion', methods=['POST'])
@login_required
def api_kana_confusion_log():
    """Loggt, welche FALSCHEN Kana fuer ein Ziel-Kana platziert wurden
    (Fehl-Drops im Kana-Grid). Body: {confusions: [{target_kana_id, confused_kana_id}, ...]}.

    Speist den gezielten Verwechslungs-Drill (datengetriebene Distraktoren).
    """
    from app.models import Kana

    data = request.get_json(silent=True) or {}
    raw = data.get('confusions') or []
    if not isinstance(raw, list):
        return jsonify({'error': 'confusions muss eine Liste sein'}), 400

    raw = raw[:200]  # Cap gegen Missbrauch
    pairs = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            t = int(item.get('target_kana_id'))
            c = int(item.get('confused_kana_id'))
        except (TypeError, ValueError):
            continue
        pairs.append((t, c))

    # FK-Schutz: nur existierende Kana-IDs (verhindert IntegrityError auf Postgres)
    all_ids = {i for pair in pairs for i in pair}
    if all_ids:
        existing = {k.id for k in Kana.query.filter(Kana.id.in_(all_ids)).all()}
        pairs = [(t, c) for (t, c) in pairs if t in existing and c in existing]

    try:
        n = _record_kana_confusions(current_user.id, pairs)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f'Fehler bei kana-confusion-log: {e}')
        return jsonify({'error': 'Interner Fehler'}), 500
    return jsonify({'recorded': n})


@srs_bp.route('/api/practice/kana/confusion')
def api_practice_confusion():
    """Baut eine Verwechslungs-Drill-Session: optisch aehnliche Kana liegen
    als Cluster ('Reihe') zusammen im Grid, sodass die bestehende Zuordnungs-
    Mechanik die Diskrimination erzwingt.

    Quelle: kanonische CONFUSION_SETS, eingeschraenkt auf die verfuegbaren Kana.
    Eingeloggt: nur freigeschaltete Kana, priorisiert nach dem echten Per-User-
    Verwechslungssignal (KanaConfusion) und Lapses. Gast (ohne Login): komplettes
    Grund-Hiragana, generische Cluster-Reihenfolge (kein Per-User-Signal). Pro
    Kana wird stroke_order_info fuer den Spot-the-difference-Tooltip mitgeliefert.

    Query-Params: mode ('schreiben'|'lesen'), schrift, limit.
    """
    from collections import defaultdict
    from app.models import CardReviewState, Kana, KanaConfusion, LessonContent
    from app.services.kana_confusion import confusion_clusters

    mode = request.args.get('mode', 'schreiben')
    if mode not in ('schreiben', 'lesen'):
        mode = 'schreiben'
    schrift = request.args.get('schrift', 'both')
    if schrift not in ('hiragana', 'katakana', 'both'):
        schrift = 'both'
    # Confusion-Drill behaelt einen Default (ganze Cluster bis ~20 Zeichen) —
    # ein Drill ueber ALLE Cluster waere zu lang fuer eine Runde.
    limit = _parse_limit(default=20, cap=50)

    is_auth = current_user.is_authenticated

    # char -> (lc_id, kana); dedup auf Zeichen (selbe Kana evtl. in mehreren Lessons)
    by_char = {}
    if is_auth:
        include_locked = bool(getattr(current_user, 'is_admin', False))
        unlocked_lc_rows = _user_unlocked_kana_ids(current_user.id, include_locked=include_locked)
        unlocked_lc_ids = [r[0] for r in unlocked_lc_rows]
        if not unlocked_lc_ids:
            return jsonify({
                'kana': [], 'count': 0, 'mode': mode,
                'message': 'Keine freigeschalteten Kana — bitte erst eine Lesson abschliessen.',
            })
        q = (
            db.session.query(LessonContent.id, Kana)
            .join(Kana, LessonContent.content_id == Kana.id)
            .filter(LessonContent.content_type == 'kana')
            .filter(LessonContent.id.in_(unlocked_lc_ids))
        )
        if schrift != 'both':
            q = q.filter(Kana.type == schrift)
        for lc_id, kana in q.all():
            by_char.setdefault(kana.character, (lc_id, kana))
    else:
        # Gast: voller Referenz-Scope (inkl. Dakuten — Paare wie ば/ぱ brauchen
        # sie), Schrift-Filter wie bei Eingeloggten. Kein User-State.
        for lc_id, kana in _guest_kana_rows(schrift=schrift, include_dakuten=True):
            by_char.setdefault(kana.character, (lc_id, kana))

    clusters = confusion_clusters(set(by_char.keys()))
    if not clusters:
        return jsonify({
            'kana': [], 'count': 0, 'mode': mode,
            'message': 'Noch keine verwechselbaren Paare freigeschaltet — ueb weiter, '
                       'dann schalten sich Paare frei.',
        })

    kana_id_by_char = {ch: kana.id for ch, (lc_id, kana) in by_char.items()}
    lc_id_by_char = {ch: lc_id for ch, (lc_id, kana) in by_char.items()}

    # ── Priorisierung: echtes User-Signal (KanaConfusion) stark, Lapses schwach.
    #    Fuer Gaeste bleiben beide leer -> generische CONFUSION_SETS-Reihenfolge. ──
    confusion_score_by_kana = defaultdict(int)
    lapses_by_lc = {}
    if is_auth:
        conf_rows = (
            db.session.query(
                KanaConfusion.target_kana_id, KanaConfusion.confused_kana_id, KanaConfusion.count
            )
            .filter(KanaConfusion.user_id == current_user.id)
            .all()
        )
        for tgt, conf, cnt in conf_rows:
            confusion_score_by_kana[tgt] += (cnt or 0)
            confusion_score_by_kana[conf] += (cnt or 0)

        valid_lc_ids = [v for v in lc_id_by_char.values() if v is not None]
        if valid_lc_ids:
            states = (
                db.session.query(CardReviewState.content_id, CardReviewState.lapses)
                .filter(
                    CardReviewState.user_id == current_user.id,
                    CardReviewState.content_id.in_(valid_lc_ids),
                )
                .all()
            )
            lapses_by_lc = {cid: (lap or 0) for cid, lap in states}

    def cluster_score(members):
        score = 0
        for ch in members:
            score += confusion_score_by_kana.get(kana_id_by_char.get(ch), 0) * 10
            score += lapses_by_lc.get(lc_id_by_char.get(ch), 0)
        return score

    clusters.sort(key=cluster_score, reverse=True)

    # Ganze Cluster auffuellen bis ~limit (keine zerschnittenen Cluster)
    items = []
    labels = {}
    used_chars = set()
    for idx, members in enumerate(clusters):
        fresh = [c for c in members if c not in used_chars]
        if len(fresh) < 2:
            continue
        if items and len(items) + len(fresh) > limit:
            break
        key = f'cf_{idx}'
        labels[key] = '・'.join(fresh)
        for ch in fresh:
            lc_id, kana = by_char[ch]
            used_chars.add(ch)
            items.append(_kana_item(lc_id, kana, row_key=key))

    return jsonify({
        'kana': items,
        'count': len(items),
        'mode': mode,
        'row_labels': labels,
        'layout': 'confusion',
    })


# ── Kana-Grid-Spiel (Phase 1) ─────────────────────────────────


@srs_bp.route('/api/kana-grid/<int:content_id>/config')
def api_kana_grid_config(content_id):
    """Liefert Konfiguration eines Kana-Grid-Spiels (Drag-Drop).

    Bewusst NICHT @login_required — Lesson-Zugriff wird ueber
    Lesson.is_accessible_to_user(current_user) geprueft. Gaeste auf
    guest-zugaenglichen Lessons sollen das Spiel auch starten koennen
    (Ratings via /api/srs/rate brauchen aber weiterhin Login).
    """
    from app.models import KanaGridConfig, Kana, Lesson, LessonContent
    from app.services.kana_rows import kana_rows_for_lesson, ROMAJI_ROWS

    content = LessonContent.query.get(content_id)
    if not content or content.content_type != 'kana_grid_game':
        return jsonify({'error': 'Spiel nicht gefunden'}), 404

    lesson = Lesson.query.get(content.lesson_id)
    if not lesson:
        return jsonify({'error': 'Lektion nicht gefunden'}), 404

    # current_user kann AnonymousUserMixin sein — is_accessible_to_user
    # toleriert das (Guest-Pfad)
    user_for_check = current_user if current_user.is_authenticated else None
    accessible, _msg = lesson.is_accessible_to_user(user_for_check)
    if not accessible:
        return jsonify({'error': 'Kein Zugriff'}), 403

    config = KanaGridConfig.query.filter_by(lesson_content_id=content_id).first()
    if not config:
        return jsonify({'error': 'Spiel-Konfiguration fehlt'}), 404

    kana_ids = config.kana_ids or []
    kana_objs = Kana.query.filter(Kana.id.in_(kana_ids)).all() if kana_ids else []
    # Reihenfolge wie in config.kana_ids erhalten (Datenbank-Reihenfolge ist nicht garantiert)
    id_to_obj = {k.id: k for k in kana_objs}
    ordered = [id_to_obj[i] for i in kana_ids if i in id_to_obj]

    # Mapping Kana-ID -> LessonContent-ID (fuer FSRS-Anbindung). Wir suchen
    # innerhalb der Lesson nach kana-Items mit passender content_id.
    lc_for_kana = {}
    kana_contents = LessonContent.query.filter_by(
        lesson_id=lesson.id, content_type='kana'
    ).all()
    for lc in kana_contents:
        if lc.content_id in kana_ids and lc.content_id not in lc_for_kana:
            lc_for_kana[lc.content_id] = lc.id

    grouped = kana_rows_for_lesson(ordered)
    rows_payload = []
    for group in grouped:
        rows_payload.append({
            'key': group['key'],
            'label': group['label'],
            'romaji': ROMAJI_ROWS.get(group['key'], []),
            'kana_ids': [k.id for k in group['kana']],
        })

    return jsonify({
        'content_id': content.id,
        'lesson_id': lesson.id,
        'lesson_title': lesson.title,
        'kana': [
            {
                'id': k.id,
                'character': k.character,
                'romanization': k.romanization,
                'type': k.type,
                'audio_url': k.example_sound_url,
                'lesson_content_id': lc_for_kana.get(k.id),  # fuer /api/srs/rate
                'stroke_order_info': k.stroke_order_info,
                'mnemonic': k.mnemonic,
            }
            for k in ordered
        ],
        'rows': rows_payload,
        'config': {
            'default_mode': config.default_mode,
            'allow_mode_switch': config.allow_mode_switch,
            'grid_layout': config.grid_layout,
            'shuffle_pool': config.shuffle_pool,
            'timer_enabled': config.timer_enabled,
            'max_hints': config.max_hints,
            'show_romaji_hint_on_pool': config.show_romaji_hint_on_pool,
        },
    })

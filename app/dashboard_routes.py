# app/dashboard_routes.py
"""Lernenden-Dashboard „Mein Lernen" (japanese-learning.ch).

Eigenes Blueprint (NICHT srs_bp), damit die vielen Dashboard-Endpoints und
die Seiten-Route nicht denselben Datei-Hotspot (srs_routes.py) teilen — das
maximiert die parallele Bearbeitung der einzelnen Tracks.

Spine-Stand: liefert nur das stabile Seiten-Geruest + Basis-KPIs (Streak,
Level, faellige Karten). Die reichen Datenfelder (adaptiver Plan, Kompass-
Saeulen, Statistik-Tabs) werden in spaeteren Tracks gegen den eingefrorenen
Daten-Vertrag (docs/dashboard_contract.md) ergaenzt — teils server-gerendert
in diesen Context, teils lazy per /api/dashboard/* gefetcht.
"""
import logging

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app import dashboard_service, srs_service

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/mein-lernen')
def index():
    """„Mein Lernen"-Dashboard.

    Gast-Gating wie die uebrigen Lern-Seiten (review/stats/browse): kein
    harter Login-Redirect, sondern die weiche Teaser-Landing.
    """
    if not current_user.is_authenticated:
        return render_template('review_teaser.html', teaser_page='dashboard')

    # Basis-KPIs (server-gerendert, sofort sichtbar) — identische Quelle wie
    # /review/stats, damit Streak/Level/Faellig konsistent sind.
    stats = srs_service.get_user_stats(current_user.id)
    stats['current_streak'] = current_user.current_streak or 0
    stats['longest_streak'] = current_user.longest_streak or 0
    level = current_user.level or 1
    total_xp = current_user.total_xp or 0
    stats['level'] = level
    stats['total_xp'] = total_xp
    stats['level_title'] = current_user.level_title

    # Pro-Level-Fortschritt (Boden des aktuellen Levels abziehen — sonst
    # uebertreibt der Anteil bei hoeheren Levels; vgl. srs_routes.stats_page).
    xp_next = current_user.xp_for_next_level
    xp_floor = int(100 * ((level - 1) ** 1.5))
    span = max(1, xp_next - xp_floor)
    in_level = max(0, total_xp - xp_floor)
    stats['xp_next_level'] = xp_next
    stats['xp_to_next'] = max(0, xp_next - total_xp)
    stats['level_progress_pct'] = max(0, min(100, round(in_level / span * 100)))

    # N5-Kompass (server-gerendert): 4 echte Saeulen + Zahlen-Kacheln.
    pillars = dashboard_service.compass_pillars(current_user.id)
    numbers = dashboard_service.learner_numbers(current_user.id)

    return render_template(
        'learner_dashboard.html',
        stats=stats,
        pillars=pillars,
        numbers=numbers,
    )


@dashboard_bp.route('/api/dashboard/compass-glyphs')
@login_required
def api_compass_glyphs():
    """Per-Glyph-Detail (Lern-Landkarte) fuer kana/kanji.

    Query: type = kana | kanji. Lazy gefetcht, wenn die Saeule aufgeklappt wird.
    """
    content_type = request.args.get('type', 'kana')
    if content_type not in ('kana', 'kanji'):
        return jsonify({'data': [], 'count': 0})
    data = dashboard_service.compass_glyphs(current_user.id, content_type)
    return jsonify({'data': data, 'count': len(data)})

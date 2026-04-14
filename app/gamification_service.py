# app/gamification_service.py
"""Gamification: XP-Berechnung, Karten-Stufen, DailyAggregate."""
import json
import logging
from datetime import datetime

from app import db
from app.models import DailyReviewAggregate

logger = logging.getLogger(__name__)

# ── XP-Tabelle ────────────────────────────────────────────────

XP_PER_RATING = {1: 2, 2: 5, 3: 10, 4: 12}
XP_NEW_CARD_BONUS = 15
XP_STREAK_DAY = 20
XP_PERFECT_SESSION = 50

# ── Karten-Stufen (basierend auf FSRS Stability) ─────────────

CARD_STAGES = [
    # (min_stability_days, name, color)
    (365, 'Gemeistert', '#2ecc71'),
    (180, 'Erleuchtet', '#f1c40f'),
    (90, 'Meister', '#9b59b6'),
    (30, 'Vertraut 2', '#009432'),
    (14, 'Vertraut 1', '#6ab04c'),
    (7, 'Anfaenger 4', '#ffbe76'),
    (3, 'Anfaenger 3', '#f0932b'),
    (1, 'Anfaenger 2', '#ee5a24'),
    (0.17, 'Anfaenger 1', '#ff6b6b'),
    (0, 'Neu', '#6c757d'),
]

STAGE_GEMEISTERT = 0  # Index in CARD_STAGES (hoechste Stufe zuerst)


def calculate_xp(rating_int, is_new_card=False):
    """Berechnet XP fuer einen einzelnen Review."""
    xp = XP_PER_RATING.get(rating_int, 0)
    if is_new_card:
        xp += XP_NEW_CARD_BONUS
    return xp


def get_card_stage(fsrs_card_json):
    """Bestimmt die SRS-Stufe basierend auf FSRS Stability.

    Args:
        fsrs_card_json: JSON-String oder dict des FSRS Card State

    Returns:
        tuple: (stage_index, stage_name, color)
        stage_index: 0=Neu, 9=Gemeistert
    """
    if not fsrs_card_json:
        return (0, 'Neu', '#6c757d')

    try:
        if isinstance(fsrs_card_json, str):
            state = json.loads(fsrs_card_json)
        else:
            state = fsrs_card_json
        stability = state.get('stability', 0) or 0
    except (json.JSONDecodeError, AttributeError):
        return (0, 'Neu', '#6c757d')

    # CARD_STAGES ist absteigend sortiert, erste Uebereinstimmung gewinnt
    for i, (min_stab, name, color) in enumerate(CARD_STAGES):
        if stability >= min_stab:
            # stage_index: 9 (Gemeistert) bis 0 (Neu)
            stage_index = len(CARD_STAGES) - 1 - i
            return (stage_index, name, color)

    return (0, 'Neu', '#6c757d')


def update_daily_aggregate(user_id, rating_int, time_taken_ms, xp_earned,
                           is_new=False, leveled_up=False, leveled_down=False):
    """Aktualisiert die taeglich aggregierten Review-Statistiken (inkrementell)."""
    today = datetime.utcnow().date()

    agg = DailyReviewAggregate.query.filter_by(
        user_id=user_id, review_date=today
    ).first()

    if not agg:
        agg = DailyReviewAggregate(user_id=user_id, review_date=today)
        db.session.add(agg)

    agg.total_reviews = (agg.total_reviews or 0) + 1
    if rating_int >= 3:
        agg.correct_reviews = (agg.correct_reviews or 0) + 1

    rating_fields = {1: 'again_count', 2: 'hard_count', 3: 'good_count', 4: 'easy_count'}
    field = rating_fields.get(rating_int)
    if field:
        setattr(agg, field, (getattr(agg, field) or 0) + 1)

    agg.total_time_ms = (agg.total_time_ms or 0) + (time_taken_ms or 0)
    agg.xp_earned = (agg.xp_earned or 0) + xp_earned

    if is_new:
        agg.new_cards_learned = (agg.new_cards_learned or 0) + 1
    if leveled_up:
        agg.cards_leveled_up = (agg.cards_leveled_up or 0) + 1
    if leveled_down:
        agg.cards_leveled_down = (agg.cards_leveled_down or 0) + 1

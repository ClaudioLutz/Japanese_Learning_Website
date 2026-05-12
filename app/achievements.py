# app/achievements.py
"""Achievement-Definitionen fuer das Gamification-System.

Achievements werden im Code definiert (nicht DB), damit Aenderungen
ohne Migration moeglich sind. Die DB speichert nur freigeschaltete Keys.
"""
import logging

from app import db
from app.models import UserAchievement

logger = logging.getLogger(__name__)

# ── Achievement-Definitionen ──────────────────────────────────

ACHIEVEMENTS = {
    # ── Konsistenz (Streak) ──
    'streak_3': {
        'name': 'Erste Schritte',
        'description': '3 Tage Streak',
        'icon': 'fa-seedling',
        'category': 'konsistenz',
        'rarity': 'common',
        'check': lambda u, ctx: (u.current_streak or 0) >= 3,
    },
    'streak_7': {
        'name': 'Bestaendig',
        'description': '7 Tage Streak',
        'icon': 'fa-leaf',
        'category': 'konsistenz',
        'rarity': 'common',
        'check': lambda u, ctx: (u.current_streak or 0) >= 7,
    },
    'streak_30': {
        'name': 'Unaufhaltsam',
        'description': '30 Tage Streak',
        'icon': 'fa-tree',
        'category': 'konsistenz',
        'rarity': 'uncommon',
        'check': lambda u, ctx: (u.current_streak or 0) >= 30,
    },
    'streak_100': {
        'name': 'Ausdauer-Meister',
        'description': '100 Tage Streak',
        'icon': 'fa-mountain',
        'category': 'konsistenz',
        'rarity': 'rare',
        'check': lambda u, ctx: (u.current_streak or 0) >= 100,
    },
    'streak_365': {
        'name': 'Unerschuetterlich',
        'description': '365 Tage Streak',
        'icon': 'fa-volcano',
        'category': 'konsistenz',
        'rarity': 'legendary',
        'check': lambda u, ctx: (u.current_streak or 0) >= 365,
    },

    # ── Volumen (Reviews) ──
    'reviews_1': {
        'name': 'Erster Review',
        'description': '1 Review abgeschlossen',
        'icon': 'fa-book-open',
        'category': 'volumen',
        'rarity': 'common',
        'check': lambda u, ctx: (u.total_reviews or 0) >= 1,
    },
    'reviews_100': {
        'name': 'Fleissig',
        'description': '100 Reviews abgeschlossen',
        'icon': 'fa-books',
        'category': 'volumen',
        'rarity': 'common',
        'check': lambda u, ctx: (u.total_reviews or 0) >= 100,
    },
    'reviews_500': {
        'name': 'Lernmaschine',
        'description': '500 Reviews abgeschlossen',
        'icon': 'fa-graduation-cap',
        'category': 'volumen',
        'rarity': 'uncommon',
        'check': lambda u, ctx: (u.total_reviews or 0) >= 500,
    },
    'reviews_1000': {
        'name': 'Review-Maschine',
        'description': "1'000 Reviews abgeschlossen",
        'icon': 'fa-bolt',
        'category': 'volumen',
        'rarity': 'uncommon',
        'check': lambda u, ctx: (u.total_reviews or 0) >= 1000,
    },
    'reviews_5000': {
        'name': 'Unersaettlich',
        'description': "5'000 Reviews abgeschlossen",
        'icon': 'fa-fire',
        'category': 'volumen',
        'rarity': 'rare',
        'check': lambda u, ctx: (u.total_reviews or 0) >= 5000,
    },
    'reviews_10000': {
        'name': 'Lernlegende',
        'description': "10'000 Reviews abgeschlossen",
        'icon': 'fa-gem',
        'category': 'volumen',
        'rarity': 'legendary',
        'check': lambda u, ctx: (u.total_reviews or 0) >= 10000,
    },

    # ── Meisterschaft (Gemeisterte Karten) ──
    'mastered_1': {
        'name': 'Erste Meisterung',
        'description': '1 Karte gemeistert',
        'icon': 'fa-star',
        'category': 'meisterschaft',
        'rarity': 'common',
        'check': lambda u, ctx: (u.total_mastered or 0) >= 1,
    },
    'mastered_10': {
        'name': 'Zehn Gemeistert',
        'description': '10 Karten gemeistert',
        'icon': 'fa-stars',
        'category': 'meisterschaft',
        'rarity': 'uncommon',
        'check': lambda u, ctx: (u.total_mastered or 0) >= 10,
    },
    'mastered_50': {
        'name': 'Fuenfzig Gemeistert',
        'description': '50 Karten gemeistert',
        'icon': 'fa-crown',
        'category': 'meisterschaft',
        'rarity': 'rare',
        'check': lambda u, ctx: (u.total_mastered or 0) >= 50,
    },
    'mastered_100': {
        'name': 'Hundert Gemeistert',
        'description': '100 Karten gemeistert',
        'icon': 'fa-trophy',
        'category': 'meisterschaft',
        'rarity': 'rare',
        'check': lambda u, ctx: (u.total_mastered or 0) >= 100,
    },

    # ── Session ──
    'perfect_session': {
        'name': 'Perfekte Session',
        'description': 'Alle Karten einer Session mit Gut/Einfach bewertet',
        'icon': 'fa-bullseye',
        'category': 'session',
        'rarity': 'uncommon',
        'check': lambda u, ctx: ctx.get('perfect_session', False),
    },
    'kana_first_perfect_grid': {
        'name': 'Erste Kana-Tabelle',
        'description': 'Drag-Drop-Spiel ohne Fehler abgeschlossen',
        'icon': 'fa-th',
        'category': 'session',
        'rarity': 'common',
        'check': lambda u, ctx: ctx.get('perfect_kana_grid', False),
    },

    # ── Phase 2: Kana-spezifische Meisterschaft ──
    'kana_vowels_mastered': {
        'name': 'Vokale gemeistert',
        'description': 'Alle 5 Hiragana-Vokale auf Stufe Meister oder hoeher',
        'icon': 'fa-spa',
        'category': 'meisterschaft',
        'rarity': 'rare',
        'check': lambda u, ctx: ctx.get('kana_vowels_mastered', False),
    },
    'kana_hiragana_50': {
        'name': '50 Hiragana erlernt',
        'description': '50 Hiragana mindestens auf Stufe "Vertraut 1"',
        'icon': 'fa-feather',
        'category': 'meisterschaft',
        'rarity': 'uncommon',
        'check': lambda u, ctx: ctx.get('kana_hiragana_50', False),
    },
    'kana_katakana_50': {
        'name': '50 Katakana erlernt',
        'description': '50 Katakana mindestens auf Stufe "Vertraut 1"',
        'icon': 'fa-pen-fancy',
        'category': 'meisterschaft',
        'rarity': 'uncommon',
        'check': lambda u, ctx: ctx.get('kana_katakana_50', False),
    },
    'kana_perfect_streak_5': {
        'name': 'Tabellen-Champion',
        'description': '5 Kana-Spiele in Folge ohne Fehler',
        'icon': 'fa-medal',
        'category': 'session',
        'rarity': 'rare',
        'check': lambda u, ctx: ctx.get('perfect_kana_grid_streak', 0) >= 5,
    },

    # ── Level ──
    'level_5': {
        'name': 'Schüler',
        'description': 'Level 5 erreicht',
        'icon': 'fa-user-graduate',
        'category': 'level',
        'rarity': 'common',
        'check': lambda u, ctx: (u.level or 1) >= 5,
    },
    'level_10': {
        'name': 'Kenner',
        'description': 'Level 10 erreicht',
        'icon': 'fa-hat-wizard',
        'category': 'level',
        'rarity': 'uncommon',
        'check': lambda u, ctx: (u.level or 1) >= 10,
    },
    'level_25': {
        'name': 'Fortgeschritten',
        'description': 'Level 25 erreicht',
        'icon': 'fa-chess-knight',
        'category': 'level',
        'rarity': 'rare',
        'check': lambda u, ctx: (u.level or 1) >= 25,
    },
}


def check_achievements(user, context=None):
    """Prueft alle Achievements und gibt neu freigeschaltete zurueck.

    Args:
        user: User-Objekt
        context: dict mit Session-spezifischen Daten (z.B. perfect_session)

    Returns:
        list of dicts: [{key, name, icon, description}, ...]
    """
    ctx = context or {}
    existing = {a.achievement_key for a in UserAchievement.query.filter_by(user_id=user.id).all()}

    newly_unlocked = []
    for key, defn in ACHIEVEMENTS.items():
        if key in existing:
            continue
        try:
            if defn['check'](user, ctx):
                achievement = UserAchievement(
                    user_id=user.id,
                    achievement_key=key,
                    notified=False,
                )
                db.session.add(achievement)
                newly_unlocked.append({
                    'key': key,
                    'name': defn['name'],
                    'icon': defn['icon'],
                    'description': defn['description'],
                })
        except Exception as e:
            logger.warning(f'Achievement-Check fehlgeschlagen fuer {key}: {e}')

    return newly_unlocked

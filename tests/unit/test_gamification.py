# tests/unit/test_gamification.py
"""Unit-Tests fuer Gamification: XP, Level, Achievements, Karten-Stufen."""
from app.gamification_service import calculate_xp, get_card_stage, XP_PER_RATING, XP_NEW_CARD_BONUS
from app.achievements import ACHIEVEMENTS, check_achievements
from app.models import User, UserAchievement
from app import db


class TestXPCalculation:
    """XP-Berechnung pro Rating."""

    def test_xp_again(self, app):
        assert calculate_xp(1) == 2

    def test_xp_hard(self, app):
        assert calculate_xp(2) == 5

    def test_xp_good(self, app):
        assert calculate_xp(3) == 10

    def test_xp_easy(self, app):
        assert calculate_xp(4) == 12

    def test_xp_new_card_bonus(self, app):
        assert calculate_xp(3, is_new_card=True) == 10 + 15

    def test_xp_new_card_again(self, app):
        assert calculate_xp(1, is_new_card=True) == 2 + 15


class TestLevelSystem:
    """Level-Up-Logik via User.add_xp()."""

    def test_level_starts_at_1(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()
        assert user.level == 1
        assert user.total_xp == 0

    def test_add_xp_increments(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()
        user.add_xp(50)
        assert user.total_xp == 50
        assert user.level == 1  # 100 XP fuer Level 2

    def test_level_up(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()
        user.add_xp(100)  # Level 1 → 2 (Schwelle: 100)
        assert user.level == 2

    def test_xp_for_next_level_polynomial(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()
        # Level 1: 100 * 1^1.5 = 100
        assert user.xp_for_next_level == 100
        user.level = 5
        # Level 5: 100 * 5^1.5 = 1118
        assert user.xp_for_next_level == 1118

    def test_level_title(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()
        # Umlaute korrekt (siehe Mayuko-Direktive: keine ASCII-Fallbacks)
        assert 'Anfänger' in user.level_title
        user.level = 10
        assert 'Schüler' in user.level_title
        user.level = 50
        assert 'Meister' in user.level_title
        user.level = 51
        assert 'Grossmeister' in user.level_title


class TestCardStages:
    """Karten-Stufen basierend auf FSRS Stability."""

    def test_new_card(self, app):
        stage_idx, name, color = get_card_stage(None)
        assert stage_idx == 0
        assert name == 'Neu'

    def test_empty_json(self, app):
        stage_idx, name, _ = get_card_stage('{}')
        assert stage_idx == 0
        assert name == 'Neu'

    def test_low_stability(self, app):
        stage_idx, name, _ = get_card_stage('{"stability": 0.5}')
        assert stage_idx == 1
        assert 'Anfänger 1' in name

    def test_medium_stability(self, app):
        stage_idx, name, _ = get_card_stage('{"stability": 20.0}')
        assert stage_idx == 5
        assert 'Vertraut' in name

    def test_high_stability(self, app):
        stage_idx, name, _ = get_card_stage('{"stability": 400.0}')
        assert stage_idx == 9
        assert 'Gemeistert' in name

    def test_stability_thresholds(self, app):
        """Alle Schwellenwerte pruefen."""
        test_cases = [
            (0.1, 0, 'Neu'),
            (0.5, 1, 'Anfänger 1'),
            (2.0, 2, 'Anfänger 2'),
            (5.0, 3, 'Anfänger 3'),
            (10.0, 4, 'Anfänger 4'),
            (20.0, 5, 'Vertraut 1'),
            (50.0, 6, 'Vertraut 2'),
            (100.0, 7, 'Meister'),
            (200.0, 8, 'Erleuchtet'),
            (365.0, 9, 'Gemeistert'),
        ]
        for stability, expected_idx, expected_name in test_cases:
            idx, name, _ = get_card_stage(f'{{"stability": {stability}}}')
            assert idx == expected_idx, f'stability={stability}: expected stage {expected_idx}, got {idx}'
            assert name == expected_name, f'stability={stability}: expected {expected_name}, got {name}'


class TestAchievements:
    """Achievement-Check und Idempotenz."""

    def test_achievement_definitions_exist(self, app):
        assert len(ACHIEVEMENTS) > 10
        for key, defn in ACHIEVEMENTS.items():
            assert 'name' in defn
            assert 'icon' in defn
            assert 'check' in defn
            assert 'category' in defn

    def test_streak_achievement_unlocks(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        user.current_streak = 7
        db.session.commit()

        unlocked = check_achievements(user)
        keys = [a['key'] for a in unlocked]
        assert 'streak_3' in keys
        assert 'streak_7' in keys
        assert 'streak_30' not in keys

    def test_volume_achievement(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        user.total_reviews = 100
        db.session.commit()

        unlocked = check_achievements(user)
        keys = [a['key'] for a in unlocked]
        assert 'reviews_1' in keys
        assert 'reviews_100' in keys

    def test_achievement_not_duplicated(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        user.current_streak = 7
        db.session.commit()

        # Erstes Mal
        unlocked1 = check_achievements(user)
        db.session.commit()
        assert len(unlocked1) > 0

        # Zweites Mal: keine Duplikate
        unlocked2 = check_achievements(user)
        assert len(unlocked2) == 0

    def test_perfect_session_context(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()

        unlocked = check_achievements(user, context={'perfect_session': True})
        keys = [a['key'] for a in unlocked]
        assert 'perfect_session' in keys

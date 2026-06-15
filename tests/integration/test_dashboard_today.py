"""Tests fuer Heute-Hero (Plan/Wochenziel/Freezes), Can-do und die
Kompass-Detailmaps Vokabel-Themen / Grammatik-Liste.
"""
from datetime import datetime

from app import dashboard_service, db
from app.models import UserLessonProgress, UserSRSSettings
from tests.factories import (
    CardReviewStateFactory,
    DailyReviewAggregateFactory,
    GrammarFactory,
    LessonCategoryFactory,
    LessonContentFactory,
    LessonFactory,
    VocabularyFactory,
)


class TestWeekGoal:
    def test_counts_active_days(self, auth_client):
        _client, user = auth_client
        DailyReviewAggregateFactory(user_id=user.id, review_date=datetime.utcnow().date(), total_reviews=5)
        db.session.commit()
        wg = dashboard_service.week_goal(user.id)
        assert wg['total'] == 7
        assert wg['done'] >= 1


class TestFreezes:
    def test_caps_at_one(self, auth_client):
        _client, user = auth_client
        db.session.add(UserSRSSettings(user_id=user.id, streak_freezes_available=5))
        db.session.commit()
        assert dashboard_service.streak_freezes(user.id) == 1

    def test_zero_without_settings(self, auth_client):
        _client, user = auth_client
        assert dashboard_service.streak_freezes(user.id) == 0


class TestNextLesson:
    def test_resume_not_completed(self, auth_client):
        _client, user = auth_client
        lesson = LessonFactory(is_published=True, title='Café')
        db.session.add(UserLessonProgress(user_id=user.id, lesson_id=lesson.id, is_completed=False))
        db.session.commit()
        nl = dashboard_service.next_lesson(user.id)
        assert nl['lesson_id'] == lesson.id
        assert nl['kind'] == 'resume'

    def test_next_when_nothing_started(self, auth_client):
        _client, user = auth_client
        lesson = LessonFactory(is_published=True, title='Erste Lektion', order_index=0)
        db.session.commit()
        nl = dashboard_service.next_lesson(user.id)
        assert nl['lesson_id'] == lesson.id
        assert nl['kind'] == 'next'


class TestBuildPlan:
    def test_review_step_present(self, app, auth_client):
        _client, user = auth_client
        with app.test_request_context():
            plan, minutes = dashboard_service.build_plan(user.id, 8)
        assert any(s['kind'] == 'review' for s in plan)
        assert all('href' in s and 'done' in s for s in plan)
        assert minutes >= 1

    def test_fallback_when_empty(self, app, auth_client):
        _client, user = auth_client
        with app.test_request_context():
            plan, minutes = dashboard_service.build_plan(user.id, 0)
        # ohne due/Lektion/Schwaechen: mind. der Fallback-Schritt
        assert len(plan) >= 1


class TestCanDo:
    def test_status_from_completed_lessons(self, auth_client):
        _client, user = auth_client
        # 3 abgeschlossene Lektionen
        for i in range(3):
            lesson = LessonFactory(is_published=True)
            db.session.add(UserLessonProgress(user_id=user.id, lesson_id=lesson.id, is_completed=True))
        db.session.commit()
        cd = dashboard_service.can_do(user.id)
        assert len(cd) == len(dashboard_service._CAN_DO)
        # Statements mit threshold <= 3 sind 'done'
        assert cd[0]['s'] == 'done'
        # alle Status gueltig
        assert all(c['s'] in ('done', 'prog', 'open') for c in cd)


class TestGrammarList:
    def test_level_from_stage(self, auth_client):
        _client, user = auth_client
        lesson = LessonFactory()
        gram = GrammarFactory(title='〜です', structure='N です')
        content = LessonContentFactory(lesson_id=lesson.id, content_type='grammar', content_id=gram.id)
        db.session.commit()
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        db.session.commit()
        gl = dashboard_service.grammar_list(user.id)
        assert len(gl) == 1
        assert gl[0]['pat'] == '〜です'
        assert 0 <= gl[0]['level'] <= 3


class TestVocabThemes:
    def test_have_total_per_category(self, auth_client):
        _client, user = auth_client
        cat = LessonCategoryFactory(name='Begrüssungen')
        lesson = LessonFactory(is_published=True, category_id=cat.id)
        v1 = VocabularyFactory()
        v2 = VocabularyFactory()
        c1 = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=v1.id)
        LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=v2.id)
        db.session.commit()
        CardReviewStateFactory(user_id=user.id, content_id=c1.id)  # 1 von 2 begonnen
        db.session.commit()
        themes = dashboard_service.vocab_themes(user.id)
        begr = next((t for t in themes if t['name'] == 'Begrüssungen'), None)
        assert begr is not None
        assert begr['total'] == 2
        assert begr['have'] == 1


class TestDashboardPageFullContext:
    def test_page_renders_with_all_real_context(self, auth_client):
        """GET /mein-lernen rendert mit vollem echten Context (Plan/Themen/Can-do)."""
        client, _user = auth_client
        resp = client.get('/mein-lernen')
        assert resp.status_code == 200
        assert b'N5-Kompass' in resp.data

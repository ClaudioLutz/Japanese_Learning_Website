"""Tests fuer den N5-Kompass des Lernenden-Dashboards.

dashboard_service: maturity_by_type / compass_pillars / learner_numbers /
compass_glyphs + Endpoint /api/dashboard/compass-glyphs.
"""
from app import dashboard_service, db
from tests.factories import (
    CardReviewStateFactory,
    KanjiFactory,
    LessonContentFactory,
    LessonFactory,
    ReviewLogFactory,
    UserLessonProgressFactory,
    VocabularyFactory,
)


def _listen_lesson(content_type='audio'):
    """Publizierte Lektion mit Hoer-Inhalt (audio/dialog_slideshow)."""
    lesson = LessonFactory(is_published=True)
    LessonContentFactory(lesson_id=lesson.id, content_type=content_type)
    db.session.commit()
    return lesson


def _vocab_card(user_id):
    lesson = LessonFactory()
    vocab = VocabularyFactory()
    content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.commit()
    CardReviewStateFactory(user_id=user_id, content_id=content.id)
    db.session.commit()
    return content


def _kanji_card(user_id, **kanji_kwargs):
    lesson = LessonFactory()
    kanji = KanjiFactory(**kanji_kwargs)
    content = LessonContentFactory(lesson_id=lesson.id, content_type='kanji', content_id=kanji.id)
    db.session.commit()
    CardReviewStateFactory(user_id=user_id, content_id=content.id, reps=4)
    ReviewLogFactory(user_id=user_id, content_id=content.id, rating=3)
    db.session.commit()
    return content


class TestCompassService:
    def test_pillars_five_with_listen(self, auth_client):
        """5 Saeulen in v3-Reihenfolge inkl. „listen" (Hoeren); korrekte Form."""
        _client, user = auth_client
        pillars = dashboard_service.compass_pillars(user.id)
        keys = [p['key'] for p in pillars]
        assert keys == ['kana', 'vocab', 'kanji', 'grammar', 'listen']
        for p in pillars:
            assert len(p['dist']) == 5
            assert p['total'] >= 1
            assert {'key', 'name', 'icon', 'targetPct', 'cta', 'started', 'total', 'dist', 'sowhat'} <= set(p.keys())

    def test_maturity_by_type_counts_card(self, auth_client):
        """Eine Vokabel-Karte -> vocabulary.started=1, genau eine Karte in dist."""
        _client, user = auth_client
        _vocab_card(user.id)
        by_type = dashboard_service.maturity_by_type(user.id)
        assert by_type['vocabulary']['started'] == 1
        assert sum(by_type['vocabulary']['dist']) == 1
        assert by_type['kanji']['started'] == 0

    def test_numbers_reflect_started(self, auth_client):
        _client, user = auth_client
        _vocab_card(user.id)
        numbers = dashboard_service.learner_numbers(user.id)
        assert numbers['vocab'] == 1
        assert numbers['kanji'] == 0
        assert set(numbers.keys()) == {'kanji', 'vocab', 'grammar', 'kana'}

    def test_compass_glyphs_kanji_fields_and_accuracy(self, auth_client):
        """Kanji-Glyph: Felder gemappt (c/on/kun/mean), acc aus ReviewLog, reps aus State."""
        _client, user = auth_client
        _kanji_card(user.id, character='日', onyomi='ニチ', kunyomi='ひ', meaning='Tag')
        glyphs = dashboard_service.compass_glyphs(user.id, 'kanji')
        assert len(glyphs) == 1
        g = glyphs[0]
        assert g['c'] == '日'
        assert g['on'] == 'ニチ'
        assert g['kun'] == 'ひ'
        assert g['mean'] == 'Tag'
        assert g['acc'] == 100.0   # rating 3 = correct
        assert g['reps'] == 4

    def test_compass_glyphs_unsupported_type_empty(self, auth_client):
        """vocab/grammar haben eigene Ansichten -> compass_glyphs liefert []."""
        _client, user = auth_client
        assert dashboard_service.compass_glyphs(user.id, 'vocabulary') == []
        assert dashboard_service.compass_glyphs(user.id, 'grammar') == []


class TestCompassEndpoint:
    def test_endpoint_kanji_returns_data(self, auth_client):
        client, user = auth_client
        _kanji_card(user.id, character='山', onyomi='サン', kunyomi='やま', meaning='Berg')
        resp = client.get('/api/dashboard/compass-glyphs?type=kanji')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 1
        assert data['data'][0]['c'] == '山'

    def test_endpoint_invalid_type_empty(self, auth_client):
        client, _user = auth_client
        resp = client.get('/api/dashboard/compass-glyphs?type=vocab')
        assert resp.status_code == 200
        assert resp.get_json()['data'] == []

    def test_endpoint_requires_auth(self, client):
        resp = client.get('/api/dashboard/compass-glyphs?type=kanji')
        assert resp.status_code in (302, 401)


class TestListenPillar:
    """„Hoeren"-Saeule aus Lektions-Completion (audio/dialog_slideshow)."""

    def test_counts_published_listening_lessons(self, auth_client):
        _client, user = auth_client
        _listen_lesson('audio')
        _listen_lesson('dialog_slideshow')
        # Nicht-Hoer-Lektion zaehlt nicht.
        non = LessonFactory(is_published=True)
        LessonContentFactory(lesson_id=non.id, content_type='text')
        db.session.commit()
        pillar = dashboard_service.listen_pillar(user.id)
        assert pillar['key'] == 'listen'
        assert pillar['total'] == 2
        assert pillar['started'] == 0
        assert pillar['dist'] == [2, 0, 0, 0, 0]

    def test_unpublished_listening_lesson_excluded(self, auth_client):
        _client, user = auth_client
        lesson = LessonFactory(is_published=False)
        LessonContentFactory(lesson_id=lesson.id, content_type='audio')
        db.session.commit()
        assert dashboard_service.listen_pillar(user.id)['total'] == 1  # 0 -> auf 1 gecappt

    def test_completion_maps_to_mastered_bucket(self, auth_client):
        _client, user = auth_client
        done = _listen_lesson('audio')
        prog = _listen_lesson('dialog_slideshow')
        _listen_lesson('audio')  # unberuehrt -> neu
        UserLessonProgressFactory(user_id=user.id, lesson_id=done.id, is_completed=True, progress_percentage=100)
        UserLessonProgressFactory(user_id=user.id, lesson_id=prog.id, is_completed=False, progress_percentage=40)
        db.session.commit()
        pillar = dashboard_service.listen_pillar(user.id)
        assert pillar['total'] == 3
        # 1 gemeistert (Bucket 4), 1 begonnen (Bucket 1), 1 neu (Bucket 0)
        assert pillar['dist'] == [1, 1, 0, 0, 1]
        assert pillar['started'] == 2

    def test_listen_present_in_compass_pillars(self, auth_client):
        _client, user = auth_client
        _listen_lesson('audio')
        listen = next(p for p in dashboard_service.compass_pillars(user.id) if p['key'] == 'listen')
        assert listen['name'] == 'Hören'
        assert listen['total'] == 1

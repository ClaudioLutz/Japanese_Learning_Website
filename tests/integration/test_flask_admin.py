# tests/integration/test_flask_admin.py
"""
Integrationstests fuer Flask-Admin CRUD-Panel.
Prueft Authentifizierung, Zugriffsschutz und CRUD-Operationen.
"""
from tests.factories import (
    KanaFactory, KanjiFactory, VocabularyFactory,
    GrammarFactory, LessonCategoryFactory, LessonFactory,
    CourseFactory,
)


class TestFlaskAdminAuth:
    """Nur Admins duerfen auf /admin-panel zugreifen."""

    def test_anonymous_redirect(self, client):
        resp = client.get('/admin-panel/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_non_admin_redirect(self, auth_client):
        client, user = auth_client
        resp = client.get('/admin-panel/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_admin_access(self, admin_client):
        client, admin = admin_client
        resp = client.get('/admin-panel/')
        assert resp.status_code == 200
        assert b'JP Admin' in resp.data


class TestFlaskAdminIndex:
    """Dashboard zeigt korrekte Statistiken."""

    def test_index_shows_stats(self, admin_client):
        client, admin = admin_client
        KanaFactory()
        KanjiFactory()
        VocabularyFactory()
        GrammarFactory()

        resp = client.get('/admin-panel/')
        assert resp.status_code == 200
        # Dashboard-Template wird gerendert
        assert b'Benutzer' in resp.data
        assert b'Vokabeln' in resp.data


class TestKanaAdmin:
    """CRUD fuer Kana-Modell."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        KanaFactory(character='あ', romanization='a', type='hiragana')
        KanaFactory(character='ア', romanization='a', type='katakana')

        resp = client.get('/admin-panel/admin_kana/')
        assert resp.status_code == 200
        assert 'あ'.encode() in resp.data
        assert 'ア'.encode() in resp.data

    def test_create_view(self, admin_client):
        client, _ = admin_client
        resp = client.get('/admin-panel/admin_kana/new/')
        assert resp.status_code == 200

    def test_create_kana(self, admin_client):
        client, _ = admin_client
        resp = client.post('/admin-panel/admin_kana/new/', data={
            'character': 'い',
            'romanization': 'i',
            'type': 'hiragana',
        }, follow_redirects=True)
        assert resp.status_code == 200

        from app.models import Kana
        assert Kana.query.filter_by(character='い').first() is not None


class TestKanjiAdmin:
    """CRUD fuer Kanji-Modell."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        KanjiFactory(character='一', meaning='one')

        resp = client.get('/admin-panel/admin_kanji/')
        assert resp.status_code == 200
        assert '一'.encode() in resp.data

    def test_filter_by_status(self, admin_client):
        client, _ = admin_client
        KanjiFactory(character='二', status='approved')
        KanjiFactory(character='三', status='pending_approval')

        resp = client.get('/admin-panel/admin_kanji/?flt0_0=approved')
        assert resp.status_code == 200


class TestVocabularyAdmin:
    """CRUD fuer Vocabulary-Modell."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        VocabularyFactory(word='犬', reading='いぬ', meaning='dog')

        resp = client.get('/admin-panel/admin_vocabulary/')
        assert resp.status_code == 200
        assert '犬'.encode() in resp.data

    def test_search(self, admin_client):
        client, _ = admin_client
        VocabularyFactory(word='猫', reading='ねこ', meaning='cat')

        resp = client.get('/admin-panel/admin_vocabulary/?search=cat')
        assert resp.status_code == 200


class TestGrammarAdmin:
    """CRUD fuer Grammar-Modell."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        GrammarFactory(title='は Particle')

        resp = client.get('/admin-panel/admin_grammar/')
        assert resp.status_code == 200

    def test_detail_view(self, admin_client):
        client, _ = admin_client
        g = GrammarFactory(title='も Particle')

        resp = client.get(f'/admin-panel/admin_grammar/details/?id={g.id}')
        assert resp.status_code == 200


class TestCategoryAdmin:
    """CRUD fuer LessonCategory-Modell."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        LessonCategoryFactory(name='Beginner')

        resp = client.get('/admin-panel/admin_categories/')
        assert resp.status_code == 200
        assert b'Beginner' in resp.data


class TestCourseAdmin:
    """CRUD fuer Course-Modell."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        CourseFactory(title='MNN Beginner I')

        resp = client.get('/admin-panel/admin_courses/')
        assert resp.status_code == 200
        assert b'MNN Beginner I' in resp.data


class TestLessonAdmin:
    """Lesson-Listenansicht (kein Delete erlaubt)."""

    def test_list_view(self, admin_client):
        client, _ = admin_client
        LessonFactory(title='Lesson 1')

        resp = client.get('/admin-panel/admin_lessons/')
        assert resp.status_code == 200
        assert b'Lesson 1' in resp.data

    def test_delete_disabled(self, admin_client):
        """Lektionen duerfen nicht ueber Flask-Admin geloescht werden."""
        client, _ = admin_client
        lesson = LessonFactory(title='Protected')

        client.post(f'/admin-panel/admin_lessons/delete/?id={lesson.id}',
                    follow_redirects=True)
        # Flask-Admin gibt 404 oder Fehler wenn can_delete=False
        from app.models import Lesson
        assert Lesson.query.get(lesson.id) is not None


class TestUserAdmin:
    """User-Admin: nur Bearbeitung, kein Create/Delete."""

    def test_list_view(self, admin_client):
        client, admin = admin_client
        resp = client.get('/admin-panel/admin_users/')
        assert resp.status_code == 200
        assert admin.username.encode() in resp.data

    def test_create_disabled(self, admin_client):
        client, _ = admin_client
        resp = client.get('/admin-panel/admin_users/new/')
        # Sollte 404 oder Redirect sein, da can_create=False
        assert resp.status_code in (302, 404)

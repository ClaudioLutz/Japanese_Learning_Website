"""Integration-Tests fuer /api/kana-grid/<id>/config (Phase 1)."""
from app import db
from app.models import KanaGridConfig
from tests.factories import (
    KanaFactory,
    LessonContentFactory,
    LessonFactory,
)


def _setup_kana_grid_lesson(allow_guest=True):
    """Erstellt eine Lesson mit 5 Kana + 1 kana_grid_game-Content."""
    lesson = LessonFactory(allow_guest_access=allow_guest, price=0.0, is_purchasable=False)
    kana_items = [
        KanaFactory(character='あ', romanization='a'),
        KanaFactory(character='い', romanization='i'),
        KanaFactory(character='う', romanization='u'),
        KanaFactory(character='え', romanization='e'),
        KanaFactory(character='お', romanization='o'),
    ]
    # Kana-LessonContents (notwendig fuer lesson_content_id-Mapping)
    for i, k in enumerate(kana_items):
        LessonContentFactory(
            lesson_id=lesson.id,
            content_type='kana',
            content_id=k.id,
            order_index=i,
            page_number=1,
        )
    # Das eigentliche Game-Content
    game = LessonContentFactory(
        lesson_id=lesson.id,
        content_type='kana_grid_game',
        title='Vokale einsortieren',
        order_index=99,
        page_number=1,
    )
    config = KanaGridConfig(
        lesson_content_id=game.id,
        kana_ids=[k.id for k in kana_items],
        default_mode='schreiben',
        allow_mode_switch=True,
        grid_layout='rows',
        shuffle_pool=True,
        timer_enabled=False,
    )
    db.session.add(config)
    db.session.commit()
    return lesson, game, kana_items


class TestKanaGridConfigEndpoint:
    """I-KGRID01-04: Konfig-API."""

    def test_guest_can_access_guest_lesson(self, client, db):
        """Gaeste duerfen Spiel-Config laden, wenn Lesson allow_guest_access=True."""
        lesson, game, _ = _setup_kana_grid_lesson(allow_guest=True)
        resp = client.get(f'/api/kana-grid/{game.id}/config')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['content_id'] == game.id

    def test_guest_blocked_on_paid_lesson(self, client, db):
        """Gaeste werden bei paid Lessons mit 403 abgewiesen."""
        lesson = LessonFactory(allow_guest_access=False, price=29.0, is_purchasable=True, lesson_type='paid')
        game = LessonContentFactory(lesson_id=lesson.id, content_type='kana_grid_game', title='Paid', page_number=1)
        config = KanaGridConfig(
            lesson_content_id=game.id, kana_ids=[],
            default_mode='schreiben', allow_mode_switch=True,
            grid_layout='rows', shuffle_pool=True, timer_enabled=False,
        )
        db.session.add(config)
        db.session.commit()
        resp = client.get(f'/api/kana-grid/{game.id}/config')
        # Guest auf paid lesson => Lesson.is_accessible_to_user gibt
        # "Login required" zurueck und wir antworten mit 403 (kein Zugriff).
        assert resp.status_code == 403

    def test_not_found_when_wrong_content_type(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(allow_guest_access=True, price=0.0)
        # Ein "text" Content, kein kana_grid_game
        text_content = LessonContentFactory(
            lesson_id=lesson.id, content_type='text', title='Nicht-Spiel', page_number=1
        )
        db.session.commit()
        resp = client.get(f'/api/kana-grid/{text_content.id}/config')
        assert resp.status_code == 404
        assert 'nicht gefunden' in resp.get_json().get('error', '').lower()

    def test_missing_config_returns_404(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(allow_guest_access=True, price=0.0)
        game = LessonContentFactory(
            lesson_id=lesson.id, content_type='kana_grid_game', title='Solo', page_number=1
        )
        db.session.commit()
        # Kein KanaGridConfig fuer dieses LessonContent
        resp = client.get(f'/api/kana-grid/{game.id}/config')
        assert resp.status_code == 404

    def test_happy_path_returns_rows_and_kana(self, auth_client):
        client, user = auth_client
        lesson, game, kana = _setup_kana_grid_lesson(allow_guest=True)
        resp = client.get(f'/api/kana-grid/{game.id}/config')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['content_id'] == game.id
        assert data['lesson_id'] == lesson.id
        # 5 Kana drin
        assert len(data['kana']) == 5
        # Alle haben lesson_content_id (gemappt)
        for k in data['kana']:
            assert k['lesson_content_id'] is not None
        # Vowels-Reihe vorhanden
        keys = [r['key'] for r in data['rows']]
        assert 'vowels' in keys
        # Config-Block korrekt
        assert data['config']['default_mode'] == 'schreiben'
        assert data['config']['allow_mode_switch'] is True


class TestKanaGridAccessControl:
    """I-KGRID05-06: Zugriffskontrolle."""

    def test_locked_lesson_returns_403(self, auth_client):
        client, user = auth_client
        # Paid Lesson ohne Kauf
        lesson = LessonFactory(
            allow_guest_access=False, price=29.0, is_purchasable=True, lesson_type='paid'
        )
        game = LessonContentFactory(
            lesson_id=lesson.id, content_type='kana_grid_game', title='Premium-Spiel', page_number=1
        )
        config = KanaGridConfig(
            lesson_content_id=game.id, kana_ids=[],
            default_mode='schreiben', allow_mode_switch=True,
            grid_layout='rows', shuffle_pool=True, timer_enabled=False,
        )
        db.session.add(config)
        db.session.commit()
        resp = client.get(f'/api/kana-grid/{game.id}/config')
        assert resp.status_code == 403

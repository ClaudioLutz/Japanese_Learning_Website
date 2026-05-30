"""Integration-Tests fuer Verwechslungs-Signal (#2) + Verwechslungs-Drill (#3)."""
from datetime import datetime

from app import db
from app.models import KanaConfusion, UserLessonProgress
from tests.factories import KanaFactory, LessonContentFactory, LessonFactory


def _unlock(user, chars_romaji, type_='hiragana'):
    """Schaltet Kana fuer den User frei (abgeschlossene Lesson). Gibt Kana-Objekte zurueck."""
    lesson = LessonFactory(allow_guest_access=True)
    kanas = []
    for ch, rom in chars_romaji:
        k = KanaFactory(character=ch, romanization=rom, type=type_)
        LessonContentFactory(
            lesson_id=lesson.id, content_type='kana', content_id=k.id, page_number=1
        )
        kanas.append(k)
    db.session.add(UserLessonProgress(
        user_id=user.id, lesson_id=lesson.id,
        is_completed=True, completed_at=datetime.utcnow(), progress_percentage=100,
    ))
    db.session.commit()
    return kanas


class TestKanaConfusionLog:
    def test_logs_new_pair(self, auth_client):
        client, user = auth_client
        k = _unlock(user, [('ね', 'ne'), ('れ', 're')])
        resp = client.post('/api/srs/kana-confusion', json={'confusions': [
            {'target_kana_id': k[0].id, 'confused_kana_id': k[1].id},
        ]})
        assert resp.status_code == 200
        assert resp.get_json()['recorded'] == 1
        row = KanaConfusion.query.filter_by(
            user_id=user.id, target_kana_id=k[0].id, confused_kana_id=k[1].id
        ).first()
        assert row is not None and row.count == 1

    def test_increments_existing_pair(self, auth_client):
        client, user = auth_client
        k = _unlock(user, [('ね', 'ne'), ('れ', 're')])
        body = {'confusions': [{'target_kana_id': k[0].id, 'confused_kana_id': k[1].id}]}
        client.post('/api/srs/kana-confusion', json=body)
        client.post('/api/srs/kana-confusion', json=body)
        row = KanaConfusion.query.filter_by(
            user_id=user.id, target_kana_id=k[0].id, confused_kana_id=k[1].id
        ).first()
        assert row.count == 2

    def test_ignores_self_confusion(self, auth_client):
        client, user = auth_client
        k = _unlock(user, [('ね', 'ne')])
        resp = client.post('/api/srs/kana-confusion', json={'confusions': [
            {'target_kana_id': k[0].id, 'confused_kana_id': k[0].id},
        ]})
        assert resp.get_json()['recorded'] == 0
        assert KanaConfusion.query.count() == 0

    def test_ignores_nonexistent_kana(self, auth_client):
        client, user = auth_client
        _unlock(user, [('ね', 'ne')])
        resp = client.post('/api/srs/kana-confusion', json={'confusions': [
            {'target_kana_id': 999999, 'confused_kana_id': 888888},
        ]})
        assert resp.get_json()['recorded'] == 0

    def test_requires_login(self, client):
        resp = client.post('/api/srs/kana-confusion', json={'confusions': []})
        assert resp.status_code in (401, 302)


class TestConfusionDrill:
    def test_empty_without_unlocked_kana(self, auth_client):
        client, user = auth_client
        data = client.get('/api/practice/kana/confusion').get_json()
        assert data['count'] == 0
        assert 'message' in data

    def test_returns_confusable_clusters_only(self, auth_client):
        client, user = auth_client
        _unlock(user, [('ね', 'ne'), ('れ', 're'), ('わ', 'wa'), ('あ', 'a')])
        data = client.get('/api/practice/kana/confusion').get_json()
        chars = {k['character'] for k in data['kana']}
        # ねれわ bilden ein Cluster; 'あ' allein nicht
        assert {'ね', 'れ', 'わ'}.issubset(chars)
        assert 'あ' not in chars

    def test_items_carry_cluster_key_and_labels(self, auth_client):
        client, user = auth_client
        _unlock(user, [('ね', 'ne'), ('れ', 're'), ('わ', 'wa')])
        data = client.get('/api/practice/kana/confusion').get_json()
        assert all(k['row'].startswith('cf_') for k in data['kana'])
        assert data['row_labels']
        assert data['layout'] == 'confusion'

    def test_payload_includes_stroke_info(self, auth_client):
        client, user = auth_client
        _unlock(user, [('ね', 'ne'), ('れ', 're')])
        data = client.get('/api/practice/kana/confusion').get_json()
        assert all('stroke_order_info' in k for k in data['kana'])

    def test_message_when_no_confusable_pairs(self, auth_client):
        client, user = auth_client
        # Nur ein einzelnes Kana ohne Verwechslungspartner freigeschaltet
        _unlock(user, [('の', 'no')])
        data = client.get('/api/practice/kana/confusion').get_json()
        assert data['count'] == 0
        assert 'message' in data


class TestSessionPayloadFields:
    """Phase-0-Durchreichung: Session-Payload fuehrt jetzt stroke_order_info + mnemonic."""

    def test_session_payload_has_new_fields(self, auth_client):
        client, user = auth_client
        _unlock(user, [('あ', 'a'), ('い', 'i')])
        data = client.get('/api/practice/kana/session?limit=5').get_json()
        assert data['count'] >= 1
        assert all('stroke_order_info' in k and 'mnemonic' in k for k in data['kana'])

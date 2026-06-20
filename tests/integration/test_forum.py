"""Integrationstests fuer das Benutzer-Forum (/forum).

Deckt ab: Login-Gate (Lesen login-pflichtig), Topic-Erstellung, Antworten,
Edit/Delete (Soft), Lock verhindert Reply, Autor/Admin-Autorisierung,
Ankuendigungen admin-only, Moderation (pin/lock/delete), Soft-Delete-Rendering,
Slug-Format, Pagination, 404. Muster: conftest-Fixtures + factory_boy.
"""
from app import db
from app.models import ForumPost, ForumTopic, _forum_slugify
from tests.factories import (
    ForumCategoryFactory, ForumPostFactory, ForumTopicFactory, UserFactory,
)


def _category(**kw):
    cat = ForumCategoryFactory(**kw)
    db.session.commit()
    return cat


def _topic_with_op(category, author, **kw):
    topic = ForumTopicFactory(category_id=category.id, author_id=author.id, **kw)
    db.session.flush()
    ForumPostFactory(topic_id=topic.id, author_id=author.id, is_op=True)
    db.session.commit()
    op = ForumPost.query.filter_by(topic_id=topic.id, is_op=True).first()
    return topic, op


# ── Modelle ──────────────────────────────────────────────────────────────

class TestForumModels:
    def test_slug_format(self, app, db):
        u = UserFactory()
        db.session.flush()
        c = ForumCategoryFactory()
        db.session.flush()
        t = ForumTopicFactory(category_id=c.id, author_id=u.id,
                              title="Wie lerne ich Höflichkeit?")
        db.session.flush()
        assert t.build_slug() == f"wie-lerne-ich-hoeflichkeit-{t.id}"

    def test_slug_japanese_fallback(self):
        # rein japanischer Titel -> leerer Basis-Slug -> Aufrufer faellt auf 'thema'
        assert _forum_slugify("敬語のテスト") == ""

    def test_post_can_edit(self, app, db):
        author = UserFactory()
        other = UserFactory()
        admin = UserFactory(is_admin=True)
        db.session.flush()
        c = ForumCategoryFactory()
        db.session.flush()
        t = ForumTopicFactory(category_id=c.id, author_id=author.id)
        db.session.flush()
        p = ForumPostFactory(topic_id=t.id, author_id=author.id)
        db.session.commit()
        assert p.can_edit(author) is True
        assert p.can_edit(admin) is True
        assert p.can_edit(other) is False


# ── Login-Gate (Lesen ist login-pflichtig) ────────────────────────────────

class TestForumLoginGate:
    def test_index_requires_login(self, client):
        resp = client.get('/forum/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_category_requires_login(self, app, client):
        _category(slug='vorschlaege')
        resp = client.get('/forum/vorschlaege')
        assert resp.status_code == 302

    def test_topic_requires_login(self, app, client):
        u = UserFactory()
        db.session.flush()
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, u)
        resp = client.get(f'/forum/topic/{t.id}')
        assert resp.status_code == 302

    def test_index_ok_logged_in(self, auth_client):
        client, user = auth_client
        _category(name='Vorschläge', slug='vorschlaege')
        resp = client.get('/forum/')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Vorschläge' in body
        assert 'noindex' in body


# ── Topic erstellen ────────────────────────────────────────────────────────

class TestForumCreate:
    def test_create_topic_success(self, auth_client):
        client, user = auth_client
        _category(slug='vorschlaege')
        resp = client.post('/forum/vorschlaege/new', data={
            'title': 'Mein erster Vorschlag',
            'body': 'Ich hätte da eine richtig gute Idee für die Seite.',
        })
        assert resp.status_code == 302
        topic = ForumTopic.query.filter_by(title='Mein erster Vorschlag').first()
        assert topic is not None
        assert topic.slug == f'mein-erster-vorschlag-{topic.id}'
        assert topic.reply_count == 0
        op = ForumPost.query.filter_by(topic_id=topic.id, is_op=True).first()
        assert op is not None
        assert 'gute Idee' in op.body

    def test_create_topic_invalid_short_title(self, auth_client):
        client, user = auth_client
        _category(slug='vorschlaege')
        resp = client.post('/forum/vorschlaege/new', data={'title': 'ab', 'body': 'zu kurz'})
        assert resp.status_code == 200  # Formular neu gerendert
        assert ForumTopic.query.count() == 0

    def test_create_topic_admin_only_blocked_for_user(self, auth_client):
        client, user = auth_client
        _category(slug='ankuendigungen', admin_only_post=True)
        resp = client.post('/forum/ankuendigungen/new', data={
            'title': 'Darf ich nicht', 'body': 'Sollte 403 geben bitte.',
        })
        assert resp.status_code == 403
        assert ForumTopic.query.count() == 0

    def test_create_topic_admin_only_allowed_for_admin(self, admin_client):
        client, admin = admin_client
        _category(slug='ankuendigungen', admin_only_post=True)
        resp = client.post('/forum/ankuendigungen/new', data={
            'title': 'Wichtige Ankündigung', 'body': 'Das Team meldet sich zu Wort.',
        })
        assert resp.status_code == 302
        assert ForumTopic.query.count() == 1

    def test_admin_only_category_hides_new_button(self, auth_client):
        client, user = auth_client
        _category(name='Ankündigungen', slug='ankuendigungen', admin_only_post=True)
        body = client.get('/forum/ankuendigungen').get_data(as_text=True)
        assert 'Nur Team' in body
        assert '/forum/ankuendigungen/new' not in body

    def test_create_topic_rate_limited(self, auth_client):
        client, user = auth_client
        _category(slug='vorschlaege')
        codes = []
        for i in range(4):
            r = client.post('/forum/vorschlaege/new', data={
                'title': f'Vorschlag Nummer {i}', 'body': 'Genug Text fuer die Validierung.',
            })
            codes.append(r.status_code)
        # Limit 3/h -> spaetestens der 4. Versuch wird gedrosselt.
        assert 429 in codes


# ── Antworten ──────────────────────────────────────────────────────────────

class TestForumReply:
    def test_reply_success(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, user)
        resp = client.post(f'/forum/topic/{t.id}/reply', data={'body': 'Gute Antwort hier.'})
        assert resp.status_code == 302
        db.session.refresh(t)
        assert t.reply_count == 1
        assert ForumPost.query.filter_by(topic_id=t.id, is_op=False).count() == 1

    def test_reply_locked_blocked_for_user(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, user, is_locked=True)
        resp = client.post(f'/forum/topic/{t.id}/reply', data={'body': 'Sollte nicht durchgehen.'})
        assert resp.status_code == 302  # Redirect mit Warn-Flash
        assert ForumPost.query.filter_by(topic_id=t.id, is_op=False).count() == 0

    def test_reply_locked_allowed_for_admin(self, admin_client):
        client, admin = admin_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, admin, is_locked=True)
        resp = client.post(f'/forum/topic/{t.id}/reply', data={'body': 'Moderations-Antwort.'})
        assert resp.status_code == 302
        assert ForumPost.query.filter_by(topic_id=t.id, is_op=False).count() == 1


# ── Edit / Delete (Soft) ────────────────────────────────────────────────────

class TestForumEditDelete:
    def test_author_can_edit_own_post(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, op = _topic_with_op(c, user)
        resp = client.post(f'/forum/post/{op.id}/edit', data={'body': 'Überarbeiteter Text.'})
        assert resp.status_code == 302
        db.session.refresh(op)
        assert op.body == 'Überarbeiteter Text.'
        assert op.edited_at is not None

    def test_non_author_cannot_edit(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        other = UserFactory()
        db.session.flush()
        t, op = _topic_with_op(c, other)
        resp = client.post(f'/forum/post/{op.id}/edit', data={'body': 'Fremder Eingriff.'})
        assert resp.status_code == 403

    def test_admin_can_edit_any_post(self, admin_client):
        client, admin = admin_client
        author = UserFactory()
        db.session.flush()
        c = _category(slug='vorschlaege')
        t, op = _topic_with_op(c, author)
        resp = client.post(f'/forum/post/{op.id}/edit', data={'body': 'Admin-Korrektur.'})
        assert resp.status_code == 302
        db.session.refresh(op)
        assert op.body == 'Admin-Korrektur.'

    def test_author_soft_deletes_reply_decrements_count(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, op = _topic_with_op(c, user)
        reply = ForumPostFactory(topic_id=t.id, author_id=user.id, is_op=False)
        t.reply_count = 1
        db.session.commit()
        reply_id = reply.id
        resp = client.post(f'/forum/post/{reply_id}/delete')
        assert resp.status_code == 302
        db.session.refresh(t)
        deleted = ForumPost.query.get(reply_id)
        assert deleted is not None        # Zeile bleibt (Soft-Delete)
        assert deleted.is_deleted is True
        assert t.reply_count == 0         # Zaehler korrigiert

    def test_non_author_cannot_delete(self, auth_client):
        client, user = auth_client
        other = UserFactory()
        db.session.flush()
        c = _category(slug='vorschlaege')
        t, op = _topic_with_op(c, other)
        resp = client.post(f'/forum/post/{op.id}/delete')
        assert resp.status_code == 403
        db.session.refresh(op)
        assert op.is_deleted is False

    def test_delete_in_locked_topic_blocked_for_user(self, auth_client):
        # Symmetrisch zu edit_post: in gesperrtem Thema kein Loeschen (ausser Admin)
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, op = _topic_with_op(c, user, is_locked=True)
        resp = client.post(f'/forum/post/{op.id}/delete')
        assert resp.status_code == 403
        db.session.refresh(op)
        assert op.is_deleted is False

    def test_deleted_post_renders_placeholder(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, op = _topic_with_op(c, user)
        ForumPostFactory(topic_id=t.id, author_id=user.id, is_op=False,
                         is_deleted=True, body='geheim')
        db.session.commit()
        body = client.get(f'/forum/topic/{t.id}').get_data(as_text=True)
        assert 'gelöscht' in body
        assert 'geheim' not in body


# ── Moderation (Admin) ──────────────────────────────────────────────────────

class TestForumModeration:
    def test_admin_pin_toggle(self, admin_client):
        client, admin = admin_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, admin)
        client.post(f'/forum/topic/{t.id}/pin')
        db.session.refresh(t)
        assert t.is_pinned is True
        client.post(f'/forum/topic/{t.id}/pin')
        db.session.refresh(t)
        assert t.is_pinned is False

    def test_admin_lock_toggle(self, admin_client):
        client, admin = admin_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, admin)
        client.post(f'/forum/topic/{t.id}/lock')
        db.session.refresh(t)
        assert t.is_locked is True

    def test_non_admin_pin_blocked(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, user)
        resp = client.post(f'/forum/topic/{t.id}/pin')
        assert resp.status_code == 302  # admin_required -> Flash + Redirect
        db.session.refresh(t)
        assert t.is_pinned is False

    def test_admin_deletes_topic(self, admin_client):
        client, admin = admin_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, admin)
        resp = client.post(f'/forum/topic/{t.id}/delete')
        assert resp.status_code == 302
        db.session.refresh(t)
        assert t.is_deleted is True
        # danach nicht mehr erreichbar
        assert client.get(f'/forum/topic/{t.id}').status_code == 404


# ── Sichtbarkeit / 404 / Pagination ────────────────────────────────────────

class TestForumViewAndPagination:
    def test_topic_404_when_deleted(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, user, is_deleted=True)
        assert client.get(f'/forum/topic/{t.id}').status_code == 404

    def test_category_404_wrong_slug(self, auth_client):
        client, user = auth_client
        assert client.get('/forum/gibt-es-nicht').status_code == 404

    def test_view_increments_view_count(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        t, _ = _topic_with_op(c, user)
        client.get(f'/forum/topic/{t.id}')
        db.session.refresh(t)
        assert t.view_count == 1

    def test_category_pagination(self, auth_client):
        client, user = auth_client
        c = _category(slug='vorschlaege')
        for _ in range(25):
            ForumTopicFactory(category_id=c.id, author_id=user.id)
        db.session.commit()
        body = client.get('/forum/vorschlaege').get_data(as_text=True)
        assert 'forum-pagination' in body
        assert 'page=2' in body

"""Integrationstests fuer das oeffentliche Hinweis-/Feedback-Board (/feedback).

Schwerpunkt (anders als das Forum!): LESEN ist OEFFENTLICH, SCHREIBEN braucht
ein Konto. Deckt ab: Public-Read (kein Login), noindex, Autor-E-Mail wird NIE
gerendert, Create/Comment login-pflichtig, Rate-Limit, Verankerung + Validierung,
Resolve (admin-only, Toggle, Notify nur open->resolved), Soft-Delete.
"""
import app.issue_routes as issue_routes
from app import db
from app.issue_routes import (
    _location_descriptor, _page_descriptor, _resolve_content_ref,
)
from app.models import ContentIssue, ContentIssueComment
from tests.factories import (
    AdminUserFactory, ContentIssueCommentFactory, ContentIssueFactory,
    LessonContentFactory, LessonFactory, LessonPageFactory, UserFactory,
)


def _issue(author, **kw):
    iss = ContentIssueFactory(author_id=author.id, **kw)
    db.session.commit()
    return iss


# ── Modelle ──────────────────────────────────────────────────────────────

class TestIssueModels:
    def test_slug_and_can_edit(self, app, db):
        author = UserFactory()
        other = UserFactory()
        admin = UserFactory(is_admin=True)
        db.session.flush()
        iss = ContentIssueFactory(author_id=author.id, title="Höfliche Anrede falsch")
        db.session.flush()
        assert iss.build_slug() == f"hoefliche-anrede-falsch-{iss.id}"
        assert iss.is_resolved is False
        assert iss.can_edit(author) is True
        assert iss.can_edit(admin) is True
        assert iss.can_edit(other) is False


# ── Oeffentliches Lesen (Kern-Unterschied zum Forum) ───────────────────────

class TestIssuePublicRead:
    def test_index_public_no_login(self, client, db):
        u = UserFactory()
        db.session.flush()
        _issue(u, title="Oeffentlich sichtbar")
        resp = client.get('/feedback/')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'Oeffentlich sichtbar' in body
        assert 'noindex' in body

    def test_issue_detail_public_no_login(self, client, db):
        u = UserFactory()
        db.session.flush()
        iss = _issue(u, title="Detail offen lesbar")
        resp = client.get(f'/feedback/{iss.id}')
        assert resp.status_code == 200
        assert 'Detail offen lesbar' in resp.get_data(as_text=True)

    def test_author_email_never_rendered(self, client, db):
        u = UserFactory()
        db.session.flush()
        iss = _issue(u)
        body = client.get(f'/feedback/{iss.id}').get_data(as_text=True)
        assert u.username in body          # Pseudonym sichtbar
        assert u.email not in body         # E-Mail NIE oeffentlich

    def test_deleted_issue_404_and_out_of_list(self, client, db):
        u = UserFactory()
        db.session.flush()
        iss = _issue(u, title="Geloeschter Hinweis", is_deleted=True)
        assert client.get(f'/feedback/{iss.id}').status_code == 404
        body = client.get('/feedback/?status=all').get_data(as_text=True)
        assert 'Geloeschter Hinweis' not in body

    def test_status_filter_separates_open_resolved(self, client, db):
        u = UserFactory()
        db.session.flush()
        _issue(u, title="Noch offen hier", status='open')
        _issue(u, title="Schon erledigt hier", status='resolved')
        open_body = client.get('/feedback/?status=open').get_data(as_text=True)
        assert 'Noch offen hier' in open_body
        assert 'Schon erledigt hier' not in open_body
        done_body = client.get('/feedback/?status=resolved').get_data(as_text=True)
        assert 'Schon erledigt hier' in done_body
        assert 'Noch offen hier' not in done_body

    def test_anchored_issue_shows_backlink(self, client, db):
        u = UserFactory()
        db.session.flush()
        lesson = LessonFactory(title="Begruessungen")
        db.session.flush()
        db.session.commit()
        iss = _issue(u, content_type='lesson', content_id=lesson.id)
        body = client.get(f'/feedback/{iss.id}').get_data(as_text=True)
        assert f'/lessons/{lesson.id}' in body
        assert 'Begruessungen' in body


# ── Schreiben braucht ein Konto ────────────────────────────────────────────

class TestIssueCreate:
    def test_create_requires_login(self, client, db):
        resp = client.post('/feedback/new', data={
            'title': 'Kein Login', 'body': 'Sollte zum Login leiten bitte.',
        })
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']
        assert ContentIssue.query.count() == 0

    def test_create_success_with_lesson_anchor(self, auth_client, db):
        client, user = auth_client
        lesson = LessonFactory()
        db.session.flush()
        db.session.commit()
        resp = client.post('/feedback/new', data={
            'title': 'Tippfehler in Lektion',
            'body': 'Auf Seite 2 steht ein Fehler im Beispielsatz.',
            'content_type': 'lesson', 'content_id': str(lesson.id),
        })
        assert resp.status_code == 302
        iss = ContentIssue.query.filter_by(title='Tippfehler in Lektion').first()
        assert iss is not None
        assert iss.content_type == 'lesson'
        assert iss.content_id == lesson.id
        assert iss.status == 'open'
        assert iss.author_id == user.id

    def test_create_invalid_anchor_stored_as_general(self, auth_client, db):
        client, user = auth_client
        resp = client.post('/feedback/new', data={
            'title': 'Genereller Hinweis',
            'body': 'Etwas Allgemeines ohne gueltige Verankerung.',
            'content_type': 'lesson', 'content_id': '999999',
        })
        assert resp.status_code == 302
        iss = ContentIssue.query.filter_by(title='Genereller Hinweis').first()
        assert iss is not None
        assert iss.content_type is None
        assert iss.content_id is None

    def test_create_short_title_rejected(self, auth_client, db):
        client, user = auth_client
        resp = client.post('/feedback/new', data={'title': 'ab', 'body': 'zu kurz'})
        assert resp.status_code == 200  # Formular neu gerendert
        assert ContentIssue.query.count() == 0

    def test_create_rate_limited(self, auth_client, db):
        client, user = auth_client
        codes = []
        for i in range(6):
            r = client.post('/feedback/new', data={
                'title': f'Hinweis Nummer {i}', 'body': 'Genug Text fuer die Validierung.',
            })
            codes.append(r.status_code)
        assert 429 in codes  # Limit 5/h

    def test_new_issue_notifies_admins(self, auth_client, db, monkeypatch):
        client, user = auth_client
        AdminUserFactory()
        db.session.commit()
        calls = []
        monkeypatch.setattr(
            issue_routes, 'send_new_issue_admin_email',
            lambda *a, **k: calls.append(a) or True,
        )
        client.post('/feedback/new', data={
            'title': 'Neuer Hinweis', 'body': 'Inhaltlicher Text fuer die Pruefung.',
        })
        assert len(calls) == 1


# ── Antworten ──────────────────────────────────────────────────────────────

class TestIssueComment:
    def test_comment_requires_login(self, client, db):
        u = UserFactory()
        db.session.flush()
        iss = _issue(u)
        resp = client.post(f'/feedback/{iss.id}/comment', data={'body': 'Anonyme Antwort'})
        assert resp.status_code == 302
        assert ContentIssueComment.query.count() == 0

    def test_comment_success_not_maintainer(self, auth_client, db):
        client, user = auth_client
        iss = _issue(user)
        resp = client.post(f'/feedback/{iss.id}/comment', data={'body': 'Meine Antwort dazu.'})
        assert resp.status_code == 302
        c = ContentIssueComment.query.filter_by(issue_id=iss.id).first()
        assert c is not None
        assert c.is_maintainer_reply is False

    def test_admin_comment_is_maintainer_reply(self, admin_client, db):
        client, admin = admin_client
        author = UserFactory()
        db.session.flush()
        iss = _issue(author)
        client.post(f'/feedback/{iss.id}/comment', data={'body': 'Antwort vom Team.'})
        c = ContentIssueComment.query.filter_by(issue_id=iss.id).first()
        assert c.is_maintainer_reply is True


# ── Resolve (Admin) + Notify ───────────────────────────────────────────────

class TestIssueResolve:
    def test_resolve_requires_admin(self, auth_client, db):
        client, user = auth_client
        iss = _issue(user)
        resp = client.post(f'/feedback/{iss.id}/resolve')
        assert resp.status_code == 302  # admin_required -> Flash + Redirect
        db.session.refresh(iss)
        assert iss.status == 'open'

    def test_admin_resolve_sets_fields_and_notifies(self, admin_client, db, monkeypatch):
        client, admin = admin_client
        reporter = UserFactory()
        db.session.flush()
        iss = _issue(reporter, title='Bitte fixen')
        calls = []
        monkeypatch.setattr(
            issue_routes, 'send_issue_resolved_email',
            lambda *a, **k: calls.append(a) or True,
        )
        resp = client.post(f'/feedback/{iss.id}/resolve')
        assert resp.status_code == 302
        db.session.refresh(iss)
        assert iss.status == 'resolved'
        assert iss.resolved_at is not None
        assert iss.resolved_by_id == admin.id
        assert len(calls) == 1
        assert calls[0][0] == reporter.email  # erster Positionsarg = Empfaenger

    def test_resolve_toggle_reopen(self, admin_client, db):
        client, admin = admin_client
        reporter = UserFactory()
        db.session.flush()
        iss = _issue(reporter)
        client.post(f'/feedback/{iss.id}/resolve')   # -> resolved
        client.post(f'/feedback/{iss.id}/resolve')   # -> wieder offen
        db.session.refresh(iss)
        assert iss.status == 'open'
        assert iss.resolved_at is None

    def test_self_resolve_no_self_notify(self, admin_client, db, monkeypatch):
        client, admin = admin_client
        iss = _issue(admin)  # Admin ist selbst Melder
        calls = []
        monkeypatch.setattr(
            issue_routes, 'send_issue_resolved_email',
            lambda *a, **k: calls.append(a) or True,
        )
        client.post(f'/feedback/{iss.id}/resolve')
        assert calls == []


# ── Soft-Delete ─────────────────────────────────────────────────────────────

class TestIssueDelete:
    def test_author_deletes_own_issue(self, auth_client, db):
        client, user = auth_client
        iss = _issue(user)
        resp = client.post(f'/feedback/{iss.id}/delete')
        assert resp.status_code == 302
        db.session.refresh(iss)
        assert iss.is_deleted is True

    def test_non_author_cannot_delete_issue(self, auth_client, db):
        client, user = auth_client
        other = UserFactory()
        db.session.flush()
        iss = _issue(other)
        resp = client.post(f'/feedback/{iss.id}/delete')
        assert resp.status_code == 403
        db.session.refresh(iss)
        assert iss.is_deleted is False

    def test_admin_deletes_any_issue(self, admin_client, db):
        client, admin = admin_client
        author = UserFactory()
        db.session.flush()
        iss = _issue(author)
        resp = client.post(f'/feedback/{iss.id}/delete')
        assert resp.status_code == 302
        db.session.refresh(iss)
        assert iss.is_deleted is True

    def test_deleted_comment_renders_placeholder(self, client, db):
        u = UserFactory()
        db.session.flush()
        iss = _issue(u)
        ContentIssueCommentFactory(
            issue_id=iss.id, author_id=u.id, is_deleted=True, body='geheim',
        )
        db.session.commit()
        body = client.get(f'/feedback/{iss.id}').get_data(as_text=True)
        assert 'gelöscht' in body
        assert 'geheim' not in body


# ── Fundstellen-Pfad: Lektion › Seite › Container ──────────────────────────

class TestIssueLocationPath:
    def test_resolve_lesson_content_includes_lesson_page_container(self, app, db):
        lesson = LessonFactory(title="Begruessungen")
        db.session.flush()
        LessonPageFactory(lesson_id=lesson.id, page_number=2, title="Vokabeln")
        lc = LessonContentFactory(
            lesson_id=lesson.id, page_number=2, title="おはよう",
        )
        db.session.commit()
        label, url = _resolve_content_ref('lesson_content', lc.id)
        assert 'Lektion: Begruessungen' in label
        assert 'Seite 2' in label
        assert 'Vokabeln' in label        # Seitentitel im Pfad
        assert 'おはよう' in label          # Container im Pfad
        # URL deep-linkt auf Seite + Container (vom Frontend gehandhabt)
        assert url == f'/lessons/{lesson.id}#content-{lc.id}'

    def test_page_descriptor_without_metadata_no_none(self, app, db):
        """Fehlende LessonPage-Metadaten -> nur 'Seite N', niemals 'None'."""
        lesson = LessonFactory()
        db.session.flush()
        lc = LessonContentFactory(lesson_id=lesson.id, page_number=3, title="X")
        db.session.commit()
        assert _page_descriptor(lesson.id, 3) == 'Seite 3'
        label, _ = _resolve_content_ref('lesson_content', lc.id)
        assert 'Seite 3' in label
        assert 'None' not in label

    def test_location_descriptor_lesson_with_page(self, app, db):
        lesson = LessonFactory(title="Zahlen")
        db.session.flush()
        LessonPageFactory(lesson_id=lesson.id, page_number=2, title="Übung")
        db.session.commit()
        assert _location_descriptor('lesson', lesson.id, 2) == \
            'Lektion: Zahlen › Seite 2: Übung'

    def test_location_descriptor_lesson_without_page(self, app, db):
        lesson = LessonFactory(title="Zahlen")
        db.session.commit()
        assert _location_descriptor('lesson', lesson.id, None) == 'Lektion: Zahlen'


# ── Vorbefuellung: Fundstelle wird in Titel + Text mitgegeben ──────────────

class TestIssuePrefill:
    def test_new_issue_prefills_path_for_lesson_content(self, auth_client, db):
        client, user = auth_client
        lesson = LessonFactory(title="Begruessungen")
        db.session.flush()
        LessonPageFactory(lesson_id=lesson.id, page_number=1, title="Einstieg")
        lc = LessonContentFactory(
            lesson_id=lesson.id, page_number=1, title="こんにちは",
        )
        db.session.commit()
        body = client.get(
            f'/feedback/new?content_type=lesson_content&content_id={lc.id}'
        ).get_data(as_text=True)
        assert 'Fundstelle' in body          # editierbarer Pfad im Textfeld
        assert 'Seite 1' in body
        assert 'Begruessungen' in body

    def test_new_issue_prefills_page_for_lesson_anchor(self, auth_client, db):
        client, user = auth_client
        lesson = LessonFactory(title="Zahlen")
        db.session.flush()
        LessonPageFactory(lesson_id=lesson.id, page_number=2, title="Übung")
        db.session.commit()
        body = client.get(
            f'/feedback/new?content_type=lesson&content_id={lesson.id}&page=2'
        ).get_data(as_text=True)
        assert 'Seite 2' in body
        assert 'Zahlen' in body

    def test_new_issue_invalid_page_ignored(self, auth_client, db):
        """Nicht-numerische ?page darf nicht crashen und wird ignoriert."""
        client, user = auth_client
        lesson = LessonFactory(title="Zahlen")
        db.session.commit()
        resp = client.get(
            f'/feedback/new?content_type=lesson&content_id={lesson.id}&page=abc'
        )
        assert resp.status_code == 200
        assert 'Zahlen' in resp.get_data(as_text=True)


# ── Lektionsansicht: Melden-Bruecken zum Issue-Board ───────────────────────

class TestLessonViewReportLinks:
    def test_per_page_report_link_rendered(self, auth_client, db):
        """Jede Lektionsseite hat einen 'Fehler auf dieser Seite melden'-Link
        (auch mobil sichtbar — der Hero-Link verschwindet ab Seite 2)."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0)
        db.session.flush()
        LessonContentFactory(
            lesson_id=lesson.id, page_number=1, content_type='text',
            content_text='Hallo Welt',
        )
        db.session.commit()
        body = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'Fehler auf dieser Seite melden' in body
        assert 'content_type=lesson' in body
        assert 'page=1' in body

    def test_audio_disclaimer_links_to_issue_board(self, auth_client, db):
        """Der KI-Stimmen-Disclaimer verweist aufs Issue-Board, verankert am
        Container (content_id) — damit Lektion+Seite+Container mitgehen."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0)
        db.session.flush()
        lc = LessonContentFactory(
            lesson_id=lesson.id, page_number=1, content_type='text',
            content_text='Hallo Welt', media_url='http://example.test/a.wav',
            file_type='audio/wav',
        )
        db.session.commit()
        body = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'KI-Stimmen' in body
        assert 'Aussprache melden' in body
        assert 'content_type=lesson_content' in body
        assert f'content_id={lc.id}' in body

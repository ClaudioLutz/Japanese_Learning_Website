"""Editierbarer Alt-Text fuer Bild-Content (JSON in ai_generation_details).

Keine Migration, keine Massen-Befuellung: leer = Fallback wie bisher (Titel bzw.
'Seitenbild').
"""
from app import db
from app.models import LessonContent
from tests.factories import LessonContentFactory, LessonFactory


def _image(lesson, **kw):
    kw.setdefault('title', 'Bild Titel')
    item = LessonContentFactory(lesson_id=lesson.id, content_type='image',
                                content_text=None, media_url='/uploads/lessons/img/x.png', **kw)
    db.session.commit()
    return item


def test_alt_text_property_roundtrip_keeps_other_json(app_context):
    lesson = LessonFactory()
    db.session.flush()
    item = _image(lesson, ai_generation_details={'prompt': 'p'})
    assert item.alt_text is None
    item.alt_text = '  Zwei Personen verbeugen sich  '
    db.session.commit()
    db.session.expire_all()
    item = db.session.get(LessonContent, item.id)
    assert item.alt_text == 'Zwei Personen verbeugen sich'
    assert item.ai_generation_details['prompt'] == 'p'
    item.alt_text = ''
    db.session.commit()
    db.session.expire_all()
    item = db.session.get(LessonContent, item.id)
    assert item.alt_text is None
    assert item.ai_generation_details == {'prompt': 'p'}


def test_alt_text_empty_does_not_create_json(app_context):
    lesson = LessonFactory()
    db.session.flush()
    item = _image(lesson)
    item.alt_text = None
    assert item.ai_generation_details is None
    item.alt_text = 'x' * 500
    assert len(item.alt_text) == LessonContent.ALT_TEXT_MAX_LEN


def test_admin_edit_and_get_alt_text(admin_client):
    client, _admin = admin_client
    lesson = LessonFactory()
    db.session.flush()
    item = _image(lesson)
    resp = client.put(f'/api/admin/content/{item.id}/edit', json={
        'content_type': 'image', 'title': 'Bild Titel',
        'media_url': '/uploads/lessons/img/x.png', 'alt_text': 'Ein roter Torii im Schnee',
    })
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = client.get(f'/api/admin/content/{item.id}').get_json()
    assert data['alt_text'] == 'Ein roter Torii im Schnee'
    # Edit ohne alt_text-Feld laesst den Wert stehen
    client.put(f'/api/admin/content/{item.id}/edit', json={'content_type': 'image', 'title': 'Neu'})
    assert client.get(f'/api/admin/content/{item.id}').get_json()['alt_text'] == 'Ein roter Torii im Schnee'


def test_admin_create_with_alt_text(admin_client):
    client, _admin = admin_client
    lesson = LessonFactory()
    db.session.commit()
    resp = client.post(f'/api/admin/lessons/{lesson.id}/content/new', json={
        'content_type': 'image', 'title': 'T', 'media_url': '/uploads/a.png', 'alt_text': 'Alt neu',
    })
    assert resp.status_code == 201
    assert db.session.get(LessonContent, resp.get_json()['id']).alt_text == 'Alt neu'
    resp = client.post(f'/api/admin/lessons/{lesson.id}/content/file', json={
        'content_type': 'image', 'title': 'T2', 'file_path': 'lessons/img/b.png', 'alt_text': 'Alt Datei',
    })
    assert resp.status_code == 201
    assert db.session.get(LessonContent, resp.get_json()['id']).alt_text == 'Alt Datei'


def test_lesson_view_renders_alt_text_with_fallback(client, app_context):
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    with_alt = _image(lesson)
    with_alt.alt_text = 'Eine Katze schläft auf dem Tatami'
    _image(lesson, title='Nur Titel')
    db.session.commit()
    html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
    assert 'alt="Eine Katze schläft auf dem Tatami"' in html
    assert 'alt="Nur Titel"' in html


def test_admin_editor_has_alt_text_field(admin_client):
    client, _admin = admin_client
    html = client.get('/admin/manage/lessons').get_data(as_text=True)
    assert 'id="mediaAltText"' in html
    assert 'name="alt_text"' in html
    assert "altInput.value = content.alt_text || ''" in html

"""User.created_at / User.last_login: gesetzt bei Registrierung und Login."""

from datetime import datetime, timedelta

from app.models import User


def _register(client, n=1):
    return client.post('/register', data={
        'username': f'zeitstempel{n}',
        'email': f'zeitstempel{n}@example.com',
        'password': 'Passwort1',
        'password2': 'Passwort1',
        'website': '',
    })


def test_created_at_wird_bei_registrierung_gesetzt(client, db):
    vorher = datetime.utcnow() - timedelta(seconds=5)
    assert _register(client, 1).status_code == 302
    user = User.query.filter_by(username='zeitstempel1').first()
    assert user is not None
    assert user.created_at is not None
    assert vorher <= user.created_at <= datetime.utcnow() + timedelta(seconds=5)


def test_last_login_wird_bei_registrierung_gesetzt(client, db):
    """Nach der Registrierung wird automatisch eingeloggt -> last_login zaehlt."""
    _register(client, 2)
    user = User.query.filter_by(username='zeitstempel2').first()
    assert user.last_login is not None


def test_last_login_nach_login_gesetzt_und_aktualisiert(client, db):
    from tests.factories import UserFactory
    user = UserFactory(email='login@example.com')
    user.set_password('Passwort1')
    user.last_login = None
    db.session.commit()
    uid = user.id

    assert User.query.get(uid).last_login is None

    client.post('/login', data={'email': 'login@example.com', 'password': 'Passwort1'})
    erster = User.query.get(uid).last_login
    assert erster is not None

    # Zweiter Login muss den Zeitstempel fortschreiben.
    User.query.get(uid).last_login = erster - timedelta(hours=3)
    db.session.commit()
    client.get('/logout')
    client.post('/login', data={'email': 'login@example.com', 'password': 'Passwort1'})
    zweiter = User.query.get(uid).last_login
    assert zweiter > erster - timedelta(hours=3)


def test_fehlgeschlagener_login_setzt_last_login_nicht(client, db):
    from tests.factories import UserFactory
    user = UserFactory(email='falsch@example.com')
    user.set_password('Passwort1')
    user.last_login = None
    db.session.commit()
    uid = user.id

    client.post('/login', data={'email': 'falsch@example.com', 'password': 'Falsch999'})
    assert User.query.get(uid).last_login is None


def test_admin_user_liste_zeigt_zeitstempel(admin_client):
    client, _ = admin_client
    body = client.get('/admin-panel/admin_users/').get_data(as_text=True)
    assert 'Registriert am' in body
    assert 'Letzter Login' in body

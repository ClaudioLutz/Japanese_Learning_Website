# tests/conftest.py
"""
Globale Test-Fixtures für pytest.
Stellt App, DB, Client und Auth-Helpers bereit.
"""

import pytest
import os

# Umgebungsvariablen VOR dem App-Import setzen
# SICHERHEIT: Tests laufen gegen eine wegwerfbare In-Memory-SQLite. Ein in der
# Shell gesetztes DATABASE_URL (z.B. versehentlich die Produktions-Postgres)
# wird hier HART IGNORIERT — sonst löscht die `db`-Fixture per drop_all() echte
# Produktionstabellen. Eine abweichende Test-DB nur über die ausdrückliche
# Variable TEST_DATABASE_URL (deren Name 'test' enthalten muss, siehe Guard
# in der db-Fixture).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("WTF_CSRF_SECRET_KEY", "test-csrf-key")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")
os.environ.setdefault("MAIL_SUPPRESS_SEND", "true")

from app import create_app, db as _db


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Rate-Limiter global zwischen Tests zuruecksetzen (verhindert 429-Durchschlag,
    z.B. bei mehreren /register- oder /login-POSTs innerhalb derselben Minute)."""
    from app import limiter
    try:
        limiter.reset()
    except Exception:
        pass
    yield
    try:
        limiter.reset()
    except Exception:
        pass


@pytest.fixture(scope="session")
def app():
    """Flask-App mit Test-Konfiguration."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SERVER_NAME": "localhost",
        "PAYMENT_PROVIDER": "mock",
        "MOCK_PAYMENTS_ENABLED": "true",
        "GCS_BUCKET_NAME": "",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_SECRET_KEY": "test-csrf-key",
        "MAIL_SUPPRESS_SEND": True,
        "MAIL_DEFAULT_SENDER": "test@japanese-learning.ch",
        # Phase 2: Variable XP-Boost in Tests deaktivieren (sonst non-deterministisch)
        "XP_BOOST_PROBABILITY": 0.0,
        "UPLOAD_FOLDER": os.path.join(os.path.dirname(__file__), "test_uploads"),
        "ALLOWED_EXTENSIONS": {
            "image": {"png", "jpg", "jpeg", "gif", "webp"},
            "video": {"mp4", "webm", "ogg", "avi", "mov"},
            "audio": {"mp3", "wav", "ogg", "aac", "m4a"},
        },
    })
    yield app


@pytest.fixture(scope="function")
def db(app):
    """Frische Datenbank pro Test."""
    with app.app_context():
        # Letzte Schutzlinie vor dem destruktiven drop_all(): die gebundene
        # Engine MUSS eine SQLite- oder ausdrücklich als Test markierte DB sein.
        # Verhindert, dass Tests jemals echte Tabellen löschen.
        engine_url = str(_db.engine.url)
        assert engine_url.startswith("sqlite") or "test" in engine_url, (
            "SICHERHEITSABBRUCH: db-Fixture würde create_all/drop_all gegen "
            f"'{engine_url}' ausführen — das ist keine Test-Datenbank. "
            "Tests niemals gegen eine echte DB laufen lassen."
        )
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Flask Test-Client mit DB."""
    with app.app_context():
        yield app.test_client()


@pytest.fixture
def app_context(app, db):
    """App-Context für Tests die keinen Client brauchen."""
    with app.app_context():
        yield


@pytest.fixture
def auth_client(app, db):
    """Eingeloggter Standard-User (Free)."""
    from tests.factories import UserFactory
    with app.app_context():
        user = UserFactory()
        db.session.commit()

        client = app.test_client()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True
        yield client, user


@pytest.fixture
def admin_client(app, db):
    """Eingeloggter Admin-User."""
    from tests.factories import AdminUserFactory
    with app.app_context():
        admin = AdminUserFactory()
        db.session.commit()

        client = app.test_client()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(admin.id)
            sess["_fresh"] = True
        yield client, admin


@pytest.fixture
def premium_client(app, db):
    """Eingeloggter Premium-User."""
    from tests.factories import PremiumUserFactory
    with app.app_context():
        user = PremiumUserFactory()
        db.session.commit()

        client = app.test_client()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True
        yield client, user

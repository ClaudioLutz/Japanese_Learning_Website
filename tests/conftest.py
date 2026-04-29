# tests/conftest.py
"""
Globale Test-Fixtures für pytest.
Stellt App, DB, Client und Auth-Helpers bereit.
"""

import pytest
import os

# Umgebungsvariablen VOR dem App-Import setzen
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("WTF_CSRF_SECRET_KEY", "test-csrf-key")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")
os.environ.setdefault("MAIL_SUPPRESS_SEND", "true")

from app import create_app, db as _db


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

"""Sentry-Initialisierung: nur mit SENTRY_DSN, sonst keinerlei Wirkung."""
import sys
import types
from unittest.mock import MagicMock, patch

import app as app_module


def _fake_sentry_modules():
    sdk = types.ModuleType("sentry_sdk")
    sdk.init = MagicMock()
    integrations = types.ModuleType("sentry_sdk.integrations")
    flask_int = types.ModuleType("sentry_sdk.integrations.flask")
    flask_int.FlaskIntegration = MagicMock(return_value="FLASK_INTEGRATION")
    return sdk, {
        "sentry_sdk": sdk,
        "sentry_sdk.integrations": integrations,
        "sentry_sdk.integrations.flask": flask_int,
    }


def test_ohne_dsn_kein_init(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    sdk, modules = _fake_sentry_modules()
    with patch.dict(sys.modules, modules):
        assert app_module.init_sentry() is False
    sdk.init.assert_not_called()


def test_leerer_dsn_kein_init(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "   ")
    sdk, modules = _fake_sentry_modules()
    with patch.dict(sys.modules, modules):
        assert app_module.init_sentry() is False
    sdk.init.assert_not_called()


def test_app_startet_ohne_dsn(monkeypatch, app):
    """create_app laeuft ohne DSN normal (die app-Fixture baut sie)."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert app is not None
    assert app.config["SECRET_KEY"]


def test_mit_dsn_wird_init_aufgerufen(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SENTRY_RELEASE", "abc1234")
    sdk, modules = _fake_sentry_modules()
    with patch.dict(sys.modules, modules):
        assert app_module.init_sentry() is True
    kwargs = sdk.init.call_args.kwargs
    assert kwargs["dsn"] == "https://public@example.ingest.sentry.io/1"
    assert kwargs["traces_sample_rate"] == 0.0
    assert kwargs["send_default_pii"] is False
    assert kwargs["environment"] == "production"
    assert kwargs["release"] == "abc1234"
    assert kwargs["integrations"] == ["FLASK_INTEGRATION"]


def test_release_faellt_auf_commit_hash_zurueck(monkeypatch):
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    fake = MagicMock(returncode=0, stdout="deadbee\n")
    with patch("subprocess.run", return_value=fake):
        assert app_module._release_id() == "deadbee"
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert app_module._release_id() is None

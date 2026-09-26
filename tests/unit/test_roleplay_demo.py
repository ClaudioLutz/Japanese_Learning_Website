"""Unit-Tests: Token + Tageszaehler der Gast-Demo (services/roleplay_demo.py)."""
import pytest

from app.models import GuestDemoCounter
from app.services import roleplay_demo as demo
from app.services import roleplay_service as svc


@pytest.fixture
def ctx(app, db, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_DEMO_CONTENT_ID", 42)
    with app.test_request_context():
        yield


class TestToken:
    def test_roundtrip(self, ctx):
        state = {"v": 1, "c": 42, "n": 1, "h": [["b", "こんにちは"], ["u", "はい"]]}
        assert demo.read_token(demo.issue_token(state)) == state

    def test_tampered(self, ctx):
        token = demo.issue_token({"v": 1, "c": 42, "n": 0, "h": []})
        with pytest.raises(demo.DemoError) as exc:
            # Zeichen mitten in der Signatur tauschen (das letzte Base64-Zeichen traegt
            # Fuellbits — dessen Tausch aendert die Bytes nicht immer → war flaky).
            demo.read_token(token[:-10] + ("A" if token[-10] != "A" else "B") + token[-9:])
        assert exc.value.code == "demo_invalid"
        assert exc.value.http_status == 400

    def test_expired(self, ctx):
        token = demo.issue_token({"v": 1, "c": 42, "n": 0, "h": []})
        with pytest.raises(demo.DemoError) as exc:
            demo.read_token(token, max_age=-1)
        assert exc.value.code == "demo_expired"

    def test_other_scene_rejected(self, ctx):
        token = demo.issue_token({"v": 1, "c": 7, "n": 0, "h": []})
        with pytest.raises(demo.DemoError):
            demo.read_token(token)

    @pytest.mark.parametrize("bad", [None, "", 123, "x" * 20001])
    def test_garbage(self, ctx, bad):
        with pytest.raises(demo.DemoError):
            demo.read_token(bad)

    def test_other_salt_rejected(self, ctx, app):
        from itsdangerous import URLSafeTimedSerializer
        token = URLSafeTimedSerializer(app.secret_key, salt="anders").dumps({"v": 1, "c": 42, "n": 0, "h": []})
        with pytest.raises(demo.DemoError):
            demo.read_token(token)


class TestCounter:
    def test_reserve_until_limit(self, ctx):
        assert all(demo._reserve("k", 3) for _ in range(3))
        assert demo._reserve("k", 3) is False
        assert demo.count_for("k") == 3

    def test_release(self, ctx):
        demo._reserve("k", 3)
        demo._release("k")
        demo._release("k")   # nie unter 0
        assert demo.count_for("k") == 0

    def test_zero_limit(self, ctx):
        assert demo._reserve("k", 0) is False
        assert GuestDemoCounter.query.count() == 0

    def test_ip_hash_no_raw_ip(self, ctx):
        h = demo.ip_hash("203.0.113.9")
        assert "203" not in h and len(h) == 32
        assert h == demo.ip_hash("203.0.113.9") != demo.ip_hash("203.0.113.10")

    def test_reserve_turn_ip_limit(self, ctx):
        for _ in range(demo.IP_DAILY_LIMIT):
            demo.reserve_turn("198.51.100.1")
        with pytest.raises(svc.LimitReached):
            demo.reserve_turn("198.51.100.1")
        assert demo.count_for(demo.GLOBAL_KEY) == demo.IP_DAILY_LIMIT

    def test_reserve_turn_global_cap_releases_ip(self, ctx, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_GUEST_DAILY_CAP", 1)
        demo.reserve_turn("198.51.100.1")
        with pytest.raises(svc.CostCapReached):
            demo.reserve_turn("198.51.100.2")
        assert demo.count_for(demo.ip_hash("198.51.100.2")) == 0

    def test_guest_daily_cap_env(self, ctx, app, monkeypatch):
        assert demo.guest_daily_cap() == demo.GUEST_DAILY_CAP_DEFAULT
        monkeypatch.setenv("ROLEPLAY_GUEST_DAILY_CAP", "7")
        assert demo.guest_daily_cap() == 7
        monkeypatch.setenv("ROLEPLAY_GUEST_DAILY_CAP", "abc")
        assert demo.guest_daily_cap() == demo.GUEST_DAILY_CAP_DEFAULT


class TestMessages:
    def test_user_text_only_in_user_turns(self, ctx):
        msgs = demo.build_demo_messages([["b", "A"], ["u", "B"], ["b", "C"]], "D")
        assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant", "user"]
        assert msgs[-1]["content"] == "D"

    def test_malformed_history(self, ctx):
        with pytest.raises(demo.DemoError):
            demo.build_demo_messages([["b"]], "D")

    def test_prompt_turn_range(self, ctx):
        scene = {"lines": [], "scene_de": "Szene: Im Café."}
        text = svc.build_system_prompt(scene, "Lisa", "Tanaka", "Ziel", [], [], min_turns=3, max_turns=3)
        assert "genau 3 Züge" in text
        default = svc.build_system_prompt(scene, "Lisa", "Tanaka", "Ziel", [], [])
        assert "4 bis 8 Züge" in default

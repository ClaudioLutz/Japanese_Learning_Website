"""Integration-Tests fuer /api/roleplay/* (Rollenspiel-Tutor + „Frag zur Seite").

Provider ist durchgehend gemockt (kein echter Modell-/CLI-Aufruf).
"""
import json

import pytest

from app.gamification_service import XP_ROLEPLAY_COMPLETE
from app.models import RoleplaySession, RoleplayTurn, TutorQuestion, User
from app.services import roleplay_service as svc
from tests.factories import LessonContentFactory, LessonFactory, UserFactory

DIALOG = {"slides": [
    {"speaker": "Kellner", "jp": "いらっしゃいませ。", "de": "Willkommen."},
    {"speaker": "Gast", "jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte."},
    {"speaker": "Kellner", "jp": "はい、どうぞ。", "de": "Bitte schön."},
]}


def payload(done=False, correction=None):
    return {
        "bot_line_jp": "なにに しますか。",
        "reading_kana": "なにに しますか。",
        "de": "Was möchten Sie?",
        "suggestions": [{"jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte."},
                        {"jp": "おちゃを ください。", "de": "Einen Tee, bitte."},
                        {"jp": "みずを ください。", "de": "Wasser, bitte."}],
        "hint_de": "Bestelle ein Getränk.",
        "done": done,
        "correction": correction or [],
    }


class FakeProvider(svc.RoleplayProvider):
    name = "fake"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, system, messages, schema, *, system_suffix="", max_tokens=0):
        self.calls += 1
        r = self.responses.pop(0) if self.responses else svc.ProviderResult(data=payload())
        if isinstance(r, Exception):
            raise r
        return r


def ok(data):
    return svc.ProviderResult(data=data, usage=svc.Usage(tokens_in=100, tokens_out=40))


@pytest.fixture
def enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    return app


@pytest.fixture
def fake(monkeypatch):
    provider = FakeProvider([])
    monkeypatch.setattr(svc, "get_provider", lambda: provider)
    return provider


@pytest.fixture
def dialog(db):
    lesson = LessonFactory(title="Im Restaurant")
    content = LessonContentFactory(lesson_id=lesson.id, content_type="dialog_slideshow",
                                   content_text=json.dumps(DIALOG, ensure_ascii=False), page_number=2)
    db.session.commit()
    return content


ROUTES = [
    ("get", "/api/roleplay/scene/1", None),
    ("post", "/api/roleplay/start", {"content_id": 1, "role_user": "Gast"}),
    ("post", "/api/roleplay/1/turn", {"text": "はい"}),
    ("post", "/api/roleplay/1/end", {}),
    ("post", "/api/roleplay/tutor", {"lesson_id": 1, "page": 1, "question": "?"}),
]


class TestFeatureGate:
    @pytest.mark.parametrize("method,url,body", ROUTES)
    def test_flag_off_404_even_logged_in(self, auth_client, app, monkeypatch, method, url, body):
        monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", False)
        client, _ = auth_client
        resp = getattr(client, method)(url, json=body) if body is not None else client.get(url)
        assert resp.status_code == 404

    def test_flag_on_without_provider_404(self, auth_client, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
        monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "api")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        client, _ = auth_client
        assert client.get("/api/roleplay/scene/1").status_code == 404

    @pytest.mark.parametrize("method,url,body", ROUTES)
    def test_not_logged_in_redirects(self, client, enabled, method, url, body):
        resp = getattr(client, method)(url, json=body) if body is not None else client.get(url)
        assert resp.status_code in (301, 302)
        assert "/login" in resp.headers["Location"]

    def test_context_processor_flag(self, app, auth_client, monkeypatch):
        from flask import render_template_string
        with app.test_request_context("/"):
            assert render_template_string("{{ roleplay_enabled }}") == "False"
        monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
        monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
        monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://b")
        monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "t")
        with app.test_request_context("/"):
            assert render_template_string("{{ roleplay_enabled }}") == "True"


class TestScene:
    def test_scene(self, auth_client, enabled, dialog):
        client, _ = auth_client
        resp = client.get(f"/api/roleplay/scene/{dialog.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert [r["name"] for r in data["roles"]] == ["Kellner", "Gast"]
        assert "Gast" in data["goal_suggestions"]
        assert "lines" not in data
        assert data["limits"]["sessions_left"] == 5

    def test_non_dialog_404(self, auth_client, enabled, db):
        client, _ = auth_client
        lesson = LessonFactory()
        text = LessonContentFactory(lesson_id=lesson.id, content_type="text")
        db.session.commit()
        resp = client.get(f"/api/roleplay/scene/{text.id}")
        assert resp.status_code == 404
        assert resp.get_json()["error"] == "not_found"

    def test_unpublished_lesson_404(self, auth_client, enabled, db):
        client, _ = auth_client
        lesson = LessonFactory(is_published=False)
        c = LessonContentFactory(lesson_id=lesson.id, content_type="dialog_slideshow",
                                 content_text=json.dumps(DIALOG))
        db.session.commit()
        assert client.get(f"/api/roleplay/scene/{c.id}").status_code == 404


class TestLifecycle:
    def test_start_turns_end_awards_xp_once(self, auth_client, enabled, fake, dialog, db):
        client, user = auth_client
        fake.responses = [ok(payload()) for _ in range(5)] + [ok(payload(done=True, correction=[
            {"original": "コーヒー ください", "better": "コーヒーを ください。",
             "explanation_de": "Das Objekt bekommt を."}]))]

        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
        assert resp.status_code == 201
        data = resp.get_json()
        sid = data["session"]["id"]
        assert data["session"]["role_bot"] == "Kellner"
        assert data["bot_turn"]["jp"] == "なにに しますか。"
        assert len(data["bot_turn"]["suggestions"]) == 3
        assert data["limits"]["sessions_left"] == 4

        for i in range(4):
            resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "コーヒーを ください。"})
            assert resp.status_code == 200, resp.get_json()
            body = resp.get_json()
            assert body["done"] is False and body["xp_awarded"] == 0
        assert body["session"]["turn_count"] == 4

        resp = client.post(f"/api/roleplay/{sid}/end")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["xp_awarded"] == XP_ROLEPLAY_COMPLETE
        assert body["correction"][0]["better"] == "コーヒーを ください。"
        assert body["session"]["status"] == "completed"
        assert body["farewell"]["jp"]
        assert db.session.get(User, user.id).total_xp == XP_ROLEPLAY_COMPLETE

        # Idempotent: kein zweites XP, kein weiterer Modell-Aufruf.
        calls = fake.calls
        resp = client.post(f"/api/roleplay/{sid}/end")
        assert resp.get_json()["xp_awarded"] == XP_ROLEPLAY_COMPLETE
        assert fake.calls == calls
        assert db.session.get(User, user.id).total_xp == XP_ROLEPLAY_COMPLETE

        # Nach Abschluss: weiterer Zug abgelehnt.
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "もう一つ"})
        assert resp.status_code == 409
        assert resp.get_json()["error"] == "session_finished"

        users_turns = RoleplayTurn.query.filter_by(session_id=sid, speaker="user").count()
        assert users_turns == 4

    def test_bot_done_completes_via_turn(self, auth_client, enabled, fake, dialog, db):
        client, user = auth_client
        fake.responses = [ok(payload()) for _ in range(4)] + [ok(payload(done=True))]
        sid = client.post("/api/roleplay/start",
                          json={"content_id": dialog.id, "role_user": "Gast"}).get_json()["session"]["id"]
        for _ in range(3):
            client.post(f"/api/roleplay/{sid}/turn", json={"text": "はい"})
        body = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ありがとう"}).get_json()
        assert body["done"] is True
        assert body["xp_awarded"] == XP_ROLEPLAY_COMPLETE
        assert db.session.get(User, user.id).total_xp == XP_ROLEPLAY_COMPLETE

    def test_foreign_session_404(self, auth_client, enabled, fake, dialog, db):
        client, _ = auth_client
        other = UserFactory()
        s = RoleplaySession(user_id=other.id, lesson_content_id=dialog.id, role_user="Gast",
                            role_bot="Kellner")
        db.session.add(s)
        db.session.commit()
        assert client.post(f"/api/roleplay/{s.id}/turn", json={"text": "x"}).status_code == 404
        assert client.post(f"/api/roleplay/{s.id}/end").status_code == 404

    def test_invalid_role_400(self, auth_client, enabled, fake, dialog):
        client, _ = auth_client
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Koch"})
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "invalid_request"

    def test_custom_goal_stored(self, auth_client, enabled, fake, dialog, db):
        client, _ = auth_client
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast",
                                                        "goal": "Ich will zwei Kaffees bestellen."})
        assert resp.status_code == 201
        assert resp.get_json()["session"]["goal_de"] == "Ich will zwei Kaffees bestellen."


class TestLimitsAndErrors:
    def test_session_limit_reached(self, auth_client, enabled, fake, dialog, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_LIMIT_SESSIONS_PER_DAY", 1)
        client, _ = auth_client
        body = {"content_id": dialog.id, "role_user": "Gast"}
        assert client.post("/api/roleplay/start", json=body).status_code == 201
        resp = client.post("/api/roleplay/start", json=body)
        assert resp.status_code == 429
        data = resp.get_json()
        assert data["error"] == "limit_reached"
        assert "Morgen" in data["message"]

    def test_message_limit_reached(self, auth_client, enabled, fake, dialog, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_LIMIT_MESSAGES_PER_DAY", 1)
        client, _ = auth_client
        sid = client.post("/api/roleplay/start",
                          json={"content_id": dialog.id, "role_user": "Gast"}).get_json()["session"]["id"]
        assert client.post(f"/api/roleplay/{sid}/turn", json={"text": "はい"}).status_code == 200
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "はい"})
        assert resp.status_code == 429 and resp.get_json()["error"] == "limit_reached"

    def test_cost_cap(self, auth_client, enabled, fake, dialog, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_DAILY_COST_CAP_USD", 0)
        client, _ = auth_client
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
        assert resp.status_code == 503
        assert resp.get_json()["error"] == "cost_cap"

    def test_upstream_error_json_not_500(self, auth_client, enabled, fake, dialog):
        client, user = auth_client
        fake.responses = [svc.ProviderError("down", retryable=True), svc.ProviderError("down")]
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
        assert resp.status_code == 502
        data = resp.get_json()
        assert data["error"] == "upstream_error"
        assert data["message"]
        # Fehlstart ohne Kosten zaehlt nicht gegen das Tageslimit.
        assert RoleplaySession.query.filter_by(user_id=user.id).count() == 0

    def test_upstream_error_on_turn_keeps_session(self, auth_client, enabled, fake, dialog):
        client, _ = auth_client
        fake.responses = [ok(payload()), ok(None), ok(None)]
        sid = client.post("/api/roleplay/start",
                          json={"content_id": dialog.id, "role_user": "Gast"}).get_json()["session"]["id"]
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "はい"})
        assert resp.status_code == 502 and resp.get_json()["error"] == "upstream_error"
        # Nutzerzug wurde nicht verbucht → erneut senden moeglich.
        fake.responses = [ok(payload())]
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "はい"})
        assert resp.status_code == 200
        assert resp.get_json()["session"]["turn_count"] == 1

    def test_busy_bridge(self, auth_client, enabled, fake, dialog):
        client, _ = auth_client
        fake.responses = [svc.ProviderError("busy", busy=True)]
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
        assert resp.status_code == 502
        assert "beschäftigt" in resp.get_json()["message"]

    def test_empty_text_400(self, auth_client, enabled, fake, dialog):
        client, _ = auth_client
        sid = client.post("/api/roleplay/start",
                          json={"content_id": dialog.id, "role_user": "Gast"}).get_json()["session"]["id"]
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "   "})
        assert resp.status_code == 400 and resp.get_json()["error"] == "invalid_request"

    def test_rate_limit(self, auth_client, enabled, fake, dialog, rate_limited):
        client, _ = auth_client
        codes = [client.get(f"/api/roleplay/scene/{dialog.id}").status_code for _ in range(21)]
        assert codes[:20] == [200] * 20
        assert codes[20] == 429


class TestTutor:
    def test_tutor_answer(self, auth_client, enabled, fake, dialog, db):
        client, user = auth_client
        fake.responses = [ok({"answer": "を markiert das Objekt."})]
        resp = client.post("/api/roleplay/tutor",
                           json={"lesson_id": dialog.lesson_id, "page": 2, "question": "Wozu を?"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["answer"] == "を markiert das Objekt."
        assert data["limits"]["tutor_left"] == 19
        assert TutorQuestion.query.filter_by(user_id=user.id).count() == 1

    def test_tutor_missing_page(self, auth_client, enabled, fake, dialog):
        client, _ = auth_client
        resp = client.post("/api/roleplay/tutor",
                           json={"lesson_id": dialog.lesson_id, "page": 99, "question": "?"})
        assert resp.status_code == 404

    def test_tutor_invalid_body(self, auth_client, enabled, fake):
        client, _ = auth_client
        resp = client.post("/api/roleplay/tutor", json={"lesson_id": "x"})
        assert resp.status_code == 400

    def test_tutor_limit(self, auth_client, enabled, fake, dialog, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_LIMIT_TUTOR_PER_DAY", 0)
        client, _ = auth_client
        resp = client.post("/api/roleplay/tutor",
                           json={"lesson_id": dialog.lesson_id, "page": 2, "question": "?"})
        assert resp.status_code == 429 and resp.get_json()["error"] == "limit_reached"

    def test_tutor_upstream_error(self, auth_client, enabled, fake, dialog):
        client, user = auth_client
        fake.responses = [ok({"answer": ""}), ok({"answer": ""})]
        resp = client.post("/api/roleplay/tutor",
                           json={"lesson_id": dialog.lesson_id, "page": 2, "question": "?"})
        assert resp.status_code == 502 and resp.get_json()["error"] == "upstream_error"
        assert TutorQuestion.query.filter_by(user_id=user.id).count() == 0


class TestAdminViews:
    def test_admin_lists_readonly(self, admin_client, db):
        client, _ = admin_client
        for ep in ("admin_roleplay_sessions", "admin_roleplay_turns", "admin_tutor_questions"):
            assert client.get(f"/admin-panel/{ep}/").status_code == 200
            assert client.get(f"/admin-panel/{ep}/new/").status_code in (302, 403, 404)

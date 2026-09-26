"""Integration-Tests: Gast-Demo des Rollenspiels (Startseite) + Sprech-Hero.

Provider durchgehend gemockt (kein Modell-/CLI-Aufruf). Die Demo schreibt nur
den Tageszaehler guest_demo_counter — keine Gespraechstexte.
"""
import json

import pytest

from app.models import GuestDemoCounter, RoleplaySession, RoleplayTurn
from app.services import roleplay_demo as demo
from app.services import roleplay_service as svc
from tests.factories import LessonContentFactory, LessonFactory

DIALOG = {"slides": [
    {"speaker": "Tanaka", "jp": "リサさん、なにが のみたいですか？", "de": "Lisa, was möchtest du trinken?"},
    {"speaker": "Lisa", "jp": "こうちゃが のみたいです。", "de": "Ich möchte Schwarztee trinken."},
    {"speaker": "Tanaka", "jp": "いいですね。", "de": "Klingt gut."},
]}


def payload(done=False, correction=None):
    return {
        "bot_line_jp": "なにを たべたいですか。",
        "reading_kana": "なにを たべたいですか。",
        "de": "Was möchtest du essen?",
        "suggestions": [{"jp": "カレーが たべたいです。", "de": "Ich möchte Curry essen."},
                        {"jp": "サンドイッチを ください。", "de": "Ein Sandwich, bitte."},
                        {"jp": "わたしも カレーが いいです。", "de": "Ich nehme auch Curry."}],
        "hint_de": "Nenne ein Essen.",
        "done": done,
        "correction": correction or [],
    }


CORR = [{"original": "コーヒー ください", "better": "コーヒーを ください。",
         "explanation_de": "Das Objekt bekommt die Partikel を."}]


class FakeProvider(svc.RoleplayProvider):
    name = "fake"

    def __init__(self):
        self.responses = []
        self.calls = []

    def complete(self, system, messages, schema, *, system_suffix="", max_tokens=0):
        self.calls.append({"system": system, "messages": messages, "suffix": system_suffix})
        r = self.responses.pop(0) if self.responses else svc.ProviderResult(data=payload())
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    return app


@pytest.fixture
def fake(monkeypatch):
    provider = FakeProvider()
    monkeypatch.setattr(svc, "get_provider", lambda: provider)
    return provider


@pytest.fixture
def scene(app, db, monkeypatch):
    lesson = LessonFactory(title="Alltag & Essen 2", is_published=True, allow_guest_access=True)
    db.session.flush()
    content = LessonContentFactory(lesson_id=lesson.id, content_type="dialog_slideshow",
                                   content_text=json.dumps(DIALOG, ensure_ascii=False), page_number=2)
    db.session.commit()
    monkeypatch.setitem(app.config, "ROLEPLAY_DEMO_CONTENT_ID", content.id)
    return content


def start(client, **extra):
    return client.post("/api/roleplay/demo/start", json={"website": "", **extra})


def turn(client, token, text="こうちゃが のみたいです。", ip=None, **extra):
    headers = {"CF-Connecting-IP": ip} if ip else {}
    return client.post("/api/roleplay/demo/turn", json={"token": token, "text": text, "website": "", **extra},
                       headers=headers)


def ok(data):
    return svc.ProviderResult(data=data, usage=svc.Usage(tokens_in=100, tokens_out=40))


class TestFeatureGate:
    @pytest.mark.parametrize("url", ["/api/roleplay/demo/start", "/api/roleplay/demo/turn"])
    def test_flag_off_404(self, client, scene, url):
        assert client.post(url, json={}).status_code == 404

    def test_no_login_needed(self, client, enabled, scene):
        resp = start(client)
        assert resp.status_code == 201

    def test_scene_missing_404(self, client, enabled, app, monkeypatch, db):
        monkeypatch.setitem(app.config, "ROLEPLAY_DEMO_CONTENT_ID", 999999)
        resp = start(client)
        assert resp.status_code == 404
        assert resp.get_json()["error"] == "not_found"

    def test_scene_without_guest_access_404(self, client, enabled, scene, db):
        from app.models import Lesson
        lesson = db.session.get(Lesson, scene.lesson_id)
        lesson.allow_guest_access = False
        db.session.commit()
        assert start(client).status_code == 404


class TestStart:
    def test_start_static_opening_no_model_call(self, client, enabled, scene, fake):
        data = start(client).get_json()
        assert fake.calls == []
        assert data["token"]
        assert data["session"]["role_user"] == "Lisa"
        assert data["session"]["role_bot"] == "Tanaka"
        assert data["session"]["max_user_turns"] == 3
        assert data["bot_turn"]["jp"] == demo.DEMO_OPENING["jp"]
        assert len(data["bot_turn"]["suggestions"]) == 3
        assert data["scene"]["title"] == "Im Café"
        assert GuestDemoCounter.query.count() == 0

    def test_honeypot_rejected(self, client, enabled, scene, fake):
        resp = start(client, website="http://spam.example")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "invalid_request"


class TestTurns:
    def test_three_turns_then_done_with_correction(self, client, enabled, scene, fake):
        fake.responses = [ok(payload()), ok(payload()), ok(payload(done=False, correction=CORR))]
        token = start(client).get_json()["token"]
        r1 = turn(client, token).get_json()
        assert r1["done"] is False and r1["token"]
        assert r1["session"]["turn_count"] == 1
        r2 = turn(client, r1["token"]).get_json()
        assert r2["done"] is False
        r3 = turn(client, r2["token"]).get_json()
        # Dritter Zug: Server erzwingt das Ende (force_done).
        assert r3["done"] is True
        assert r3["token"] is None
        assert r3["xp_awarded"] == 0
        assert len(fake.calls) == 3
        assert "genau 3 Züge" in fake.calls[0]["system"]
        assert "letzte (3.)" in fake.calls[2]["suffix"]
        # Verlauf reist im Token: 3. Aufruf kennt alle frueheren Zuege.
        msgs = fake.calls[2]["messages"]
        assert msgs[0]["role"] == "user" and msgs[1]["role"] == "assistant"
        assert msgs[1]["content"] == demo.DEMO_OPENING["jp"]
        assert len(msgs) == 7
        # Nichts gespeichert ausser dem Zaehler.
        assert RoleplaySession.query.count() == 0
        assert RoleplayTurn.query.count() == 0

    def test_early_done_is_overridden(self, client, enabled, scene, fake):
        fake.responses = [ok(payload(done=True, correction=CORR))]
        token = start(client).get_json()["token"]
        r1 = turn(client, token).get_json()
        assert r1["done"] is False
        assert r1["correction"] == []

    def test_max_three_turns(self, client, enabled, scene, fake):
        state = {"v": 1, "c": scene.id, "n": 3, "h": [["b", "x"]]}
        with client.application.test_request_context():
            token = demo.issue_token(state)
        resp = turn(client, token)
        assert resp.status_code == 409
        assert resp.get_json()["error"] == "session_finished"
        assert fake.calls == []

    def test_text_too_long(self, client, enabled, scene, fake):
        token = start(client).get_json()["token"]
        resp = turn(client, token, text="あ" * 201)
        assert resp.status_code == 400
        assert fake.calls == []

    def test_empty_text(self, client, enabled, scene, fake):
        token = start(client).get_json()["token"]
        assert turn(client, token, text="  ").status_code == 400

    def test_honeypot_on_turn(self, client, enabled, scene, fake):
        token = start(client).get_json()["token"]
        resp = turn(client, token, website="x")
        assert resp.status_code == 400
        assert fake.calls == []

    def test_invalid_token_400(self, client, enabled, scene, fake):
        resp = turn(client, "kaputt.token.xyz")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "demo_invalid"
        assert turn(client, None).status_code == 400

    def test_expired_token_400(self, client, enabled, scene, fake, monkeypatch):
        import time as _time
        token = start(client).get_json()["token"]
        real = _time.time
        monkeypatch.setattr(_time, "time", lambda: real() + demo.TOKEN_MAX_AGE_S + 60)
        resp = turn(client, token)
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "demo_expired"
        assert fake.calls == []

    def test_upstream_error_releases_counter(self, client, enabled, scene, fake):
        fake.responses = [svc.ProviderError("x"), svc.ProviderError("x")]
        token = start(client).get_json()["token"]
        resp = turn(client, token)
        assert resp.status_code == 502
        with client.application.test_request_context():
            assert demo.count_for(demo.GLOBAL_KEY) == 0
            assert demo.count_for(demo.ip_hash("127.0.0.1")) == 0


class TestLimits:
    def test_ip_daily_limit(self, client, enabled, scene, fake):
        for _ in range(demo.IP_DAILY_LIMIT):
            token = start(client).get_json()["token"]
            assert turn(client, token, ip="10.0.0.1").status_code == 200
        token = start(client).get_json()["token"]
        resp = turn(client, token, ip="10.0.0.1")
        assert resp.status_code == 429
        body = resp.get_json()
        assert body["error"] == "limit_reached"
        assert body["message"] == demo.CAP_MESSAGE
        # Andere IP ist nicht betroffen.
        assert turn(client, token, ip="10.0.0.2").status_code == 200

    def test_global_daily_cap(self, client, enabled, scene, fake, app, monkeypatch):
        monkeypatch.setitem(app.config, "ROLEPLAY_GUEST_DAILY_CAP", 2)
        token = start(client).get_json()["token"]
        assert turn(client, token, ip="10.0.1.1").status_code == 200
        assert turn(client, token, ip="10.0.1.2").status_code == 200
        resp = turn(client, token, ip="10.0.1.3")
        assert resp.status_code == 503
        assert resp.get_json()["message"] == demo.CAP_MESSAGE
        with app.test_request_context():
            # IP-Reservierung wurde zurueckgegeben.
            assert demo.count_for(demo.ip_hash("10.0.1.3")) == 0
            assert demo.count_for(demo.GLOBAL_KEY) == 2

    def test_guest_turns_count_against_global_model_cap(self, client, enabled, scene, fake, app, monkeypatch):
        token = start(client).get_json()["token"]
        assert turn(client, token).status_code == 200
        with app.test_request_context():
            assert svc.model_replies_today() == 1
        monkeypatch.setitem(app.config, "ROLEPLAY_DAILY_MESSAGE_CAP", 1)
        resp = turn(client, token)
        assert resp.status_code == 503
        assert resp.get_json()["message"] == demo.CAP_MESSAGE

    def test_rate_limit_per_ip(self, client, enabled, scene, fake, rate_limited):
        codes = [start(client).status_code for _ in range(7)]
        assert codes[:6] == [201] * 6
        assert codes[6] == 429


class TestHomepageHero:
    def test_guest_speak_hero_with_flag(self, client, enabled, scene):
        LessonContentFactory(lesson_id=scene.lesson_id, content_type="dialog_slideshow",
                             content_text=json.dumps(DIALOG, ensure_ascii=False), page_number=3)
        from app import db
        db.session.commit()
        body = client.get("/").get_data(as_text=True)
        assert "Sprich Japanisch" in body and "vom ersten Tag an." in body
        assert "Übe echte Gespräche auf N5-Niveau, mit Antwortvorschlägen und Korrektur auf Deutsch." in body
        assert "2 Szenen aus den Lektionen." in body
        assert "Gespräch ausprobieren" in body
        assert "Kostenlos starten" in body
        assert "/register?next=/sprechen" in body or "/register?next=%2Fsprechen" in body
        # Gast-Demo (Panel im Demo-Modus) + Assets.
        assert 'id="gespraech-demo"' in body
        assert 'data-demo="1"' in body
        assert "/api/roleplay/demo/start" in body
        assert "roleplay_panel.js" in body and "roleplay_panel.css" in body
        assert "Frag zur Seite" not in body
        assert "Gespräch beenden" not in body
        # SEO: Begriffe in Text + Meta-Description.
        assert 'content="Japanisch sprechen üben' in body
        assert "Japanisch-Konversation für Anfänger" in body
        # Kana-Spiel bleibt (zweiter Block), H1 jetzt Sprechen, Hiragana als H2.
        assert "home-kana-block" in body
        assert "kana-hero-card" in body and "startStorm()" in body and "kana-hero-tabs" in body
        assert 'id="homeKanaTitle">Hiragana lernen' in body
        assert body.count("<h1") == 1

    def test_guest_hero_without_flag_unchanged(self, client, scene):
        body = client.get("/").get_data(as_text=True)
        assert "Sprich Japanisch" not in body
        assert "gespraech-demo" not in body
        assert "roleplay_panel.js" not in body
        assert "home-kana-block" not in body
        assert "Hiragana lernen —<br>fang mit einer Runde an.</h1>" in body

    def test_flag_on_but_demo_scene_missing_keeps_old_hero(self, client, enabled, app, monkeypatch, db):
        monkeypatch.setitem(app.config, "ROLEPLAY_DEMO_CONTENT_ID", 999999)
        body = client.get("/").get_data(as_text=True)
        assert "Sprich Japanisch" not in body
        assert "Hiragana lernen —<br>fang mit einer Runde an.</h1>" in body

    def test_logged_in_hero_unchanged(self, auth_client, enabled, scene):
        client, user = auth_client
        body = client.get("/").get_data(as_text=True)
        assert "Sprich Japanisch" not in body
        assert "gespraech-demo" not in body
        assert "home-kana-block" not in body
        assert user.username in body
        assert ("Bereit für" in body) or ("Weiter lernen." in body)

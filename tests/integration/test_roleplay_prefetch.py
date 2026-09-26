"""Vorausberechnung der Antwortvorschlaege (roleplay_prefetch).

Provider durchgehend gemockt. Die Vorausberechnung laeuft in den Tests
synchron (ROLEPLAY_PREFETCH_SYNC) statt im Thread-Pool.
"""
import json
from datetime import datetime, timedelta

import pytest

from app.models import GuestDemoCounter, RoleplayPrefetch, RoleplaySession, RoleplayTurn
from app.services import roleplay_demo as demo
from app.services import roleplay_prefetch as prefetch
from app.services import roleplay_service as svc
from tests.factories import LessonContentFactory, LessonFactory

DIALOG = {"slides": [
    {"speaker": "Kellner", "jp": "いらっしゃいませ。", "de": "Willkommen."},
    {"speaker": "Gast", "jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte."},
    {"speaker": "Kellner", "jp": "はい、どうぞ。", "de": "Bitte schön."},
]}
DEMO_DIALOG = {"slides": [
    {"speaker": "Tanaka", "jp": "リサさん、なにが のみたいですか？", "de": "Lisa, was möchtest du trinken?"},
    {"speaker": "Lisa", "jp": "こうちゃが のみたいです。", "de": "Ich möchte Schwarztee trinken."},
]}
SUGG = [{"jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte."},
        {"jp": "おちゃを ください。", "de": "Einen Tee, bitte."},
        {"jp": "みずを ください。", "de": "Wasser, bitte."}]


def payload(line="なにに しますか。", done=False, correction=None):
    return {"bot_line_jp": line, "reading_kana": line, "de": "Was möchten Sie?",
            "suggestions": [] if done else SUGG, "hint_de": "Tipp.", "done": done,
            "correction": correction or []}


class EchoProvider(svc.RoleplayProvider):
    """Antwortet mit einer Zeile, die den letzten Nutzertext enthaelt.
    Wie get_provider() in Produktion: pro Aufruf eine neue Instanz, gemeinsames Protokoll."""
    name = "echo"

    def __init__(self, calls):
        self.calls = calls
        self.priority = "high"

    def complete(self, system, messages, schema, *, system_suffix="", max_tokens=0):
        last = messages[-1]["content"]
        self.calls.append({"last": last, "priority": self.priority})
        return svc.ProviderResult(data=payload(line=f"「{last}」ですね。"),
                                  usage=svc.Usage(tokens_in=10, tokens_out=5))


class ForbiddenProvider(svc.RoleplayProvider):
    name = "forbidden"

    def __init__(self, calls=None):
        pass

    def complete(self, *a, **k):
        raise AssertionError("Provider darf bei einem Cache-Treffer nicht aufgerufen werden")


@pytest.fixture
def enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH", "1")
    monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH_SYNC", "1")
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    return app


class Holder:
    def __init__(self):
        self.cls = EchoProvider
        self.calls = []

    def make(self):
        return self.cls(self.calls)


@pytest.fixture
def provider(monkeypatch):
    holder = Holder()
    monkeypatch.setattr(svc, "get_provider", holder.make)
    return holder


@pytest.fixture
def dialog(db):
    lesson = LessonFactory(title="Im Restaurant")
    content = LessonContentFactory(lesson_id=lesson.id, content_type="dialog_slideshow",
                                   content_text=json.dumps(DIALOG, ensure_ascii=False), page_number=2)
    db.session.commit()
    return content


def _start(client, dialog):
    resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


# ── Normalisierung / Aufraeumen / Nachschlagen ───────────────────────────

class TestNormalize:
    @pytest.mark.parametrize("a,b", [
        ("コーヒーを ください。", "コーヒーをください"),
        ("コーヒーを　ください！", "コーヒーを ください。"),      # Vollbreiten-Leerzeichen, ！
        ("はい、そうです。", "はい そうです"),
        ("ＡＢＣ？", "ABC"),                                       # NFKC
    ])
    def test_equal(self, a, b):
        assert prefetch.normalize(a) == prefetch.normalize(b)

    def test_different(self):
        assert prefetch.normalize("おちゃを ください。") != prefetch.normalize("みずを ください。")
        assert prefetch.normalize("コーヒー") != prefetch.normalize("コーヒ")   # ー bleibt

    def test_empty(self):
        assert prefetch.normalize("  。 ") == ""
        assert prefetch.normalize(None) == ""


def _row(db, **kw):
    base = dict(session_id=1, turn_index=0, user_text="コーヒーを ください。",
                norm_text=prefetch.normalize("コーヒーを ください。"), status="ready",
                response_json=json.dumps(payload(line="はい、どうぞ。"), ensure_ascii=False))
    base.update(kw)
    row = RoleplayPrefetch(**base)
    db.session.add(row)
    db.session.commit()
    return row


class TestTakeAndCleanup:
    def test_hit_marks_used(self, app, db):
        row = _row(db)
        data = prefetch.take(session_id=1, turn_index=0, text="コーヒーをください")
        db.session.commit()
        assert data["bot_line_jp"] == "はい、どうぞ。"
        assert db.session.get(RoleplayPrefetch, row.id).status == "used"
        # Zweites Mal kein Treffer mehr (schon verbraucht).
        assert prefetch.take(session_id=1, turn_index=0, text="コーヒーをください") is None

    @pytest.mark.parametrize("kw,text", [
        ({}, "おちゃを ください。"),                       # anderer Text
        ({"turn_index": 1}, "コーヒーを ください。"),       # anderer Zug
        ({"session_id": 2}, "コーヒーを ください。"),       # andere Session
        ({"status": "failed", "response_json": None}, "コーヒーを ください。"),
        ({"status": "stale"}, "コーヒーを ください。"),
    ])
    def test_miss(self, app, db, kw, text):
        _row(db, **kw)
        assert prefetch.take(session_id=1, turn_index=0, text=text) is None

    def test_orphaned_pending_not_awaited(self, app, db):
        _row(db, status="pending", response_json=None,
             created_at=datetime.utcnow() - timedelta(minutes=5))
        t0 = datetime.utcnow()
        assert prefetch.take(session_id=1, turn_index=0, text="コーヒーを ください。") is None
        assert (datetime.utcnow() - t0).total_seconds() < 1

    def test_demo_key_separate(self, app, db):
        _row(db, session_id=None, demo_key="abc")
        assert prefetch.take(session_id=1, turn_index=0, text="コーヒーを ください。") is None
        assert prefetch.take(demo="abc", turn_index=0, text="コーヒーを ください。") is not None

    def test_consume_clears_rest(self, app, db):
        a = _row(db)
        b = _row(db, user_text="おちゃ", norm_text="おちゃ")
        prefetch.take(session_id=1, turn_index=0, text="コーヒーを ください。")
        prefetch.consume(session_id=1, turn_index=0)
        db.session.commit()
        db.session.expire_all()
        assert db.session.get(RoleplayPrefetch, a.id).status == "used"
        rest = db.session.get(RoleplayPrefetch, b.id)
        assert rest.status == "stale" and rest.response_json is None

    def test_cleanup_old(self, app, db):
        old = _row(db, created_at=datetime.utcnow() - timedelta(hours=25))
        new = _row(db, created_at=datetime.utcnow() - timedelta(hours=23))
        old_id, new_id = old.id, new.id
        assert prefetch.cleanup_old() == 1
        assert {r.id for r in RoleplayPrefetch.query.all()} == {new_id} != {old_id}

    def test_count_today_excludes_used(self, app, db):
        _row(db, status="used")
        _row(db, status="stale")
        _row(db, status="pending")
        _row(db, status="ready", created_at=datetime.utcnow() - timedelta(days=2))
        assert prefetch.count_today() == 2
        assert svc.model_replies_today() == 2

    def test_prefetch_cost_counts_for_cost_cap(self, app, db):
        _row(db, cost_usd=1.5)
        assert svc.cost_today() == pytest.approx(1.5)


# ── Eingeloggt: /start + /turn ───────────────────────────────────────────

class TestSessionPrefetch:
    def test_start_prefetches_three_suggestions(self, auth_client, enabled, provider, dialog, db):
        client, _ = auth_client
        data = _start(client, dialog)
        rows = RoleplayPrefetch.query.filter_by(session_id=data["session"]["id"]).all()
        assert sorted(r.user_text for r in rows) == sorted(s["jp"] for s in SUGG)
        assert all(r.status == "ready" and r.turn_index == 0 for r in rows)
        # 1 Eroeffnung (Live, high) + 3 Vorausberechnungen (low)
        p = provider
        assert [c["priority"] for c in p.calls] == ["high", "low", "low", "low"]
        # Vorausberechnung zaehlt nicht gegen Nutzerlimits
        assert data["limits"]["messages_left"] == 60

    def test_turn_cache_hit_without_provider_call(self, auth_client, enabled, provider, dialog, db, app,
                                                  monkeypatch):
        client, _ = auth_client
        sid = _start(client, dialog)["session"]["id"]
        monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH", "0")   # keine neue Vorausberechnung
        provider.cls = ForbiddenProvider
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "おちゃを　ください"})
        assert resp.status_code == 200, resp.get_json()
        body = resp.get_json()
        assert body["bot_turn"]["jp"] == "「おちゃを ください。」ですね。"
        assert body["session"]["turn_count"] == 1
        assert body["limits"]["messages_left"] == 59        # Zug normal verbucht
        turns = RoleplayTurn.query.filter_by(session_id=sid).order_by(RoleplayTurn.turn_index).all()
        assert [t.speaker for t in turns] == ["bot", "user", "bot"]
        assert turns[1].text_jp == "おちゃを　ください"
        statuses = sorted(r.status for r in RoleplayPrefetch.query.filter_by(session_id=sid))
        assert statuses == ["stale", "stale", "used"]
        assert all(r.response_json is None for r in RoleplayPrefetch.query.filter_by(status="stale"))

    def test_turn_freetext_calls_provider_and_prefetches_next(self, auth_client, enabled, provider, dialog, db):
        client, _ = auth_client
        sid = _start(client, dialog)["session"]["id"]
        p = provider
        n = len(p.calls)
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ビールを ください。"})
        assert resp.status_code == 200
        assert resp.get_json()["bot_turn"]["jp"] == "「ビールを ください。」ですね。"
        new_calls = p.calls[n:]
        assert new_calls[0] == {"last": "ビールを ください。", "priority": "high"}
        assert [c["priority"] for c in new_calls[1:]] == ["low", "low", "low"]
        assert RoleplayPrefetch.query.filter_by(session_id=sid, turn_index=1, status="ready").count() == 3

    def test_message_limit_applies_to_cache_hit(self, auth_client, enabled, provider, dialog, app, monkeypatch):
        client, _ = auth_client
        sid = _start(client, dialog)["session"]["id"]
        monkeypatch.setitem(app.config, "ROLEPLAY_LIMIT_MESSAGES_PER_DAY", 0)
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "おちゃを ください。"})
        assert resp.status_code == 429

    def test_cache_hit_allowed_at_global_cap(self, auth_client, enabled, provider, dialog, app, monkeypatch):
        client, _ = auth_client
        sid = _start(client, dialog)["session"]["id"]
        monkeypatch.setitem(app.config, "ROLEPLAY_DAILY_MESSAGE_CAP", 1)
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "おちゃを ください。"})
        assert resp.status_code == 200          # kein neuer Modell-Aufruf noetig
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ビールを ください。"})
        assert resp.status_code == 503          # Freitext braucht das Modell → Kappe

    def test_no_prefetch_when_cap_would_be_exceeded(self, auth_client, enabled, provider, dialog, app,
                                                    monkeypatch):
        client, _ = auth_client
        monkeypatch.setitem(app.config, "ROLEPLAY_DAILY_MESSAGE_CAP", 3)   # 1 Eroeffnung + 3 > 3
        sid = _start(client, dialog)["session"]["id"]
        assert RoleplayPrefetch.query.filter_by(session_id=sid).count() == 0
        assert len(provider.calls) == 1

    def test_prefetch_counts_against_global_cap(self, auth_client, enabled, provider, dialog, db):
        client, _ = auth_client
        _start(client, dialog)
        assert svc.model_replies_today() == 4       # 1 Bot-Zug + 3 Vorausberechnungen

    def test_start_cleans_up_old_rows(self, auth_client, enabled, provider, dialog, db):
        client, _ = auth_client
        old = _row(db, session_id=999, created_at=datetime.utcnow() - timedelta(hours=30))
        assert old.session_id == 999
        _start(client, dialog)
        assert RoleplayPrefetch.query.filter_by(session_id=999).count() == 0

    def test_prefetch_failure_does_not_break_turn(self, auth_client, enabled, dialog, db, monkeypatch):
        client, _ = auth_client

        class Flaky(EchoProvider):
            def complete(self, system, messages, schema, **kw):
                if self.priority == "low":
                    raise svc.ProviderError("bridge_busy", busy=True)
                return super().complete(system, messages, schema, **kw)
        monkeypatch.setattr(svc, "get_provider", lambda: Flaky([]))
        sid = _start(client, dialog)["session"]["id"]
        assert RoleplayPrefetch.query.filter_by(session_id=sid, status="failed").count() == 3
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "おちゃを ください。"})
        assert resp.status_code == 200      # Fallback: regulaerer Aufruf

    def test_stale_session_job_is_skipped(self, auth_client, enabled, provider, dialog, db, app, monkeypatch):
        """Ein Job fuer einen alten Zug rechnet nicht mehr (Session ist weiter)."""
        client, _ = auth_client
        monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH", "0")
        sid = _start(client, dialog)["session"]["id"]
        session = db.session.get(RoleplaySession, sid)
        row = RoleplayPrefetch(session_id=sid, turn_index=5, user_text="x", norm_text="x", status="pending")
        db.session.add(row)
        db.session.commit()
        n = len(provider.calls)
        prefetch._session_job(app, True, row.id)
        assert len(provider.calls) == n
        assert db.session.get(RoleplayPrefetch, row.id).status == "stale"
        assert session.status == "active"


class TestBridgePriority:
    def test_priority_sent(self):
        sent = {}

        class Http:
            def post(self, url, json, headers, timeout):
                sent.update(json)
                return type("R", (), {"status_code": 200, "json": lambda self: {"data": {}, "usage": {}}})()
        p = svc.ClaudeCliBridgeProvider("http://b", "t", http=Http())
        p.complete("S", [{"role": "user", "content": "x"}], {"type": "object"})
        assert sent["priority"] == "high"
        p.priority = "low"
        p.complete("S", [{"role": "user", "content": "x"}], {"type": "object"})
        assert sent["priority"] == "low"


# ── Gast-Demo ────────────────────────────────────────────────────────────

@pytest.fixture
def demo_scene(app, db, monkeypatch):
    lesson = LessonFactory(title="Alltag & Essen 2", is_published=True, allow_guest_access=True)
    db.session.flush()
    content = LessonContentFactory(lesson_id=lesson.id, content_type="dialog_slideshow",
                                   content_text=json.dumps(DEMO_DIALOG, ensure_ascii=False), page_number=2)
    db.session.commit()
    monkeypatch.setitem(app.config, "ROLEPLAY_DEMO_CONTENT_ID", content.id)
    return content


def _demo_start(client):
    resp = client.post("/api/roleplay/demo/start", json={"website": ""})
    assert resp.status_code == 201
    return resp.get_json()


class TestDemoPrefetch:
    def test_start_prefetches_opening_suggestions(self, client, enabled, provider, demo_scene, db):
        data = _demo_start(client)
        rows = RoleplayPrefetch.query.all()
        assert len(rows) == 3
        assert all(r.session_id is None and r.demo_key == prefetch.demo_key(data["token"]) for r in rows)
        assert {r.user_text for r in rows} == {s["jp"] for s in demo.DEMO_OPENING["suggestions"]}
        assert all(r.status == "ready" for r in rows)
        # Start zaehlt nicht gegen die Gast-Limits
        assert GuestDemoCounter.query.count() == 0
        # Keine Gespraeche gespeichert
        assert RoleplaySession.query.count() == 0

    def test_suggestion_turn_from_cache(self, client, enabled, provider, demo_scene, db, app, monkeypatch):
        data = _demo_start(client)
        monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH", "0")
        provider.cls = ForbiddenProvider
        text = demo.DEMO_OPENING["suggestions"][1]["jp"]
        resp = client.post("/api/roleplay/demo/turn", json={"token": data["token"], "text": text, "website": ""})
        assert resp.status_code == 200, resp.get_json()
        body = resp.get_json()
        assert body["bot_turn"]["jp"] == f"「{text}」ですね。"
        assert body["token"]
        # Zug zaehlt normal gegen IP-Limit/Gast-Kappe
        assert demo.count_for(demo.GLOBAL_KEY) == 1
        # Verbrauchte Vorausberechnungen tragen keine Antworttexte mehr
        assert RoleplayPrefetch.query.filter(RoleplayPrefetch.response_json.isnot(None)).count() == 0
        assert RoleplaySession.query.count() == 0

    def test_freetext_calls_provider_and_prefetches_next(self, client, enabled, provider, demo_scene, db):
        data = _demo_start(client)
        p = provider
        n = len(p.calls)
        resp = client.post("/api/roleplay/demo/turn",
                           json={"token": data["token"], "text": "ジュースが いいです。", "website": ""})
        assert resp.status_code == 200
        new = p.calls[n:]
        assert new[0]["priority"] == "high" and new[0]["last"] == "ジュースが いいです。"
        body = resp.get_json()
        key = prefetch.demo_key(body["token"])
        assert RoleplayPrefetch.query.filter_by(demo_key=key, turn_index=1, status="ready").count() == 3

    def test_last_turn_no_further_prefetch(self, client, enabled, provider, demo_scene, db):
        data = _demo_start(client)
        tok = data["token"]
        for _ in range(3):
            body = client.post("/api/roleplay/demo/turn",
                               json={"token": tok, "text": "ジュースが いいです。", "website": ""}).get_json()
            tok = body["token"]
        assert body["done"] is True and tok is None
        # Nach Zug 2 wurde fuer Zug 3 vorausberechnet, nach Zug 3 nichts mehr.
        assert RoleplayPrefetch.query.filter_by(turn_index=3).count() == 0

    def test_no_prefetch_when_guest_ip_exhausted(self, client, enabled, provider, demo_scene, db, monkeypatch):
        monkeypatch.setattr(demo, "IP_DAILY_LIMIT", 0)
        _demo_start(client)
        assert RoleplayPrefetch.query.count() == 0

"""Zweigeteilter Rollenspiel-Zug (Sofort-Antwort): erst die Bot-Zeile, Lernhilfen
per zweitem Aufruf im Hintergrund, Nachladen ueber /details; Stream-Routen (SSE).

Provider durchgehend gemockt. Hintergrund-Jobs werden abgefangen und im Test
von Hand ausgefuehrt, damit „erste Antwort ohne Details, Details spaeter" pruefbar ist.
"""
import json

import pytest

from app.models import RoleplayPrefetch, RoleplaySession, RoleplayTurn
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
SUGG = [{"jp": "コーヒーを ください。", "reading_kana": "コーヒーを ください。", "de": "Einen Kaffee, bitte."},
        {"jp": "おちゃを ください。", "reading_kana": "おちゃを ください。", "de": "Einen Tee, bitte."},
        {"jp": "みずを ください。", "reading_kana": "みずを ください。", "de": "Wasser, bitte."}]
CORR = [{"original": "コーヒー ください", "better": "コーヒーを ください。", "better_kana": "コーヒーを ください。",
         "explanation_de": "Das Objekt bekommt die Partikel を."}]
# Serverseitig abgeleitete Romaji (API-Antworten)
SUGG_API = [dict(s, romaji=r) for s, r in zip(SUGG, ["Kōhī o kudasai.", "Ocha o kudasai.", "Mizu o kudasai."])]
CORR_API = [dict(CORR[0], better_romaji="Kōhī o kudasai.")]
LINE = "ケーキも ありますよ。"


class SplitProvider(svc.RoleplayProvider):
    """Antwortet je nach Schema: Zeile, Details oder voller Zug. Protokolliert jeden Aufruf."""
    name = "split"

    def __init__(self, log):
        self.log = log
        self.priority = "high"

    def complete(self, system, messages, schema, *, system_suffix="", max_tokens=0, fast=False):
        kind = ("line" if schema is svc.LINE_SCHEMA else
                "details" if schema is svc.DETAILS_SCHEMA else "full")
        self.log.calls.append({"kind": kind, "fast": fast, "messages": messages, "suffix": system_suffix,
                               "priority": self.priority})
        fail = self.log.fail.get(kind)
        if fail:
            raise fail
        usage = svc.Usage(tokens_in=10, tokens_out=5)
        if kind == "line":
            return svc.ProviderResult(data={"bot_line_jp": LINE, "done": self.log.line_done}, usage=usage)
        if kind == "details":
            done = "beendet" in system_suffix
            return svc.ProviderResult(data={
                "reading_kana": "けーきも ありますよ。", "de": "Es gibt auch Kuchen.",
                "suggestions": [] if done else SUGG, "hint_de": "Bestell etwas.",
                "correction": CORR if done else []}, usage=usage)
        last = messages[-1]["content"]
        return svc.ProviderResult(data={
            "bot_line_jp": f"「{last}」ですね。", "reading_kana": "はい。", "de": "Gut.",
            "suggestions": [] if "letzte" in system_suffix else SUGG, "hint_de": "Tipp.",
            "done": "letzte" in system_suffix, "correction": CORR if "letzte" in system_suffix else []},
            usage=usage)

    def stream(self, system, messages, schema, *, system_suffix="", max_tokens=0, fast=False):
        result = self.complete(system, messages, schema, system_suffix=system_suffix, fast=fast)
        text = json.dumps(result.data, ensure_ascii=False)
        for i in range(0, len(text), 4):   # in kleinen Stuecken wie ein echter Stream
            yield text[i:i + 4]
        return result


class Log:
    def __init__(self):
        self.calls = []
        self.fail = {}
        self.line_done = False
        self.jobs = []

    def kinds(self):
        return [c["kind"] for c in self.calls]


@pytest.fixture
def log(app, monkeypatch):
    log = Log()
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setitem(app.config, "ROLEPLAY_SPLIT_TURN", "1")
    monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH", "1")
    monkeypatch.setitem(app.config, "ROLEPLAY_PREFETCH_SYNC", "1")
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    monkeypatch.setattr(svc, "get_provider", lambda: SplitProvider(log))

    def capture(fn, *args, details=False):
        log.jobs.append((fn, args, details))
    monkeypatch.setattr(prefetch, "_submit", capture)
    return log


def run_jobs(app, log, only_details=None):
    """Abgefangene Hintergrund-Jobs ausfuehren (synchron, wie ROLEPLAY_PREFETCH_SYNC)."""
    kept = []
    while log.jobs:
        fn, args, details = log.jobs.pop(0)
        if only_details is not None and details != only_details:
            kept.append((fn, args, details))
            continue
        fn(app, True, *args)
    log.jobs.extend(kept)


@pytest.fixture
def dialog(db):
    lesson = LessonFactory(title="Im Restaurant")
    content = LessonContentFactory(lesson_id=lesson.id, content_type="dialog_slideshow",
                                   content_text=json.dumps(DIALOG, ensure_ascii=False), page_number=2)
    db.session.commit()
    return content


def _start(client, dialog, app, log):
    resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    run_jobs(app, log, only_details=True)
    log.jobs.clear()          # Vorausberechnungen des Starts interessieren hier nicht
    return data


def sse_events(resp):
    events = []
    for block in resp.get_data(as_text=True).split("\n\n"):
        if not block.strip():
            continue
        ev = next(line[6:].strip() for line in block.split("\n") if line.startswith("event:"))
        data = json.loads(next(line[5:].strip() for line in block.split("\n") if line.startswith("data:")))
        events.append((ev, data))
    return events


# ── Eingeloggt ───────────────────────────────────────────────────────────

class TestStart:
    def test_start_returns_line_first(self, auth_client, dialog, log, app):
        client, _ = auth_client
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
        bot = resp.get_json()["bot_turn"]
        assert bot["jp"] == LINE and bot["details_pending"] is True and bot["suggestions"] == []
        assert log.kinds() == ["line"] and log.calls[0]["fast"] is True
        run_jobs(app, log, only_details=True)
        assert log.kinds() == ["line", "details"]
        sid = resp.get_json()["session"]["id"]
        det = client.get(f"/api/roleplay/{sid}/turn/{bot['turn_index']}/details").get_json()
        assert det["status"] == "ready" and det["bot_turn"]["suggestions"] == SUGG_API


class TestFreitextTurn:
    def test_first_answer_without_details_then_details(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        log.calls.clear()

        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"})
        assert resp.status_code == 200
        data = resp.get_json()
        bot = data["bot_turn"]
        assert bot["jp"] == LINE
        assert bot["details_pending"] is True
        assert bot["suggestions"] == [] and bot["reading_kana"] == "" and bot["de"] == ""
        assert data["session"]["turn_count"] == 1 and data["done"] is False
        assert log.kinds() == ["line"]
        # Zug ist verbucht (atomar beim ersten Aufruf): Eroeffnung + Nutzer- + Bot-Zeile
        assert RoleplayTurn.query.filter_by(session_id=sid).count() == 3

        url = f"/api/roleplay/{sid}/turn/{bot['turn_index']}/details"
        assert client.get(url).get_json() == {"status": "pending", "bot_turn": None}

        run_jobs(app, log, only_details=True)
        det = client.get(url).get_json()
        assert det["status"] == "ready"
        assert det["bot_turn"]["suggestions"] == SUGG_API
        assert det["bot_turn"]["de"] == "Es gibt auch Kuchen."
        assert det["bot_turn"]["jp"] == LINE                    # Zeile unveraendert
        assert det["bot_turn"]["details_pending"] is False
        # Zweiter Aufruf: Zeile als Vorgabe (assistant) + Steuersignal, nicht fast
        call = log.calls[-1]
        assert call["kind"] == "details" and call["fast"] is False
        assert call["messages"][-2] == {"role": "assistant", "content": LINE}
        assert call["messages"][-1]["content"] == svc.DETAILS_USER_TEXT
        assert call["messages"][-3]["content"] == "ケーキは ありますか。"

    def test_prefetch_starts_after_details(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"})
        assert [j[2] for j in log.jobs] == [True]            # nur der Details-Job
        run_jobs(app, log, only_details=True)
        rows = RoleplayPrefetch.query.filter_by(session_id=sid, turn_index=1).all()
        assert sorted(r.norm_text != "" for r in rows) == [False, True, True, True]

    def test_details_count_as_own_model_call(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        before = svc.model_replies_today()
        client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"})
        assert svc.model_replies_today() == before + 2        # Bot-Zug + Details-Zeile
        # ... aber nur eine Nutzer-Nachricht
        assert svc.limits_status(auth_client[1].id)["messages_left"] == \
            svc.limit_value("ROLEPLAY_LIMIT_MESSAGES_PER_DAY") - 1

    def test_details_failure(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        log.fail["details"] = svc.ProviderError("bridge_http_502", retryable=False)
        bot = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"}).get_json()["bot_turn"]
        run_jobs(app, log)
        det = client.get(f"/api/roleplay/{sid}/turn/{bot['turn_index']}/details").get_json()
        assert det == {"status": "failed", "bot_turn": None}
        # Keine Vorausberechnung ohne Vorschlaege; Freitext geht weiter
        assert RoleplayPrefetch.query.filter(RoleplayPrefetch.session_id == sid, RoleplayPrefetch.turn_index == 1,
                                             RoleplayPrefetch.norm_text != "").count() == 0
        del log.fail["details"]
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "じゃあ、ケーキを ください。"})
        assert resp.status_code == 200 and resp.get_json()["session"]["turn_count"] == 2
        # Wiedergabe des gescheiterten Zugs im Verlauf: ohne Vorschlaege
        turn = RoleplayTurn.query.filter_by(session_id=sid, turn_index=bot["turn_index"]).one()
        assert svc.serialize_bot_turn(turn)["details_failed"] is True

    def test_line_failure_not_booked(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        log.fail["line"] = svc.ProviderError("bridge_http_502", retryable=False)
        resp = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"})
        assert resp.status_code == 502
        assert db_turn_count(sid) == 0

    def test_stale_pending_counts_as_failed(self, auth_client, dialog, log, app, db):
        from datetime import datetime, timedelta
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        bot = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"}).get_json()["bot_turn"]
        turn = RoleplayTurn.query.filter_by(session_id=sid, turn_index=bot["turn_index"]).one()
        turn.created_at = datetime.utcnow() - timedelta(seconds=svc.DETAILS_STALE_S + 5)
        db.session.commit()
        assert client.get(f"/api/roleplay/{sid}/turn/{bot['turn_index']}/details").get_json()["status"] == "failed"

    def test_details_skipped_when_user_moved_on(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"})
        client.post(f"/api/roleplay/{sid}/turn", json={"text": "じゃあ、ケーキを ください。"})
        n = len(log.calls)
        fn, args, _d = log.jobs.pop(0)          # Details-Job des ersten Zugs kommt zu spaet
        fn(app, True, *args)
        assert len(log.calls) == n               # kein Modell-Aufruf mehr

    def test_details_404_for_unknown_turn_and_foreign_session(self, auth_client, dialog, log, app, db):
        from tests.factories import UserFactory
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        assert client.get(f"/api/roleplay/{sid}/turn/99/details").status_code == 404
        other = UserFactory()
        db.session.commit()
        foreign = RoleplaySession(user_id=other.id, lesson_content_id=dialog.id, role_user="Gast",
                                  role_bot="Kellner", status="active")
        db.session.add(foreign)
        db.session.commit()
        assert client.get(f"/api/roleplay/{foreign.id}/turn/0/details").status_code == 404

    def test_model_done_early_keeps_playing(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        log.line_done = True
        data = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"}).get_json()
        assert data["done"] is False and data["bot_turn"]["details_pending"] is True

    def test_model_done_after_min_turns_fetches_correction(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        for i in range(3):
            client.post(f"/api/roleplay/{sid}/turn", json={"text": f"テスト{i}です。"})
        log.line_done = True
        log.calls.clear()
        data = client.post(f"/api/roleplay/{sid}/turn", json={"text": "ありがとう ございました。"}).get_json()
        assert data["done"] is True and data["correction"] == CORR_API
        assert data["session"]["status"] == "completed"
        assert log.kinds() == ["line", "details"]             # Korrektur synchron mitgeholt
        assert data["bot_turn"]["details_pending"] is False

    def test_last_turn_single_full_call(self, auth_client, dialog, log, app, db):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        session = db.session.get(RoleplaySession, sid)
        session.turn_count = svc.MAX_USER_TURNS - 1
        db.session.commit()
        log.calls.clear()
        data = client.post(f"/api/roleplay/{sid}/turn", json={"text": "さようなら。"}).get_json()
        assert log.kinds() == ["full"]
        assert data["done"] is True and data["correction"] == CORR_API


def db_turn_count(sid):
    return RoleplayTurn.query.filter_by(session_id=sid, speaker="user").count()


class TestStream:
    def test_stream_line_then_result(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        resp = client.post(f"/api/roleplay/{sid}/turn/stream", json={"text": "ケーキは ありますか。"})
        assert resp.status_code == 200
        assert resp.mimetype == "text/event-stream"
        assert resp.headers["Cache-Control"] == "no-cache"
        events = sse_events(resp)
        lines = [d["text"] for e, d in events if e == "line"]
        assert len(lines) > 1 and "".join(lines) == LINE
        kind, result = events[-1]
        assert kind == "result"
        assert result["bot_turn"]["jp"] == LINE and result["bot_turn"]["details_pending"] is True
        assert result["session"]["turn_count"] == 1
        assert log.calls[-1]["fast"] is True

    def test_stream_survives_session_teardown(self, auth_client, dialog, log, app, db):
        """Regression (live 2026-09-27): nach der View raeumt Flask-SQLAlchemy die Session ab —
        der Stream darf keine ORM-Objekte aus der View weiterverwenden."""
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        resp = client.post(f"/api/roleplay/{sid}/turn/stream", json={"text": "ケーキは ありますか。"})
        db.session.remove()          # wie der Teardown nach dem View-Return in Produktion
        events = sse_events(resp)
        assert events[-1][0] == "result", events[-1]
        assert events[-1][1]["session"]["turn_count"] == 1

    def test_stream_error_event_turn_not_booked(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        log.fail["line"] = svc.ProviderError("bridge_http_502", retryable=False)
        events = sse_events(client.post(f"/api/roleplay/{sid}/turn/stream", json={"text": "ケーキは ありますか。"}))
        assert events[-1][0] == "error" and events[-1][1]["error"] == "upstream_error"
        assert events[-1][1]["status"] == 502
        assert db_turn_count(sid) == 0

    def test_stream_prechecks_as_json(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        resp = client.post(f"/api/roleplay/{sid}/turn/stream", json={"text": "  "})
        assert resp.status_code == 400 and resp.get_json()["error"] == "invalid_request"

    def test_stream_prefetch_hit_without_line_events(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        client.post(f"/api/roleplay/{sid}/turn", json={"text": "ケーキは ありますか。"})
        run_jobs(app, log)                       # Details + Vorausberechnung der 3 Vorschlaege
        n = len(log.calls)
        events = sse_events(client.post(f"/api/roleplay/{sid}/turn/stream", json={"text": SUGG[0]["jp"]}))
        assert [e for e, _ in events] == ["result"]
        assert len(log.calls) == n               # kein neuer Modell-Aufruf
        assert events[0][1]["bot_turn"]["suggestions"] == SUGG_API


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


def _demo_start(client, app, log):
    token = client.post("/api/roleplay/demo/start", json={"website": ""}).get_json()["token"]
    log.jobs.clear()
    return token


class TestDemo:
    def test_demo_turn_line_first_then_details(self, client, demo_scene, log, app):
        token = _demo_start(client, app, log)
        data = client.post("/api/roleplay/demo/turn",
                           json={"token": token, "text": "ケーキも たべたいです。", "website": ""}).get_json()
        assert data["bot_turn"]["jp"] == LINE and data["bot_turn"]["details_pending"] is True
        assert data["bot_turn"]["suggestions"] == []
        new_token = data["token"]
        assert client.post("/api/roleplay/demo/details", json={"token": new_token}).get_json() == \
            {"status": "pending", "bot_turn": None}
        run_jobs(app, log, only_details=True)
        det = client.post("/api/roleplay/demo/details", json={"token": new_token}).get_json()
        assert det["status"] == "ready"
        assert det["bot_turn"]["suggestions"] == SUGG_API
        assert det["bot_turn"]["jp"] == LINE
        assert det["bot_turn"]["turn_index"] == data["bot_turn"]["turn_index"]
        # danach geplant: Vorausberechnung der drei Vorschlaege
        assert len([j for j in log.jobs if not j[2]]) == 3

    def test_demo_details_failure(self, client, demo_scene, log, app):
        token = _demo_start(client, app, log)
        log.fail["details"] = svc.ProviderError("bridge_http_502", retryable=False)
        data = client.post("/api/roleplay/demo/turn",
                           json={"token": token, "text": "ケーキも たべたいです。", "website": ""}).get_json()
        run_jobs(app, log)
        det = client.post("/api/roleplay/demo/details", json={"token": data["token"]}).get_json()
        assert det == {"status": "failed", "bot_turn": None}
        # Freitext geht weiter
        del log.fail["details"]
        resp = client.post("/api/roleplay/demo/turn",
                           json={"token": data["token"], "text": "おいしいですね。", "website": ""})
        assert resp.status_code == 200

    def test_demo_details_invalid_token(self, client, demo_scene, log):
        resp = client.post("/api/roleplay/demo/details", json={"token": "kaputt"})
        assert resp.status_code == 400 and resp.get_json()["error"] == "demo_invalid"

    def test_demo_stream(self, client, demo_scene, log, app):
        token = _demo_start(client, app, log)
        resp = client.post("/api/roleplay/demo/turn/stream",
                           json={"token": token, "text": "ケーキも たべたいです。", "website": ""})
        assert resp.mimetype == "text/event-stream"
        events = sse_events(resp)
        assert "".join(d["text"] for e, d in events if e == "line") == LINE
        assert events[-1][0] == "result" and events[-1][1]["token"]

    def test_demo_last_turn_full_call(self, client, demo_scene, log, app):
        token = _demo_start(client, app, log)
        for text in ("ケーキも たべたいです。", "おいしいですね。"):
            token = client.post("/api/roleplay/demo/turn",
                                json={"token": token, "text": text, "website": ""}).get_json()["token"]
        log.calls.clear()
        data = client.post("/api/roleplay/demo/turn",
                           json={"token": token, "text": "ありがとう。", "website": ""}).get_json()
        assert log.kinds() == ["full"] and data["done"] is True

    def test_demo_stream_honeypot_json_error(self, client, demo_scene, log, app):
        token = _demo_start(client, app, log)
        resp = client.post("/api/roleplay/demo/turn/stream",
                           json={"token": token, "text": "はい", "website": "spam"})
        assert resp.status_code == 400

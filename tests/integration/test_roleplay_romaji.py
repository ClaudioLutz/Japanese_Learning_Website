"""Rollenspiel: serverseitig abgeleitete Romaji in der API (eingeloggt + Gast-Demo)
und im Panel-Markup. Provider gemockt (Harness aus test_roleplay_split)."""
# ruff: noqa: F811  (importierte pytest-Fixtures werden als Parameter „neu definiert“)
from app.models import RoleplaySession
from app.services import roleplay_service as svc
from tests.integration.test_roleplay_split import (  # noqa: F401  (Fixtures)
    CORR, LINE, _demo_start, _start, demo_scene, dialog, log, run_jobs, sse_events,
)

LINE_ROMAJI = "Kēki mo arimasu yo."   # aus der Details-Lesung けーきも ありますよ。 (Katakana restauriert)


class TestEingeloggt:
    def test_details_liefern_romaji_fuer_zeile_und_vorschlaege(self, auth_client, dialog, log, app):
        client, _ = auth_client
        resp = client.post("/api/roleplay/start", json={"content_id": dialog.id, "role_user": "Gast"})
        bot = resp.get_json()["bot_turn"]
        assert bot["romaji"] == LINE_ROMAJI             # Zeile ist reine Kana → Romaji sofort
        run_jobs(app, log, only_details=True)
        sid = resp.get_json()["session"]["id"]
        det = client.get(f"/api/roleplay/{sid}/turn/{bot['turn_index']}/details").get_json()["bot_turn"]
        assert det["reading_kana"] == "ケーキも ありますよ。"
        assert det["romaji"] == LINE_ROMAJI
        assert [s["romaji"] for s in det["suggestions"]] == \
            ["Kōhī o kudasai.", "Ocha o kudasai.", "Mizu o kudasai."]

    def test_user_romaji_nur_bei_kana(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        data = client.post(f"/api/roleplay/{sid}/turn", json={"text": "こうちゃが のみたいです。"}).get_json()
        assert data["user_romaji"] == "Kōcha ga nomitai desu."
        data = client.post(f"/api/roleplay/{sid}/turn", json={"text": "水が 飲みたいです。"}).get_json()
        assert data["user_romaji"] == ""

    def test_stream_result_traegt_user_romaji(self, auth_client, dialog, log, app):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        events = sse_events(client.post(f"/api/roleplay/{sid}/turn/stream", json={"text": "はい、おねがいします。"}))
        result = dict(events)["result"]
        assert result["user_romaji"] == "Hai, onegaishimasu."
        assert "romaji" in result["bot_turn"]

    def test_letzter_zug_korrektur_mit_better_romaji(self, auth_client, dialog, log, app, db):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        session = db.session.get(RoleplaySession, sid)
        session.turn_count = svc.MAX_USER_TURNS - 1
        db.session.commit()
        data = client.post(f"/api/roleplay/{sid}/turn", json={"text": "コーヒー ください"}).get_json()
        assert data["done"] is True
        assert data["correction"][0]["better"] == CORR[0]["better"]
        assert data["correction"][0]["better_romaji"] == "Kōhī o kudasai."
        assert data["bot_turn"]["romaji"] == "Hai."      # volle Antwort des Mocks: reading_kana はい。

    def test_end_route_ergaenzt_better_romaji(self, auth_client, dialog, log, app, monkeypatch):
        client, _ = auth_client
        sid = _start(client, dialog, app, log)["session"]["id"]
        monkeypatch.setattr(svc, "end_session", lambda session: {
            "correction": CORR, "xp_awarded": 0, "farewell": None, "correction_unavailable": False})
        data = client.post(f"/api/roleplay/{sid}/end").get_json()
        assert data["correction"][0]["better_romaji"] == "Kōhī o kudasai."


class TestDemo:
    def test_demo_start_romaji(self, client, demo_scene, log, app):
        data = client.post("/api/roleplay/demo/start", json={"website": ""}).get_json()
        bot = data["bot_turn"]
        assert bot["romaji"] == "Risa-san, nani ga nomitai desu ka?"
        assert [s["romaji"] for s in bot["suggestions"]] == [
            "Kōcha ga nomitai desu.", "Watashi wa kōhī ga ii desu.", "Tsumetai mizu ga nomitai desu."]

    def test_demo_turn_und_details_romaji(self, client, demo_scene, log, app):
        token = _demo_start(client, app, log)
        data = client.post("/api/roleplay/demo/turn",
                           json={"token": token, "text": "ケーキも たべたいです。", "website": ""}).get_json()
        assert data["user_romaji"] == "Kēki mo tabetai desu."
        assert data["bot_turn"]["jp"] == LINE
        run_jobs(app, log, only_details=True)
        det = client.post("/api/roleplay/demo/details", json={"token": data["token"]}).get_json()["bot_turn"]
        assert det["romaji"] == LINE_ROMAJI
        assert det["suggestions"][0]["romaji"] == "Kōhī o kudasai."


class TestMarkup:
    def test_gast_hero_beispiel_hat_romaji_und_schalter(self, client, demo_scene, log, app):
        html = client.get("/").get_data(as_text=True)
        assert "Nani o tabetai desu ka." in html
        assert "Karē ga tabetai desu." in html
        assert "Kōhī o kudasai." in html
        assert "Romaji anzeigen" in html
        assert 'x-show="romajiShow && bot && bot.romaji"' in html


def test_romaji_felder_werden_nicht_gespeichert(auth_client, dialog, log, app, db):
    """Romaji entstehen erst bei der Ausgabe — gespeichert wird nur die Lesung."""
    from app.models import RoleplayTurn
    client, _ = auth_client
    sid = _start(client, dialog, app, log)["session"]["id"]
    turn = RoleplayTurn.query.filter_by(session_id=sid, speaker="bot").first()
    assert "romaji" not in (turn.suggestions_json or "")
    assert "reading_kana" in (turn.suggestions_json or "")
    assert svc.serialize_bot_turn(turn)["suggestions"][0]["romaji"] == "Kōhī o kudasai."

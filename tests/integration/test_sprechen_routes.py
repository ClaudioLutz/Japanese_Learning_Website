"""Integration-Tests fuer /sprechen, /sprechen/<id>, /sprechen/verlauf[/<id>]
und die Sprechen-Kachel/-Kennzahlen auf /mein-lernen.

Kein Modell-Aufruf: die Seiten sind reines SSR aus DB-Daten.
"""
import json
from datetime import datetime, timedelta

import pytest

from app import db
from app.models import LessonContent, RoleplaySession, RoleplayTurn, UserLessonProgress
from tests.factories import LessonCategoryFactory, LessonFactory, UserFactory

DIALOG = {"slides": [
    {"speaker": "Tanaka", "jp": "いらっしゃいませ。", "de": "Willkommen.", "image": "/uploads/x/line_01.webp"},
    {"speaker": "Lisa", "jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte."},
    {"speaker": "Tanaka", "jp": "はい、どうぞ。", "de": "Bitte schön."},
]}


@pytest.fixture
def enabled(app, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setitem(app.config, "CONTENT_LANGUAGES", ["german"])
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    return app


def _dialog_lesson(category, title, order):
    lesson = LessonFactory(title=title, category_id=category.id, order_index=order,
                           instruction_language="german", is_published=True)
    db.session.flush()
    content = LessonContent(lesson_id=lesson.id, content_type="dialog_slideshow", page_number=2,
                            order_index=0, title="Konversation (Slideshow)",
                            content_text=json.dumps(DIALOG, ensure_ascii=False))
    db.session.add(content)
    db.session.flush()
    return lesson, content


@pytest.fixture
def world(db):
    """Zwei Module (Reihenfolge per display_order vertauscht angelegt), drei Dialoge."""
    mod_b = LessonCategoryFactory(name="Modul Zwei", jlpt_level=5, display_order=2)
    mod_a = LessonCategoryFactory(name="Modul Eins", jlpt_level=5, display_order=1)
    db.session.flush()
    l1, c1 = _dialog_lesson(mod_a, "Im Café", 1)
    l2, c2 = _dialog_lesson(mod_a, "Am Bahnhof", 2)
    l3, c3 = _dialog_lesson(mod_b, "Beim Arzt", 1)
    # Nicht publiziert → nie sichtbar
    hidden = LessonFactory(title="Geheim", category_id=mod_a.id, is_published=False, instruction_language="german")
    db.session.flush()
    db.session.add(LessonContent(lesson_id=hidden.id, content_type="dialog_slideshow", page_number=1,
                                 content_text=json.dumps(DIALOG)))
    db.session.commit()
    return {"lessons": [l1, l2, l3], "contents": [c1, c2, c3]}


def _login(app, user=None):
    user = user or UserFactory()
    db.session.commit()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return client, user


def _complete(user, lesson, when=None):
    db.session.add(UserLessonProgress(user_id=user.id, lesson_id=lesson.id, is_completed=True,
                                      progress_percentage=100, completed_at=when or datetime.utcnow()))
    db.session.commit()


def _session(user, content, turns=4, corrections=None, status="completed", started=None, xp=25):
    s = RoleplaySession(user_id=user.id, lesson_content_id=content.id, role_user="Lisa", role_bot="Tanaka",
                        goal_de="Bestelle etwas.", status=status, turn_count=turns, xp_awarded=xp,
                        started_at=started or datetime.utcnow(),
                        correction_json=json.dumps(corrections or [], ensure_ascii=False))
    db.session.add(s)
    db.session.flush()
    idx = 0
    db.session.add(RoleplayTurn(session_id=s.id, turn_index=idx, speaker="bot", text_jp="いらっしゃいませ。",
                                reading_kana="いらっしゃいませ。", text_de="Willkommen."))
    for _ in range(turns):
        idx += 1
        db.session.add(RoleplayTurn(session_id=s.id, turn_index=idx, speaker="user", text_jp="コーヒー ください"))
        idx += 1
        db.session.add(RoleplayTurn(session_id=s.id, turn_index=idx, speaker="bot", text_jp="はい。",
                                    reading_kana="はい。", text_de="Ja."))
    db.session.commit()
    return s


PAGES = ["/sprechen", "/sprechen/verlauf", "/sprechen/verlauf/1"]


class TestGate:
    @pytest.mark.parametrize("url", PAGES)
    def test_flag_aus_404(self, auth_client, url):
        client, _ = auth_client
        assert client.get(url).status_code == 404

    def test_flag_aus_play_404(self, app, world):
        client, _ = _login(app)
        assert client.get(f"/sprechen/{world['contents'][0].id}").status_code == 404

    @pytest.mark.parametrize("url", PAGES)
    def test_ohne_login_redirect(self, client, enabled, url):
        resp = client.get(url)
        assert resp.status_code in (301, 302)
        assert "/login" in resp.headers["Location"]

    def test_nav_eintrag_nur_mit_flag(self, app, world):
        client, _ = _login(app)
        html = client.get("/lessons").get_data(as_text=True)
        assert 'href="/sprechen"' not in html

    def test_nav_eintrag_mit_flag(self, app, enabled, world):
        client, _ = _login(app)
        html = client.get("/lessons").get_data(as_text=True)
        # Desktop-Dropdown + Mobile-Bottom-Sheet
        assert html.count('href="/sprechen"') == 2


class TestIndex:
    def test_gruppierung_und_reihenfolge(self, app, enabled, world):
        client, _ = _login(app)
        html = client.get("/sprechen").get_data(as_text=True)
        assert html.index("Modul Eins") < html.index("Modul Zwei")
        assert html.index("Im Café") < html.index("Am Bahnhof") < html.index("Beim Arzt")
        assert "Geheim" not in html
        assert 'content="noindex,nofollow"' in html
        # Bild = erstes Slide-Bild, Figuren sichtbar
        assert "/uploads/x/line_01.webp" in html
        assert "Tanaka" in html and "Lisa" in html

    def test_bereit_und_nicht_gelernt(self, app, enabled, world):
        client, user = _login(app)
        _complete(user, world["lessons"][0])
        html = client.get("/sprechen").get_data(as_text=True)
        c1, c2 = world["contents"][0], world["contents"][1]
        assert f'data-content-id="{c1.id}" data-ready="1"' in html
        assert f'data-content-id="{c2.id}" data-ready="0"' in html
        assert "1 von 3 Szenen bereit" in html
        assert f'href="/lessons/{world["lessons"][1].id}">Erst die Lektion lernen' in html
        # beide spielbar
        assert f'href="/sprechen/{c1.id}"' in html and f'href="/sprechen/{c2.id}"' in html

    def test_nicht_in_sitemap(self, app, enabled, world):
        client, _ = _login(app)
        xml = client.get("/sitemap.xml").get_data(as_text=True)
        assert "/sprechen" not in xml


class TestPlay:
    def test_panel_standalone(self, app, enabled, world):
        client, _ = _login(app)
        c = world["contents"][0]
        resp = client.get(f"/sprechen/{c.id}")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert f'x-data="roleplayPanel({c.id})"' in html
        assert 'data-standalone="1"' in html
        assert "rp-open-btn" not in html  # kein Start-Knopf
        assert "js/roleplay_panel.js?v=" in html and "css/roleplay_panel.css?v=" in html
        assert "Originaldialog ansehen" in html
        assert "noch nicht abgeschlossen" in html

    def test_scene_api_liefert_geschlecht_und_lektionstitel(self, app, enabled, world):
        client, _ = _login(app)
        data = client.get(f"/api/roleplay/scene/{world['contents'][0].id}").get_json()
        assert [(r["name"], r["gender"]) for r in data["roles"]] == [("Tanaka", "m"), ("Lisa", "f")]
        # Generischer Inhaltstitel „Konversation (Slideshow)" → Lektionstitel
        assert data["title"] == "Im Café"

    def test_lektion_zeigt_panel_weiter_mit_knopf(self, app, enabled, world):
        client, _ = _login(app)
        html = client.get(f"/lessons/{world['lessons'][0].id}").get_data(as_text=True)
        assert 'data-standalone="0"' in html
        assert "rp-open-btn" in html

    def test_kein_dialog_404(self, app, enabled, world):
        client, _ = _login(app)
        text = LessonContent(lesson_id=world["lessons"][0].id, content_type="text", page_number=1)
        db.session.add(text)
        db.session.commit()
        assert client.get(f"/sprechen/{text.id}").status_code == 404
        assert client.get("/sprechen/999999").status_code == 404


class TestVerlauf:
    def test_liste_neueste_zuerst_ohne_leere(self, app, enabled, world):
        client, user = _login(app)
        c1, c3 = world["contents"][0], world["contents"][2]
        _session(user, c1, started=datetime.utcnow() - timedelta(days=1),
                 corrections=[{"original": "コーヒー ください", "better": "コーヒーを ください。", "explanation_de": "を fehlt."}])
        _session(user, c3, turns=2, status="abandoned", xp=0)
        _session(user, c1, turns=0, status="abandoned", xp=0)  # ohne Zug → nicht gelistet
        html = client.get("/sprechen/verlauf").get_data(as_text=True)
        assert html.index("Beim Arzt") < html.index("Im Café")
        assert html.count('class="sp-hist-card"') == 2
        assert "+25 XP" in html
        assert "1 Korrektur" in html
        assert "vorzeitig beendet" in html

    def test_detail_mit_korrekturen(self, app, enabled, world):
        client, user = _login(app)
        s = _session(user, world["contents"][0], corrections=[
            {"original": "コーヒー ください", "better": "コーヒーを ください。", "explanation_de": "Das Objekt bekommt を."},
            {"original": "はい。", "better": "はい。", "explanation_de": "Gut gemacht!"},
        ])
        html = client.get(f"/sprechen/verlauf/{s.id}").get_data(as_text=True)
        assert "Das Objekt bekommt を." in html
        assert "Gut gemacht!" in html
        assert "1 Korrektur" in html  # Lob zaehlt nicht
        assert "Lesung und Deutsch" in html
        assert "Willkommen." in html
        assert html.count("sp-line is-user") == 4

    def test_detail_korrektur_fallback_raw_json(self, app, enabled, world):
        client, user = _login(app)
        s = _session(user, world["contents"][0])
        s.correction_json = None
        last = [t for t in s.turns if t.speaker == "bot"][-1]
        last.raw_json = json.dumps({"correction": [{"original": "a", "better": "b", "explanation_de": "Aus raw_json."}]})
        db.session.commit()
        html = client.get(f"/sprechen/verlauf/{s.id}").get_data(as_text=True)
        assert "Aus raw_json." in html

    def test_fremde_session_404(self, app, enabled, world):
        other = UserFactory()
        db.session.commit()
        s = _session(other, world["contents"][0])
        client, _ = _login(app)
        assert client.get(f"/sprechen/verlauf/{s.id}").status_code == 404
        assert "Im Café" not in client.get("/sprechen/verlauf").get_data(as_text=True)


class TestDashboard:
    def test_kachel_und_kennzahlen(self, app, enabled, world):
        client, user = _login(app)
        _complete(user, world["lessons"][1])
        _session(user, world["contents"][2], turns=4,
                 corrections=[{"original": "x", "better": "y", "explanation_de": "e"}] * 2)
        html = client.get("/mein-lernen").get_data(as_text=True)
        assert "Heute sprechen" in html
        assert f'href="/sprechen/{world["contents"][1].id}"' in html  # frisch gelernt, nie gespielt
        assert "Frisch gelernt" in html
        assert "Sprechen · Rollenspiel" in html
        assert "Korrekturen pro Gespräch" in html
        assert "2.0" in html

    def test_ohne_bereite_szene_hinweis(self, app, enabled, world):
        client, _ = _login(app)
        html = client.get("/mein-lernen").get_data(as_text=True)
        assert "Heute sprechen" in html
        assert f'href="/lessons/{world["lessons"][0].id}"' in html

    def test_flag_aus_keine_kachel(self, app, world):
        client, _ = _login(app)
        html = client.get("/mein-lernen").get_data(as_text=True)
        assert "Heute sprechen" not in html
        assert "Sprechen · Rollenspiel" not in html

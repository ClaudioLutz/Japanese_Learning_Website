"""Tests fuer die Test-/Pruefungsseite (/pruefen).

Deckt den Service (evaluate_answer, build_question_pool, serialize_question) und
die Endpoints (pool/check/grade, Auth-Gating) ab. Rein additiv — keine Aenderung
am bestehenden Lektions-Quiz.
"""
from app import db
from app.models import UserQuizAnswer, Lesson
from app.services import pruefen_service as svc
from tests.factories import (
    UserFactory, LessonCategoryFactory, LessonFactory, LessonContentFactory,
    QuizQuestionFactory, QuizOptionFactory,
)


def _question(lesson, qtype="multiple_choice", n=3, correct_idx=0):
    """Hilfsfunktion: Quiz-Frage mit Optionen an einer Lektion erzeugen."""
    content = LessonContentFactory(lesson_id=lesson.id, content_type="quiz",
                                   is_interactive=True)
    q = QuizQuestionFactory(lesson_content_id=content.id, question_type=qtype)
    opts = []
    if qtype in ("multiple_choice", "true_false"):
        for i in range(n):
            opts.append(QuizOptionFactory(question_id=q.id, option_text=f"opt{i}",
                                          is_correct=(i == correct_idx)))
    db.session.flush()
    return q, opts


def _matching(lesson, mapping):
    content = LessonContentFactory(lesson_id=lesson.id, content_type="quiz",
                                   is_interactive=True)
    q = QuizQuestionFactory(lesson_content_id=content.id, question_type="matching")
    for prompt, answer in mapping.items():
        QuizOptionFactory(question_id=q.id, option_text=prompt, feedback=answer)
    db.session.flush()
    return q


# ── evaluate_answer ─────────────────────────────────────────

def test_evaluate_multiple_choice(app_context):
    lesson = LessonFactory()
    q, opts = _question(lesson)
    good = svc.evaluate_answer(q, {"selected_option_id": opts[0].id})
    assert good["is_correct"] and good["correct"] == 1 and good["total"] == 1
    assert good["correct_option_id"] == opts[0].id
    bad = svc.evaluate_answer(q, {"selected_option_id": opts[1].id})
    assert not bad["is_correct"] and bad["correct"] == 0


def test_evaluate_matching_full_and_partial(app_context):
    lesson = LessonFactory()
    q = _matching(lesson, {"水": "みず", "火": "ひ"})
    full = svc.evaluate_answer(q, {"pairs": [
        {"prompt": "水", "answer": "みず"}, {"prompt": "火", "answer": "ひ"}]})
    assert full["is_correct"] and full["correct"] == 2 and full["total"] == 2

    partial = svc.evaluate_answer(q, {"pairs": [
        {"prompt": "水", "answer": "みず"}, {"prompt": "火", "answer": "みず"}]})
    assert not partial["is_correct"] and partial["correct"] == 1 and partial["total"] == 2


# ── build_question_pool ─────────────────────────────────────

def test_pool_excludes_fill_blank(app_context):
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    good, _ = _question(lesson)
    content = LessonContentFactory(lesson_id=lesson.id)
    fb = QuizQuestionFactory(lesson_content_id=content.id, question_type="fill_blank")
    db.session.flush()
    ids = [q.id for q in svc.build_question_pool(user, scope={"kind": "all"})]
    assert good.id in ids
    assert fb.id not in ids


def test_pool_excludes_unpublished(app_context):
    user = UserFactory()
    lesson = LessonFactory(is_published=False, allow_guest_access=True)
    q, _ = _question(lesson)
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"})]
    assert q.id not in ids


def test_pool_respects_access(app_context, monkeypatch):
    user = UserFactory()
    lesson = LessonFactory(is_published=True)
    q, _ = _question(lesson)
    # Der Pool batcht den Zugriff jetzt ueber access_check(access_ctx=...) statt
    # is_accessible_to_user (N+1-Vermeidung) -> hier access_check stubben.
    denied = type("Denied", (), {"accessible": False, "message": "nope", "reason": None})()
    monkeypatch.setattr(Lesson, "access_check",
                        lambda self, u, access_ctx=None: denied)
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"})]
    assert q.id not in ids


def test_pool_wrong_filter(app_context):
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q_wrong, _ = _question(lesson)
    q_ok, _ = _question(lesson)
    db.session.add(UserQuizAnswer(user_id=user.id, question_id=q_wrong.id,
                                  is_correct=False, attempts=1))
    db.session.flush()
    ids = [q.id for q in svc.build_question_pool(user, scope={"kind": "all"},
                                                 selection="wrong")]
    assert q_wrong.id in ids
    assert q_ok.id not in ids


def test_pool_level_scope(app_context):
    user = UserFactory()
    cat = LessonCategoryFactory(jlpt_level=5)
    lesson = LessonFactory(category_id=cat.id, price=0.0, allow_guest_access=True)
    q, _ = _question(lesson)
    db.session.flush()
    ids = [x.id for x in svc.build_question_pool(
        user, scope={"kind": "level", "id": 5})]
    assert q.id in ids


def test_serialize_no_leak(app_context):
    lesson = LessonFactory()
    q, _ = _question(lesson)
    data = svc.serialize_question(q, mode="pruefung")
    assert "options" in data and data["options"]
    for o in data["options"]:
        assert "is_correct" not in o
    assert "hint" not in data  # Pruefungsmodus blendet Hint aus


def test_serialize_matching_no_mapping(app_context):
    lesson = LessonFactory()
    q = _matching(lesson, {"水": "みず", "火": "ひ"})
    data = svc.serialize_question(q, mode="uebung")
    assert set(data["matching"].keys()) == {"prompts", "answers"}
    assert sorted(data["matching"]["prompts"]) == ["水", "火"]
    assert sorted(data["matching"]["answers"]) == ["ひ", "みず"]


# ── Endpoints ───────────────────────────────────────────────

def test_start_open_to_guest(client):
    assert client.get("/pruefen").status_code == 200


def test_session_redirects_guest(client):
    r = client.get("/pruefen/test")
    assert r.status_code in (301, 302)


def test_pool_requires_login(client):
    r = client.get("/api/pruefen/pool")
    assert r.status_code in (301, 302, 401)


def test_check_endpoint(auth_client):
    client, user = auth_client
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q, opts = _question(lesson)
    db.session.commit()
    r = client.post("/api/pruefen/check",
                    json={"question_id": q.id, "selected_option_id": opts[0].id})
    assert r.status_code == 200
    data = r.get_json()
    assert data["is_correct"] is True
    assert data["correct_option_id"] == opts[0].id
    assert "explanation" in data


def test_grade_endpoint(auth_client):
    client, user = auth_client
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q, opts = _question(lesson)
    db.session.commit()
    r = client.post("/api/pruefen/grade",
                    json={"answers": [{"question_id": q.id,
                                       "selected_option_id": opts[0].id}]})
    assert r.status_code == 200
    d = r.get_json()
    assert d["graded"] == 1 and d["correct"] == 1
    assert d["score_pct"] == 100 and d["passed"] is True


def test_overview_endpoint(auth_client):
    client, user = auth_client
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    _question(lesson)
    db.session.commit()
    r = client.get("/api/pruefen/overview")
    assert r.status_code == 200
    d = r.get_json()
    assert d["total"] >= 1
    assert "wrong_count" in d and "modules" in d and "lessons" in d


# ── Pool-Guards (degenerierte Daten ausschliessen) ──────────

def test_pool_excludes_mc_multiple_correct(app_context):
    """M3: MC mit mehr als einer korrekten Option ist mehrdeutig -> raus."""
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q, opts = _question(lesson, n=3, correct_idx=0)
    opts[1].is_correct = True  # zweite korrekte Option
    db.session.flush()
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"})]
    assert q.id not in ids


def test_pool_excludes_mc_no_correct(app_context):
    """N1: MC ohne markierte korrekte Option ist nie loesbar -> raus."""
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q, _ = _question(lesson, n=3, correct_idx=99)  # keine Option korrekt
    db.session.flush()
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"})]
    assert q.id not in ids


def test_pool_excludes_matching_without_mapping(app_context):
    """M2: matching mit leerem/NULL feedback ist serverseitig unloesbar -> raus."""
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    content = LessonContentFactory(lesson_id=lesson.id, content_type="quiz",
                                   is_interactive=True)
    q = QuizQuestionFactory(lesson_content_id=content.id, question_type="matching")
    QuizOptionFactory(question_id=q.id, option_text="水", feedback=None)
    QuizOptionFactory(question_id=q.id, option_text="火", feedback="ひ")
    db.session.flush()
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"})]
    assert q.id not in ids


def test_pool_excludes_matching_duplicate_prompt(app_context):
    """M1-Guard: doppelte Prompt-Texte machen das Text-Mapping mehrdeutig -> raus."""
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    content = LessonContentFactory(lesson_id=lesson.id, content_type="quiz",
                                   is_interactive=True)
    q = QuizQuestionFactory(lesson_content_id=content.id, question_type="matching")
    QuizOptionFactory(question_id=q.id, option_text="水", feedback="みず")
    QuizOptionFactory(question_id=q.id, option_text="水", feedback="ひ")  # Dublette
    db.session.flush()
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"})]
    assert q.id not in ids


def test_pool_wrong_filter_attempts_proxy(app_context):
    """attempts>1-Ast des Falsch-Proxys: auch eine 'richtig' beantwortete Frage
    mit Mehrfachversuch zaehlt als falsch (or_(is_correct=False, attempts>1))."""
    user = UserFactory()
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q, _ = _question(lesson)
    db.session.add(UserQuizAnswer(user_id=user.id, question_id=q.id,
                                  is_correct=True, attempts=2))
    db.session.flush()
    ids = [x.id for x in svc.build_question_pool(user, scope={"kind": "all"},
                                                 selection="wrong")]
    assert q.id in ids


def test_evaluate_matching_total_is_option_count(app_context):
    """M1: total = Anzahl Optionen, nicht der (kollabierenden) Dict-Keys."""
    lesson = LessonFactory()
    content = LessonContentFactory(lesson_id=lesson.id, content_type="quiz",
                                   is_interactive=True)
    q = QuizQuestionFactory(lesson_content_id=content.id, question_type="matching")
    QuizOptionFactory(question_id=q.id, option_text="水", feedback="みず")
    QuizOptionFactory(question_id=q.id, option_text="水", feedback="ひ")
    db.session.flush()
    res = svc.evaluate_answer(q, {"pairs": [{"prompt": "水", "answer": "みず"}]})
    assert res["total"] == 2  # zwei Slots, nicht ein kollabierter Key
    assert not res["is_correct"]


# ── Endpoint-Sicherheit + Edge Cases ────────────────────────

def test_check_unpublished_question_404(auth_client):
    """S1: check auf eine Frage einer unveroeffentlichten Lektion -> 404 (kein Leak)."""
    client, user = auth_client
    lesson = LessonFactory(is_published=False, price=0.0, allow_guest_access=True)
    q, opts = _question(lesson)
    db.session.commit()
    r = client.post("/api/pruefen/check",
                    json={"question_id": q.id, "selected_option_id": opts[0].id})
    assert r.status_code == 404


def test_grade_excludes_unpublished(auth_client):
    """S1: grade ueberspringt unveroeffentlichte Fragen (nicht mitgewertet)."""
    client, user = auth_client
    lesson = LessonFactory(is_published=False, price=0.0, allow_guest_access=True)
    q, opts = _question(lesson)
    db.session.commit()
    r = client.post("/api/pruefen/grade",
                    json={"answers": [{"question_id": q.id,
                                       "selected_option_id": opts[0].id}]})
    assert r.status_code == 200
    assert r.get_json()["graded"] == 0


def test_grade_empty_answers(auth_client):
    """Leerer Antwortsatz -> 200, score 0, kein 500 (Division-Guard, possible=0)."""
    client, user = auth_client
    r = client.post("/api/pruefen/grade", json={"answers": []})
    assert r.status_code == 200
    d = r.get_json()
    assert d["graded"] == 0 and d["score_pct"] == 0 and d["passed"] is False


def test_grade_partial_matching_score(auth_client):
    """1 von 2 Zuordnungen richtig -> Teilkredit fliesst in score_pct (50%) und
    die Aufschluesselung fuehrt earned (N2: Balken == Headline-Basis)."""
    client, user = auth_client
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    q = _matching(lesson, {"水": "みず", "火": "ひ"})
    db.session.commit()
    r = client.post("/api/pruefen/grade", json={"answers": [
        {"question_id": q.id, "pairs": [
            {"prompt": "水", "answer": "みず"},
            {"prompt": "火", "answer": "みず"}]}]})
    assert r.status_code == 200
    d = r.get_json()
    assert d["score_pct"] == 50
    assert d["by_type"]["matching"]["earned"] == 0.5
    assert d["by_type"]["matching"]["total"] == 1


def test_pool_invalid_scope_id_400(auth_client):
    """N3: lesson/module-Scope ohne gueltige id -> 400 statt stiller Leer-Pool."""
    client, user = auth_client
    assert client.get("/api/pruefen/pool?scope=lesson").status_code == 400
    assert client.get("/api/pruefen/pool?scope=module&id=abc").status_code == 400


def test_pool_renders_markdown(auth_client):
    """Mi1: question_text wird als Markdown gerendert (wie der Lektions-Quiz),
    sonst erschienen **fett** etc. roh."""
    client, user = auth_client
    lesson = LessonFactory(price=0.0, allow_guest_access=True)
    content = LessonContentFactory(lesson_id=lesson.id, content_type="quiz",
                                   is_interactive=True)
    q = QuizQuestionFactory(lesson_content_id=content.id, question_type="true_false",
                            question_text="Die **G-Reihe** ist nasaliert")
    QuizOptionFactory(question_id=q.id, option_text="Wahr", is_correct=True)
    QuizOptionFactory(question_id=q.id, option_text="Falsch", is_correct=False)
    db.session.commit()
    r = client.get("/api/pruefen/pool")
    assert r.status_code == 200
    texts = [x["question_text"] for x in r.get_json()["questions"]]
    assert any("<strong>G-Reihe</strong>" in t for t in texts)

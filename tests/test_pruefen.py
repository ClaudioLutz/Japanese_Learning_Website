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
    monkeypatch.setattr(Lesson, "is_accessible_to_user", lambda self, u: (False, "nope"))
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

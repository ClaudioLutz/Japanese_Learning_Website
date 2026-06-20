"""Service-Layer fuer die Test-/Pruefungsseite (/pruefen).

Rein additiv und READ-ONLY: liest aus QuizQuestion/QuizOption/UserQuizAnswer und
nutzt Lesson.is_accessible_to_user fuer die Zugriffskontrolle. Schreibt NICHTS —
der Test ist risikofrei und beruehrt UserQuizAnswer/UserLessonProgress/SRS nicht.

Konzept: docs/konzept-test-seite/ (00 Modi, 03 Implementierungsplan).
"""
from __future__ import annotations

import random

from sqlalchemy import or_

from app import db
from app.models import (
    QuizQuestion,
    UserQuizAnswer,
    LessonContent,
    Lesson,
    LessonCategory,
)

# fill_blank ist Legacy/verboten und wird ueberall hart ausgeschlossen.
ALLOWED_TYPES = ("multiple_choice", "true_false", "matching")
N5_LEVEL = 5
PASS_THRESHOLD = 0.6  # 60 % — bewusst ueber der echten JLPT-N5-Schwelle (~44 %)


def _accessible_lesson_ids(user, lesson_ids):
    """Map lesson_id -> bool (zugaenglich fuer user). Einmal pro Pool-Build, batch
    geladen, um N+1 ueber is_accessible_to_user zu vermeiden."""
    result = {}
    ids = [i for i in lesson_ids if i is not None]
    if not ids:
        return result
    for lesson in Lesson.query.filter(Lesson.id.in_(ids)).all():
        try:
            accessible, _ = lesson.is_accessible_to_user(user)
        except Exception:
            accessible = False
        result[lesson.id] = bool(accessible)
    return result


def build_question_pool(user, scope=None, selection="all", q_types=None,
                        limit=None, shuffle=True):
    """Liefert eine Liste QuizQuestion gemaess Scope + Filter, access-gefiltert.

    scope:     {"kind": "lesson"|"module"|"level"|"all", "id": int|None}
    selection: "all" | "wrong" | "unseen"
    q_types:   Teilmenge von ALLOWED_TYPES (None = alle erlaubten)
    limit:     max. Anzahl Fragen (None = alle)
    """
    scope = scope or {"kind": "all"}
    types = [t for t in (q_types or ALLOWED_TYPES) if t in ALLOWED_TYPES]
    if not types:
        types = list(ALLOWED_TYPES)

    q = (
        db.session.query(QuizQuestion)
        .join(LessonContent, LessonContent.id == QuizQuestion.lesson_content_id)
        .join(Lesson, Lesson.id == LessonContent.lesson_id)
        .filter(QuizQuestion.question_type.in_(types))
        .filter(Lesson.is_published.is_(True))
    )

    kind = scope.get("kind", "all")
    if kind == "lesson":
        q = q.filter(Lesson.id == scope.get("id"))
    elif kind == "module":
        q = q.filter(Lesson.category_id == scope.get("id"))
    elif kind == "level":
        # JLPT-Level liegt auf LessonCategory, nicht auf Lesson.
        q = q.join(LessonCategory, LessonCategory.id == Lesson.category_id).filter(
            LessonCategory.jlpt_level == (scope.get("id") or N5_LEVEL)
        )

    if selection == "wrong":
        q = (
            q.join(UserQuizAnswer, UserQuizAnswer.question_id == QuizQuestion.id)
            .filter(UserQuizAnswer.user_id == user.id)
            .filter(or_(UserQuizAnswer.is_correct.is_(False), UserQuizAnswer.attempts > 1))
        )
    elif selection == "unseen":
        answered = db.session.query(UserQuizAnswer.question_id).filter(
            UserQuizAnswer.user_id == user.id
        )
        q = q.filter(~QuizQuestion.id.in_(answered))

    questions = q.all()

    # Zugriffskontrolle (is_accessible_to_user ist eine Python-Methode, kein SQL-Feld).
    access = _accessible_lesson_ids(
        user, {qq.content.lesson_id for qq in questions if qq.content}
    )
    questions = [
        qq for qq in questions if qq.content and access.get(qq.content.lesson_id)
    ]

    if shuffle:
        random.shuffle(questions)
    else:
        questions.sort(key=lambda x: (x.content.lesson_id, x.order_index or 0))

    if limit:
        try:
            questions = questions[: int(limit)]
        except (TypeError, ValueError):
            pass
    return questions


def serialize_question(question, mode="uebung"):
    """JSON-sichere Repraesentation einer Frage OHNE Korrekt-Flags (kein Leak).
    Bei matching werden prompts + (gemischte) answers geliefert, ohne das Mapping."""
    content = question.content
    lesson = content.lesson if content else None
    data = {
        "id": question.id,
        "type": question.question_type,
        "question_text": question.question_text or "",
        "difficulty": question.difficulty_level or 1,
        "points": question.points or 1,
        "lesson": {
            "id": content.lesson_id if content else None,
            "title": lesson.title if lesson else "",
        },
    }
    if mode == "uebung" and question.hint:
        data["hint"] = question.hint

    options = sorted(question.options, key=lambda o: o.order_index or 0)
    if question.question_type in ("multiple_choice", "true_false"):
        data["options"] = [{"id": o.id, "text": o.option_text} for o in options]
    elif question.question_type == "matching":
        prompts = [o.option_text for o in options]
        answers = [o.feedback for o in options]
        shuffled = answers[:]
        random.shuffle(shuffled)
        data["matching"] = {"prompts": prompts, "answers": shuffled}
    return data


def evaluate_answer(question, payload):
    """Reine Bewertung einer Antwort. KEINE DB-Writes.

    payload (MC/true_false): {"selected_option_id": int}
    payload (matching):      {"pairs": [{"prompt": str, "answer": str}, ...]}

    Returns dict: is_correct, correct (n richtige Teile), total (n Teile),
    correct_option_id (MC/tf), correct_pairs ({prompt: answer} bei matching).
    """
    qtype = question.question_type
    if qtype in ("multiple_choice", "true_false"):
        selected = payload.get("selected_option_id")
        correct_opt = next((o for o in question.options if o.is_correct), None)
        is_correct = bool(
            selected is not None
            and correct_opt is not None
            and int(selected) == correct_opt.id
        )
        return {
            "is_correct": is_correct,
            "correct": 1 if is_correct else 0,
            "total": 1,
            "correct_option_id": correct_opt.id if correct_opt else None,
            "correct_pairs": None,
        }

    if qtype == "matching":
        # option_text = Prompt, feedback = korrekte Zuordnung (wie routes.py:4159).
        correct_map = {o.option_text: o.feedback for o in question.options}
        total = len(correct_map)
        correct = 0
        for pair in payload.get("pairs") or []:
            prompt = pair.get("prompt")
            answer = pair.get("answer")
            expected = correct_map.get(prompt)
            if expected is not None and answer == expected:
                correct += 1
        return {
            "is_correct": total > 0 and correct == total,
            "correct": correct,
            "total": total,
            "correct_option_id": None,
            "correct_pairs": correct_map,
        }

    return {
        "is_correct": False,
        "correct": 0,
        "total": 0,
        "correct_option_id": None,
        "correct_pairs": None,
    }


def overview(user):
    """Daten fuer den Start-Screen: zugaengliche Module + Lektionen mit Fragenzahl,
    Gesamt-Zahl und Falsch-Zahl (Proxy)."""
    pool = build_question_pool(user, scope={"kind": "all"}, shuffle=False)
    wrong = build_question_pool(user, scope={"kind": "all"}, selection="wrong",
                                shuffle=False)

    lessons = {}
    modules = {}
    for q in pool:
        content = q.content
        lesson = content.lesson if content else None
        if not lesson:
            continue
        lrow = lessons.setdefault(
            lesson.id,
            {"id": lesson.id, "title": lesson.title,
             "category_id": lesson.category_id, "count": 0},
        )
        lrow["count"] += 1
        if lesson.category_id:
            cat = lesson.category
            mrow = modules.setdefault(
                lesson.category_id,
                {"id": lesson.category_id,
                 "name": cat.name if cat else f"Modul {lesson.category_id}",
                 "count": 0},
            )
            mrow["count"] += 1

    return {
        "total": len(pool),
        "wrong_count": len(wrong),
        "modules": sorted(modules.values(), key=lambda m: m["name"]),
        "lessons": sorted(lessons.values(), key=lambda x: x["title"]),
    }

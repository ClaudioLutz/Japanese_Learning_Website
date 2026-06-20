"""Routen fuer die Test-/Pruefungsseite (/pruefen).

Start-Screen + gesperrte Session-Buehne + JSON-APIs (pool/check/grade/overview).
Der Server bewertet (Pool ohne Korrekt-Flags) — kein Antwort-Leak. Schreibt NICHTS
in den Lernstand (Test ist risikofrei). Konzept: docs/konzept-test-seite/.
"""
from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for,
    current_app,
)
from flask_login import login_required, current_user

from app.models import QuizQuestion
from app.services import pruefen_service as svc

pruefen_bp = Blueprint("pruefen", __name__)


def _md(text, inline=False):
    """Markdown -> HTML ueber die App-Filter (markdown_safe/-inline, bleach-sanitisiert,
    XSS-sicher). Direkter Filter-Call statt render_template_string — kein Template-
    Compile pro Item (wichtig beim Vollpruefungs-Pool mit ~900 Fragen)."""
    if not text:
        return ""
    name = "markdown_inline" if inline else "markdown_safe"
    return current_app.jinja_env.filters[name](text)


def _scope_from_args():
    kind = request.args.get("scope", "all")
    scope = {"kind": kind}
    if kind in ("lesson", "module", "level"):
        try:
            scope["id"] = int(request.args.get("id"))
        except (TypeError, ValueError):
            scope["id"] = None
    return scope


# ── Seiten ────────────────────────────────────────────────────────────────

@pruefen_bp.route("/pruefen")
def pruefen_start():
    """Start-Screen. Gaeste sehen einen Teaser (im Template via current_user)."""
    return render_template("pruefen.html")


@pruefen_bp.route("/pruefen/test")
def pruefen_session():
    """Gesperrte Session-Buehne. Gaeste werden zum Login geleitet (Pool braucht Login)."""
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login", next=request.full_path))
    return render_template("pruefen_session.html")


# ── APIs ──────────────────────────────────────────────────────────────────

@pruefen_bp.route("/api/pruefen/overview")
@login_required
def api_overview():
    return jsonify(svc.overview(current_user))


@pruefen_bp.route("/api/pruefen/pool")
@login_required
def api_pool():
    scope = _scope_from_args()
    # lesson/module brauchen eine gueltige id; fehlt/ungueltig -> 400 statt still
    # einen leeren Pool zu liefern (sonst sieht der Nutzer faelschlich "keine Fragen").
    if scope["kind"] in ("lesson", "module") and scope.get("id") is None:
        return jsonify({"error": "invalid scope id"}), 400

    mode = request.args.get("mode", "uebung")
    selection = request.args.get("selection", "all")
    q_types = request.args.getlist("type") or None
    try:
        limit = int(request.args.get("limit"))
    except (TypeError, ValueError):
        limit = None

    questions = svc.build_question_pool(
        current_user,
        scope=scope,
        selection=selection,
        q_types=q_types,
        limit=limit,
    )
    payload = [svc.serialize_question(q, mode=mode) for q in questions]
    # question_text als Markdown rendern (wie der Lektions-Quiz, markdown_inline) —
    # sonst erscheinen **fett** etc. roh. Client bindet es per x-html.
    for qd in payload:
        qd["question_text"] = _md(qd.get("question_text"), inline=True)
    return jsonify({
        "count": len(payload),
        "mode": mode,
        "questions": payload,
    })


def _load_accessible_question(question_id):
    """Frage laden + Zugriff pruefen. Returns (question, error_response|None)."""
    if not question_id:
        return None, (jsonify({"error": "question_id required"}), 400)
    try:
        question = QuizQuestion.query.get(int(question_id))
    except (TypeError, ValueError):
        return None, (jsonify({"error": "invalid question_id"}), 400)
    if not question or not question.content or not question.content.lesson:
        return None, (jsonify({"error": "unknown question"}), 404)
    lesson = question.content.lesson
    # Der Pool liefert nur veroeffentlichte Lektionen — check/grade muessen das
    # spiegeln, sonst liesse sich per beliebiger question_id die Loesung einer
    # unveroeffentlichten (Draft-)Frage abgreifen. Draft = wie nicht existent.
    if not lesson.is_published:
        return None, (jsonify({"error": "unknown question"}), 404)
    accessible, _ = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return None, (jsonify({"error": "forbidden"}), 403)
    return question, None


@pruefen_bp.route("/api/pruefen/check", methods=["POST"])
@login_required
def api_check():
    """Uebungsmodus: eine Antwort sofort bewerten + Erklaerung liefern."""
    data = request.get_json(silent=True) or {}
    question, err = _load_accessible_question(data.get("question_id"))
    if err:
        return err

    res = svc.evaluate_answer(question, data)
    out = {
        "is_correct": res["is_correct"],
        "correct": res["correct"],
        "total": res["total"],
        "correct_option_id": res["correct_option_id"],
        "correct_pairs": res["correct_pairs"],
        "explanation": _md(question.explanation),
    }
    selected = data.get("selected_option_id")
    if selected:
        try:
            opt = next((o for o in question.options if o.id == int(selected)), None)
        except (TypeError, ValueError):
            opt = None
        if opt and opt.feedback:
            out["option_feedback"] = _md(opt.feedback, inline=True)
    return jsonify(out)


@pruefen_bp.route("/api/pruefen/grade", methods=["POST"])
@login_required
def api_grade():
    """Pruefungsmodus: ganzen Satz Antworten bewerten -> Score + Aufschluesselung."""
    data = request.get_json(silent=True) or {}
    answers = data.get("answers") or []

    qids = []
    for a in answers:
        try:
            qids.append(int(a.get("question_id")))
        except (TypeError, ValueError):
            continue
    qmap = {q.id: q for q in QuizQuestion.query.filter(QuizQuestion.id.in_(qids)).all()}

    earned = 0.0
    possible = 0.0
    correct_n = 0
    graded = 0
    by_type = {}
    by_lesson = {}
    details = []

    for a in answers:
        try:
            q = qmap.get(int(a.get("question_id")))
        except (TypeError, ValueError):
            q = None
        if (not q or not q.content or not q.content.lesson
                or not q.content.lesson.is_published):
            continue
        accessible, _ = q.content.lesson.is_accessible_to_user(current_user)
        if not accessible:
            continue

        res = svc.evaluate_answer(q, a)
        pts = q.points or 1
        frac = (res["correct"] / res["total"]) if res["total"] else 0.0
        earned += pts * frac
        possible += pts
        graded += 1
        if res["is_correct"]:
            correct_n += 1

        # 'correct'/'total' = ganze Fragen (Mastery-Zaehler), 'earned' = Teilkredit
        # (Summe der Bruchteile). Der Fortschrittsbalken nutzt earned/total und
        # liegt damit auf derselben Basis wie score_pct (kein Headline-Widerspruch).
        bt = by_type.setdefault(q.question_type, {"correct": 0, "total": 0, "earned": 0.0})
        bt["total"] += 1
        bt["correct"] += 1 if res["is_correct"] else 0
        bt["earned"] += frac

        lid = q.content.lesson_id
        bl = by_lesson.setdefault(
            lid, {"title": q.content.lesson.title, "correct": 0, "total": 0, "earned": 0.0}
        )
        bl["total"] += 1
        bl["correct"] += 1 if res["is_correct"] else 0
        bl["earned"] += frac

        details.append({
            "question_id": q.id,
            "question_text": _md(q.question_text, inline=True),
            "is_correct": res["is_correct"],
            "correct": res["correct"],
            "total": res["total"],
            "correct_option_id": res["correct_option_id"],
            "correct_pairs": res["correct_pairs"],
            "explanation": _md(q.explanation),
        })

    pct = round(100 * earned / possible) if possible else 0
    threshold = int(svc.PASS_THRESHOLD * 100)
    return jsonify({
        "graded": graded,
        "correct": correct_n,
        "score_pct": pct,
        "passed": pct >= threshold,
        "pass_threshold": threshold,
        "by_type": by_type,
        "by_lesson": by_lesson,
        "details": details,
    })

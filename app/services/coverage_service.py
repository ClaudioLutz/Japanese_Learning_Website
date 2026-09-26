"""JLPT-Coverage-Service.

Liefert Live-Zahlen aus DB vs. canonical JLPT-Listen — fuer die Verkaufsseite
/n5-bundle und das Bundle-Pricing. Quelle der Logik: pipeline.py:499-590
(generate-lesson Skill). Hier gekapselt fuer Web-Routes.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from app import db
from app.models import (
    Kanji,
    Lesson,
    LessonCategory,
    LessonContent,
    QuizQuestion,
    Vocabulary,
)


# Canonical JSON liegt im generate-lesson Skill (MIT-lizenziert von elzup, von Tanos abgeleitet)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = PROJECT_ROOT / ".claude" / "skills" / "generate-lesson" / "sources"

_CANONICAL_CACHE: dict[int, dict] = {}
_VARIANT_SPLIT_RE = re.compile(r"[;；/・]")


def _load_canonical(level: int) -> dict:
    """Laedt JLPT-Level canonical Liste. Cached pro Level."""
    if level in _CANONICAL_CACHE:
        return _CANONICAL_CACHE[level]
    path = CANONICAL_DIR / f"jlpt_n{level}_canonical.json"
    if not path.exists():
        raise FileNotFoundError(f"Canonical JLPT-N{level}-Liste fehlt: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    # Wie pipeline.py (generate-lesson): Eintraege mit Schreibvarianten in EINEM
    # word-Feld ("足; 脚", "いい; よい") in Einzelwoerter zerlegen.
    vocab_set: set[str] = set()
    for v in data.get("vocab", []):
        vocab_set |= {p.strip() for p in _VARIANT_SPLIT_RE.split(v["word"] or "") if p.strip()}
    # Bewusst nicht angelegte Schreibvarianten (有る → ある): gelten als gedeckt,
    # wenn ihr covered_by-Wort in der DB ist (sources/jlpt_n{level}_variants.json).
    aliases: dict[str, str] = {}
    variants_path = CANONICAL_DIR / f"jlpt_n{level}_variants.json"
    if variants_path.exists():
        vdata = json.loads(variants_path.read_text(encoding="utf-8"))
        aliases = {v["canonical"]: v["covered_by"] for v in vdata.get("variants", [])}
    cache = {
        "vocab_set": vocab_set,
        "kanji_set": {k["char"] for k in data.get("kanji", [])},
        "aliases": aliases,
    }
    _CANONICAL_CACHE[level] = cache
    return cache


def get_jlpt_coverage(level: int = 5) -> dict:
    """Liefert Coverage-Dict fuer ein JLPT-Level.

    Returns:
        {
            'level': 5,
            'vocab_total': 710, 'vocab_covered': 234, 'vocab_pct': 33.0,
            'kanji_total': 80, 'kanji_covered': 2, 'kanji_pct': 2.5,
            'lessons_published_total': N,
            'lessons_published_recent_7d': M,
            'updated_at': datetime,
        }
    """
    canon = _load_canonical(level)
    canon_vocab = canon["vocab_set"]
    canon_kanji = canon["kanji_set"]

    # Alle DB-Vokabeln/Kanji einmal holen — Vergleich gegen canonical Set
    all_db_vocab = {v.word for v in db.session.query(Vocabulary.word).all()}
    all_db_kanji = {k.character for k in db.session.query(Kanji.character).all()}

    aliases = canon.get("aliases", {})
    covered_vocab = {
        w for w in canon_vocab
        if w in all_db_vocab or aliases.get(w) in all_db_vocab
    }
    covered_kanji = canon_kanji & all_db_kanji

    vocab_total = len(canon_vocab)
    kanji_total = len(canon_kanji)
    vocab_pct = (100.0 * len(covered_vocab) / vocab_total) if vocab_total else 0.0
    kanji_pct = (100.0 * len(covered_kanji) / kanji_total) if kanji_total else 0.0

    # Lessons-Counts ueber LessonCategory.jlpt_level
    lessons_total_q = (
        db.session.query(Lesson)
        .join(LessonCategory, Lesson.category_id == LessonCategory.id)
        .filter(LessonCategory.jlpt_level == level)
        .filter(Lesson.is_published.is_(True))
    )
    lessons_total = lessons_total_q.count()

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    lessons_recent = lessons_total_q.filter(Lesson.created_at >= seven_days_ago).count()

    return {
        "level": level,
        "vocab_total": vocab_total,
        "vocab_covered": len(covered_vocab),
        "vocab_pct": round(vocab_pct, 1),
        "kanji_total": kanji_total,
        "kanji_covered": len(covered_kanji),
        "kanji_pct": round(kanji_pct, 1),
        "lessons_published_total": lessons_total,
        "lessons_published_recent_7d": lessons_recent,
        "updated_at": datetime.utcnow(),
    }


def _published_level_content(level: int):
    """Query-Basis: LessonContent publizierter Lektionen eines JLPT-Levels."""
    return (
        db.session.query(LessonContent)
        .join(Lesson, Lesson.id == LessonContent.lesson_id)
        .join(LessonCategory, Lesson.category_id == LessonCategory.id)
        .filter(LessonCategory.jlpt_level == level)
        .filter(Lesson.is_published.is_(True))
    )


def get_level_showcase(level: int = 5) -> dict:
    """Kennzahlen fuer „JLPT N5 komplett" (Startseite + /n5-bundle).

    Alles live aus der DB, nur publizierte Lektionen der Level-Module:
        lessons, modules, vocab (verschiedene Vokabeln in Lektionen),
        kanji / kanji_total (canonical-Kanji in der DB), scenes (Dialogszenen),
        quiz_questions, grammar (verschiedene Grammatikpunkte in Lektionen),
        plus vocab_pct / kanji_pct aus get_jlpt_coverage().
    """
    cov = get_jlpt_coverage(level)
    lessons_q = (
        db.session.query(Lesson)
        .join(LessonCategory, Lesson.category_id == LessonCategory.id)
        .filter(LessonCategory.jlpt_level == level)
        .filter(Lesson.is_published.is_(True))
    )
    content_q = _published_level_content(level)

    def _distinct_ids(content_type: str) -> int:
        return (
            content_q.filter(LessonContent.content_type == content_type)
            .filter(LessonContent.content_id.isnot(None))
            .with_entities(LessonContent.content_id)
            .distinct()
            .count()
        )

    quiz_questions = (
        db.session.query(QuizQuestion)
        .join(LessonContent, LessonContent.id == QuizQuestion.lesson_content_id)
        .join(Lesson, Lesson.id == LessonContent.lesson_id)
        .join(LessonCategory, Lesson.category_id == LessonCategory.id)
        .filter(LessonCategory.jlpt_level == level)
        .filter(Lesson.is_published.is_(True))
        .count()
    )

    return {
        "level": level,
        "lessons": lessons_q.count(),
        "modules": lessons_q.with_entities(Lesson.category_id).distinct().count(),
        "vocab": _distinct_ids("vocabulary"),
        "grammar": _distinct_ids("grammar"),
        "kanji": cov["kanji_covered"],
        "kanji_total": cov["kanji_total"],
        "scenes": content_q.filter(LessonContent.content_type == "dialog_slideshow").count(),
        "quiz_questions": quiz_questions,
        "vocab_pct": cov["vocab_pct"],
        "kanji_pct": cov["kanji_pct"],
        "vocab_covered": cov["vocab_covered"],
        "vocab_total": cov["vocab_total"],
    }

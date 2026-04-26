"""JLPT-Coverage-Service.

Liefert Live-Zahlen aus DB vs. canonical JLPT-Listen — fuer die Verkaufsseite
/n5-bundle und das Bundle-Pricing. Quelle der Logik: pipeline.py:499-590
(generate-lesson Skill). Hier gekapselt fuer Web-Routes.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from app import db
from app.models import Kanji, Lesson, LessonCategory, Vocabulary


# Canonical JSON liegt im generate-lesson Skill (MIT-lizenziert von elzup, von Tanos abgeleitet)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = PROJECT_ROOT / ".claude" / "skills" / "generate-lesson" / "sources"

_CANONICAL_CACHE: dict[int, dict] = {}


def _load_canonical(level: int) -> dict:
    """Laedt JLPT-Level canonical Liste. Cached pro Level."""
    if level in _CANONICAL_CACHE:
        return _CANONICAL_CACHE[level]
    path = CANONICAL_DIR / f"jlpt_n{level}_canonical.json"
    if not path.exists():
        raise FileNotFoundError(f"Canonical JLPT-N{level}-Liste fehlt: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    cache = {
        "vocab_set": {v["word"] for v in data.get("vocab", [])},
        "kanji_set": {k["char"] for k in data.get("kanji", [])},
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

    covered_vocab = canon_vocab & all_db_vocab
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

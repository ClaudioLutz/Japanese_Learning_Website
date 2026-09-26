"""Analyse (READ-ONLY): alte „Einfach"-Karten aus dem Lektions-Deck.

Hintergrund: Vor der Brücke Lektion→Wiederholen (2026-09-20, Commit 54898f7)
wurde die erste Deck-Bewertung nicht gedeckelt. Lernende drückten beim
Erstkontakt im Lektions-Deck fast nur „Einfach" → FSRS setzt die Karte direkt
in den Review-Zustand mit Anfangs-Stabilität w[3] (~8.3 Tage), obwohl die
Karte nie wirklich wiederholt wurde.

Kandidat = CardReviewState mit
  - genau EINEM ReviewLog-Eintrag (user, content, direction),
  - dieser Eintrag mit rating=4 (Easy) vor dem Stichtag (Default 2026-09-20),
  - Quelle Deck: source='deck' oder NULL (Altlogs vor Einführung von
    ReviewLog.source sind NULL; der einzige Review einer Karte ist dort
    praktisch immer der Deck-Erstkontakt),
  - nicht suspendiert, reps == 1.

Usage (auf hp-ubuntu, DATABASE_URL auf localhost:5432 überschreiben):
  DATABASE_URL=postgresql://app_user:<pw>@localhost:5432/japanese_learning \\
    venv/bin/python scripts/analyze_easy_cards.py [--cutoff 2026-09-20] [--min-days 30] [--list]

Schreibt nichts. Korrektur: scripts/fix_easy_cards.py.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

logger = logging.getLogger("analyze_easy_cards")

DEFAULT_CUTOFF = "2026-09-20"

CANDIDATE_SQL = """
SELECT c.id, c.user_id, c.content_id, c.direction, c.fsrs_card_state,
       c.due_date, c.status, c.reps, r.rating, r.reviewed_at, r.source
FROM card_review_state c
JOIN review_log r
  ON r.user_id = c.user_id AND r.content_id = c.content_id AND r.direction = c.direction
WHERE r.rating = 4
  AND r.reviewed_at < :cutoff
  AND (r.source IS NULL OR r.source = 'deck')
  AND c.status <> 'suspended'
  AND c.reps = 1
  AND (SELECT count(*) FROM review_log r2
       WHERE r2.user_id = c.user_id AND r2.content_id = c.content_id
         AND r2.direction = c.direction) = 1
ORDER BY c.user_id, c.due_date
"""


@dataclass
class EasyCard:
    state_id: int
    user_id: int
    content_id: int
    direction: str
    card_json: dict
    due_date: datetime  # naive UTC
    status: str
    reps: int
    reviewed_at: datetime  # naive UTC
    source: str | None
    raw_state: str = ""  # Original-JSON (Optimistic-Lock beim Schreiben)

    @property
    def stability(self) -> float | None:
        return self.card_json.get("stability")

    @property
    def interval_days(self) -> float:
        return (self.due_date - self.reviewed_at).total_seconds() / 86400

    def due_in_days(self, now: datetime) -> float:
        return (self.due_date - now).total_seconds() / 86400


def _as_naive_utc(value) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fetch_candidates(conn, cutoff: str = DEFAULT_CUTOFF) -> list[EasyCard]:
    """Alle Kandidaten (siehe Modul-Docstring). ``conn``: SQLAlchemy-Connection."""
    rows = conn.execute(text(CANDIDATE_SQL), {"cutoff": cutoff}).mappings().all()
    cards = []
    for r in rows:
        try:
            card_json = json.loads(r["fsrs_card_state"])
        except (TypeError, ValueError):
            logger.warning("Korrupter FSRS-State bei card_review_state.id=%s — übersprungen", r["id"])
            continue
        cards.append(EasyCard(
            state_id=r["id"], user_id=r["user_id"], content_id=r["content_id"],
            direction=r["direction"], card_json=card_json,
            due_date=_as_naive_utc(r["due_date"]), status=r["status"], reps=r["reps"],
            reviewed_at=_as_naive_utc(r["reviewed_at"]), source=r["source"],
            raw_state=r["fsrs_card_state"],
        ))
    return cards


def summarize(cards: list[EasyCard], now: datetime, min_days: float) -> dict:
    per_user = Counter(c.user_id for c in cards)
    return {
        "total": len(cards),
        "per_user": dict(sorted(per_user.items())),
        "interval_gt_min": sum(1 for c in cards if c.interval_days > min_days),
        "due_gt_min": sum(1 for c in cards if c.due_in_days(now) > min_days),
        "not_yet_due": sum(1 for c in cards if c.due_in_days(now) > 0),
        "max_interval_days": round(max((c.interval_days for c in cards), default=0), 1),
        "stabilities": dict(Counter(round(c.stability or 0, 2) for c in cards)),
    }


def engine_from_env():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL fehlt (auf hp-ubuntu: …@localhost:5432/japanese_learning)")
    return create_engine(url)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="Stichtag (exklusiv), Default 2026-09-20")
    ap.add_argument("--min-days", type=float, default=30.0,
                    help="Schwelle für 'lange' Intervalle/Fälligkeiten (Tage)")
    ap.add_argument("--list", action="store_true", help="Alle Kandidaten einzeln auflisten")
    args = ap.parse_args(argv)

    now = utcnow_naive()
    with engine_from_env().connect() as conn:
        cards = fetch_candidates(conn, args.cutoff)

    s = summarize(cards, now, args.min_days)
    logger.info("Kandidaten (1 Review, Easy, Deck/NULL, vor %s): %d", args.cutoff, s["total"])
    logger.info("  pro User: %s", s["per_user"])
    logger.info("  Intervall > %g Tage: %d", args.min_days, s["interval_gt_min"])
    logger.info("  fällig in > %g Tagen: %d", args.min_days, s["due_gt_min"])
    logger.info("  noch nicht fällig: %d", s["not_yet_due"])
    logger.info("  max. Intervall: %.1f Tage", s["max_interval_days"])
    logger.info("  Stabilitäten: %s", s["stabilities"])

    if args.list:
        logger.info("%-8s %-6s %-8s %-8s %-10s %-9s %-8s %-19s %s",
                    "state_id", "user", "content", "dir", "stability", "interval", "due_in", "reviewed_at", "source")
        for c in cards:
            logger.info("%-8d %-6d %-8d %-8s %-10.2f %-9.1f %-8.1f %-19s %s",
                        c.state_id, c.user_id, c.content_id, c.direction, c.stability or 0,
                        c.interval_days, c.due_in_days(now),
                        c.reviewed_at.strftime("%Y-%m-%d %H:%M"), c.source or "NULL")
    return 0


if __name__ == "__main__":
    sys.exit(main())

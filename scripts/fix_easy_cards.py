"""Korrektur alter „Einfach"-Deck-Karten (DRY-RUN-Default, --apply schreibt).

Kandidaten wie in scripts/analyze_easy_cards.py: genau EIN Review, rating=4
(Easy), vor dem Stichtag, Quelle Deck/NULL, nicht suspendiert. Karten mit mehr
als einem Review oder einer späteren Bewertung werden nie angefasst (die
Kandidaten-Abfrage verlangt count(review_log)=1 und reps=1; das UPDATE prüft
zusätzlich, dass sich der FSRS-State seit dem Lesen nicht geändert hat).

Korrektur (FSRS-konform): der einzige Review wird mit „Gut" statt „Einfach"
neu durchgerechnet — frische Card, Scheduler mit den Parametern des Users
(desired_retention/fsrs_parameters, ohne Fuzzing), review_datetime = Zeitpunkt
des Original-Reviews. Übernommen werden state/step/stability/difficulty der
Neuberechnung; die Fälligkeit wird auf höchstens ``--cap-days`` (14) Tage ab
jetzt gekappt. ReviewLog bleibt unverändert (Historie bleibt wahr).

Vor dem Schreiben: pg_dump der Tabelle card_review_state nach
``--backup-dir`` (Default /home/hp-ubuntu/jpl-backups). Ohne Backup kein Apply.

Usage (auf hp-ubuntu):
  DATABASE_URL=postgresql://app_user:<pw>@localhost:5432/japanese_learning \\
    venv/bin/python scripts/fix_easy_cards.py            # Dry-Run
  … scripts/fix_easy_cards.py --apply                    # Backup + schreiben
"""
from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fsrs import Card, Rating, Scheduler, State
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analyze_easy_cards import (  # noqa: E402
    DEFAULT_CUTOFF,
    EasyCard,
    engine_from_env,
    fetch_candidates,
    utcnow_naive,
)

logger = logging.getLogger("fix_easy_cards")

DEFAULT_BACKUP_DIR = "/home/hp-ubuntu/jpl-backups"
DEFAULT_CAP_DAYS = 14
STATE_MAP = {State.Learning: "learning", State.Review: "review", State.Relearning: "relearning"}


@dataclass
class Plan:
    card: EasyCard
    new_json: str
    new_due: datetime  # naive UTC
    new_status: str
    old_stability: float
    new_stability: float


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def load_scheduler_settings(conn) -> dict[int, dict]:
    """user_id → Scheduler-kwargs (desired_retention, parameters)."""
    rows = conn.execute(text(
        "SELECT user_id, desired_retention, fsrs_parameters FROM user_srs_settings"
    )).mappings().all()
    out = {}
    for r in rows:
        kw = {}
        if r["desired_retention"]:
            kw["desired_retention"] = float(r["desired_retention"])
        if r["fsrs_parameters"]:
            kw["parameters"] = tuple(json.loads(r["fsrs_parameters"]))
        out[r["user_id"]] = kw
    return out


def plan_card(card: EasyCard, now: datetime, cap_days: float = DEFAULT_CAP_DAYS,
              scheduler_kwargs: dict | None = None) -> Plan | None:
    """Neuberechnung „Gut" statt „Einfach". None = nichts zu tun (idempotent)."""
    scheduler = Scheduler(enable_fuzzing=False, **(scheduler_kwargs or {}))
    last_review = card.card_json.get("last_review")
    review_dt = _aware(datetime.fromisoformat(last_review)) if last_review else _aware(card.reviewed_at)

    fresh = Card(card_id=card.card_json.get("card_id"), due=review_dt)
    replay, _ = scheduler.review_card(fresh, Rating.Good, review_datetime=review_dt)

    old_stab = float(card.stability or 0)
    if old_stab <= (replay.stability or 0) + 1e-6:
        return None  # schon korrigiert bzw. nicht stabiler als „Gut"

    cap = _aware(now) + timedelta(days=cap_days)
    replay.due = min(replay.due, cap)
    new_due = replay.due.astimezone(timezone.utc).replace(tzinfo=None)
    return Plan(
        card=card, new_json=replay.to_json(), new_due=new_due,
        new_status=STATE_MAP.get(replay.state, "review"),
        old_stability=old_stab, new_stability=float(replay.stability),
    )


def build_plans(conn, cutoff: str, now: datetime, cap_days: float) -> list[Plan]:
    settings = load_scheduler_settings(conn)
    plans = []
    for c in fetch_candidates(conn, cutoff):
        p = plan_card(c, now, cap_days, settings.get(c.user_id))
        if p:
            plans.append(p)
    return plans


def apply_plans(conn, plans: list[Plan], now: datetime) -> int:
    """Schreibt die Pläne (im Transaktions-Kontext des Aufrufers). Rückgabe: # Zeilen."""
    written = 0
    for p in plans:
        res = conn.execute(text(
            "UPDATE card_review_state SET fsrs_card_state = :new_json, due_date = :due, "
            "status = :status, updated_at = :now "
            "WHERE id = :id AND reps = 1 AND fsrs_card_state = :old_json"
        ), {
            "new_json": p.new_json, "due": p.new_due, "status": p.new_status, "now": now,
            "id": p.card.state_id, "old_json": p.card.raw_state,
        })
        written += res.rowcount or 0
    return written


def backup_table(database_url: str, backup_dir: str, now: datetime) -> Path:
    """pg_dump -t card_review_state → <backup_dir>/card_review_state_<ts>.sql.gz."""
    from sqlalchemy.engine import make_url

    if not shutil.which("pg_dump"):
        raise RuntimeError("pg_dump nicht gefunden — ohne Backup kein Apply")
    url = make_url(database_url)
    target_dir = Path(backup_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / f"card_review_state_{now:%Y%m%d_%H%M%S}.sql.gz"
    env = dict(os.environ, PGPASSWORD=url.password or "")
    cmd = ["pg_dump", "-h", url.host or "localhost", "-p", str(url.port or 5432),
           "-U", url.username or "", "-d", url.database or "", "-t", "card_review_state"]
    proc = subprocess.run(cmd, env=env, capture_output=True, check=False)
    if proc.returncode != 0 or not proc.stdout:
        raise RuntimeError(f"pg_dump fehlgeschlagen: {proc.stderr.decode(errors='replace')[:300]}")
    with gzip.open(out, "wb") as fh:
        fh.write(proc.stdout)
    return out


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description="Alte Easy-Deck-Karten FSRS-konform korrigieren")
    ap.add_argument("--apply", action="store_true", help="Wirklich schreiben (sonst Dry-Run)")
    ap.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    ap.add_argument("--cap-days", type=float, default=DEFAULT_CAP_DAYS)
    ap.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR)
    ap.add_argument("--expect", type=int, default=None,
                    help="Erwartete Anzahl; bei Abweichung >10%% bricht --apply ab")
    args = ap.parse_args(argv)

    now = utcnow_naive()
    engine = engine_from_env()
    with engine.connect() as conn:
        plans = build_plans(conn, args.cutoff, now, args.cap_days)

    n = len(plans)
    changed_due = sum(1 for p in plans if p.new_due != p.card.due_date)
    became_due_now = sum(1 for p in plans if p.card.due_date > now >= p.new_due)
    logger.info("%s: %d Karten zu korrigieren", "APPLY" if args.apply else "DRY-RUN", n)
    per_user: dict[int, int] = {}
    for p in plans:
        per_user[p.card.user_id] = per_user.get(p.card.user_id, 0) + 1
    logger.info("  pro User: %s", dict(sorted(per_user.items())))
    logger.info("  Fälligkeit ändert sich: %d (davon neu sofort fällig: %d)", changed_due, became_due_now)
    if plans:
        logger.info("  Stabilität alt→neu (Bsp.): %.2f → %.2f, Status → %s",
                    plans[0].old_stability, plans[0].new_stability, plans[0].new_status)

    if not args.apply:
        logger.info("Dry-Run — nichts geschrieben. Mit --apply ausführen.")
        return 0
    if args.expect is not None and abs(n - args.expect) > max(1, args.expect * 0.1):
        logger.error("Abbruch: %d Karten weichen von erwarteten %d ab.", n, args.expect)
        return 2
    if n == 0:
        logger.info("Nichts zu tun.")
        return 0

    backup = backup_table(os.environ["DATABASE_URL"], args.backup_dir, now)
    logger.info("Backup: %s", backup)
    with engine.begin() as conn:
        written = apply_plans(conn, plans, now)
    logger.info("Geschrieben: %d von %d Karten.", written, n)
    return 0 if written == n else 1


if __name__ == "__main__":
    sys.exit(main())

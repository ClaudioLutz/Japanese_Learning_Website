"""Setzt die Lektions-Cover (``lesson.thumbnail_url``) auf die neuen,
mit Gemini erzeugten Flat-Gouache-Cover.

Die Cover-Dateien liegen unter
``app/static/uploads/lessons/cover_images/cover_<id>.webp`` (per scp auf das
hp-ubuntu uploads-Volume gebracht). Dieses Skript zeigt jeder published Lektion
aus ``scripts/data/cover_image_prompts.json`` auf ihr neues Cover.

SICHERHEIT (Produktions-DB!):
  * Default ist DRY-RUN — es wird nichts geschrieben.
  * ``--apply`` schreibt; davor wird IMMER ein JSON-Backup der alten
    thumbnail_url-Werte unter ``backups/cover_thumbnails/`` abgelegt.
  * Es wird ausschliesslich die Spalte ``thumbnail_url`` der Tabelle ``lesson``
    angefasst — keine Nutzer-/Zahlungs-/Fortschrittsdaten.
  * Bereits korrekt gesetzte Zeilen werden uebersprungen (idempotent).

Aufruf (aus dem Projekt-Root, wo DATABASE_URL erreichbar ist):
    python -m scripts.apply_cover_thumbnails            # Dry-run
    python -m scripts.apply_cover_thumbnails --apply    # tatsaechlich schreiben
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Lesson  # noqa: E402

PROMPTS_FILE = ROOT / "scripts" / "data" / "cover_image_prompts.json"
BACKUP_DIR = ROOT / "backups" / "cover_thumbnails"
# Relativ (ohne /uploads-Praefix, ohne fuehrenden Slash): get_thumbnail_url()
# baut daraus via url_for('routes.uploaded_file', filename=...) die /uploads/-URL.
# Ein gespeicherter /uploads-Praefix wuerde zu /uploads//uploads/... (404) fuehren.
URL_TPL = "lessons/cover_images/cover_{id}.webp"


def load_lesson_ids() -> list[int]:
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    return [c["lesson_id"] for c in data["covers"]]


def write_backup(rows: list[Lesson]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"cover_thumbnails_backup_{stamp}.json"
    payload = [{"id": r.id, "title": r.title, "thumbnail_url": r.thumbnail_url} for r in rows]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Tatsaechlich schreiben (Default: Dry-run)")
    args = parser.parse_args()

    ids = load_lesson_ids()
    app = create_app()
    with app.app_context():
        rows = Lesson.query.filter(Lesson.id.in_(ids)).all()
        found = {r.id for r in rows}
        missing = sorted(set(ids) - found)
        if missing:
            print(f"WARNUNG — IDs nicht in DB gefunden: {missing}")

        planned, skipped = [], 0
        for r in sorted(rows, key=lambda x: x.id):
            target = URL_TPL.format(id=r.id)
            if r.thumbnail_url == target:
                skipped += 1
                continue
            planned.append((r, target))

        print(f"{len(rows)} Lektionen geladen, {skipped} bereits korrekt, "
              f"{len(planned)} zu aktualisieren\n")
        for r, target in planned:
            print(f"  [{r.id}] {r.title[:48]:48} {r.thumbnail_url}  ->  {target}")

        if not planned:
            print("\nNichts zu tun.")
            return

        if not args.apply:
            print("\nDRY-RUN — es wurde nichts geschrieben. Mit --apply ausfuehren.")
            return

        backup_path = write_backup([r for r, _ in planned])
        print(f"\nBackup geschrieben: {backup_path}")
        for r, target in planned:
            r.thumbnail_url = target
        db.session.commit()
        print(f"FERTIG — {len(planned)} thumbnail_url aktualisiert.")


if __name__ == "__main__":
    main()

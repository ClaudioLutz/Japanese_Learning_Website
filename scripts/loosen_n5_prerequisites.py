"""Lockert die N5-Lernpfad-Voraussetzungen: setzt prerequisite_category_id=NULL
fuer alle N5-Module, sodass Lerner in beliebiger Reihenfolge starten koennen.

Hintergrund: Strenge Vorgaenger-Sperren (Hiragana 80% komplett bevor Begruessung
geoeffnet wird) sind fuer erwachsene Lerner abschreckend. Modernes Lern-Pattern
(Brilliant, Duolingo Path 2022+, MasterClass): Reihenfolge als Empfehlung statt
Korridor. Die display_order bleibt — der Pfad schaut linear aus, ist aber an
jeder Stelle klickbar.

Idempotent. Speichert die alten Voraussetzungen als Backup-Datei, sodass --restore
sie zurueckdrehen kann.

Usage:
    venv/Scripts/python scripts/loosen_n5_prerequisites.py            # apply
    venv/Scripts/python scripts/loosen_n5_prerequisites.py --dry-run  # preview
    venv/Scripts/python scripts/loosen_n5_prerequisites.py --restore  # zurueck
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import create_app, db  # noqa: E402
from app.models import LessonCategory  # noqa: E402

JLPT_LEVEL = 5
BACKUP_PATH = Path(__file__).resolve().parent / "_n5_prerequisites_backup.json"


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    restore = "--restore" in sys.argv

    app = create_app()
    with app.app_context():
        cats = (
            db.session.query(LessonCategory)
            .filter(LessonCategory.jlpt_level == JLPT_LEVEL)
            .order_by(LessonCategory.display_order)
            .all()
        )

        if restore:
            if not BACKUP_PATH.exists():
                print(f"[FEHLER] Backup-Datei {BACKUP_PATH} existiert nicht.")
                return 1
            backup = json.loads(BACKUP_PATH.read_text(encoding="utf-8"))
            print(f"[RESTORE] Stelle Voraussetzungen aus {BACKUP_PATH} wieder her.")
            restored = 0
            for cat in cats:
                if str(cat.id) in backup:
                    new_pre = backup[str(cat.id)]
                    if cat.prerequisite_category_id != new_pre:
                        if not dry_run:
                            cat.prerequisite_category_id = new_pre
                        restored += 1
                        print(f"  [{cat.slug}] prerequisite -> {new_pre}")
            if not dry_run:
                db.session.commit()
            print(f"[OK] {restored} Module wiederhergestellt.")
            return 0

        # Apply: alle prerequisites entfernen + Backup schreiben
        backup = {str(cat.id): cat.prerequisite_category_id for cat in cats
                  if cat.prerequisite_category_id is not None}
        if not dry_run and backup:
            BACKUP_PATH.write_text(
                json.dumps(backup, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[BACKUP] Alte Voraussetzungen gespeichert: {BACKUP_PATH}")

        cleared = 0
        unchanged = 0
        for cat in cats:
            if cat.prerequisite_category_id is not None:
                old = cat.prerequisite_category_id
                if not dry_run:
                    cat.prerequisite_category_id = None
                cleared += 1
                print(f"  GELOCKERT [{cat.slug}]  (war: prerequisite={old})")
            else:
                unchanged += 1

        if not dry_run:
            db.session.commit()

        print("=" * 70)
        mode = "DRY-RUN" if dry_run else "COMMIT"
        print(f"  N5-Prerequisites lockern ({mode})")
        print("=" * 70)
        print(f"  Gelockert: {cleared}")
        print(f"  Schon offen (unveraendert): {unchanged}")
        print(f"  Total N5-Module: {len(cats)}")
        if cleared > 0:
            print()
            print("  Konsequenz: Alle Module sind jetzt von Anfang an klickbar.")
            print("  Display-Reihenfolge (display_order) bleibt unveraendert —")
            print("  der Pfad schaut weiterhin linear aus, ist aber kein Korridor.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

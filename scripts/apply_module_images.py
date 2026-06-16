"""Setzt LessonCategory.image_url auf den Modul-Banner-Pfad.

Fuer jede N5-Kategorie, fuer die unter app/static/uploads/modules/
eine Datei module_<slug>.webp existiert, wird
  image_url = 'modules/module_<slug>.webp'
gesetzt (uploads-relativer Pfad, serviert via routes.uploaded_file).

Idempotent. DRY-RUN per Default — erst mit --apply wird geschrieben.

Usage:
  python scripts/apply_module_images.py            # Vorschau (DRY-RUN)
  python scripts/apply_module_images.py --apply     # schreiben
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "modules"
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    apply = "--apply" in sys.argv

    from app import create_app, db
    from app.models import LessonCategory

    app = create_app()
    with app.app_context():
        cats = (
            LessonCategory.query.filter(LessonCategory.slug.isnot(None))
            .order_by(LessonCategory.display_order.asc(), LessonCategory.id.asc())
            .all()
        )
        changes = 0
        skipped_missing = 0
        for c in cats:
            fname = f"module_{c.slug}.webp"
            if not (MODULES_DIR / fname).exists():
                continue
            rel = f"modules/{fname}"
            if c.image_url == rel:
                print(f"=  [{c.id}] {c.slug}: bereits gesetzt")
                continue
            print(f"~  [{c.id}] {c.slug}: {c.image_url!r} -> {rel!r}")
            changes += 1
            if apply:
                c.image_url = rel
        # Kategorien ohne Bilddatei nur informativ auflisten
        for c in cats:
            if not (MODULES_DIR / f"module_{c.slug}.webp").exists():
                skipped_missing += 1
                print(f"!  [{c.id}] {c.slug}: keine Bilddatei -> uebersprungen")

        if apply and changes:
            db.session.commit()
            print(f"\nFERTIG (APPLY) — {changes} Kategorien aktualisiert, "
                  f"{skipped_missing} ohne Bild.")
        else:
            mode = "APPLY, nichts zu tun" if apply else "DRY-RUN"
            print(f"\n{mode} — {changes} Aenderungen vorgemerkt, "
                  f"{skipped_missing} ohne Bild. (--apply zum Schreiben)")


if __name__ == "__main__":
    main()

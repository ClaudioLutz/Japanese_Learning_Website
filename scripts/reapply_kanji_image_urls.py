"""Re-applien der `kanji.image_url`-Werte aus existierenden Dateien.

Nach einem Cloud-Pull werden lokale Spalten ueberschrieben, wenn die Cloud
die Spalte mittlerweile hat aber alle NULL-Werte. Dieses Skript scannt
`app/static/uploads/kanji_generated/` und setzt fuer jede Datei
`kanji_{id}_{hash}.png` die `image_url`-Spalte des Kanji mit ID=`id`.

Idempotent: ueberspringt Eintraege deren image_url bereits gesetzt ist.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db  # noqa: E402
from app.models import Kanji  # noqa: E402

IMAGE_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "kanji_generated"
PATTERN = re.compile(r"^kanji_(\d+)_[a-f0-9]+\.png$")


def main() -> int:
    app = create_app()
    with app.app_context():
        if not IMAGE_DIR.exists():
            print(f"[FEHLER] Verzeichnis fehlt: {IMAGE_DIR}")
            return 1

        files = list(IMAGE_DIR.glob("kanji_*.png"))
        print(f"[INFO] {len(files)} Bilddateien gefunden")

        applied = 0
        skipped = 0
        for f in files:
            m = PATTERN.match(f.name)
            if not m:
                print(f"  [SKIP] Unerwartetes Filename-Format: {f.name}")
                continue
            kanji_id = int(m.group(1))
            kanji = db.session.get(Kanji, kanji_id)
            if not kanji:
                print(f"  [SKIP] Kein Kanji mit id={kanji_id}")
                continue
            url = f"kanji_generated/{f.name}"
            if kanji.image_url == url:
                skipped += 1
                continue
            kanji.image_url = url
            applied += 1
            print(f"  [OK] {kanji.character} (id={kanji_id}) -> {url}")

        if applied:
            db.session.commit()
            print(f"\n[DONE] {applied} updated, {skipped} bereits korrekt.")
        else:
            print(f"\n[DONE] Keine Aenderungen, {skipped} bereits korrekt.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

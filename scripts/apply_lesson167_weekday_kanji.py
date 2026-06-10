"""Apply: Lektion 167 — fehlende Wochentags-Kanji 日月火金土 als eigenständige
Kanji-Karten ergänzen.

Lektion 167 ("N5 Kanji 2 — Tage und Wochentage 日月火水木金土") lehrte bisher nur
水 und 木 als eigenständige Kanji-Karten (Seite 3); 日月火金土 kamen nur in
Komposita (日曜日 etc.) vor. Dieses Skript fügt die fehlenden 5 Kanji als
Kanji-Karten auf Seite 3 ein und ordnet sie kanonisch 日月火水木金土 an.

Die 5 Kanji-Datensätze existieren bereits sauber in der ``kanji``-Tabelle
(ids 19/20/21/24/25) — es wird kein Kanji-Content verfasst, nur die
Lektionsstruktur ergänzt.

SICHERHEIT (Produktions-DB!):
  * Default DRY-RUN; ``--apply`` schreibt nach Auto-Backup unter
    ``backups/lesson167/`` (Seite-3-Reihenfolge + eingefügte Karten).
  * Nur ``lesson_content`` (eine Lektion, eine Seite). Keine Nutzerdaten.
  * Idempotent: existiert bereits eine Kanji-Karte für 日 in Lektion 167,
    wird nichts getan.
  * Harte Guards: bricht ab, wenn der erwartete Seiten-3-Zustand nicht passt
    (Daten-Drift) — schreibt dann nichts.

Aufruf (auf hp-ubuntu, DATABASE_URL erreichbar):
    python -m scripts.apply_lesson167_weekday_kanji            # Dry-run
    python -m scripts.apply_lesson167_weekday_kanji --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import LessonContent, Kanji  # noqa: E402

LESSON_ID = 167
PAGE = 3
BACKUP_DIR = ROOT / "backups" / "lesson167"

# Bestehende Seite-3-Items, die verschoben werden: lc_id -> (erwarteter content_type,
# erwartete content_id, neuer order_index)
REORDER = {
    6850: ("kanji", 22, 11),       # 水
    6851: ("kanji", 23, 12),       # 木
    6852: ("vocabulary", 452, 15),  # お金
    6853: ("vocabulary", 53, 16),   # 日本
}
# Neue Kanji-Karten: kanji_id -> (erwartetes Zeichen, order_index)
NEW_CARDS = {
    19: ("日", 8),
    20: ("月", 9),
    21: ("火", 10),
    24: ("金", 13),
    25: ("土", 14),
}


def write_backup(payload: dict) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"lesson167_backup_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Schreibt Änderungen (sonst Dry-run)")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"=== Lektion 167: Wochentags-Kanji 日月火金土 ergänzen ({mode}) ===")

        # Idempotenz: existiert schon eine Kanji-Karte für 日 in 167?
        already = (LessonContent.query
                   .filter_by(lesson_id=LESSON_ID, content_type="kanji", content_id=19)
                   .first())
        if already:
            print("Bereits angewendet (Kanji-Karte 日 existiert in Lektion 167). Nichts zu tun.")
            return 0

        # Guards: erwarteten Zustand prüfen
        problems: list[str] = []
        for lc_id, (ctype, cid, _new) in REORDER.items():
            lc = LessonContent.query.get(lc_id)
            if not lc:
                problems.append(f"lc {lc_id} fehlt")
            elif not (lc.lesson_id == LESSON_ID and lc.page_number == PAGE
                      and lc.content_type == ctype and lc.content_id == cid):
                problems.append(
                    f"lc {lc_id} unerwartet: lesson={lc.lesson_id} page={lc.page_number} "
                    f"type={lc.content_type} cid={lc.content_id} (erwartet {ctype}/{cid} auf 167/3)")
        for kid, (ch, _ord) in NEW_CARDS.items():
            k = Kanji.query.get(kid)
            if not k:
                problems.append(f"Kanji-Datensatz id={kid} ({ch}) fehlt")
            elif k.character != ch:
                problems.append(f"Kanji id={kid}: Zeichen {k.character!r} != erwartet {ch!r}")

        if problems:
            print(f"ABBRUCH — erwarteter Zustand passt nicht ({len(problems)}):")
            for p in problems:
                print(f"  ! {p}")
            return 2
        print("Guards ok.")

        # Backup
        page_rows = (LessonContent.query
                     .filter_by(lesson_id=LESSON_ID, page_number=PAGE)
                     .order_by(LessonContent.order_index).all())
        backup = {"page3_before": [{"id": r.id, "content_type": r.content_type,
                                    "content_id": r.content_id, "order_index": r.order_index}
                                   for r in page_rows]}

        # Plan ausgeben
        print("\nGeplante neue Reihenfolge Seite 3:")
        plan = []
        for r in page_rows:
            new_ord = REORDER.get(r.id, (None, None, r.order_index))[2] if r.id in REORDER else r.order_index
            plan.append((new_ord, f"(bestehend) {r.content_type}/{r.content_id}", r.id))
        for kid, (ch, ordr) in NEW_CARDS.items():
            plan.append((ordr, f"(NEU) kanji {ch} (id {kid})", None))
        for ordr, label, lcid in sorted(plan):
            print(f"  {ordr:>2}: {label}{'' if lcid is None else f'  [lc {lcid}]'}")

        if not args.apply:
            print("\nDRY-RUN — nichts geschrieben. Mit --apply ausführen.")
            return 0

        backup_path = write_backup(backup)
        print(f"\nBackup geschrieben: {backup_path}")

        # Reorder bestehende
        for lc_id, (_ct, _cid, new_ord) in REORDER.items():
            LessonContent.query.get(lc_id).order_index = new_ord
        # Insert neue Kanji-Karten
        inserted = []
        for kid, (ch, ordr) in NEW_CARDS.items():
            db.session.add(LessonContent(
                lesson_id=LESSON_ID, content_type="kanji", content_id=kid,
                page_number=PAGE, order_index=ordr,
                is_optional=False, is_interactive=False, generated_by_ai=True))
            inserted.append((ch, kid, ordr))
        db.session.commit()
        print(f"GESCHRIEBEN: 4 Karten umsortiert, {len(inserted)} Kanji-Karten eingefügt "
              f"({', '.join(ch for ch, _, _ in inserted)}).")
        return 0


if __name__ == "__main__":
    sys.exit(main())

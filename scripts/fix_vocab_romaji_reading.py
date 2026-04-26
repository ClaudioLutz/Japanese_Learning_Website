"""Fix vocabulary entries where romaji landed in the `reading` column and `romaji` is empty.

Group A (reine Kana): word ist Hiragana/Katakana -> reading = word, romaji = (alter reading-Wert)
Group B (Kanji-Worte): manuelles Mapping fuer 韓国 / 中国 / 日本

Run:
    python scripts/fix_vocab_romaji_reading.py            # Preview (Dry-Run)
    python scripts/fix_vocab_romaji_reading.py --commit   # Tatsaechlich schreiben
"""
from __future__ import annotations

import argparse
import sys

from app import create_app, db
from app.models import Vocabulary

GROUP_B = {
    49: ("かんこく", "kankoku"),
    51: ("ちゅうごく", "chuugoku"),
    53: ("にほん", "nihon"),
}


def find_candidates() -> list[Vocabulary]:
    return (
        Vocabulary.query
        .filter(db.or_(Vocabulary.romaji.is_(None), Vocabulary.romaji == ""))
        .filter(Vocabulary.reading.op("~")(r"^[a-zA-Z\s\-]+$"))
        .order_by(Vocabulary.id)
        .all()
    )


def fix_entry(v: Vocabulary) -> tuple[str, str, str]:
    """Return (reading_new, romaji_new, group_label)."""
    if v.id in GROUP_B:
        reading_new, romaji_new = GROUP_B[v.id]
        return reading_new, romaji_new, "B"
    return v.word, v.reading, "A"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true", help="Tatsaechlich schreiben")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        candidates = find_candidates()
        print(f"Kandidaten gefunden: {len(candidates)}")

        changes = []
        for v in candidates:
            reading_new, romaji_new, group = fix_entry(v)
            if v.reading == reading_new and (v.romaji or "") == romaji_new:
                continue
            changes.append((v, reading_new, romaji_new, group))

        print(f"Aenderungen geplant: {len(changes)}")
        for v, r_new, ro_new, group in changes[:10]:
            print(
                f"  [{group}] id={v.id:>4} word={v.word!r:>20} "
                f"reading {v.reading!r} -> {r_new!r}, romaji {v.romaji!r} -> {ro_new!r}"
            )
        if len(changes) > 10:
            print(f"  ... ({len(changes) - 10} weitere)")

        if not args.commit:
            print("\nDRY-RUN. Mit --commit ausfuehren um zu schreiben.")
            return 0

        for v, r_new, ro_new, _ in changes:
            v.reading = r_new
            v.romaji = ro_new
        db.session.commit()
        print(f"OK — {len(changes)} Eintraege aktualisiert.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

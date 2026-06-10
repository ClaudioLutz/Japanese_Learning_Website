"""Apply: N5-Vokabel-Cleanup + Kanji-Vereinheitlichung.

Schreibt eine von Claude verfasste und adversarial faktengepruefte Aenderungs-
menge (``scripts/data/cleanup_kanji_changeset.json``) in die DB. Vier Bloecke:

1. ``meaningDe``   — fehlende deutsche Wortbedeutung (``vocabulary.meaning_de``)
2. ``readingFix``  — Romaji aus ``vocabulary.reading`` in ``vocabulary.romaji``
                     trennen (Format war "kana (romaji)")
3. ``kanjiUpsert`` — fehlende Kanji-Datensaetze anlegen / verschmutzte (Romaji in
                     onyomi/kunyomi) bereinigen
4. ``cardUpgrades``— Einzelzeichen-Vokabelkarten in den Kanji-Lektionen
                     (164/167/168/169/170) auf ``content_type='kanji'`` umstellen,
                     damit Lerner Strichzahl/On-Kun bekommen (171-173-Standard).

SICHERHEIT (Produktions-DB!):
  * Default ist DRY-RUN — es wird nichts geschrieben.
  * ``--apply`` schreibt; davor IMMER ein JSON-Backup der betroffenen Zeilen
    unter ``backups/cleanup_kanji/``.
  * Es werden ausschliesslich Content-Tabellen angefasst (vocabulary, kanji,
    lesson_content) — keine Nutzer-/Zahlungs-/Fortschrittsdaten.
  * Idempotent: bereits korrekte Zeilen werden uebersprungen.
  * Jede Aenderung wird vor dem Schreiben validiert; Ungueltiges wird NICHT
    geschrieben, sondern gemeldet.

Aufruf (auf hp-ubuntu, DATABASE_URL muss die Postgres erreichen):
    python -m scripts.apply_cleanup_kanji              # Dry-run
    python -m scripts.apply_cleanup_kanji --apply      # tatsaechlich schreiben
    python -m scripts.apply_cleanup_kanji --only meaningDe,readingFix
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Vocabulary, Kanji, LessonContent  # noqa: E402

DEFAULT_DATA = ROOT / "scripts" / "data" / "cleanup_kanji_changeset.json"
BACKUP_DIR = ROOT / "backups" / "cleanup_kanji"

HIRA_OK = re.compile(r"^[぀-ゟ.,\s]*$")
KATA_OK = re.compile(r"^[゠-ヿ.,\s]*$")


def has_latin(s: str) -> bool:
    return bool(re.search(r"[A-Za-z]", s or ""))


def validate(changeset: dict) -> list[str]:
    """Gibt eine Liste von Validierungsfehlern zurueck (leer = ok)."""
    errs: list[str] = []

    for e in changeset.get("meaningDe", []):
        if not (e.get("meaning_de") or "").strip():
            errs.append(f"meaningDe id={e.get('id')}: leer")
        elif has_latin(e["meaning_de"]) and "/" in e["meaning_de"]:
            errs.append(f"meaningDe id={e.get('id')}: enthaelt evtl. Englisch: {e['meaning_de']!r}")

    for e in changeset.get("readingFix", []):
        if has_latin(e.get("reading", "")):
            errs.append(f"readingFix id={e.get('id')}: reading enthaelt Latein: {e.get('reading')!r}")
        if not (e.get("romaji") or "").strip():
            errs.append(f"readingFix id={e.get('id')}: romaji leer")

    for e in changeset.get("kanjiUpsert", []):
        ch = e.get("character", "")
        if len(ch) != 1:
            errs.append(f"kanjiUpsert: character nicht einzeln: {ch!r}")
        on = e.get("onyomi", "")
        kun = e.get("kunyomi", "")
        if has_latin(on):
            errs.append(f"kanjiUpsert {ch}: onyomi enthaelt Latein: {on!r}")
        if has_latin(kun):
            errs.append(f"kanjiUpsert {ch}: kunyomi enthaelt Latein: {kun!r}")
        if on and not KATA_OK.match(on):
            errs.append(f"kanjiUpsert {ch}: onyomi nicht reines Katakana: {on!r}")
        if kun and not HIRA_OK.match(kun):
            errs.append(f"kanjiUpsert {ch}: kunyomi nicht reines Hiragana: {kun!r}")
        if "、" in on or "、" in kun:
            errs.append(f"kanjiUpsert {ch}: enthaelt japanisches Komma 、 (soll ', ' sein)")
        if not isinstance(e.get("stroke_count"), int) or e["stroke_count"] <= 0:
            errs.append(f"kanjiUpsert {ch}: stroke_count ungueltig: {e.get('stroke_count')!r}")
        if (e.get("meaning", "").count("/") != 1):
            errs.append(f"kanjiUpsert {ch}: meaning nicht 'Deutsch / English': {e.get('meaning')!r}")

    return errs


def write_backup(payload: dict) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"cleanup_kanji_backup_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Schreibt Aenderungen (sonst Dry-run)")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA))
    parser.add_argument("--only", type=str, default=None,
                        help="Komma-Liste von Bloecken: meaningDe,readingFix,kanjiUpsert,cardUpgrades")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"FEHLER: Datendatei nicht gefunden: {data_path}")
        return 1
    changeset = json.loads(data_path.read_text(encoding="utf-8"))
    blocks = set((args.only or "meaningDe,readingFix,kanjiUpsert,cardUpgrades").split(","))

    errs = validate(changeset)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== Cleanup + Kanji-Vereinheitlichung ({mode}) ===")
    if errs:
        print(f"VALIDIERUNG fehlgeschlagen ({len(errs)} Probleme) — es wird NICHTS geschrieben:")
        for e in errs:
            print(f"  ! {e}")
        return 2
    print("Validierung ok.")

    app = create_app()
    with app.app_context():
        backup: dict = {"vocabulary": [], "kanji": [], "lesson_content": []}
        report = {"meaningDe": 0, "readingFix": 0, "kanji_new": 0, "kanji_clean": 0, "cardUpgrades": 0, "skipped": 0}

        # 1) meaning_de
        if "meaningDe" in blocks:
            for e in changeset.get("meaningDe", []):
                v = Vocabulary.query.get(e["id"])
                if not v:
                    print(f"  ? meaningDe id={e['id']} nicht in DB")
                    continue
                if (v.meaning_de or "").strip() == e["meaning_de"].strip():
                    report["skipped"] += 1
                    continue
                backup["vocabulary"].append({"id": v.id, "field": "meaning_de", "old": v.meaning_de})
                if args.apply:
                    v.meaning_de = e["meaning_de"].strip()
                report["meaningDe"] += 1

        # 2) reading/romaji split
        if "readingFix" in blocks:
            for e in changeset.get("readingFix", []):
                v = Vocabulary.query.get(e["id"])
                if not v:
                    print(f"  ? readingFix id={e['id']} nicht in DB")
                    continue
                if v.reading == e["reading"] and (v.romaji or "") == e["romaji"]:
                    report["skipped"] += 1
                    continue
                backup["vocabulary"].append({"id": v.id, "field": "reading/romaji",
                                             "old": {"reading": v.reading, "romaji": v.romaji}})
                if args.apply:
                    v.reading = e["reading"]
                    v.romaji = e["romaji"]
                report["readingFix"] += 1

        # 3) kanji upsert (by character)
        if "kanjiUpsert" in blocks:
            for e in changeset.get("kanjiUpsert", []):
                ch = e["character"]
                k = Kanji.query.filter_by(character=ch).first()
                if k:
                    changed = (k.onyomi != e["onyomi"] or k.kunyomi != e["kunyomi"]
                               or k.stroke_count != e["stroke_count"] or k.meaning != e["meaning"]
                               or (k.radical or "") != e.get("radical", ""))
                    if not changed:
                        report["skipped"] += 1
                    continue
                    backup["kanji"].append({"id": k.id, "character": ch,
                                            "old": {"onyomi": k.onyomi, "kunyomi": k.kunyomi,
                                                    "stroke_count": k.stroke_count, "radical": k.radical,
                                                    "meaning": k.meaning}})
                    if args.apply:
                        k.onyomi = e["onyomi"]
                        k.kunyomi = e["kunyomi"]
                        k.stroke_count = e["stroke_count"]
                        k.radical = e.get("radical")
                        k.meaning = e["meaning"]
                    report["kanji_clean"] += 1
                else:
                    backup["kanji"].append({"id": None, "character": ch, "old": None})
                    if args.apply:
                        db.session.add(Kanji(
                            character=ch, onyomi=e["onyomi"], kunyomi=e["kunyomi"],
                            stroke_count=e["stroke_count"], radical=e.get("radical"),
                            meaning=e["meaning"], jlpt_level=e.get("jlpt_level", 5),
                            status="approved", created_by_ai=False))
                    report["kanji_new"] += 1
            if args.apply:
                db.session.flush()  # neue Kanji bekommen IDs fuer cardUpgrades

        # 4) card upgrades vocabulary -> kanji
        if "cardUpgrades" in blocks:
            for e in changeset.get("cardUpgrades", []):
                lc = LessonContent.query.get(e["lc_id"])
                if not lc:
                    print(f"  ? cardUpgrade lc_id={e['lc_id']} nicht in DB")
                    continue
                k = Kanji.query.filter_by(character=e["character"]).first()
                if not k:
                    print(f"  ! cardUpgrade lc_id={e['lc_id']}: kein Kanji fuer {e['character']!r} — uebersprungen")
                    continue
                if lc.content_type == "kanji" and lc.content_id == k.id:
                    report["skipped"] += 1
                    continue
                if lc.content_type != "vocabulary":
                    print(f"  ! cardUpgrade lc_id={e['lc_id']}: erwartet 'vocabulary', ist {lc.content_type!r} — uebersprungen")
                    continue
                backup["lesson_content"].append({"id": lc.id, "old": {"content_type": lc.content_type,
                                                                      "content_id": lc.content_id}})
                if args.apply:
                    lc.content_type = "kanji"
                    lc.content_id = k.id
                report["cardUpgrades"] += 1

        if args.apply:
            backup_path = write_backup(backup)
            db.session.commit()
            print(f"Backup geschrieben: {backup_path}")
            print("GESCHRIEBEN.")
        else:
            print("DRY-RUN — nichts geschrieben.")

        print("\nZusammenfassung:")
        for key, val in report.items():
            print(f"  {key:14}: {val}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

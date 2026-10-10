"""N5-Lücke 723/723 (2026-10-10): Vokabel-Zeilen korrigieren und Karten in bestehende Lektionen einhängen.

Zwei Arten von Änderungen, beide aus JSON-Dateien, alles in EINER Transaktion:

1. ``--updates DATEI`` (mehrfach möglich), Format
   ``{"updates": [{"vocab_id": 224, "field": "example_sentence_japanese", "old": "…", "new": "…", "reason": "…"}]}``
   Exakte Vorher/Nachher-Ersetzung auf einer Spalte von ``vocabulary``. Ist der Ist-Wert
   schon ``new``, gilt die Änderung als angewendet. Weicht er von ``old`` ab: SKIP.
   Neue Beispielsätze werden geprüft (nur N5-Kanji, rein japanisch, Satzende,
   ``Romaji — Deutsch``).

2. ``--cards DATEI``, Format ``{"cards": [{"lesson_id": 164, "page": 2, "after_lc": 6750,
   "vocab_id": 402, "word": "一"}]}``: hängt eine Vokabelkarte direkt hinter das Item
   ``after_lc`` (z.B. die Kanji-Karte desselben Zeichens) und nummeriert ``order_index``
   der Seite neu durch (Startwert bleibt, z.B. 0 für das Seitenbild). Steht die Vokabel
   schon in der Lektion, wird sie übersprungen.

DRY-RUN ist Standard und zeigt die SELECT-Vorschau (Ist-Werte, neue Reihenfolge je Seite,
erwartete Zeilenzahlen). ``--apply`` schreibt erst danach; bei einem SKIP wird nichts
geschrieben (ausser ``--allow-partial``). Vorher ein DB-Backup ziehen
(``sudo /usr/local/bin/jpl-db-backup.sh``).

Im Container ausführen (DATABASE_URL zeigt dort auf den Service-Host ``db``):
  sudo docker exec -w /app japanese_app python scripts/apply_n5_luecke.py \\
      --updates scripts/data/n5_luecke_bestand.json --cards scripts/data/n5_luecke_bestand.json [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, os.getcwd())

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / ".claude" / "skills" / "generate-lesson" / "sources" / "jlpt_n5_canonical.json"

ALLOWED_FIELDS = {
    "example_sentence_japanese", "example_sentence_english", "reading", "romaji",
    "meaning_de", "production_cue_de",
}
KANJI_RE = re.compile(r"[一-鿿]")
JP_RE = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")
LATIN_RE = re.compile(r"[A-Za-zĀ-ž]")


def n5_kanji() -> set[str]:
    data = json.loads(CANONICAL.read_text(encoding="utf-8"))
    return {k["char"] for k in data.get("kanji", [])}


def check_new_value(field: str, value: str, kanji_ok: set[str]) -> list[str]:
    """Prüft einen neuen Wert. Gibt Fehlertexte zurück (leer = ok)."""
    errors = []
    if not isinstance(value, str) or not value.strip():
        return ["leerer Wert"]
    if field == "example_sentence_japanese":
        bad = sorted({c for c in KANJI_RE.findall(value) if c not in kanji_ok})
        if bad:
            errors.append(f"Nicht-N5-Kanji im Beispielsatz: {''.join(bad)}")
        if LATIN_RE.search(value):
            errors.append("Lateinbuchstaben im japanischen Beispielsatz")
        if not JP_RE.search(value):
            errors.append("kein Japanisch im Beispielsatz")
        if not re.search(r"[。！？]$", value.strip()):
            errors.append("Beispielsatz endet nicht mit 。/！/？")
    elif field == "example_sentence_english":
        if " — " not in value:
            errors.append("Format 'Romaji — Deutsch' fehlt (Em-Dash)")
        elif JP_RE.search(value.split(" — ", 1)[0]):
            errors.append("Romaji-Teil enthält japanische Zeichen")
    return errors


def plan_updates(updates: list[dict], fetch, kanji_ok: set[str]):
    """Gibt (writes, report) zurück. writes: {(vocab_id, field): (alt, neu)}."""
    writes, report = {}, []
    for u in updates:
        vid, field = int(u["vocab_id"]), u["field"]
        label = f"vocabulary#{vid}.{field}"
        if field not in ALLOWED_FIELDS:
            report.append(("SKIP", label, "Feld nicht erlaubt"))
            continue
        problems = check_new_value(field, u["new"], kanji_ok)
        if problems:
            report.append(("SKIP", label, "; ".join(problems)))
            continue
        found, cur = fetch(vid, field)
        if not found:
            report.append(("SKIP", label, "Zeile fehlt"))
            continue
        if cur == u["new"]:
            report.append(("SCHON", label, ""))
            continue
        if cur != u["old"]:
            report.append(("SKIP", label, f"Ist-Wert weicht ab: {cur!r}"))
            continue
        writes[(vid, field)] = (cur, u["new"])
        report.append(("OK", label, f"{cur!r} -> {u['new']!r}"))
    return writes, report


def plan_page_order(items: list[dict], inserts: list[dict]) -> list[dict]:
    """Neue Reihenfolge einer Seite.

    items: bestehende Items [{"id", "order_index", "label"}]; inserts: [{"after_lc", "vocab_id", "label"}].
    Rückgabe: Liste in neuer Reihenfolge mit Schlüssel "new_order"; neue Items haben "id": None.
    """
    ordered = sorted(items, key=lambda x: (x["order_index"], x["id"]))
    result = []
    for it in ordered:
        result.append(dict(it))
        for ins in inserts:
            if ins["after_lc"] == it["id"]:
                result.append({"id": None, "vocab_id": ins["vocab_id"], "label": ins["label"]})
    missing = [ins for ins in inserts if not any(i["id"] == ins["after_lc"] for i in ordered)]
    if missing:
        raise ValueError(f"Anker fehlt auf der Seite: {[m['after_lc'] for m in missing]}")
    base = min((it["order_index"] for it in ordered), default=0)
    for pos, it in enumerate(result):
        it["new_order"] = base + pos
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--updates", action="append", default=[], help="JSON mit {'updates': [...]}")
    ap.add_argument("--cards", help="JSON mit {'cards': [...]}")
    ap.add_argument("--apply", action="store_true", help="wirklich schreiben (sonst DRY-RUN)")
    ap.add_argument("--allow-partial", action="store_true", help="trotz SKIPs schreiben")
    args = ap.parse_args()

    updates = []
    for path in args.updates:
        updates += json.loads(Path(path).read_text(encoding="utf-8")).get("updates", [])
    cards = json.loads(Path(args.cards).read_text(encoding="utf-8")).get("cards", []) if args.cards else []

    from app import create_app, db

    app = create_app()
    with app.app_context():
        def fetch(vid, field):
            row = db.session.execute(
                text(f"SELECT {field} FROM vocabulary WHERE id = :id"), {"id": vid}
            ).fetchone()
            return (row is not None), (row[0] if row else None)

        writes, report = plan_updates(updates, fetch, n5_kanji())
        print(f"=== Vokabel-Zeilen: {len(updates)} Änderungen geplant ===")
        for status, label, info in report:
            print(f"[{status:5}] {label} {info}")
        skips = [r for r in report if r[0] == "SKIP"]

        # Karten: je (Lektion, Seite) neue Reihenfolge berechnen
        by_page: dict[tuple[int, int], list[dict]] = {}
        card_skips = []
        for c in cards:
            lid, page, vid = int(c["lesson_id"]), int(c["page"]), int(c["vocab_id"])
            word = db.session.execute(
                text("SELECT word FROM vocabulary WHERE id = :id"), {"id": vid}).scalar()
            if word != c.get("word"):
                card_skips.append(f"L{lid} S{page}: vocabulary#{vid} ist {word!r}, erwartet {c.get('word')!r}")
                continue
            exists = db.session.execute(text(
                "SELECT count(*) FROM lesson_content WHERE lesson_id = :l AND content_type = 'vocabulary' "
                "AND content_id = :v"), {"l": lid, "v": vid}).scalar()
            if exists:
                print(f"[SCHON] L{lid}: vocabulary#{vid} {word} hängt schon an der Lektion")
                continue
            by_page.setdefault((lid, page), []).append(
                {"after_lc": int(c["after_lc"]), "vocab_id": vid, "label": f"NEU vocabulary {word}"})

        page_plans = {}
        for (lid, page), inserts in sorted(by_page.items()):
            rows = db.session.execute(text(
                "SELECT lc.id, lc.order_index, lc.content_type, coalesce(v.word, k.character, lc.title, '') "
                "FROM lesson_content lc "
                "LEFT JOIN vocabulary v ON lc.content_type = 'vocabulary' AND v.id = lc.content_id "
                "LEFT JOIN kanji k ON lc.content_type = 'kanji' AND k.id = lc.content_id "
                "WHERE lc.lesson_id = :l AND lc.page_number = :p"), {"l": lid, "p": page}).fetchall()
            items = [{"id": r[0], "order_index": r[1] or 0, "label": f"{r[2]} {r[3][:30]}"} for r in rows]
            try:
                page_plans[(lid, page)] = plan_page_order(items, inserts)
            except ValueError as exc:
                card_skips.append(f"L{lid} S{page}: {exc}")
                continue
            print(f"\n--- L{lid} Seite {page}: {len(inserts)} neue Karte(n) ---")
            for it in page_plans[(lid, page)]:
                old = "" if it["id"] is None else f"(alt {it['order_index']})"
                print(f"  {it['new_order']:>3} {old:>9} {it['label']}")
        for msg in card_skips:
            print(f"[SKIP ] {msg}")

        n_cards = sum(1 for plan in page_plans.values() for it in plan if it["id"] is None)
        n_reorder = sum(1 for plan in page_plans.values() for it in plan
                        if it["id"] is not None and it["new_order"] != it["order_index"])
        print(f"\nErwartete Zeilen: UPDATE vocabulary {len(writes)}, INSERT lesson_content {n_cards}, "
              f"UPDATE lesson_content.order_index {n_reorder}")

        if not args.apply:
            print("DRY-RUN — nichts geschrieben. Mit --apply ausführen.")
            return 0
        if (skips or card_skips) and not args.allow_partial:
            print("ABBRUCH: SKIPs vorhanden — nichts geschrieben (--allow-partial erzwingt).")
            return 1

        for (vid, field), (old, new) in writes.items():
            res = db.session.execute(
                text(f"UPDATE vocabulary SET {field} = :new WHERE id = :id AND {field} = :old"),
                {"new": new, "id": vid, "old": old})
            if res.rowcount != 1:
                db.session.rollback()
                print(f"ROLLBACK: vocabulary#{vid}.{field} hat sich währenddessen geändert.")
                return 1
        from app.models import LessonContent

        for (lid, page), plan in page_plans.items():
            for it in plan:
                if it["id"] is None:
                    db.session.add(LessonContent(
                        lesson_id=lid, content_type="vocabulary", content_id=it["vocab_id"],
                        order_index=it["new_order"], page_number=page, is_optional=False,
                        generated_by_ai=True,
                        ai_generation_details={"source": "n5_luecke_2026-10-10"},
                    ))
                elif it["new_order"] != it["order_index"]:
                    db.session.execute(
                        text("UPDATE lesson_content SET order_index = :o WHERE id = :id"),
                        {"o": it["new_order"], "id": it["id"]})
        db.session.commit()
        print(f"APPLY OK: {len(writes)} Vokabel-Felder, {n_cards} neue Karten, {n_reorder} Umnummerierungen.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

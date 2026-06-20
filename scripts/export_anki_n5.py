"""Exportiert ein GRATIS JLPT-N5-Vokabel-Anki-Deck als ``.apkg``.

japanese-learning.ch ist gratis — dieses Deck ist eine grosszuegige, komplette,
teilbare Ressource (kein "Koeder") und zugleich dezente Markenpraesenz.

Quellen (zwei austauschbare Eingabe-Pfade, EINE Render-Logik):
  * DB (Standard): liest ``app.models.Vocabulary`` ueber SQLAlchemy/DATABASE_URL,
    gefiltert auf ``jlpt_level == 5`` und ``status == 'approved'``.
  * ``--from-json PATH``: Liste von Dicts — laeuft OHNE DB (Smoke-Test/Offline).

Karten-Design (Front -> Back):
  * Front: Wort (Kanji/Kana) gross + zentriert.
  * Back: Lesung (Furigana/Kana), Romaji, deutsche Bedeutung; darunter der
    Beispielsatz (JP) mit Romaji + deutscher Uebersetzung.

Determinismus / Updates:
  * deck_id, model_id und der Note-``guid`` werden STABIL aus festen Strings bzw.
    aus der Wort-Identitaet gehasht (NICHT zufaellig, NICHT datumsabhaengig).
    -> Re-Import in Anki AKTUALISIERT dieselben Karten, statt zu duplizieren —
    auch wenn sich Bedeutung/Beispielsatz aendert (guid haengt am Wort, nicht
    am Inhalt).

Aufruf:
    # Echtes Deck aus der DB (Projekt-Root, DATABASE_URL erreichbar):
    python scripts/export_anki_n5.py --out dist/jlpt_n5_vokabeln.apkg

    # Offline / Smoke-Test (KEINE DB-Verbindung):
    python scripts/export_anki_n5.py --from-json scripts/data/anki_n5_sample.json \
        --out /tmp/anki_smoke.apkg

Felder pro Eintrag (DB-Spalte bzw. JSON-Key):
    word, reading, romaji, meaning_de (Fallback: meaning),
    example_sentence_japanese, example_sentence_english ("Romaji — Deutsch").
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# --- Markenkonstanten -------------------------------------------------------
BRAND = "japanese-learning.ch"
DECK_NAME = "JLPT N5 Vokabeln (Deutsch) · " + BRAND
DECK_DESCRIPTION = (
    "JLPT-N5-Grundwortschatz mit Lesung, Romaji, deutscher Bedeutung und "
    "Beispielsatz. Gratis erstellt von " + BRAND + " — frei teilbar."
)
# Feste Seeds => stabile, deterministische IDs (kein random.randrange!).
DECK_ID_SEED = "jpl-anki-n5-vocab-deck-v1"
MODEL_ID_SEED = "jpl-anki-n5-vocab-model-v1"
GUID_NAMESPACE = "jpl-n5"

# Trenner zwischen Romaji und Uebersetzung in example_sentence_english.
# Spiegelt Vocabulary._split_example_translation (em-dash bevorzugt).
_EXAMPLE_SEPARATORS = (" — ", " – ", " - ")


def stable_id(seed: str) -> int:
    """Deterministische ID im von genanki erwarteten 31-bit-Bereich."""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return (int(digest, 16) % (1 << 30)) + (1 << 30)


def split_example_translation(raw: str | None) -> tuple[str, str]:
    """Zerlegt 'Romaji — Deutsch' in (romaji, deutsch).

    Tolerant gegenueber em-dash/en-dash/ASCII-Bindestrich. Ohne Trenner gilt der
    gesamte Inhalt als Uebersetzung (Romaji leer).
    """
    text = (raw or "").strip()
    if not text:
        return "", ""
    for sep in _EXAMPLE_SEPARATORS:
        if sep in text:
            left, right = text.split(sep, 1)
            return left.strip(), right.strip()
    return "", text


def normalize_entry(src: dict) -> dict[str, str] | None:
    """Bringt einen DB-/JSON-Eintrag auf EINE Form fuer den Karten-Builder.

    Liefert ``None``, wenn Pflichtfelder (word, reading, Bedeutung) fehlen —
    solche Eintraege werden uebersprungen.
    """
    word = (src.get("word") or "").strip()
    reading = (src.get("reading") or "").strip()
    # meaning_de bevorzugt, sonst meaning als Fallback.
    meaning = (src.get("meaning_de") or src.get("meaning") or "").strip()
    if not word or not reading or not meaning:
        return None

    romaji = (src.get("romaji") or "").strip()
    example_jp = (src.get("example_sentence_japanese") or "").strip()
    example_romaji, example_de = split_example_translation(
        src.get("example_sentence_english")
    )
    return {
        "word": word,
        "reading": reading,
        "romaji": romaji,
        "meaning": meaning,
        "example_jp": example_jp,
        "example_romaji": example_romaji,
        "example_de": example_de,
    }


def render_back(entry: dict[str, str]) -> str:
    """Baut das HTML der Rueckseite (alle Werte HTML-escaped)."""
    e = {k: html.escape(v) for k, v in entry.items()}
    parts = [f'<div class="reading">{e["reading"]}</div>']
    if e["romaji"]:
        parts.append(f'<div class="romaji">{e["romaji"]}</div>')
    parts.append(f'<div class="meaning">{e["meaning"]}</div>')

    if e["example_jp"] or e["example_de"]:
        parts.append('<hr class="sep">')
        parts.append('<div class="example">')
        if e["example_jp"]:
            parts.append(f'<div class="ex-jp">{e["example_jp"]}</div>')
        if e["example_romaji"]:
            parts.append(f'<div class="ex-romaji">{e["example_romaji"]}</div>')
        if e["example_de"]:
            parts.append(f'<div class="ex-de">{e["example_de"]}</div>')
        parts.append("</div>")
    return "\n".join(parts)


CARD_CSS = """\
.card {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans JP",
               "Meiryo", sans-serif;
  text-align: center;
  color: #1a1a1a;
  background: #faf7f2;            /* warmes Washi-Papier */
  padding: 28px 18px;
}
.word {
  font-size: 64px;
  font-weight: 700;
  line-height: 1.15;
  margin: 8px 0 4px;
}
.reading { font-size: 30px; margin-top: 6px; }
.romaji  { font-size: 20px; color: #7a6f63; margin-top: 2px; }
.meaning { font-size: 26px; font-weight: 600; margin-top: 14px; }
.sep {
  border: none;
  border-top: 1px solid #d8cfc2;
  margin: 18px auto;
  width: 70%;
}
.example { margin-top: 6px; }
.ex-jp     { font-size: 24px; line-height: 1.5; }
.ex-romaji { font-size: 17px; color: #7a6f63; margin-top: 4px; }
.ex-de     { font-size: 19px; color: #333; margin-top: 4px; }
.brand {
  margin-top: 22px;
  font-size: 12px;
  color: #b04a32;                /* 朱 shu, dezent */
  letter-spacing: 0.04em;
}
"""


def build_model():
    import genanki

    return genanki.Model(
        stable_id(MODEL_ID_SEED),
        "JPL N5 Vokabel (Front->Back)",
        fields=[{"name": "Word"}, {"name": "Back"}],
        templates=[
            {
                "name": "JP -> Deutsch",
                "qfmt": '<div class="word">{{Word}}</div>'
                        f'<div class="brand">{BRAND}</div>',
                "afmt": '<div class="word">{{Word}}</div>'
                        '<hr id="answer">{{Back}}'
                        f'<div class="brand">{BRAND}</div>',
            }
        ],
        css=CARD_CSS,
    )


def build_deck_and_package(entries: list[dict[str, str]]):
    import genanki

    model = build_model()
    deck = genanki.Deck(stable_id(DECK_ID_SEED), DECK_NAME, DECK_DESCRIPTION)
    deck.description = DECK_DESCRIPTION

    for entry in entries:
        note = genanki.Note(
            model=model,
            fields=[entry["word"], render_back(entry)],
            # Stabiler guid aus der Wort-Identitaet (NICHT aus dem Inhalt) =>
            # Re-Import aktualisiert dieselbe Karte statt zu duplizieren.
            guid=genanki.guid_for(GUID_NAMESPACE, entry["word"]),
        )
        deck.add_note(note)

    return genanki.Package(deck)


def load_from_json(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("JSON muss eine Liste von Objekten sein")
    return raw


def load_from_db(limit: int | None) -> list[dict]:
    """Liest approved N5-Vokabeln aus der DB (nur fuer den echten Export)."""
    from app import create_app
    from app.models import Vocabulary

    app = create_app()
    rows: list[dict] = []
    with app.app_context():
        query = (
            Vocabulary.query
            .filter(Vocabulary.jlpt_level == 5)
            .filter(Vocabulary.status == "approved")
            .order_by(Vocabulary.id)
        )
        if limit is not None:
            query = query.limit(limit)
        for v in query.all():
            rows.append({
                "word": v.word,
                "reading": v.reading,
                "romaji": v.romaji,
                "meaning_de": v.meaning_de,
                "meaning": v.meaning,
                "example_sentence_japanese": v.example_sentence_japanese,
                "example_sentence_english": v.example_sentence_english,
            })
    return rows


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-json", type=str, default=None,
        help="JSON-Datei (Liste von Dicts) statt DB-Quelle — laeuft OHNE DB",
    )
    parser.add_argument(
        "--out", type=str, default=str(ROOT / "dist" / "jlpt_n5_vokabeln.apkg"),
        help="Zielpfad der .apkg-Datei",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maximale Anzahl Karten (Stichprobe)",
    )
    args = parser.parse_args()

    # Eingabe laden (genau EINER der beiden Pfade).
    if args.from_json:
        json_path = Path(args.from_json)
        if not json_path.exists():
            print(f"FEHLER: JSON-Datei nicht gefunden: {json_path}")
            return 1
        raw_rows = load_from_json(json_path)
        if args.limit is not None:
            raw_rows = raw_rows[:args.limit]
        source_desc = f"JSON: {json_path}"
    else:
        raw_rows = load_from_db(args.limit)
        source_desc = "DB: Vocabulary (jlpt_level=5, status=approved)"

    # Normalisieren + filtern (ueberspringt Eintraege ohne word/reading/Bedeutung).
    entries: list[dict[str, str]] = []
    skipped = 0
    for src in raw_rows:
        norm = normalize_entry(src)
        if norm is None:
            skipped += 1
            continue
        entries.append(norm)

    print(f"=== Anki-Export — {DECK_NAME} ===")
    print(f"Quelle: {source_desc}")
    print(f"Eingelesen: {len(raw_rows)} | Gueltig: {len(entries)} | "
          f"Uebersprungen (unvollstaendig): {skipped}")

    if not entries:
        print("FEHLER: Keine gueltigen Karten — nichts geschrieben.")
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = build_deck_and_package(entries)
    package.write_to_file(str(out_path))

    print()
    print(f"OK: {len(entries)} Karten geschrieben.")
    print(f"Datei: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

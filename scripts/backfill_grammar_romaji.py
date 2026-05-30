"""Backfill Romaji auf Grammatik-Karten, deren `structure` japanische Schrift
enthaelt, aber bei denen das `romaji`-Feld leer ist.

Die Grammatik-Karten-Vorderseite (review.html) zeigt unter dem Titel die Zeile
`Grammar.romaji` als Lesehilfe (`.front-romaji`). Fehlt sie, hat die Karte keine
Romaji auf der Vorderseite. Romaji wird — wie bei den bereits gepflegten Karten
(IDs 4–23) — aus dem `structure`-Pattern erzeugt:

    N₁ は N₂ です        -> N1 wa N2 desu
    〜が 好き / 嫌い      -> 〜ga suki / kirai
    Vて ください          -> V te kudasai

Lateinische Platzhalter (N, V, S, "Ort", "Adjektiv"), `～`, `/`, Indizes (₁₂)
und Satzzeichen bleiben erhalten; nur die japanischen Anteile werden
transkribiert. Strukturen ganz ohne japanische Schrift (z.B. "Potential Form",
"counting") bekommen KEIN Romaji (nichts zu lesen) und werden uebersprungen.

Idempotent: ueberschreibt nie ein bereits vorhandenes Romaji.

CLI:
  python scripts/backfill_grammar_romaji.py                # Dry-Run (Default)
  python scripts/backfill_grammar_romaji.py --dry-run      # explizit Dry-Run
  python scripts/backfill_grammar_romaji.py --apply        # tatsaechlich schreiben
"""
from __future__ import annotations

import argparse
import re
import sys

# Hiragana, Katakana (inkl. Halbbreite), CJK Unified Ideographs
JP_REGEX = re.compile(r"[぀-ゟ゠-ヿｦ-ﾟ一-鿿]")

# Tiefgestellte Ziffern ₀–₉ -> 0–9 (matcht den Stil "N1 wa N2 desu" der
# bereits gepflegten Karten; NFKC waere zu grob — es wuerde ～ zu ~ verflachen).
_SUBSCRIPT_MAP = {0x2080 + i: str(i) for i in range(10)}

# Finale Partikel, die pykakasi sonst falsch transkribiert (ha/wo/he statt
# wa/o/e). Werden vom vorhergehenden Wort getrennt, damit die Hepburn-Norm greift.
_PARTICLE_FINALS = {"は", "を", "へ"}

_kakasi = None


def _get_kakasi():
    global _kakasi
    if _kakasi is None:
        import pykakasi

        _kakasi = pykakasi.kakasi()
    return _kakasi


def _split_final_particles(text: str) -> str:
    """Trenne ein finales は/を/へ vom Wort (nur ab Token-Laenge >= 3), damit
    pykakasi die phonetische Hepburn-Form (wa/o/e) liefert."""
    out = []
    for tok in re.split(r"(\s+)", text):
        if not tok or tok.isspace():
            out.append(tok)
            continue
        if len(tok) >= 3 and tok[-1] in _PARTICLE_FINALS and JP_REGEX.match(tok[-2]):
            out.append(tok[:-1] + " " + tok[-1])
        else:
            out.append(tok)
    return "".join(out)


def structure_to_romaji(text: str) -> str:
    """Konvertiere ein Grammatik-`structure`-Pattern zu Hepburn-Romaji.

    Gibt "" zurueck, wenn der Text keine japanische Schrift enthaelt (dann ist
    Romaji bedeutungslos). Lateinische/Platzhalter-Anteile bleiben erhalten.
    """
    if not text or not JP_REGEX.search(text):
        return ""

    kks = _get_kakasi()
    # Japanische Klammern entfernen — kakasi macht daraus ASCII () und das mischt
    # sich mit unserem Format.
    cleaned = re.sub(r"[「」『』【】]", "", text)
    cleaned = cleaned.translate(_SUBSCRIPT_MAP)
    pre = _split_final_particles(cleaned)

    parts = []
    for tok in kks.convert(pre):
        h = (tok.get("hepburn") or "").strip()
        if h:
            parts.append(h)
    out = " ".join(parts)

    # Standalone-Partikel-Korrektur (Hepburn-Norm)
    out = re.sub(r"\bha\b", "wa", out)
    out = re.sub(r"\bhe\b", "e", out)
    # Japanische Satzzeichen normalisieren
    out = out.replace("、", ", ").replace("。", ". ")
    # Whitespace vor Satzzeichen einsammeln + Mehrfach-Spaces glaetten
    out = re.sub(r"\s+([,.!?])", r"\1", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Aenderungen tatsaechlich speichern (sonst Dry-Run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur anzeigen (Default, wenn --apply fehlt)")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    from app import create_app, db  # noqa: E402  (lazy: Funktion ist DB-frei testbar)
    from app.models import Grammar  # noqa: E402

    app = create_app()
    with app.app_context():
        candidates = (
            Grammar.query
            .filter(db.or_(Grammar.romaji.is_(None), db.func.btrim(Grammar.romaji) == ""))
            .order_by(Grammar.id)
            .all()
        )
        print(f"[INFO] {len(candidates)} Karten ohne Romaji "
              f"({'APPLY' if args.apply else 'DRY-RUN'})")

        changed = 0
        skipped_no_jp = 0
        for g in candidates:
            rom = structure_to_romaji(g.structure or "")
            if not rom:
                skipped_no_jp += 1
                continue
            print(f"  id={g.id:>4} structure={g.structure!r}")
            print(f"           -> romaji={rom!r}")
            if args.apply:
                g.romaji = rom
            changed += 1

        print(f"\n[SUMMARY] gefuellt: {changed} | "
              f"uebersprungen (kein Japanisch in structure): {skipped_no_jp}")

        if args.apply and changed:
            db.session.commit()
            print("[OK] Commit gemacht.")
        elif args.apply:
            print("[OK] Keine Aenderungen noetig.")
        else:
            print("[INFO] Dry-Run — kein Commit. Mit --apply ausfuehren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

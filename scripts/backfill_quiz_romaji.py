"""Backfill Romaji on Quiz-Fragen + -Optionen die japanischen Text enthalten,
aber kein ASCII-Alphabet (= kein Romaji).

Idempotent: ueberspringt Eintraege, die bereits Romaji enthalten.

Standard-Filter: difficulty_level=1 (= JLPT N5).

CLI:
  python scripts/backfill_quiz_romaji.py --dry-run            # Nur anzeigen
  python scripts/backfill_quiz_romaji.py --lesson 162         # Nur eine Lesson
  python scripts/backfill_quiz_romaji.py --apply              # Tatsaechlich speichern
  python scripts/backfill_quiz_romaji.py --jlpt all --apply   # Alle Lessons
"""
import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db  # noqa: E402
from app.models import Lesson, LessonContent, QuizOption, QuizQuestion  # noqa: E402

# Hiragana, Katakana (inkl. Halbbreite), CJK Unified Ideographs
JP_REGEX = re.compile(r"[぀-ゟ゠-ヿｦ-ﾟ一-鿿]")
ASCII_LETTER_REGEX = re.compile(r"[A-Za-z]")


def needs_romaji(text: str) -> bool:
    """True, wenn der Text japanische Schrift enthaelt aber kein lateinisches
    Alphabet (also keinen Romaji-Anteil)."""
    if not text:
        return False
    return bool(JP_REGEX.search(text)) and not ASCII_LETTER_REGEX.search(text)


_kakasi = None

# Pre-Konversion: Trenne finale Partikel (は/を/へ) vom vorhergehenden Wort, damit
# pykakasi die phonetisch korrekte Hepburn-Form (wa/wo/e) ausgibt statt
# ha/wo/he aus dem Kana-Tabelle. Nur ab Token-Laenge >= 3, um content-Words
# wie はは, へ allein zu schonen.
_PARTICLE_FINALS = {"は", "を", "へ"}


def _split_final_particles(text: str) -> str:
    out = []
    for tok in re.split(r"(\s+)", text):
        if not tok or tok.isspace():
            out.append(tok)
            continue
        if len(tok) >= 3 and tok[-1] in _PARTICLE_FINALS:
            prev = tok[-2]
            if JP_REGEX.match(prev):
                out.append(tok[:-1] + " " + tok[-1])
                continue
        out.append(tok)
    return "".join(out)


def _get_kakasi():
    global _kakasi
    if _kakasi is None:
        import pykakasi
        _kakasi = pykakasi.kakasi()
    return _kakasi


def to_romaji(text: str) -> str:
    """Konvertiere japanischen Text zu Hepburn-Romaji.
    pykakasi liefert pro Token ein dict {'orig', 'hira', 'kana', 'hepburn'}."""
    kks = _get_kakasi()
    # Japanische Anfuehrungszeichen entfernen — kakasi konvertiert sie zu
    # ASCII `()` und das mischt sich mit unserem Wrap-Format.
    cleaned = re.sub(r"[「」『』【】\[\]]", "", text)
    pre = _split_final_particles(cleaned)
    parts = []
    for tok in kks.convert(pre):
        h = tok.get("hepburn", "").strip()
        if h:
            parts.append(h)
    out = " ".join(parts)
    # Standalone-Partikel-Korrektur (Hepburn-Norm)
    out = re.sub(r"\bha\b", "wa", out)
    out = re.sub(r"\bhe\b", "e", out)
    # Satzzeichen-Cleanup
    out = re.sub(r"\s+([,.!?])", r"\1", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    # Reine ASCII-Punktuation/Klammern aus dem kakasi-Output entfernen
    out = out.strip(" .,()[]{}「」『』")
    if out:
        out = out[0].upper() + out[1:]
    return out


def annotate(text: str) -> str:
    """Gib `text` zurueck, ergaenzt um ` (romaji)` falls noetig.
    Fallback: bei Fehler oder leerem Romaji bleibt `text` unveraendert.
    Skippt sehr kurze Kana-only Strings (1-2 Zeichen, kein Kanji) — die
    kann der Lerner sowieso lesen und das Romaji waere nur Rauschen."""
    if not needs_romaji(text):
        return text
    # Strip Anfuehrungszeichen/Whitespace fuer die Mindestlaenge-Pruefung
    core = re.sub(r"[「」『』【】\[\]\s]", "", text)
    has_kanji = bool(re.search(r"[一-鿿]", core))
    if not has_kanji and len(core) <= 2:
        return text  # zu kurz, lohnt nicht
    try:
        rom = to_romaji(text)
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] kakasi-Fehler fuer '{text[:30]}': {e}")
        return text
    if not rom or len(rom) < 2:
        return text
    return f"{text} ({rom})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lesson", type=int, default=None,
                        help="Nur diese Lesson-ID")
    parser.add_argument("--jlpt", type=str, default="5",
                        help="JLPT-Level (5/4/3/2/1) oder 'all' (Default: 5)")
    parser.add_argument("--apply", action="store_true",
                        help="Aenderungen tatsaechlich speichern (sonst: dry-run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Alias fuer fehlendes --apply")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        q = (
            db.session.query(QuizQuestion, LessonContent, Lesson)
            .join(LessonContent, QuizQuestion.lesson_content_id == LessonContent.id)
            .join(Lesson, LessonContent.lesson_id == Lesson.id)
        )
        if args.lesson:
            q = q.filter(Lesson.id == args.lesson)
        elif args.jlpt != "all":
            level = int(args.jlpt)
            difficulty_map = {5: 1, 4: 2, 3: 3, 2: 4, 1: 5}
            q = q.filter(Lesson.difficulty_level == difficulty_map.get(level, 1))

        rows = q.all()
        print(f"[INFO] {len(rows)} Fragen zu pruefen "
              f"({'DRY-RUN' if not args.apply else 'APPLY'})")

        questions_changed = 0
        options_changed = 0
        for qq, _lc, _lesson in rows:
            new_text = annotate(qq.question_text or "")
            if new_text != (qq.question_text or ""):
                print(f"  Q{qq.id}: {qq.question_text}")
                print(f"     -> {new_text}")
                if args.apply:
                    qq.question_text = new_text
                questions_changed += 1

            for opt in qq.options:
                new_opt = annotate(opt.option_text or "")
                if new_opt != (opt.option_text or ""):
                    print(f"  O{opt.id} (Q{qq.id}): {opt.option_text}")
                    print(f"          -> {new_opt}")
                    if args.apply:
                        opt.option_text = new_opt
                    options_changed += 1

        print(f"\n[SUMMARY] Fragen: {questions_changed} | Optionen: {options_changed}")

        if args.apply and (questions_changed or options_changed):
            db.session.commit()
            print("[OK] Commit gemacht.")
        elif args.apply:
            print("[OK] Keine Aenderungen noetig.")
        else:
            print("[INFO] Dry-run — kein Commit. Mit --apply ausfuehren.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

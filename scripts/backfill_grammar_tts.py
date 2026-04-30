"""Backfill `grammar.tts_example_jp` aus `example_sentences`.

Pro Eintrag wird genau EIN japanischer Satz extrahiert, der zum Audio-Button
gehoert. Akzeptiert sowohl JSON-Format ([{japanese, english, ...}]) als auch
Plain-Text-Format mit nummerierten Saetzen.

Aufruf:
    python -m scripts.backfill_grammar_tts            # nur Report (dry-run)
    python -m scripts.backfill_grammar_tts --apply    # tatsaechlich schreiben
    python -m scripts.backfill_grammar_tts --force    # auch nicht-leere ueberschreiben
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Projektroot in sys.path einhaengen, damit `app` importierbar ist.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Grammar  # noqa: E402

# Hiragana, Katakana, CJK Unified, Halfwidth Katakana
JAPANESE_RE = re.compile(r'[぀-ゟ゠-ヿ一-鿿ｦ-ﾟ]')
# JP-Satzzeichen, an denen wir Saetze trennen
SENTENCE_END_RE = re.compile(r'[。！？]')
# Romaji/Latin-only Zeile (keine japanischen Zeichen) — die wollen wir NICHT
LATIN_ONLY_RE = re.compile(r'^[A-Za-zĀ-ž\s\.\,\?\!\(\)\-—–:;\'"0-9]+$')


def is_pure_japanese_sentence(text: str) -> bool:
    """True, wenn der Text einen vollstaendigen JP-Satz darstellt: enthaelt
    japanische Zeichen, hat ein JP-Satzende und keine deutschen/englischen
    Erlaeuterungen am Ende."""
    if not text or len(text) < 4 or len(text) > 200:
        return False
    if not JAPANESE_RE.search(text):
        return False
    if not SENTENCE_END_RE.search(text):
        return False
    # Heuristik: wenn nach dem Satzende noch Latin-Zeichen kommen (z.B. "..."),
    # ist es wahrscheinlich gemischt. Wir nehmen nur den Teil bis zum ersten Ende.
    return True


def first_sentence(text: str) -> str | None:
    """Schneide bis zum ersten 。/！/？ und gib den JP-Satz inkl. Endzeichen zurueck."""
    if not text:
        return None
    m = SENTENCE_END_RE.search(text)
    if not m:
        return None
    return text[: m.end()].strip()


def extract_from_json(raw: str) -> str | None:
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, list) or not data:
        return None
    for entry in data:
        if not isinstance(entry, dict):
            continue
        jp = (entry.get('japanese') or '').strip()
        if jp and is_pure_japanese_sentence(jp):
            return first_sentence(jp)
    return None


def extract_from_plain(raw: str) -> str | None:
    """Plain-Text-Format: Erste Zeile ziehen, die japanische Zeichen + 。/！/？ hat
    und nicht offensichtlich Romaji-in-Klammern oder Uebersetzung ist."""
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Markierungen wie ①, "1.", "- " entfernen
        stripped = re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩\d]+[\.\)\s]+', '', stripped)
        stripped = re.sub(r'^[\-–—•\*]\s*', '', stripped)
        # In Klammern stehende Romaji: (Watashi wa ...) ueberspringen
        if stripped.startswith('(') and LATIN_ONLY_RE.match(stripped.strip('()')):
            continue
        # Reine Latin-Zeile (Uebersetzung) ueberspringen
        if LATIN_ONLY_RE.match(stripped):
            continue
        if is_pure_japanese_sentence(stripped):
            return first_sentence(stripped)
    return None


# Erklaerende Meta-Karten ohne natuerlichen Beispielsatz — Hand-geschriebene
# einfache N5-Saetze, die das Grammatik-Thema illustrieren.
MANUAL_OVERRIDES: dict[int, str] = {
    72: 'ごはんを食べてください。',         # Te-Form: "Bitte iss/essen Sie."
    82: '山は高いです。',                   # On/Kun: "Berge sind hoch." (kun-yomi: yama)
    83: 'まいにち漢字を書きます。',         # Strichfolge: "Jeden Tag schreibe ich Kanji."
    91: '今日は月曜日です。',               # Wochentag: "Heute ist Montag."
}


def derive_tts_sentence(grammar: Grammar) -> str | None:
    if grammar.id in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[grammar.id]
    raw = grammar.example_sentences or ''
    if not raw.strip():
        return None
    if raw.strip().startswith('['):
        result = extract_from_json(raw)
        if result:
            return result
    return extract_from_plain(raw)


def main() -> int:
    # Windows-Konsole haengt sonst beim Drucken japanischer Zeichen.
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Schreibt Aenderungen in die DB')
    parser.add_argument('--force', action='store_true', help='Auch nicht-leere Felder ueberschreiben')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        all_grammar = Grammar.query.order_by(Grammar.id).all()
        total = len(all_grammar)
        filled = 0
        skipped = 0
        gaps: list[tuple[int, str]] = []
        updates: list[tuple[int, str, str]] = []

        for g in all_grammar:
            if g.tts_example_jp and not args.force:
                skipped += 1
                continue
            sentence = derive_tts_sentence(g)
            if sentence:
                updates.append((g.id, g.title, sentence))
                if args.apply:
                    g.tts_example_jp = sentence
                filled += 1
            else:
                gaps.append((g.id, g.title))

        if args.apply:
            db.session.commit()

        print(f"=== Grammar-TTS-Backfill ({'APPLY' if args.apply else 'DRY-RUN'}) ===")
        print(f"Total: {total} | gefuellt: {filled} | bereits gesetzt (skip): {skipped} | Luecken: {len(gaps)}")
        print()
        print("Beispiele (erste 5 Updates):")
        for gid, title, sentence in updates[:5]:
            print(f"  [{gid}] {title[:50]}  ->  {sentence}")
        if gaps:
            print()
            print(f"Luecken (kein JP-Satz extrahierbar) — {len(gaps)} Eintraege:")
            for gid, title in gaps[:20]:
                print(f"  [{gid}] {title[:70]}")
            if len(gaps) > 20:
                print(f"  ... +{len(gaps) - 20} weitere")
        return 0


if __name__ == '__main__':
    sys.exit(main())

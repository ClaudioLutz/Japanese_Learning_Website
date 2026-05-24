#!/usr/bin/env python3
"""Kuratierte Nuance-/„Verwechselt-mit"-Notizen für die wichtigsten
verwechselbaren N5-Grammatikpunkte in `grammar.nuance` schreiben.

Matching über einen japanischen Titel-Teilstring (in beiden Sprach-Tracks
identisch) + Sprach-Guard auf die *deutsche* Erklärung — so erhalten nur die
deutschen Karten die deutschen Notizen, die englischen bleiben unberührt.

Aufruf (zuerst Dry-Run!):
    python -m scripts.seed_grammar_nuance            # nur Report (dry-run)
    python -m scripts.seed_grammar_nuance --apply    # tatsächlich schreiben
    python -m scripts.seed_grammar_nuance --apply --force  # auch volle überschreiben

Hinweis: setzt voraus, dass die Migration c4e1a8b6f2d9 (Spalte grammar.nuance)
bereits angewandt ist (läuft beim Deploy via `flask db upgrade`).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Erkennt eine deutsche Erklärung (grenzt den EN-Track aus).
_GERMAN_RE = re.compile(r'\b(der|die|das|wird|Partikel|Nomen|man|wenn|Satz)\b',
                        re.IGNORECASE)

# (japanischer Titel-Teilstring, Nuance-Notiz). Reihenfolge = Priorität.
# Innere Glossen bewusst mit einfachen Quotes, damit die Strings sauber bleiben.
CURATED: list[tuple[str, str]] = [
    ("これ/それ/あれ",
     "これ/それ/あれ stehen ALLEIN (これは 本です = 'Das ist ein Buch'). "
     "Nicht mit この/その/あの verwechseln, die VOR einem Nomen stehen "
     "(この 本 = 'dieses Buch'). Eselsbrücke: こ = beim Sprecher, "
     "そ = beim Hörer, あ = von beiden entfernt."),
    ("この/その/あの",
     "この/その/あの stehen immer DIREKT vor einem Nomen (あの 人 = 'jene Person'). "
     "Ohne folgendes Nomen brauchst du これ/それ/あれ (あれは 何ですか)."),
    ("N も",
     "も ersetzt は oder が und heißt 'auch'. NICHT zusätzlich zu は benutzen: "
     "falsch わたしはも, richtig わたしも. Beispiel: グプタさんも 会社員です."),
    ("は N です",
     "は markiert das THEMA (worüber gesprochen wird), nicht zwingend das Subjekt. "
     "Vergleiche mit が: bekannte/kontrastierte Information nimmt は, "
     "neue/betonte Information nimmt が. は wird hier 'wa' gesprochen, nicht 'ha'."),
    ("じゃ ありません",
     "じゃ ありません ist die GESPROCHENE, lockere Verneinung von です. "
     "In formellen oder schriftlichen Texten steht stattdessen では ありません — "
     "gleiche Bedeutung, höheres Register."),
    ("S か",
     "Die höfliche Frage endet auf か; die Wortstellung bleibt gleich. "
     "In lockerer Sprache lässt man か oft weg und hebt nur die Stimme am Satzende."),
    ("で 行きます",
     "Das で des Transportmittels (バスで = 'mit dem Bus') nicht mit dem "
     "Handlungsort-で verwechseln. Bei 'zu Fuß' steht KEIN で: 歩いて 行きます."),
    ("N の N",
     "の verbindet zwei Nomen: Besitz (わたしの 本 = 'mein Buch') oder "
     "Zugehörigkeit/Art (日本語の 本 = 'Japanisch-Buch'). "
     "Reihenfolge: Bestimmer の Hauptwort."),
]


def nuance_for(title: str | None, explanation: str | None) -> str | None:
    """Liefert die kuratierte Notiz für eine Karte — nur für deutsche Karten
    (Sprach-Guard) und nur bei Titel-Treffer. Sonst None."""
    if not _GERMAN_RE.search(explanation or ''):
        return None
    title = title or ''
    for needle, note in CURATED:
        if needle in title:
            return note
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Änderungen schreiben')
    parser.add_argument('--force', action='store_true',
                        help='auch bereits gefüllte nuance überschreiben')
    args = parser.parse_args()

    from app import create_app, db
    from app.models import Grammar

    app = create_app()
    with app.app_context():
        updated = skipped = 0
        for g in Grammar.query.order_by(Grammar.id).all():
            note = nuance_for(g.title, g.explanation)
            if not note:
                continue
            if g.nuance and not args.force:
                skipped += 1
                continue
            print(f"[{'WRITE' if args.apply else 'DRY'}] id={g.id} {g.title[:48]}")
            if args.apply:
                g.nuance = note
                updated += 1
        if args.apply:
            db.session.commit()
            print(f"\nFertig: {updated} aktualisiert, {skipped} übersprungen (bereits gefüllt).")
        else:
            print("\nDry-Run — nichts geschrieben. Mit --apply ausführen.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

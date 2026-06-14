"""Re-Render des Block-Player-Audios fuer Lektionen, die vom TTS-Text-Fix
(Romaji-nach-JP-Satzzeichen + Platzhalter-Tilde, 2026-06-15) betroffen sind.

Hintergrund: ``app/services/tts_text.py`` wurde gefixt, sodass (a) Romaji-
Klammerausdruecke auch nach japanischen Satzzeichen (``。、！？``) gestrippt
werden und (b) die Platzhalter-Tilde (``~ 〜 ～``) entfernt wird. Bereits
gerenderte WAVs tragen den Bug aber weiter — sie muessen neu erzeugt werden.

Nur der BLOCK-PLAYER ist betroffen: nur dieser Pfad splittet Text in DE/JP-
Segmente und liess die deutsche Stimme Romaji/Tilde mitlesen. Inline-Klick-Audio
ist JP-only, der Dialog-Slideshow rendert aus sauberen Einzelfeldern.

Betroffen ist ein (published) text-Block, wenn nach ``strip_markdown``:
  - eine Tilde uebrig bleibt (``~ 〜 ～`` — ``~~strike~~`` zaehlt NICHT, da von
    strip_markdown entfernt), ODER
  - ein Klammerausdruck mit Latein direkt nach einem JP-Satzzeichen steht
    (``…ますか。 (Risa-san, …)``).

Dialog-Bloecke ueberspringt ``gen_text_audio.py`` ohnehin — sie werden hier
zwar als betroffen gelistet sein koennen, erzeugen aber kein Block-Audio.

Usage:
    python scripts/rerender_affected_block_audio.py            # DRY-RUN (nur Liste)
    python scripts/rerender_affected_block_audio.py --apply    # rendert neu (--force)

Auf hp-ubuntu gegen die Prod-DB ausfuehren (``.env`` zeigt im Container auf den
Service-Host ``db``; vom Host aus DATABASE_URL auf localhost:5432 setzen).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

from app import create_app, db  # noqa: E402
from app.models import Lesson, LessonContent  # noqa: E402
from app.services.tts_text import strip_markdown  # noqa: E402

GEN_SCRIPT = (
    PROJECT_ROOT / ".claude" / "skills" / "generate-lesson" / "scripts" / "gen_text_audio.py"
)

# Latein-Klammerausdruck direkt nach einem japanischen Satzzeichen/Trenner.
_ROMAJI_AFTER_PUNCT = re.compile(r"[。、，！？…‥・][\s]*\([^)]*[A-Za-z]")
_TILDE_CHARS = ("~", "〜", "～")  # ~  〜  ～


def block_is_affected(content_text: str) -> str | None:
    """Gibt einen Grund-String zurueck, wenn der Block betroffen ist, sonst None."""
    stripped = strip_markdown(content_text or "")
    reasons = []
    if any(t in stripped for t in _TILDE_CHARS):
        reasons.append("tilde")
    if _ROMAJI_AFTER_PUNCT.search(stripped):
        reasons.append("romaji-nach-satzzeichen")
    return "+".join(reasons) if reasons else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Tatsaechlich neu rendern (sonst nur DRY-RUN-Liste).",
    )
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        lessons = (
            db.session.query(Lesson)
            .filter_by(is_published=True)
            .order_by(Lesson.id)
            .all()
        )

        affected: list[tuple[int, str, list[str]]] = []
        for lesson in lessons:
            blocks = (
                db.session.query(LessonContent)
                .filter_by(lesson_id=lesson.id, content_type="text")
                .all()
            )
            reasons: set[str] = set()
            for lc in blocks:
                r = block_is_affected(lc.content_text or "")
                if r:
                    reasons.update(r.split("+"))
            if reasons:
                affected.append((lesson.id, lesson.title, sorted(reasons)))

        print(f"\n=== {len(affected)} betroffene published Lektionen ===\n")
        for lid, title, reasons in affected:
            print(f"  Lesson {lid}: {title}  [{', '.join(reasons)}]")

        if not args.apply:
            print(
                "\n(DRY-RUN — nichts gerendert. Mit --apply tatsaechlich neu rendern.)"
            )
            return 0

        print(f"\n=== Rendere {len(affected)} Lektionen neu (--force) ===\n")
        failures: list[int] = []
        for i, (lid, title, _reasons) in enumerate(affected, start=1):
            print(f"\n[{i}/{len(affected)}] === Lesson {lid}: {title} ===")
            try:
                result = subprocess.run(
                    [sys.executable, str(GEN_SCRIPT), str(lid), "--force"],
                    cwd=str(PROJECT_ROOT),
                    timeout=1800,  # 30 min hart-cap pro Lesson
                )
                if result.returncode != 0:
                    print(f"  [FEHLER] gen_text_audio Exit {result.returncode}")
                    failures.append(lid)
            except subprocess.TimeoutExpired:
                print(f"  [TIMEOUT] Lesson {lid} nach 30 min abgebrochen")
                failures.append(lid)
            except Exception as e:  # noqa: BLE001
                print(f"  [EXC] {e}")
                failures.append(lid)

        print(f"\n=== Fertig. {len(affected) - len(failures)} ok, {len(failures)} Fehler ===")
        if failures:
            print(f"    Fehlgeschlagen: {failures}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

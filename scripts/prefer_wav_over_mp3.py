"""Korrigiert augmented_html-URLs: bevorzugt <hash>.wav ueber <hash>.mp3.

Hintergrund: durch Gemini-Quota-Hits wurden viele Audios als Chirp-MP3-Fallback
generiert, aber dieselben Hashes haben oft auch eine WAV aus frueheren
Laeufen. Dieses Skript scannt alle augmented_html und ersetzt .mp3-URLs durch
.wav-URLs, wenn die WAV-Datei existiert.

ACHTUNG: .wav heisst NICHT Gemini. Seit 29.09.2026 schreibt auch der
Chirp-Fallback WAV (LINEAR16, 24 kHz) unter demselben Hash-Namen. Welche Engine
eine WAV erzeugt hat, steht nur im Engine-Manifest
``inline_audio/_engines.json`` (fehlender Eintrag = unbekannt). Das Skript
uebernimmt die Engine aus dem Manifest ins ``data-audio-engine``-Attribut und
meldet die Verteilung; Chirp-WAVs hebt ``pregenerate_inline_audio.py
--upgrade-chirp`` auf Gemini.

Bleibt fuer den Altbestand: nach ``pregenerate_inline_audio.py <id>
--replace-mp3`` stellt es die uebrigen LessonContents mit gleichem Text
(gleicher Hash) ebenfalls auf .wav um.
"""
from __future__ import annotations
import os
import sys
import re
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")

from bs4 import BeautifulSoup  # noqa: E402
from sqlalchemy.orm.attributes import flag_modified  # noqa: E402
from app import create_app, db  # noqa: E402
from app.models import LessonContent  # noqa: E402
from app.services.audio_engine_manifest import (  # noqa: E402
    KNOWN_ENGINES,
    engine_for,
    load_manifest,
)

AUDIO_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "inline_audio"

# Findet z.B. /static/uploads/lessons/inline_audio/<hash>.mp3
URL_RE = re.compile(r'(/static/uploads/lessons/inline_audio/([a-f0-9]+))\.mp3$')


def switch_html(html: str, audio_dir: Path, manifest: dict[str, str]) -> tuple[str, Counter]:
    """Stellt .mp3-Verweise mit vorhandener .wav um. Gibt (html, Engine-Zaehler)."""
    soup = BeautifulSoup(html, "html.parser")
    engines: Counter = Counter()
    for el in soup.find_all(attrs={"data-audio-url": True}):
        match = URL_RE.match(el["data-audio-url"])
        if not match or not (audio_dir / f"{match.group(2)}.wav").exists():
            continue
        engine = engine_for(manifest, match.group(2))
        el["data-audio-url"] = f"{match.group(1)}.wav"
        if engine in KNOWN_ENGINES:
            el["data-audio-engine"] = engine
        elif el.has_attr("data-audio-engine"):
            del el["data-audio-engine"]  # MP3-Engine gilt nicht fuer die WAV
        engines[engine] += 1
    if not engines:
        return html, engines
    return str(soup), engines


def main():
    app = create_app()
    with app.app_context():
        rows = (
            db.session.query(LessonContent)
            .filter(LessonContent.content_type == "text")
            .all()
        )
        manifest = load_manifest(AUDIO_DIR)

        changed_lcs = 0
        engines_total: Counter = Counter()
        for lc in rows:
            details = lc.ai_generation_details or {}
            html = details.get("augmented_html")
            if not html or ".mp3" not in html:
                continue

            new_html, engines = switch_html(html, AUDIO_DIR, manifest)
            if engines:
                details["augmented_html"] = new_html
                lc.ai_generation_details = details
                # JSONB-Mutation explizit markieren, sonst commit'd SQLAlchemy nichts
                flag_modified(lc, "ai_generation_details")
                changed_lcs += 1
                engines_total += engines

        db.session.commit()
        print(f"=== {changed_lcs} LessonContents aktualisiert, "
              f"{sum(engines_total.values())} URLs auf .wav umgestellt "
              f"(Engines laut Manifest: {dict(engines_total)}) ===")


if __name__ == "__main__":
    main()

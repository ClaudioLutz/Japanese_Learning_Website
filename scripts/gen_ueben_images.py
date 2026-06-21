"""Banner-Bilder fuer den Uebungs-Hub (/ueben) via Gemini 2.5 Flash Image (Nano Banana).

Generiert drei kohaerente, themenbezogene 16:9-Banner als WebP:
  app/static/img/ueben/wiederholen.webp   (SRS / Wiederholen)
  app/static/img/ueben/kana.webp          (Kana ueben)
  app/static/img/ueben/pruefen.webp       (Pruefen / Examen)

UI-Chrome -> liegt in app/static/img/ (git-getrackt, deployt mit dem Code),
NICHT im uploads-Volume. Text-/personenfrei (Projektregel). ~$0.039/Bild.

Usage: python scripts/gen_ueben_images.py [--force]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from nano_banana import generate_nano_banana_image_bytes  # noqa: E402

OUT_DIR = PROJECT_ROOT / "app" / "static" / "img" / "ueben"

STYLE = (
    "Modern premium e-learning banner illustration, warm and calm, Japanese-inspired. "
    "Soft flat shapes with gentle gradients and a subtle paper grain. Cohesive palette: "
    "warm washi cream background (#F5F0E8), deep indigo-navy (#1F2A44), muted sage and "
    "soft ochre, with ONE warm vermillion accent (#EB6101). Soft long shadows, generous "
    "negative space, balanced centered composition, tasteful and uncluttered."
)

RULES = (
    " STRICT RULES: absolutely no text of any kind (no letters, kanji, kana, numbers, "
    "signs, labels, watermarks, calligraphy glyphs, artist seals, hanko stamps). No "
    "people, no human figures, no faces, no hands. Pure object/scenic illustration only. "
    "All paper, cards and surfaces are completely blank with no markings."
)

JOBS = {
    "wiederholen": (
        "Subject: a neat fanned stack of plain blank study flash-cards gently lifting into "
        "a soft circular orbit of small dots and light motion arcs, evoking spaced repetition "
        "and memory returning in cycles. Warm, focused, encouraging."
    ),
    "kana": (
        "Subject: a traditional Japanese calligraphy brush resting on a small brush rest next "
        "to a round dish of vermillion ink, with a few playful loose ink droplets and soft "
        "abstract brush swooshes that do NOT form any character, plus a couple of plain blank "
        "rounded game tiles. Light, playful, game-like."
    ),
    "pruefen": (
        "Subject: a clean flat-lay study desk with a single wooden pencil, a plain blank sheet "
        "of paper, and a small rounded vermillion badge bearing a simple white check mark shape. "
        "Calm, focused exam-preparation mood."
    ),
}


def to_webp(png_bytes: bytes) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=85, method=6)
    return buf.getvalue()


def load_api_key() -> str:
    for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env gefunden")


def main() -> None:
    key = load_api_key()
    force = "--force" in sys.argv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fails = 0
    for name, motif in JOBS.items():
        out = OUT_DIR / f"{name}.webp"
        if out.exists() and not force:
            print(f"SKIP {out.name} (existiert)", flush=True)
            continue
        prompt = f"{STYLE} {motif}{RULES}"
        try:
            webp = to_webp(
                generate_nano_banana_image_bytes(prompt, key, aspect_ratio="16:9")
            )
            out.write_bytes(webp)
            print(f"OK   {out.name} ({len(webp) // 1024} KB)", flush=True)
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"FAIL {out.name}: {e}", flush=True)
    print(f"FERTIG — {len(JOBS) - fails} OK, {fails} FAIL", flush=True)


if __name__ == "__main__":
    main()

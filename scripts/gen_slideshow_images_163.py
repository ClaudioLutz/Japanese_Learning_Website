"""Slideshow-Bilder Lesson 163 neu: personenfreie Szenen pro Dialogzeile.

Ersetzt die alten Tanaka/Lisa-Charakterbilder (inkonsistent) durch
stimmige Szenen-Aquarelle — EIN Stil fuer die ganze Konversation,
pro Zeile ein Motiv, das den Inhalt der Zeile spiegelt.

Output: app/static/uploads/lessons/dialog_slideshow/lesson_163/line_0N_v2.webp
Usage: python scripts/gen_slideshow_images_163.py [--force]
"""
from __future__ import annotations

import base64
import io
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "dialog_slideshow" / "lesson_163"

STYLE = (
    "Soft atmospheric Japanese watercolor illustration on warm washi paper, "
    "gentle painterly washes, consistent palette of soft blues, warm creams and "
    "spring pastels, tranquil morning mood, same artistic hand across a series. "
)
RULES = (
    "STRICT RULES: absolutely no text of any kind (no letters, kanji, kana, "
    "numbers, signs, labels, watermarks, artist seals, hanko stamps) and no "
    "people, no human figures, no faces, no hands. Pure scenic imagery, "
    "wide 16:9 composition."
)

# Szene pro Dialogzeile (Wetter-Smalltalk vor dem Sprachkurs)
SCENES: dict[int, str] = {
    1: "the entrance street of a small Japanese language school on a bright clear morning, deep blue sky, crisp sunlight, sparkling clean air after the night",  # ii o-tenki desu ne
    2: "a sun-warmed classroom windowsill with a steaming teacup and a small potted plant, warm golden light pooling on the wood",  # kyou wa atatakai
    3: "cold blue scene: delicate frost crystals on a window pane, a bare tree shivering in pale winter mist outside",  # kinou wa samukatta
    4: "an open sky in transition seen above rooftops — half brooding grey clouds, half clearing blue, a weather vane silhouette turning",  # ashita no tenki wa dou
    5: "gentle rain on the school entrance: rain chain streaming, puddles with soft ripples, blue-grey watercolor washes",  # ashita wa ame
    6: "a plum branch with the very first pink buds opening, last patches of melting snow below, promise of spring",  # haru ga kimasu ne
    7: "full cherry blossoms framing a sunlit path, petals drifting in warm golden-pink morning light",  # haru wa suki na kisetsu
}


def load_api_key() -> str:
    for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env gefunden")


def generate(prompt: str, key: str) -> bytes:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
        },
    }).encode()
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-image:generateContent?key={key}",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError(f"Keine Bilddaten: {json.dumps(data)[:300]}")


def to_webp(png_bytes: bytes) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=85)
    return buf.getvalue()


def main() -> None:
    key = load_api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for n, scene in SCENES.items():
        out = OUT_DIR / f"line_{n:02d}_v2.webp"
        if out.exists() and "--force" not in sys.argv:
            print(f"line {n}: existiert, skip")
            continue
        print(f"line {n}: generiere ...", flush=True)
        webp = to_webp(generate(STYLE + scene + ". " + RULES, key))
        out.write_bytes(webp)
        print(f"line {n}: OK ({len(webp) // 1024} KB)")


if __name__ == "__main__":
    main()

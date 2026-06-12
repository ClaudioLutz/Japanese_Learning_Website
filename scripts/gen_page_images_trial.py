"""Probelauf Lektionsbilder: 7 Seitenbilder fuer Lesson 163 (Wetter & Jahreszeiten).

Claude verfasst die Prompts (siehe PROMPTS), Gemini 2.5 Flash Image rendert.
Output: app/static/uploads/lessons/page_images/lesson_163/page_<n>.webp

Usage: python scripts/gen_page_images_trial.py
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LESSON_ID = 163
OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "page_images" / f"lesson_{LESSON_ID}"

NO_TEXT_NO_PEOPLE = (
    "STRICT RULES: absolutely no text of any kind (no letters, kanji, kana, numbers, "
    "signs, labels, watermarks) and no people, no human figures, no faces, no hands. "
    "Pure scenic/object imagery only. Wide 16:9 composition with calm negative space."
)

# Pro Seite: eigenes Motiv UND eigener Kunststil — bewusst komplett unterschiedlich.
PROMPTS: dict[int, str] = {
    1: (  # Einfuehrung — Wetter als Smalltalk-Thema
        "Traditional Japanese sumi-e ink wash painting on cream washi paper: view through "
        "a half-open wooden engawa veranda onto a rainy garden, a single oil-paper umbrella "
        "leaning against the post, rain chain (kusari-doi) with falling water drops, distant "
        "mist over stones. Sparse brush strokes, one subtle vermillion red accent on the "
        "umbrella. " + NO_TEXT_NO_PEOPLE
    ),
    2: (  # Vokabeln 1 — Wetter und Himmel (Regen, Schnee, sonnig, bewoelkt)
        "Ukiyo-e woodblock print in the style of Hiroshige: the same small mountain village "
        "landscape shown as a four-panel folding screen (byobu), each panel a different "
        "weather — heavy slanted rain, quiet falling snow, bright clear sun, low grey clouds. "
        "Flat color planes, visible woodgrain texture, indigo and ochre palette. "
        + NO_TEXT_NO_PEOPLE
    ),
    3: (  # Vokabeln 2 — Jahreszeiten und Temperatur
        "Chigiri-e torn-paper collage artwork: one large solitary tree whose canopy blends "
        "through the four seasons from left to right — pink cherry blossoms, lush summer "
        "green, fiery autumn maple red, bare snow-covered branches. Handmade textured washi "
        "paper layers, soft fiber edges, warm paper background. " + NO_TEXT_NO_PEOPLE
    ),
    4: (  # Grammatik — i-Adjektive (heiss/kalt-Kontrast)
        "Shin-hanga style Japanese print with dramatic temperature contrast: a steaming "
        "outdoor onsen hot spring pool glowing warm orange at dusk, surrounded by deep blue "
        "snow drifts and ice-covered pine branches, steam rising into cold air, snow "
        "monkeys absent, lantern light reflecting on water. " + NO_TEXT_NO_PEOPLE
    ),
    5: (  # Dialog — Smalltalk vor dem Sprachkurs
        "Soft atmospheric watercolor illustration: the entrance of a small Japanese language "
        "school building on a drizzly morning — two closed wet umbrellas leaning together "
        "against the doorway, two pairs of shoes on the genkan step, warm light from inside, "
        "gentle rain puddles mirroring the sky. The scene implies a friendly conversation "
        "without showing anyone. " + NO_TEXT_NO_PEOPLE
    ),
    6: (  # Uebung — Quiz
        "Playful gouache painting, bright and encouraging: a single white teru-teru-bozu "
        "weather charm doll hanging by a window, outside the glass the sky is half dramatic "
        "rain clouds and half breaking sunshine with a faint rainbow, raindrops on the "
        "window pane catching light. Cheerful, slightly whimsical children's book style. "
        + NO_TEXT_NO_PEOPLE
    ),
    7: (  # Zusammenfassung & Ausblick
        "Minimalist modern Japanese poster art, flat design with grain texture: a wide "
        "serene landscape after rain — Mount Fuji silhouette at golden dusk, a full rainbow "
        "arcing across a clearing sky, small torii gate by a lake reflecting the light, "
        "restrained palette of dusk purple, gold and one vermillion accent. "
        + NO_TEXT_NO_PEOPLE
    ),
}


def load_api_key() -> str:
    env_path = PROJECT_ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
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
    raise RuntimeError(f"Keine Bilddaten in Antwort: {json.dumps(data)[:300]}")


def to_webp(png_bytes: bytes) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=85)
    return buf.getvalue()


def main() -> None:
    key = load_api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for page, prompt in PROMPTS.items():
        out = OUT_DIR / f"page_{page}.webp"
        if out.exists() and "--force" not in sys.argv:
            print(f"page {page}: existiert, skip")
            continue
        print(f"page {page}: generiere ...", flush=True)
        png = generate(prompt, key)
        webp = to_webp(png)
        out.write_bytes(webp)
        print(f"page {page}: OK ({len(webp) // 1024} KB → {out.name})")


if __name__ == "__main__":
    main()

"""Generiert das OpenGraph-/Social-Share-Bild (1200x630 PNG) fuer japanese-learning.ch.

Output: app/static/images/og-image.png  (versioniert, wie favicon.png)

Vorgehen (B-7 aus docs/quick-wins-plan.md):
- OpenAI Images erzeugt NUR die Bildflaeche im Marken-Look (washi-Papier, Sumi-Tusche,
  ein einzelner Vermillion-/朱-Akzent) - bewusst OHNE Text, da AI-Text unzuverlaessig ist.
- Pillow schneidet auf 1200x630 und legt scharfen, korrekten deutschen Marken-Text + 朱-Akzent darueber.

Bilderzeugung via OpenAI Images ist laut CLAUDE.md ausdruecklich erlaubt (Ausnahme fuer Bilder).
Brand-Referenz: Washi-Papier, Sumi-Tinte, ein heisses Vermillion (朱) als einziger Akzent, deutsche UI.

Aufruf:  venv/Scripts/python.exe scripts/generate_og_image.py
"""
from __future__ import annotations

import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

from openai import OpenAI  # noqa: E402

W, H = 1200, 630
OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "images" / "og-image.png"

# Markenfarben (aus app/static/css/custom.css)
WASHI = (250, 247, 242)      # Papier-Hintergrund
SUMI = (38, 34, 30)          # Tusche / Haupttext
SUMI_SOFT = (104, 96, 86)    # gedaempfter Text
SHU = (235, 97, 1)           # 朱 Vermillion-Akzent (--shu #EB6101)

PROMPT = (
    "A refined, minimalist Japanese washi-paper background illustration for a brand social card. "
    "Warm off-white handmade paper texture (#FAF7F2) with soft subtle fibers. "
    "On the RIGHT side: a single elegant sumi-ink brush stroke and a faint distant Mount Fuji silhouette, "
    "plus one small vermillion (朱) red circular hanko seal as the only saturated color accent. "
    "Lots of calm empty negative space on the LEFT half (text will be added later). "
    "Serene, premium, editorial, authentic Japanese aesthetic, flat soft lighting. "
    "Absolutely NO text, NO letters, NO words, NO numbers anywhere in the image."
)


def _font(path: str, size: int, *fallbacks: str) -> ImageFont.FreeTypeFont:
    for p in (path, *fallbacks):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def generate_background() -> Image.Image:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    attempts = (
        ("gpt-image-1-mini", "1536x1024"),
        ("gpt-image-1", "1536x1024"),
        ("dall-e-3", "1792x1024"),
    )
    for model, size in attempts:
        try:
            print(f"-> Bildflaeche generieren mit {model} ({size}) ...")
            kwargs: dict = dict(model=model, prompt=PROMPT, size=size, n=1)
            if model == "dall-e-3":
                kwargs["response_format"] = "b64_json"
            resp = client.images.generate(**kwargs)
            b64 = resp.data[0].b64_json
            img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
            print(f"   OK: {img.size}")
            return img
        except Exception as e:  # noqa: BLE001
            print(f"   {model} fehlgeschlagen: {e}")
    raise SystemExit("Keine Bildgenerierung moeglich (alle Modelle fehlgeschlagen).")


def cover_resize(img: Image.Image, w: int, h: int) -> Image.Image:
    """Skaliert 'cover' auf w x h und schneidet mittig."""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_w, new_h = round(h * src_ratio), h
    else:
        new_w, new_h = w, round(w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left, top = (new_w - w) // 2, (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def add_left_scrim(img: Image.Image) -> Image.Image:
    """Weicher washi-Verlauf von links (deckend) zur Mitte (transparent) fuer Textlesbarkeit."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fade_end = 760
    for x in range(fade_end):
        alpha = int(232 * (1 - x / fade_end))
        draw.line([(x, 0), (x, H)], fill=(*WASHI, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_text(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img)
    x = 72
    f_eyebrow = _font("C:/Windows/Fonts/arialbd.ttf", 30, "C:/Windows/Fonts/segoeuib.ttf")
    f_head = _font("C:/Windows/Fonts/georgiab.ttf", 84, "C:/Windows/Fonts/segoeuib.ttf")
    f_sub = _font("C:/Windows/Fonts/georgia.ttf", 40, "C:/Windows/Fonts/arial.ttf")
    f_foot = _font("C:/Windows/Fonts/arialbd.ttf", 30, "C:/Windows/Fonts/arial.ttf")

    draw.text((x, 96), "JLPT N5  ·  AUF DEUTSCH", font=f_eyebrow, fill=SHU)
    draw.rectangle([x, 150, x + 84, 158], fill=SHU)  # 朱-Akzentbalken
    draw.text((x, 186), "Japanisch lernen,", font=f_head, fill=SUMI)
    draw.text((x, 292), "Schritt für Schritt.", font=f_head, fill=SUMI)
    draw.text((x, 420), "Auf Deutsch erklärt. In der Schweiz gemacht.", font=f_sub, fill=SUMI_SOFT)
    draw.text((x, 540), "japanese-learning.ch", font=f_foot, fill=SHU)
    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bg = generate_background()
    bg = cover_resize(bg, W, H)
    bg = add_left_scrim(bg)
    bg = draw_text(bg)
    bg.save(OUT, "PNG", optimize=True)
    print(f"\nGespeichert: {OUT}  ({bg.size[0]}x{bg.size[1]})  {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()

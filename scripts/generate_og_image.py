"""Generiert das OpenGraph-Share-Bild (1200x630 PNG) fuer japanese-learning.ch.

Output: app/static/images/og-image.png

Aufruf: python scripts/generate_og_image.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 630
OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "images" / "og-image.png"

JP_FONT = "C:/Windows/Fonts/YuGothB.ttc"
DE_FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
DE_FONT = "C:/Windows/Fonts/arial.ttf"


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def gradient(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        col = (lerp(top[0], bottom[0], t), lerp(top[1], bottom[1], t), lerp(top[2], bottom[2], t))
        for x in range(w):
            px[x, y] = col
    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    img = gradient(W, H, (79, 70, 229), (37, 99, 235))
    draw = ImageDraw.Draw(img, "RGBA")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for r in range(700, 0, -20):
        a = max(0, int(40 - (700 - r) / 700 * 40))
        odraw.ellipse((W - r // 2 - 100, -r // 2 + 50, W - r // 2 - 100 + r, -r // 2 + 50 + r), fill=(255, 255, 255, a))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    draw = ImageDraw.Draw(img)

    f_jp = ImageFont.truetype(JP_FONT, 220)
    f_de_big = ImageFont.truetype(DE_FONT_BOLD, 76)
    f_de_sub = ImageFont.truetype(DE_FONT, 36)
    f_url = ImageFont.truetype(DE_FONT_BOLD, 32)

    jp_text = "日本語"
    bbox = draw.textbbox((0, 0), jp_text, font=f_jp)
    jw, jh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - jw) // 2 - bbox[0], 90 - bbox[1]), jp_text, font=f_jp, fill=(255, 255, 255, 255))

    de = "Japanisch lernen"
    bbox = draw.textbbox((0, 0), de, font=f_de_big)
    dw = bbox[2] - bbox[0]
    draw.text(((W - dw) // 2 - bbox[0], 360 - bbox[1]), de, font=f_de_big, fill=(255, 255, 255))

    sub = "JLPT-Lernpfad für deutschsprachige Anfänger"
    bbox = draw.textbbox((0, 0), sub, font=f_de_sub)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2 - bbox[0], 460 - bbox[1]), sub, font=f_de_sub, fill=(220, 230, 255))

    url = "japanese-learning.ch"
    bbox = draw.textbbox((0, 0), url, font=f_url)
    uw = bbox[2] - bbox[0]
    pad_x, pad_y = 28, 14
    bx, by = (W - uw) // 2 - pad_x, 540
    draw.rounded_rectangle(
        (bx, by, bx + uw + 2 * pad_x, by + 32 + 2 * pad_y),
        radius=22,
        fill=(255, 255, 255, 230),
    )
    draw.text((bx + pad_x - bbox[0], by + pad_y - bbox[1]), url, font=f_url, fill=(37, 99, 235))

    img.save(OUT, "PNG", optimize=True)
    print(f"OG image written: {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

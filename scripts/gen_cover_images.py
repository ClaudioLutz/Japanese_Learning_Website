"""Lektions-Cover (thumbnail_url) via Gemini 2.5 Flash Image rendern.

Liest scripts/data/cover_image_prompts.json (einheitlicher Hausstil + ein
Motiv pro Lektion, von Claude verfasst) und generiert:
  app/static/uploads/lessons/cover_images/cover_<lesson_id>.webp

Einheitlicher Stil ueber alle Cover (Katalog-Grid soll ruhig wirken), nur das
Motiv wechselt. Personen-/textfrei, keine Hanko-Siegel.

Idempotent (bestehende Dateien werden uebersprungen), 1 Retry pro Bild,
Safety-Blocks werden geloggt und uebersprungen. 4 parallele Worker.

Usage: python scripts/gen_cover_images.py [--limit N] [--lesson ID] [--force]
"""
from __future__ import annotations

import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = PROJECT_ROOT / "scripts" / "data" / "cover_image_prompts.json"
OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "cover_images"

RULES = (
    " STRICT RULES: absolutely no text of any kind (no letters, kanji, kana, "
    "numbers, signs, labels, watermarks, calligraphy glyphs, artist seals, "
    "hanko stamps, red seal marks). No people, no human figures, no faces, no "
    "hands. Pure object/scenic imagery only. All surfaces are completely "
    "blank: clock faces show no numerals, telephone dials are plain, papers, "
    "cards, books, packaging and signs carry no markings at all. Not a "
    "woodblock reproduction — no signature, no red hanko seal anywhere."
)


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
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError(f"keine Bilddaten (safety-block?): {json.dumps(data)[:200]}")


def to_webp(png_bytes: bytes) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=85)
    return buf.getvalue()


def build_jobs(data: dict, only_lesson: int | None, force: bool) -> list[tuple[Path, str]]:
    style = data["style"]
    jobs: list[tuple[Path, str]] = []
    for c in data["covers"]:
        lid = c["lesson_id"]
        if only_lesson and lid != only_lesson:
            continue
        out = OUT_DIR / f"cover_{lid}.webp"
        if out.exists() and not force:
            continue
        prompt = f"{style} Subject: {c['motif']}.{RULES}"
        jobs.append((out, prompt))
    return jobs


def render(job: tuple[Path, str], key: str) -> str:
    out, prompt = job
    for attempt in (1, 2):
        try:
            webp = to_webp(generate(prompt, key))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(webp)
            return f"OK   {out.name} ({len(webp) // 1024} KB)"
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as e:
            if attempt == 2:
                return f"FAIL {out.name}: {e}"
            time.sleep(5)
    return f"FAIL {out.name}: unreachable"


def main() -> None:
    key = load_api_key()
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    only_lesson = None
    force = "--force" in sys.argv
    if "--lesson" in sys.argv:
        only_lesson = int(sys.argv[sys.argv.index("--lesson") + 1])
    jobs = build_jobs(data, only_lesson, force)
    if "--limit" in sys.argv:
        jobs = jobs[: int(sys.argv[sys.argv.index("--limit") + 1])]
    print(f"{len(jobs)} Cover zu generieren", flush=True)

    fails = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(render, j, key): j for j in jobs}
        for i, fut in enumerate(as_completed(futures), 1):
            line = fut.result()
            if line.startswith("FAIL"):
                fails += 1
            print(f"[{i}/{len(jobs)}] {line}", flush=True)
    print(f"FERTIG — {len(jobs) - fails} OK, {fails} FAIL", flush=True)


if __name__ == "__main__":
    main()

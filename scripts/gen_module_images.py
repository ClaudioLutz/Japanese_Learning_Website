"""Modul-Banner (16:9) via Gemini 2.5 Flash Image (Nano Banana) rendern.

Liest scripts/data/module_image_prompts.json (froehlicher, bunter Hausstil +
ein Motiv pro Modul) und generiert:
  app/static/uploads/modules/module_<slug>.webp

User-Direktive 2026-06-16: FROEHLICHE, BUNTE Farben — bewusst NICHT der
gedaempfte Washi/Sepia-Stil der Lektionsbilder. Text-/personenfrei.

Idempotent (bestehende Dateien werden uebersprungen), 1 Retry pro Bild,
Safety-Blocks werden geloggt und uebersprungen. 4 parallele Worker.

Usage: python scripts/gen_module_images.py [--limit N] [--slug n5-hiragana] [--force]
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
PROMPTS_FILE = PROJECT_ROOT / "scripts" / "data" / "module_image_prompts.json"
OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "modules"

RULES = (
    " STRICT RULES: absolutely no text of any kind (no letters, kanji, kana, "
    "numbers, signs, labels, watermarks, calligraphy glyphs, artist seals, "
    "hanko stamps). No people, no human figures, no faces, no hands. "
    "Pure object/scenic illustration only. All surfaces are completely blank: "
    "clock faces show no numerals, calendar pages, papers, books and signs "
    "carry no markings at all."
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


def build_jobs(data: dict, only_slug: str | None, force: bool) -> list[tuple[Path, str]]:
    style = data["style"]
    jobs: list[tuple[Path, str]] = []
    for m in data["modules"]:
        slug = m["slug"]
        if only_slug and slug != only_slug:
            continue
        out = OUT_DIR / f"module_{slug}.webp"
        if out.exists() and not force:
            continue
        prompt = f"{style} Subject: {m['motif']}.{RULES}"
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
    only_slug = None
    force = "--force" in sys.argv
    if "--slug" in sys.argv:
        only_slug = sys.argv[sys.argv.index("--slug") + 1]
    jobs = build_jobs(data, only_slug, force)
    if "--limit" in sys.argv:
        jobs = jobs[: int(sys.argv[sys.argv.index("--limit") + 1])]
    print(f"{len(jobs)} Modul-Banner zu generieren", flush=True)

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

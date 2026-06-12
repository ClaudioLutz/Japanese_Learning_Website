"""Voll-Rollout Lektionsbilder: rendert Claude-verfasste Prompts via Gemini.

Liest scripts/data/page_image_prompts.json (von Claude per Workflow-Fan-out
verfasst, eine Prompt-Welt pro Lektion) und generiert:
  - Seitenbilder  → app/static/uploads/lessons/page_images/lesson_<id>/page_<n>.webp
  - Slideshow     → app/static/uploads/lessons/dialog_slideshow/lesson_<id>/line_<nn>_v2.webp

Idempotent (bestehende Dateien werden uebersprungen), 1 Retry pro Bild,
Safety-Blocks werden geloggt und uebersprungen. 4 parallele Worker.

Usage: python scripts/generate_lesson_images.py [--limit N] [--lesson ID]
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
PROMPTS_FILE = PROJECT_ROOT / "scripts" / "data" / "page_image_prompts.json"
UPLOADS = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons"

RULES = (
    " STRICT RULES: absolutely no text of any kind (no letters, kanji, kana, "
    "numbers, signs, labels, watermarks, calligraphy, artist seals, hanko "
    "stamps, red seal marks) and no people, no human figures, no faces, no "
    "hands. Pure scenic/object imagery, wide 16:9 composition. "
    "CRITICAL: this is NOT a woodblock reproduction — NO artist signature, NO "
    "red hanko seal stamp anywhere, not even small ones in corners. All "
    "surfaces are completely blank: clock faces and dials show plain dots or "
    "nothing (never numerals), telephone dials are plain, noren curtains, "
    "banners, scrolls, book pages, papers and packaging carry no markings at "
    "all."
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


def build_jobs(data: dict, only_lesson: int | None) -> list[tuple[Path, str]]:
    jobs: list[tuple[Path, str]] = []
    for lesson in data["lessons"]:
        lid = lesson["lesson_id"]
        if only_lesson and lid != only_lesson:
            continue
        for p in lesson["pages"]:
            out = UPLOADS / "page_images" / f"lesson_{lid}" / f"page_{p['page_number']}.webp"
            prompt = f"{p['style']}: {p['prompt']}." + RULES
            jobs.append((out, prompt))
        if lesson.get("slideshow_scenes"):
            style = lesson.get("slideshow_style") or "soft atmospheric watercolor"
            for s in lesson["slideshow_scenes"]:
                out = UPLOADS / "dialog_slideshow" / f"lesson_{lid}" / f"line_{s['line']:02d}_v2.webp"
                prompt = (
                    f"{style}, one continuous visual world across a series: "
                    f"{s['prompt']}." + RULES
                )
                jobs.append((out, prompt))
    return jobs


def render(job: tuple[Path, str], key: str) -> str:
    out, prompt = job
    if out.exists():
        return f"skip {out.relative_to(UPLOADS)}"
    for attempt in (1, 2):
        try:
            webp = to_webp(generate(prompt, key))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(webp)
            return f"OK   {out.relative_to(UPLOADS)} ({len(webp) // 1024} KB)"
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as e:
            if attempt == 2:
                return f"FAIL {out.relative_to(UPLOADS)}: {e}"
            time.sleep(5)
    return f"FAIL {out.relative_to(UPLOADS)}: unreachable"


def main() -> None:
    key = load_api_key()
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    only_lesson = None
    if "--lesson" in sys.argv:
        only_lesson = int(sys.argv[sys.argv.index("--lesson") + 1])
    jobs = build_jobs(data, only_lesson)
    if "--limit" in sys.argv:
        jobs = jobs[: int(sys.argv[sys.argv.index("--limit") + 1])]
    todo = [j for j in jobs if not j[0].exists()]
    print(f"{len(jobs)} Jobs, davon {len(todo)} offen", flush=True)

    fails = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(render, j, key): j for j in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            line = fut.result()
            if line.startswith("FAIL"):
                fails += 1
            print(f"[{i}/{len(todo)}] {line}", flush=True)
    print(f"FERTIG — {len(todo) - fails} OK, {fails} FAIL", flush=True)


if __name__ == "__main__":
    main()

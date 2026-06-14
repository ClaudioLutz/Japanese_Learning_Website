"""Nano-Banana-Bildgenerierung fuer Lektions-Drafts (User-Direktive: gemini-2.5-flash-image, NICHT DALL-E).

Generiert pro Draft:
  - Thumbnail (16:9)  -> app/static/uploads/generated/thumbnail_<slug>.webp  -> draft.thumbnail_url
  - Vokabel-Icons (1:1) -> app/static/uploads/vocab_generated/vocab_<hash>.webp -> data.image_url

Idempotent (bestehende Dateien/URLs werden uebersprungen), 1 Retry, Safety-Blocks werden geloggt + uebersprungen.

Usage:
  python .claude/skills/generate-lesson/scripts/nb_images.py <draft.json> [--no-vocab] [--workers N]
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
UPLOADS = PROJECT_ROOT / "app" / "static" / "uploads"

VOCAB_RULES = (
    " Clean minimalist flat vector illustration, soft muted pastel colours, a single "
    "centred subject, plain off-white background, gentle Japanese aesthetic. STRICT: "
    "absolutely no text, no letters, no kana, no kanji, no numbers, no labels, no "
    "watermark, no signature, no seal/hanko stamp."
)
THUMB_RULES = (
    " Soft modern flat illustration, warm muted palette, calm Japanese aesthetic, "
    "no people, no faces. STRICT: no text of any kind, no letters, no kana, no kanji, "
    "no numbers, no watermark, no signature, no seal/hanko stamp."
)


def load_api_key() -> str:
    for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env gefunden")


def generate(prompt: str, key: str, aspect: str) -> bytes:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect},
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
    raise RuntimeError(f"keine Bilddaten (safety-block?): {json.dumps(data)[:160]}")


def to_webp(png_bytes: bytes) -> bytes:
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=85)
    return buf.getvalue()


def render(prompt: str, out: Path, key: str, aspect: str) -> str:
    if out.exists():
        return f"skip {out.name}"
    for attempt in (1, 2):
        try:
            webp = to_webp(generate(prompt, key, aspect))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(webp)
            return f"OK   {out.name} ({len(webp)//1024} KB)"
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as e:
            if attempt == 2:
                return f"FAIL {out.name}: {str(e)[:120]}"
            time.sleep(4)
    return f"FAIL {out.name}: unreachable"


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit("Draft-Pfad fehlt")
    draft_path = Path(args[0])
    no_vocab = "--no-vocab" in args
    workers = 4
    if "--workers" in args:
        workers = int(args[args.index("--workers") + 1])

    key = load_api_key()
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    slug = draft.get("topic", draft["title"]).lower().replace(" ", "_").replace("/", "_")[:40]

    jobs: list[tuple[str, Path, str, dict, str]] = []  # (kind, out, prompt, target_obj, key_field)

    # Thumbnail
    if not draft.get("thumbnail_url"):
        thumb_out = UPLOADS / "generated" / f"thumbnail_{slug}.webp"
        topic = draft.get("topic", draft["title"])
        tprompt = f"A lesson cover illustration representing the theme '{topic}' for a Japanese-learning lesson." + THUMB_RULES
        jobs.append(("thumb", thumb_out, tprompt, draft, "thumbnail_url"))
    else:
        print(f"[SKIP] Thumbnail vorhanden: {draft['thumbnail_url']}")

    # Vokabel-Icons
    if not no_vocab:
        vocab_items = [
            it.get("data", {})
            for page in draft.get("pages", [])
            for it in page.get("contents", [])
            if it.get("content_type") == "vocabulary"
        ]
        for data in vocab_items:
            if data.get("image_url"):
                continue
            word = data.get("word", "")
            meaning = data.get("meaning_de") or data.get("meaning") or word
            h = hashlib.md5(word.encode()).hexdigest()[:8]
            out = UPLOADS / "vocab_generated" / f"vocab_{h}.webp"
            prompt = f"An icon-style illustration clearly depicting the concept: {meaning}." + VOCAB_RULES
            jobs.append(("vocab", out, prompt, data, "image_url"))

    if not jobs:
        print("[INFO] Nichts zu generieren.")
        return

    print(f"[INFO] {len(jobs)} Bild(er) zu generieren ({workers} Worker)...")
    results: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {}
        for i, (kind, out, prompt, obj, field) in enumerate(jobs):
            aspect = "16:9" if kind == "thumb" else "1:1"
            futs[ex.submit(render, prompt, out, key, aspect)] = i
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            print("  " + results[i])

    # URLs in den Draft schreiben (relativ zu UPLOAD_FOLDER)
    for i, (kind, out, prompt, obj, field) in enumerate(jobs):
        res = results.get(i, "")
        if res.startswith("OK") or res.startswith("skip"):
            rel = str(out.relative_to(UPLOADS)).replace("\\", "/")
            obj[field] = rel

    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results.values() if r.startswith("OK"))
    skipped = sum(1 for r in results.values() if r.startswith("skip"))
    failed = sum(1 for r in results.values() if r.startswith("FAIL"))
    print(f"[FERTIG] {ok} neu, {skipped} vorhanden, {failed} fehlgeschlagen -> Draft aktualisiert: {draft_path.name}")


if __name__ == "__main__":
    main()

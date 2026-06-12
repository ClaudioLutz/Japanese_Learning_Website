"""Generate-until-clean: regeneriert geflaggte Bilder bis der QC-Check passt.

Pro Datei: bis zu 4 Versuche — generieren (verschaerfte Regeln + pro Versuch
zusaetzlicher Anti-Text-Nachdruck), direkt mit gemini-2.5-flash auf Text/
Siegel pruefen, bei sauber: fertig. Nach 4 Versuchen bleibt der letzte Stand
(wird als RESIDUAL geloggt).

Input: scripts/data/qc_regen_list.txt (relative Pfade unter uploads/lessons)
Usage: python scripts/gen_until_clean.py
"""
from __future__ import annotations

import base64
import io
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOADS = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons"
PROMPTS_FILE = PROJECT_ROOT / "scripts" / "data" / "page_image_prompts.json"
LIST_FILE = PROJECT_ROOT / "scripts" / "data" / "qc_regen_list.txt"

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
ESCALATION = [
    "",
    " The artwork is completely unsigned and unstamped, no red marks of any kind exist anywhere in the frame.",
    " Remove all banners, scrolls, lanterns with markings and shop curtains from the scene entirely — replace them with plain architectural surfaces.",
    " Extreme minimalism: only the core objects of the scene on plain background, nothing that could carry writing.",
]

QC_QUESTION = (
    "Does this image contain ANY visible text, letters, digits, numbers, "
    "Japanese characters (kanji/hiragana/katakana), or red artist seal stamps "
    "(hanko)? Answer ONLY with JSON: {\"has_text\": true/false, \"detail\": \"...\"}"
)


def load_api_key() -> str:
    for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env")


def gemini(model: str, parts: list, gen_cfg: dict, key: str) -> dict:
    body = json.dumps({"contents": [{"parts": parts}], "generationConfig": gen_cfg}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        data=body, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def build_prompt_map() -> dict[str, str]:
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    m: dict[str, str] = {}
    for lesson in data["lessons"]:
        lid = lesson["lesson_id"]
        for p in lesson["pages"]:
            rel = f"page_images/lesson_{lid}/page_{p['page_number']}.webp"
            m[rel] = f"{p['style']}: {p['prompt']}."
        if lesson.get("slideshow_scenes"):
            style = lesson.get("slideshow_style") or "soft atmospheric watercolor"
            for s in lesson["slideshow_scenes"]:
                rel = f"dialog_slideshow/lesson_{lid}/line_{s['line']:02d}_v2.webp"
                m[rel] = f"{style}, one continuous visual world across a series: {s['prompt']}."
    return m


def qc_clean(webp: bytes, key: str) -> tuple[bool, str]:
    data = gemini(
        "gemini-2.5-flash",
        [{"inlineData": {"mimeType": "image/webp", "data": base64.b64encode(webp).decode()}},
         {"text": QC_QUESTION}],
        {"responseMimeType": "application/json"}, key,
    )
    verdict = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
    detail = str(verdict.get("detail", ""))[:120]
    if not verdict.get("has_text"):
        return True, detail
    # minor-Toleranz: unleserlich/schwach ohne Siegel/Zeichen/Ziffern gilt als ok
    serious = re.search(r"seal|hanko|signature|character|kanji|digit|number|numeral|letter", detail, re.I)
    return (not serious), detail


def render_until_clean(rel: str, prompt: str, key: str) -> str:
    out = UPLOADS / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image

    for attempt in range(4):
        try:
            data = gemini(
                "gemini-2.5-flash-image",
                [{"text": prompt + RULES + ESCALATION[attempt]}],
                {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}, key,
            )
            png = None
            for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                if "inlineData" in part:
                    png = base64.b64decode(part["inlineData"]["data"])
            if png is None:
                time.sleep(3)
                continue
            img = Image.open(io.BytesIO(png)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=85)
            webp = buf.getvalue()
            ok, detail = qc_clean(webp, key)
            out.write_bytes(webp)  # letzter Stand bleibt immer erhalten
            if ok:
                return f"OK({attempt + 1})  {rel}"
        except Exception as e:  # noqa: BLE001
            time.sleep(5)
            last_err = str(e)[:80]
    return f"RESIDUAL {rel} :: {detail if 'detail' in dir() else ''}"


SAFE_STYLES = [
    "soft atmospheric watercolor",
    "minimalist flat poster art with grain texture",
    "playful gouache (children's book style)",
]


def main() -> None:
    key = load_api_key()
    pmap = build_prompt_map()
    rels = [r.strip().replace("\\", "/") for r in LIST_FILE.read_text().splitlines() if r.strip()]
    rels = [r for r in rels if r in pmap]
    if "--swap-style" in sys.argv:
        # Stil vor dem ersten ':' durch sicheren Stil ersetzen (Motiv bleibt)
        for i, r in enumerate(rels):
            head, sep, motif = pmap[r].partition(":")
            if sep:
                pmap[r] = f"{SAFE_STYLES[i % len(SAFE_STYLES)]}:{motif}"
    print(f"{len(rels)} Dateien in der Until-Clean-Schleife", flush=True)
    residual = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(render_until_clean, r, pmap[r], key): r for r in rels}
        for i, fut in enumerate(as_completed(futures), 1):
            line = fut.result()
            if line.startswith("RESIDUAL"):
                residual += 1
            print(f"[{i}/{len(rels)}] {line}", flush=True)
    print(f"FERTIG — {len(rels) - residual} sauber, {residual} RESIDUAL", flush=True)


if __name__ == "__main__":
    main()

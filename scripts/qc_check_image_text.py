"""QC-Pass: prueft generierte Lektionsbilder auf sichtbaren Text/Ziffern.

Schickt jedes WebP an gemini-2.5-flash mit der Frage, ob Text/Ziffern/
Schriftzeichen sichtbar sind. Ausgabe: eine Zeile pro Bild, FLAG bei Befund.

Usage: python scripts/qc_check_image_text.py > /tmp/qc_result.log
"""
from __future__ import annotations

import base64
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOADS = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons"

QUESTION = (
    "Does this image contain ANY visible text, letters, digits, numbers, "
    "Japanese characters (kanji/hiragana/katakana), or red artist seal stamps "
    "(hanko)? Answer ONLY with JSON: {\"has_text\": true/false, \"detail\": "
    "\"short description of what text/digits you see, or empty\"}"
)


def load_api_key() -> str:
    for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env gefunden")


def check(path: Path, key: str) -> str:
    img_b64 = base64.b64encode(path.read_bytes()).decode()
    body = json.dumps({
        "contents": [{"parts": [
            {"inlineData": {"mimeType": "image/webp", "data": img_b64}},
            {"text": QUESTION},
        ]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={key}",
        data=body, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.load(resp)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        verdict = json.loads(text)
        rel = path.relative_to(UPLOADS)
        if verdict.get("has_text"):
            return f"FLAG {rel} :: {verdict.get('detail', '')[:120]}"
        return f"ok   {rel}"
    except Exception as e:  # noqa: BLE001 - QC soll weiterlaufen
        return f"ERR  {path.relative_to(UPLOADS)} :: {e}"


def main() -> None:
    key = load_api_key()
    files = sorted(UPLOADS.glob("page_images/lesson_*/page_*.webp")) + sorted(
        UPLOADS.glob("dialog_slideshow/lesson_*/line_*_v2.webp")
    )
    print(f"{len(files)} Bilder zu pruefen", flush=True)
    flags = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(check, f, key): f for f in files}
        for i, fut in enumerate(as_completed(futures), 1):
            line = fut.result()
            if line.startswith("FLAG"):
                flags += 1
            print(f"[{i}/{len(files)}] {line}", flush=True)
    print(f"FERTIG — {flags} geflaggt von {len(files)}", flush=True)


if __name__ == "__main__":
    main()

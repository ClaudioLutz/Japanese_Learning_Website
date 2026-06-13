# -*- coding: utf-8 -*-
"""Lektions-Bilder via Gemini Nano Banana (gemini-2.5-flash-image) statt DALL-E.

Ersetzt den DALL-E-`pipeline.py images`-Schritt UND `gen_kanji_images.py` durch
die etablierte Nano-Banana-Pipeline (vgl. scripts/generate_lesson_images.py,
Memory project_lektionsbilder_nano_banana). Nutzt GOOGLE_AI_API_KEY (REST).

Modi:
  draft <draft.json>   Thumbnail + Vokabel-Icon pro Vokabel ohne image_url
                       (schreibt thumbnail_url / vocab.data.image_url in den Draft)
  kanji <lesson_id>    Kanji-Karten-Bild pro Kanji der Lesson ohne image_url
                       (aktualisiert kanji.image_url in der DB)

Idempotent (vorhandene Dateien / gesetzte image_url werden uebersprungen).
1 Retry pro Bild, Safety-Blocks werden geloggt + uebersprungen. 4 Worker.

Pfade (relativ zu UPLOAD_FOLDER = app/static/uploads/):
  generated/thumbnail_<slug>_<ts>.png
  vocab_generated/vocab_<md5[:8]>.png
  kanji_generated/kanji_<id>_<md5[:8]>.png
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

UPLOADS = PROJECT_ROOT / "app" / "static" / "uploads"
MODEL = "gemini-2.5-flash-image"

# Strikte No-Text-/No-People-Regeln (Nano Banana neigt zu Hanko-Siegeln + Text).
ICON_RULES = (
    " STRICT RULES: absolutely NO text of any kind — no letters, no kanji, no "
    "kana, no numbers, no words, no labels, no watermarks, no signatures, no "
    "red hanko seal stamps, no calligraphy anywhere. No people, no faces, no "
    "hands. Pure visual imagery only. Flat modern pictogram, simple geometric "
    "shapes, soft muted pastel colors, clean white background, no harsh "
    "shadows, centered single subject, app-icon style."
)
THUMB_RULES = (
    " STRICT RULES: absolutely NO text of any kind (no letters, kanji, kana, "
    "numbers, labels, watermarks, signatures, red hanko seal stamps, "
    "calligraphy). No human faces. Soft, calm, educational mood."
)


def load_api_key() -> str:
    for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env gefunden")


def generate(prompt: str, key: str, aspect: str = "1:1") -> bytes:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect},
        },
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError(f"keine Bilddaten (safety-block?): {json.dumps(data)[:200]}")


def _render(prompt: str, out: Path, key: str, aspect: str = "1:1") -> str:
    if out.exists():
        return f"skip {out.name}"
    for attempt in (1, 2):
        try:
            png = generate(prompt, key, aspect)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(png)
            return f"OK   {out.name} ({len(png)//1024} KB)"
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as e:
            if attempt == 2:
                return f"FAIL {out.name}: {e}"
            time.sleep(5)
    return f"FAIL {out.name}: unreachable"


def _icon_prompt(meaning: str) -> str:
    concept = (meaning or "").split("/")[0].split(",")[0].split(";")[0].strip()
    return (
        f"A single centered flat-design icon representing the concept "
        f"'{concept}'." + ICON_RULES
    )


# ------------------------------------------------------------------ draft mode
def run_draft(draft_path: Path, key: str) -> None:
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    jobs: list[tuple[str, Path, str]] = []  # (label, out, prompt)

    # Thumbnail
    if not draft.get("thumbnail_url"):
        topic = draft.get("topic") or draft.get("thema") or draft["title"]
        slug = "".join(c if c.isalnum() else "_" for c in str(topic).lower())[:40]
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        thumb_name = f"thumbnail_{slug}_{ts}.png"
        out = UPLOADS / "generated" / thumb_name
        prompt = (
            f"Minimalist flat editorial illustration representing the theme "
            f"'{topic}' for a Japanese language lesson, soft pastel colors, "
            f"calm Japanese aesthetic, clean composition." + THUMB_RULES
        )
        jobs.append(("thumbnail", out, prompt))

    # Vokabel-Icons
    vocab_items = [
        item for page in draft.get("pages", [])
        for item in page.get("contents", [])
        if item.get("content_type") == "vocabulary"
    ]
    for item in vocab_items:
        data = item.get("data", {})
        if data.get("image_url"):
            continue
        word = data.get("word", "")
        meaning = data.get("meaning_de") or data.get("meaning") or word
        h = hashlib.md5(word.encode()).hexdigest()[:8]
        out = UPLOADS / "vocab_generated" / f"vocab_{h}.png"
        jobs.append((f"vocab:{word}", out, _icon_prompt(meaning)))

    print(f"[draft] {draft_path.name}: {len(jobs)} Bilder offen", flush=True)
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(_render, p, o, key): (lbl, o) for (lbl, o, p) in jobs}
        for i, fut in enumerate(as_completed(futs), 1):
            lbl, o = futs[fut]
            line = fut.result()
            results[lbl] = (o, line)
            print(f"  [{i}/{len(jobs)}] {lbl}: {line}", flush=True)

    # Draft mit URLs befuellen (relativ zu UPLOAD_FOLDER)
    for lbl, (out, line) in results.items():
        if line.startswith("FAIL"):
            continue
        rel = f"{out.parent.name}/{out.name}"
        if lbl == "thumbnail":
            draft["thumbnail_url"] = rel
    # Vokabeln: ueber Datei-Existenz mappen (auch skip = vorhanden)
    for item in vocab_items:
        data = item.get("data", {})
        if data.get("image_url"):
            continue
        word = data.get("word", "")
        h = hashlib.md5(word.encode()).hexdigest()[:8]
        f = UPLOADS / "vocab_generated" / f"vocab_{h}.png"
        if f.exists():
            data["image_url"] = f"vocab_generated/{f.name}"

    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[draft] {draft_path.name} aktualisiert (thumbnail_url + vocab image_url)", flush=True)


# ------------------------------------------------------------------ kanji mode
def run_kanji(lesson_id: int, key: str) -> None:
    from app import create_app, db
    from app.models import Kanji, LessonContent

    app = create_app()
    with app.app_context():
        used = (
            db.session.query(LessonContent.content_id)
            .filter(LessonContent.lesson_id == lesson_id,
                    LessonContent.content_type == "kanji")
            .distinct().all()
        )
        ids = {r[0] for r in used if r[0] is not None}
        rows = db.session.query(Kanji).filter(Kanji.id.in_(ids)).all() if ids else []
        todo = [k for k in rows if not k.image_url]
        print(f"[kanji] Lesson {lesson_id}: {len(rows)} Kanji, {len(todo)} ohne Bild", flush=True)

        jobs = []
        for k in todo:
            meaning = (k.meaning or k.character)
            h = hashlib.md5(k.character.encode()).hexdigest()[:8]
            out = UPLOADS / "kanji_generated" / f"kanji_{k.id}_{h}.png"
            jobs.append((k.id, out, _icon_prompt(meaning)))

        results = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = {pool.submit(_render, p, o, key): (kid, o) for (kid, o, p) in jobs}
            for i, fut in enumerate(as_completed(futs), 1):
                kid, o = futs[fut]
                line = fut.result()
                results[kid] = (o, line)
                print(f"  [{i}/{len(jobs)}] kanji_id={kid}: {line}", flush=True)

        for k in todo:
            entry = results.get(k.id)
            if not entry:
                continue
            out, line = entry
            if out.exists():
                k.image_url = f"kanji_generated/{out.name}"
        db.session.commit()
        print(f"[kanji] Lesson {lesson_id}: image_url gesetzt + committed", flush=True)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: gen_images_nanobanana.py draft <draft.json> | kanji <lesson_id>")
        return 2
    key = load_api_key()
    mode = sys.argv[1]
    if mode == "draft":
        run_draft(Path(sys.argv[2]), key)
    elif mode == "kanji":
        run_kanji(int(sys.argv[2]), key)
    else:
        print(f"Unbekannter Modus: {mode}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

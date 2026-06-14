"""DB-basierte Nano-Banana-Bildgenerierung (gemini-2.5-flash-image) fuer bestehende
Lektionen in der Ziel-DB (lokal ODER prod via DATABASE_URL-Override).

Generiert pro angegebener Lesson, wo image_url NULL ist ODER die Datei fehlt:
  - Lesson.thumbnail_url   (16:9)  -> generated/thumbnail_<slug>.webp
  - Kanji.image_url        (1:1)   -> kanji_generated/kanji_<md5(char)>.webp
  - Vocabulary.image_url   (1:1)   -> vocab_generated/vocab_<md5(word)>.webp
Deterministische, id-unabhaengige Dateinamen (natuerlich-schluessel-basiert) →
identisch lokal/prod. Idempotent (skip wenn url gesetzt UND Datei existiert).
NICHT DALL-E (User-Direktive Nano Banana).

Aufruf (aus Repo-Root):
  DATABASE_URL=... PYTHONIOENCODING=utf-8 python .claude/skills/generate-lesson/scripts/nb_images_db.py <lesson_id> [<lesson_id> ...] [--workers N] [--apply]
Ohne --apply: DRY-RUN (zeigt nur, was generiert/gesetzt wuerde).
"""
from __future__ import annotations
import base64, hashlib, io, json, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from app import create_app, db
from app.models import Lesson, LessonContent, Vocabulary, Kanji

VOCAB_RULES = (" Clean minimalist flat vector illustration, soft muted pastel colours, a single "
               "centred subject, plain off-white background, gentle Japanese aesthetic. STRICT: "
               "absolutely no text, no letters, no kana, no kanji, no numbers, no labels, no "
               "watermark, no signature, no seal/hanko stamp.")
THUMB_RULES = (" Soft modern flat illustration, warm muted palette, calm Japanese aesthetic, "
               "no people, no faces. STRICT: no text of any kind, no letters, no kana, no kanji, "
               "no numbers, no watermark, no signature, no seal/hanko stamp.")


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_AI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GOOGLE_AI_API_KEY nicht in .env gefunden")


def generate(prompt: str, key: str, aspect: str) -> bytes:
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"responseModalities": ["IMAGE"],
                                            "imageConfig": {"aspectRatio": aspect}}}).encode()
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-image:generateContent?key={key}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError(f"keine Bilddaten (safety-block?): {json.dumps(data)[:160]}")


def to_webp(png: bytes) -> bytes:
    from PIL import Image
    img = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO(); img.save(buf, "WEBP", quality=85); return buf.getvalue()


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s[:48] or "lesson"


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    workers = 4
    if "--workers" in args:
        workers = int(args[args.index("--workers") + 1])
    ids = [int(a) for a in args if a.isdigit()]
    key = load_api_key()
    app = create_app()
    with app.app_context():
        upload = Path(app.config["UPLOAD_FOLDER"])
        # targets: dict path -> (prompt, aspect, [(obj, field)...])
        targets = {}

        def need(url):
            return (not url) or (not (upload / url).exists())

        def add(rel, prompt, aspect, obj, field):
            t = targets.setdefault(rel, {"prompt": prompt, "aspect": aspect, "setters": []})
            t["setters"].append((obj, field))

        seen_kanji, seen_vocab = set(), set()
        for lid in ids:
            L = db.session.get(Lesson, lid)
            if not L:
                print(f"[WARN] Lesson {lid} fehlt"); continue
            if need(L.thumbnail_url):
                slug = slugify(L.title)
                rel = f"generated/thumbnail_{slug}.webp"
                topic = re.sub(r"\(.*?\)", "", L.title).strip()
                add(rel, f"A lesson cover illustration representing the theme '{topic}' for a Japanese-learning lesson." + THUMB_RULES, "16:9", L, "thumbnail_url")
            for c in db.session.query(LessonContent).filter_by(lesson_id=lid).all():
                if c.content_type == "kanji" and c.content_id and c.content_id not in seen_kanji:
                    k = db.session.get(Kanji, c.content_id)
                    if k and need(k.image_url):
                        seen_kanji.add(k.id)
                        h = hashlib.md5(k.character.encode()).hexdigest()[:8]
                        rel = f"kanji_generated/kanji_{h}.webp"
                        m = (k.meaning or "").split(",")[0].split("/")[0].strip()
                        add(rel, f"A minimalist icon symbolising the concept '{m}'." + VOCAB_RULES, "1:1", k, "image_url")
                elif c.content_type == "vocabulary" and c.content_id and c.content_id not in seen_vocab:
                    v = db.session.get(Vocabulary, c.content_id)
                    if v and need(v.image_url):
                        seen_vocab.add(v.id)
                        h = hashlib.md5(v.word.encode()).hexdigest()[:8]
                        rel = f"vocab_generated/vocab_{h}.webp"
                        m = v.meaning_de or v.meaning or v.word
                        add(rel, f"An icon-style illustration clearly depicting the concept: {m}." + VOCAB_RULES, "1:1", v, "image_url")

        print(f"[INFO] {len(targets)} eindeutige Bilder zu erzeugen/setzen ({workers} Worker, apply={apply})")
        if not apply:
            for rel, t in list(targets.items())[:8]:
                print(f"  würde: {rel}  ({len(t['setters'])} setter)")
            print("[DRY-RUN] nichts geschrieben. Mit --apply ausfuehren."); return

        def work(rel, t):
            out = upload / rel
            if out.exists():
                return rel, "exists"
            for attempt in (1, 2):
                try:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(to_webp(generate(t["prompt"], key, t["aspect"])))
                    return rel, "OK"
                except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as e:
                    if attempt == 2:
                        return rel, f"FAIL {str(e)[:90]}"
                    time.sleep(4)
            return rel, "FAIL"

        results = {}
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(work, rel, t): rel for rel, t in targets.items()}
            for fut in as_completed(futs):
                rel, status = fut.result(); results[rel] = status
                print(f"  {status:5} {rel}")

        set_count = 0
        for rel, t in targets.items():
            if results.get(rel) in ("OK", "exists"):
                for obj, field in t["setters"]:
                    if getattr(obj, field) != rel:
                        setattr(obj, field, rel); set_count += 1
        db.session.commit()
        ok = sum(1 for s in results.values() if s == "OK")
        ex_ = sum(1 for s in results.values() if s == "exists")
        fail = sum(1 for s in results.values() if s.startswith("FAIL"))
        print(f"\n[FERTIG] {ok} generiert, {ex_} vorhanden, {fail} fehlgeschlagen; {set_count} image_url-Felder gesetzt (committed).")


if __name__ == "__main__":
    main()

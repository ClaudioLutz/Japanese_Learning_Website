"""Generate Kanji-Backside-Images (Nano Banana / gemini-2.5-flash-image) fuer
alle Kanji ohne image_url die in mindestens einer Lesson verwendet werden.

Speichert PNGs unter app/static/uploads/kanji_generated/ und setzt
kanji.image_url auf den relativen Pfad.

Idempotent: ueberspringt Eintraege mit bereits gesetztem image_url.

Optional: --jlpt 5    nur N5 generieren
          --only 漢字  nur dieses eine Zeichen
          --all-jlpt5  alle JLPT-N5 (auch ohne Lesson-Bezug)
"""
import argparse
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db  # noqa: E402
from app.models import Kanji, LessonContent  # noqa: E402
from app.ai_services import AILessonContentGenerator  # noqa: E402

OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "kanji_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _candidates(args) -> list[Kanji]:
    q = db.session.query(Kanji)
    if args.only:
        return q.filter(Kanji.character == args.only).all()

    if args.all_jlpt5:
        if args.jlpt:
            q = q.filter(Kanji.jlpt_level == args.jlpt)
        else:
            q = q.filter(Kanji.jlpt_level == 5)
        return q.order_by(Kanji.id).all()

    # Default: nur Kanji die in einer Lesson verwendet werden
    used_ids = (
        db.session.query(LessonContent.content_id)
        .filter(LessonContent.content_type == "kanji")
        .distinct()
        .all()
    )
    used_ids = {row[0] for row in used_ids if row[0] is not None}
    if not used_ids:
        return []

    q = q.filter(Kanji.id.in_(used_ids))
    if args.jlpt:
        q = q.filter(Kanji.jlpt_level == args.jlpt)
    return q.order_by(Kanji.id).all()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jlpt", type=int, default=None, help="Nur dieses JLPT-Level (z.B. 5)")
    parser.add_argument("--only", type=str, default=None, help="Nur dieses eine Zeichen")
    parser.add_argument("--all-jlpt5", action="store_true",
                        help="Alle N5-Kanji, nicht nur die in Lessons benutzten")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        gen = AILessonContentGenerator()
        if not gen.gemini_api_key and not args.dry_run:
            print("[FEHLER] Nano Banana nicht konfiguriert (GOOGLE_AI_API_KEY?)")
            return 1

        rows = _candidates(args)
        todo = [k for k in rows if not k.image_url]
        print(f"[INFO] {len(rows)} Kanji-Kandidaten, {len(todo)} ohne Bild")

        if args.dry_run:
            for k in todo:
                print(f"  TODO {k.character} (id={k.id}, JLPT N{k.jlpt_level}) — {k.meaning[:50]}")
            return 0

        for i, k in enumerate(todo, start=1):
            meaning = (k.meaning or k.character).split("/")[0].strip()
            print(f"  [{i:2d}/{len(todo)}] GEN {k.character} / {meaning} ...")
            result = gen.generate_vocabulary_image_nb(word=k.character, meaning=meaning)
            if not result or "image_bytes" not in result:
                err = (result or {}).get("error", "unbekannt")
                print(f"      [FEHLER] {err}")
                continue

            hash_suffix = hashlib.md5(k.character.encode()).hexdigest()[:8]
            filename = f"kanji_{k.id}_{hash_suffix}.png"
            out_path = OUT_DIR / filename
            out_path.write_bytes(result["image_bytes"])
            url = f"kanji_generated/{filename}"
            k.image_url = url
            db.session.commit()
            print(f"      OK -> {url}")

        print("[DONE]")
        return 0


if __name__ == "__main__":
    sys.exit(main())

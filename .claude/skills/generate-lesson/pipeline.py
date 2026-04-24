"""
generate-lesson pipeline — Persistiert Claude-generierte Lektionen in Postgres.

Claude produziert JSON-Drafts (siehe SKILL.md §5 für Schema).
Dieses Script validiert, persistiert, und loggt.

Subcommands:
  status                 # DB-Gap-Analyse: welche JLPT-Themen fehlen?
  validate <draft.json>  # Prüft Constraints, ohne zu schreiben
  images   <draft.json>  # Generiert DALL-E-Bilder für Thumbnail/Vokabeln
  insert   <draft.json>  # Transaktionaler INSERT, gibt lesson_id zurück
  commit   <lesson_id>   # Git-add/commit/push (nur Metadaten, kein App-Code)

Usage: python .claude/skills/generate-lesson/pipeline.py <subcommand> [args]
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# --- Projekt-Setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))


# ========================================================================
# VALIDATION
# ========================================================================

# Harte Constraints aus SKILL.md §3
ALLOWED_QUIZ_TYPES = {"multiple_choice", "true_false", "matching"}
ALLOWED_JLPT = {4, 5}
ALLOWED_CONTENT_TYPES = {"kana", "kanji", "vocabulary", "grammar", "text", "image", "video", "audio"}
ALLOWED_PAGE_TYPES = {"normal", "quiz_carousel"}

REQUIRED_LESSON_FIELDS = ["title", "description", "jlpt_level", "topic", "pages"]
REQUIRED_VOCAB_FIELDS = ["word", "reading", "romaji", "meaning", "meaning_de", "jlpt_level"]
REQUIRED_GRAMMAR_FIELDS = ["title", "explanation", "structure", "romaji", "jlpt_level"]

# HTML-Tags in content_text sind verboten: lesson_view.html:683 nutzt `| nl2br`,
# was HTML escaped. Nur Plaintext mit \n\n fuer Absaetze.
HTML_TAG_RE = __import__("re").compile(r"<\s*/?\s*[a-zA-Z][^>]*>")


class ValidationError(Exception):
    pass


def validate_draft(draft: dict) -> list[str]:
    """Validiert den Draft. Gibt Liste von Fehlern zurueck (leer = OK)."""
    errors = []

    # Lesson-Meta
    for f in REQUIRED_LESSON_FIELDS:
        if f not in draft:
            errors.append(f"Lesson fehlt Feld: {f}")

    jlpt = draft.get("jlpt_level")
    if jlpt not in ALLOWED_JLPT:
        errors.append(f"jlpt_level={jlpt} nicht erlaubt. Erlaubt: {sorted(ALLOWED_JLPT)}")

    pages = draft.get("pages", [])
    if len(pages) < 3:
        errors.append(f"Mindestens 3 Pages erforderlich, hat {len(pages)}")

    # Quiz-Carousel muss vorhanden sein
    if not any(p.get("page_type") == "quiz_carousel" for p in pages):
        errors.append("Mindestens eine Page muss page_type='quiz_carousel' sein")

    # Pages + Content
    vocab_count = 0
    grammar_count = 0
    quiz_count = 0
    quiz_types_seen = set()

    for p_idx, page in enumerate(pages, start=1):
        pt = page.get("page_type", "normal")
        if pt not in ALLOWED_PAGE_TYPES:
            errors.append(f"Page {p_idx}: page_type={pt} nicht erlaubt")

        for c_idx, item in enumerate(page.get("contents", []), start=1):
            ct = item.get("content_type")
            if ct not in ALLOWED_CONTENT_TYPES:
                errors.append(f"Page {p_idx}.{c_idx}: content_type={ct} nicht erlaubt")
                continue

            # HTML-Tag-Check fuer text-Content: lesson_view.html nutzt | nl2br
            if ct == "text":
                data = item.get("data", {})
                ctext = data.get("content_text", "")
                tags = HTML_TAG_RE.findall(ctext)
                if tags:
                    errors.append(
                        f"Page {p_idx}.{c_idx} text: HTML-Tags verboten "
                        f"(lesson_view.html nutzt | nl2br → Tags werden escaped). "
                        f"Gefunden: {tags[:3]}. Nutze Plaintext mit \\n\\n fuer Absaetze."
                    )

            if ct == "vocabulary":
                data = item.get("data", {})
                vocab_count += 1
                for f in REQUIRED_VOCAB_FIELDS:
                    if f not in data:
                        errors.append(f"Page {p_idx}.{c_idx} Vocabulary fehlt: {f}")
                v_jlpt = data.get("jlpt_level")
                if v_jlpt is not None and v_jlpt < jlpt:
                    # Niedriger ist OK (z.B. N5-Vokabel in N4-Lektion)
                    pass
                elif v_jlpt is not None and v_jlpt > jlpt:
                    errors.append(
                        f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                        f"jlpt_level={v_jlpt} > Lesson-Level {jlpt}"
                    )

            elif ct == "grammar":
                data = item.get("data", {})
                grammar_count += 1
                for f in REQUIRED_GRAMMAR_FIELDS:
                    if f not in data:
                        errors.append(f"Page {p_idx}.{c_idx} Grammar fehlt: {f}")

            # Quiz-Fragen (in quiz_carousel)
            for q_idx, q in enumerate(item.get("quiz_questions", []), start=1):
                qt = q.get("question_type")
                if qt not in ALLOWED_QUIZ_TYPES:
                    errors.append(
                        f"Page {p_idx}.{c_idx}.Q{q_idx}: question_type={qt} "
                        f"VERBOTEN. Erlaubt: {sorted(ALLOWED_QUIZ_TYPES)}"
                    )
                else:
                    quiz_types_seen.add(qt)
                quiz_count += 1

                if qt == "multiple_choice":
                    opts = q.get("options", [])
                    if len(opts) != 4:
                        errors.append(
                            f"Page {p_idx}.{c_idx}.Q{q_idx}: multiple_choice braucht "
                            f"genau 4 Optionen, hat {len(opts)}"
                        )
                    correct = sum(1 for o in opts if o.get("is_correct"))
                    if correct != 1:
                        errors.append(
                            f"Page {p_idx}.{c_idx}.Q{q_idx}: multiple_choice braucht "
                            f"genau 1 richtige Option, hat {correct}"
                        )

    # Budget-Checks aus SKILL.md §4 (angepasst 2026-04-24: groessere Lektionen)
    if not (15 <= vocab_count <= 25):
        errors.append(f"Vocabulary-Count {vocab_count} ausserhalb [15,25]")
    if not (2 <= grammar_count <= 4):
        errors.append(f"Grammar-Count {grammar_count} ausserhalb [2,4]")
    if not (10 <= quiz_count <= 18):
        errors.append(f"Quiz-Count {quiz_count} ausserhalb [10,18]")
    if len(quiz_types_seen) < 2:
        errors.append(
            f"Mind. 2 verschiedene Quiz-Typen erforderlich, nur {quiz_types_seen} verwendet"
        )
    if len(pages) < 5:
        errors.append(f"Mindestens 5 Pages erforderlich (Einfuehrung/Vokabeln/Grammar/Dialog/Quiz/Zusammenfassung), hat {len(pages)}")

    # Bilder-Pflicht: thumbnail_url im Lesson-Header
    if not draft.get("thumbnail_url"):
        errors.append(
            "thumbnail_url fehlt. Pipeline-Schritt `images` muss vor `insert` laufen "
            "(DALL-E Thumbnail). Notfalls manuell URL setzen."
        )

    # Umlaut-Fallback-Check (hart) — erkennt ASCII-Ersatz fuer Umlaute
    # in ALLEN deutschen Fliesstexten des Drafts.
    blob = json.dumps(draft, ensure_ascii=False)
    # Regex: typische deutsche Woerter, die bei Umlaut-Fallback erscheinen
    umlaut_fallback_re = __import__("re").compile(
        r"\b("
        r"hoeflich|Hoeflich|"
        r"fuer|Fuer|ueber|Ueber|"
        r"koennen|Koennen|koennt|muessen|Muessen|"
        r"hoeren|Hoeren|nuetzlich|Nuetzlich|"
        r"Schueler|schuelerin|Schuelerin|Gruesse|gruesse|"
        r"Einfuehrung|einfuehrung|Uebung|uebung|Uebersicht|uebersicht|"
        r"Getraenk|getraenk|koestlich|Koestlich|spaet|Spaet|"
        r"Waehrung|waehrung|Erklaerung|erklaerung|Uebersetzung|uebersetzung"
        r")\b"
    )
    for m in umlaut_fallback_re.finditer(blob):
        errors.append(
            f"ASCII-Umlaut-Fallback verboten: '{m.group(0)}' — "
            f"nutze Umlaute (ue → ü, oe → ö, ae → ä)."
        )

    # Romaji-in-Text-Check: Wenn ein content_text japanische Zeichen enthaelt,
    # muss in naher Umgebung auch Romaji (lateinische Klammer-Passage) stehen.
    jp_char_re = __import__("re").compile(r"[぀-ヿ一-鿿]")
    romaji_hint_re = __import__("re").compile(r"\([a-zA-Z][a-zA-Z \-'?!.,]{1,}\)")
    for p_idx, page in enumerate(draft.get("pages", []), start=1):
        for c_idx, item in enumerate(page.get("contents", []), start=1):
            if item.get("content_type") != "text":
                continue
            ctext = item.get("data", {}).get("content_text", "")
            if jp_char_re.search(ctext) and not romaji_hint_re.search(ctext):
                errors.append(
                    f"Page {p_idx}.{c_idx} text enthaelt JP-Zeichen, "
                    f"aber keine Romaji in Klammern. Regel: jedes JP-Wort "
                    f"im Fliesstext muss mit Romaji `(romaji)` annotiert sein."
                )

    return errors


# ========================================================================
# DB-GAP-ANALYSE (status)
# ========================================================================

def db_status():
    """Zeigt DB-Gaps fuer naechsten Lesson-Vorschlag."""
    try:
        from app import create_app, db
        from app.models import Lesson, Vocabulary, Grammar, LessonCategory
    except ImportError as e:
        print(f"[FEHLER] App-Import fehlgeschlagen: {e}")
        print("Tipp: venv aktivieren und docker compose up db -d")
        return

    app = create_app()
    with app.app_context():
        total_lessons = db.session.query(Lesson).count()
        n5_lessons = db.session.query(Lesson).filter(Lesson.difficulty_level <= 2).count()
        n4_lessons = db.session.query(Lesson).filter(
            Lesson.difficulty_level.in_([3, 4])
        ).count()

        n5_vocab = db.session.query(Vocabulary).filter_by(jlpt_level=5).count()
        n4_vocab = db.session.query(Vocabulary).filter_by(jlpt_level=4).count()

        print("=" * 60)
        print("  DB-Gap-Analyse")
        print("=" * 60)
        print(f"  Lessons gesamt:       {total_lessons}")
        print(f"    davon N5 (diff 1-2): {n5_lessons}")
        print(f"    davon N4 (diff 3-4): {n4_lessons}")
        print(f"  Vocabulary:")
        print(f"    N5:                  {n5_vocab}")
        print(f"    N4:                  {n4_vocab}")

        # Themen-Verteilung ueber Kategorien
        categories = db.session.query(LessonCategory).all()
        print(f"\n  Kategorien ({len(categories)}):")
        for cat in categories:
            cat_lesson_count = db.session.query(Lesson).filter_by(
                category_id=cat.id
            ).count()
            print(f"    {cat.name}: {cat_lesson_count} Lessons")

        print("\n  Vorgeschlagene Themen (noch wenig abgedeckt):")
        # Heuristik: vergleiche gegen Standard-N5-Themen
        standard_topics = [
            "Begruessung", "Zahlen", "Familie", "Uhrzeit", "Essen",
            "Wohnen", "Transport", "Wetter", "Hobbys", "Einkaufen"
        ]
        missing = []
        for topic in standard_topics:
            exists = db.session.query(Lesson).filter(
                Lesson.title.ilike(f"%{topic}%")
            ).first()
            if not exists:
                missing.append(topic)
        for t in missing[:5]:
            print(f"    - {t} (keine Lesson mit diesem Titel-Fragment gefunden)")


# ========================================================================
# INSERT
# ========================================================================

def _get_or_create_vocab(db, Vocabulary, data: dict) -> int:
    """Duplicate-safe: gibt bestehende ID zurueck oder erstellt neu."""
    existing = db.session.query(Vocabulary).filter_by(word=data["word"]).first()
    if existing:
        return existing.id
    v = Vocabulary(
        word=data["word"],
        reading=data["reading"],
        romaji=data.get("romaji"),
        meaning=data["meaning"],
        meaning_de=data.get("meaning_de"),
        jlpt_level=data.get("jlpt_level"),
        example_sentence_japanese=data.get("example_sentence_japanese"),
        example_sentence_english=data.get("example_sentence_english"),
        image_url=data.get("image_url"),
        status="approved",
        created_by_ai=True,
    )
    db.session.add(v)
    db.session.flush()
    return v.id


def _get_or_create_grammar(db, Grammar, data: dict) -> int:
    existing = db.session.query(Grammar).filter_by(title=data["title"]).first()
    if existing:
        return existing.id
    g = Grammar(
        title=data["title"],
        explanation=data["explanation"],
        structure=data.get("structure"),
        romaji=data.get("romaji"),
        jlpt_level=data.get("jlpt_level"),
        example_sentences=data.get("example_sentences"),
        status="approved",
        created_by_ai=True,
    )
    db.session.add(g)
    db.session.flush()
    return g.id


def insert_draft(draft_path: Path) -> int:
    """Transaktionaler INSERT einer Lektion. Gibt lesson_id zurueck."""
    errors = validate_draft(json.loads(draft_path.read_text(encoding="utf-8")))
    if errors:
        print("[ABBRUCH] Validation-Fehler:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    from app import create_app, db
    from app.models import (
        Lesson, LessonPage, LessonContent, Vocabulary, Grammar,
        QuizQuestion, QuizOption,
    )

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    app = create_app()

    with app.app_context():
        try:
            # Map JLPT → difficulty_level (N5=1, N4=3)
            jlpt = draft["jlpt_level"]
            difficulty_level = 1 if jlpt == 5 else 3

            lesson = Lesson(
                title=draft["title"],
                description=draft["description"],
                lesson_type="free",
                difficulty_level=difficulty_level,
                is_published=False,  # erst nach Verifikation True
                allow_guest_access=draft.get("allow_guest_access", False),
                instruction_language=draft.get("instruction_language", "german"),
                thumbnail_url=draft.get("thumbnail_url"),
                price=0.0,
                is_purchasable=False,
            )
            db.session.add(lesson)
            db.session.flush()
            lesson_id = lesson.id

            for page_num, page_data in enumerate(draft["pages"], start=1):
                page = LessonPage(
                    lesson_id=lesson_id,
                    page_number=page_num,
                    title=page_data.get("title"),
                    description=page_data.get("description"),
                    page_type=page_data.get("page_type", "normal"),
                )
                db.session.add(page)
                db.session.flush()

                for order_idx, item in enumerate(page_data.get("contents", []), start=1):
                    ct = item["content_type"]
                    content_id = None
                    content_text = None
                    title = None

                    if ct == "vocabulary":
                        content_id = _get_or_create_vocab(db, Vocabulary, item["data"])
                    elif ct == "grammar":
                        content_id = _get_or_create_grammar(db, Grammar, item["data"])
                    elif ct == "text":
                        content_text = item.get("data", {}).get("content_text")
                        title = item.get("data", {}).get("title")

                    lc = LessonContent(
                        lesson_id=lesson_id,
                        content_type=ct,
                        content_id=content_id,
                        title=title,
                        content_text=content_text,
                        order_index=order_idx,
                        page_number=page_num,
                        is_interactive=bool(item.get("quiz_questions")),
                        quiz_type="standard",
                        generated_by_ai=True,
                        ai_generation_details={"generator": "claude", "draft": draft_path.name},
                    )
                    db.session.add(lc)
                    db.session.flush()

                    # Quiz-Fragen
                    for q_idx, q in enumerate(item.get("quiz_questions", []), start=1):
                        qq = QuizQuestion(
                            lesson_content_id=lc.id,
                            question_type=q["question_type"],
                            question_text=q["question_text"],
                            explanation=q.get("explanation"),
                            hint=q.get("hint"),
                            difficulty_level=q.get("difficulty_level", 1),
                            points=q.get("points", 1),
                            order_index=q_idx,
                        )
                        db.session.add(qq)
                        db.session.flush()

                        for o_idx, opt in enumerate(q.get("options", []), start=1):
                            qo = QuizOption(
                                question_id=qq.id,
                                option_text=opt["option_text"],
                                is_correct=opt.get("is_correct", False),
                                order_index=o_idx,
                                feedback=opt.get("feedback"),
                            )
                            db.session.add(qo)

            db.session.commit()
            print(f"[OK] Lesson inserted: id={lesson_id}, title='{draft['title']}'")

            # Generated-lessons.jsonl anhaengen
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "lesson_id": lesson_id,
                "title": draft["title"],
                "jlpt_level": jlpt,
                "topic": draft.get("topic"),
                "draft_file": str(draft_path),
            }
            log_path = SKILL_DIR / "generated-lessons.jsonl"
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            return lesson_id

        except Exception as e:
            db.session.rollback()
            print(f"[FEHLER] Rollback wegen: {e}")
            raise


# ========================================================================
# GIT COMMIT
# ========================================================================

def git_commit(lesson_id: int):
    """Committet nur Skill-Metadata (keine App-Code-Aenderungen)."""
    files = [
        ".claude/skills/generate-lesson/generated-lessons.jsonl",
        ".claude/skills/generate-lesson/learnings.md",
    ]
    subprocess.run(["git", "add", *files], cwd=PROJECT_ROOT, check=True)
    msg = f"Lektion generiert via Skill (Lesson ID {lesson_id})"
    subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_ROOT, check=True)
    subprocess.run(["git", "push"], cwd=PROJECT_ROOT, check=True)
    print(f"[OK] Git push abgeschlossen.")


# ========================================================================
# DALL-E Images (Stub — benoetigt OPENAI_API_KEY)
# ========================================================================

def generate_images(draft_path: Path):
    """Erweitert den Draft mit DALL-E-Bild-URLs.

    Diese Funktion ist explizit die einzige erlaubte Nutzung externer AI-APIs
    im Skill, siehe SKILL.md §7.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        print("[SKIP] OPENAI_API_KEY nicht gesetzt — keine Bilder generiert.")
        return

    # Bestehenden Service verwenden (der nutzt DALL-E)
    from app.ai_services import AILessonContentGenerator
    from app import create_app

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    app = create_app()

    import hashlib

    with app.app_context():
        gen = AILessonContentGenerator()

        # --- (1) Thumbnail ------------------------------------------------
        if not draft.get("thumbnail_url"):
            topic = draft.get("topic", draft["title"])
            prompt = (
                f"minimalist flat illustration of '{topic}', "
                f"soft pastels, no text, Japanese aesthetic"
            )
            result = gen.generate_single_image(prompt=prompt)
            if result and result.get("image_bytes"):
                thumb_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "generated"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                slug = draft.get("topic", "lesson").lower().replace(" ", "_")
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"thumbnail_{slug}_{ts}.png"
                (thumb_dir / filename).write_bytes(result["image_bytes"])
                draft["thumbnail_url"] = f"/static/uploads/generated/{filename}"
                print(f"[OK] Thumbnail -> {draft['thumbnail_url']}")
            else:
                err = (result or {}).get("error", "unbekannt")
                print(f"[FEHLER] Thumbnail-Generierung: {err}")
        else:
            print(f"[SKIP] Thumbnail vorhanden: {draft['thumbnail_url']}")

        # --- (2) Vokabel-Icons fuer JEDE Vokabel --------------------------
        vocab_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "vocab_generated"
        vocab_dir.mkdir(parents=True, exist_ok=True)

        vocab_items = [
            item
            for page in draft.get("pages", [])
            for item in page.get("contents", [])
            if item.get("content_type") == "vocabulary"
        ]
        print(f"[INFO] {len(vocab_items)} Vokabeln — generiere fehlende Icons")

        for i, item in enumerate(vocab_items, start=1):
            data = item.get("data", {})
            if data.get("image_url"):
                continue
            word = data.get("word", "")
            meaning = data.get("meaning") or data.get("meaning_de") or word
            print(f"  [{i:2d}/{len(vocab_items)}] {word} ({meaning[:35]})")
            res = gen.generate_vocabulary_image(word=word, meaning=meaning)
            if not res or "image_bytes" not in res:
                err = (res or {}).get("error", "unbekannt")
                print(f"      [FEHLER] {err}")
                continue
            hash_suffix = hashlib.md5(word.encode()).hexdigest()[:8]
            filename = f"vocab_{hash_suffix}.png"
            (vocab_dir / filename).write_bytes(res["image_bytes"])
            # IMPORTANT: Pfad relativ zu UPLOAD_FOLDER (app/static/uploads/),
            # damit url_for('routes.uploaded_file', filename=...) passt.
            # Siehe lesson_view.html:859 und routes.py:3973 /uploads/<path:filename>.
            data["image_url"] = f"vocab_generated/{filename}"

        # Draft ueberschreiben mit gefuellten URLs
        draft_path.write_text(
            json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("[OK] Draft aktualisiert.")


# ========================================================================
# AUDIO (Google Cloud TTS fuer die Dialog-Page)
# ========================================================================

def generate_conversation_audio(lesson_id: int) -> int:
    """Rendert die Dialog-Page einer Lesson als MP3 (Google Cloud TTS)
    und legt ein LessonContent(content_type='audio') vor dem Dialog-Text an.

    Idempotent: hat die Dialog-Page bereits ein audio-Content, kein Neu-Insert.
    Gibt 0 = OK, 1 = Fehler, 2 = Skip (existiert) zurueck.
    """
    script = SKILL_DIR / "scripts" / "gen_conversation_audio.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script), str(lesson_id)],
        cwd=PROJECT_ROOT, env=env,
    )
    return result.returncode


def generate_dialog_slideshow(lesson_id: int) -> int:
    """Baut pro Dialog-Zeile ein Slide mit TTS-Audio und DALL-E-Bild.

    Siehe scripts/gen_dialog_slideshow.py fuer die Details. Legt einen
    LessonContent(content_type='dialog_slideshow', content_text=JSON)
    auf der Dialog-Page an.
    """
    script = SKILL_DIR / "scripts" / "gen_dialog_slideshow.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script), str(lesson_id)],
        cwd=PROJECT_ROOT, env=env,
    )
    return result.returncode


# ========================================================================
# CLI
# ========================================================================

def main():
    parser = argparse.ArgumentParser(description="generate-lesson pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="DB-Gap-Analyse")

    p_val = sub.add_parser("validate", help="Draft validieren (ohne insert)")
    p_val.add_argument("draft", type=Path)

    p_img = sub.add_parser("images", help="DALL-E-Bilder erzeugen")
    p_img.add_argument("draft", type=Path)

    p_ins = sub.add_parser("insert", help="Draft in DB persistieren")
    p_ins.add_argument("draft", type=Path)

    p_aud = sub.add_parser("audio", help="Dialog-MP3 via Google Cloud TTS generieren")
    p_aud.add_argument("lesson_id", type=int)

    p_slide = sub.add_parser("slideshow", help="Dialog-Slideshow (TTS+DALL-E pro Zeile) bauen")
    p_slide.add_argument("lesson_id", type=int)

    p_cmt = sub.add_parser("commit", help="Git-commit Skill-Metadata")
    p_cmt.add_argument("lesson_id", type=int)

    args = parser.parse_args()

    if args.cmd == "status":
        db_status()
    elif args.cmd == "validate":
        draft = json.loads(args.draft.read_text(encoding="utf-8"))
        errors = validate_draft(draft)
        if errors:
            print("[FEHLER] Validation:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("[OK] Draft valide.")
    elif args.cmd == "images":
        generate_images(args.draft)
    elif args.cmd == "insert":
        insert_draft(args.draft)
    elif args.cmd == "audio":
        sys.exit(generate_conversation_audio(args.lesson_id))
    elif args.cmd == "slideshow":
        sys.exit(generate_dialog_slideshow(args.lesson_id))
    elif args.cmd == "commit":
        git_commit(args.lesson_id)


if __name__ == "__main__":
    main()

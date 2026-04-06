#!/usr/bin/env python3
"""
Minna No Nihongo → DB Import-Skript.

Liest JSON-Dateien aus scripts/mnn_data/ und importiert:
- Vocabulary-Einträge
- Grammar-Einträge
- Lesson + LessonContent (verlinkt Vocabulary/Grammar)
- Optionale Quiz-Fragen pro Vokabel

Verwendung:
    python scripts/import_mnn.py                           # Alle JSON-Dateien
    python scripts/import_mnn.py beginner1_lesson01.json   # Einzelne Datei
    python scripts/import_mnn.py --dry-run                 # Nur anzeigen, nicht schreiben
"""

import json
import os
import shutil
import sys
import io
from pathlib import Path

# Windows: UTF-8-Ausgabe erzwingen
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Projekt-Root ermitteln und zum Path hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Umgebungsvariablen setzen bevor App importiert wird
os.environ.setdefault("DATABASE_URL", "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")

from app import create_app, db
from app.models import (
    Vocabulary, Grammar, Lesson, LessonContent,
    LessonCategory, LessonPage, Course, course_lessons,
)

DATA_DIR = PROJECT_ROOT / "scripts" / "mnn_data"
UPLOADS_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "audio"

# Pfade zu den MNN Audio-CDs
MNN_AUDIO_PATHS = {
    "Beginner I": Path("D:/Media/Language/Minna No Nihongo/Beginner I/Minna No Nihongo Beginner I - Textbook {CD}"),
    "Beginner II": Path("D:/Media/Language/Minna No Nihongo/Beginner II/Minna No Nihongo Beginner II - Textbook {CD}"),
    "Intermediate I": Path("D:/Media/Language/Minna No Nihongo/Intermediate I/Minna No Nihongo Intermediate I - Textbook {CD}"),
    "Intermediate II": Path("D:/Media/Language/Minna No Nihongo/Intermediate II/Minna No Nihongo Intermediate II - Textbook {CD}"),
}

# Audio-Datei-Typ-Mapping (Dateiname-Suffix → Anzeigename)
AUDIO_LABELS = {
    "Kotoba": "Vokabeln (Audio)",
    "Bunkei": "Satzmuster (Audio)",
    "Reibun": "Beispielsätze (Audio)",
    "Kaiwa": "Konversation (Audio)",
    "Renshuu C1": "Übung C1 (Audio)",
    "Renshuu C2": "Übung C2 (Audio)",
    "Renshuu C3": "Übung C3 (Audio)",
    "Mondai 1": "Aufgabe 1 (Audio)",
    "Mondai 2": "Aufgabe 2 (Audio)",
    "Mondai 3": "Aufgabe 3 (Audio)",
    "Mondai 4": "Aufgabe 4 (Audio)",
}


def load_json(filepath: Path) -> dict:
    """Lädt eine JSON-Datei."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def import_vocabulary(data: dict, dry_run: bool = False) -> list[Vocabulary]:
    """Importiert Vokabeln und gibt die erstellten/gefundenen Objekte zurück."""
    all_vocab = data.get("vocabulary", []) + data.get("vocabulary_countries", [])
    result = []

    for item in all_vocab:
        word = item["word"]
        existing = None if dry_run else Vocabulary.query.filter_by(word=word).first()
        if existing:
            print(f"  [SKIP] Vocabulary '{word}' existiert bereits (ID {existing.id})")
            result.append(existing)
            continue

        vocab = Vocabulary(
            word=word,
            reading=item["reading"],
            meaning=item["meaning"],
            jlpt_level=data.get("jlpt_level", 5),
            status="approved",
            created_by_ai=False,
        )

        if dry_run:
            print(f"  [DRY] Vocabulary: {word} ({item['reading']}) — {item['meaning']}")
        else:
            db.session.add(vocab)
            db.session.flush()  # ID zuweisen
            print(f"  [NEW] Vocabulary: {word} (ID {vocab.id})")
            result.append(vocab)

    return result


def import_grammar(data: dict, dry_run: bool = False) -> list[Grammar]:
    """Importiert Grammatik-Einträge."""
    result = []

    for item in data.get("grammar", []):
        title = item["title"]
        existing = None if dry_run else Grammar.query.filter_by(title=title).first()
        if existing:
            print(f"  [SKIP] Grammar '{title}' existiert bereits (ID {existing.id})")
            result.append(existing)
            continue

        grammar = Grammar(
            title=title,
            explanation=item["explanation"],
            structure=item.get("structure"),
            jlpt_level=data.get("jlpt_level", 5),
            example_sentences=item.get("example_sentences"),
            status="approved",
            created_by_ai=False,
        )

        if dry_run:
            print(f"  [DRY] Grammar: {title}")
        else:
            db.session.add(grammar)
            db.session.flush()
            print(f"  [NEW] Grammar: {title} (ID {grammar.id})")
            result.append(grammar)

    return result


def get_or_create_category(name: str, description: str = "", color: str = "#007bff") -> LessonCategory:
    """Findet oder erstellt eine Lektions-Kategorie."""
    cat = LessonCategory.query.filter_by(name=name).first()
    if not cat:
        cat = LessonCategory(name=name, description=description, color_code=color)
        db.session.add(cat)
        db.session.flush()
        print(f"  [NEW] Kategorie: {name} (ID {cat.id})")
    return cat


def get_or_create_course(title: str, description: str = "") -> Course:
    """Findet oder erstellt einen Kurs."""
    course = Course.query.filter_by(title=title).first()
    if not course:
        course = Course(
            title=title,
            description=description,
            is_published=True,
            price=0.0,
        )
        db.session.add(course)
        db.session.flush()
        print(f"  [NEW] Kurs: {title} (ID {course.id})")
    return course


def _format_conversation(conv: dict) -> str:
    """Formatiert eine Konversation als lesbaren Text."""
    lines = []
    for line in conv.get("lines", []):
        lines.append(f"{line['speaker']}: {line['japanese']}")
        if line.get("romaji"):
            lines.append(f"  ({line['romaji']})")
        lines.append(f"  → {line['english']}")
        lines.append("")  # Leerzeile zwischen Sprechern
    return "\n".join(lines).strip()


def create_lesson(
    data: dict,
    vocab_items: list[Vocabulary],
    grammar_items: list[Grammar],
    category: LessonCategory,
    dry_run: bool = False,
) -> Lesson | None:
    """Erstellt eine Lektion mit Content-Seiten."""

    lesson_number = data["lesson_number"]
    source = data.get("source", "Minna No Nihongo")
    title = f"MNN L{lesson_number}: {data['title']}"

    existing = None if dry_run else Lesson.query.filter_by(title=title).first()
    if existing:
        print(f"  [SKIP] Lesson '{title}' existiert bereits (ID {existing.id})")
        return existing

    if dry_run:
        print(f"  [DRY] Lesson: {title}")
        print(f"        Seite 1: {len(vocab_items)} Vokabeln")
        print(f"        Seite 2: {len(grammar_items)} Grammatik-Punkte")
        print(f"        Seite 3: Konversation")
        return None

    # Lektion erstellen
    lesson = Lesson(
        title=title,
        description=data.get("description", ""),
        lesson_type="free",
        category_id=category.id,
        difficulty_level=1,
        order_index=lesson_number,
        is_published=True,
        allow_guest_access=True,
        instruction_language="english",
        price=0.0,
        is_purchasable=False,
    )
    db.session.add(lesson)
    db.session.flush()
    print(f"  [NEW] Lesson: {title} (ID {lesson.id})")

    # --- Seite 1: Vokabeln ---
    page1 = LessonPage(lesson_id=lesson.id, page_number=1, title="Vocabulary")
    db.session.add(page1)

    # Intro-Text
    intro = LessonContent(
        lesson_id=lesson.id,
        content_type="text",
        title=f"Lesson {lesson_number} — Vocabulary",
        content_text=f"Vokabeln aus {source}, Lektion {lesson_number}.",
        page_number=1,
        order_index=0,
    )
    db.session.add(intro)

    for idx, vocab in enumerate(vocab_items, start=1):
        content = LessonContent(
            lesson_id=lesson.id,
            content_type="vocabulary",
            content_id=vocab.id,
            page_number=1,
            order_index=idx,
        )
        db.session.add(content)

    # --- Seite 2: Grammatik ---
    page2 = LessonPage(lesson_id=lesson.id, page_number=2, title="Grammar")
    db.session.add(page2)

    grammar_intro = LessonContent(
        lesson_id=lesson.id,
        content_type="text",
        title=f"Lesson {lesson_number} — Grammar",
        content_text=f"Grammatik aus {source}, Lektion {lesson_number}.",
        page_number=2,
        order_index=0,
    )
    db.session.add(grammar_intro)

    for idx, gram in enumerate(grammar_items, start=1):
        content = LessonContent(
            lesson_id=lesson.id,
            content_type="grammar",
            content_id=gram.id,
            page_number=2,
            order_index=idx,
        )
        db.session.add(content)

    # --- Seite 3: Konversation (Haupt- + Zusatzdialoge) ---
    conv = data.get("conversation")
    if conv:
        page3 = LessonPage(lesson_id=lesson.id, page_number=3, title="Conversation")
        db.session.add(page3)

        # Hauptkonversation
        conv_content = LessonContent(
            lesson_id=lesson.id,
            content_type="text",
            title=conv.get("title", "Conversation"),
            content_text=_format_conversation(conv),
            page_number=3,
            order_index=0,
        )
        db.session.add(conv_content)

        # Zusätzliche Konversationen
        for idx, extra_conv in enumerate(data.get("additional_conversations", []), start=1):
            situation = extra_conv.get("situation", "")
            title_text = extra_conv.get("title", f"Conversation {idx + 1}")
            if situation:
                title_text = f"{title_text} — {situation}"

            extra_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title=title_text,
                content_text=_format_conversation(extra_conv),
                page_number=3,
                order_index=idx,
            )
            db.session.add(extra_content)
            print(f"  [NEW] Conversation: {title_text}")

    return lesson


def import_audio_for_lesson(
    lesson: Lesson,
    lesson_number: int,
    source: str,
    dry_run: bool = False,
) -> int:
    """Kopiert Audio-Dateien und erstellt LessonContent-Einträge."""
    # Bestimme Audio-Quellverzeichnis
    for key, path in MNN_AUDIO_PATHS.items():
        if key in source:
            audio_dir = path
            break
    else:
        print("  [WARN] Kein Audio-Verzeichnis gefunden")
        return 0

    if not audio_dir.exists():
        print(f"  [WARN] Audio-Verzeichnis nicht gefunden: {audio_dir}")
        return 0

    # Finde alle Audio-Dateien für diese Lektion (Format: "01 - 01 - Kotoba.mp3")
    prefix = f"{lesson_number:02d} - "
    audio_files = sorted([f for f in audio_dir.iterdir() if f.name.startswith(prefix)])

    if not audio_files:
        print(f"  [WARN] Keine Audio-Dateien mit Prefix '{prefix}' gefunden")
        return 0

    # Ziel-Verzeichnis erstellen
    lesson_audio_dir = UPLOADS_DIR / f"mnn_lesson_{lesson_number:02d}"
    if not dry_run:
        lesson_audio_dir.mkdir(parents=True, exist_ok=True)

    # Prüfe ob Audio-Seite schon existiert
    if not dry_run:
        existing_audio = LessonContent.query.filter_by(
            lesson_id=lesson.id, content_type="audio"
        ).first()
        if existing_audio:
            print(f"  [SKIP] Audio bereits vorhanden für Lesson {lesson.id}")
            return 0

    # Audio-Seite erstellen (nach den bestehenden Seiten)
    max_page = 4  # Nach Vocabulary(1), Grammar(2), Conversation(3)
    if not dry_run:
        page = LessonPage(lesson_id=lesson.id, page_number=max_page, title="Audio")
        db.session.add(page)

    count = 0
    for idx, audio_file in enumerate(audio_files):
        # Label bestimmen
        # Dateiname: "01 - 03 - Reibun.mp3" → "Reibun"
        parts = audio_file.stem.split(" - ")
        audio_type = parts[-1].strip() if len(parts) >= 3 else audio_file.stem
        label = AUDIO_LABELS.get(audio_type, f"{audio_type} (Audio)")

        if dry_run:
            print(f"  [DRY] Audio: {label} ← {audio_file.name}")
            count += 1
            continue

        # Datei kopieren
        dest = lesson_audio_dir / audio_file.name
        if not dest.exists():
            shutil.copy2(audio_file, dest)

        # Relativer Pfad für DB (ab static/)
        # file_path ohne 'uploads/' Prefix, da Template 'uploads/' + file_path macht
        rel_path = f"lessons/audio/mnn_lesson_{lesson_number:02d}/{audio_file.name}"

        content = LessonContent(
            lesson_id=lesson.id,
            content_type="audio",
            title=label,
            media_url=f"/static/uploads/{rel_path}",
            file_path=rel_path,
            file_type="audio/mpeg",
            original_filename=audio_file.name,
            file_size=audio_file.stat().st_size,
            page_number=max_page,
            order_index=idx,
        )
        db.session.add(content)
        print(f"  [NEW] Audio: {label} ({audio_file.name})")
        count += 1

    return count


def import_lesson_file(filepath: Path, dry_run: bool = False) -> None:
    """Importiert eine einzelne JSON-Datei."""
    print(f"\n{'='*60}")
    print(f"Importiere: {filepath.name}")
    print(f"{'='*60}")

    data = load_json(filepath)
    source = data.get("source", "Minna No Nihongo")

    # Kategorie bestimmen
    if "Beginner I" in source:
        cat_name = "MNN Beginner I"
        cat_color = "#28a745"
        course_title = "Minna No Nihongo — Beginner I (Lektionen 1–25)"
    elif "Beginner II" in source:
        cat_name = "MNN Beginner II"
        cat_color = "#17a2b8"
        course_title = "Minna No Nihongo — Beginner II (Lektionen 26–50)"
    elif "Intermediate I" in source:
        cat_name = "MNN Intermediate I"
        cat_color = "#ffc107"
        course_title = "Minna No Nihongo — Intermediate I"
    else:
        cat_name = "MNN Intermediate II"
        cat_color = "#dc3545"
        course_title = "Minna No Nihongo — Intermediate II"

    if not dry_run:
        category = get_or_create_category(cat_name, f"Lektionen aus {source}", cat_color)
        course = get_or_create_course(course_title, f"Alle Lektionen aus {source}")
    else:
        category = None
        course = None

    # 1. Vokabeln importieren
    print("\n--- Vocabulary ---")
    vocab_items = import_vocabulary(data, dry_run)

    # 2. Grammatik importieren
    print("\n--- Grammar ---")
    grammar_items = import_grammar(data, dry_run)

    # 3. Lektion erstellen
    print("\n--- Lesson ---")
    if not dry_run:
        lesson = create_lesson(data, vocab_items, grammar_items, category, dry_run)

        # Lektion zum Kurs hinzufügen
        if lesson and course:
            existing_link = db.session.execute(
                course_lessons.select().where(
                    course_lessons.c.course_id == course.id,
                    course_lessons.c.lesson_id == lesson.id,
                )
            ).first()
            if not existing_link:
                db.session.execute(
                    course_lessons.insert().values(
                        course_id=course.id, lesson_id=lesson.id
                    )
                )
                print(f"  [LINK] Lesson → Kurs '{course.title}'")
    else:
        lesson = create_lesson(data, vocab_items, grammar_items, None, dry_run)

    # 4. Audio importieren
    print("\n--- Audio ---")
    lesson_number = data["lesson_number"]
    if not dry_run and lesson:
        audio_count = import_audio_for_lesson(lesson, lesson_number, source, dry_run)
    else:
        audio_count = import_audio_for_lesson(None, lesson_number, source, dry_run=True)

    # Zusammenfassung
    print(f"\n--- Zusammenfassung ---")
    print(f"  Vokabeln:  {len(data.get('vocabulary', []) + data.get('vocabulary_countries', []))}")
    print(f"  Grammatik: {len(data.get('grammar', []))}")
    if data.get("conversation"):
        extra_count = len(data.get("additional_conversations", []))
        print(f"  Konversation: {data['conversation'].get('title', '?')} + {extra_count} Zusatzdialoge")
    print(f"  Audio:     {audio_count} Dateien")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Minna No Nihongo → DB Import")
    parser.add_argument("files", nargs="*", help="JSON-Dateien (Standard: alle in mnn_data/)")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht schreiben")
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        # Dateien bestimmen
        if args.files:
            files = [DATA_DIR / f for f in args.files]
        else:
            files = sorted(DATA_DIR.glob("*.json"))

        if not files:
            print("Keine JSON-Dateien gefunden in", DATA_DIR)
            sys.exit(1)

        print(f"Modus: {'DRY RUN' if args.dry_run else 'LIVE IMPORT'}")
        print(f"Dateien: {len(files)}")

        for filepath in files:
            if not filepath.exists():
                print(f"FEHLER: {filepath} nicht gefunden")
                continue
            import_lesson_file(filepath, dry_run=args.dry_run)

        if not args.dry_run:
            db.session.commit()
            print(f"\n{'='*60}")
            print("COMMIT erfolgreich! Alle Daten gespeichert.")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("DRY RUN — keine Änderungen vorgenommen.")
            print(f"{'='*60}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generiert KI-basierte Quizzes für MNN-Lektionen.
Vorschlag 4: Pro Thema ein Quiz (Vokabeln, Grammatik, Konversation).

Verwendung:
    python scripts/generate_quizzes.py                    # Lektion 1
    python scripts/generate_quizzes.py --lesson 5         # Lektion 5
    python scripts/generate_quizzes.py --dry-run          # Nur AI-Output anzeigen
"""
import json
import os
import sys
import io
from pathlib import Path

# Windows: UTF-8 (nicht unter pytest, da es Capture stoert)
if sys.platform == "win32" and "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")

DATA_DIR = PROJECT_ROOT / "scripts" / "mnn_data"


def load_lesson_data(lesson_num: int) -> dict:
    """Lädt JSON-Daten für eine Lektion."""
    json_file = DATA_DIR / f"beginner1_lesson{lesson_num:02d}.json"
    if not json_file.exists():
        candidates = list(DATA_DIR.glob(f"*lesson{lesson_num:02d}*.json"))
        if candidates:
            json_file = candidates[0]
        else:
            raise FileNotFoundError(f"Keine JSON-Datei für Lektion {lesson_num}")
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def build_vocab_keywords(data: dict) -> str:
    """Baut Keywords aus Vokabeln für die AI."""
    vocab = data.get("vocabulary", [])
    parts = []
    for v in vocab:
        parts.append(f"{v['word']} ({v['reading']}) = {v['meaning']}")
    return ", ".join(parts)


def build_grammar_keywords(data: dict) -> str:
    """Baut Keywords aus Grammatik für die AI."""
    grammar = data.get("grammar", [])
    parts = []
    for g in grammar:
        parts.append(f"{g['title']}: {g.get('structure', '')}")
    return ", ".join(parts)


def build_conversation_keywords(data: dict) -> str:
    """Baut Keywords aus Konversation für die AI."""
    conv = data.get("conversation", {})
    lines = conv.get("lines", [])
    parts = []
    for line in lines:
        parts.append(f"{line['speaker']}: {line['japanese']} ({line.get('romaji', '')}) = {line['english']}")
    return "; ".join(parts)


def save_quiz_to_db(lesson, page_number: int, title: str, quiz_result: dict,
                    max_attempts: int = 3, passing_score: int = 70,
                    order_index_start: int = 900):
    """Speichert generierte Quiz-Fragen in die DB.

    Args:
        max_attempts: 0 = unbegrenzt (Practice), 3 = Standard (Test)
        passing_score: 0 = kein Bestehen noetig (Practice), 70 = Standard
        order_index_start: Basis-order_index fuer die Fragen
    """
    from app import db
    from app.models import LessonContent, QuizQuestion, QuizOption

    questions = quiz_result.get("questions", [])
    if not questions:
        print(f"  WARNUNG: Keine Fragen erhalten fuer '{title}'")
        return 0

    count = 0
    for q in questions:
        q_type = q["question_type"]
        # LessonContent erstellen (Container fuer die Frage)
        content = LessonContent(
            lesson_id=lesson.id,
            content_type="interactive",
            title=f"Quiz: {q['question_text'][:60]}",
            is_interactive=True,
            max_attempts=max_attempts,
            passing_score=passing_score,
            page_number=page_number,
            order_index=order_index_start + count,  # Nach dem regulaeren Content
        )
        db.session.add(content)
        db.session.flush()

        # QuizQuestion erstellen
        explanation = q.get("overall_explanation") or q.get("explanation", "")
        question = QuizQuestion(
            lesson_content_id=content.id,
            question_type=q_type,
            question_text=q["question_text"],
            explanation=explanation,
            hint=q.get("hint", ""),
            difficulty_level=q.get("difficulty_level", 1),
            points=q.get("points", 1),
        )
        db.session.add(question)
        db.session.flush()

        # Optionen erstellen je nach Typ
        if q_type == "multiple_choice":
            for i, opt in enumerate(q.get("options", [])):
                option = QuizOption(
                    question_id=question.id,
                    option_text=opt["text"],
                    is_correct=opt.get("is_correct", False),
                    order_index=i,
                    feedback=opt.get("feedback", ""),
                )
                db.session.add(option)

        elif q_type == "true_false":
            correct = q.get("correct_answer", True)
            db.session.add(QuizOption(
                question_id=question.id,
                option_text="True",
                is_correct=correct is True,
                order_index=0,
            ))
            db.session.add(QuizOption(
                question_id=question.id,
                option_text="False",
                is_correct=correct is False,
                order_index=1,
            ))

        elif q_type == "matching":
            for i, pair in enumerate(q.get("pairs", [])):
                option = QuizOption(
                    question_id=question.id,
                    option_text=pair["prompt"],
                    is_correct=True,
                    order_index=i,
                    feedback=pair["answer"],  # feedback = korrekte Zuordnung
                )
                db.session.add(option)

        print(f"  [NEW] {q_type}: {q['question_text'][:70]}")
        count += 1

    return count


def check_existing_quizzes(lesson, page_number: int) -> int:
    """Prueft ob bereits Quizzes fuer eine Seite existieren. Gibt Anzahl zurueck."""
    from app.models import LessonContent
    existing = LessonContent.query.filter_by(
        lesson_id=lesson.id,
        is_interactive=True,
        page_number=page_number,
    ).count()
    return existing


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Quiz-Generierung für MNN-Lektionen")
    parser.add_argument("--lesson", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Bestehende Quizzes ueberschreiben (loescht alte, generiert neu)")
    parser.add_argument("--pages", type=str, default="1,2,3,4,5",
                        help="Komma-getrennte Seitennummern (z.B. '4,5' für nur Practice+Test)")
    args = parser.parse_args()
    target_pages = [int(p.strip()) for p in args.pages.split(",")]

    lesson_num = args.lesson
    data = load_lesson_data(lesson_num)

    print("=" * 60)
    print(f"Quiz-Generierung: Lektion {lesson_num}")
    print(f"Modus: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)

    from app import create_app, db
    from app.models import Lesson
    from app.ai_services import AILessonContentGenerator

    app = create_app()

    with app.app_context():
        # Lektion finden
        lesson = Lesson.query.filter(Lesson.title.like(f"MNN L{lesson_num}:%")).first()
        if not lesson:
            print(f"FEHLER: Lektion {lesson_num} nicht in DB!")
            sys.exit(1)
        print(f"Lektion: {lesson.title} (ID {lesson.id})")

        # Duplikat-Schutz: Bestehende Quizzes pruefen
        if not args.dry_run:
            from app.models import LessonContent, QuizQuestion, QuizOption
            pages_to_skip = []
            for p in target_pages:
                existing_count = check_existing_quizzes(lesson, p)
                if existing_count > 0:
                    if args.force:
                        # --force: Bestehende Quizzes loeschen
                        existing_items = LessonContent.query.filter_by(
                            lesson_id=lesson.id,
                            is_interactive=True,
                            page_number=p,
                        ).all()
                        for item in existing_items:
                            # Zugehoerige QuizQuestions + Options loeschen
                            for qq in QuizQuestion.query.filter_by(lesson_content_id=item.id).all():
                                QuizOption.query.filter_by(question_id=qq.id).delete()
                                db.session.delete(qq)
                            db.session.delete(item)
                        db.session.flush()
                        print(f"  [FORCE] Seite {p}: {existing_count} bestehende Quizzes geloescht")
                    else:
                        print(f"  [SKIP] Seite {p}: Bereits {existing_count} Quizzes vorhanden (--force zum Ueberschreiben)")
                        pages_to_skip.append(p)
            target_pages = [p for p in target_pages if p not in pages_to_skip]
            if not target_pages:
                print("\nAlle Seiten haben bereits Quizzes. Nichts zu tun.")
                print("Tipp: --force verwenden um bestehende Quizzes zu ueberschreiben.")
                return

        # LessonPages fuer Practice (4) und Test (5) sicherstellen
        if not args.dry_run:
            from app.models import LessonPage
            PAGE_TITLES = {4: "Practice", 5: "Test"}
            for pn, ptitle in PAGE_TITLES.items():
                if pn in target_pages:
                    existing_page = LessonPage.query.filter_by(
                        lesson_id=lesson.id, page_number=pn
                    ).first()
                    if not existing_page:
                        new_page = LessonPage(lesson_id=lesson.id, page_number=pn, title=ptitle)
                        db.session.add(new_page)
                        db.session.flush()
                        print(f"  [NEW] LessonPage: Seite {pn} ({ptitle})")

        ai = AILessonContentGenerator()

        # Keywords vorbereiten
        vocab_keywords = build_vocab_keywords(data)
        grammar_keywords = build_grammar_keywords(data)
        conv_keywords = build_conversation_keywords(data)
        all_keywords = f"VOCABULARY: {vocab_keywords}\nGRAMMAR: {grammar_keywords}\nCONVERSATION: {conv_keywords}"

        # === Seite 1: Vokabel-Quiz (3x Multiple Choice) ===
        if 1 in target_pages:
            print(f"\n--- Seite 1: Vokabel-Quiz ---")
            vocab_topic = f"Japanese Vocabulary from Minna No Nihongo Lesson {lesson_num}: {data['title']}"

            vocab_result = ai.generate_page_quiz_batch(
                topic=vocab_topic,
                difficulty=1,
                keywords=vocab_keywords,
                quiz_specifications=[
                    {"type": "multiple_choice", "count": 3},
                ],
            )

            if "error" in vocab_result:
                print(f"  FEHLER: {vocab_result['error']}")
            else:
                print(f"  {len(vocab_result.get('questions', []))} Fragen generiert")
                if args.dry_run:
                    print(json.dumps(vocab_result, indent=2, ensure_ascii=False))
                else:
                    saved = save_quiz_to_db(lesson, page_number=1, title="Vocabulary Quiz", quiz_result=vocab_result)
                    print(f"  {saved} Fragen gespeichert.")

        # === Seite 2: Grammatik-Quiz (2x True/False + 1x Multiple Choice) ===
        if 2 in target_pages:
            print(f"\n--- Seite 2: Grammatik-Quiz ---")
            grammar_topic = f"Japanese Grammar from Minna No Nihongo Lesson {lesson_num}: Particles は, じゃありません, か, も, の"

            grammar_result = ai.generate_page_quiz_batch(
                topic=grammar_topic,
                difficulty=1,
                keywords=grammar_keywords,
                quiz_specifications=[
                    {"type": "true_false", "count": 2},
                    {"type": "multiple_choice", "count": 1},
                ],
            )

            if "error" in grammar_result:
                print(f"  FEHLER: {grammar_result['error']}")
            else:
                print(f"  {len(grammar_result.get('questions', []))} Fragen generiert")
                if args.dry_run:
                    print(json.dumps(grammar_result, indent=2, ensure_ascii=False))
                else:
                    saved = save_quiz_to_db(lesson, page_number=2, title="Grammar Quiz", quiz_result=grammar_result)
                    print(f"  {saved} Fragen gespeichert.")

        # === Seite 3: Pro Konversation ein Quiz ===
        if 3 in target_pages:
            all_convs = []
            # Hauptkonversation
            if data.get("conversation"):
                all_convs.append(data["conversation"])
            # Zusaetzliche Konversationen
            all_convs.extend(data.get("additional_conversations", []))

            for conv_idx, conv in enumerate(all_convs):
                conv_title = conv.get("title", f"Conversation {conv_idx + 1}")
                print(f"\n--- Seite 3, Dialog {conv_idx + 1}/{len(all_convs)}: {conv_title} ---")

                # Keywords aus dieser spezifischen Konversation
                conv_kw_parts = []
                for line in conv.get("lines", []):
                    conv_kw_parts.append(
                        f"{line['speaker']}: {line['japanese']} ({line.get('romaji', '')}) = {line['english']}"
                    )
                this_conv_keywords = "; ".join(conv_kw_parts)

                conv_topic = (
                    f"Japanese Conversation Quiz for Minna No Nihongo Lesson {lesson_num}: "
                    f"'{conv_title}'. Based on this specific dialogue: {this_conv_keywords}. "
                    f"Create questions that test understanding of this conversation."
                )

                conv_result = ai.generate_page_quiz_batch(
                    topic=conv_topic,
                    difficulty=1,
                    keywords=this_conv_keywords,
                    quiz_specifications=[
                        {"type": "multiple_choice", "count": 1},
                    ],
                )

                if "error" in conv_result:
                    print(f"  FEHLER: {conv_result['error']}")
                else:
                    print(f"  {len(conv_result.get('questions', []))} Fragen generiert")
                    if args.dry_run:
                        print(json.dumps(conv_result, indent=2, ensure_ascii=False))
                    else:
                        saved = save_quiz_to_db(
                            lesson, page_number=3,
                            title=f"Quiz: {conv_title}",
                            quiz_result=conv_result,
                            order_index_start=900 + conv_idx * 10,
                        )
                        print(f"  {saved} Fragen gespeichert.")

        # === Seite 4: Practice — Übungsfragen (formativ, unbegrenzte Versuche) ===
        if 4 in target_pages:
            print(f"\n--- Seite 4: Practice (Uebungsfragen) ---")
            practice_topic = (
                f"Practice exercises for Minna No Nihongo Lesson {lesson_num}: {data['title']}. "
                f"This is a PRACTICE page — questions should reinforce vocabulary, grammar and "
                f"conversation patterns from this lesson through pattern drills and application."
            )

            practice_result = ai.generate_page_quiz_batch(
                topic=practice_topic,
                difficulty=1,
                keywords=all_keywords,
                quiz_specifications=[
                    {"type": "multiple_choice", "count": 5},
                    {"type": "true_false", "count": 3},
                    {"type": "matching", "count": 1},
                ],
            )

            if "error" in practice_result:
                print(f"  FEHLER: {practice_result['error']}")
            else:
                print(f"  {len(practice_result.get('questions', []))} Fragen generiert")
                if args.dry_run:
                    print(json.dumps(practice_result, indent=2, ensure_ascii=False))
                else:
                    saved = save_quiz_to_db(
                        lesson, page_number=4, title="Practice Quiz",
                        quiz_result=practice_result,
                        max_attempts=0,       # unbegrenzt
                        passing_score=0,      # kein Bestehen noetig
                    )
                    print(f"  {saved} Fragen gespeichert.")

        # === Seite 5: Test — Verstaendnistest (summativ, 3 Versuche, 70%) ===
        if 5 in target_pages:
            print(f"\n--- Seite 5: Test (Verstaendnistest) ---")
            test_topic = (
                f"Comprehension test for Minna No Nihongo Lesson {lesson_num}: {data['title']}. "
                f"This is a GRADED TEST — questions should assess understanding of vocabulary, "
                f"grammar rules, and conversation comprehension at a slightly higher difficulty. "
                f"Include questions that require combining multiple concepts."
            )

            test_result = ai.generate_page_quiz_batch(
                topic=test_topic,
                difficulty=2,
                keywords=all_keywords,
                quiz_specifications=[
                    {"type": "multiple_choice", "count": 5},
                    {"type": "true_false", "count": 3},
                    {"type": "matching", "count": 1},
                ],
            )

            if "error" in test_result:
                print(f"  FEHLER: {test_result['error']}")
            else:
                print(f"  {len(test_result.get('questions', []))} Fragen generiert")
                if args.dry_run:
                    print(json.dumps(test_result, indent=2, ensure_ascii=False))
                else:
                    saved = save_quiz_to_db(
                        lesson, page_number=5, title="Comprehension Test",
                        quiz_result=test_result,
                        max_attempts=3,
                        passing_score=70,
                    )
                    print(f"  {saved} Fragen gespeichert.")

        # Commit
        if not args.dry_run:
            db.session.commit()
            print(f"\n{'=' * 60}")
            print("COMMIT erfolgreich! Alle Quizzes gespeichert.")
            print("=" * 60)
        else:
            print(f"\n{'=' * 60}")
            print("DRY RUN — nichts gespeichert.")
            print("=" * 60)


if __name__ == "__main__":
    main()

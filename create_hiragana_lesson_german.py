#!/usr/bin/env python3
"""
This script creates a comprehensive, multi-page lesson on "Complete Hiragana Mastery"
in German, covering all Hiragana characters organized by vowel groups.
Each vowel group has a detailed description page followed by a quiz page.
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent, QuizQuestion, QuizOption
from app.ai_services import AILessonContentGenerator

# --- Configuration (in German) ---
LESSON_TITLE = "Vollständige Hiragana-Meisterschaft"
LESSON_DIFFICULTY = "Absoluter Anfänger"

# Complete Hiragana organized by vowel groups with German descriptions
HIRAGANA_GROUPS = {
    "vowels": {
        "characters": ["あ (a)", "い (i)", "う (u)", "え (e)", "お (o)"],
        "description": "Die fünf grundlegenden Vokale, die die Basis der gesamten japanischen Aussprache bilden."
    },
    "k_group": {
        "characters": ["か (ka)", "き (ki)", "く (ku)", "け (ke)", "こ (ko)"],
        "description": "Die K-Konsonantengruppe, kombiniert mit jedem Vokallaut."
    },
    "s_group": {
        "characters": ["さ (sa)", "し (shi)", "す (su)", "せ (se)", "そ (so)"],
        "description": "Die S-Konsonantengruppe, einschließlich der unregelmäßigen 'shi'-Aussprache."
    },
    "t_group": {
        "characters": ["た (ta)", "ち (chi)", "つ (tsu)", "て (te)", "と (to)"],
        "description": "Die T-Konsonantengruppe mit den unregelmäßigen Aussprachen 'chi' und 'tsu'."
    },
    "n_group": {
        "characters": ["な (na)", "に (ni)", "ぬ (nu)", "ね (ne)", "の (no)"],
        "description": "Die N-Konsonantengruppe mit konsistenten Aussprachemustern."
    },
    "h_group": {
        "characters": ["は (ha)", "ひ (hi)", "ふ (fu)", "へ (he)", "ほ (ho)"],
        "description": "Die H-Konsonantengruppe, einschließlich der unregelmäßigen 'fu'-Aussprache."
    },
    "m_group": {
        "characters": ["ま (ma)", "み (mi)", "む (mu)", "め (me)", "も (mo)"],
        "description": "Die M-Konsonantengruppe mit konsistenten Aussprachemustern."
    },
    "y_group": {
        "characters": ["や (ya)", "ゆ (yu)", "よ (yo)"],
        "description": "Die Y-Konsonantengruppe mit nur drei Zeichen (keine 'yi'- oder 'ye'-Laute)."
    },
    "r_group": {
        "characters": ["ら (ra)", "り (ri)", "る (ru)", "れ (re)", "ろ (ro)"],
        "description": "Die R-Konsonantengruppe mit einem weichen 'r'-Laut, ähnlich einem 'l'."
    },
    "w_group": {
        "characters": ["わ (wa)", "を (wo)", "ん (n)"],
        "description": "Die übrigen Zeichen: 'wa', der Partikel 'wo' und das eigenständige 'n'."
    }
}

def generate_pages():
    """Generate the complete page structure for all Hiragana groups in German."""
    pages = []
    page_number = 1
    
    # Introduction page (in German)
    pages.append({
        "page_number": page_number,
        "title": "Einführung in Hiragana",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "Was ist Hiragana? Eine umfassende Einführung in das japanische phonetische Schriftsystem, seine Geschichte, seinen Zweck und seine Bedeutung für das Japanischlernen. Erklären Sie, wie Hiragana Laute darstellt und für native japanische Wörter, Grammatikpartikel und Verb-Endungen verwendet wird.",
                "keywords": "hiragana, japanisches schriftsystem, phonetisch, silbenschrift, geschichte, aussprache, grammatikpartikel"
            }
        ]
    })
    page_number += 1
    
    # Generate pages for each Hiragana group (in German)
    for group_name, group_info in HIRAGANA_GROUPS.items():
        # Description page for each group
        group_title_key = group_name.replace("_", " ").title()
        if group_name == "vowels":
            group_title = "Vokale (あ, い, う, え, お)"
        elif group_name == "w_group":
            group_title = "W-Gruppe und Sonderzeichen (わ, を, ん)"
        else:
            group_title = f"{group_name.upper().replace('_GROUP', '')}-Gruppe ({', '.join(group_info['characters'][:3])}...)"
        
        # Detailed description page (in German)
        pages.append({
            "page_number": page_number,
            "title": f"{group_title} - Beschreibung",
            "content": [
                {
                    "type": "formatted_explanation",
                    "topic": f"Umfassende Erklärung der {group_title}-Zeichen: {', '.join(group_info['characters'])}. {group_info['description']}. Fügen Sie eine detaillierte Ausspracheanleitung, Grundlagen der Strichfolge, gängige Anwendungsbeispiele, Gedächtnistechniken und kulturellen Kontext hinzu. Geben Sie Beispielwörter mit diesen Zeichen an und erklären Sie alle unregelmäßigen Aussprachen oder Sonderregeln.",
                    "keywords": f"{group_name}, {', '.join(group_info['characters'])}, aussprache, strichfolge, beispiele, gedächtnistechniken"
                }
            ]
        })
        page_number += 1
        
        # Quiz page for each group (in German)
        pages.append({
            "page_number": page_number,
            "title": f"{group_title} - Quiz",
            "content": [
                {
                    "type": "multiple_choice",
                    "topic": f"Leseverständnis-Quiz für {group_title}-Zeichen. Testen Sie die Fähigkeit, die korrekte Aussprache von {', '.join(group_info['characters'][:3])} und anderen Zeichen aus dieser Gruppe zu identifizieren. Basieren Sie die Fragen auf der detaillierten Beschreibung der vorherigen Seite.",
                    "keywords": f"{group_name}, lesen, aussprache, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "multiple_choice",
                    "topic": f"Zeichenerkennungs-Quiz für {group_title}. Testen Sie die Fähigkeit, das korrekte Hiragana-Zeichen bei gegebener Aussprache zu identifizieren. Beziehen Sie Zeichen ein, die auf der vorherigen Beschreibungsseite behandelt wurden.",
                    "keywords": f"{group_name}, zeichenerkennung, hiragana, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "fill_in_the_blank",
                    "topic": f"Vervollständigen Sie die Aussprache für die {group_title}-Zeichen. Testen Sie das Wissen über die auf der Beschreibungsseite erklärten Aussprachemuster.",
                    "keywords": f"{group_name}, aussprache, lückentext, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "true_false",
                    "topic": f"Wahr-oder-Falsch-Fragen zu den Eigenschaften, Ausspracheregeln oder Verwendungsmustern der {group_title}, die auf der Beschreibungsseite behandelt wurden.",
                    "keywords": f"{group_name}, wahr falsch, ausspracheregeln, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "matching",
                    "topic": f"Ordnen Sie die {group_title} Hiragana-Zeichen ihren korrekten Aussprachen zu. Verwenden Sie Zeichen und Aussprachen, die auf der Beschreibungsseite erklärt wurden.",
                    "keywords": f"{group_name}, zuordnen, hiragana, aussprache, {', '.join(group_info['characters'])}"
                }
            ]
        })
        page_number += 1
    
    # Final review page (in German)
    pages.append({
        "page_number": page_number,
        "title": "Vollständige Hiragana-Wiederholung",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "Umfassende Wiederholung aller gelernten Hiragana-Zeichen. Zusammenfassung aller Vokalgruppen, Aussprachemuster, gebräuchlicher Verwendungen und Tipps zum weiteren Üben. Fügen Sie eine vollständige Hiragana-Tabelle als Referenz und Lernstrategien hinzu.",
                "keywords": "hiragana wiederholung, vollständige tabelle, lernstrategien, aussprachemuster, alle gruppen"
            },
            {
                "type": "multiple_choice",
                "topic": "Gemischtes Wiederholungsquiz, das Zeichen aus allen auf den vorherigen Seiten behandelten Hiragana-Gruppen abdeckt.",
                "keywords": "hiragana wiederholung, gemischtes quiz, alle gruppen, umfassend"
            },
            {
                "type": "matching",
                "topic": "Umfassende Zuordnungsübung mit Zeichen aus allen Hiragana-Gruppen.",
                "keywords": "hiragana zuordnung, umfassende wiederholung, alle zeichen"
            }
        ]
    })
    
    return pages

PAGES = generate_pages()

def create_lesson(app):
    """Creates the lesson and its content within the Flask app context."""
    with app.app_context():
        print(f"--- Erstelle Lektion: {LESSON_TITLE} ---")
        print(f"Gesamtseitenzahl zu erstellen: {len(PAGES)}")

        # Check if lesson already exists and delete it
        existing_lesson = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing_lesson:
            print(f"Bestehende Lektion '{LESSON_TITLE}' (ID: {existing_lesson.id}) gefunden. Wird gelöscht.")
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Bestehende Lektion gelöscht.")

        # Create the lesson (in German)
        lesson = Lesson(
            title=LESSON_TITLE,
            description="Eine umfassende, mehrseitige Lektion zur Beherrschung aller Hiragana-Zeichen, geordnet nach Vokalgruppen. Jede Gruppe enthält detaillierte Erklärungen, gefolgt von gezielten Quizfragen.",
            lesson_type="free",
            difficulty_level=1, # Absoluter Anfänger
            is_published=True
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lektion '{LESSON_TITLE}' erstellt mit ID: {lesson.id}")

        # Initialize AI generator
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI-Generator konnte nicht initialisiert werden. Überprüfen Sie Ihren API-Schlüssel.")
            return

        # Create pages and content
        for page_info in PAGES:
            print(f"\n--- Erstelle Seite {page_info['page_number']}: {page_info['title']} ---")
            
            lesson_page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_info['page_number'],
                title=page_info['title'],
                description=f"Diese Seite behandelt: {page_info['title']}"
            )
            db.session.add(lesson_page)
            
            order_index = 0
            for content_info in page_info['content']:
                content_type = content_info['type']
                topic = content_info['topic']
                keywords = content_info['keywords']
                
                print(f"🤖 Generiere {content_type} für '{topic[:60]}...'")
                
                result = None
                if content_type == 'formatted_explanation':
                    result = generator.generate_formatted_explanation(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'multiple_choice':
                    result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'true_false':
                    result = generator.generate_true_false_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'fill_in_the_blank':
                    result = generator.generate_fill_in_the_blank_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'matching':
                    result = generator.generate_matching_question(topic, LESSON_DIFFICULTY, keywords)

                if not result or "error" in result:
                    error_msg = result.get('error', 'Unbekannter Fehler') if result else 'Kein Ergebnis zurückgegeben'
                    print(f"❌ Fehler beim Generieren von {content_type}: {error_msg}")
                    continue

                # --- Create LessonContent ---
                if content_type == 'formatted_explanation':
                    content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="text",
                        title=f"Erklärung: {page_info['title']}",
                        content_text=result['generated_text'],
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4.5-preview", **content_info}
                    )
                    db.session.add(content)
                    print(f"✅ Formatierte Erklärung hinzugefügt.")
                else: # It's a quiz
                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="interactive",
                        title=f"Quiz: {result.get('question_text', topic)[:40]}...",
                        is_interactive=True,
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4.5-preview", **content_info}
                    )
                    db.session.add(quiz_content)
                    db.session.flush()

                    question = None
                    if content_type == 'multiple_choice':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="multiple_choice",
                            question_text=result['question_text'],
                            explanation=result['overall_explanation']
                        )
                        db.session.add(question)
                        db.session.flush()
                        for option_data in result['options']:
                            db.session.add(QuizOption(question_id=question.id, option_text=option_data['text'], is_correct=option_data['is_correct'], feedback=option_data.get('feedback', '')))
                    
                    elif content_type == 'true_false':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="true_false",
                            question_text=result['question_text'],
                            explanation=result['explanation']
                        )
                        db.session.add(question)
                        db.session.flush()
                        db.session.add(QuizOption(question_id=question.id, option_text="Wahr", is_correct=result['is_true']))
                        db.session.add(QuizOption(question_id=question.id, option_text="Falsch", is_correct=not result['is_true']))

                    elif content_type == 'fill_in_the_blank':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="fill_blank",
                            question_text=result['question_text'],
                            explanation=result['explanation']
                        )
                        db.session.add(question)
                        db.session.flush()
                        db.session.add(QuizOption(question_id=question.id, option_text=result['correct_answer'], is_correct=True))

                    elif content_type == 'matching':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="matching",
                            question_text=result['question_text'],
                            explanation=result.get('explanation', ''),
                        )
                        db.session.add(question)
                        db.session.flush()
                        for pair in result['pairs']:
                            db.session.add(QuizOption(question_id=question.id, option_text=pair['prompt'], feedback=pair['answer'], is_correct=True))

                    print(f"✅ {content_type.replace('_', ' ').title()}-Quiz hinzugefügt.")

                order_index += 1

        db.session.commit()
        print(f"\n--- Erstellung der Lektion abgeschlossen! ---")
        print(f"Erstellt wurden {len(PAGES)} Seiten, die alle Hiragana-Zeichen abdecken.")
        print("Jede Vokalgruppe hat eine detaillierte Beschreibungsseite, gefolgt von umfassenden Quizfragen.")

if __name__ == "__main__":
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Fehler: Die Umgebungsvariable OPENAI_API_KEY ist nicht gesetzt.")
        sys.exit(1)

    app = create_app()
    create_lesson(app)
#!/usr/bin/env python3
"""
This script creates a comprehensive, multi-page lesson on "Complete Hiragana Mastery"
covering all Hiragana characters organized by vowel groups.
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

# --- Configuration ---
LESSON_TITLE = "Complete Hiragana Mastery"
LESSON_DIFFICULTY = "Absolute Beginner"

# Complete Hiragana organized by vowel groups
HIRAGANA_GROUPS = {
    "vowels": {
        "characters": ["あ (a)", "い (i)", "う (u)", "え (e)", "お (o)"],
        "description": "The five fundamental vowel sounds that form the foundation of all Japanese pronunciation"
    },
    "k_group": {
        "characters": ["か (ka)", "き (ki)", "く (ku)", "け (ke)", "こ (ko)"],
        "description": "The K-consonant group combined with each vowel sound"
    },
    "s_group": {
        "characters": ["さ (sa)", "し (shi)", "す (su)", "せ (se)", "そ (so)"],
        "description": "The S-consonant group, including the irregular 'shi' pronunciation"
    },
    "t_group": {
        "characters": ["た (ta)", "ち (chi)", "つ (tsu)", "て (te)", "と (to)"],
        "description": "The T-consonant group with irregular pronunciations 'chi' and 'tsu'"
    },
    "n_group": {
        "characters": ["な (na)", "に (ni)", "ぬ (nu)", "ね (ne)", "の (no)"],
        "description": "The N-consonant group with consistent pronunciation patterns"
    },
    "h_group": {
        "characters": ["は (ha)", "ひ (hi)", "ふ (fu)", "へ (he)", "ほ (ho)"],
        "description": "The H-consonant group, including the irregular 'fu' pronunciation"
    },
    "m_group": {
        "characters": ["ま (ma)", "み (mi)", "む (mu)", "め (me)", "も (mo)"],
        "description": "The M-consonant group with consistent pronunciation patterns"
    },
    "y_group": {
        "characters": ["や (ya)", "ゆ (yu)", "よ (yo)"],
        "description": "The Y-consonant group with only three characters (no 'yi' or 'ye' sounds)"
    },
    "r_group": {
        "characters": ["ら (ra)", "り (ri)", "る (ru)", "れ (re)", "ろ (ro)"],
        "description": "The R-consonant group with a soft 'r' sound similar to 'l'"
    },
    "w_group": {
        "characters": ["わ (wa)", "を (wo)", "ん (n)"],
        "description": "The remaining characters: 'wa', the particle 'wo', and the standalone 'n'"
    }
}

def generate_pages():
    """Generate the complete page structure for all Hiragana groups."""
    pages = []
    page_number = 1
    
    # Introduction page
    pages.append({
        "page_number": page_number,
        "title": "Introduction to Hiragana",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "What is Hiragana? A comprehensive introduction to the Japanese phonetic writing system, its history, purpose, and importance in learning Japanese. Explain how Hiragana represents sounds and is used for native Japanese words, grammar particles, and verb endings.",
                "keywords": "hiragana, japanese writing system, phonetic, syllabary, history, pronunciation, grammar particles"
            }
        ]
    })
    page_number += 1
    
    # Generate pages for each Hiragana group
    for group_name, group_info in HIRAGANA_GROUPS.items():
        # Description page for each group
        group_title = group_name.replace("_", " ").title()
        if group_name == "vowels":
            group_title = "Vowels (あ, い, う, え, お)"
        elif group_name == "w_group":
            group_title = "W Group and Special Characters (わ, を, ん)"
        else:
            group_title = f"{group_name.upper().replace('_', '')} Group ({', '.join(group_info['characters'][:3])}...)"
        
        # Detailed description page
        pages.append({
            "page_number": page_number,
            "title": f"{group_title} - Description",
            "content": [
                {
                    "type": "formatted_explanation",
                    "topic": f"Comprehensive explanation of the {group_title} characters: {', '.join(group_info['characters'])}. {group_info['description']}. Include detailed pronunciation guide, stroke order basics, common usage examples, memory techniques, and cultural context. Provide example words using these characters and explain any irregular pronunciations or special rules.",
                    "keywords": f"{group_name}, {', '.join(group_info['characters'])}, pronunciation, stroke order, examples, memory techniques"
                }
            ]
        })
        page_number += 1
        
        # Quiz page for each group
        pages.append({
            "page_number": page_number,
            "title": f"{group_title} - Quiz",
            "content": [
                {
                    "type": "multiple_choice",
                    "topic": f"Reading recognition quiz for {group_title} characters. Test ability to identify the correct pronunciation of {', '.join(group_info['characters'][:3])} and other characters from this group. Base questions on the detailed description from the previous page.",
                    "keywords": f"{group_name}, reading, pronunciation, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "multiple_choice",
                    "topic": f"Character recognition quiz for {group_title}. Test ability to identify the correct Hiragana character when given the pronunciation. Include characters covered in the previous description page.",
                    "keywords": f"{group_name}, character recognition, hiragana, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "fill_in_the_blank",
                    "topic": f"Complete the pronunciation for {group_title} characters. Test knowledge of pronunciation patterns explained in the description page.",
                    "keywords": f"{group_name}, pronunciation, fill blank, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "true_false",
                    "topic": f"True or false questions about {group_title} characteristics, pronunciation rules, or usage patterns covered in the description page.",
                    "keywords": f"{group_name}, true false, pronunciation rules, {', '.join(group_info['characters'])}"
                },
                {
                    "type": "matching",
                    "topic": f"Match {group_title} Hiragana characters to their correct pronunciations. Use characters and pronunciations explained in the description page.",
                    "keywords": f"{group_name}, matching, hiragana, pronunciation, {', '.join(group_info['characters'])}"
                }
            ]
        })
        page_number += 1
    
    # Final review page
    pages.append({
        "page_number": page_number,
        "title": "Complete Hiragana Review",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "Comprehensive review of all Hiragana characters learned. Summary of all vowel groups, pronunciation patterns, common usage, and tips for continued practice. Include a complete Hiragana chart reference and study strategies.",
                "keywords": "hiragana review, complete chart, study strategies, pronunciation patterns, all groups"
            },
            {
                "type": "multiple_choice",
                "topic": "Mixed review quiz covering characters from all Hiragana groups studied in previous pages.",
                "keywords": "hiragana review, mixed quiz, all groups, comprehensive"
            },
            {
                "type": "matching",
                "topic": "Comprehensive matching exercise with characters from all Hiragana groups.",
                "keywords": "hiragana matching, comprehensive review, all characters"
            }
        ]
    })
    
    return pages

PAGES = generate_pages()

def create_lesson(app):
    """Creates the lesson and its content within the Flask app context."""
    with app.app_context():
        print(f"--- Creating Lesson: {LESSON_TITLE} ---")
        print(f"Total pages to create: {len(PAGES)}")

        # Check if lesson already exists and delete it
        existing_lesson = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing_lesson:
            print(f"Found existing lesson '{LESSON_TITLE}' (ID: {existing_lesson.id}). Deleting it.")
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson deleted.")

        # Create the lesson
        lesson = Lesson(
            title=LESSON_TITLE,
            description="A comprehensive, multi-page lesson to master all Hiragana characters organized by vowel groups. Each group has detailed explanations followed by targeted quizzes.",
            lesson_type="free",
            difficulty_level=1, # Absolute Beginner
            is_published=True
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lesson '{LESSON_TITLE}' created with ID: {lesson.id}")

        # Initialize AI generator
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return

        # Create pages and content
        for page_info in PAGES:
            print(f"\n--- Creating Page {page_info['page_number']}: {page_info['title']} ---")
            
            lesson_page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_info['page_number'],
                title=page_info['title'],
                description=f"This page covers: {page_info['title']}"
            )
            db.session.add(lesson_page)
            
            order_index = 0
            for content_info in page_info['content']:
                content_type = content_info['type']
                topic = content_info['topic']
                keywords = content_info['keywords']
                
                print(f"🤖 Generating {content_type} for '{topic[:60]}...'")
                
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
                    print(f"❌ Error generating {content_type}: {result.get('error', 'Unknown error') if result else 'No result returned'}")
                    continue

                # --- Create LessonContent ---
                if content_type == 'formatted_explanation':
                    content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="text",
                        title=f"Explanation: {page_info['title']}",
                        content_text=result['generated_text'],
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4o", **content_info}
                    )
                    db.session.add(content)
                    print(f"✅ Formatted explanation added.")
                else: # It's a quiz
                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="interactive",
                        title=f"Quiz: {result.get('question_text', topic)[:40]}...",
                        is_interactive=True,
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4o", **content_info}
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
                        db.session.add(QuizOption(question_id=question.id, option_text="True", is_correct=result['is_true']))
                        db.session.add(QuizOption(question_id=question.id, option_text="False", is_correct=not result['is_true']))

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
                        # For matching, we store the pairs as JSON in the explanation field
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="matching",
                            question_text=result['question_text'],
                            explanation=result.get('explanation', ''),
                            # Storing pairs in the question_text as a fallback if frontend needs it directly
                            # A better approach is for the frontend to parse the options
                        )
                        db.session.add(question)
                        db.session.flush()
                        # Store pairs in QuizOptions. Prompt in option_text, Answer in feedback.
                        for pair in result['pairs']:
                            db.session.add(QuizOption(question_id=question.id, option_text=pair['prompt'], feedback=pair['answer'], is_correct=True))

                    print(f"✅ {content_type.replace('_', ' ').title()} quiz added.")

                order_index += 1

        db.session.commit()
        print(f"\n--- Lesson Creation Complete! ---")
        print(f"Created {len(PAGES)} pages covering all Hiragana characters")
        print("Each vowel group has a detailed description page followed by comprehensive quizzes")

if __name__ == "__main__":
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    app = create_app()
    create_lesson(app)

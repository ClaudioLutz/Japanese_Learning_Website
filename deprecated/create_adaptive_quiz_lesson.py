import os
import sys
from datetime import datetime

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Lesson, LessonContent, QuizQuestion, QuizOption, LessonCategory
from app.ai_services import AILessonContentGenerator

def create_adaptive_quiz_lesson():
    """
    Generates a lesson with an adaptive quiz using the AI service.
    """
    app = create_app()
    with app.app_context():
        print("Starting adaptive quiz lesson creation...")

        # 1. Define Lesson Details
        lesson_title = "Advanced Particles Adaptive Quiz"
        lesson_description = "An adaptive quiz to test your knowledge of Japanese particles (は, が, を, に, で, へ, と, も)."
        lesson_difficulty = 3  # Intermediate
        lesson_topic = "Japanese Particles"
        difficulty_levels = [1, 2, 3, 4, 5]

        # 2. Find or create a category
        category_name = "Quizzes"
        category = LessonCategory.query.filter_by(name=category_name).first()
        if not category:
            print(f"Creating new category: {category_name}")
            category = LessonCategory(name=category_name, description="Interactive quizzes to test your knowledge.")
            db.session.add(category)
            db.session.commit()

        # 3. Create the Lesson
        lesson = Lesson(
            title=lesson_title,
            description=lesson_description,
            lesson_type="premium",
            category_id=category.id,
            difficulty_level=lesson_difficulty,
            is_published=True,
            instruction_language='english'
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"Created lesson: '{lesson.title}'")

        # 4. Create the Interactive Content Item (the quiz container)
        quiz_content = LessonContent(
            lesson_id=lesson.id,
            content_type='interactive',
            title='Adaptive Particle Quiz',
            order_index=1,
            page_number=1,
            is_interactive=True,
            quiz_type='adaptive',  # Set the new quiz type
            max_attempts=5,
            passing_score=80,
            generated_by_ai=True
        )
        db.session.add(quiz_content)
        db.session.commit()
        print("Created interactive content item for the quiz.")

        # 5. Generate the adaptive quiz questions using the AI service
        ai_generator = AILessonContentGenerator()
        print("Generating adaptive quiz questions from AI...")
        quiz_data = ai_generator.create_adaptive_quiz(
            topic=lesson_topic,
            difficulty_levels=difficulty_levels,
            num_questions_per_level=2
        )

        if not quiz_data or 'questions' not in quiz_data:
            print(f"Failed to generate quiz data from AI: {quiz_data.get('error', 'Unknown error')}")
            return

        # 6. Populate the quiz with questions and options
        questions = quiz_data.get('questions', [])
        if not isinstance(questions, list):
            print("AI response for questions is not a list.")
            return

        for question_data in questions:
            if not isinstance(question_data, dict):
                print(f"Skipping invalid question data: {question_data}")
                continue

            question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type='multiple_choice',
                question_text=question_data.get('question_text'),
                explanation=question_data.get('overall_explanation'),
                hint=question_data.get('hint'),
                difficulty_level=question_data.get('difficulty_level'),
                points=question_data.get('difficulty_level', 1) # More points for harder questions
            )
            db.session.add(question)
            db.session.commit()

            for option_data in question_data.get('options', []):
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data.get('text'),
                    is_correct=option_data.get('is_correct', False),
                    feedback=option_data.get('feedback')
                )
                db.session.add(option)
            db.session.commit()

        print(f"Successfully added {len(quiz_data['questions'])} questions to the quiz.")
        print("Adaptive quiz lesson creation complete!")

if __name__ == '__main__':
    create_adaptive_quiz_lesson()

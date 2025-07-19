import os
import sys
import json
from datetime import datetime

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import (
    Lesson, LessonContent, QuizQuestion, QuizOption, LessonCategory, 
    Kanji, Vocabulary, Grammar, LessonPage
)
from app.ai_services import AILessonContentGenerator

def create_comprehensive_kitsune_lesson():
    """
    Generates a complete, engaging, and interactive Japanese lesson 
    about the mythical Kitsune (狐) following the exact task requirements.
    
    This implements the full AI Lesson Architect workflow:
    - Part 1: Foundational Database Generation
    - Part 2: Main Lesson Content
    - Part 3: Multimedia Enhancement
    - Part 4: Adaptive Quiz for Knowledge Assessment
    """
    app = create_app()
    with app.app_context():
        print("=== AI Lesson Architect: The Mysteries of the Kitsune (狐) ===")
        print("Starting comprehensive Kitsune lesson creation...")
        
        ai_generator = AILessonContentGenerator()

        # Create or find category
        category_name = "Japanese Folklore"
        category = LessonCategory.query.filter_by(name=category_name).first()
        if not category:
            print(f"Creating new category: {category_name}")
            category = LessonCategory(
                name=category_name, 
                description="Lessons about Japanese myths, legends, and folklore.",
                color_code="#8B4513"  # Brown color for folklore
            )
            db.session.add(category)
            db.session.commit()

        # ===================================================================
        # PART 1: FOUNDATIONAL DATABASE GENERATION
        # ===================================================================
        print("\n" + "="*60)
        print("PART 1: FOUNDATIONAL DATABASE GENERATION")
        print("="*60)

        # 1.1. Kanji Generation
        print("\n--- 1.1. Generating Kanji Data ---")
        kanji_to_generate = [
            ('狐', 'N4'),  # fox
            ('化', 'N4'),  # change, take the form of
            ('尾', 'N3'),  # tail
            ('神', 'N4')   # god, spirit
        ]
        
        generated_kanji_ids = []
        for char, level in kanji_to_generate:
            print(f"Generating Kanji data for: {char} (JLPT {level})")
            
            # Check if kanji already exists
            existing_kanji = Kanji.query.filter_by(character=char).first()
            if existing_kanji:
                print(f"  Kanji {char} already exists in database")
                generated_kanji_ids.append(existing_kanji.id)
                continue
            
            kanji_data = ai_generator.generate_kanji_data(kanji_character=char, jlpt_level=level)
            if kanji_data and 'error' not in kanji_data:
                print(f"  Generated data: {json.dumps(kanji_data, indent=2, ensure_ascii=False)}")
                
                # Save to database
                kanji_entry = Kanji(
                    character=kanji_data['character'],
                    meaning=kanji_data['meaning'],
                    onyomi=kanji_data.get('onyomi', ''),
                    kunyomi=kanji_data.get('kunyomi', ''),
                    jlpt_level=kanji_data['jlpt_level'],
                    stroke_count=kanji_data.get('stroke_count'),
                    radical=kanji_data.get('radical', ''),
                    created_by_ai=True,
                    status='approved'
                )
                db.session.add(kanji_entry)
                db.session.commit()
                generated_kanji_ids.append(kanji_entry.id)
                print(f"  ✓ Saved Kanji {char} to database (ID: {kanji_entry.id})")
            else:
                print(f"  ✗ Failed to generate data for Kanji {char}: {kanji_data.get('error')}")

        # 1.2. Vocabulary Generation
        print("\n--- 1.2. Generating Vocabulary Data ---")
        vocab_to_generate = [
            ('狐', 'N4'),        # kitsune - fox
            ('化ける', 'N4'),     # bakeru - to shapeshift, to disguise oneself
            ('尻尾', 'N4'),      # shippo - tail
            ('稲荷大神', 'N4'),   # Inari Ōkami - the god of foxes, rice, and sake
            ('伝説', 'N4')       # densetsu - legend
        ]
        
        generated_vocab_ids = []
        for word, level in vocab_to_generate:
            print(f"Generating Vocabulary data for: {word} (JLPT {level})")
            
            # Check if vocabulary already exists
            existing_vocab = Vocabulary.query.filter_by(word=word).first()
            if existing_vocab:
                print(f"  Vocabulary {word} already exists in database")
                generated_vocab_ids.append(existing_vocab.id)
                continue
            
            vocab_data = ai_generator.generate_vocabulary_data(word=word, jlpt_level=level)
            if vocab_data and 'error' not in vocab_data:
                print(f"  Generated data: {json.dumps(vocab_data, indent=2, ensure_ascii=False)}")
                
                # Save to database
                vocab_entry = Vocabulary(
                    word=vocab_data['word'],
                    reading=vocab_data['reading'],
                    meaning=vocab_data['meaning'],
                    jlpt_level=vocab_data['jlpt_level'],
                    example_sentence_japanese=vocab_data.get('example_sentence_japanese', ''),
                    example_sentence_english=vocab_data.get('example_sentence_english', ''),
                    created_by_ai=True,
                    status='approved'
                )
                db.session.add(vocab_entry)
                db.session.commit()
                generated_vocab_ids.append(vocab_entry.id)
                print(f"  ✓ Saved Vocabulary {word} to database (ID: {vocab_entry.id})")
            else:
                print(f"  ✗ Failed to generate data for Vocabulary {word}: {vocab_data.get('error')}")

        # 1.3. Grammar Generation
        print("\n--- 1.3. Generating Grammar Data ---")
        grammar_point = "～そうです"
        print(f"Generating Grammar data for: {grammar_point} (hearsay pattern)")
        
        # Check if grammar already exists
        existing_grammar = Grammar.query.filter_by(title=grammar_point).first()
        generated_grammar_id = None
        
        if existing_grammar:
            print(f"  Grammar {grammar_point} already exists in database")
            generated_grammar_id = existing_grammar.id
        else:
            grammar_data = ai_generator.generate_grammar_data(grammar_point=grammar_point, jlpt_level='N4')
            if grammar_data and 'error' not in grammar_data:
                print(f"  Generated data: {json.dumps(grammar_data, indent=2, ensure_ascii=False)}")
                
                # Save to database
                grammar_entry = Grammar(
                    title=grammar_data['title'],
                    explanation=grammar_data['explanation'],
                    structure=grammar_data.get('structure', ''),
                    jlpt_level=grammar_data['jlpt_level'],
                    example_sentences=grammar_data.get('example_sentences', ''),
                    created_by_ai=True,
                    status='approved'
                )
                db.session.add(grammar_entry)
                db.session.commit()
                generated_grammar_id = grammar_entry.id
                print(f"  ✓ Saved Grammar {grammar_point} to database (ID: {grammar_entry.id})")
            else:
                print(f"  ✗ Failed to generate data for Grammar {grammar_point}: {grammar_data.get('error')}")

        # ===================================================================
        # PART 2: MAIN LESSON CONTENT
        # ===================================================================
        print("\n" + "="*60)
        print("PART 2: MAIN LESSON CONTENT")
        print("="*60)

        # Create the main lesson
        lesson_title = "The Mysteries of the Kitsune (狐) - Japan's Mythical Fox"
        lesson = Lesson(
            title=lesson_title,
            description="Explore the fascinating world of Kitsune, Japan's mythical foxes, their powers, types, and cultural significance.",
            lesson_type='free',
            category_id=category.id,
            difficulty_level=3,  # Intermediate
            estimated_duration=45,  # 45 minutes
            is_published=True,
            instruction_language='english'
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"✓ Created lesson: {lesson_title} (ID: {lesson.id})")

        # 2.1. Introduction
        print("\n--- 2.1. Generating Introduction ---")
        intro_topic = "The Mysteries of the Kitsune (狐) - Japan's Mythical Fox"
        introduction = ai_generator.generate_explanation(
            topic=intro_topic, 
            difficulty='intermediate',
            keywords=['Kitsune', 'fox', 'myth', 'folklore', 'Japan']
        )
        
        if introduction and 'error' not in introduction:
            print(f"Generated introduction: {introduction['generated_text'][:200]}...")
            
            # Save introduction as lesson content
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type='text',
                title='Introduction to Kitsune',
                content_text=introduction['generated_text'],
                order_index=1,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={'function': 'generate_explanation', 'topic': intro_topic}
            )
            db.session.add(intro_content)
            db.session.commit()
            print(f"  ✓ Saved introduction to database (ID: {intro_content.id})")
        else:
            print(f"  ✗ Failed to generate introduction: {introduction.get('error')}")

        # 2.2. Detailed Explanation
        print("\n--- 2.2. Generating Formatted Explanation ---")
        formatted_explanation = ai_generator.generate_formatted_explanation(
            topic=intro_topic,
            difficulty='intermediate',
            keywords=['Kitsune', 'zenko', 'yako', 'Inari', 'shapeshifting', 'magic', 'nine-tails']
        )
        
        if formatted_explanation and 'error' not in formatted_explanation:
            print(f"Generated formatted explanation: {formatted_explanation['generated_text'][:300]}...")
            
            # Save formatted explanation as lesson content
            main_content = LessonContent(
                lesson_id=lesson.id,
                content_type='text',
                title='The World of Kitsune',
                content_text=formatted_explanation['generated_text'],
                order_index=2,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={'function': 'generate_formatted_explanation', 'topic': intro_topic}
            )
            db.session.add(main_content)
            db.session.commit()
            print(f"  ✓ Saved formatted explanation to database (ID: {main_content.id})")
        else:
            print(f"  ✗ Failed to generate formatted explanation: {formatted_explanation.get('error')}")

        # ===================================================================
        # PART 3: MULTIMEDIA ENHANCEMENT
        # ===================================================================
        print("\n" + "="*60)
        print("PART 3: MULTIMEDIA ENHANCEMENT")
        print("="*60)

        # 3.1. Multimedia Analysis
        print("\n--- 3.1. Analyzing Content for Multimedia Needs ---")
        content_for_analysis = formatted_explanation.get('generated_text', '') if formatted_explanation and 'error' not in formatted_explanation else "Kitsune folklore content"
        
        multimedia_analysis = ai_generator.analyze_content_for_multimedia_needs(
            content_text=content_for_analysis,
            lesson_topic="Kitsune folklore"
        )
        
        if multimedia_analysis and 'error' not in multimedia_analysis:
            print("Multimedia analysis results:")
            print(json.dumps(multimedia_analysis, indent=2, ensure_ascii=False))
        else:
            print(f"  ✗ Failed to analyze content for multimedia: {multimedia_analysis.get('error')}")

        # 3.2. Image Generation
        print("\n--- 3.2. Generating Lesson Images ---")
        image_prompts = [
            "A mystical nine-tailed fox (kyuubi no kitsune) in a moonlit, ancient Japanese forest, traditional ukiyo-e art style, ethereal and magical atmosphere",
            "A beautiful woman in a traditional kimono whose shadow on a shoji screen reveals the silhouette of a fox, ukiyo-e style, subtle supernatural elements",
            "A serene Shinto shrine dedicated to Inari with stone fox statues (kitsune-zuka) guarding the entrance, traditional Japanese architecture, ukiyo-e art style"
        ]
        
        generated_images = []
        for i, prompt in enumerate(image_prompts, 1):
            print(f"Generating image {i}/3...")
            print(f"  Prompt: {prompt}")
            
            image_result = ai_generator.generate_single_image(
                prompt=prompt,
                size="1024x1024",
                quality="standard"
            )
            
            if image_result and 'error' not in image_result:
                print(f"  ✓ Generated image URL: {image_result['image_url']}")
                generated_images.append(image_result)
                
                # Save image as lesson content
                image_titles = [
                    "Nine-Tailed Kitsune in the Forest",
                    "Kitsune in Human Form",
                    "Inari Shrine with Fox Guardians"
                ]
                
                image_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type='image',
                    title=image_titles[i-1],
                    media_url=image_result['image_url'],
                    order_index=2 + i,
                    page_number=2,
                    generated_by_ai=True,
                    ai_generation_details={
                        'function': 'generate_single_image',
                        'prompt': prompt,
                        'size': image_result['size'],
                        'quality': image_result['quality']
                    }
                )
                db.session.add(image_content)
                db.session.commit()
                print(f"  ✓ Saved image to database (ID: {image_content.id})")
            else:
                print(f"  ✗ Failed to generate image {i}: {image_result.get('error')}")

        # ===================================================================
        # PART 4: ADAPTIVE QUIZ FOR KNOWLEDGE ASSESSMENT
        # ===================================================================
        print("\n" + "="*60)
        print("PART 4: ADAPTIVE QUIZ FOR KNOWLEDGE ASSESSMENT")
        print("="*60)

        # Create quiz content container
        quiz_content = LessonContent(
            lesson_id=lesson.id,
            content_type='text',
            title='Kitsune Knowledge Quiz',
            content_text='Test your understanding of Kitsune folklore with this adaptive quiz.',
            order_index=10,
            page_number=3,
            is_interactive=True,
            quiz_type='adaptive',
            max_attempts=3,
            passing_score=70,
            generated_by_ai=True
        )
        db.session.add(quiz_content)
        db.session.commit()
        print(f"✓ Created quiz content container (ID: {quiz_content.id})")

        # 4.1. Generate Adaptive Quiz
        print("\n--- 4.1. Generating Adaptive Quiz ---")
        quiz_data = ai_generator.create_adaptive_quiz(
            topic="Kitsune Folklore",
            difficulty_levels=['easy', 'medium'],
            num_questions_per_level=3
        )

        if quiz_data and 'questions' in quiz_data:
            print(f"✓ Generated adaptive quiz with {len(quiz_data['questions'])} questions")
            
            # Save each question to database
            for i, question_data in enumerate(quiz_data['questions']):
                print(f"\nProcessing question {i+1}: {question_data['question_text'][:50]}...")
                
                quiz_question = QuizQuestion(
                    lesson_content_id=quiz_content.id,
                    question_type='multiple_choice',
                    question_text=question_data['question_text'],
                    explanation=question_data.get('overall_explanation', ''),
                    hint=question_data.get('hint', ''),
                    difficulty_level=question_data.get('difficulty_level', 1),
                    points=1,
                    order_index=i
                )
                db.session.add(quiz_question)
                db.session.commit()
                
                # Add options
                for j, option_data in enumerate(question_data.get('options', [])):
                    quiz_option = QuizOption(
                        question_id=quiz_question.id,
                        option_text=option_data['text'],
                        is_correct=option_data['is_correct'],
                        order_index=j,
                        feedback=option_data.get('feedback', '')
                    )
                    db.session.add(quiz_option)
                
                db.session.commit()
                print(f"  ✓ Saved question with {len(question_data.get('options', []))} options")
        else:
            print(f"  ✗ Failed to generate adaptive quiz: {quiz_data.get('error', 'Unknown error')}")

        # 4.2. Generate Individual Question Types (as specified in task)
        print("\n--- 4.2. Generating Specific Question Types ---")
        
        # Multiple Choice Question
        print("\nGenerating multiple choice question...")
        mc_question = ai_generator.generate_multiple_choice_question(
            topic="Kitsune tails and power",
            difficulty='medium',
            keywords=['nine-tails', 'power', 'kyuubi']
        )
        
        if mc_question and 'error' not in mc_question:
            print("✓ Generated multiple choice question")
            quiz_question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type='multiple_choice',
                question_text=mc_question['question_text'],
                explanation=mc_question.get('overall_explanation', ''),
                hint=mc_question.get('hint', ''),
                difficulty_level=mc_question.get('difficulty_level', 2),
                points=2,
                order_index=100
            )
            db.session.add(quiz_question)
            db.session.commit()
            
            for j, option_data in enumerate(mc_question.get('options', [])):
                quiz_option = QuizOption(
                    question_id=quiz_question.id,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    order_index=j,
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(quiz_option)
            db.session.commit()
            print(f"  ✓ Saved multiple choice question (ID: {quiz_question.id})")

        # True/False Question
        print("\nGenerating true/false question...")
        tf_question = ai_generator.generate_true_false_question(
            topic="Kitsune nature",
            difficulty='easy',
            keywords=['evil', 'trickster', 'zenko', 'yako']
        )
        
        if tf_question and 'error' not in tf_question:
            print("✓ Generated true/false question")
            quiz_question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type='true_false',
                question_text=tf_question['question_text'],
                explanation=tf_question.get('explanation', ''),
                difficulty_level=1,
                points=1,
                order_index=101
            )
            db.session.add(quiz_question)
            db.session.commit()
            
            # Add True/False options
            quiz_option_true = QuizOption(
                question_id=quiz_question.id,
                option_text='True',
                is_correct=tf_question['is_true'],
                order_index=0
            )
            quiz_option_false = QuizOption(
                question_id=quiz_question.id,
                option_text='False',
                is_correct=not tf_question['is_true'],
                order_index=1
            )
            db.session.add(quiz_option_true)
            db.session.add(quiz_option_false)
            db.session.commit()
            print(f"  ✓ Saved true/false question (ID: {quiz_question.id})")

        # Fill in the Blank Question
        print("\nGenerating fill-in-the-blank question...")
        fib_question = ai_generator.generate_fill_in_the_blank_question(
            topic="Kitsune shapeshifting",
            difficulty='medium',
            keywords=['化ける', 'bakeru', 'transform', 'human']
        )
        
        if fib_question and 'error' not in fib_question:
            print("✓ Generated fill-in-the-blank question")
            quiz_question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type='fill_blank',
                question_text=fib_question['question_text'],
                explanation=fib_question.get('explanation', ''),
                difficulty_level=2,
                points=2,
                order_index=102
            )
            db.session.add(quiz_question)
            db.session.commit()
            
            # For fill-in-the-blank, we store the correct answer as an option
            quiz_option = QuizOption(
                question_id=quiz_question.id,
                option_text=fib_question['correct_answer'],
                is_correct=True,
                order_index=0
            )
            db.session.add(quiz_option)
            db.session.commit()
            print(f"  ✓ Saved fill-in-the-blank question (ID: {quiz_question.id})")

        # Matching Question
        print("\nGenerating matching question...")
        matching_question = ai_generator.generate_matching_question(
            topic="Kanji meanings",
            difficulty='medium',
            keywords=['狐', '化', '尾', '神', 'kanji', 'meaning']
        )
        
        if matching_question and 'error' not in matching_question:
            print("✓ Generated matching question")
            quiz_question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type='matching',
                question_text=matching_question['question_text'],
                explanation=matching_question.get('explanation', ''),
                difficulty_level=2,
                points=3,
                order_index=103
            )
            db.session.add(quiz_question)
            db.session.commit()
            
            # For matching questions, we store pairs as options
            for j, pair in enumerate(matching_question.get('pairs', [])):
                quiz_option = QuizOption(
                    question_id=quiz_question.id,
                    option_text=f"{pair['prompt']} → {pair['answer']}",
                    is_correct=True,
                    order_index=j
                )
                db.session.add(quiz_option)
            db.session.commit()
            print(f"  ✓ Saved matching question (ID: {quiz_question.id})")

        # Add lesson pages metadata
        page1 = LessonPage(lesson_id=lesson.id, page_number=1, title="Introduction and Overview", description="Learn about Kitsune mythology and folklore")
        page2 = LessonPage(lesson_id=lesson.id, page_number=2, title="Visual Gallery", description="Traditional art depicting Kitsune")
        page3 = LessonPage(lesson_id=lesson.id, page_number=3, title="Knowledge Assessment", description="Test your understanding with an adaptive quiz")
        
        db.session.add_all([page1, page2, page3])
        db.session.commit()

        # Add foundational content to lesson
        print("\n--- Adding Foundational Database Content to Lesson ---")
        content_order = 20
        
        # Add Kanji content
        for kanji_id in generated_kanji_ids:
            kanji_content = LessonContent(
                lesson_id=lesson.id,
                content_type='kanji',
                content_id=kanji_id,
                title='Kanji Study',
                order_index=content_order,
                page_number=1
            )
            db.session.add(kanji_content)
            content_order += 1
        
        # Add Vocabulary content
        for vocab_id in generated_vocab_ids:
            vocab_content = LessonContent(
                lesson_id=lesson.id,
                content_type='vocabulary',
                content_id=vocab_id,
                title='Vocabulary Study',
                order_index=content_order,
                page_number=1
            )
            db.session.add(vocab_content)
            content_order += 1
        
        # Add Grammar content
        if generated_grammar_id:
            grammar_content = LessonContent(
                lesson_id=lesson.id,
                content_type='grammar',
                content_id=generated_grammar_id,
                title='Grammar Study',
                order_index=content_order,
                page_number=1
            )
            db.session.add(grammar_content)
        
        db.session.commit()

        # ===================================================================
        # COMPLETION SUMMARY
        # ===================================================================
        print("\n" + "="*60)
        print("LESSON CREATION COMPLETE!")
        print("="*60)
        
        print(f"✓ Lesson Title: {lesson.title}")
        print(f"✓ Lesson ID: {lesson.id}")
        print(f"✓ Category: {category.name}")
        print(f"✓ Difficulty: Level {lesson.difficulty_level} (Intermediate)")
        print(f"✓ Estimated Duration: {lesson.estimated_duration} minutes")
        print(f"✓ Total Content Items: {len(lesson.content_items)}")
        print(f"✓ Total Quiz Questions: {len([c for c in lesson.content_items if c.is_interactive])}")
        print(f"✓ Generated Kanji Entries: {len(generated_kanji_ids)}")
        print(f"✓ Generated Vocabulary Entries: {len(generated_vocab_ids)}")
        print(f"✓ Generated Grammar Entries: {1 if generated_grammar_id else 0}")
        print(f"✓ Generated Images: {len(generated_images)}")
        
        print("\nLesson Structure:")
        for page in lesson.pages:
            print(f"  Page {page['metadata'].page_number if page['metadata'] else 'Unknown'}: {len(page['content'])} content items")
        
        print(f"\nThe comprehensive Kitsune lesson has been successfully created!")
        print(f"You can now view it in the web application at lesson ID: {lesson.id}")
        
        return lesson.id


if __name__ == '__main__':
    lesson_id = create_comprehensive_kitsune_lesson()
    print(f"\n🦊 Lesson creation completed! Lesson ID: {lesson_id}")

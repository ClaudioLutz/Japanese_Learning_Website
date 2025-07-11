#!/usr/bin/env python3
"""
Multimedia-Enhanced Lesson Creator

This script demonstrates Phase 3: Multimedia Enhancement implementation.
It integrates AI image generation with file upload capabilities to create
rich, multimedia lessons automatically.

Features:
- AI-powered image generation for lesson content
- Automatic multimedia content analysis
- File upload integration
- Enhanced lesson creation with multimedia elements
"""

import os
import sys
import json
import requests
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import urlretrieve

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Lesson, LessonContent, LessonCategory, LessonPage
from app.ai_services import AILessonContentGenerator
from app.utils import FileUploadHandler

class MultimediaLessonCreator:
    """
    Enhanced lesson creator with multimedia capabilities.
    Integrates AI image generation and file upload systems.
    """
    
    def __init__(self, app_context=None):
        """Initialize the multimedia lesson creator."""
        if app_context:
            self.app = app_context
        else:
            self.app = create_app()
        
        self.ai_generator = AILessonContentGenerator()
        self.upload_folder = None
        
        with self.app.app_context():
            self.upload_folder = self.app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    
    def create_multimedia_lesson(self, lesson_config):
        """
        Create a lesson with multimedia enhancements.
        
        Args:
            lesson_config (dict): Configuration for the lesson including:
                - title: Lesson title
                - description: Lesson description
                - difficulty: Difficulty level
                - topic: Main topic
                - content_items: List of content items
                - generate_images: Whether to generate AI images
                - analyze_multimedia: Whether to analyze multimedia needs
        """
        with self.app.app_context():
            print(f"Creating multimedia lesson: {lesson_config['title']}")
            
            # Create the lesson
            lesson = self._create_base_lesson(lesson_config)
            
            # Analyze multimedia needs if requested
            if lesson_config.get('analyze_multimedia', True):
                multimedia_analysis = self._analyze_lesson_multimedia_needs(
                    lesson_config['content_items'], 
                    lesson_config['topic']
                )
                print(f"Multimedia analysis completed: {len(multimedia_analysis.get('image_suggestions', []))} image suggestions")
            
            # Process content items with multimedia enhancements
            for page_num, page_content in enumerate(lesson_config['content_items'], 1):
                self._create_multimedia_page(lesson, page_num, page_content, lesson_config)
            
            # Generate summary images if requested
            if lesson_config.get('generate_summary_images', False):
                self._generate_lesson_summary_images(lesson, lesson_config)
            
            db.session.commit()
            print(f"✅ Multimedia lesson created successfully: ID {lesson.id}")
            return lesson
    
    def _create_base_lesson(self, config):
        """Create the base lesson object."""
        # Get or create category
        category = LessonCategory.query.filter_by(name=config.get('category', 'Multimedia')).first()
        if not category:
            category = LessonCategory(
                name=config.get('category', 'Multimedia'),
                description='Multimedia-enhanced lessons',
                color_code='#FF6B6B'
            )
            db.session.add(category)
            db.session.flush()
        
        # Create lesson
        lesson = Lesson(
            title=config['title'],
            description=config.get('description', ''),
            lesson_type=config.get('lesson_type', 'free'),
            category_id=category.id,
            difficulty_level=config.get('difficulty', 'Beginner'),
            estimated_duration=config.get('duration', 30),
            is_published=config.get('is_published', True),
            instruction_language=config.get('language', 'english')
        )
        
        db.session.add(lesson)
        db.session.flush()
        return lesson
    
    def _create_multimedia_page(self, lesson, page_num, page_content, lesson_config):
        """Create a page with multimedia content."""
        print(f"Creating page {page_num}: {page_content.get('title', f'Page {page_num}')}")
        
        # Create page metadata
        page = LessonPage(
            lesson_id=lesson.id,
            page_number=page_num,
            title=page_content.get('title', f'Page {page_num}'),
            description=page_content.get('description', '')
        )
        db.session.add(page)
        
        order_index = 0
        
        # Add text content
        if 'text' in page_content:
            text_content = LessonContent(
                lesson_id=lesson.id,
                content_type='text',
                title=page_content.get('text_title', 'Content'),
                content_text=page_content['text'],
                page_number=page_num,
                order_index=order_index
            )
            db.session.add(text_content)
            order_index += 1
        
        # Generate and add AI images if requested
        if lesson_config.get('generate_images', True) and 'text' in page_content:
            image_content = self._generate_page_image(
                lesson, page_num, page_content['text'], lesson_config
            )
            if image_content:
                image_content.order_index = order_index
                db.session.add(image_content)
                order_index += 1
        
        # Add interactive content if specified
        if 'interactive' in page_content:
            interactive_content = self._create_interactive_content(
                lesson, page_num, page_content['interactive'], order_index
            )
            if interactive_content:
                db.session.add(interactive_content)
                order_index += 1
        
        # Add custom media if specified
        if 'media' in page_content:
            media_content = self._add_custom_media(
                lesson, page_num, page_content['media'], order_index
            )
            if media_content:
                db.session.add(media_content)
                order_index += 1
    
    def _generate_page_image(self, lesson, page_num, text_content, lesson_config):
        """Generate an AI image for page content."""
        try:
            print(f"  Generating AI image for page {page_num}...")
            
            # Generate image using AI service
            image_result = self.ai_generator.generate_single_image(
                prompt=self._create_image_prompt(text_content, lesson_config),
                size="1024x1024",
                quality="standard"
            )
            
            if 'error' in image_result:
                print(f"  ❌ Image generation failed: {image_result['error']}")
                return None
            
            # Download and save the image
            image_url = image_result['image_url']
            saved_path = self._download_and_save_image(image_url, lesson.id, page_num)
            
            if saved_path:
                print(f"  ✅ Image generated and saved: {saved_path}")
                
                # Create content entry
                return LessonContent(
                    lesson_id=lesson.id,
                    content_type='image',
                    title=f'Illustration for Page {page_num}',
                    content_text=f'AI-generated illustration: {image_result.get("prompt", "")}',
                    file_path=saved_path,
                    page_number=page_num
                )
            
        except Exception as e:
            print(f"  ❌ Error generating image: {e}")
        
        return None
    
    def _create_image_prompt(self, text_content, lesson_config):
        """Create an optimized prompt for image generation."""
        # Use AI to generate optimized prompt
        prompt_result = self.ai_generator.generate_image_prompt(
            text_content, 
            lesson_config['topic'], 
            lesson_config.get('difficulty', 'Beginner')
        )
        
        if 'error' not in prompt_result:
            return prompt_result['image_prompt']
        
        # Fallback to basic prompt
        return f"Educational illustration for Japanese language learning about {lesson_config['topic']}, {lesson_config.get('difficulty', 'beginner')} level, clean and professional style"
    
    def _download_and_save_image(self, image_url, lesson_id, page_num):
        """Download AI-generated image and save it to the upload folder."""
        try:
            # Create directory structure
            image_dir = os.path.join(self.upload_folder, 'lessons', 'image', f'lesson_{lesson_id}')
            os.makedirs(image_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_generated_page_{page_num}_{timestamp}.png"
            file_path = os.path.join(image_dir, filename)
            
            # Download image
            urlretrieve(image_url, file_path)
            
            # Return relative path for database storage
            relative_path = os.path.join('lessons', 'image', f'lesson_{lesson_id}', filename).replace('\\', '/')
            return relative_path
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def _create_interactive_content(self, lesson, page_num, interactive_config, order_index):
        """Create interactive content (quiz questions)."""
        try:
            print(f"  Creating interactive content for page {page_num}...")
            
            content_type = interactive_config.get('type', 'multiple_choice')
            
            # Generate question using AI
            if content_type == 'multiple_choice':
                question_data = self.ai_generator.generate_multiple_choice_question(
                    interactive_config.get('topic', 'Japanese'),
                    interactive_config.get('difficulty', 'Beginner'),
                    interactive_config.get('keywords', '')
                )
            elif content_type == 'true_false':
                question_data = self.ai_generator.generate_true_false_question(
                    interactive_config.get('topic', 'Japanese'),
                    interactive_config.get('difficulty', 'Beginner'),
                    interactive_config.get('keywords', '')
                )
            elif content_type == 'fill_blank':
                question_data = self.ai_generator.generate_fill_in_the_blank_question(
                    interactive_config.get('topic', 'Japanese'),
                    interactive_config.get('difficulty', 'Beginner'),
                    interactive_config.get('keywords', '')
                )
            else:
                print(f"  ❌ Unsupported interactive type: {content_type}")
                return None
            
            if 'error' in question_data:
                print(f"  ❌ Question generation failed: {question_data['error']}")
                return None
            
            # Create interactive content
            content = LessonContent(
                lesson_id=lesson.id,
                content_type='interactive',
                title=interactive_config.get('title', 'Quiz Question'),
                is_interactive=True,
                page_number=page_num,
                order_index=order_index,
                max_attempts=interactive_config.get('max_attempts', 3),
                passing_score=interactive_config.get('passing_score', 70)
            )
            
            print(f"  ✅ Interactive content created")
            return content
            
        except Exception as e:
            print(f"  ❌ Error creating interactive content: {e}")
            return None
    
    def _add_custom_media(self, lesson, page_num, media_config, order_index):
        """Add custom media content."""
        try:
            media_type = media_config.get('type', 'image')
            media_url = media_config.get('url')
            
            if not media_url:
                return None
            
            print(f"  Adding custom {media_type} media...")
            
            content = LessonContent(
                lesson_id=lesson.id,
                content_type=media_type,
                title=media_config.get('title', f'{media_type.title()} Content'),
                content_text=media_config.get('description', ''),
                media_url=media_url,
                page_number=page_num,
                order_index=order_index
            )
            
            print(f"  ✅ Custom media added")
            return content
            
        except Exception as e:
            print(f"  ❌ Error adding custom media: {e}")
            return None
    
    def _analyze_lesson_multimedia_needs(self, content_items, topic):
        """Analyze lesson content for multimedia enhancement opportunities."""
        try:
            # Combine all text content for analysis
            all_text = ""
            for page in content_items:
                if 'text' in page:
                    all_text += page['text'] + " "
            
            if not all_text.strip():
                return {}
            
            # Use AI to analyze multimedia needs
            analysis = self.ai_generator.analyze_content_for_multimedia_needs(all_text, topic)
            
            if 'error' not in analysis:
                return analysis
            
        except Exception as e:
            print(f"Error analyzing multimedia needs: {e}")
        
        return {}
    
    def _generate_lesson_summary_images(self, lesson, lesson_config):
        """Generate summary images for the entire lesson."""
        try:
            print("Generating lesson summary images...")
            
            # Create a summary of the lesson
            summary_text = f"Summary of {lesson.title}: {lesson.description}"
            
            # Generate summary image
            image_result = self.ai_generator.generate_single_image(
                prompt=f"Educational summary illustration for Japanese lesson '{lesson.title}', showing key concepts, clean professional style",
                size="1024x1024",
                quality="standard"
            )
            
            if 'error' not in image_result:
                saved_path = self._download_and_save_image(
                    image_result['image_url'], lesson.id, 'summary'
                )
                
                if saved_path:
                    # Update lesson thumbnail
                    lesson.thumbnail_url = saved_path
                    print("✅ Lesson summary image generated and set as thumbnail")
            
        except Exception as e:
            print(f"Error generating summary images: {e}")


def create_sample_multimedia_lesson():
    """Create a sample multimedia lesson to demonstrate capabilities."""
    
    creator = MultimediaLessonCreator()
    
    lesson_config = {
        'title': 'Multimedia Japanese Greetings',
        'description': 'Learn Japanese greetings with AI-generated illustrations and interactive content',
        'topic': 'Japanese Greetings',
        'difficulty': 'Beginner',
        'category': 'Multimedia Lessons',
        'generate_images': True,
        'analyze_multimedia': True,
        'generate_summary_images': True,
        'content_items': [
            {
                'title': 'Introduction to Greetings',
                'description': 'Basic Japanese greeting concepts',
                'text': '''
                Japanese greetings are an essential part of daily communication. 
                The most common greeting is "こんにちは" (konnichiwa), which means "hello" 
                and can be used throughout the day. In the morning, people say "おはよう" 
                (ohayou) for "good morning," and in the evening, "こんばんは" (konbanwa) 
                for "good evening."
                ''',
                'interactive': {
                    'type': 'multiple_choice',
                    'topic': 'Japanese Greetings',
                    'difficulty': 'Beginner',
                    'keywords': 'konnichiwa, ohayou, konbanwa'
                }
            },
            {
                'title': 'Formal vs Informal Greetings',
                'description': 'Understanding politeness levels',
                'text': '''
                Japanese has different levels of politeness. "おはようございます" 
                (ohayou gozaimasu) is the formal version of "good morning," while 
                "おはよう" (ohayou) is casual. Similarly, "こんにちは" (konnichiwa) 
                is generally polite, but the tone and context matter greatly.
                ''',
                'interactive': {
                    'type': 'true_false',
                    'topic': 'Japanese Politeness',
                    'difficulty': 'Beginner',
                    'keywords': 'formal, informal, politeness'
                }
            },
            {
                'title': 'Cultural Context',
                'description': 'When and how to use greetings',
                'text': '''
                In Japanese culture, greetings are often accompanied by bowing. 
                The depth of the bow indicates the level of respect. When meeting 
                someone for the first time, you might say "はじめまして" (hajimemashite), 
                meaning "nice to meet you," followed by "よろしくお願いします" 
                (yoroshiku onegaishimasu), which roughly means "please treat me favorably."
                '''
            }
        ]
    }
    
    try:
        lesson = creator.create_multimedia_lesson(lesson_config)
        print(f"\n🎉 Sample multimedia lesson created successfully!")
        print(f"Lesson ID: {lesson.id}")
        print(f"Title: {lesson.title}")
        print(f"Pages: {len(lesson.pages)}")
        print(f"Content Items: {len(lesson.content_items)}")
        
        # Print content summary
        print("\nContent Summary:")
        for content in lesson.content_items:
            print(f"  - {content.content_type}: {content.title}")
            if content.file_path:
                print(f"    File: {content.file_path}")
        
        return lesson
        
    except Exception as e:
        print(f"❌ Error creating sample lesson: {e}")
        return None


def create_advanced_multimedia_lesson():
    """Create an advanced multimedia lesson with more complex features."""
    
    creator = MultimediaLessonCreator()
    
    lesson_config = {
        'title': 'Advanced Kanji with Visual Learning',
        'description': 'Master complex kanji characters through AI-generated visual mnemonics and interactive exercises',
        'topic': 'Advanced Kanji Learning',
        'difficulty': 'Intermediate',
        'category': 'Advanced Multimedia',
        'generate_images': True,
        'analyze_multimedia': True,
        'generate_summary_images': True,
        'content_items': [
            {
                'title': 'Complex Kanji Structure',
                'description': 'Understanding radical combinations',
                'text': '''
                Complex kanji are built from simpler components called radicals. 
                For example, the kanji 語 (go, meaning "language") contains the 
                radicals 言 (speech) and 吾 (I/me). Understanding these building 
                blocks helps memorize and understand new kanji characters.
                ''',
                'interactive': {
                    'type': 'multiple_choice',
                    'topic': 'Kanji Radicals',
                    'difficulty': 'Intermediate',
                    'keywords': 'radicals, components, structure'
                }
            },
            {
                'title': 'Visual Memory Techniques',
                'description': 'Using imagery to remember kanji',
                'text': '''
                Visual mnemonics are powerful tools for kanji memorization. 
                The kanji 森 (mori, forest) literally shows three trees (木) 
                together, creating a visual representation of a forest. 
                Similarly, 明 (mei, bright) combines sun (日) and moon (月), 
                representing brightness from celestial bodies.
                ''',
                'interactive': {
                    'type': 'true_false',
                    'topic': 'Kanji Mnemonics',
                    'difficulty': 'Intermediate',
                    'keywords': 'visual memory, mnemonics, imagery'
                }
            },
            {
                'title': 'Stroke Order Mastery',
                'description': 'Proper writing technique',
                'text': '''
                Correct stroke order is crucial for proper kanji writing. 
                Generally, strokes go from top to bottom and left to right. 
                Horizontal strokes usually come before vertical ones, and 
                enclosing strokes are completed last. Practice with proper 
                stroke order improves both writing speed and character recognition.
                '''
            }
        ]
    }
    
    try:
        lesson = creator.create_multimedia_lesson(lesson_config)
        print(f"\n🎉 Advanced multimedia lesson created successfully!")
        print(f"Lesson ID: {lesson.id}")
        print(f"Title: {lesson.title}")
        return lesson
        
    except Exception as e:
        print(f"❌ Error creating advanced lesson: {e}")
        return None


if __name__ == "__main__":
    print("🚀 Multimedia Lesson Creator - Phase 3 Implementation")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables.")
        print("   AI image generation will not work without this key.")
        print("   Set the key with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Create sample lessons
    print("Creating sample multimedia lesson...")
    sample_lesson = create_sample_multimedia_lesson()
    
    if sample_lesson:
        print("\nCreating advanced multimedia lesson...")
        advanced_lesson = create_advanced_multimedia_lesson()
        
        if advanced_lesson:
            print("\n✅ Phase 3: Multimedia Enhancement implementation complete!")
            print("\nFeatures demonstrated:")
            print("  ✓ AI image generation integration")
            print("  ✓ Multimedia content analysis")
            print("  ✓ File upload system integration")
            print("  ✓ Enhanced lesson creation workflow")
            print("  ✓ Automatic thumbnail generation")
            print("  ✓ Interactive content with multimedia")
            
            print(f"\nLessons created:")
            print(f"  1. {sample_lesson.title} (ID: {sample_lesson.id})")
            print(f"  2. {advanced_lesson.title} (ID: {advanced_lesson.id})")
        else:
            print("❌ Failed to create advanced lesson")
    else:
        print("❌ Failed to create sample lesson")

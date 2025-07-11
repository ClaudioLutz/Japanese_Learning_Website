#!/usr/bin/env python3
"""
Base class for lesson creation scripts that eliminates code duplication
and provides a standardized lesson creation workflow.
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent, QuizQuestion, QuizOption, LessonCategory
from app.models import Kana, Kanji, Vocabulary, Grammar
from app.ai_services import AILessonContentGenerator
from content_discovery import ContentDiscovery, ContentGapAnalyzer

class BaseLessonCreator:
    """Base class for creating lessons with AI-generated content."""
    
    def __init__(self, title, difficulty, lesson_type="free", language="english", category_name=None):
        self.title = title
        self.difficulty = difficulty
        self.lesson_type = lesson_type
        self.language = language
        self.category_name = category_name
        self.pages = []
        self.generator = None
        self.app = None
        self.content_discovery = None
        self.gap_analyzer = None
        
    def add_page(self, title, content_list, description=None):
        """Add a page with content to the lesson."""
        page_number = len(self.pages) + 1
        self.pages.append({
            "page_number": page_number,
            "title": title,
            "description": description or f"This page covers: {title}",
            "content": content_list
        })
        
    def add_content_to_page(self, page_number, content_item):
        """Add content to an existing page."""
        if page_number <= len(self.pages):
            self.pages[page_number - 1]["content"].append(content_item)
        else:
            raise ValueError(f"Page {page_number} does not exist")
    
    def initialize_ai_generator(self):
        """Initialize the AI content generator."""
        self.generator = AILessonContentGenerator()
        if not self.generator.client:
            raise RuntimeError("AI Generator could not be initialized. Check your API key.")
    
    def initialize_content_discovery(self):
        """Initialize the content discovery system."""
        self.content_discovery = ContentDiscovery()
        self.gap_analyzer = ContentGapAnalyzer(self.content_discovery)
        print("✅ Content discovery system initialized.")
    
    def discover_existing_content(self, topic, content_type=None, jlpt_level=None):
        """
        Discover existing content related to a topic.
        
        Args:
            topic: The topic to search for
            content_type: Specific content type ('kana', 'kanji', 'vocabulary', 'grammar')
            jlpt_level: JLPT level to filter by
            
        Returns:
            Dictionary with discovered content
        """
        if not self.content_discovery:
            self.initialize_content_discovery()
        
        print(f"🔍 Discovering existing content for topic: '{topic}'")
        
        # Get related content
        related_content = self.content_discovery.suggest_related_content(topic, content_type)
        
        # Filter by JLPT level if specified
        if jlpt_level:
            filtered_content = {}
            for ctype, items in related_content.items():
                if ctype in ['kanji', 'vocabulary', 'grammar']:
                    filtered_items = [item for item in items if hasattr(item, 'jlpt_level') and item.jlpt_level == jlpt_level]
                    filtered_content[ctype] = filtered_items
                else:
                    filtered_content[ctype] = items
            related_content = filtered_content
        
        # Print discovery results
        for ctype, items in related_content.items():
            if items:
                print(f"  📚 Found {len(items)} {ctype} items")
            else:
                print(f"  ❌ No {ctype} items found")
        
        return related_content
    
    def analyze_content_gaps(self, topic, jlpt_level=None):
        """
        Analyze content gaps for the lesson topic.
        
        Args:
            topic: The lesson topic
            jlpt_level: Target JLPT level
            
        Returns:
            Gap analysis results
        """
        if not self.content_discovery:
            self.initialize_content_discovery()
        
        print(f"📊 Analyzing content gaps for: '{topic}'")
        
        gap_analysis = self.content_discovery.analyze_content_gaps(topic, jlpt_level)
        
        # Print gap analysis results
        print(f"  📈 Existing content types: {len(gap_analysis['existing_content'])}")
        print(f"  📋 Recommendations: {len(gap_analysis['recommendations'])}")
        
        if gap_analysis['recommendations']:
            print("  💡 Recommendations:")
            for rec in gap_analysis['recommendations'][:3]:  # Show first 3
                print(f"    - {rec}")
        
        return gap_analysis
    
    def find_content_by_jlpt_level(self, jlpt_level, content_type=None, limit=None):
        """
        Find existing content by JLPT level.
        
        Args:
            jlpt_level: JLPT level (1-5)
            content_type: Specific content type or None for all
            limit: Maximum number of items to return per type
            
        Returns:
            Dictionary with found content
        """
        if not self.content_discovery:
            self.initialize_content_discovery()
        
        print(f"🎯 Finding JLPT N{jlpt_level} content")
        
        content_types = [content_type] if content_type else ['kanji', 'vocabulary', 'grammar']
        found_content = {}
        
        for ctype in content_types:
            if ctype == 'kanji':
                items = self.content_discovery.find_kanji_by_jlpt_level(jlpt_level)
            elif ctype == 'vocabulary':
                items = self.content_discovery.find_vocabulary_by_jlpt_level(jlpt_level)
            elif ctype == 'grammar':
                items = self.content_discovery.find_grammar_by_jlpt_level(jlpt_level)
            else:
                items = []
            
            if limit:
                items = items[:limit]
            
            found_content[ctype] = items
            print(f"  📚 Found {len(items)} {ctype} items for JLPT N{jlpt_level}")
        
        return found_content
    
    def add_database_content_to_page(self, page_number, content_items, title_prefix="Database Content"):
        """
        Add existing database content to a page.
        
        Args:
            page_number: Page number to add content to
            content_items: List of database content items
            title_prefix: Prefix for content titles
        """
        if page_number > len(self.pages):
            raise ValueError(f"Page {page_number} does not exist")
        
        for item in content_items:
            content_type = type(item).__name__.lower()
            
            # Create content reference
            content_ref = {
                'type': content_type,
                'content_id': item.id,
                'title': f"{title_prefix}: {getattr(item, 'character', getattr(item, 'word', getattr(item, 'title', str(item))))}"
            }
            
            self.add_content_to_page(page_number, content_ref)
            print(f"  ➕ Added {content_type} '{content_ref['title']}' to page {page_number}")
    
    def create_jlpt_focused_page(self, jlpt_level, content_types=['kanji', 'vocabulary'], limit_per_type=5):
        """
        Create a page focused on specific JLPT level content.
        
        Args:
            jlpt_level: JLPT level (1-5)
            content_types: List of content types to include
            limit_per_type: Maximum items per content type
        """
        page_title = f"JLPT N{jlpt_level} Content"
        page_description = f"Essential content for JLPT N{jlpt_level} preparation"
        
        # Find content for this JLPT level
        jlpt_content = self.find_content_by_jlpt_level(jlpt_level, limit=limit_per_type)
        
        # Create content list for the page
        content_list = []
        
        # Add explanation about JLPT level
        content_list.append({
            'type': 'explanation',
            'topic': f'JLPT N{jlpt_level} Overview',
            'keywords': [f'JLPT N{jlpt_level}', 'Japanese proficiency', 'study guide']
        })
        
        # Add database content references
        for content_type in content_types:
            if content_type in jlpt_content and jlpt_content[content_type]:
                for item in jlpt_content[content_type]:
                    content_list.append({
                        'type': content_type,
                        'content_id': item.id,
                        'title': f"{content_type.title()}: {getattr(item, 'character', getattr(item, 'word', getattr(item, 'title', str(item))))}"
                    })
        
        # Add quiz based on the content
        if any(jlpt_content.values()):
            content_list.append({
                'type': 'multiple_choice',
                'topic': f'JLPT N{jlpt_level} Review Quiz',
                'keywords': [f'JLPT N{jlpt_level}', 'review', 'practice']
            })
        
        self.add_page(page_title, content_list, page_description)
        print(f"✅ Created JLPT N{jlpt_level} focused page with {len(content_list)} content items")
    
    def create_thematic_page(self, theme, include_quiz=True):
        """
        Create a page based on a theme using existing database content.
        
        Args:
            theme: Theme to search for (e.g., 'food', 'family', 'colors')
            include_quiz: Whether to include a quiz
        """
        page_title = f"{theme.title()} Theme"
        page_description = f"Learn Japanese vocabulary and concepts related to {theme}"
        
        # Discover content related to the theme
        theme_content = self.discover_existing_content(theme)
        
        content_list = []
        
        # Add theme introduction
        content_list.append({
            'type': 'formatted_explanation',
            'topic': f'Introduction to {theme} in Japanese',
            'keywords': [theme, 'Japanese culture', 'vocabulary']
        })
        
        # Add discovered content
        for content_type, items in theme_content.items():
            if items:
                # Limit to avoid overwhelming the page
                limited_items = items[:8]  
                for item in limited_items:
                    content_list.append({
                        'type': content_type,
                        'content_id': item.id,
                        'title': f"{content_type.title()}: {getattr(item, 'character', getattr(item, 'word', getattr(item, 'title', str(item))))}"
                    })
        
        # Add quiz if requested and we have content
        if include_quiz and any(theme_content.values()):
            content_list.append({
                'type': 'multiple_choice',
                'topic': f'{theme} vocabulary quiz',
                'keywords': [theme, 'vocabulary', 'practice']
            })
        
        self.add_page(page_title, content_list, page_description)
        print(f"✅ Created {theme} themed page with {len(content_list)} content items")
    
    def find_or_create_category(self):
        """Find existing category or create new one."""
        if not self.category_name:
            return None
            
        category = LessonCategory.query.filter_by(name=self.category_name).first()
        if not category:
            category = LessonCategory(
                name=self.category_name,
                description=f"Lessons related to {self.category_name}"
            )
            db.session.add(category)
            db.session.flush()
        return category
    
    def delete_existing_lesson(self):
        """Delete existing lesson with the same title."""
        existing_lesson = Lesson.query.filter_by(title=self.title).first()
        if existing_lesson:
            print(f"Found existing lesson '{self.title}' (ID: {existing_lesson.id}). Deleting it.")
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson deleted.")
    
    def create_lesson_record(self):
        """Create the main lesson database record."""
        category = self.find_or_create_category()
        
        lesson = Lesson(
            title=self.title,
            description=f"AI-generated lesson: {self.title}",
            lesson_type=self.lesson_type,
            difficulty_level=self._get_difficulty_level(),
            is_published=True,
            instruction_language=self.language,
            category_id=category.id if category else None
        )
        
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lesson '{self.title}' created with ID: {lesson.id}")
        return lesson
    
    def _get_difficulty_level(self):
        """Convert difficulty string to numeric level."""
        difficulty_map = {
            "absolute_beginner": 1,
            "beginner": 2,
            "intermediate": 3,
            "advanced": 4,
            "expert": 5
        }
        return difficulty_map.get(self.difficulty.lower().replace(" ", "_"), 2)
    
    def create_pages_and_content(self, lesson):
        """Create all pages and their content."""
        for page_info in self.pages:
            print(f"\n--- Creating Page {page_info['page_number']}: {page_info['title']} ---")
            
            # Create lesson page metadata
            lesson_page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_info['page_number'],
                title=page_info['title'],
                description=page_info['description']
            )
            db.session.add(lesson_page)
            
            # Create content for this page
            order_index = 0
            for content_info in page_info['content']:
                self.create_content_item(lesson, page_info['page_number'], content_info, order_index)
                order_index += 1
    
    def create_content_item(self, lesson, page_number, content_info, order_index):
        """Create a single content item."""
        content_type = content_info['type']
        
        print(f"🤖 Generating {content_type} for '{content_info.get('topic', 'content')[:60]}...'")
        
        if content_type in ['explanation', 'formatted_explanation']:
            self.create_explanation_content(lesson, page_number, content_info, order_index)
        elif content_type in ['multiple_choice', 'true_false', 'fill_in_the_blank', 'matching']:
            self.create_quiz_content(lesson, page_number, content_info, order_index)
        elif content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
            self.create_reference_content(lesson, page_number, content_info, order_index)
        else:
            print(f"❌ Unknown content type: {content_type}")
    
    def create_explanation_content(self, lesson, page_number, content_info, order_index):
        """Create explanation content using AI."""
        # Use formatted explanation if available, otherwise fall back to simple explanation
        if content_info['type'] == 'formatted_explanation':
            result = self.generator.generate_formatted_explanation(
                content_info['topic'], 
                self.difficulty, 
                content_info['keywords']
            )
        else:
            result = self.generator.generate_explanation(
                content_info['topic'], 
                self.difficulty, 
                content_info['keywords']
            )
        
        if "error" in result:
            print(f"❌ Error generating explanation: {result['error']}")
            return
        
        content = LessonContent(
            lesson_id=lesson.id,
            page_number=page_number,
            content_type="text",
            title=content_info.get('title', f"Explanation: {content_info['topic'][:30]}..."),
            content_text=result['generated_text'],
            order_index=order_index,
            generated_by_ai=True,
            ai_generation_details={
                "model": "gpt-4.1",
                "topic": content_info['topic'],
                "difficulty": self.difficulty,
                "keywords": content_info['keywords']
            }
        )
        db.session.add(content)
        print("✅ Explanation content added.")
    
    def create_quiz_content(self, lesson, page_number, content_info, order_index):
        """Create quiz content using AI."""
        content_type = content_info['type']
        
        # Generate quiz content based on type
        if content_type == 'multiple_choice':
            result = self.generator.generate_multiple_choice_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        elif content_type == 'true_false':
            result = self.generator.generate_true_false_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        elif content_type == 'fill_in_the_blank':
            result = self.generator.generate_fill_in_the_blank_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        elif content_type == 'matching':
            result = self.generator.generate_matching_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        else:
            print(f"❌ Unsupported quiz type: {content_type}")
            return
        
        if "error" in result:
            print(f"❌ Error generating {content_type}: {result['error']}")
            return
        
        # Create quiz content record
        quiz_content = LessonContent(
            lesson_id=lesson.id,
            page_number=page_number,
            content_type="interactive",
            title=f"Quiz: {result.get('question_text', content_info['topic'])[:40]}...",
            is_interactive=True,
            order_index=order_index,
            max_attempts=content_info.get('max_attempts', 3),
            passing_score=content_info.get('passing_score', 70),
            generated_by_ai=True,
            ai_generation_details={
                "model": "gpt-4.1",
                "type": content_type,
                "topic": content_info['topic'],
                "difficulty": self.difficulty,
                "keywords": content_info['keywords']
            }
        )
        db.session.add(quiz_content)
        db.session.flush()
        
        # Create quiz question and options
        self.create_quiz_question(quiz_content.id, content_type, result)
        print(f"✅ {content_type.replace('_', ' ').title()} quiz added.")
    
    def create_quiz_question(self, content_id, question_type, result):
        """Create quiz question and options."""
        question = QuizQuestion(
            lesson_content_id=content_id,
            question_type=question_type,
            question_text=result['question_text'],
            explanation=result.get('explanation', result.get('overall_explanation', ''))
        )
        db.session.add(question)
        db.session.flush()
        
        # Create options based on question type
        if question_type == 'multiple_choice':
            for option_data in result['options']:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(option)
        
        elif question_type == 'true_false':
            db.session.add(QuizOption(
                question_id=question.id, 
                option_text="True", 
                is_correct=result['is_true']
            ))
            db.session.add(QuizOption(
                question_id=question.id, 
                option_text="False", 
                is_correct=not result['is_true']
            ))
        
        elif question_type == 'fill_in_the_blank':
            db.session.add(QuizOption(
                question_id=question.id,
                option_text=result['correct_answer'],
                is_correct=True
            ))
        
        elif question_type == 'matching':
            for pair in result['pairs']:
                db.session.add(QuizOption(
                    question_id=question.id,
                    option_text=pair['prompt'],
                    feedback=pair['answer'],
                    is_correct=True
                ))
    
    def create_reference_content(self, lesson, page_number, content_info, order_index):
        """Create content that references existing database entries."""
        content = LessonContent(
            lesson_id=lesson.id,
            page_number=page_number,
            content_type=content_info['type'],
            content_id=content_info['content_id'],
            title=content_info.get('title', f"{content_info['type'].title()} Reference"),
            order_index=order_index
        )
        db.session.add(content)
        print(f"✅ {content_info['type'].title()} reference content added.")
    
    def create_lesson(self):
        """Main method to create the complete lesson."""
        if not self.pages:
            raise ValueError("No pages defined. Add pages before creating lesson.")
        
        self.app = create_app()
        
        with self.app.app_context():
            print(f"--- Creating Lesson: {self.title} ---")
            print(f"Total pages to create: {len(self.pages)}")
            
            # Initialize AI generator
            self.initialize_ai_generator()
            
            # Delete existing lesson
            self.delete_existing_lesson()
            
            # Create lesson record
            lesson = self.create_lesson_record()
            
            # Create pages and content
            self.create_pages_and_content(lesson)
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n--- Lesson Creation Complete! ---")
            print(f"Created lesson '{self.title}' with {len(self.pages)} pages")
            
            return lesson

# Utility function for easy script creation
def create_lesson_script(title, difficulty, pages_config, **kwargs):
    """Utility function to create a lesson from configuration."""
    creator = BaseLessonCreator(title, difficulty, **kwargs)
    
    for page_config in pages_config:
        creator.add_page(
            page_config['title'],
            page_config['content'],
            page_config.get('description')
        )
    
    return creator.create_lesson()

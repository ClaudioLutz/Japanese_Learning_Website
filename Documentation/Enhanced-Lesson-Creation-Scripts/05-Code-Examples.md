# Code Examples for Enhanced Lesson Creation Scripts

## 1. Base Lesson Creator Class Implementation

### lesson_creator_base.py
```python
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
from app.ai_services import AILessonContentGenerator

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
        
        if content_type == 'formatted_explanation':
            self.create_explanation_content(lesson, page_number, content_info, order_index)
        elif content_type in ['multiple_choice', 'true_false', 'fill_in_the_blank', 'matching']:
            self.create_quiz_content(lesson, page_number, content_info, order_index)
        elif content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
            self.create_reference_content(lesson, page_number, content_info, order_index)
        else:
            print(f"❌ Unknown content type: {content_type}")
    
    def create_explanation_content(self, lesson, page_number, content_info, order_index):
        """Create explanation content using AI."""
        result = self.generator.generate_formatted_explanation(
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
                "model": "gpt-4o",
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
                "model": "gpt-4o",
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
```

## 2. Content Pattern Library

### lesson_patterns.py
```python
"""
Reusable content patterns for lesson creation.
"""

PATTERNS = {
    "character_introduction": {
        "description": "Introduces a character or set of characters with explanation and practice",
        "pages": [
            {
                "title": "Introduction to {character_name}",
                "content": [
                    {
                        "type": "formatted_explanation",
                        "topic": "Detailed introduction to {character_name} including pronunciation, stroke order, usage examples, and cultural context",
                        "keywords": "{character_name}, pronunciation, stroke order, usage, examples"
                    }
                ]
            },
            {
                "title": "{character_name} Practice",
                "content": [
                    {
                        "type": "multiple_choice",
                        "topic": "Reading recognition quiz for {character_name}",
                        "keywords": "{character_name}, reading, recognition"
                    },
                    {
                        "type": "matching",
                        "topic": "Match {character_name} to its pronunciation",
                        "keywords": "{character_name}, pronunciation, matching"
                    }
                ]
            }
        ]
    },
    
    "vocabulary_set": {
        "description": "Teaches a set of vocabulary words with explanations and practice",
        "pages": [
            {
                "title": "Vocabulary: {topic_name}",
                "content": [
                    {
                        "type": "formatted_explanation",
                        "topic": "Learn these {word_count} vocabulary words related to {topic_name}: {word_list}",
                        "keywords": "{topic_name}, vocabulary, {word_list}"
                    }
                ]
            },
            {
                "title": "{topic_name} Vocabulary Practice",
                "content": [
                    {
                        "type": "multiple_choice",
                        "topic": "Vocabulary quiz for {topic_name} words",
                        "keywords": "{topic_name}, vocabulary, quiz"
                    },
                    {
                        "type": "fill_in_the_blank",
                        "topic": "Complete sentences using {topic_name} vocabulary",
                        "keywords": "{topic_name}, vocabulary, sentences"
                    }
                ]
            }
        ]
    },
    
    "grammar_point": {
        "description": "Explains a grammar point with examples and practice",
        "pages": [
            {
                "title": "Grammar: {grammar_name}",
                "content": [
                    {
                        "type": "formatted_explanation",
                        "topic": "Comprehensive explanation of {grammar_name} grammar point including structure, usage rules, and examples",
                        "keywords": "{grammar_name}, grammar, structure, usage, examples"
                    }
                ]
            },
            {
                "title": "{grammar_name} Practice",
                "content": [
                    {
                        "type": "fill_in_the_blank",
                        "topic": "Practice using {grammar_name} in sentences",
                        "keywords": "{grammar_name}, grammar, practice, sentences"
                    },
                    {
                        "type": "true_false",
                        "topic": "True or false questions about {grammar_name} usage",
                        "keywords": "{grammar_name}, grammar, true false"
                    }
                ]
            }
        ]
    },
    
    "comprehensive_review": {
        "description": "Reviews multiple topics with mixed practice",
        "pages": [
            {
                "title": "Review: {topic_list}",
                "content": [
                    {
                        "type": "formatted_explanation",
                        "topic": "Comprehensive review of {topic_list} covering key points and connections",
                        "keywords": "{topic_list}, review, summary"
                    }
                ]
            },
            {
                "title": "Mixed Practice",
                "content": [
                    {
                        "type": "multiple_choice",
                        "topic": "Mixed quiz covering {topic_list}",
                        "keywords": "{topic_list}, mixed, comprehensive"
                    },
                    {
                        "type": "matching",
                        "topic": "Match concepts from {topic_list}",
                        "keywords": "{topic_list}, matching, concepts"
                    }
                ]
            }
        ]
    }
}

class PatternApplicator:
    """Applies patterns to create lesson structures."""
    
    def __init__(self, pattern_name):
        if pattern_name not in PATTERNS:
            raise ValueError(f"Pattern '{pattern_name}' not found")
        self.pattern = PATTERNS[pattern_name]
    
    def apply_pattern(self, substitutions):
        """Apply pattern with given substitutions."""
        pages = []
        
        for page_template in self.pattern['pages']:
            page = {
                'title': self._substitute_placeholders(page_template['title'], substitutions),
                'content': []
            }
            
            for content_template in page_template['content']:
                content = {
                    'type': content_template['type'],
                    'topic': self._substitute_placeholders(content_template['topic'], substitutions),
                    'keywords': self._substitute_placeholders(content_template['keywords'], substitutions)
                }
                page['content'].append(content)
            
            pages.append(page)
        
        return pages
    
    def _substitute_placeholders(self, text, substitutions):
        """Replace placeholders in text with actual values."""
        for key, value in substitutions.items():
            placeholder = "{" + key + "}"
            text = text.replace(placeholder, str(value))
        return text

# Usage example
def create_hiragana_lesson_with_pattern():
    """Example of using patterns to create a lesson."""
    pattern = PatternApplicator("character_introduction")
    
    hiragana_groups = [
        {"character_name": "あ (a)", "description": "The first vowel sound"},
        {"character_name": "か (ka)", "description": "K-consonant with 'a' vowel"},
        {"character_name": "さ (sa)", "description": "S-consonant with 'a' vowel"}
    ]
    
    creator = BaseLessonCreator(
        title="Hiragana Basics with Patterns",
        difficulty="beginner"
    )
    
    # Add introduction page
    creator.add_page("Introduction", [
        {
            "type": "formatted_explanation",
            "topic": "Introduction to basic Hiragana characters",
            "keywords": "hiragana, introduction, basics"
        }
    ])
    
    # Apply pattern for each character
    for char_info in hiragana_groups:
        pages = pattern.apply_pattern(char_info)
        for page in pages:
            creator.add_page(page['title'], page['content'])
    
    return creator.create_lesson()
```

## 3. Configuration-Driven Script Example

### create_lesson_from_config.py
```python
#!/usr/bin/env python3
"""
Configuration-driven lesson creation script.
"""
import json
import yaml
from lesson_creator_base import BaseLessonCreator
from lesson_patterns import PatternApplicator

class ConfigLessonCreator:
    """Creates lessons from configuration files."""
    
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.validate_config()
    
    def load_config(self, config_path):
        """Load configuration from JSON or YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                return json.load(f)
            elif config_path.endswith(('.yml', '.yaml')):
                return yaml.safe_load(f)
            else:
                raise ValueError("Config file must be JSON or YAML")
    
    def validate_config(self):
        """Validate configuration structure."""
        required_fields = ['title', 'difficulty']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required field: {field}")
    
    def create_lesson(self):
        """Create lesson from configuration."""
        creator = BaseLessonCreator(
            title=self.config['title'],
            difficulty=self.config['difficulty'],
            lesson_type=self.config.get('lesson_type', 'free'),
            language=self.config.get('language', 'english'),
            category_name=self.config.get('category')
        )
        
        # Handle different configuration styles
        if 'pattern' in self.config:
            self.apply_pattern_config(creator)
        elif 'pages' in self.config:
            self.apply_pages_config(creator)
        else:
            raise ValueError("Config must specify either 'pattern' or 'pages'")
        
        return creator.create_lesson()
    
    def apply_pattern_config(self, creator):
        """Apply pattern-based configuration."""
        pattern_name = self.config['pattern']
        pattern = PatternApplicator(pattern_name)
        
        # Apply pattern for each item
        for item in self.config.get('items', []):
            pages = pattern.apply_pattern(item)
            for page in pages:
                creator.add_page(page['title'], page['content'])
    
    def apply_pages_config(self, creator):
        """Apply direct page configuration."""
        for page_config in self.config['pages']:
            creator.add_page(
                page_config['title'],
                page_config['content'],
                page_config.get('description')
            )

# Example configuration files

# hiragana_vowels.json
HIRAGANA_VOWELS_CONFIG = {
    "title": "Hiragana Vowels Mastery",
    "difficulty": "beginner",
    "language": "english",
    "category": "Hiragana",
    "pattern": "character_introduction",
    "items": [
        {
            "character_name": "あ (a)",
            "description": "The first vowel sound in Japanese"
        },
        {
            "character_name": "い (i)", 
            "description": "The second vowel sound"
        },
        {
            "character_name": "う (u)",
            "description": "The third vowel sound"
        },
        {
            "character_name": "え (e)",
            "description": "The fourth vowel sound"
        },
        {
            "character_name": "お (o)",
            "description": "The fifth vowel sound"
        }
    ]
}

# jlpt_n5_vocab.json
JLPT_N5_VOCAB_CONFIG = {
    "title": "JLPT N5 Daily Life Vocabulary",
    "difficulty": "beginner",
    "language": "english",
    "category": "JLPT N5",
    "pages": [
        {
            "title": "Introduction to Daily Life Vocabulary",
            "content": [
                {
                    "type": "formatted_explanation",
                    "topic": "Essential daily life vocabulary for JLPT N5 level",
                    "keywords": "JLPT N5, daily life, vocabulary, essential"
                }
            ]
        },
        {
            "title": "Family Members",
            "content": [
                {
                    "type": "formatted_explanation",
                    "topic": "Japanese family member vocabulary: 家族 (kazoku), お父さん (otousan), お母さん (okaasan)",
                    "keywords": "family, kazoku, otousan, okaasan, vocabulary"
                },
                {
                    "type": "multiple_choice",
                    "topic": "Quiz on family member vocabulary",
                    "keywords": "family, vocabulary, quiz"
                }
            ]
        },
        {
            "title": "Daily Activities",
            "content": [
                {
                    "type": "formatted_explanation",
                    "topic": "Common daily activity verbs: 食べる (taberu), 飲む (nomu), 寝る (neru)",
                    "keywords": "daily activities, taberu, nomu, neru, verbs"
                },
                {
                    "type": "fill_in_the_blank",
                    "topic": "Complete sentences with daily activity verbs",
                    "keywords": "daily activities, verbs, sentences"
                }
            ]
        }
    ]
}

if __name__ == "__main__":
    # Save example configs
    with open('hiragana_vowels.json', 'w', encoding='utf-8') as f:
        json.dump(HIRAGANA_VOWELS_CONFIG, f, indent=2, ensure_ascii=False)
    
    with open('jlpt_n5_vocab.json', 'w', encoding='utf-8') as f:
        json.dump(JLPT_N5_VOCAB_CONFIG, f, indent=2, ensure_ascii=False)
    
    # Create lessons from configs
    print("Creating lesson from hiragana_vowels.json...")
    creator1 = ConfigLessonCreator('hiragana_vowels.json')
    lesson1 = creator1.create_lesson()
    
    print("Creating lesson from jlpt_n5_vocab.json...")
    creator2 = ConfigLessonCreator('jlpt_n5_vocab.json')
    lesson2 = creator2.create_lesson()
    
    print("✅ Both lessons created successfully!")
```

## 4. Database-Aware Content Script

### create_vocabulary_lesson_from_db.py
```python
#!/usr/bin/env python3
"""
Database-aware lesson creation that leverages existing content.
"""
from lesson_creator_base import BaseLessonCreator
from app.models import Vocabulary, Kanji, Grammar

class DatabaseAwareLessonCreator(BaseLessonCreator):
    """Lesson creator that integrates with existing database content."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_content = {}
    
    def find_vocabulary_by_jlpt(self, jlpt_level):
        """Find vocabulary entries by JLPT level."""
        return Vocabulary.query.filter_by(jlpt_level=jlpt_level).all()
    
    def find_kanji_by_jlpt(self, jlpt_level):
        """Find kanji entries by JLPT level."""
        return Kanji.query.filter_by(jlpt_level=jlpt_level).all()
    
    def find_grammar_by_jlpt(self, jlpt_level):
        """Find grammar entries by JLPT level."""
        return Grammar.query.filter_by(jlpt_level=jlpt_level).all()
    
    def add_vocabulary_reference_page(self, vocab_item):
        """Add a page that references existing vocabulary."""
        self.add_page(f"Vocabulary: {vocab_item.word}", [
            {
                "type": "vocabulary",
                "content_id": vocab_item.id,
                "title": f"Learn: {vocab_item.word}"
            },
            {
                "type": "multiple_choice",
                "topic": f"Quiz about the vocabulary word {vocab_item.word} ({vocab_item.meaning})",
                "keywords": f"{vocab_item.word}, {vocab_item.meaning}, vocabulary"
            }
        ])
    
    def add_kanji_reference_page(self, kanji_item):
        """Add a page that references existing kanji."""
        self.add_page(f"Kanji: {kanji_item.character}", [
            {
                "type": "kanji",
                "content_id": kanji_item.id,
                "title": f"Learn: {kanji_item.character}"
            },
            {
                "type": "multiple_choice",
                "topic": f"Quiz about the kanji {kanji_item.character} meaning {kanji_item.meaning}",
                "keywords": f"{kanji_item.character}, {kanji_item.meaning}, kanji"
            }
        ])
    
    def create_jlpt_vocabulary_lesson(self, jlpt_level, topic_filter=None):
        """Create a lesson using existing JLPT vocabulary."""
        vocab_items = self.find_vocabulary_by_jlpt(jlpt_level)
        
        if not vocab_items:
            print(f"No vocabulary found for JLPT N{jlpt_level}")
            return None
        
        # Filter by topic if specified
        if topic_filter:
            vocab_items = [v for v in vocab_items if topic_filter.lower() in v.meaning.lower()]
        
        # Update lesson title
        self.title = f"JLPT N{jlpt_level} Vocabulary" + (f" - {topic_filter}" if topic_filter else "")
        
        # Add introduction
        self.add_page("Introduction", [
            {
                "type": "formatted_explanation",
                "topic": f"Introduction to JLPT N{jlpt_level} vocabulary with {len(vocab_items)} essential words",
                "keywords": f"JLPT N{jlpt_level}, vocabulary, essential words"
            }
        ])
        
        # Add page for each vocabulary item
        for vocab in vocab_items[:10]:  # Limit to first 10 for demo
            self.add_vocabulary_reference_page(vocab)
        
        # Add review page
        word_list = ", ".join([v.word for v in vocab_items[:10]])
        self.add_page("Vocabulary Review", [
            {
                "type": "formatted_explanation",
                "topic": f"Review of JLPT N{jlpt_level} vocabulary: {word_list}",
                "keywords": f"JLPT N{jlpt_level}, vocabulary, review, {word_list}"
            },
            {
                "type": "matching",
                "topic": f"Match JLPT N{jlpt_level} vocabulary words to their meanings",
                "keywords": f"JLPT N{jlpt_level}, vocabulary, matching"
            }
        ])
        
        return self.create_lesson()

def create_jlpt_n5_family_lesson():
    """Example: Create JLPT N5 family vocabulary lesson."""
    creator = DatabaseAwareLessonCreator(
        title="JLPT N5 Family Vocabulary",
        difficulty="beginner",
        category_name="JLPT N

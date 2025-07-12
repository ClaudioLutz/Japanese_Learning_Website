"""
Personalized Lesson Generator for Phase 5: Intelligence and Adaptation
Generates adaptive lessons based on user performance analysis.
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from flask import current_app
from app.ai_services import AILessonContentGenerator
from app.user_performance_analyzer import UserPerformanceAnalyzer
from app.models import (
    User, Lesson, LessonContent, LessonCategory, Kanji, Vocabulary, Grammar,
    QuizQuestion, QuizOption
)
from app import db


class PersonalizedLessonGenerator:
    """
    Generates personalized lessons based on user performance analysis
    and adaptive content generation strategies.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.query.get(user_id)
        if not self.user:
            raise ValueError(f"User with ID {user_id} not found")
        
        self.performance_analyzer = UserPerformanceAnalyzer(user_id)
        self.ai_generator = AILessonContentGenerator()
    
    def generate_personalized_lesson(self, lesson_type: str = "remedial") -> Dict[str, Any]:
        """
        Generate a personalized lesson based on user's performance analysis.
        
        Args:
            lesson_type: Type of lesson to generate ('remedial', 'advancement', 'review')
            
        Returns:
            Dict containing the generated lesson data and metadata
        """
        # Analyze user performance
        weakness_analysis = self.performance_analyzer.analyze_weaknesses()
        remediation_suggestions = self.performance_analyzer.suggest_remediation(weakness_analysis)
        
        # Generate lesson based on analysis
        if lesson_type == "remedial":
            lesson_data = self._generate_remedial_lesson(weakness_analysis, remediation_suggestions)
        elif lesson_type == "advancement":
            lesson_data = self._generate_advancement_lesson(weakness_analysis)
        elif lesson_type == "review":
            lesson_data = self._generate_review_lesson(weakness_analysis)
        else:
            raise ValueError(f"Unknown lesson type: {lesson_type}")
        
        # Create the lesson in database
        lesson_id = self._create_lesson_in_database(lesson_data)
        
        return {
            'lesson_id': lesson_id,
            'lesson_type': lesson_type,
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': self.user_id,
            'performance_analysis': weakness_analysis,
            'lesson_data': lesson_data,
            'success': True
        }
    
    def _generate_remedial_lesson(self, analysis: Dict[str, Any], suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a remedial lesson targeting user's weak areas."""
        priority_areas = suggestions.get('priority_areas', [])
        
        if not priority_areas:
            return self._generate_general_review_lesson()
        
        # Focus on the highest priority weakness
        primary_weakness = priority_areas[0]
        weakness_type = primary_weakness['type']
        weakness_area = primary_weakness['area']
        
        lesson_data = {
            'title': f"Remedial Practice: {weakness_area.replace('_', ' ').title()}",
            'description': f"Targeted practice to improve your {weakness_area.replace('_', ' ')} skills",
            'lesson_type': 'free',  # Remedial lessons are always free
            'difficulty_level': 1,  # Start with easier content
            'estimated_duration': 25,
            'instruction_language': 'english',
            'content_items': [],
            'category_name': 'Personalized Practice'
        }
        
        if weakness_type == 'content_type':
            lesson_data['content_items'] = self._generate_content_type_remediation(weakness_area, analysis)
        elif weakness_type == 'topic':
            lesson_data['content_items'] = self._generate_content_type_remediation('mixed', analysis)
        elif weakness_type == 'difficulty':
            lesson_data['content_items'] = self._generate_content_type_remediation('mixed', analysis)
        
        return lesson_data
    
    def _generate_advancement_lesson(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an advancement lesson for areas where user is performing well."""
        overall_score = analysis.get('overall_score', 0)
        
        # Determine next level content based on performance
        if overall_score >= 85:
            difficulty_level = 4
            advancement_type = "Advanced Practice"
        elif overall_score >= 70:
            difficulty_level = 3
            advancement_type = "Intermediate Plus"
        else:
            difficulty_level = 2
            advancement_type = "Progressive Practice"
        
        lesson_data = {
            'title': f"{advancement_type}: Next Level Challenge",
            'description': f"Advanced content to challenge your growing skills",
            'lesson_type': 'free',
            'difficulty_level': difficulty_level,
            'estimated_duration': 35,
            'instruction_language': 'english',
            'content_items': [],
            'category_name': 'Advancement'
        }
        
        # Generate challenging content in user's strong areas
        strong_areas = self._identify_strong_areas(analysis)
        lesson_data['content_items'] = self._generate_advancement_content(strong_areas, difficulty_level)
        
        return lesson_data
    
    def _generate_review_lesson(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive review lesson."""
        lesson_data = {
            'title': "Personalized Review Session",
            'description': "Comprehensive review of your recent learning",
            'lesson_type': 'free',
            'difficulty_level': 2,
            'estimated_duration': 30,
            'instruction_language': 'english',
            'content_items': [],
            'category_name': 'Review'
        }
        
        # Mix of content types based on user's history
        lesson_data['content_items'] = self._generate_mixed_review_content(analysis)
        
        return lesson_data
    
    def _generate_content_type_remediation(self, content_type: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate remediation content for specific content type (kanji, vocabulary, grammar)."""
        content_items = []
        
        # Add explanatory content
        content_items.append({
            'content_type': 'text',
            'title': f"{content_type.title()} Practice Session",
            'content_text': self._generate_remedial_explanation(content_type, analysis),
            'page_number': 1,
            'order_index': 0
        })
        
        # Add practice content based on type
        if content_type == 'kanji':
            content_items.extend(self._generate_kanji_practice_content())
        elif content_type == 'vocabulary':
            content_items.extend(self._generate_vocabulary_practice_content())
        elif content_type == 'grammar':
            content_items.extend(self._generate_grammar_practice_content())
        
        # Add adaptive quiz
        content_items.append(self._generate_adaptive_quiz(content_type, difficulty_level=1))
        
        return content_items
    
    def _generate_remedial_explanation(self, content_type: str, analysis: Dict[str, Any]) -> str:
        """Generate AI-powered remedial explanation."""
        weakness_details = analysis.get('content_type_weaknesses', {}).get(content_type, {})
        
        system_prompt = (
            "You are a Japanese language tutor creating personalized remedial content. "
            "Generate encouraging, helpful explanations that address specific weaknesses."
        )
        
        user_prompt = f"""
        Create a remedial explanation for {content_type} practice.
        
        User's Performance Data:
        - Accuracy: {weakness_details.get('accuracy_percentage', 0)}%
        - Average Attempts: {weakness_details.get('average_attempts', 0)}
        - Total Questions: {weakness_details.get('total_questions', 0)}
        
        Create an encouraging explanation that:
        1. Acknowledges the challenge
        2. Provides helpful study tips
        3. Explains why this content type is important
        4. Motivates continued practice
        
        Keep it concise but supportive (2-3 paragraphs).
        """
        
        result = self.ai_generator.generate_explanation(content_type, "beginner", "remedial practice")
        return result.get('generated_text') or f"Let's practice {content_type} together!"
    
    def _generate_kanji_practice_content(self) -> List[Dict[str, Any]]:
        """Generate kanji practice content items."""
        content_items = []
        
        # Get some basic kanji for practice
        basic_kanji = Kanji.query.filter(
            Kanji.jlpt_level >= 4,
            Kanji.status == 'approved'
        ).limit(5).all()
        
        for i, kanji in enumerate(basic_kanji):
            content_items.append({
                'content_type': 'kanji',
                'content_id': kanji.id,
                'page_number': 2,
                'order_index': i
            })
        
        return content_items
    
    def _generate_vocabulary_practice_content(self) -> List[Dict[str, Any]]:
        """Generate vocabulary practice content items."""
        content_items = []
        
        # Get basic vocabulary
        basic_vocab = Vocabulary.query.filter(
            Vocabulary.jlpt_level >= 4,
            Vocabulary.status == 'approved'
        ).limit(5).all()
        
        for i, vocab in enumerate(basic_vocab):
            content_items.append({
                'content_type': 'vocabulary',
                'content_id': vocab.id,
                'page_number': 2,
                'order_index': i
            })
        
        return content_items
    
    def _generate_grammar_practice_content(self) -> List[Dict[str, Any]]:
        """Generate grammar practice content items."""
        content_items = []
        
        # Get basic grammar points
        basic_grammar = Grammar.query.filter(
            Grammar.jlpt_level >= 4,
            Grammar.status == 'approved'
        ).limit(3).all()
        
        for i, grammar in enumerate(basic_grammar):
            content_items.append({
                'content_type': 'grammar',
                'content_id': grammar.id,
                'page_number': 2,
                'order_index': i
            })
        
        return content_items
    
    def _generate_adaptive_quiz(self, topic: str, difficulty_level: int = 1) -> Dict[str, Any]:
        """Generate an adaptive quiz for the given topic."""
        quiz_data = self.ai_generator.create_adaptive_quiz(
            topic=topic,
            difficulty_levels=[difficulty_level, difficulty_level + 1],
            num_questions_per_level=3
        )
        
        return {
            'content_type': 'text',
            'title': f"{topic.title()} Practice Quiz",
            'content_text': "Test your understanding with this adaptive quiz.",
            'is_interactive': True,
            'quiz_type': 'adaptive',
            'max_attempts': 3,
            'passing_score': 70,
            'page_number': 3,
            'order_index': 0,
            'quiz_data': quiz_data,
            'generated_by_ai': True,
            'ai_generation_details': {
                'model': 'gpt-4',
                'generated_at': datetime.utcnow().isoformat(),
                'topic': topic,
                'difficulty_level': difficulty_level
            }
        }
    
    def _identify_strong_areas(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify areas where user is performing well."""
        strong_areas = []
        
        content_weaknesses = analysis.get('content_type_weaknesses', {})
        for content_type, stats in content_weaknesses.items():
            if not stats.get('is_weakness', True) and stats.get('accuracy_percentage', 0) >= 80:
                strong_areas.append(content_type)
        
        return strong_areas if strong_areas else ['vocabulary']  # Default to vocabulary
    
    def _generate_advancement_content(self, strong_areas: List[str], difficulty_level: int) -> List[Dict[str, Any]]:
        """Generate challenging content for advancement."""
        content_items = []
        
        # Introduction
        content_items.append({
            'content_type': 'text',
            'title': 'Ready for the Next Challenge?',
            'content_text': self._generate_advancement_intro(strong_areas, difficulty_level),
            'page_number': 1,
            'order_index': 0
        })
        
        # Advanced content in strong areas
        for i, area in enumerate(strong_areas[:2]):  # Limit to 2 areas
            if area == 'kanji':
                advanced_kanji = Kanji.query.filter(
                    Kanji.jlpt_level <= 3,
                    Kanji.status == 'approved'
                ).limit(3).all()
                
                for j, kanji in enumerate(advanced_kanji):
                    content_items.append({
                        'content_type': 'kanji',
                        'content_id': kanji.id,
                        'page_number': 2 + i,
                        'order_index': j
                    })
        
        # Challenging quiz
        content_items.append(self._generate_adaptive_quiz("advanced_practice", difficulty_level))
        
        return content_items
    
    def _generate_advancement_intro(self, strong_areas: List[str], difficulty_level: int) -> str:
        """Generate introduction for advancement lesson."""
        areas_text = ", ".join(strong_areas)
        return f"""
        <h2>Congratulations on Your Progress!</h2>
        <p>You've shown strong performance in {areas_text}. It's time to challenge yourself with more advanced content!</p>
        <p>This lesson will push your skills to the next level with difficulty level {difficulty_level} content. 
        Take your time and don't worry if it feels challenging - that's how we grow!</p>
        """
    
    def _generate_mixed_review_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mixed content for comprehensive review."""
        content_items = []
        
        # Review introduction
        content_items.append({
            'content_type': 'text',
            'title': 'Your Personalized Review',
            'content_text': self._generate_review_intro(analysis),
            'page_number': 1,
            'order_index': 0
        })
        
        # Mix of content types
        content_types = ['kanji', 'vocabulary', 'grammar']
        for i, content_type in enumerate(content_types):
            # Add 2-3 items of each type
            if content_type == 'kanji':
                items = Kanji.query.filter(Kanji.status == 'approved').limit(2).all()
                for j, item in enumerate(items):
                    content_items.append({
                        'content_type': 'kanji',
                        'content_id': item.id,
                        'page_number': 2,
                        'order_index': i * 3 + j
                    })
            elif content_type == 'vocabulary':
                items = Vocabulary.query.filter(Vocabulary.status == 'approved').limit(2).all()
                for j, item in enumerate(items):
                    content_items.append({
                        'content_type': 'vocabulary',
                        'content_id': item.id,
                        'page_number': 2,
                        'order_index': i * 3 + j
                    })
            elif content_type == 'grammar':
                items = Grammar.query.filter(Grammar.status == 'approved').limit(2).all()
                for j, item in enumerate(items):
                    content_items.append({
                        'content_type': 'grammar',
                        'content_id': item.id,
                        'page_number': 2,
                        'order_index': i * 3 + j
                    })
        
        # Review quiz
        content_items.append(self._generate_adaptive_quiz("mixed_review", difficulty_level=2))
        
        return content_items
    
    def _generate_review_intro(self, analysis: Dict[str, Any]) -> str:
        """Generate introduction for review lesson."""
        overall_score = analysis.get('overall_score', 0)
        lessons_completed = analysis.get('time_patterns', {}).get('lessons_completed', 0)
        
        return f"""
        <h2>Time for Review!</h2>
        <p>You've completed {lessons_completed} lessons with an overall performance score of {overall_score}%. 
        Let's review some key concepts to reinforce your learning.</p>
        <p>This mixed review will help consolidate your knowledge across different areas of Japanese.</p>
        """
    
    def _generate_general_review_lesson(self) -> Dict[str, Any]:
        """Generate a general review lesson when no specific weaknesses are identified."""
        return {
            'title': "General Japanese Review",
            'description': "A balanced review of Japanese fundamentals",
            'lesson_type': 'free',
            'difficulty_level': 2,
            'estimated_duration': 20,
            'instruction_language': 'english',
            'content_items': [
                {
                    'content_type': 'text',
                    'title': 'Keep Up the Great Work!',
                    'content_text': '<p>You\'re doing well! Let\'s review some fundamentals to keep your skills sharp.</p>',
                    'page_number': 1,
                    'order_index': 0
                }
            ],
            'category_name': 'General Review'
        }
    
    def _create_lesson_in_database(self, lesson_data: Dict[str, Any]) -> int:
        """Create the generated lesson in the database."""
        try:
            # Get or create category
            category = LessonCategory.query.filter_by(name=lesson_data['category_name']).first()
            if not category:
                category = LessonCategory(
                    name=lesson_data['category_name'],
                    description=f"Personalized lessons for {self.user.username if self.user else 'user'}",
                    color_code='#28a745'  # Green for personalized content
                )
                db.session.add(category)
                db.session.flush()
            
            # Create lesson
            lesson = Lesson(
                title=lesson_data['title'],
                description=lesson_data['description'],
                lesson_type=lesson_data['lesson_type'],
                category_id=category.id,
                difficulty_level=lesson_data['difficulty_level'],
                estimated_duration=lesson_data['estimated_duration'],
                instruction_language=lesson_data['instruction_language'],
                is_published=True
            )
            db.session.add(lesson)
            db.session.flush()
            
            # Create content items
            for content_data in lesson_data['content_items']:
                content_item = LessonContent(
                    lesson_id=lesson.id,
                    content_type=content_data['content_type'],
                    content_id=content_data.get('content_id'),
                    title=content_data.get('title'),
                    content_text=content_data.get('content_text'),
                    page_number=content_data.get('page_number', 1),
                    order_index=content_data.get('order_index', 0),
                    is_interactive=content_data.get('is_interactive', False),
                    quiz_type=content_data.get('quiz_type', 'standard'),
                    max_attempts=content_data.get('max_attempts', 3),
                    passing_score=content_data.get('passing_score', 70),
                    generated_by_ai=content_data.get('generated_by_ai', True),
                    ai_generation_details=content_data.get('ai_generation_details')
                )
                db.session.add(content_item)
                
                # Create quiz questions if this is an interactive item
                if content_data.get('is_interactive') and content_data.get('quiz_data'):
                    db.session.flush()  # Get content_item.id
                    self._create_quiz_questions(content_item.id, content_data['quiz_data'])
            
            db.session.commit()
            return lesson.id
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating personalized lesson: {e}")
            raise
    
    def _create_quiz_questions(self, content_id: int, quiz_data: Dict[str, Any]) -> None:
        """Create quiz questions from AI-generated quiz data."""
        questions = quiz_data.get('questions', [])
        
        for i, question_data in enumerate(questions):
            question = QuizQuestion(
                lesson_content_id=content_id,
                question_type='multiple_choice',
                question_text=question_data.get('question_text', ''),
                explanation=question_data.get('overall_explanation', ''),
                hint=question_data.get('hint', ''),
                difficulty_level=question_data.get('difficulty_level', 1),
                points=1,
                order_index=i
            )
            db.session.add(question)
            db.session.flush()
            
            # Create options
            options = question_data.get('options', [])
            for j, option_data in enumerate(options):
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data.get('text', ''),
                    is_correct=option_data.get('is_correct', False),
                    order_index=j,
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(option)
    
    def generate_study_plan(self, weeks: int = 4) -> Dict[str, Any]:
        """
        Generate a personalized study plan for the specified number of weeks.
        
        Args:
            weeks: Number of weeks to plan for
            
        Returns:
            Dict containing the study plan
        """
        analysis = self.performance_analyzer.analyze_weaknesses()
        suggestions = self.performance_analyzer.suggest_remediation(analysis)
        
        study_plan = {
            'user_id': self.user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'duration_weeks': weeks,
            'weekly_plans': [],
            'overall_goals': [],
            'performance_baseline': analysis
        }
        
        # Generate weekly plans
        for week in range(1, weeks + 1):
            weekly_plan = self._generate_weekly_plan(week, analysis, suggestions)
            study_plan['weekly_plans'].append(weekly_plan)
        
        # Set overall goals
        study_plan['overall_goals'] = self._generate_overall_goals(analysis, weeks)
        
        return study_plan
    
    def _generate_weekly_plan(self, week_number: int, analysis: Dict[str, Any], suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a plan for a specific week."""
        priority_areas = suggestions.get('priority_areas', [])
        
        # Adjust focus based on week number
        if week_number <= 2:
            focus = "remediation"
            target_areas = priority_areas[:2]  # Focus on top 2 weaknesses
        elif week_number <= 3:
            focus = "reinforcement"
            target_areas = priority_areas[2:4] if len(priority_areas) > 2 else priority_areas
        else:
            focus = "advancement"
            target_areas = self._identify_strong_areas(analysis)
        
        return {
            'week': week_number,
            'focus': focus,
            'target_areas': [area.get('area', 'unknown') if isinstance(area, dict) else str(area) for area in target_areas] if target_areas else ['general_review'],
            'recommended_lessons': 3,
            'study_time_minutes': 90,
            'goals': [
                f"Focus on {focus} in week {week_number}",
                f"Complete 3 personalized lessons",
                f"Spend 90 minutes studying"
            ]
        }
    
    def _generate_overall_goals(self, analysis: Dict[str, Any], weeks: int) -> List[str]:
        """Generate overall goals for the study plan."""
        current_score = analysis.get('overall_score', 0)
        target_score = min(current_score + (weeks * 5), 95)  # Aim for 5 points improvement per week
        
        return [
            f"Improve overall performance score from {current_score}% to {target_score}%",
            f"Complete {weeks * 3} personalized lessons",
            "Address identified weak areas systematically",
            "Build consistent study habits",
            "Advance to more challenging content"
        ]

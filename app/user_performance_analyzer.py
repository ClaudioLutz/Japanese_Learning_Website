"""
User Performance Analyzer for Phase 5: Intelligence and Adaptation
Analyzes user performance data to identify weaknesses and suggest remediation.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from flask import current_app
from app.models import (
    User, UserLessonProgress, UserQuizAnswer, QuizQuestion, 
    LessonContent, Lesson, Kanji, Vocabulary, Grammar
)
from app import db


class UserPerformanceAnalyzer:
    """
    Analyzes user performance data to identify learning patterns,
    weaknesses, and suggest personalized content generation.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.query.get(user_id)
        if not self.user:
            raise ValueError(f"User with ID {user_id} not found")
    
    def analyze_weaknesses(self) -> Dict[str, Any]:
        """
        Identify struggling areas based on user performance data.
        
        Returns:
            Dict containing weakness analysis with categories:
            - content_types: Which content types user struggles with
            - difficulty_levels: Which difficulty levels are problematic
            - topics: Specific topics needing attention
            - quiz_performance: Quiz-specific weaknesses
            - time_patterns: Time-based learning patterns
        """
        analysis = {
            'user_id': self.user_id,
            'analysis_date': datetime.utcnow().isoformat(),
            'content_type_weaknesses': self._analyze_content_type_performance(),
            'difficulty_weaknesses': self._analyze_difficulty_performance(),
            'topic_weaknesses': self._analyze_topic_performance(),
            'quiz_weaknesses': self._analyze_quiz_performance(),
            'time_patterns': self._analyze_time_patterns(),
            'overall_score': self._calculate_overall_performance_score()
        }
        
        return analysis
    
    def _analyze_content_type_performance(self) -> Dict[str, Any]:
        """Analyze performance across different content types (kanji, vocabulary, grammar)."""
        content_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'avg_attempts': 0})
        
        # Get all quiz answers for the user
        quiz_answers = db.session.query(UserQuizAnswer, QuizQuestion, LessonContent).join(
            QuizQuestion, UserQuizAnswer.question_id == QuizQuestion.id
        ).join(
            LessonContent, QuizQuestion.lesson_content_id == LessonContent.id
        ).filter(UserQuizAnswer.user_id == self.user_id).all()
        
        for answer, question, content in quiz_answers:
            content_type = content.content_type
            content_performance[content_type]['total'] += 1
            if answer.is_correct:
                content_performance[content_type]['correct'] += 1
            content_performance[content_type]['avg_attempts'] += answer.attempts
        
        # Calculate percentages and identify weaknesses
        weaknesses = {}
        for content_type, stats in content_performance.items():
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                avg_attempts = stats['avg_attempts'] / stats['total']
                
                weaknesses[content_type] = {
                    'accuracy_percentage': round(accuracy, 2),
                    'total_questions': stats['total'],
                    'correct_answers': stats['correct'],
                    'average_attempts': round(avg_attempts, 2),
                    'is_weakness': accuracy < 70 or avg_attempts > 2
                }
        
        return weaknesses
    
    def _analyze_difficulty_performance(self) -> Dict[str, Any]:
        """Analyze performance across different difficulty levels."""
        difficulty_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        quiz_answers = db.session.query(UserQuizAnswer, QuizQuestion).join(
            QuizQuestion, UserQuizAnswer.question_id == QuizQuestion.id
        ).filter(UserQuizAnswer.user_id == self.user_id).all()
        
        for answer, question in quiz_answers:
            difficulty = question.difficulty_level
            difficulty_performance[difficulty]['total'] += 1
            if answer.is_correct:
                difficulty_performance[difficulty]['correct'] += 1
        
        weaknesses = {}
        for difficulty, stats in difficulty_performance.items():
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                weaknesses[f"level_{difficulty}"] = {
                    'accuracy_percentage': round(accuracy, 2),
                    'total_questions': stats['total'],
                    'correct_answers': stats['correct'],
                    'is_weakness': accuracy < 70
                }
        
        return weaknesses
    
    def _analyze_topic_performance(self) -> Dict[str, Any]:
        """Analyze performance on specific topics/lessons."""
        lesson_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'completion_rate': 0})
        
        # Get lesson progress
        progress_records = UserLessonProgress.query.filter_by(user_id=self.user_id).all()
        
        for progress in progress_records:
            lesson = progress.lesson
            lesson_performance[lesson.title]['completion_rate'] = progress.progress_percentage
            
            # Get quiz performance for this lesson
            quiz_answers = db.session.query(UserQuizAnswer, QuizQuestion, LessonContent).join(
                QuizQuestion, UserQuizAnswer.question_id == QuizQuestion.id
            ).join(
                LessonContent, QuizQuestion.lesson_content_id == LessonContent.id
            ).filter(
                UserQuizAnswer.user_id == self.user_id,
                LessonContent.lesson_id == lesson.id
            ).all()
            
            for answer, question, content in quiz_answers:
                lesson_performance[lesson.title]['total'] += 1
                if answer.is_correct:
                    lesson_performance[lesson.title]['correct'] += 1
        
        # Identify problematic topics
        topic_weaknesses = {}
        for topic, stats in lesson_performance.items():
            quiz_accuracy = 0
            if stats['total'] > 0:
                quiz_accuracy = (stats['correct'] / stats['total']) * 100
            
            topic_weaknesses[topic] = {
                'completion_rate': stats['completion_rate'],
                'quiz_accuracy': round(quiz_accuracy, 2),
                'total_quiz_questions': stats['total'],
                'is_weakness': stats['completion_rate'] < 80 or quiz_accuracy < 70
            }
        
        return topic_weaknesses
    
    def _analyze_quiz_performance(self) -> Dict[str, Any]:
        """Analyze specific quiz performance patterns."""
        quiz_stats = {
            'total_questions_attempted': 0,
            'total_correct': 0,
            'average_attempts_per_question': 0,
            'question_types_performance': defaultdict(lambda: {'correct': 0, 'total': 0}),
            'common_mistakes': []
        }
        
        quiz_answers = db.session.query(UserQuizAnswer, QuizQuestion).join(
            QuizQuestion, UserQuizAnswer.question_id == QuizQuestion.id
        ).filter(UserQuizAnswer.user_id == self.user_id).all()
        
        total_attempts = 0
        for answer, question in quiz_answers:
            quiz_stats['total_questions_attempted'] += 1
            total_attempts += answer.attempts
            
            if answer.is_correct:
                quiz_stats['total_correct'] += 1
            
            # Track performance by question type
            q_type = question.question_type
            quiz_stats['question_types_performance'][q_type]['total'] += 1
            if answer.is_correct:
                quiz_stats['question_types_performance'][q_type]['correct'] += 1
        
        if quiz_stats['total_questions_attempted'] > 0:
            quiz_stats['overall_accuracy'] = round(
                (quiz_stats['total_correct'] / quiz_stats['total_questions_attempted']) * 100, 2
            )
            quiz_stats['average_attempts_per_question'] = round(
                total_attempts / quiz_stats['total_questions_attempted'], 2
            )
        
        # Convert defaultdict to regular dict for JSON serialization
        quiz_stats['question_types_performance'] = dict(quiz_stats['question_types_performance'])
        
        return quiz_stats
    
    def _analyze_time_patterns(self) -> Dict[str, Any]:
        """Analyze time-based learning patterns."""
        progress_records = UserLessonProgress.query.filter_by(user_id=self.user_id).all()
        
        time_patterns = {
            'total_time_spent': 0,
            'average_session_length': 0,
            'lessons_completed': 0,
            'lessons_started': len(progress_records),
            'completion_rate': 0,
            'recent_activity': self._get_recent_activity()
        }
        
        completed_lessons = 0
        for progress in progress_records:
            time_patterns['total_time_spent'] += progress.time_spent
            if progress.is_completed:
                completed_lessons += 1
        
        time_patterns['lessons_completed'] = completed_lessons
        if len(progress_records) > 0:
            time_patterns['completion_rate'] = round((completed_lessons / len(progress_records)) * 100, 2)
            time_patterns['average_session_length'] = round(
                time_patterns['total_time_spent'] / len(progress_records), 2
            )
        
        return time_patterns
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent activity patterns."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_progress = UserLessonProgress.query.filter(
            UserLessonProgress.user_id == self.user_id,
            UserLessonProgress.last_accessed >= thirty_days_ago
        ).all()
        
        very_recent_progress = UserLessonProgress.query.filter(
            UserLessonProgress.user_id == self.user_id,
            UserLessonProgress.last_accessed >= seven_days_ago
        ).all()
        
        return {
            'lessons_accessed_last_30_days': len(recent_progress),
            'lessons_accessed_last_7_days': len(very_recent_progress),
            'is_active_learner': len(very_recent_progress) > 0
        }
    
    def _calculate_overall_performance_score(self) -> float:
        """Calculate an overall performance score (0-100)."""
        quiz_answers = UserQuizAnswer.query.filter_by(user_id=self.user_id).all()
        progress_records = UserLessonProgress.query.filter_by(user_id=self.user_id).all()
        
        if not quiz_answers and not progress_records:
            return 0.0
        
        # Quiz performance component (40% of score)
        quiz_score = 0.0
        if quiz_answers:
            correct_answers = sum(1 for answer in quiz_answers if answer.is_correct)
            quiz_score = (correct_answers / len(quiz_answers)) * 40
        
        # Lesson completion component (40% of score)
        completion_score = 0.0
        if progress_records:
            avg_completion = sum(p.progress_percentage for p in progress_records) / len(progress_records)
            completion_score = (avg_completion / 100) * 40
        
        # Consistency component (20% of score)
        consistency_score = 0.0
        if progress_records:
            recent_activity = self._get_recent_activity()
            if recent_activity['is_active_learner']:
                consistency_score = 20
            elif recent_activity['lessons_accessed_last_30_days'] > 0:
                consistency_score = 10
        
        return round(quiz_score + completion_score + consistency_score, 2)
    
    def suggest_remediation(self, weakness_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate targeted content suggestions based on weakness analysis.
        
        Args:
            weakness_analysis: Output from analyze_weaknesses()
            
        Returns:
            Dict containing remediation suggestions
        """
        suggestions = {
            'user_id': self.user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'priority_areas': [],
            'content_suggestions': [],
            'study_plan': [],
            'difficulty_adjustments': {}
        }
        
        # Identify priority areas
        priority_areas = self._identify_priority_areas(weakness_analysis)
        suggestions['priority_areas'] = priority_areas
        
        # Generate content suggestions
        content_suggestions = self._generate_content_suggestions(weakness_analysis, priority_areas)
        suggestions['content_suggestions'] = content_suggestions
        
        # Create study plan
        study_plan = self._create_study_plan(weakness_analysis, priority_areas)
        suggestions['study_plan'] = study_plan
        
        # Suggest difficulty adjustments
        difficulty_adjustments = self._suggest_difficulty_adjustments(weakness_analysis)
        suggestions['difficulty_adjustments'] = difficulty_adjustments
        
        return suggestions
    
    def _identify_priority_areas(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify the most critical areas needing attention."""
        priority_areas = []
        
        # Check content type weaknesses
        for content_type, stats in analysis['content_type_weaknesses'].items():
            if stats.get('is_weakness', False):
                priority_areas.append({
                    'type': 'content_type',
                    'area': content_type,
                    'severity': 'high' if stats['accuracy_percentage'] < 50 else 'medium',
                    'details': f"Low accuracy ({stats['accuracy_percentage']}%) in {content_type}"
                })
        
        # Check topic weaknesses
        for topic, stats in analysis['topic_weaknesses'].items():
            if stats.get('is_weakness', False):
                severity = 'high' if stats['completion_rate'] < 50 or stats['quiz_accuracy'] < 50 else 'medium'
                priority_areas.append({
                    'type': 'topic',
                    'area': topic,
                    'severity': severity,
                    'details': f"Topic needs attention: {stats['completion_rate']}% completion, {stats['quiz_accuracy']}% quiz accuracy"
                })
        
        # Check difficulty level issues
        for level, stats in analysis['difficulty_weaknesses'].items():
            if stats.get('is_weakness', False):
                priority_areas.append({
                    'type': 'difficulty',
                    'area': level,
                    'severity': 'medium',
                    'details': f"Struggling with {level}: {stats['accuracy_percentage']}% accuracy"
                })
        
        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        priority_areas.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return priority_areas[:5]  # Return top 5 priority areas
    
    def _generate_content_suggestions(self, analysis: Dict[str, Any], priority_areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific content creation suggestions."""
        suggestions = []
        
        for area in priority_areas:
            if area['type'] == 'content_type':
                content_type = area['area']
                if content_type == 'kanji':
                    suggestions.append({
                        'type': 'remedial_lesson',
                        'content_type': 'kanji',
                        'title': 'Kanji Review and Practice',
                        'description': 'Focused kanji practice with stroke order and mnemonics',
                        'difficulty': 'adaptive',
                        'estimated_duration': 30
                    })
                elif content_type == 'vocabulary':
                    suggestions.append({
                        'type': 'remedial_lesson',
                        'content_type': 'vocabulary',
                        'title': 'Vocabulary Reinforcement',
                        'description': 'Spaced repetition vocabulary practice',
                        'difficulty': 'adaptive',
                        'estimated_duration': 25
                    })
                elif content_type == 'grammar':
                    suggestions.append({
                        'type': 'remedial_lesson',
                        'content_type': 'grammar',
                        'title': 'Grammar Pattern Practice',
                        'description': 'Interactive grammar exercises with examples',
                        'difficulty': 'adaptive',
                        'estimated_duration': 35
                    })
            
            elif area['type'] == 'topic':
                suggestions.append({
                    'type': 'topic_review',
                    'content_type': 'mixed',
                    'title': f"Review: {area['area']}",
                    'description': f"Comprehensive review of {area['area']} with additional practice",
                    'difficulty': 'review',
                    'estimated_duration': 40
                })
        
        return suggestions
    
    def _create_study_plan(self, analysis: Dict[str, Any], priority_areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create a personalized study plan."""
        study_plan = []
        
        # Immediate actions (next 1-2 sessions)
        immediate_actions = []
        for area in priority_areas[:2]:  # Top 2 priority areas
            immediate_actions.append({
                'session': 'next',
                'action': f"Focus on {area['area']}",
                'duration': 20,
                'type': 'remediation'
            })
        
        # Short-term goals (next week)
        short_term = []
        for area in priority_areas[2:4]:  # Next 2 priority areas
            short_term.append({
                'timeframe': 'this_week',
                'goal': f"Improve {area['area']} performance",
                'target': 'Achieve 80% accuracy',
                'type': 'improvement'
            })
        
        # Long-term recommendations
        overall_score = analysis.get('overall_score', 0)
        if overall_score < 60:
            long_term = [{
                'timeframe': 'next_month',
                'goal': 'Establish consistent study routine',
                'target': 'Study 3-4 times per week',
                'type': 'habit_building'
            }]
        else:
            long_term = [{
                'timeframe': 'next_month',
                'goal': 'Advance to next difficulty level',
                'target': 'Complete current level with 85% accuracy',
                'type': 'progression'
            }]
        
        study_plan = immediate_actions + short_term + long_term
        return study_plan
    
    def _suggest_difficulty_adjustments(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest difficulty level adjustments."""
        adjustments = {}
        
        difficulty_performance = analysis.get('difficulty_weaknesses', {})
        overall_score = analysis.get('overall_score', 0)
        
        if overall_score < 40:
            adjustments['recommendation'] = 'decrease'
            adjustments['reason'] = 'Overall performance is low, suggest easier content'
            adjustments['target_difficulty'] = 1
        elif overall_score > 85:
            adjustments['recommendation'] = 'increase'
            adjustments['reason'] = 'High performance, ready for more challenging content'
            adjustments['target_difficulty'] = 4
        else:
            adjustments['recommendation'] = 'maintain'
            adjustments['reason'] = 'Current difficulty level is appropriate'
            adjustments['target_difficulty'] = 2
        
        # Specific adjustments per content type
        content_adjustments = {}
        for content_type, stats in analysis.get('content_type_weaknesses', {}).items():
            if stats['accuracy_percentage'] < 60:
                content_adjustments[content_type] = 'decrease'
            elif stats['accuracy_percentage'] > 90:
                content_adjustments[content_type] = 'increase'
            else:
                content_adjustments[content_type] = 'maintain'
        
        adjustments['content_specific'] = content_adjustments
        return adjustments

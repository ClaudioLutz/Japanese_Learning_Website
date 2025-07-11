"""
AI-Powered Content Validation for Phase 5: Intelligence and Adaptation
Validates content accuracy, cultural context, and educational effectiveness.
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from flask import current_app
from app.ai_services import AILessonContentGenerator
from app.models import (
    Lesson, LessonContent, Kanji, Vocabulary, Grammar,
    QuizQuestion, QuizOption
)
from app import db


class ContentValidator:
    """
    AI-powered content validation system that checks linguistic accuracy,
    cultural context, and educational effectiveness of lesson content.
    """
    
    def __init__(self):
        self.ai_generator = AILessonContentGenerator()
    
    def validate_lesson(self, lesson_id: int) -> Dict[str, Any]:
        """
        Validate an entire lesson including all its content items.
        
        Args:
            lesson_id: ID of the lesson to validate
            
        Returns:
            Dict containing comprehensive validation results
        """
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return {"error": f"Lesson with ID {lesson_id} not found"}
        
        validation_results = {
            'lesson_id': lesson_id,
            'lesson_title': lesson.title,
            'validation_date': datetime.utcnow().isoformat(),
            'overall_score': 0.0,
            'content_validations': [],
            'quiz_validations': [],
            'recommendations': [],
            'issues_found': [],
            'cultural_concerns': [],
            'educational_effectiveness': {}
        }
        
        # Validate each content item
        total_score = 0.0
        content_count = 0
        
        for content_item in lesson.content_items:
            content_validation = self.validate_content_item(content_item)
            validation_results['content_validations'].append(content_validation)
            
            if 'overall_score' in content_validation:
                total_score += content_validation['overall_score']
                content_count += 1
            
            # Collect issues and recommendations
            if content_validation.get('issues'):
                validation_results['issues_found'].extend(content_validation['issues'])
            
            if content_validation.get('cultural_concerns'):
                validation_results['cultural_concerns'].extend(content_validation['cultural_concerns'])
            
            if content_validation.get('recommendations'):
                validation_results['recommendations'].extend(content_validation['recommendations'])
        
        # Validate quiz content
        for content_item in lesson.content_items:
            if content_item.is_interactive and content_item.quiz_questions:
                quiz_validation = self.validate_quiz_content(content_item)
                validation_results['quiz_validations'].append(quiz_validation)
                
                if 'overall_score' in quiz_validation:
                    total_score += quiz_validation['overall_score']
                    content_count += 1
        
        # Calculate overall lesson score
        if content_count > 0:
            validation_results['overall_score'] = round(total_score / content_count, 2)
        
        # Assess educational effectiveness
        validation_results['educational_effectiveness'] = self._assess_educational_effectiveness(lesson)
        
        return validation_results
    
    def validate_content_item(self, content_item: LessonContent) -> Dict[str, Any]:
        """
        Validate a single content item for accuracy and appropriateness.
        
        Args:
            content_item: LessonContent instance to validate
            
        Returns:
            Dict containing validation results for the content item
        """
        validation = {
            'content_id': content_item.id,
            'content_type': content_item.content_type,
            'linguistic_accuracy': {},
            'cultural_context': {},
            'educational_value': {},
            'overall_score': 0.0,
            'issues': [],
            'recommendations': [],
            'cultural_concerns': []
        }
        
        try:
            # Get content data for validation
            content_data = content_item.get_content_data()
            
            if content_item.content_type in ['kanji', 'vocabulary', 'grammar']:
                # Validate database content
                validation.update(self._validate_database_content(content_item, content_data))
            elif content_item.content_type == 'text':
                # Validate text content
                validation.update(self._validate_text_content(content_item))
            
            # Calculate overall score
            scores = []
            if validation['linguistic_accuracy'].get('score'):
                scores.append(validation['linguistic_accuracy']['score'])
            if validation['cultural_context'].get('score'):
                scores.append(validation['cultural_context']['score'])
            if validation['educational_value'].get('score'):
                scores.append(validation['educational_value']['score'])
            
            if scores:
                validation['overall_score'] = round(sum(scores) / len(scores), 2)
        
        except Exception as e:
            current_app.logger.error(f"Error validating content item {content_item.id}: {e}")
            validation['issues'].append(f"Validation error: {str(e)}")
        
        return validation
    
    def _validate_database_content(self, content_item: LessonContent, content_data: Any) -> Dict[str, Any]:
        """Validate kanji, vocabulary, or grammar content from database."""
        validation_update = {
            'linguistic_accuracy': {'score': 0, 'details': []},
            'cultural_context': {'score': 0, 'details': []},
            'educational_value': {'score': 0, 'details': []},
            'issues': [],
            'recommendations': []
        }
        
        if not content_data:
            validation_update['issues'].append("Content data not found in database")
            return validation_update
        
        # Validate based on content type
        if content_item.content_type == 'kanji':
            validation_update.update(self._validate_kanji_accuracy(content_data))
        elif content_item.content_type == 'vocabulary':
            validation_update.update(self._validate_vocabulary_accuracy(content_data))
        elif content_item.content_type == 'grammar':
            validation_update.update(self._validate_grammar_accuracy(content_data))
        
        return validation_update
    
    def _validate_kanji_accuracy(self, kanji: Kanji) -> Dict[str, Any]:
        """Validate kanji character data for accuracy."""
        system_prompt = (
            "You are a Japanese language expert specializing in kanji validation. "
            "Analyze the provided kanji data for accuracy and provide a detailed assessment. "
            "Format your response as JSON."
        )
        
        user_prompt = f"""
        Please validate this kanji data for accuracy:
        
        Character: {kanji.character}
        Meaning: {kanji.meaning}
        Onyomi: {kanji.onyomi}
        Kunyomi: {kanji.kunyomi}
        JLPT Level: N{kanji.jlpt_level}
        Stroke Count: {kanji.stroke_count}
        Radical: {kanji.radical}
        
        Provide a JSON response with:
        {{
          "linguistic_accuracy": {{
            "score": 85,
            "details": ["Accurate readings", "Correct meaning", "Any issues found"]
          }},
          "cultural_context": {{
            "score": 90,
            "details": ["Cultural appropriateness assessment"]
          }},
          "educational_value": {{
            "score": 80,
            "details": ["Educational effectiveness notes"]
          }},
          "issues": ["List any problems found"],
          "recommendations": ["Suggestions for improvement"]
        }}
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error:
            return {
                'linguistic_accuracy': {'score': 0, 'details': [f"Validation error: {error}"]},
                'cultural_context': {'score': 0, 'details': []},
                'educational_value': {'score': 0, 'details': []},
                'issues': [f"AI validation failed: {error}"],
                'recommendations': []
            }
        
        try:
            return json.loads(content) if content else {}
        except json.JSONDecodeError:
            return {
                'linguistic_accuracy': {'score': 0, 'details': ["Failed to parse validation response"]},
                'cultural_context': {'score': 0, 'details': []},
                'educational_value': {'score': 0, 'details': []},
                'issues': ["Validation response parsing failed"],
                'recommendations': []
            }
    
    def _validate_vocabulary_accuracy(self, vocab: Vocabulary) -> Dict[str, Any]:
        """Validate vocabulary data for accuracy."""
        system_prompt = (
            "You are a Japanese language expert specializing in vocabulary validation. "
            "Analyze the provided vocabulary data for accuracy and provide a detailed assessment. "
            "Format your response as JSON."
        )
        
        user_prompt = f"""
        Please validate this vocabulary data for accuracy:
        
        Word: {vocab.word}
        Reading: {vocab.reading}
        Meaning: {vocab.meaning}
        JLPT Level: N{vocab.jlpt_level}
        Example Sentence (Japanese): {vocab.example_sentence_japanese}
        Example Sentence (English): {vocab.example_sentence_english}
        
        Provide a JSON response with the same structure as kanji validation.
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error or not content:
            return self._get_default_validation_result(error or "No response from AI")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._get_default_validation_result("JSON parsing failed")
    
    def _validate_grammar_accuracy(self, grammar: Grammar) -> Dict[str, Any]:
        """Validate grammar point data for accuracy."""
        system_prompt = (
            "You are a Japanese language expert specializing in grammar validation. "
            "Analyze the provided grammar data for accuracy and provide a detailed assessment. "
            "Format your response as JSON."
        )
        
        user_prompt = f"""
        Please validate this grammar data for accuracy:
        
        Title: {grammar.title}
        Explanation: {grammar.explanation}
        Structure: {grammar.structure}
        JLPT Level: N{grammar.jlpt_level}
        Example Sentences: {grammar.example_sentences}
        
        Provide a JSON response with the same structure as previous validations.
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error or not content:
            return self._get_default_validation_result(error or "No response from AI")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._get_default_validation_result("JSON parsing failed")
    
    def _validate_text_content(self, content_item: LessonContent) -> Dict[str, Any]:
        """Validate text content for accuracy and appropriateness."""
        if not content_item.content_text:
            return self._get_default_validation_result("No text content to validate")
        
        system_prompt = (
            "You are a Japanese language education expert. Validate the provided lesson text "
            "for linguistic accuracy, cultural appropriateness, and educational effectiveness. "
            "Format your response as JSON."
        )
        
        user_prompt = f"""
        Please validate this lesson text content:
        
        Title: {content_item.title or 'No title'}
        Content: {content_item.content_text}
        
        Assess for:
        1. Linguistic accuracy (grammar, vocabulary usage, etc.)
        2. Cultural context and appropriateness
        3. Educational value and clarity
        
        Provide a JSON response with scores (0-100) and detailed feedback.
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error or not content:
            return self._get_default_validation_result(error or "No response from AI")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._get_default_validation_result("JSON parsing failed")
    
    def validate_quiz_content(self, content_item: LessonContent) -> Dict[str, Any]:
        """
        Validate quiz questions and options for accuracy and educational value.
        
        Args:
            content_item: LessonContent with quiz questions
            
        Returns:
            Dict containing quiz validation results
        """
        validation = {
            'content_id': content_item.id,
            'quiz_type': content_item.quiz_type,
            'question_validations': [],
            'overall_score': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        total_score = 0.0
        question_count = 0
        
        for question in content_item.quiz_questions:
            question_validation = self._validate_quiz_question(question)
            validation['question_validations'].append(question_validation)
            
            if 'score' in question_validation:
                total_score += question_validation['score']
                question_count += 1
            
            if question_validation.get('issues'):
                validation['issues'].extend(question_validation['issues'])
            
            if question_validation.get('recommendations'):
                validation['recommendations'].extend(question_validation['recommendations'])
        
        if question_count > 0:
            validation['overall_score'] = round(total_score / question_count, 2)
        
        return validation
    
    def _validate_quiz_question(self, question: QuizQuestion) -> Dict[str, Any]:
        """Validate a single quiz question."""
        system_prompt = (
            "You are a Japanese language assessment expert. Validate the provided quiz question "
            "for accuracy, clarity, and educational effectiveness. Format your response as JSON."
        )
        
        # Prepare options text
        options_text = ""
        if question.options:
            options_text = "\n".join([
                f"Option {i+1}: {opt.option_text} (Correct: {opt.is_correct})"
                for i, opt in enumerate(question.options)
            ])
        
        user_prompt = f"""
        Please validate this quiz question:
        
        Question Type: {question.question_type}
        Question Text: {question.question_text}
        Difficulty Level: {question.difficulty_level}
        Explanation: {question.explanation}
        Hint: {question.hint}
        
        Options:
        {options_text}
        
        Provide a JSON response with:
        {{
          "score": 85,
          "accuracy_issues": ["List any accuracy problems"],
          "clarity_issues": ["List any clarity problems"],
          "educational_value": "Assessment of educational effectiveness",
          "issues": ["Overall issues found"],
          "recommendations": ["Suggestions for improvement"]
        }}
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error or not content:
            return {
                'question_id': question.id,
                'score': 0,
                'issues': [f"Validation failed: {error or 'No response'}"],
                'recommendations': []
            }
        
        try:
            result = json.loads(content)
            result['question_id'] = question.id
            return result
        except json.JSONDecodeError:
            return {
                'question_id': question.id,
                'score': 0,
                'issues': ["Failed to parse validation response"],
                'recommendations': []
            }
    
    def _assess_educational_effectiveness(self, lesson: Lesson) -> Dict[str, Any]:
        """Assess the overall educational effectiveness of a lesson."""
        system_prompt = (
            "You are an educational design expert specializing in Japanese language learning. "
            "Assess the educational effectiveness of the provided lesson structure. "
            "Format your response as JSON."
        )
        
        # Prepare lesson structure summary
        content_summary = []
        for content in lesson.content_items:
            content_summary.append({
                'type': content.content_type,
                'title': content.title,
                'is_interactive': content.is_interactive,
                'page_number': content.page_number
            })
        
        user_prompt = f"""
        Please assess the educational effectiveness of this lesson:
        
        Title: {lesson.title}
        Description: {lesson.description}
        Difficulty Level: {lesson.difficulty_level}
        Estimated Duration: {lesson.estimated_duration} minutes
        
        Content Structure:
        {json.dumps(content_summary, indent=2)}
        
        Assess:
        1. Learning progression and flow
        2. Content variety and engagement
        3. Difficulty appropriateness
        4. Interactive elements effectiveness
        
        Provide a JSON response with:
        {{
          "overall_effectiveness_score": 85,
          "learning_progression": {{"score": 80, "notes": "Assessment notes"}},
          "content_variety": {{"score": 90, "notes": "Assessment notes"}},
          "engagement_level": {{"score": 75, "notes": "Assessment notes"}},
          "recommendations": ["List of improvement suggestions"]
        }}
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error or not content:
            return {
                'overall_effectiveness_score': 0,
                'error': f"Assessment failed: {error or 'No response'}"
            }
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                'overall_effectiveness_score': 0,
                'error': "Failed to parse assessment response"
            }
    
    def _get_default_validation_result(self, error_msg: str) -> Dict[str, Any]:
        """Return a default validation result when validation fails."""
        return {
            'linguistic_accuracy': {'score': 0, 'details': [f"Validation error: {error_msg}"]},
            'cultural_context': {'score': 0, 'details': []},
            'educational_value': {'score': 0, 'details': []},
            'issues': [error_msg],
            'recommendations': []
        }
    
    def generate_improvement_suggestions(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate specific improvement suggestions based on validation results.
        
        Args:
            validation_results: Output from validate_lesson()
            
        Returns:
            Dict containing prioritized improvement suggestions
        """
        suggestions = {
            'lesson_id': validation_results.get('lesson_id'),
            'generated_at': datetime.utcnow().isoformat(),
            'priority_improvements': [],
            'content_fixes': [],
            'quiz_improvements': [],
            'educational_enhancements': []
        }
        
        overall_score = validation_results.get('overall_score', 0)
        
        # Prioritize improvements based on severity
        if overall_score < 60:
            suggestions['priority_improvements'].append({
                'priority': 'high',
                'area': 'overall_quality',
                'suggestion': 'Lesson requires comprehensive review and improvement',
                'impact': 'critical'
            })
        
        # Analyze content validation issues
        for content_val in validation_results.get('content_validations', []):
            if content_val.get('overall_score', 0) < 70:
                suggestions['content_fixes'].append({
                    'content_id': content_val['content_id'],
                    'content_type': content_val['content_type'],
                    'issues': content_val.get('issues', []),
                    'recommendations': content_val.get('recommendations', []),
                    'priority': 'high' if content_val.get('overall_score', 0) < 50 else 'medium'
                })
        
        # Analyze quiz validation issues
        for quiz_val in validation_results.get('quiz_validations', []):
            if quiz_val.get('overall_score', 0) < 70:
                suggestions['quiz_improvements'].append({
                    'content_id': quiz_val['content_id'],
                    'issues': quiz_val.get('issues', []),
                    'recommendations': quiz_val.get('recommendations', []),
                    'priority': 'high' if quiz_val.get('overall_score', 0) < 50 else 'medium'
                })
        
        # Educational effectiveness improvements
        edu_effectiveness = validation_results.get('educational_effectiveness', {})
        if edu_effectiveness.get('overall_effectiveness_score', 0) < 75:
            suggestions['educational_enhancements'] = edu_effectiveness.get('recommendations', [])
        
        return suggestions
    
    def validate_cultural_context(self, content_text: str, content_type: str) -> Dict[str, Any]:
        """
        Specifically validate cultural context and appropriateness of content.
        
        Args:
            content_text: Text content to validate
            content_type: Type of content being validated
            
        Returns:
            Dict containing cultural validation results
        """
        system_prompt = (
            "You are a Japanese cultural expert and language educator. "
            "Analyze the provided content for cultural accuracy, appropriateness, "
            "and potential cultural sensitivity issues. Format your response as JSON."
        )
        
        user_prompt = f"""
        Please analyze this {content_type} content for cultural context:
        
        Content: {content_text}
        
        Assess for:
        1. Cultural accuracy and authenticity
        2. Potential cultural sensitivity issues
        3. Appropriateness for language learners
        4. Stereotypes or misconceptions
        
        Provide a JSON response with:
        {{
          "cultural_accuracy_score": 85,
          "sensitivity_issues": ["List any concerns"],
          "authenticity_notes": "Assessment of cultural authenticity",
          "recommendations": ["Suggestions for improvement"],
          "approval_status": "approved/needs_review/rejected"
        }}
        """
        
        content, error = self.ai_generator._generate_content(system_prompt, user_prompt, is_json=True)
        
        if error or not content:
            return {
                'cultural_accuracy_score': 0,
                'error': f"Cultural validation failed: {error or 'No response'}",
                'approval_status': 'needs_review'
            }
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                'cultural_accuracy_score': 0,
                'error': "Failed to parse cultural validation response",
                'approval_status': 'needs_review'
            }

"""
Content Discovery Module for Enhanced Lesson Creation Scripts

This module provides intelligent content discovery and gap analysis capabilities
for database-aware lesson creation. It can find existing content, identify gaps,
and suggest content creation strategies.

Phase 2: Database Integration - Priority 4: Database-Aware Content Scripts
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, func
from app import create_app
from app.models import (
    Kana, Kanji, Vocabulary, Grammar, LessonCategory, 
    Lesson, LessonContent, db
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentDiscovery:
    """
    Intelligent content discovery system for lesson creation scripts.
    
    This class provides methods to:
    - Query existing database content
    - Identify content gaps
    - Suggest related content
    - Analyze content relationships
    """
    
    def __init__(self):
        """Initialize the content discovery system."""
        self.content_types = {
            'kana': Kana,
            'kanji': Kanji,
            'vocabulary': Vocabulary,
            'grammar': Grammar
        }
    
    def find_existing_content(self, content_type: str, criteria: Dict[str, Any]) -> List[Any]:
        """
        Find existing content in the database based on criteria.
        
        Args:
            content_type: Type of content ('kana', 'kanji', 'vocabulary', 'grammar')
            criteria: Dictionary of search criteria
            
        Returns:
            List of matching database objects
        """
        if content_type not in self.content_types:
            logger.error(f"Unknown content type: {content_type}")
            return []
        
        model = self.content_types[content_type]
        query = model.query
        
        try:
            # Apply filters based on criteria
            for field, value in criteria.items():
                if hasattr(model, field):
                    if isinstance(value, list):
                        # Handle list values (e.g., JLPT levels)
                        query = query.filter(getattr(model, field).in_(value))
                    elif isinstance(value, str) and '%' in value:
                        # Handle LIKE queries
                        query = query.filter(getattr(model, field).like(value))
                    else:
                        # Handle exact matches
                        query = query.filter(getattr(model, field) == value)
            
            results = query.all()
            logger.info(f"Found {len(results)} {content_type} entries matching criteria: {criteria}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying {content_type} with criteria {criteria}: {e}")
            return []
    
    def find_kana_by_type(self, kana_type: str) -> List[Kana]:
        """Find all Kana characters of a specific type."""
        return self.find_existing_content('kana', {'type': kana_type})
    
    def find_kanji_by_jlpt_level(self, jlpt_level: int) -> List[Kanji]:
        """Find all Kanji for a specific JLPT level."""
        return self.find_existing_content('kanji', {'jlpt_level': jlpt_level})
    
    def find_vocabulary_by_jlpt_level(self, jlpt_level: int) -> List[Vocabulary]:
        """Find all Vocabulary for a specific JLPT level."""
        return self.find_existing_content('vocabulary', {'jlpt_level': jlpt_level})
    
    def find_grammar_by_jlpt_level(self, jlpt_level: int) -> List[Grammar]:
        """Find all Grammar points for a specific JLPT level."""
        return self.find_existing_content('grammar', {'jlpt_level': jlpt_level})
    
    def find_vocabulary_containing_kanji(self, kanji_character: str) -> List[Vocabulary]:
        """Find vocabulary words that contain a specific kanji character."""
        return self.find_existing_content('vocabulary', {'word': f'%{kanji_character}%'})
    
    def suggest_related_content(self, topic: str, content_type: str = None) -> Dict[str, List[Any]]:
        """
        Suggest related content based on a topic using keyword matching.
        
        Args:
            topic: The topic to search for
            content_type: Specific content type to search, or None for all types
            
        Returns:
            Dictionary with content type as key and list of related items as value
        """
        suggestions = {}
        search_types = [content_type] if content_type else self.content_types.keys()
        
        for ctype in search_types:
            model = self.content_types[ctype]
            related_items = []
            
            try:
                # Search in different fields based on content type
                if ctype == 'kana':
                    # Search in romanization
                    related_items = model.query.filter(
                        model.romanization.like(f'%{topic}%')
                    ).all()
                
                elif ctype == 'kanji':
                    # Search in meaning
                    related_items = model.query.filter(
                        model.meaning.like(f'%{topic}%')
                    ).all()
                
                elif ctype == 'vocabulary':
                    # Search in word, reading, and meaning
                    related_items = model.query.filter(
                        or_(
                            model.word.like(f'%{topic}%'),
                            model.reading.like(f'%{topic}%'),
                            model.meaning.like(f'%{topic}%')
                        )
                    ).all()
                
                elif ctype == 'grammar':
                    # Search in title and explanation
                    related_items = model.query.filter(
                        or_(
                            model.title.like(f'%{topic}%'),
                            model.explanation.like(f'%{topic}%')
                        )
                    ).all()
                
                suggestions[ctype] = related_items
                logger.info(f"Found {len(related_items)} {ctype} items related to '{topic}'")
                
            except Exception as e:
                logger.error(f"Error searching for {ctype} related to '{topic}': {e}")
                suggestions[ctype] = []
        
        return suggestions
    
    def analyze_content_gaps(self, lesson_topic: str, target_jlpt_level: int = None) -> Dict[str, Any]:
        """
        Analyze content gaps for a specific lesson topic and JLPT level.
        
        Args:
            lesson_topic: The topic of the lesson
            target_jlpt_level: Target JLPT level (1-5), or None for all levels
            
        Returns:
            Dictionary containing gap analysis results
        """
        gap_analysis = {
            'topic': lesson_topic,
            'target_jlpt_level': target_jlpt_level,
            'existing_content': {},
            'missing_content': {},
            'recommendations': []
        }
        
        # Find existing content related to the topic
        related_content = self.suggest_related_content(lesson_topic)
        gap_analysis['existing_content'] = related_content
        
        # Analyze gaps based on JLPT level if specified
        if target_jlpt_level:
            gap_analysis['missing_content'] = self._analyze_jlpt_gaps(target_jlpt_level)
        
        # Generate recommendations
        gap_analysis['recommendations'] = self._generate_content_recommendations(
            lesson_topic, related_content, target_jlpt_level
        )
        
        return gap_analysis
    
    def _analyze_jlpt_gaps(self, jlpt_level: int) -> Dict[str, int]:
        """Analyze content gaps for a specific JLPT level."""
        gaps = {}
        
        # Expected content counts for each JLPT level (approximate)
        expected_counts = {
            5: {'kanji': 80, 'vocabulary': 800, 'grammar': 40},
            4: {'kanji': 170, 'vocabulary': 1500, 'grammar': 60},
            3: {'kanji': 370, 'vocabulary': 3750, 'grammar': 90},
            2: {'kanji': 1000, 'vocabulary': 6000, 'grammar': 120},
            1: {'kanji': 2000, 'vocabulary': 10000, 'grammar': 150}
        }
        
        if jlpt_level in expected_counts:
            for content_type in ['kanji', 'vocabulary', 'grammar']:
                model = self.content_types[content_type]
                actual_count = model.query.filter_by(jlpt_level=jlpt_level).count()
                expected_count = expected_counts[jlpt_level][content_type]
                
                if actual_count < expected_count:
                    gaps[content_type] = expected_count - actual_count
                    logger.info(f"JLPT {jlpt_level} {content_type} gap: {gaps[content_type]} items missing")
        
        return gaps
    
    def _generate_content_recommendations(self, topic: str, existing_content: Dict[str, List], 
                                        jlpt_level: int = None) -> List[str]:
        """Generate recommendations for content creation."""
        recommendations = []
        
        # Check if we have basic content types
        for content_type, items in existing_content.items():
            if not items:
                recommendations.append(f"Create {content_type} content for '{topic}'")
            elif len(items) < 5:  # Arbitrary threshold
                recommendations.append(f"Expand {content_type} content for '{topic}' (only {len(items)} items found)")
        
        # JLPT-specific recommendations
        if jlpt_level:
            recommendations.append(f"Ensure content is appropriate for JLPT level {jlpt_level}")
            
            # Check for progression content
            if jlpt_level < 5:
                next_level_content = self.find_kanji_by_jlpt_level(jlpt_level + 1)
                if next_level_content:
                    recommendations.append(f"Consider including preview content from JLPT {jlpt_level + 1}")
        
        return recommendations
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about available content."""
        stats = {
            'total_counts': {},
            'jlpt_distribution': {},
            'content_health': {}
        }
        
        # Total counts
        for content_type, model in self.content_types.items():
            stats['total_counts'][content_type] = model.query.count()
        
        # JLPT distribution
        for content_type in ['kanji', 'vocabulary', 'grammar']:
            model = self.content_types[content_type]
            jlpt_counts = {}
            
            for level in range(1, 6):
                count = model.query.filter_by(jlpt_level=level).count()
                jlpt_counts[f'N{level}'] = count
            
            stats['jlpt_distribution'][content_type] = jlpt_counts
        
        # Content health (completeness indicators)
        stats['content_health'] = {
            'kana_completeness': self._check_kana_completeness(),
            'jlpt_coverage': self._check_jlpt_coverage(),
            'example_coverage': self._check_example_coverage()
        }
        
        return stats
    
    def _check_kana_completeness(self) -> Dict[str, Any]:
        """Check completeness of Kana characters."""
        hiragana_count = Kana.query.filter_by(type='hiragana').count()
        katakana_count = Kana.query.filter_by(type='katakana').count()
        
        # Standard counts (46 basic characters each)
        return {
            'hiragana': {'count': hiragana_count, 'complete': hiragana_count >= 46},
            'katakana': {'count': katakana_count, 'complete': katakana_count >= 46}
        }
    
    def _check_jlpt_coverage(self) -> Dict[str, bool]:
        """Check if we have content for all JLPT levels."""
        coverage = {}
        
        for content_type in ['kanji', 'vocabulary', 'grammar']:
            model = self.content_types[content_type]
            coverage[content_type] = {}
            
            for level in range(1, 6):
                has_content = model.query.filter_by(jlpt_level=level).first() is not None
                coverage[content_type][f'N{level}'] = has_content
        
        return coverage
    
    def _check_example_coverage(self) -> Dict[str, float]:
        """Check what percentage of content has examples."""
        coverage = {}
        
        # Vocabulary example coverage
        vocab_total = Vocabulary.query.count()
        vocab_with_examples = Vocabulary.query.filter(
            and_(
                Vocabulary.example_sentence_japanese.isnot(None),
                Vocabulary.example_sentence_english.isnot(None)
            )
        ).count()
        
        coverage['vocabulary_examples'] = (vocab_with_examples / vocab_total * 100) if vocab_total > 0 else 0
        
        # Grammar example coverage
        grammar_total = Grammar.query.count()
        grammar_with_examples = Grammar.query.filter(
            Grammar.example_sentences.isnot(None)
        ).count()
        
        coverage['grammar_examples'] = (grammar_with_examples / grammar_total * 100) if grammar_total > 0 else 0
        
        return coverage
    
    def find_lesson_content_opportunities(self, existing_lessons: List[str] = None) -> Dict[str, Any]:
        """
        Find opportunities for new lesson content based on existing database content.
        
        Args:
            existing_lessons: List of existing lesson titles to avoid duplication
            
        Returns:
            Dictionary with lesson opportunities and supporting content
        """
        opportunities = {
            'jlpt_focused': {},
            'character_focused': {},
            'thematic': {},
            'skill_building': {}
        }
        
        existing_lessons = existing_lessons or []
        
        # JLPT-focused opportunities
        for level in range(1, 6):
            kanji_count = Kanji.query.filter_by(jlpt_level=level).count()
            vocab_count = Vocabulary.query.filter_by(jlpt_level=level).count()
            grammar_count = Grammar.query.filter_by(jlpt_level=level).count()
            
            if kanji_count > 0 or vocab_count > 0 or grammar_count > 0:
                opportunities['jlpt_focused'][f'JLPT_N{level}'] = {
                    'kanji_available': kanji_count,
                    'vocabulary_available': vocab_count,
                    'grammar_available': grammar_count,
                    'lesson_potential': 'high' if (kanji_count + vocab_count + grammar_count) > 50 else 'medium'
                }
        
        # Character-focused opportunities
        hiragana_count = Kana.query.filter_by(type='hiragana').count()
        katakana_count = Kana.query.filter_by(type='katakana').count()
        
        if hiragana_count > 0:
            opportunities['character_focused']['hiragana'] = {
                'characters_available': hiragana_count,
                'lesson_potential': 'high' if hiragana_count >= 46 else 'medium'
            }
        
        if katakana_count > 0:
            opportunities['character_focused']['katakana'] = {
                'characters_available': katakana_count,
                'lesson_potential': 'high' if katakana_count >= 46 else 'medium'
            }
        
        # Thematic opportunities (based on vocabulary meanings)
        common_themes = ['food', 'family', 'time', 'color', 'number', 'body', 'weather', 'travel']
        for theme in common_themes:
            theme_vocab = self.find_existing_content('vocabulary', {'meaning': f'%{theme}%'})
            if len(theme_vocab) >= 5:  # Minimum threshold for a themed lesson
                opportunities['thematic'][theme] = {
                    'vocabulary_available': len(theme_vocab),
                    'lesson_potential': 'high' if len(theme_vocab) >= 15 else 'medium'
                }
        
        return opportunities


class ContentGapAnalyzer:
    """
    Specialized class for analyzing content gaps and suggesting content creation.
    """
    
    def __init__(self, discovery: ContentDiscovery):
        """Initialize with a ContentDiscovery instance."""
        self.discovery = discovery
    
    def identify_missing_prerequisites(self, lesson_content: List[Dict[str, Any]]) -> List[str]:
        """
        Identify missing prerequisite content for a planned lesson.
        
        Args:
            lesson_content: List of content items planned for the lesson
            
        Returns:
            List of missing prerequisite content descriptions
        """
        missing = []
        
        for content_item in lesson_content:
            content_type = content_item.get('type')
            
            if content_type == 'kanji':
                # Check if we have the kanji in database
                character = content_item.get('character')
                if character:
                    existing = self.discovery.find_existing_content('kanji', {'character': character})
                    if not existing:
                        missing.append(f"Kanji character '{character}' not in database")
            
            elif content_type == 'vocabulary':
                # Check if we have the vocabulary
                word = content_item.get('word')
                if word:
                    existing = self.discovery.find_existing_content('vocabulary', {'word': word})
                    if not existing:
                        missing.append(f"Vocabulary word '{word}' not in database")
            
            elif content_type == 'grammar':
                # Check if we have the grammar point
                title = content_item.get('title')
                if title:
                    existing = self.discovery.find_existing_content('grammar', {'title': title})
                    if not existing:
                        missing.append(f"Grammar point '{title}' not in database")
        
        return missing
    
    def suggest_content_creation_order(self, missing_content: List[str]) -> List[Dict[str, Any]]:
        """
        Suggest the order in which missing content should be created.
        
        Args:
            missing_content: List of missing content descriptions
            
        Returns:
            List of content creation suggestions with priority
        """
        suggestions = []
        
        # Prioritize by content type (Kana -> Kanji -> Vocabulary -> Grammar)
        priority_order = ['kana', 'kanji', 'vocabulary', 'grammar']
        
        for content_desc in missing_content:
            priority = 3  # Default priority
            content_type = 'unknown'
            
            # Determine content type and priority
            if 'kana' in content_desc.lower():
                content_type = 'kana'
                priority = 1
            elif 'kanji' in content_desc.lower():
                content_type = 'kanji'
                priority = 2
            elif 'vocabulary' in content_desc.lower():
                content_type = 'vocabulary'
                priority = 3
            elif 'grammar' in content_desc.lower():
                content_type = 'grammar'
                priority = 4
            
            suggestions.append({
                'description': content_desc,
                'content_type': content_type,
                'priority': priority,
                'creation_method': self._suggest_creation_method(content_type)
            })
        
        # Sort by priority
        suggestions.sort(key=lambda x: x['priority'])
        
        return suggestions
    
    def _suggest_creation_method(self, content_type: str) -> str:
        """Suggest how to create missing content."""
        methods = {
            'kana': 'Use admin interface or create_kana_entries.py script',
            'kanji': 'Use admin interface or create_kanji_entries.py script',
            'vocabulary': 'Use admin interface or create_vocabulary_entries.py script',
            'grammar': 'Use admin interface or create_grammar_entries.py script',
            'unknown': 'Determine content type first'
        }
        
        return methods.get(content_type, methods['unknown'])


# Utility functions for easy access
def get_content_discovery() -> ContentDiscovery:
    """Get a ContentDiscovery instance."""
    return ContentDiscovery()

def get_gap_analyzer() -> ContentGapAnalyzer:
    """Get a ContentGapAnalyzer instance."""
    return ContentGapAnalyzer(get_content_discovery())

def quick_content_search(content_type: str, search_term: str) -> List[Any]:
    """Quick search for content."""
    discovery = get_content_discovery()
    
    if content_type == 'kana':
        return discovery.find_existing_content('kana', {'romanization': f'%{search_term}%'})
    elif content_type == 'kanji':
        return discovery.find_existing_content('kanji', {'meaning': f'%{search_term}%'})
    elif content_type == 'vocabulary':
        return discovery.find_existing_content('vocabulary', {'meaning': f'%{search_term}%'})
    elif content_type == 'grammar':
        return discovery.find_existing_content('grammar', {'title': f'%{search_term}%'})
    else:
        return []

def get_jlpt_content_summary(jlpt_level: int) -> Dict[str, int]:
    """Get a summary of available content for a JLPT level."""
    discovery = get_content_discovery()
    
    return {
        'kanji': len(discovery.find_kanji_by_jlpt_level(jlpt_level)),
        'vocabulary': len(discovery.find_vocabulary_by_jlpt_level(jlpt_level)),
        'grammar': len(discovery.find_grammar_by_jlpt_level(jlpt_level))
    }


if __name__ == "__main__":
    # Example usage and testing
    print("Content Discovery Module - Example Usage")
    print("=" * 50)
    
    # Initialize discovery system
    discovery = get_content_discovery()
    
    # Get content statistics
    stats = discovery.get_content_statistics()
    print("Content Statistics:")
    for content_type, count in stats['total_counts'].items():
        print(f"  {content_type.capitalize()}: {count} items")
    
    # Example content search
    print("\nExample: Searching for 'number' related content:")
    related = discovery.suggest_related_content('number')
    for content_type, items in related.items():
        print(f"  {content_type.capitalize()}: {len(items)} items found")
    
    # Example gap analysis
    print("\nExample: Gap analysis for 'colors' topic:")
    gaps = discovery.analyze_content_gaps('colors', target_jlpt_level=5)
    print(f"  Existing content types: {list(gaps['existing_content'].keys())}")
    print(f"  Recommendations: {len(gaps['recommendations'])}")
    
    print("\nContent Discovery Module initialized successfully!")

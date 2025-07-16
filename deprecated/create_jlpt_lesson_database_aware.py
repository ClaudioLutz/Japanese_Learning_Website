#!/usr/bin/env python3
"""
Database-Aware JLPT Lesson Creation Script

This script demonstrates Phase 2: Database Integration capabilities by creating
a JLPT-focused lesson that leverages existing database content (Kanji, Vocabulary, Grammar).

Features demonstrated:
- Content discovery from existing database
- JLPT-level focused content selection
- Gap analysis and recommendations
- Automatic content referencing
- Smart lesson structure based on available content

Phase 2: Database Integration - Priority 4: Database-Aware Content Scripts
"""

from lesson_creator_base import BaseLessonCreator
from app import create_app

def create_jlpt_lesson(jlpt_level=5, lesson_type="free", language="english"):
    """
    Create a comprehensive JLPT lesson using existing database content.
    
    Args:
        jlpt_level: JLPT level (1-5, where 5 is beginner)
        lesson_type: "free" or "premium"
        language: Instruction language
    """
    
    # Initialize the lesson creator
    creator = BaseLessonCreator(
        title=f"JLPT N{jlpt_level} Comprehensive Study",
        difficulty="beginner" if jlpt_level >= 4 else "intermediate" if jlpt_level >= 2 else "advanced",
        lesson_type=lesson_type,
        language=language,
        category_name=f"JLPT N{jlpt_level}"
    )
    
    print(f"🎯 Creating JLPT N{jlpt_level} lesson with database integration")
    
    # Initialize Flask app context for database operations
    app = creator.app = create_app()
    
    with app.app_context():
        # Initialize content discovery (this will be done automatically, but we can do it early for analysis)
        creator.initialize_content_discovery()
        
        # Analyze what content is available for this JLPT level
        print(f"\n📊 Analyzing available JLPT N{jlpt_level} content...")
        available_content = creator.find_content_by_jlpt_level(jlpt_level)
        
        # Perform gap analysis
        gap_analysis = creator.analyze_content_gaps(f"JLPT N{jlpt_level}", jlpt_level)
    
    # Create lesson structure based on available content
    
    # Page 1: JLPT Overview and Introduction
    creator.add_page(
        title=f"JLPT N{jlpt_level} Introduction",
        description=f"Overview of JLPT N{jlpt_level} requirements and study approach",
        content_list=[
            {
                'type': 'formatted_explanation',
                'topic': f'JLPT N{jlpt_level} Overview and Study Strategy',
                'keywords': [f'JLPT N{jlpt_level}', 'Japanese proficiency test', 'study plan', 'requirements']
            },
            {
                'type': 'explanation',
                'topic': f'What to expect in JLPT N{jlpt_level}',
                'keywords': [f'JLPT N{jlpt_level}', 'test format', 'sections', 'time management']
            }
        ]
    )
    
    # Page 2: Kanji Focus (if kanji content is available)
    if available_content.get('kanji'):
        print(f"📝 Creating Kanji page with {len(available_content['kanji'])} characters")
        
        kanji_content = [
            {
                'type': 'formatted_explanation',
                'topic': f'Essential Kanji for JLPT N{jlpt_level}',
                'keywords': [f'JLPT N{jlpt_level}', 'kanji', 'characters', 'stroke order', 'readings']
            }
        ]
        
        # Add database kanji references (limit to first 10 to avoid overwhelming)
        for kanji in available_content['kanji'][:10]:
            kanji_content.append({
                'type': 'kanji',
                'content_id': kanji.id,
                'title': f"Kanji: {kanji.character} ({kanji.meaning})"
            })
        
        # Add kanji quiz
        kanji_content.append({
            'type': 'multiple_choice',
            'topic': f'JLPT N{jlpt_level} Kanji Recognition Quiz',
            'keywords': [f'JLPT N{jlpt_level}', 'kanji', 'recognition', 'meaning', 'reading']
        })
        
        creator.add_page(
            title=f"JLPT N{jlpt_level} Kanji",
            description=f"Essential kanji characters for JLPT N{jlpt_level}",
            content_list=kanji_content
        )
    
    # Page 3: Vocabulary Focus (if vocabulary content is available)
    if available_content.get('vocabulary'):
        print(f"📚 Creating Vocabulary page with {len(available_content['vocabulary'])} words")
        
        vocab_content = [
            {
                'type': 'formatted_explanation',
                'topic': f'Core Vocabulary for JLPT N{jlpt_level}',
                'keywords': [f'JLPT N{jlpt_level}', 'vocabulary', 'words', 'usage', 'context']
            }
        ]
        
        # Add database vocabulary references (limit to first 15)
        for vocab in available_content['vocabulary'][:15]:
            vocab_content.append({
                'type': 'vocabulary',
                'content_id': vocab.id,
                'title': f"Vocabulary: {vocab.word} ({vocab.meaning})"
            })
        
        # Add vocabulary quiz
        vocab_content.append({
            'type': 'fill_in_the_blank',
            'topic': f'JLPT N{jlpt_level} Vocabulary Usage Quiz',
            'keywords': [f'JLPT N{jlpt_level}', 'vocabulary', 'usage', 'context', 'meaning']
        })
        
        creator.add_page(
            title=f"JLPT N{jlpt_level} Vocabulary",
            description=f"Essential vocabulary for JLPT N{jlpt_level}",
            content_list=vocab_content
        )
    
    # Page 4: Grammar Focus (if grammar content is available)
    if available_content.get('grammar'):
        print(f"📖 Creating Grammar page with {len(available_content['grammar'])} points")
        
        grammar_content = [
            {
                'type': 'formatted_explanation',
                'topic': f'Key Grammar Points for JLPT N{jlpt_level}',
                'keywords': [f'JLPT N{jlpt_level}', 'grammar', 'patterns', 'structures', 'usage']
            }
        ]
        
        # Add database grammar references (limit to first 8)
        for grammar in available_content['grammar'][:8]:
            grammar_content.append({
                'type': 'grammar',
                'content_id': grammar.id,
                'title': f"Grammar: {grammar.title}"
            })
        
        # Add grammar quiz
        grammar_content.append({
            'type': 'multiple_choice',
            'topic': f'JLPT N{jlpt_level} Grammar Application Quiz',
            'keywords': [f'JLPT N{jlpt_level}', 'grammar', 'application', 'sentence structure']
        })
        
        creator.add_page(
            title=f"JLPT N{jlpt_level} Grammar",
            description=f"Essential grammar patterns for JLPT N{jlpt_level}",
            content_list=grammar_content
        )
    
    # Page 5: Integrated Practice and Review
    practice_content = [
        {
            'type': 'formatted_explanation',
            'topic': f'JLPT N{jlpt_level} Integrated Practice Strategy',
            'keywords': [f'JLPT N{jlpt_level}', 'practice', 'review', 'integration', 'test preparation']
        },
        {
            'type': 'multiple_choice',
            'topic': f'JLPT N{jlpt_level} Mixed Review Quiz',
            'keywords': [f'JLPT N{jlpt_level}', 'comprehensive', 'review', 'mixed practice']
        },
        {
            'type': 'true_false',
            'topic': f'JLPT N{jlpt_level} Concept Verification',
            'keywords': [f'JLPT N{jlpt_level}', 'concepts', 'verification', 'understanding']
        }
    ]
    
    creator.add_page(
        title=f"JLPT N{jlpt_level} Practice & Review",
        description=f"Integrated practice and review for JLPT N{jlpt_level}",
        content_list=practice_content
    )
    
    # Page 6: Study Plan and Next Steps (based on gap analysis)
    study_plan_content = [
        {
            'type': 'formatted_explanation',
            'topic': f'Your JLPT N{jlpt_level} Study Plan',
            'keywords': [f'JLPT N{jlpt_level}', 'study plan', 'schedule', 'progression', 'goals']
        }
    ]
    
    # Add recommendations based on gap analysis
    if gap_analysis['recommendations']:
        study_plan_content.append({
            'type': 'explanation',
            'topic': f'Areas for Additional Study - JLPT N{jlpt_level}',
            'keywords': ['study recommendations', 'improvement areas', 'additional practice']
        })
    
    creator.add_page(
        title="Study Plan & Next Steps",
        description="Personalized study recommendations and next steps",
        content_list=study_plan_content
    )
    
    # Create the lesson
    print(f"\n🚀 Creating lesson with {len(creator.pages)} pages...")
    lesson = creator.create_lesson()
    
    # Print summary
    print(f"\n📋 Lesson Creation Summary:")
    print(f"   Title: {creator.title}")
    print(f"   JLPT Level: N{jlpt_level}")
    print(f"   Pages: {len(creator.pages)}")
    print(f"   Database Content Used:")
    print(f"     - Kanji: {len(available_content.get('kanji', []))}")
    print(f"     - Vocabulary: {len(available_content.get('vocabulary', []))}")
    print(f"     - Grammar: {len(available_content.get('grammar', []))}")
    
    if gap_analysis['recommendations']:
        print(f"   📝 Study Recommendations Generated: {len(gap_analysis['recommendations'])}")
    
    return lesson

def create_thematic_lesson(theme="food", include_cultural_context=True):
    """
    Create a thematic lesson using database content discovery.
    
    Args:
        theme: Theme to focus on (e.g., 'food', 'family', 'travel')
        include_cultural_context: Whether to include cultural explanations
    """
    
    creator = BaseLessonCreator(
        title=f"Japanese {theme.title()} Vocabulary & Culture",
        difficulty="beginner",
        lesson_type="free",
        language="english",
        category_name="Thematic Lessons"
    )
    
    print(f"🎨 Creating {theme} themed lesson with database integration")
    
    # Use the new thematic page creation method
    creator.create_thematic_page(theme, include_quiz=True)
    
    # Add cultural context if requested
    if include_cultural_context:
        creator.add_page(
            title=f"{theme.title()} in Japanese Culture",
            description=f"Cultural context and customs related to {theme}",
            content_list=[
                {
                    'type': 'formatted_explanation',
                    'topic': f'{theme} culture and customs in Japan',
                    'keywords': [theme, 'Japanese culture', 'customs', 'traditions', 'etiquette']
                },
                {
                    'type': 'multiple_choice',
                    'topic': f'Japanese {theme} culture quiz',
                    'keywords': [theme, 'culture', 'customs', 'Japan', 'traditions']
                }
            ]
        )
    
    # Create the lesson
    lesson = creator.create_lesson()
    
    print(f"\n📋 Thematic Lesson Created:")
    print(f"   Theme: {theme.title()}")
    print(f"   Pages: {len(creator.pages)}")
    print(f"   Cultural Context: {'Yes' if include_cultural_context else 'No'}")
    
    return lesson

def demonstrate_content_discovery():
    """
    Demonstrate the content discovery capabilities without creating a lesson.
    """
    print("🔍 Content Discovery Demonstration")
    print("=" * 50)
    
    # Create a temporary creator just for discovery
    creator = BaseLessonCreator("Demo", "beginner")
    
    # Initialize Flask app context for database operations
    app = creator.app = create_app()
    
    with app.app_context():
        creator.initialize_content_discovery()
        
        # Test different discovery methods
        topics_to_test = ['food', 'family', 'number', 'color', 'time']
        
        for topic in topics_to_test:
            print(f"\n🔍 Discovering content for '{topic}':")
            content = creator.discover_existing_content(topic)
            
            total_items = sum(len(items) for items in content.values())
            print(f"   Total items found: {total_items}")
            
            if total_items > 0:
                print("   Content breakdown:")
                for content_type, items in content.items():
                    if items:
                        print(f"     - {content_type}: {len(items)} items")
        
        # Test JLPT level discovery
        print(f"\n🎯 JLPT Level Content Summary:")
        for level in range(5, 0, -1):  # N5 to N1
            content = creator.find_content_by_jlpt_level(level)
            total = sum(len(items) for items in content.values())
            print(f"   JLPT N{level}: {total} total items")
        
        # Get overall statistics
        print(f"\n📊 Database Content Statistics:")
        stats = creator.content_discovery.get_content_statistics()
        
        print("   Total Content:")
        for content_type, count in stats['total_counts'].items():
            print(f"     - {content_type.title()}: {count}")
        
        print("   Content Health:")
        health = stats['content_health']
        if 'kana_completeness' in health:
            kana = health['kana_completeness']
            print(f"     - Hiragana: {kana['hiragana']['count']} ({'Complete' if kana['hiragana']['complete'] else 'Incomplete'})")
            print(f"     - Katakana: {kana['katakana']['count']} ({'Complete' if kana['katakana']['complete'] else 'Incomplete'})")

if __name__ == "__main__":
    print("Database-Aware JLPT Lesson Creator")
    print("=" * 50)
    
    # Demonstrate content discovery first
    demonstrate_content_discovery()
    
    print("\n" + "=" * 50)
    print("Creating Sample Lessons...")
    
    try:
        # Create a JLPT N5 lesson (beginner level)
        print("\n1. Creating JLPT N5 Lesson...")
        jlpt_lesson = create_jlpt_lesson(jlpt_level=5)
        
        # Create a food-themed lesson
        print("\n2. Creating Food-Themed Lesson...")
        food_lesson = create_thematic_lesson(theme="food")
        
        print("\n✅ All lessons created successfully!")
        print("\nDatabase-aware lesson creation demonstrates:")
        print("  ✓ Content discovery from existing database")
        print("  ✓ JLPT-level focused content selection")
        print("  ✓ Thematic content organization")
        print("  ✓ Gap analysis and recommendations")
        print("  ✓ Automatic database content referencing")
        print("  ✓ Smart lesson structure adaptation")
        
    except Exception as e:
        print(f"❌ Error creating lessons: {e}")
        print("This might be due to:")
        print("  - Missing database content")
        print("  - Database connection issues")
        print("  - Missing AI API configuration")
        print("\nTry running the content discovery demonstration only.")

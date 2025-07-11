#!/usr/bin/env python3
"""
Database-Aware Kana Lesson Creation Script

This script demonstrates Phase 2: Database Integration capabilities by creating
Kana-focused lessons that leverage existing database content (Hiragana/Katakana).

Features demonstrated:
- Discovery of existing Kana characters in database
- Automatic lesson structure based on available characters
- Progressive difficulty based on character complexity
- Gap detection for missing characters
- Smart grouping of characters by similarity

Phase 2: Database Integration - Priority 4: Database-Aware Content Scripts
"""

from lesson_creator_base import BaseLessonCreator

def create_kana_lesson(kana_type="hiragana", lesson_type="free", language="english", max_characters_per_page=8):
    """
    Create a comprehensive Kana lesson using existing database content.
    
    Args:
        kana_type: "hiragana" or "katakana"
        lesson_type: "free" or "premium"
        language: Instruction language
        max_characters_per_page: Maximum characters to include per page
    """
    
    # Initialize the lesson creator
    creator = BaseLessonCreator(
        title=f"Complete {kana_type.title()} Study Guide",
        difficulty="absolute_beginner",
        lesson_type=lesson_type,
        language=language,
        category_name=f"{kana_type.title()} Characters"
    )
    
    print(f"🔤 Creating {kana_type} lesson with database integration")
    
    # Initialize content discovery
    creator.initialize_content_discovery()
    
    # Find all available kana characters of the specified type
    print(f"\n📊 Discovering available {kana_type} characters...")
    kana_characters = creator.content_discovery.find_kana_by_type(kana_type)
    
    if not kana_characters:
        print(f"❌ No {kana_type} characters found in database!")
        print("Please add some Kana characters to the database first.")
        return None
    
    print(f"✅ Found {len(kana_characters)} {kana_type} characters")
    
    # Group characters by romanization patterns for better learning progression
    character_groups = group_kana_by_pattern(kana_characters)
    
    # Page 1: Introduction to Kana
    creator.add_page(
        title=f"Introduction to {kana_type.title()}",
        description=f"Learn about {kana_type} characters and their importance in Japanese",
        content_list=[
            {
                'type': 'formatted_explanation',
                'topic': f'What is {kana_type}? Understanding Japanese Writing Systems',
                'keywords': [kana_type, 'Japanese writing', 'syllabary', 'pronunciation', 'usage']
            },
            {
                'type': 'explanation',
                'topic': f'How to study {kana_type} effectively',
                'keywords': [kana_type, 'study methods', 'memorization', 'practice', 'tips']
            }
        ]
    )
    
    # Create pages for each character group
    page_count = 2
    for group_name, characters in character_groups.items():
        if not characters:
            continue
            
        # Limit characters per page to avoid overwhelming
        character_chunks = [characters[i:i + max_characters_per_page] 
                          for i in range(0, len(characters), max_characters_per_page)]
        
        for chunk_index, character_chunk in enumerate(character_chunks):
            page_title = f"{kana_type.title()} - {group_name}"
            if len(character_chunks) > 1:
                page_title += f" (Part {chunk_index + 1})"
            
            print(f"📝 Creating page: {page_title} with {len(character_chunk)} characters")
            
            # Build content list for this page
            content_list = [
                {
                    'type': 'formatted_explanation',
                    'topic': f'Learning {group_name} {kana_type} characters',
                    'keywords': [kana_type, group_name, 'pronunciation', 'writing', 'recognition']
                }
            ]
            
            # Add each character from the database
            for kana in character_chunk:
                content_list.append({
                    'type': 'kana',
                    'content_id': kana.id,
                    'title': f"{kana_type.title()}: {kana.character} ({kana.romanization})"
                })
            
            # Add practice quiz for this group
            content_list.append({
                'type': 'multiple_choice',
                'topic': f'{group_name} {kana_type} recognition quiz',
                'keywords': [kana_type, group_name, 'recognition', 'quiz', 'practice']
            })
            
            creator.add_page(
                title=page_title,
                description=f"Learn {group_name} {kana_type} characters with pronunciation and writing practice",
                content_list=content_list
            )
            
            page_count += 1
    
    # Add comprehensive review page
    creator.add_page(
        title=f"{kana_type.title()} Comprehensive Review",
        description=f"Review all {kana_type} characters and test your knowledge",
        content_list=[
            {
                'type': 'formatted_explanation',
                'topic': f'Mastering {kana_type} - Review and Practice Strategy',
                'keywords': [kana_type, 'review', 'mastery', 'practice', 'retention']
            },
            {
                'type': 'multiple_choice',
                'topic': f'Comprehensive {kana_type} recognition test',
                'keywords': [kana_type, 'comprehensive', 'test', 'all characters', 'mastery']
            },
            {
                'type': 'fill_in_the_blank',
                'topic': f'{kana_type} writing practice quiz',
                'keywords': [kana_type, 'writing', 'practice', 'recall', 'production']
            }
        ]
    )
    
    # Add next steps page
    next_kana_type = "katakana" if kana_type == "hiragana" else "hiragana"
    creator.add_page(
        title="Next Steps in Your Japanese Journey",
        description="What to study after mastering these characters",
        content_list=[
            {
                'type': 'formatted_explanation',
                'topic': f'After mastering {kana_type}: Your next steps in Japanese',
                'keywords': [next_kana_type, 'kanji', 'vocabulary', 'grammar', 'progression']
            },
            {
                'type': 'explanation',
                'topic': f'How {kana_type} connects to other Japanese writing systems',
                'keywords': [kana_type, 'kanji', 'mixed writing', 'real Japanese', 'application']
            }
        ]
    )
    
    # Create the lesson
    print(f"\n🚀 Creating lesson with {len(creator.pages)} pages...")
    lesson = creator.create_lesson()
    
    # Print summary
    print(f"\n📋 Lesson Creation Summary:")
    print(f"   Title: {creator.title}")
    print(f"   Kana Type: {kana_type.title()}")
    print(f"   Characters Used: {len(kana_characters)}")
    print(f"   Pages Created: {len(creator.pages)}")
    print(f"   Character Groups: {list(character_groups.keys())}")
    
    # Check for completeness
    expected_count = 46  # Standard hiragana/katakana count
    if len(kana_characters) >= expected_count:
        print(f"   ✅ Complete {kana_type} set available!")
    else:
        missing = expected_count - len(kana_characters)
        print(f"   ⚠️  {missing} characters missing from complete set")
    
    return lesson

def group_kana_by_pattern(kana_characters):
    """
    Group kana characters by romanization patterns for better learning progression.
    
    Args:
        kana_characters: List of Kana objects from database
        
    Returns:
        Dictionary with grouped characters
    """
    groups = {
        'Basic Vowels': [],      # a, i, u, e, o
        'K-sounds': [],          # ka, ki, ku, ke, ko
        'S-sounds': [],          # sa, shi, su, se, so
        'T-sounds': [],          # ta, chi, tsu, te, to
        'N-sounds': [],          # na, ni, nu, ne, no
        'H-sounds': [],          # ha, hi, fu, he, ho
        'M-sounds': [],          # ma, mi, mu, me, mo
        'Y-sounds': [],          # ya, yu, yo
        'R-sounds': [],          # ra, ri, ru, re, ro
        'W-sounds': [],          # wa, wo
        'N-sound': [],           # n
        'Special': []            # any others
    }
    
    for kana in kana_characters:
        rom = kana.romanization.lower()
        
        # Categorize based on romanization
        if rom in ['a', 'i', 'u', 'e', 'o']:
            groups['Basic Vowels'].append(kana)
        elif rom.startswith('k'):
            groups['K-sounds'].append(kana)
        elif rom.startswith('s') or rom in ['shi']:
            groups['S-sounds'].append(kana)
        elif rom.startswith('t') or rom in ['chi', 'tsu']:
            groups['T-sounds'].append(kana)
        elif rom.startswith('n') and rom != 'n':
            groups['N-sounds'].append(kana)
        elif rom.startswith('h') or rom in ['fu']:
            groups['H-sounds'].append(kana)
        elif rom.startswith('m'):
            groups['M-sounds'].append(kana)
        elif rom in ['ya', 'yu', 'yo']:
            groups['Y-sounds'].append(kana)
        elif rom.startswith('r'):
            groups['R-sounds'].append(kana)
        elif rom.startswith('w'):
            groups['W-sounds'].append(kana)
        elif rom == 'n':
            groups['N-sound'].append(kana)
        else:
            groups['Special'].append(kana)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if v}

def create_mixed_kana_lesson(lesson_type="free", language="english"):
    """
    Create a lesson that combines both hiragana and katakana from the database.
    
    Args:
        lesson_type: "free" or "premium"
        language: Instruction language
    """
    
    creator = BaseLessonCreator(
        title="Hiragana & Katakana Comparison Study",
        difficulty="beginner",
        lesson_type=lesson_type,
        language=language,
        category_name="Mixed Kana"
    )
    
    print("🔤 Creating mixed Kana lesson with database integration")
    
    # Initialize content discovery
    creator.initialize_content_discovery()
    
    # Get both types of kana
    hiragana_chars = creator.content_discovery.find_kana_by_type("hiragana")
    katakana_chars = creator.content_discovery.find_kana_by_type("katakana")
    
    print(f"📊 Found {len(hiragana_chars)} hiragana and {len(katakana_chars)} katakana characters")
    
    if not hiragana_chars and not katakana_chars:
        print("❌ No kana characters found in database!")
        return None
    
    # Introduction page
    creator.add_page(
        title="Hiragana vs Katakana: Understanding the Difference",
        description="Learn when and how to use hiragana and katakana",
        content_list=[
            {
                'type': 'formatted_explanation',
                'topic': 'Hiragana vs Katakana: When to use each writing system',
                'keywords': ['hiragana', 'katakana', 'usage', 'differences', 'Japanese writing']
            },
            {
                'type': 'explanation',
                'topic': 'Reading mixed hiragana and katakana text',
                'keywords': ['mixed text', 'reading', 'recognition', 'context', 'practice']
            }
        ]
    )
    
    # Create comparison pages for matching sounds
    if hiragana_chars and katakana_chars:
        # Group by romanization for comparison
        hiragana_by_rom = {h.romanization: h for h in hiragana_chars}
        katakana_by_rom = {k.romanization: k for k in katakana_chars}
        
        # Find common romanizations
        common_sounds = set(hiragana_by_rom.keys()) & set(katakana_by_rom.keys())
        
        if common_sounds:
            # Create comparison pages
            sounds_list = sorted(list(common_sounds))
            page_size = 10
            
            for i in range(0, len(sounds_list), page_size):
                page_sounds = sounds_list[i:i + page_size]
                
                content_list = [
                    {
                        'type': 'formatted_explanation',
                        'topic': f'Comparing hiragana and katakana for sounds: {", ".join(page_sounds[:5])}{"..." if len(page_sounds) > 5 else ""}',
                        'keywords': ['comparison', 'hiragana', 'katakana', 'same sound', 'recognition']
                    }
                ]
                
                # Add character pairs
                for sound in page_sounds:
                    if sound in hiragana_by_rom:
                        content_list.append({
                            'type': 'kana',
                            'content_id': hiragana_by_rom[sound].id,
                            'title': f"Hiragana: {hiragana_by_rom[sound].character} ({sound})"
                        })
                    
                    if sound in katakana_by_rom:
                        content_list.append({
                            'type': 'kana',
                            'content_id': katakana_by_rom[sound].id,
                            'title': f"Katakana: {katakana_by_rom[sound].character} ({sound})"
                        })
                
                # Add comparison quiz
                content_list.append({
                    'type': 'multiple_choice',
                    'topic': f'Hiragana vs Katakana recognition quiz for {", ".join(page_sounds[:3])} sounds',
                    'keywords': ['comparison', 'recognition', 'hiragana', 'katakana', 'quiz']
                })
                
                creator.add_page(
                    title=f"Character Comparison - Set {i//page_size + 1}",
                    description=f"Compare hiragana and katakana for sounds: {', '.join(page_sounds)}",
                    content_list=content_list
                )
    
    # Final practice page
    creator.add_page(
        title="Mixed Kana Practice",
        description="Practice reading mixed hiragana and katakana",
        content_list=[
            {
                'type': 'formatted_explanation',
                'topic': 'Strategies for reading mixed kana text',
                'keywords': ['mixed reading', 'strategies', 'context clues', 'practice']
            },
            {
                'type': 'multiple_choice',
                'topic': 'Mixed hiragana and katakana reading quiz',
                'keywords': ['mixed reading', 'comprehensive', 'hiragana', 'katakana', 'practice']
            }
        ]
    )
    
    # Create the lesson
    lesson = creator.create_lesson()
    
    print(f"\n📋 Mixed Kana Lesson Created:")
    print(f"   Hiragana characters: {len(hiragana_chars)}")
    print(f"   Katakana characters: {len(katakana_chars)}")
    print(f"   Pages: {len(creator.pages)}")
    
    return lesson

def analyze_kana_database_completeness():
    """
    Analyze the completeness of kana characters in the database.
    """
    print("🔍 Kana Database Completeness Analysis")
    print("=" * 50)
    
    # Create temporary creator for analysis
    creator = BaseLessonCreator("Analysis", "beginner")
    creator.initialize_content_discovery()
    
    # Get statistics
    stats = creator.content_discovery.get_content_statistics()
    
    if 'content_health' in stats and 'kana_completeness' in stats['content_health']:
        kana_health = stats['content_health']['kana_completeness']
        
        print("Hiragana Status:")
        hiragana = kana_health['hiragana']
        print(f"  Count: {hiragana['count']}")
        print(f"  Complete: {'✅ Yes' if hiragana['complete'] else '❌ No'}")
        if not hiragana['complete']:
            missing = 46 - hiragana['count']
            print(f"  Missing: {missing} characters")
        
        print("\nKatakana Status:")
        katakana = kana_health['katakana']
        print(f"  Count: {katakana['count']}")
        print(f"  Complete: {'✅ Yes' if katakana['complete'] else '❌ No'}")
        if not katakana['complete']:
            missing = 46 - katakana['count']
            print(f"  Missing: {missing} characters")
        
        # Recommendations
        print("\n💡 Recommendations:")
        if not hiragana['complete']:
            print("  - Add missing hiragana characters to database")
        if not katakana['complete']:
            print("  - Add missing katakana characters to database")
        
        if hiragana['complete'] and katakana['complete']:
            print("  - Database is complete for basic kana!")
            print("  - Consider adding extended kana (dakuten, handakuten, combinations)")
    
    else:
        print("❌ Could not analyze kana completeness")

if __name__ == "__main__":
    print("Database-Aware Kana Lesson Creator")
    print("=" * 50)
    
    # Analyze database first
    analyze_kana_database_completeness()
    
    print("\n" + "=" * 50)
    print("Creating Sample Lessons...")
    
    try:
        # Create hiragana lesson
        print("\n1. Creating Hiragana Lesson...")
        hiragana_lesson = create_kana_lesson(kana_type="hiragana")
        
        # Create katakana lesson
        print("\n2. Creating Katakana Lesson...")
        katakana_lesson = create_kana_lesson(kana_type="katakana")
        
        # Create mixed lesson
        print("\n3. Creating Mixed Kana Lesson...")
        mixed_lesson = create_mixed_kana_lesson()
        
        print("\n✅ All kana lessons created successfully!")
        print("\nDatabase-aware kana lesson creation demonstrates:")
        print("  ✓ Discovery of existing kana characters")
        print("  ✓ Automatic grouping by sound patterns")
        print("  ✓ Progressive difficulty structure")
        print("  ✓ Completeness analysis and gap detection")
        print("  ✓ Smart character comparison and practice")
        
    except Exception as e:
        print(f"❌ Error creating lessons: {e}")
        print("This might be due to:")
        print("  - No kana characters in database")
        print("  - Database connection issues")
        print("  - Missing AI API configuration")
        print("\nTry adding some kana characters to the database first.")

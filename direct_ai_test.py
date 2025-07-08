#!/usr/bin/env python3
"""
Direct test of AI service without web interface
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from ai_services import AILessonContentGenerator

def test_ai_service():
    """Test the AI service directly"""
    print("🤖 Testing AI Lesson Content Generator")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to the .env file:")
        print("OPENAI_API_KEY=sk-your-key-here")
        return
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Initialize the generator
    try:
        generator = AILessonContentGenerator()
        print("✅ AI Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Generator: {e}")
        return
    
    # Test 1: Generate an explanation
    print("\n📝 Test 1: Generate Explanation")
    print("-" * 40)
    
    result = generator.generate_explanation(
        topic="Japanese particles は and を",
        difficulty="JLPT N5", 
        keywords="は, を, subject marker, object marker"
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Explanation generated successfully!")
        print(f"Content: {result['generated_text'][:300]}...")
        print(f"Full length: {len(result['generated_text'])} characters")
    
    # Test 2: Generate a multiple choice question
    print("\n❓ Test 2: Generate Multiple Choice Question")
    print("-" * 40)
    
    result = generator.generate_multiple_choice_question(
        topic="Hiragana reading",
        difficulty="Absolute Beginner",
        keywords="あ, か, さ, た, な"
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Multiple choice question generated successfully!")
        print(f"Question: {result['question_text']}")
        print("\nOptions:")
        for i, option in enumerate(result['options'], 1):
            correct = "✓" if option['is_correct'] else " "
            print(f"  {i}. [{correct}] {option['text']}")
            if option.get('feedback'):
                print(f"      Feedback: {option['feedback']}")
        print(f"\nOverall explanation: {result['overall_explanation']}")
    
    # Test 3: Generate grammar explanation
    print("\n📚 Test 3: Generate Grammar Explanation")
    print("-" * 40)
    
    result = generator.generate_explanation(
        topic="Past tense formation in Japanese",
        difficulty="JLPT N4",
        keywords="た form, past tense, verb conjugation"
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Grammar explanation generated successfully!")
        print(f"Content: {result['generated_text'][:300]}...")
    
    # Test 4: Generate vocabulary quiz
    print("\n📖 Test 4: Generate Vocabulary Quiz")
    print("-" * 40)
    
    result = generator.generate_multiple_choice_question(
        topic="Basic Japanese greetings",
        difficulty="JLPT N5",
        keywords="おはよう, こんにちは, こんばんは, greetings"
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Vocabulary quiz generated successfully!")
        print(f"Question: {result['question_text']}")
        print("\nOptions:")
        for i, option in enumerate(result['options'], 1):
            correct = "✓" if option['is_correct'] else " "
            print(f"  {i}. [{correct}] {option['text']}")

def test_with_flask_context():
    """Test with Flask application context"""
    print("\n🌐 Testing with Flask Context")
    print("=" * 50)
    
    # Import Flask app
    sys.path.insert(0, os.path.dirname(__file__))
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print("✅ Flask context created")
        
        generator = AILessonContentGenerator()
        
        result = generator.generate_explanation(
            topic="Japanese writing systems",
            difficulty="Absolute Beginner",
            keywords="hiragana, katakana, kanji, writing systems"
        )
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Content generated in Flask context!")
            print(f"Content preview: {result['generated_text'][:200]}...")

if __name__ == "__main__":
    # Test the service directly
    test_ai_service()
    
    # Test with Flask context
    try:
        test_with_flask_context()
    except Exception as e:
        print(f"⚠️ Flask context test failed: {e}")
        print("This is normal if Flask dependencies aren't fully set up")

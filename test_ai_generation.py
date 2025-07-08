#!/usr/bin/env python3
"""
Test script to use AI lesson creation directly via API calls
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your server runs on different port
ADMIN_EMAIL = "admin@example.com"   # Replace with your admin email
ADMIN_PASSWORD = "your_password"    # Replace with your admin password

def login_as_admin():
    """Login and get session cookies"""
    session = requests.Session()
    
    # Get login page to get CSRF token
    login_page = session.get(f"{BASE_URL}/login")
    
    # Extract CSRF token (you might need to parse HTML or check cookies)
    # For now, let's try without CSRF for testing
    
    # Login
    login_data = {
        'email': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD,
        'remember': False
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    
    if response.status_code == 200 and "admin" in response.url:
        print("✅ Successfully logged in as admin")
        return session
    else:
        print("❌ Failed to login")
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        return None

def generate_ai_content(session, content_type, topic, difficulty, keywords):
    """Generate AI content using the API"""
    
    # Get CSRF token from a page that has it
    admin_page = session.get(f"{BASE_URL}/admin/manage/lessons")
    
    # Extract CSRF token from the page (simplified - you might need better parsing)
    csrf_token = None
    if 'csrf_token' in admin_page.text:
        # This is a simplified extraction - you might need to parse HTML properly
        import re
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', admin_page.text)
        if match:
            csrf_token = match.group(1)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    
    data = {
        'content_type': content_type,
        'topic': topic,
        'difficulty': difficulty,
        'keywords': keywords
    }
    
    print(f"🤖 Generating {content_type} for topic: {topic}")
    print(f"   Difficulty: {difficulty}")
    print(f"   Keywords: {keywords}")
    
    response = session.post(
        f"{BASE_URL}/api/admin/generate-ai-content",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ AI Generation Successful!")
        return result
    else:
        print(f"❌ AI Generation Failed: {response.status_code}")
        try:
            error = response.json()
            print(f"Error: {error}")
        except:
            print(f"Response: {response.text}")
        return None

def main():
    """Main test function"""
    print("🚀 Testing AI Lesson Creation")
    print("=" * 50)
    
    # Login
    session = login_as_admin()
    if not session:
        return
    
    # Test 1: Generate an explanation
    print("\n📝 Test 1: Generate Explanation")
    print("-" * 30)
    
    explanation = generate_ai_content(
        session=session,
        content_type="explanation",
        topic="Japanese particles は and を",
        difficulty="JLPT N5",
        keywords="は, を, subject, object"
    )
    
    if explanation:
        print(f"Generated text: {explanation.get('generated_text', 'No text')[:200]}...")
    
    # Test 2: Generate a multiple choice question
    print("\n❓ Test 2: Generate Multiple Choice Question")
    print("-" * 30)
    
    question = generate_ai_content(
        session=session,
        content_type="multiple_choice_question",
        topic="Hiragana reading",
        difficulty="Absolute Beginner",
        keywords="あ, か, さ, た"
    )
    
    if question:
        print(f"Question: {question.get('question_text', 'No question')}")
        print("Options:")
        for i, option in enumerate(question.get('options', []), 1):
            correct = "✓" if option.get('is_correct') else " "
            print(f"  {i}. [{correct}] {option.get('text', 'No text')}")
        print(f"Explanation: {question.get('overall_explanation', 'No explanation')}")

if __name__ == "__main__":
    main()

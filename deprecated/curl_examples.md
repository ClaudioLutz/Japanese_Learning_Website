# AI Lesson Creation - Backend Usage Examples

Here are several ways to use the AI lesson creation feature directly from the backend:

## Method 1: Using cURL Commands

First, you need to login and get session cookies, then make API calls.

### Step 1: Login to get session
```bash
# Login and save cookies
curl -c cookies.txt -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@example.com&password=your_password"
```

### Step 2: Get CSRF token
```bash
# Get CSRF token from admin page
curl -b cookies.txt http://localhost:5000/admin/manage/lessons > admin_page.html

# Extract CSRF token (you'll need to parse the HTML)
# Look for: <input name="csrf_token" value="TOKEN_HERE">
```

### Step 3: Generate AI Content

#### Generate an Explanation:
```bash
curl -b cookies.txt -X POST http://localhost:5000/api/admin/generate-ai-content \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN_HERE" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{
    "content_type": "explanation",
    "topic": "Japanese particles は and を",
    "difficulty": "JLPT N5",
    "keywords": "は, を, subject, object"
  }'
```

#### Generate a Multiple Choice Question:
```bash
curl -b cookies.txt -X POST http://localhost:5000/api/admin/generate-ai-content \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN_HERE" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{
    "content_type": "multiple_choice_question",
    "topic": "Hiragana reading",
    "difficulty": "Absolute Beginner",
    "keywords": "あ, か, さ, た"
  }'
```

## Method 2: Using Python Scripts

### Option A: Direct Service Usage (Simplest)

Run the provided script:
```bash
cd Japanese_Learning_Website
python direct_ai_test.py
```

### Option B: API Testing Script

Run the API testing script:
```bash
cd Japanese_Learning_Website
# Edit the script first to add your admin credentials
python test_ai_generation.py
```

## Method 3: Using Postman or Similar Tools

1. **Login Request:**
   - Method: POST
   - URL: `http://localhost:5000/login`
   - Body (form-data):
     - email: admin@example.com
     - password: your_password

2. **Get CSRF Token:**
   - Method: GET
   - URL: `http://localhost:5000/admin/manage/lessons`
   - Extract CSRF token from response HTML

3. **Generate Content:**
   - Method: POST
   - URL: `http://localhost:5000/api/admin/generate-ai-content`
   - Headers:
     - Content-Type: application/json
     - X-CSRFToken: [token from step 2]
     - X-Requested-With: XMLHttpRequest
   - Body (JSON):
     ```json
     {
       "content_type": "explanation",
       "topic": "Japanese particles",
       "difficulty": "JLPT N5",
       "keywords": "は, を, particles"
     }
     ```

## Method 4: Flask Shell (Interactive)

Start the Flask shell and use the service directly:

```bash
cd Japanese_Learning_Website
flask shell
```

Then in the shell:
```python
from app.ai_services import AILessonContentGenerator

# Initialize generator
generator = AILessonContentGenerator()

# Generate explanation
result = generator.generate_explanation(
    topic="Japanese particles は and を",
    difficulty="JLPT N5",
    keywords="は, を, subject, object"
)

print(result)

# Generate multiple choice question
question = generator.generate_multiple_choice_question(
    topic="Hiragana reading",
    difficulty="Absolute Beginner", 
    keywords="あ, か, さ, た"
)

print(question)
```

## Prerequisites

1. **OpenAI API Key**: Make sure you have set your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

2. **Admin Account**: You need admin credentials to access the AI generation endpoints.

3. **Server Running**: Make sure your Flask server is running:
   ```bash
   python run.py
   ```

## Expected Response Formats

### Explanation Response:
```json
{
  "generated_text": "Japanese particles は and を are fundamental elements..."
}
```

### Multiple Choice Question Response:
```json
{
  "question_text": "What is the correct reading of あ?",
  "options": [
    {
      "text": "a",
      "is_correct": true,
      "feedback": "Correct! あ is pronounced 'a'."
    },
    {
      "text": "ka",
      "is_correct": false,
      "feedback": "Incorrect. か is pronounced 'ka', not あ."
    }
  ],
  "overall_explanation": "あ is the first character in the hiragana syllabary..."
}
```

## Error Handling

If you get errors, check:

1. **API Key**: Ensure `OPENAI_API_KEY` is set correctly
2. **Authentication**: Make sure you're logged in as admin
3. **CSRF Token**: Include valid CSRF token in requests
4. **Content Type**: Use `application/json` for API requests
5. **Server Status**: Ensure Flask server is running

## Content Types Supported

- `"explanation"` - Generates educational text content
- `"multiple_choice_question"` - Generates structured quiz questions

## Difficulty Levels

- `"Absolute Beginner"`
- `"JLPT N5"`
- `"JLPT N4"`
- `"Intermediate"`

## Example Topics

- "Japanese particles は and を"
- "Hiragana reading"
- "Basic Japanese greetings"
- "Past tense formation"
- "Katakana characters"
- "Japanese writing systems"

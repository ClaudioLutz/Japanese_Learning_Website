# Japanese Lesson Generation System

This system uses Google Gemini 2.5 Pro to automatically generate comprehensive Japanese lesson creation scripts based on topics from `Japanese lesson generator.md`. Each generated script follows the same high-quality structure as `create_onomatopoeia_lesson.py`.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_gemini.txt
```

### 2. Setup Google Gemini API Key
Add your Google Gemini API key to your `.env` file:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Generate All Lesson Scripts
```bash
python generate_all_lesson_scripts.py
```

### 4. Fix Existing Scripts (if needed)
If you have existing scripts that were generated before the fix:
```bash
python fix_existing_scripts.py
```

### 5. Execute All Generated Scripts
```bash
python run_all_lesson_scripts.py
```

## 📁 System Components

### Core Scripts

1. **`generate_all_lesson_scripts.py`** - Main generator powered by Google Gemini 2.5 Pro
   - Reads topics from `Japanese lesson generator.md`
   - Uses AI to create lesson structures for each topic
   - Generates Python scripts in `lesson_creation_scripts/` folder
   - Each script follows the same structure as `create_onomatopoeia_lesson.py`

2. **`run_all_lesson_scripts.py`** - Batch execution system
   - Discovers and executes all generated lesson scripts
   - Provides progress tracking and error handling
   - Supports selective execution and dry-run mode
   - Generates comprehensive execution logs

3. **`create_onomatopoeia_lesson.py`** - Template script
   - Serves as the blueprint for all generated scripts
   - Contains the complete lesson creation structure
   - Includes AI content generation, image creation, and quiz systems

### Configuration Files

- **`Japanese lesson generator.md`** - Simple topic list (input)
- **`requirements_gemini.txt`** - Python dependencies for Gemini API
- **`lesson_topics_config.json`** - Generated topic configurations (optional)

## 🎯 How It Works

### Step 1: AI-Powered Structure Generation
For each topic in `Japanese lesson generator.md`, Google Gemini 2.5 Pro:
- Analyzes the topic title and description
- Determines appropriate difficulty level (Beginner/Intermediate/Advanced)
- Creates 7 content pages with specific themes
- Generates cultural context and keywords
- Designs image concepts for AI image generation
- Structures educational progression

### Step 2: Script Template System
The system uses `create_onomatopoeia_lesson.py` as a template:
- Replaces topic-specific variables with AI-generated content
- Maintains the same code structure and functionality
- Preserves all database operations and error handling
- Keeps the same lesson creation workflow

### Step 3: Batch Execution
The batch executor runs all generated scripts:
- Sequential execution to avoid database conflicts
- Progress tracking with timestamps
- Error handling and recovery
- Detailed logging and summary reports

## 📊 Generated Lesson Structure

Each generated lesson includes:

### Content Organization
- **Page 1**: Introduction with overview image and welcoming text
- **Pages 2-8**: Content pages (7 themed pages per topic)
- **Pages 3,5,7,9,11,13,15**: Quiz pages (one after each content page)
- **Final Page**: Conclusion and comprehensive quiz

### Content Types
- **AI-Generated Images**: Scene illustrations for each page
- **Comprehensive Explanations**: Detailed educational content
- **Interactive Quizzes**: Multiple choice, true/false, and matching questions
- **Cultural Context**: Authentic Japanese cultural insights
- **Progressive Learning**: Structured difficulty progression

## 🛠️ Usage Examples

### Generate Scripts for All Topics
```bash
python generate_all_lesson_scripts.py
```

### Preview What Would Be Generated (Dry Run)
```bash
python run_all_lesson_scripts.py --dry-run
```

### Execute Specific Topics Only
```bash
python run_all_lesson_scripts.py --topics "internet,anime,business"
```

### Skip Already Created Lessons
```bash
python run_all_lesson_scripts.py --skip-existing
```

### Generate Single Topic (Manual)
1. Edit `Japanese lesson generator.md` to include only desired topic
2. Run `python generate_all_lesson_scripts.py`
3. Execute the generated script manually

## 📋 Topic Coverage

The system generates scripts for all topics in `Japanese lesson generator.md`:

1. Japanese Internet Slang and Social Media Expressions
2. ~~Onomatopoeia and Mimetic Words~~ (already exists)
3. Understanding Japanese Convenience Store Culture
4. Japanese Pop Culture: Anime and Manga Terminology
5. Expressions for Dining Out in Japan
6. Unique Japanese Festivals (Matsuri)
7. Understanding Japanese Business Etiquette
8. Expressions and Etiquette in Japanese Public Transportation
9. Traveling in Japan: Practical Survival Phrases
10. Idiomatic Expressions and Proverbs in Japanese
11. Japanese Fashion and Shopping Culture
12. Nature and Seasons: Appreciating Japan's Seasonal Changes
13. Traditional Japanese Arts and Crafts
14. Japanese Folklore, Legends, and Mythology
15. Daily Routines of a Typical Japanese Person
16. Visiting Japanese Temples and Shrines
17. Japanese Food Culture and Cooking Vocabulary
18. Environmental Issues and Sustainability in Japan
19. Health, Wellness, and Japanese Hot Springs (Onsen)
20. Japanese Youth Culture and Modern Trends

## 🔧 Customization

### Adding New Topics
1. Add topic to `Japanese lesson generator.md` following the existing format:
   ```markdown
   21. **Your New Topic Title**
       * Brief description of what the topic covers.
   ```
2. Run the generator script to create the new lesson script

### Modifying Lesson Structure
- Edit `create_onomatopoeia_lesson.py` to change the template
- The generator will use your modified template for all new scripts
- Existing generated scripts won't be affected

### Adjusting AI Prompts
- Modify the `generate_lesson_structure()` function in `generate_all_lesson_scripts.py`
- Customize the prompt to change how Gemini structures lessons
- Adjust content page count, difficulty assessment, or cultural focus

## 📝 Logging and Monitoring

### Generation Logs
- `lesson_generation_log_YYYYMMDD_HHMMSS.txt` - Detailed generation process
- Shows AI responses, script creation, and any errors

### Execution Logs
- `batch_execution_log_YYYYMMDD_HHMMSS.txt` - Batch execution details
- Includes timing, success/failure status, and error messages

### Summary Reports
Both scripts provide comprehensive summary reports showing:
- Success/failure counts
- Execution times
- Error details
- Next steps

## 🚨 Troubleshooting

### Common Issues

**"GOOGLE_API_KEY not found"**
- Add your Gemini API key to the `.env` file
- Ensure the key has proper permissions

**"Google Generative AI library not installed"**
- Run: `pip install -r requirements_gemini.txt`

**"Could not extract JSON from Gemini response"**
- API rate limiting or temporary service issues
- Wait a few minutes and retry
- Check your API quota

**Script execution timeout**
- Individual scripts have 30-minute timeout
- Check database connectivity and API availability
- Review the specific script's error output

### Performance Tips

- **API Rate Limits**: The generator includes 2-second delays between requests
- **Database Performance**: Scripts run sequentially to avoid conflicts
- **Memory Usage**: Each script runs independently to prevent memory issues

## 🎉 Expected Results

After successful execution, you'll have:
- **19 new lesson creation scripts** in `lesson_creation_scripts/`
- **19 comprehensive Japanese lessons** in your database
- **Each lesson containing 15-17 pages** of content and quizzes
- **AI-generated images** for visual learning
- **Interactive quiz systems** for student engagement
- **Cultural authenticity** and educational progression

The entire system creates a comprehensive Japanese learning curriculum covering diverse topics from internet culture to traditional arts, all powered by AI and following proven educational structures.

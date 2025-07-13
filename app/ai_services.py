# In app/ai_services.py
import os
import json
from openai import OpenAI
from flask import current_app
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.completion_create_params import ResponseFormat
from typing import Literal

class AILessonContentGenerator:
    """
    A service class to handle AI content generation using the OpenAI API.
    """
    def __init__(self):
        try:
            self.api_key = os.environ.get('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            current_app.logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def _generate_content(self, system_prompt, user_prompt, is_json=False):
        """Helper function to call the OpenAI API."""
        if not self.client:
            return None, "OpenAI client is not initialized. Check API key."

        try:
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_format: ResponseFormat = {"type": "json_object"} if is_json else {"type": "text"}
            
            completion = self.client.chat.completions.create(
                model="gpt-4.5-preview", # Or "gpt-3.5-turbo"
                messages=messages,
                response_format=response_format
            )
            
            content = completion.choices[0].message.content
            return content, None
        except Exception as e:
            current_app.logger.error(f"OpenAI API call failed: {e}")
            return None, str(e)

    def generate_explanation(self, topic, difficulty, keywords):
        """Generates a simple text explanation."""
        system_prompt = "You are an expert Japanese language teacher. Your tone is clear, encouraging, and accurate. Generate a concise explanation paragraph."
        user_prompt = f"Lesson Topic: {topic}\nTarget Difficulty: {difficulty}\nKeywords to include: {keywords}\n\nPlease generate the explanation paragraph."
        
        content, error = self._generate_content(system_prompt, user_prompt)
        if error:
            return {"error": error}
        return {"generated_text": content}

    def generate_formatted_explanation(self, topic, difficulty, keywords):
        """Generates a well-formatted explanation using HTML."""
        system_prompt = (
            "You are an expert Japanese language teacher. Your tone is clear, encouraging, and accurate. "
            "Generate a well-structured and formatted explanation using HTML. "
            "Use tags like <h2> for headings, <p> for paragraphs, <strong> for bold text, and <ul>/<li> for lists. "
            "Do not include <html>, <head>, or <body> tags, only the inner content. "
            "IMPORTANT: Always include both Japanese characters AND their romanized pronunciation (romaji) in parentheses. "
            "For example: 'レストラン (resutoran)' or '美味しい (oishii)'. "
            "This helps beginners learn proper pronunciation alongside the written form."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to include: {keywords}

        Please generate a comprehensive, well-formatted explanation using HTML tags.
        
        CRITICAL REQUIREMENTS:
        - Always show Japanese words with their romanized pronunciation in parentheses
        - Example format: レストラン (resutoran) means "restaurant"
        - Include pronunciation for ALL Japanese terms mentioned
        - Make the content beginner-friendly by providing phonetic guidance
        """
        
        content, error = self._generate_content(system_prompt, user_prompt)
        if error:
            return {"error": error}
        return {"generated_text": content}

    def generate_true_false_question(self, topic, difficulty, keywords):
        """Generates a true/false question in a structured JSON format."""
        system_prompt = (
            "You are a Japanese quiz designer. Generate a true/false question. "
            "The question should be a clear statement. Provide a detailed explanation. "
            "Always include romanization for Japanese terms. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to test: {keywords}

        Generate a JSON object with the following structure:
        {{
          "question_text": "The true/false statement...",
          "correct_answer": true,
          "explanation": "A detailed explanation of why the statement is true or false."
        }}
        
        ROMANIZATION REQUIREMENTS:
        - Include romanized pronunciation for ALL Japanese characters
        - Use strategic romanization in questions to avoid giving away answers
        - Always include full romanization in explanations
        - Example: "Sushi (寿司, sushi) is always served with wasabi (わさび, wasabi)"
        """
        
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        
        try:
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_image_prompt(self, content_text, lesson_topic, difficulty):
        """Generate an optimized prompt for AI image generation based on lesson content."""
        system_prompt = (
            "You are an expert at creating image prompts for educational content. "
            "Generate a detailed, specific prompt for AI image generation that will create "
            "educational illustrations for Japanese language learning. Focus on clear, "
            "culturally appropriate, and pedagogically useful imagery."
        )
        user_prompt = f"""
        Lesson Topic: {lesson_topic}
        Difficulty Level: {difficulty}
        Content Text: {content_text}

        Create a detailed image generation prompt that would produce an educational illustration 
        for this Japanese lesson content. The image should be:
        - Culturally accurate and appropriate
        - Clear and educational
        - Suitable for {difficulty} level learners
        - Professional and clean in style
        
        Return only the image prompt, no additional text.
        """
        
        content, error = self._generate_content(system_prompt, user_prompt)
        if error:
            return {"error": error}
        return {"image_prompt": content.strip() if content else None}

    def generate_lesson_images(self, lesson_content_list, lesson_topic, difficulty):
        """Generate multiple images for lesson content using DALL-E."""
        if not self.client:
            return {"error": "OpenAI client is not initialized"}
        
        generated_images = []
        
        for content_item in lesson_content_list:
            try:
                # Generate optimized prompt
                prompt_result = self.generate_image_prompt(
                    content_item.get('text', ''), 
                    lesson_topic, 
                    difficulty
                )
                
                if 'error' in prompt_result:
                    current_app.logger.error(f"Failed to generate image prompt: {prompt_result['error']}")
                    continue
                
                # Generate image using DALL-E
                image_prompt = prompt_result.get('image_prompt')
                if not image_prompt:
                    current_app.logger.error("Generated image prompt is empty.")
                    continue

                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                if response.data:
                    image_url = response.data[0].url
                    generated_images.append({
                        'content_id': content_item.get('id'),
                        'image_url': image_url,
                        'prompt': prompt_result.get('image_prompt'),
                        'content_text': content_item.get('text', '')
                    })
                
            except Exception as e:
                current_app.logger.error(f"Failed to generate image for content: {e}")
                continue
        
        return {"generated_images": generated_images}

    def generate_single_image(self, prompt: str, size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024", quality: Literal["standard", "hd"] = "standard"):
        """Generate a single image using DALL-E."""
        if not self.client:
            return {"error": "OpenAI client is not initialized"}
        
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            if response.data:
                return {
                    "image_url": response.data[0].url,
                    "prompt": prompt,
                    "size": size,
                    "quality": quality
                }
            return {"error": "No image data in response"}
            
        except Exception as e:
            current_app.logger.error(f"Failed to generate image: {e}")
            return {"error": str(e)}

    def analyze_content_for_multimedia_needs(self, content_text, lesson_topic):
        """Analyze lesson content to suggest multimedia enhancements."""
        system_prompt = (
            "You are an educational content analyst. Analyze the provided lesson content "
            "and suggest specific multimedia enhancements that would improve learning. "
            "Format your response as JSON."
        )
        user_prompt = f"""
        Lesson Topic: {lesson_topic}
        Content: {content_text}

        Analyze this content and suggest multimedia enhancements. Return a JSON object with:
        {{
          "image_suggestions": [
            {{"type": "illustration", "description": "What image would help", "priority": "high/medium/low"}},
            {{"type": "diagram", "description": "What diagram would help", "priority": "high/medium/low"}}
          ],
          "audio_suggestions": [
            {{"type": "pronunciation", "description": "What audio would help", "priority": "high/medium/low"}}
          ],
          "video_suggestions": [
            {{"type": "demonstration", "description": "What video would help", "priority": "high/medium/low"}}
          ],
          "interactive_suggestions": [
            {{"type": "quiz", "description": "What interaction would help", "priority": "high/medium/low"}}
          ]
        }}
        """
        
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        
        try:
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_fill_in_the_blank_question(self, topic, difficulty, keywords):
        """Generates a fill-in-the-blank question in a structured JSON format."""
        system_prompt = (
            "You are a Japanese quiz designer. Create a fill-in-the-blank question. "
            "The question text should use '___' to indicate the blank. Provide the correct answer and an explanation. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to test: {keywords}

        Generate a JSON object with the following structure:
        {{
          "question_text": "Sentence with a ___ to fill in.",
          "correct_answer": "The word that fills the blank",
          "explanation": "Explanation of the correct answer and grammar."
        }}
        """
        
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        
        try:
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_matching_question(self, topic, difficulty, keywords):
        """Generates a matching question in a structured JSON format."""
        system_prompt = (
            "You are a Japanese quiz designer. Create a matching question. "
            "Provide pairs of items to match (e.g., Japanese words and their English meanings). "
            "Always include romanization for Japanese terms. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to test: {keywords}

        Generate a JSON object with the following structure:
        {{
          "question_text": "Match the Japanese words to their English meanings.",
          "pairs": [
            {{"prompt": "Japanese Word A (romanization)", "answer": "English Meaning A"}},
            {{"prompt": "Japanese Word B (romanization)", "answer": "English Meaning B"}},
            {{"prompt": "Japanese Word C (romanization)", "answer": "English Meaning C"}},
            {{"prompt": "Japanese Word D (romanization)", "answer": "English Meaning D"}}
          ],
          "explanation": "General explanation for the set of pairs with full romanization."
        }}
        
        CRITICAL REQUIREMENTS:
        - Generate 4-6 pairs for a good matching exercise
        - Include romanized pronunciation for ALL Japanese characters
        - In prompts: Include both Japanese characters and romanization, e.g., "寿司 (sushi)"
        - In answers: Provide clear, concise English meanings
        - In explanations: Include full romanization for all Japanese terms mentioned
        - Ensure all pairs are related to the lesson topic and keywords
        - Make the matching challenging but fair for the difficulty level
        """
        
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        
        try:
            if content:
                result = json.loads(content)
                # Validate the structure
                if 'pairs' not in result or not isinstance(result['pairs'], list):
                    return {"error": "Invalid matching question structure: missing or invalid pairs"}
                
                # Ensure we have at least 3 pairs for a meaningful matching exercise
                if len(result['pairs']) < 3:
                    return {"error": "Insufficient pairs for matching question (minimum 3 required)"}
                
                # Validate each pair has both prompt and answer
                for i, pair in enumerate(result['pairs']):
                    if not isinstance(pair, dict) or 'prompt' not in pair or 'answer' not in pair:
                        return {"error": f"Invalid pair structure at index {i}"}
                
                return result
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_multiple_choice_question(self, topic, difficulty, keywords, question_number=None):
        """Generates a multiple-choice question in a structured JSON format."""
        system_prompt = (
            "You are an expert Japanese quiz designer. Generate a multiple-choice question. "
            "Ensure distractors are plausible but incorrect. Provide brief feedback for each option. "
            "Include a hint and a difficulty level. "
            "CRITICAL: Create UNIQUE and VARIED questions. Avoid repetition. Use different question formats and approaches. "
            "IMPORTANT: Do NOT include the answer or hints about the correct answer in the question text itself. "
            "Keep the question challenging but fair. Save Japanese terms with pronunciations for the answer choices, not the question. "
            "Format the output as a single, valid JSON object."
        )
        
        # Add variety prompts based on question number
        variety_prompts = [
            "Focus on meaning/translation questions (What does X mean?)",
            "Focus on usage/context questions (When would you use X?)",
            "Focus on pronunciation/reading questions (How do you read X?)",
            "Focus on situational questions (What would you say when...?)",
            "Focus on comparison questions (What's the difference between X and Y?)"
        ]
        
        variety_instruction = ""
        if question_number is not None and question_number < len(variety_prompts):
            variety_instruction = f"\nVARIETY INSTRUCTION: {variety_prompts[question_number]}"
        
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to test: {keywords}
        {variety_instruction}

        Generate a JSON object with the following structure:
        {{
          "question_text": "The question...",
          "difficulty_level": {difficulty},
          "hint": "A subtle hint to help the user.",
          "options": [
            {{"text": "Option A...", "is_correct": false, "feedback": "Feedback for A..."}},
            {{"text": "Option B...", "is_correct": true, "feedback": "Feedback for B..."}},
            {{"text": "Option C...", "is_correct": false, "feedback": "Feedback for C..."}},
            {{"text": "Option D...", "is_correct": false, "feedback": "Feedback for D..."}}
          ],
          "overall_explanation": "A general explanation for the correct answer."
        }}
        
        CRITICAL REQUIREMENTS FOR ROMANIZATION:
        - ALWAYS include romanized pronunciation for ALL Japanese characters throughout the quiz
        - In QUESTION TEXT: Use romanization strategically - include it for context words but NOT for the term being tested
        - In ANSWER OPTIONS: Always include full romanization for all Japanese terms
        - In EXPLANATIONS: Always include romanization for all Japanese terms
        
        EXAMPLE APPROACH:
        - Question: "In a typical izakaya (izakaya), which yakitori item would most likely be described as 'momo' on the menu?"
        - Options: "Chicken thigh skewers (もも, momo)", "Chicken breast skewers (むね, mune)", etc.
        
        STRATEGIC ROMANIZATION RULES:
        - Context words in questions: Include romanization (e.g., "izakaya (izakaya)")
        - Terms being tested in questions: Use only romanization without Japanese characters
        - All answer options: Include both Japanese characters and romanization
        - All explanations and feedback: Include full romanization
        
        ADDITIONAL REQUIREMENTS:
        - CREATE UNIQUE QUESTIONS - avoid repetition and use varied question styles
        - Use different approaches: translation, usage, context, pronunciation, etc.
        - Focus on testing understanding rather than recognition
        - Make questions challenging but fair for learners
        """
        
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        
        try:
            # The API should return a string that is a valid JSON object. We parse it here.
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def create_adaptive_quiz(self, topic, difficulty_levels, num_questions_per_level=2):
        """Generates an adaptive quiz with questions at multiple difficulty levels."""
        system_prompt = (
            "You are a Japanese quiz designer. Generate a set of multiple-choice questions "
            "for a specified topic across a range of difficulty levels. "
            "Format the output as a single, valid JSON object containing a list of questions."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Difficulty Levels: {difficulty_levels}
        Number of Questions per Level: {num_questions_per_level}

        Generate a JSON object with a single key "questions" that contains a list of quiz questions.
        For each question, provide the following fields:
        - question_text
        - difficulty_level (from the provided list)
        - hint
        - options (list of dicts with text, is_correct, feedback)
        - overall_explanation
        
        Example for a single question in the list:
        {{
          "question_text": "...",
          "difficulty_level": 1,
          "hint": "...",
          "options": [
            {{"text": "...", "is_correct": false, "feedback": "..."}},
            {{"text": "...", "is_correct": true, "feedback": "..."}}
          ],
          "overall_explanation": "..."
        }}
        """
        
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        
        try:
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_kanji_data(self, kanji_character, jlpt_level):
        """Generates structured data for a single Kanji character."""
        system_prompt = (
            "You are a Japanese language data specialist. Generate detailed information for a single Kanji character. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Kanji Character: {kanji_character}
        JLPT Level: N{jlpt_level}

        Generate a JSON object with the following structure:
        {{
          "character": "{kanji_character}",
          "meaning": "Primary English meaning",
          "onyomi": "Onyomi reading in Katakana",
          "kunyomi": "Kunyomi reading in Hiragana",
          "jlpt_level": {jlpt_level},
          "stroke_count": 10,
          "radical": "Radical character"
        }}
        """
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        try:
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_vocabulary_data(self, word, jlpt_level):
        """Generates structured data for a single vocabulary word."""
        system_prompt = (
            "You are a Japanese language data specialist. Generate detailed information for a single vocabulary word. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Vocabulary Word: {word}
        JLPT Level: N{jlpt_level}

        Generate a JSON object with the following structure:
        {{
          "word": "{word}",
          "reading": "Reading of the word in Hiragana",
          "meaning": "Primary English meaning",
          "jlpt_level": {jlpt_level},
          "example_sentence_japanese": "Example sentence in Japanese using the word.",
          "example_sentence_english": "English translation of the example sentence."
        }}
        """
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        try:
            if content:
                return json.loads(content)
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_grammar_data(self, grammar_point, jlpt_level):
        """Generates structured data for a single grammar point."""
        system_prompt = (
            "You are a Japanese language data specialist. Generate detailed information for a single grammar point. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Grammar Point: {grammar_point}
        JLPT Level: N{jlpt_level}

        Generate a JSON object with the following structure:
        {{
          "title": "{grammar_point}",
          "explanation": "Detailed explanation of the grammar point, its usage, and nuances.",
          "structure": "Common structure, e.g., 'Verb (dictionary form) + ように'",
          "jlpt_level": {jlpt_level},
          "example_sentences": [
            {{"japanese": "Sentence 1 in Japanese.", "english": "Translation 1 in English."}},
            {{"japanese": "Sentence 2 in Japanese.", "english": "Translation 2 in English."}}
          ]
        }}
        """
        content, error = self._generate_content(system_prompt, user_prompt, is_json=True)
        if error:
            return {"error": error}
        try:
            if content:
                data = json.loads(content)
                # The model might return a list of dicts for example_sentences, but the model expects a JSON string.
                if 'example_sentences' in data and isinstance(data['example_sentences'], list):
                    data['example_sentences'] = json.dumps(data['example_sentences'], ensure_ascii=False)
                return data
            else:
                return {"error": "Empty response from AI"}
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

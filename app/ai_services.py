# In app/ai_services.py
import os
import json
from openai import OpenAI
from flask import current_app

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
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_format = {"type": "json_object"} if is_json else {"type": "text"}
            
            completion = self.client.chat.completions.create(
                model="gpt-4.1", # Or "gpt-3.5-turbo"
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
            "Do not include <html>, <head>, or <body> tags, only the inner content."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to include: {keywords}

        Please generate a comprehensive, well-formatted explanation using HTML tags.
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
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to test: {keywords}

        Generate a JSON object with the following structure:
        {{
          "question_text": "The true/false statement...",
          "is_true": true,
          "explanation": "A detailed explanation of why the statement is true or false."
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
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\\nResponse: {content}")
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
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_matching_question(self, topic, difficulty, keywords):
        """Generates a matching question in a structured JSON format."""
        system_prompt = (
            "You are a Japanese quiz designer. Create a matching question. "
            "Provide two lists of items to match (e.g., words and meanings). "
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
            {{"prompt": "Word A", "answer": "Meaning A"}},
            {{"prompt": "Word B", "answer": "Meaning B"}},
            {{"prompt": "Word C", "answer": "Meaning C"}},
            {{"prompt": "Word D", "answer": "Meaning D"}}
          ],
          "explanation": "General explanation for the set of pairs."
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
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

    def generate_multiple_choice_question(self, topic, difficulty, keywords):
        """Generates a multiple-choice question in a structured JSON format."""
        system_prompt = (
            "You are an expert Japanese quiz designer. Generate a multiple-choice question. "
            "Ensure distractors are plausible but incorrect. Provide brief feedback for each option. "
            "Format the output as a single, valid JSON object."
        )
        user_prompt = f"""
        Lesson Topic: {topic}
        Target Difficulty: {difficulty}
        Keywords to test: {keywords}

        Generate a JSON object with the following structure:
        {{
          "question_text": "The question...",
          "options": [
            {{"text": "Option A...", "is_correct": false, "feedback": "Feedback for A..."}},
            {{"text": "Option B...", "is_correct": true, "feedback": "Feedback for B..."}},
            {{"text": "Option C...", "is_correct": false, "feedback": "Feedback for C..."}},
            {{"text": "Option D...", "is_correct": false, "feedback": "Feedback for D..."}}
          ],
          "overall_explanation": "A general explanation for the correct answer."
        }}
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
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\\nResponse: {content}")
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
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\\nResponse: {content}")
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
            current_app.logger.error(f"Failed to parse JSON from AI response: {e}\\nResponse: {content}")
            return {"error": "Failed to parse AI response as JSON."}

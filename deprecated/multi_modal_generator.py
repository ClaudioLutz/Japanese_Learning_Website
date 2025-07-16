from app.ai_services import AILessonContentGenerator

class MultiModalGenerator:
    """
    A class to generate multi-modal content for lessons.
    """
    def __init__(self):
        self.ai_generator = AILessonContentGenerator()

    def create_visual_content(self, topic):
        """
        Generates visual learning materials for a given topic.
        """
        prompt = f"Create a simple and clear illustration about '{topic}' for a Japanese language lesson."
        result = self.ai_generator.generate_single_image(prompt)
        return result

    def create_auditory_content(self, topic):
        """
        Generates audio learning materials for a given topic.
        """
        # This is a placeholder for now, as we don't have a text-to-speech service integrated.
        # In a real implementation, this would call a TTS service to generate an audio file.
        return {"audio_url": f"/static/audio/{topic.replace(' ', '_').lower()}.mp3"}

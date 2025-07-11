import json
from lesson_creator_base import LessonCreatorBase

class LessonTemplate:
    """
    A class to handle lesson creation from templates.
    """
    def __init__(self, template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = json.load(f)

    def create_lesson_from_template(self, **kwargs):
        """
        Creates a lesson from the loaded template, substituting placeholders.
        """
        # Substitute placeholders in lesson properties
        title = self.template['lesson']['title'].format(**kwargs)
        description = self.template['lesson']['description'].format(**kwargs)
        lesson_type = self.template['lesson']['lesson_type']
        difficulty_level = self.template['lesson']['difficulty_level']
        category_id = self.template['lesson']['category_id']

        # Create a lesson creator instance
        lesson_creator = LessonCreatorBase(
            title=title,
            description=description,
            lesson_type=lesson_type,
            difficulty_level=difficulty_level,
            category_id=category_id
        )

        # Add pages and content from the template
        for page_template in self.template['pages']:
            page_title = page_template['title'].format(**kwargs)
            content_list = []
            for content_item in page_template['content']:
                # Substitute placeholders in content
                if 'text' in content_item and isinstance(content_item['text'], str):
                    content_item['text'] = content_item['text'].format(**kwargs)
                content_list.append(content_item)
            
            lesson_creator.add_page(page_title, content_list)

        # Create the lesson in the database
        return lesson_creator.create_lesson()

import os
import sys
from datetime import datetime

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import db
from app.models import Lesson, LessonContent, LessonPage

class LessonCreatorBase:
    """
    A base class for creating lessons.
    """
    def __init__(self, title, description, lesson_type, difficulty_level, category_id):
        self.lesson = Lesson(
            title=title,
            description=description,
            lesson_type=lesson_type,
            difficulty_level=difficulty_level,
            category_id=category_id,
            is_published=True,
            instruction_language='english'
        )
        self.pages = []

    def add_page(self, title, content_list):
        """
        Adds a page with its content to the lesson structure.
        """
        page_number = len(self.pages) + 1
        page_meta = {
            'title': title,
            'page_number': page_number
        }
        
        content_for_page = []
        for i, content_item in enumerate(content_list):
            content_for_page.append({
                'order_index': i + 1,
                'page_number': page_number,
                **content_item
            })
        
        self.pages.append({'meta': page_meta, 'content': content_for_page})

    def create_lesson(self):
        """
        Creates the lesson and all its content in the database.
        """
        # First, create the lesson to get an ID
        db.session.add(self.lesson)
        db.session.commit()

        # Then, create pages and content
        for page_data in self.pages:
            meta = page_data['meta']
            lesson_page = LessonPage(
                lesson_id=self.lesson.id,
                page_number=meta['page_number'],
                title=meta['title']
            )
            db.session.add(lesson_page)
            db.session.commit()

            for content_data in page_data['content']:
                content = LessonContent(
                    lesson_id=self.lesson.id,
                    content_type=content_data['type'],
                    content_text=content_data.get('text'),
                    order_index=content_data['order_index'],
                    page_number=content_data['page_number']
                )
                db.session.add(content)
        
        db.session.commit()
        return self.lesson

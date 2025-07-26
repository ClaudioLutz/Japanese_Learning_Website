import sys
import os
from app import create_app, db
from app.models import Lesson, LessonCategory

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = create_app()

def assign_categories():
    """Assigns categories to existing lessons based on keywords in their titles."""
    
    category_map = {
        'Culture & Traditions': ['folklore', 'traditional arts', 'matsuri', 'festive traditions', 'temples and shrines', 'shiki no irodori', 'seasons', 'craftsmanship'],
        'Food & Dining': ['food culture', 'cooking vocabulary', 'cuisine', 'dining out', 'ramen', 'restaurants', 'konbini', 'convenience store'],
        'Daily Life & Society': ['daily routines', 'cities', 'workplace', 'business etiquette', 'public transport', 'environmental issues'],
        'Pop Culture & Modern Japan': ['youth culture', 'pop culture', 'anime & manga', 'internet slang', 'social media', 'fashion', 'shopping'],
        'Language & Communication': ['idioms and proverbs', 'survival phrases', 'communication'],
        'Travel & Geography': ['travel', 'cities', 'geography', 'onsen culture', 'festivals'],
        'Language Fundamentals': ['hiragana', 'katakana', 'kanji', 'vocabulary', 'grammar', 'numbers']
    }

    with app.app_context():
        lessons = Lesson.query.all()
        categories = LessonCategory.query.all()
        
        category_name_to_id = {c.name: c.id for c in categories}
        
        for lesson in lessons:
            if lesson.category_id:
                print(f"Lesson '{lesson.title}' already has a category.")
                continue

            assigned = False
            for category_name, keywords in category_map.items():
                for keyword in keywords:
                    if keyword in lesson.title.lower():
                        lesson.category_id = category_name_to_id.get(category_name)
                        print(f"Assigned '{lesson.title}' to category '{category_name}'")
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                print(f"Could not assign a category to lesson: '{lesson.title}'")

        db.session.commit()
        print("Finished assigning categories.")

if __name__ == '__main__':
    assign_categories()

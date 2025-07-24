import sys
import os
from app import create_app, db
from app.models import LessonCategory

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = create_app()

def populate_categories():
    """Populates the database with predefined lesson categories."""
    
    categories = [
        {'name': 'Culture & Traditions', 'description': 'Explore the rich tapestry of Japanese culture, from ancient customs to modern-day practices.', 'color_code': '#D9534F'},
        {'name': 'Food & Dining', 'description': 'Delve into the world of Japanese cuisine, from street food to fine dining.', 'color_code': '#F0AD4E'},
        {'name': 'Daily Life & Society', 'description': 'Learn about everyday life in Japan, including social norms, work culture, and urban living.', 'color_code': '#5BC0DE'},
        {'name': 'Pop Culture & Modern Japan', 'description': 'Discover the vibrant world of Japanese pop culture, including anime, manga, and technology.', 'color_code': '#5CB85C'},
        {'name': 'Language & Communication', 'description': 'Master the nuances of the Japanese language, from essential phrases to complex grammar.', 'color_code': '#428BCA'},
        {'name': 'Travel & Geography', 'description': 'Get ready for your trip to Japan with essential travel tips and geographical knowledge.', 'color_code': '#7E57C2'},
        {'name': 'Language Fundamentals', 'description': 'Build a strong foundation in Japanese with lessons on grammar, vocabulary, and writing systems.', 'color_code': '#66BB6A'}
    ]
    
    with app.app_context():
        for category_data in categories:
            category = LessonCategory.query.filter_by(name=category_data['name']).first()
            if not category:
                new_category = LessonCategory(
                    name=category_data['name'],
                    description=category_data['description'],
                    color_code=category_data['color_code']
                )
                db.session.add(new_category)
                print(f"Added category: {category_data['name']}")
            else:
                print(f"Category already exists: {category_data['name']}")
        
        db.session.commit()
        print("Categories populated successfully.")

if __name__ == '__main__':
    populate_categories()

import sys
import os
import psycopg
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Google Cloud PostgreSQL configuration
CLOUD_DB_CONFIG = {
    'host': '127.0.0.1',  # Your Google Cloud SQL public IP
    'dbname': 'japanese_learning',
    'user': 'app_user',
    'password': 'Dg34.67MDt',
    'port': 5432
}

def populate_cloud_categories():
    """Populates the Google Cloud database with predefined lesson categories."""
    
    categories = [
        {'name': 'Culture & Traditions', 'description': 'Explore the rich tapestry of Japanese culture, from ancient customs to modern-day practices.', 'color_code': '#D9534F'},
        {'name': 'Food & Dining', 'description': 'Delve into the world of Japanese cuisine, from street food to fine dining.', 'color_code': '#F0AD4E'},
        {'name': 'Daily Life & Society', 'description': 'Learn about everyday life in Japan, including social norms, work culture, and urban living.', 'color_code': '#5BC0DE'},
        {'name': 'Pop Culture & Modern Japan', 'description': 'Discover the vibrant world of Japanese pop culture, including anime, manga, and technology.', 'color_code': '#5CB85C'},
        {'name': 'Language & Communication', 'description': 'Master the nuances of the Japanese language, from essential phrases to complex grammar.', 'color_code': '#428BCA'},
        {'name': 'Travel & Geography', 'description': 'Get ready for your trip to Japan with essential travel tips and geographical knowledge.', 'color_code': '#7E57C2'},
        {'name': 'Language Fundamentals', 'description': 'Build a strong foundation in Japanese with lessons on grammar, vocabulary, and writing systems.', 'color_code': '#66BB6A'}
    ]
    
    try:
        # Connect to Google Cloud PostgreSQL
        print(f"Connecting to Google Cloud PostgreSQL at {CLOUD_DB_CONFIG['host']}...")
        connection = psycopg.connect(**CLOUD_DB_CONFIG)
        cursor = connection.cursor()
        print("✓ Connected successfully!")
        
        # Check if lesson_category table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'lesson_category'
            );
        """)
        result = cursor.fetchone()
        table_exists = result[0] if result else False
        
        if not table_exists:
            print("❌ lesson_category table does not exist. Please run create_cloud_database.py first.")
            return False
        
        # Insert categories
        for category_data in categories:
            # Check if category already exists
            cursor.execute(
                "SELECT id FROM lesson_category WHERE name = %s",
                (category_data['name'],)
            )
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO lesson_category (name, description, color_code, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    category_data['name'],
                    category_data['description'],
                    category_data['color_code'],
                    datetime.now()
                ))
                print(f"✓ Added category: {category_data['name']}")
            else:
                print(f"⚠️  Category already exists: {category_data['name']}")
        
        # Commit changes
        connection.commit()
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM lesson_category")
        result = cursor.fetchone()
        count = result[0] if result else 0
        print(f"\n🎉 Categories populated successfully! Total categories: {count}")
        
        # Show all categories
        cursor.execute("SELECT name, description, color_code FROM lesson_category ORDER BY name")
        categories_in_db = cursor.fetchall()
        
        print("\nCategories in Google Cloud database:")
        for name, description, color_code in categories_in_db:
            print(f"  • {name} ({color_code})")
            print(f"    {description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == '__main__':
    print("🚀 Populating Google Cloud PostgreSQL with Lesson Categories")
    print("=" * 60)
    
    success = populate_cloud_categories()
    
    if success:
        print("\n✅ Cloud database population completed successfully!")
    else:
        print("\n❌ Cloud database population failed.")
        sys.exit(1)

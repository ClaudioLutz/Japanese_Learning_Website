#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import Lesson, LessonCategory

def create_german_categories():
    """Create German lesson categories"""
    
    categories_data = [
        {
            'name': 'Sprachgrundlagen',
            'description': 'Grundlagen der japanischen Sprache: Grammatik, Zählwörter, Höflichkeitsformen und Dialekte',
            'color_code': '#4CAF50'
        },
        {
            'name': 'Kultur & Traditionen',
            'description': 'Japanische Kultur, Feste, Traditionen, Religion, Kunst und Handwerk',
            'color_code': '#FF9800'
        },
        {
            'name': 'Essen & Kulinarik',
            'description': 'Japanische Küche, Restaurant-Etikette und kulinarische Sprache',
            'color_code': '#F44336'
        },
        {
            'name': 'Alltag & Gesellschaft',
            'description': 'Tägliches Leben in Japan: Familie, Wohnen, Schulsystem, Gesundheit und Bankwesen',
            'color_code': '#2196F3'
        },
        {
            'name': 'Popkultur & Moderne',
            'description': 'Moderne japanische Kultur: Popkultur, Musik, Mode, Technologie und Social Media',
            'color_code': '#9C27B0'
        },
        {
            'name': 'Reisen & Verkehr',
            'description': 'Reisen in Japan: Transport, Tourismus, Natur und Notfälle',
            'color_code': '#00BCD4'
        },
        {
            'name': 'Beruf & Geschäft',
            'description': 'Geschäftsjapanisch, Karriere, Politik und professionelle Kommunikation',
            'color_code': '#607D8B'
        },
        {
            'name': 'Persönliches & Soziales',
            'description': 'Persönliche Themen: Beziehungen, Hobbys, Zukunftspläne und soziale Interaktion',
            'color_code': '#E91E63'
        },
        {
            'name': 'Geschichte & Umwelt',
            'description': 'Japanische Geschichte, Umweltthemen, Nachhaltigkeit und kulturelles Erbe',
            'color_code': '#795548'
        },
        {
            'name': 'Mythen & Literatur',
            'description': 'Japanische Literatur, Mythen, Legenden, Sprichwörter und Weisheiten',
            'color_code': '#3F51B5'
        }
    ]
    
    created_categories = {}
    
    for cat_data in categories_data:
        # Check if category already exists
        existing_cat = LessonCategory.query.filter_by(name=cat_data['name']).first()
        if existing_cat:
            print(f"Category '{cat_data['name']}' already exists with ID {existing_cat.id}")
            created_categories[cat_data['name']] = existing_cat
        else:
            category = LessonCategory(
                name=cat_data['name'],
                description=cat_data['description'],
                color_code=cat_data['color_code']
            )
            db.session.add(category)
            db.session.flush()  # Get the ID
            created_categories[cat_data['name']] = category
            print(f"Created category '{cat_data['name']}' with ID {category.id}")
    
    db.session.commit()
    return created_categories

def categorize_lessons(categories):
    """Categorize all German lessons"""
    
    # Mapping of lesson titles to categories
    lesson_categorization = {
        # Sprachgrundlagen
        'Die Kunst der japanischen Zählwörter (Josuushi)': 'Sprachgrundlagen',
        'Die Kunst der japanischen Zählwörter (Josuushi - 助数詞)': 'Sprachgrundlagen',
        'Eine Reise durch Japans Dialekte: Von Kansai-ben bis Tohoku-ben': 'Sprachgrundlagen',
        'Meister der japanischen Begrüßung und Vorstellung: Von Ohayō bis Yoroshiku Onegaishimasu': 'Sprachgrundlagen',
        'Fortgeschrittene Japanische Grammatik: Kausativ, Passiv und Konditionalformen meistern': 'Sprachgrundlagen',
        'Japanisch für Debatten und Diskussionen: Meinungen souverän vertreten': 'Sprachgrundlagen',
        'Meister der Höflichkeit: Eine umfassende Anleitung zum japanischen Keigo': 'Sprachgrundlagen',
        'Japanischer Slang und Umgangssprache: Sprich wie die Locals!': 'Sprachgrundlagen',
        'Verabschiedungen auf Japanisch: Von \'Sayonara\' bis \'Mata ne\'': 'Sprachgrundlagen',
        
        # Kultur & Traditionen
        'Feste und Traditionen in Japan: Eine Reise durch die Jahreszeiten': 'Kultur & Traditionen',
        'Japanische Kunst, Kalligrafie und traditionelles Handwerk': 'Kultur & Traditionen',
        'Religion und Spiritualität in Japan: Eine Reise zu Tempeln und Schreinen': 'Kultur & Traditionen',
        'Wetter und Jahreszeiten auf Japanisch: Von Kirschblüten bis zu Schneeflocken': 'Kultur & Traditionen',
        'Zeitreise durch Japan: Ausdrücke für Geschichte und Kulturerbe': 'Kultur & Traditionen',
        
        # Essen & Kulinarik
        'Japanische Esskultur & Restaurant-Etikette': 'Essen & Kulinarik',
        'Kochen auf Japanisch: Ein kulinarischer Sprachführer': 'Essen & Kulinarik',
        
        # Alltag & Gesellschaft
        'Die japanische Familie: Struktur, Anrede und Beziehungen verstehen': 'Alltag & Gesellschaft',
        'Gesundheitssystem in Japan: Ein Leitfaden für Notfälle und Arztbesuche': 'Alltag & Gesellschaft',
        'Geld und Bankgeschäfte in Japan meistern': 'Alltag & Gesellschaft',
        'Wegweiser durch das japanische Schulsystem': 'Alltag & Gesellschaft',
        'Wohnen in Japan: Deine erste Wohnung mieten': 'Alltag & Gesellschaft',
        'Einkaufen in Japan: Vokabeln, Phrasen & Etikette': 'Alltag & Gesellschaft',
        
        # Popkultur & Moderne
        'Die Japanische Modewelt: Kleidung, Stile und Shopping': 'Popkultur & Moderne',
        'Japanische Popkultur & Unterhaltung: Sprich wie ein Fan': 'Popkultur & Moderne',
        'Musikland Japan: Von traditionellen Klängen bis J-Pop': 'Popkultur & Moderne',
        'Tech-Talk auf Japanisch: Dein Guide für Computer, Smartphones und Social Media': 'Popkultur & Moderne',
        'Sport in Japan: Von Baseball bis Sumo – Ein Leitfaden für Fans': 'Popkultur & Moderne',
        
        # Reisen & Verkehr
        'Japan Reisen: Der ultimative Sprachführer für Touristen': 'Reisen & Verkehr',
        'Abenteuer in Japans Natur: Wandern, Campen & mehr': 'Reisen & Verkehr',
        'Unterwegs in Japan: Ein Guide für Züge, Busse und Taxis': 'Reisen & Verkehr',
        'Notfall-Japanisch: Sicher und vorbereitet in jeder Situation': 'Reisen & Verkehr',
        
        # Beruf & Geschäft
        'Japanische Politik verstehen: Vokabular und Strukturen': 'Beruf & Geschäft',
        'Geschäftsjapanisch: Etikette und professionelle Sprache': 'Beruf & Geschäft',
        'Karriere in Japan: Von der Bewerbung zum Berufsalltag': 'Beruf & Geschäft',
        
        # Persönliches & Soziales
        'Liebe, Romantik und Beziehungen auf Japanisch: Ein Leitfaden für Herzensangelegenheiten': 'Persönliches & Soziales',
        'Über Hobbys und Freizeit sprechen: Deine Interessen auf Japanisch teilen': 'Persönliches & Soziales',
        'Zukunftsplanung: Ziele und Träume auf Japanisch': 'Persönliches & Soziales',
        
        # Geschichte & Umwelt
        'Umweltthemen und Nachhaltigkeit in Japan': 'Geschichte & Umwelt',
        
        # Mythen & Literatur
        'Eine Reise durch die japanische Literatur: Von Klassikern zu modernen Meistern': 'Mythen & Literatur',
        'Japanische Weisheiten: Eine Reise durch Sprichwörter (Kotowaza) und Redewendungen (Kanyouku)': 'Mythen & Literatur',
        'Japans Fabelwesen: Eine Reise durch Mythen und Legenden': 'Mythen & Literatur',
    }
    
    # Get all German lessons
    lessons = Lesson.query.filter(Lesson.instruction_language == 'german').all()
    
    updated_count = 0
    uncategorized_lessons = []
    
    for lesson in lessons:
        if lesson.title in lesson_categorization:
            category_name = lesson_categorization[lesson.title]
            if category_name in categories:
                lesson.category_id = categories[category_name].id
                print(f"Categorized '{lesson.title}' -> '{category_name}'")
                updated_count += 1
            else:
                print(f"ERROR: Category '{category_name}' not found for lesson '{lesson.title}'")
        else:
            uncategorized_lessons.append(lesson.title)
            print(f"WARNING: No category mapping found for lesson '{lesson.title}'")
    
    db.session.commit()
    
    print(f"\n=== SUMMARY ===")
    print(f"Updated {updated_count} lessons")
    if uncategorized_lessons:
        print(f"Uncategorized lessons ({len(uncategorized_lessons)}):")
        for title in uncategorized_lessons:
            print(f"  - {title}")
    
    return updated_count, uncategorized_lessons

def main():
    app = create_app()
    with app.app_context():
        print("Creating German lesson categories...")
        categories = create_german_categories()
        
        print("\nCategorizing German lessons...")
        updated_count, uncategorized = categorize_lessons(categories)
        
        print(f"\nProcess completed! Updated {updated_count} lessons.")
        
        # Show final category distribution
        print("\n=== FINAL CATEGORY DISTRIBUTION ===")
        for cat_name, cat_obj in categories.items():
            lesson_count = Lesson.query.filter_by(category_id=cat_obj.id, instruction_language='german').count()
            print(f"{cat_name}: {lesson_count} lessons")

if __name__ == '__main__':
    main()

"""Idempotentes Seeding der Forum-Kategorien.

Legt die vier Standard-Kategorien an bzw. aktualisiert sie (Upsert per slug):
- Ankuendigungen  (nur Team/Admin darf Themen erstellen)
- Vorschlaege
- Hilfe & Fragen
- Off-Topic

Mehrfach ausfuehrbar, ohne Duplikate. Nutzer-Topics/-Posts bleiben unangetastet.

Verwendung (lokal/Dev):
    python scripts/seed_forum_categories.py

Auf dem Prod-Server (hp-ubuntu), DB-Host ist im Container 'db' → vom Host aus
explizit auf localhost umbiegen:
    DATABASE_URL='postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning' \
        python scripts/seed_forum_categories.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from app.models import ForumCategory  # noqa: E402


CATEGORIES = [
    {
        'slug': 'ankuendigungen',
        'name': 'Ankündigungen',
        'description': 'Neuigkeiten und Updates vom Team.',
        'icon': 'fa-bullhorn',
        'display_order': 1,
        'admin_only_post': True,
    },
    {
        'slug': 'vorschlaege',
        'name': 'Vorschläge',
        'description': 'Wünsche und Ideen für die Plattform.',
        'icon': 'fa-lightbulb',
        'display_order': 2,
        'admin_only_post': False,
    },
    {
        'slug': 'hilfe-fragen',
        'name': 'Hilfe & Fragen',
        'description': 'Fragen zum Japanischlernen und zur Seite.',
        'icon': 'fa-circle-question',
        'display_order': 3,
        'admin_only_post': False,
    },
    {
        'slug': 'off-topic',
        'name': 'Off-Topic',
        'description': 'Alles andere rund um Japan und Sprache.',
        'icon': 'fa-mug-hot',
        'display_order': 4,
        'admin_only_post': False,
    },
]


def seed():
    created, updated = 0, 0
    for spec in CATEGORIES:
        cat = ForumCategory.query.filter_by(slug=spec['slug']).first()
        if cat is None:
            cat = ForumCategory(**spec, is_active=True)
            db.session.add(cat)
            created += 1
            print(f"  + angelegt: {spec['name']} ({spec['slug']})")
        else:
            cat.name = spec['name']
            cat.description = spec['description']
            cat.icon = spec['icon']
            cat.display_order = spec['display_order']
            cat.admin_only_post = spec['admin_only_post']
            cat.is_active = True
            updated += 1
            print(f"  ~ aktualisiert: {spec['name']} ({spec['slug']})")
    db.session.commit()
    print(f"Fertig: {created} angelegt, {updated} aktualisiert.")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed()

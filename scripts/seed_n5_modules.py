"""Seed-Script fuer 8 N5-Lernpfad-Module (Mayuko-Direktive 2026-04-25).

Idempotent: bestehende Module per slug erkannt, Updates statt Duplikate.
Reihenfolge baut auf-aufeinander (prerequisite_category_id), aber Reihenfolge
ist hauptsaechlich didaktisch und nicht hart erzwingen.

Run: venv/Scripts/python scripts/seed_n5_modules.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db  # noqa: E402
from app.models import LessonCategory  # noqa: E402


# Vorgeschlagene 8 Module — basierend auf JLPT-N5 Themenstruktur und Tanos-Reihenfolge.
N5_MODULES = [
    {
        "slug": "n5-hiragana",
        "name": "N5 · Hiragana komplett",
        "description": "Alle 46 Grund-Hiragana plus Dakuten/Handakuten/Yōon. Pflicht vor allem anderen.",
        "color_code": "#fbbf24",  # amber-400
        "icon_emoji": "あ",
        "display_order": 1,
        "prerequisite_slug": None,
    },
    {
        "slug": "n5-katakana",
        "name": "N5 · Katakana komplett",
        "description": "Alle 46 Grund-Katakana plus Dakuten/Handakuten/Yōon und gängige Lehnwörter.",
        "color_code": "#f97316",  # orange-500
        "icon_emoji": "カ",
        "display_order": 2,
        "prerequisite_slug": "n5-hiragana",
    },
    {
        "slug": "n5-zahlen-zeit",
        "name": "N5 · Zahlen, Zeit und Datum",
        "description": "Zahlen 0–10000, Uhrzeit, Wochentage, Monate, Datum, Alter, Telefonnummern.",
        "color_code": "#22c55e",  # green-500
        "icon_emoji": "🔢",
        "display_order": 3,
        "prerequisite_slug": "n5-hiragana",
    },
    {
        "slug": "n5-begruessung-hoeflichkeit",
        "name": "N5 · Begrüssung & Höflichkeit",
        "description": "Tagesgrüsse, Vorstellung, Verabschiedung, Standardphrasen für höflichen Umgang.",
        "color_code": "#06b6d4",  # cyan-500
        "icon_emoji": "🙇",
        "display_order": 4,
        "prerequisite_slug": "n5-hiragana",
    },
    {
        "slug": "n5-familie-personen",
        "name": "N5 · Familie & Personen",
        "description": "Familienmitglieder (eigene + andere), Berufe, Beschreibung von Personen.",
        "color_code": "#a855f7",  # purple-500
        "icon_emoji": "👪",
        "display_order": 5,
        "prerequisite_slug": "n5-begruessung-hoeflichkeit",
    },
    {
        "slug": "n5-alltag-essen",
        "name": "N5 · Alltag & Essen",
        "description": "Mahlzeiten, Lebensmittel, Restaurant, Alltagsgegenstände, einfache Aktivitäten.",
        "color_code": "#ec4899",  # pink-500
        "icon_emoji": "🍙",
        "display_order": 6,
        "prerequisite_slug": "n5-familie-personen",
    },
    {
        "slug": "n5-reise-ort",
        "name": "N5 · Reise & Ort",
        "description": "Verkehrsmittel, Wegbeschreibung, Orte (Bahnhof, Schule, Geschäft), Richtungsangaben.",
        "color_code": "#3b82f6",  # blue-500
        "icon_emoji": "🚉",
        "display_order": 7,
        "prerequisite_slug": "n5-alltag-essen",
    },
    {
        "slug": "n5-erste-saetze",
        "name": "N5 · Erste Sätze (Grammatik)",
        "description": "Grundgrammatik: です/ます, は/が/を/に/で-Partikel, ある/いる, einfache Verben in Präsens/Vergangenheit.",
        "color_code": "#ef4444",  # red-500
        "icon_emoji": "📝",
        "display_order": 8,
        "prerequisite_slug": "n5-begruessung-hoeflichkeit",
    },
]


def seed():
    app = create_app()
    with app.app_context():
        slug_to_id: dict[str, int] = {}

        # Pass 1: Module ohne prereq anlegen/aktualisieren
        for spec in N5_MODULES:
            cat = (
                db.session.query(LessonCategory)
                .filter_by(slug=spec["slug"])
                .first()
            )
            if cat is None:
                cat = LessonCategory(
                    slug=spec["slug"],
                    name=spec["name"],
                    description=spec["description"],
                    color_code=spec["color_code"],
                    icon_emoji=spec["icon_emoji"],
                    jlpt_level=5,
                    display_order=spec["display_order"],
                )
                db.session.add(cat)
                action = "ANGELEGT"
            else:
                cat.name = spec["name"]
                cat.description = spec["description"]
                cat.color_code = spec["color_code"]
                cat.icon_emoji = spec["icon_emoji"]
                cat.jlpt_level = 5
                cat.display_order = spec["display_order"]
                action = "AKTUALISIERT"
            db.session.flush()
            slug_to_id[spec["slug"]] = cat.id
            print(f"  [{action}] [{cat.id}] {cat.slug:32s} {cat.name}")

        # Pass 2: prerequisite_category_id setzen
        for spec in N5_MODULES:
            if spec["prerequisite_slug"]:
                cat = (
                    db.session.query(LessonCategory)
                    .filter_by(slug=spec["slug"])
                    .first()
                )
                cat.prerequisite_category_id = slug_to_id.get(spec["prerequisite_slug"])

        db.session.commit()
        print()
        print(f"Fertig: {len(N5_MODULES)} N5-Module gesetzt.")
        print()
        print("Naechster Schritt: Bestehende Lektionen den Modulen zuordnen via")
        print("Admin-Panel (/admin/lessoncategory) oder Lesson.category zuweisen.")


if __name__ == "__main__":
    seed()

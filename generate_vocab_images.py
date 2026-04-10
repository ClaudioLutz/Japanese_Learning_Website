"""Einmaliges Script: Generiert Bilder fuer alle Vokabeln ohne image_url."""
import os
import uuid
import sys
import time

# UTF-8 Output erzwingen (Windows)
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app, db
from app.models import Vocabulary
from app.ai_services import AILessonContentGenerator

app = create_app()

with app.app_context():
    vocabs = Vocabulary.query.filter(
        (Vocabulary.image_url.is_(None)) | (Vocabulary.image_url == '')
    ).all()

    total = len(vocabs)
    print(f"Starte Bildgenerierung fuer {total} Vokabeln...")

    generator = AILessonContentGenerator()
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'vocabulary', 'images')
    os.makedirs(upload_dir, exist_ok=True)

    generated = 0
    errors = 0

    for i, vocab in enumerate(vocabs, 1):
        try:
            result = generator.generate_vocabulary_image(vocab.word, vocab.meaning)
            if 'error' in result:
                print(f"  [{i}/{total}] FEHLER {vocab.word}: {result['error']}")
                errors += 1
                continue

            filename = f"vocab_{vocab.id}_{uuid.uuid4().hex[:8]}.png"
            relative_path = f"vocabulary/images/{filename}"
            save_path = os.path.join(upload_dir, filename)

            result['image'].save(save_path, 'PNG')
            vocab.image_url = relative_path
            generated += 1
            print(f"  [{i}/{total}] OK {vocab.word} ({vocab.meaning})")

            # Alle 10 Bilder committen
            if generated % 10 == 0:
                db.session.commit()
                print(f"  --- Zwischenspeicherung: {generated} Bilder gespeichert ---")

        except Exception as e:
            print(f"  [{i}/{total}] FEHLER {vocab.word}: {e}")
            errors += 1

    db.session.commit()
    print(f"\nFertig! {generated} Bilder generiert, {errors} Fehler.")

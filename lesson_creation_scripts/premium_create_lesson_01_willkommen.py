#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium-Lektion 1: Willkommen in Japan!
========================================
Yukis Ankunft am Flughafen Narita.

Neue Elemente:
  - Hiragana: あいうえお かきくけこ (10 Zeichen)
  - Phrasen: はじめまして こんにちは ありがとう すみません はい いいえ
  - Konzept: 3 Schriftsysteme

Generiert mit: Gemini 3 Flash (Text), gpt-image-1-mini (Bilder), Google Cloud TTS (Audio)
"""
import os
import sys
import json
import uuid
import codecs
import builtins
from datetime import datetime
from pathlib import Path

# UTF-8 stdout auf Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

_original_print = builtins.print
def print_and_flush(*args, **kwargs):
    _original_print(*args, **kwargs)
    sys.stdout.flush()
builtins.print = print_and_flush

# Projekt-Root zum Path hinzufuegen
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# .env laden
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

from app import create_app, db
from app.models import (
    Lesson, LessonCategory, LessonContent, LessonPage,
    QuizQuestion, QuizOption, Kana, Vocabulary
)
from app.ai_services import AILessonContentGenerator, GoogleCloudTTS

# =============================================================================
# KONFIGURATION
# =============================================================================

LESSON_TITLE = "Willkommen in Japan!"
LESSON_DESCRIPTION = (
    "Yuki landet am Flughafen Narita und entdeckt die japanische Sprache. "
    "Lerne die ersten 10 Hiragana-Zeichen und 4 wichtige Begrüssungsphrasen."
)
LESSON_DIFFICULTY = 1  # Anfaenger
LESSON_CATEGORY = "Sprachgrundlagen"
LESSON_LEARNING_OBJECTIVE = "Die ersten 10 Hiragana lesen und 4 Begrüssungsphrasen verwenden können"

# Yuki Charakter-Prompt fuer konsistente Bilder
YUKI_PROMPT = (
    "young Swiss woman around 20 years old with brown shoulder-length hair, "
    "friendly face, wearing a casual travel outfit with a backpack, "
    "anime/manga art style, warm pastel colors, clean lines"
)

# Kana fuer diese Lektion
KANA_DATA = [
    {"character": "あ", "romanization": "a", "mnemonic": "Wie eine Ameise von oben betrachtet"},
    {"character": "い", "romanization": "i", "mnemonic": "Zwei Igelstacheln nebeneinander"},
    {"character": "う", "romanization": "u", "mnemonic": "Ein Uhu mit offenem Schnabel"},
    {"character": "え", "romanization": "e", "mnemonic": "Ein energisches Strichmännchen"},
    {"character": "お", "romanization": "o", "mnemonic": "Ein Opa mit Hut und Stock"},
    {"character": "か", "romanization": "ka", "mnemonic": "Ein Katana — die scharfen Striche"},
    {"character": "き", "romanization": "ki", "mnemonic": "Eine Kiste mit Deckel"},
    {"character": "く", "romanization": "ku", "mnemonic": "Ein offener Mund der 'ku' ruft"},
    {"character": "け", "romanization": "ke", "mnemonic": "Zwei Kettenglieder"},
    {"character": "こ", "romanization": "ko", "mnemonic": "Ein kleiner Koffer — zwei parallele Striche"},
]

# Vokabeln fuer diese Lektion
VOCABULARY_DATA = [
    {
        "word": "はじめまして",
        "reading": "hajimemashite",
        "meaning": "Freut mich (bei erster Begegnung)",
        "example_jp": "はじめまして。",
        "example_de": "Freut mich, Sie kennenzulernen.",
    },
    {
        "word": "こんにちは",
        "reading": "konnichiwa",
        "meaning": "Guten Tag",
        "example_jp": "こんにちは！",
        "example_de": "Guten Tag!",
    },
    {
        "word": "ありがとう",
        "reading": "arigatou",
        "meaning": "Danke",
        "example_jp": "ありがとう！",
        "example_de": "Danke!",
    },
    {
        "word": "すみません",
        "reading": "sumimasen",
        "meaning": "Entschuldigung / Pardon",
        "example_jp": "すみません。",
        "example_de": "Entschuldigung.",
    },
    {
        "word": "はい",
        "reading": "hai",
        "meaning": "Ja",
        "example_jp": "はい！",
        "example_de": "Ja!",
    },
    {
        "word": "いいえ",
        "reading": "iie",
        "meaning": "Nein / Keine Ursache",
        "example_jp": "いいえ！",
        "example_de": "Nein! / Keine Ursache!",
    },
]

# Seiten-Konfiguration
PAGES = [
    {
        "page_number": 1,
        "title": "Landung in Narita",
        "description": "Narrativer Einstieg — Die 3 Schriftsysteme",
    },
    {
        "page_number": 2,
        "title": "Die ersten 5 Zeichen: あ い う え お",
        "description": "Hiragana-Vokale mit Eselsbrücken",
    },
    {
        "page_number": 3,
        "title": "Die K-Reihe: か き く け こ",
        "description": "Hiragana K-Reihe und das Muster erkennen",
    },
    {
        "page_number": 4,
        "title": "Yuki sagt Hallo",
        "description": "4 Begrüssungsphrasen + Kulturnotiz",
    },
    {
        "page_number": 5,
        "title": "Die erste Begegnung",
        "description": "Mini-Dialog: Yuki trifft Tanaka-san",
    },
    {
        "page_number": 6,
        "title": "Jetzt bist du dran!",
        "description": "Quiz — Kana und Begrüssungen",
    },
]

# Bild-Konfiguration
IMAGE_PROMPTS = {
    "background": (
        "Narita Airport arrival hall, soft watercolor style, gentle pastel gradient, "
        "subtle Japanese elements, professional educational tile background, "
        "optimized for text overlay, no text in image"
    ),
    "page_1": (
        f"{YUKI_PROMPT}, standing in the arrival hall of Narita Airport Tokyo, "
        "looking amazed at Japanese signs around her, warm welcoming atmosphere, "
        "wide establishing shot, no text in image, 16:9 aspect ratio"
    ),
    "page_4": (
        f"{YUKI_PROMPT}, meeting a friendly male airport information desk staff member, "
        "both bowing slightly to each other, airport information counter in background, "
        "warm friendly atmosphere, no text in image"
    ),
    "page_5": (
        f"{YUKI_PROMPT}, having a conversation with a friendly male staff member at airport, "
        "speech bubble style composition, both characters smiling, "
        "warm atmosphere, no text in image"
    ),
}

# Dialog fuer Seite 5
DIALOGUE = [
    {"speaker": "Tanaka", "jp": "こんにちは！", "romaji": "konnichiwa!", "de": "Guten Tag!"},
    {"speaker": "Yuki", "jp": "こんにちは！はじめまして。", "romaji": "konnichiwa! hajimemashite.", "de": "Guten Tag! Freut mich."},
    {"speaker": "Tanaka", "jp": "はい、はじめまして。", "romaji": "hai, hajimemashite.", "de": "Ja, freut mich ebenfalls."},
    {"speaker": "Yuki", "jp": "ありがとう！", "romaji": "arigatou!", "de": "Danke!"},
    {"speaker": "Tanaka", "jp": "いいえ！", "romaji": "iie!", "de": "Keine Ursache!"},
]


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def save_image(image_result, lesson_id, name, app):
    """Speichert ein generiertes Bild und gibt den relativen Pfad zurueck."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{name}_{timestamp}_{unique_id}.png"

        upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        target_dir = os.path.join(upload_folder, 'lessons', 'image', f'lesson_{lesson_id}')
        os.makedirs(target_dir, exist_ok=True)

        final_path = os.path.join(target_dir, filename)

        if isinstance(image_result, dict) and 'image_bytes' in image_result:
            with open(final_path, 'wb') as f:
                f.write(image_result['image_bytes'])
            print(f"  Bild gespeichert: {final_path}")
        elif isinstance(image_result, dict) and 'image_url' in image_result:
            import urllib.request
            urllib.request.urlretrieve(image_result['image_url'], final_path)
            print(f"  Bild heruntergeladen: {final_path}")
        else:
            print(f"  Kein Bild-Format erkannt: {type(image_result)}")
            return None, 0

        relative_path = os.path.join('lessons', 'image', f'lesson_{lesson_id}', filename).replace('\\', '/')
        return relative_path, os.path.getsize(final_path)

    except Exception as e:
        print(f"  Fehler beim Speichern: {e}")
        return None, 0


def save_background(image_result, lesson_id, app):
    """Speichert ein Hintergrundbild."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"lesson_{lesson_id}_bg_{timestamp}_{unique_id}.png"

        upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        target_dir = os.path.join(upload_folder, 'lessons', 'backgrounds')
        os.makedirs(target_dir, exist_ok=True)

        final_path = os.path.join(target_dir, filename)

        if isinstance(image_result, dict) and 'image_bytes' in image_result:
            with open(final_path, 'wb') as f:
                f.write(image_result['image_bytes'])
        elif isinstance(image_result, dict) and 'image_url' in image_result:
            import urllib.request
            urllib.request.urlretrieve(image_result['image_url'], final_path)
        else:
            return None, 0

        relative_path = os.path.join('lessons', 'backgrounds', filename).replace('\\', '/')
        print(f"  Hintergrund gespeichert: {relative_path}")
        return relative_path, os.path.getsize(final_path)

    except Exception as e:
        print(f"  Fehler beim Hintergrund: {e}")
        return None, 0


# =============================================================================
# HAUPTFUNKTION
# =============================================================================

def create_premium_lesson(app):
    """Erstellt die komplette Premium-Lektion 1."""
    with app.app_context():
        print("=" * 60)
        print(f"PREMIUM-LEKTION: {LESSON_TITLE}")
        print("=" * 60)

        # ------------------------------------------------------------------
        # 1. BESTEHENDE LEKTION LOESCHEN (falls vorhanden)
        # ------------------------------------------------------------------
        existing = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing:
            print(f"Bestehende Lektion gefunden (ID {existing.id}) — wird geloescht...")
            # Zuerst Quiz-Optionen und Quiz-Fragen loeschen (FK-Constraint)
            content_ids = [c.id for c in LessonContent.query.filter_by(lesson_id=existing.id).all()]
            if content_ids:
                QuizOption.query.filter(
                    QuizOption.question_id.in_(
                        db.session.query(QuizQuestion.id).filter(QuizQuestion.lesson_content_id.in_(content_ids))
                    )
                ).delete(synchronize_session=False)
                QuizQuestion.query.filter(QuizQuestion.lesson_content_id.in_(content_ids)).delete(synchronize_session=False)
            LessonContent.query.filter_by(lesson_id=existing.id).delete()
            LessonPage.query.filter_by(lesson_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()
            print("  Geloescht.")

        # ------------------------------------------------------------------
        # 2. KATEGORIE FINDEN/ERSTELLEN
        # ------------------------------------------------------------------
        category = LessonCategory.query.filter_by(name=LESSON_CATEGORY).first()
        if not category:
            category = LessonCategory(name=LESSON_CATEGORY, description="Grundlagen der japanischen Sprache", color_code="#4CAF50")
            db.session.add(category)
            db.session.flush()
        print(f"Kategorie: {category.name} (ID {category.id})")

        # ------------------------------------------------------------------
        # 3. LEKTION ERSTELLEN
        # ------------------------------------------------------------------
        lesson = Lesson(
            title=LESSON_TITLE,
            description=LESSON_DESCRIPTION,
            lesson_type='free',
            difficulty_level=LESSON_DIFFICULTY,
            category_id=category.id,
            is_published=True,
            allow_guest_access=True,
            instruction_language='german',
        )
        db.session.add(lesson)
        db.session.flush()
        print(f"Lektion erstellt: ID {lesson.id}")

        # Seiten-Metadaten erstellen
        for page_cfg in PAGES:
            page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_cfg["page_number"],
                title=page_cfg["title"],
                description=page_cfg["description"],
            )
            db.session.add(page)
        db.session.flush()
        print(f"  {len(PAGES)} Seiten-Metadaten erstellt")

        # ------------------------------------------------------------------
        # 4. KANA-DATEN IN DB SICHERSTELLEN
        # ------------------------------------------------------------------
        print("\n--- Kana-Daten erstellen ---")
        kana_ids = {}
        for kd in KANA_DATA:
            existing_kana = Kana.query.filter_by(character=kd["character"]).first()
            if existing_kana:
                kana_ids[kd["character"]] = existing_kana.id
                print(f"  {kd['character']} ({kd['romanization']}) — existiert bereits (ID {existing_kana.id})")
            else:
                kana = Kana(
                    character=kd["character"],
                    romanization=kd["romanization"],
                    type="hiragana",
                )
                db.session.add(kana)
                db.session.flush()
                kana_ids[kd["character"]] = kana.id
                print(f"  {kd['character']} ({kd['romanization']}) — erstellt (ID {kana.id})")

        # ------------------------------------------------------------------
        # 5. VOCABULARY-DATEN IN DB SICHERSTELLEN
        # ------------------------------------------------------------------
        print("\n--- Vokabel-Daten erstellen ---")
        vocab_ids = {}
        for vd in VOCABULARY_DATA:
            existing_vocab = Vocabulary.query.filter_by(word=vd["word"]).first()
            if existing_vocab:
                vocab_ids[vd["word"]] = existing_vocab.id
                print(f"  {vd['word']} — existiert bereits (ID {existing_vocab.id})")
            else:
                vocab = Vocabulary(
                    word=vd["word"],
                    reading=vd["reading"],
                    meaning=vd["meaning"],
                    jlpt_level=5,
                    example_sentence_japanese=vd["example_jp"],
                    example_sentence_english=vd["example_de"],
                )
                db.session.add(vocab)
                db.session.flush()
                vocab_ids[vd["word"]] = vocab.id
                print(f"  {vd['word']} ({vd['reading']}) — erstellt (ID {vocab.id})")

        db.session.commit()

        # ------------------------------------------------------------------
        # 6. KI-GENERATOR INITIALISIEREN
        # ------------------------------------------------------------------
        print("\n--- KI-Generatoren initialisieren ---")
        generator = AILessonContentGenerator()

        # Audio-Verzeichnis (muss vor TTS-Test existieren)
        audio_dir = os.path.join(
            app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
            'lessons', 'audio', f'lesson_{lesson.id}'
        )
        os.makedirs(audio_dir, exist_ok=True)

        tts = None
        try:
            tts = GoogleCloudTTS()
            if tts.client:
                # Schnelltest: kann der Client ueberhaupt authentifizieren?
                test_result = tts.generate_audio("テスト", os.path.join(audio_dir, "_test.mp3"), speed=1.0)
                if "error" in test_result:
                    print(f"  Google Cloud TTS: Auth fehlgeschlagen — {test_result['error'][:80]}")
                    tts = None
                else:
                    # Testdatei loeschen
                    test_file = os.path.join(audio_dir, "_test.mp3")
                    if os.path.exists(test_file):
                        os.remove(test_file)
                    print("  Google Cloud TTS: OK (Test bestanden)")
            else:
                print("  Google Cloud TTS: Nicht verfuegbar (kein Client)")
                tts = None
        except Exception as e:
            print(f"  Google Cloud TTS: Fehler — {e}")
            tts = None

        order_idx = 0  # Globaler Zaehler fuer content order

        # ------------------------------------------------------------------
        # 7. HINTERGRUND-BILD
        # ------------------------------------------------------------------
        print("\n--- Hintergrund generieren ---")
        bg_result = generator.generate_single_image(IMAGE_PROMPTS["background"], "1024x1024", "standard")
        if "error" not in bg_result:
            bg_path, bg_size = save_background(bg_result, lesson.id, app)
            if bg_path:
                lesson.background_image_path = bg_path
                db.session.commit()
        else:
            print(f"  Hintergrund-Fehler: {bg_result['error']}")

        # ------------------------------------------------------------------
        # SEITE 1: Narrativer Einstieg
        # ------------------------------------------------------------------
        print("\n--- Seite 1: Narrativer Einstieg ---")

        # Bild: Yuki in Narita
        print("  Bild generieren...")
        img1 = generator.generate_single_image(IMAGE_PROMPTS["page_1"], "1536x1024", "hd")
        if "error" not in img1:
            img_path, img_size = save_image(img1, lesson.id, "narita_arrival", app)
            if img_path:
                content = LessonContent(
                    lesson_id=lesson.id, content_type='image', page_number=1, order_index=order_idx,
                    title="Yukis Ankunft am Flughafen Narita",
                    file_path=img_path, file_size=img_size, file_type='image/png',
                )
                db.session.add(content)
                order_idx += 1
        else:
            print(f"  Bild-Fehler: {img1['error']}")

        # Text: Einfuehrung 3 Schriftsysteme
        print("  Text generieren...")
        text_result = generator.generate_formatted_explanation(
            topic=(
                "Allererste Japanisch-Lektion fuer deutschsprachige Anfaenger. "
                "Yuki, eine Schweizer Studentin, landet am Flughafen Narita. "
                "Erklaere spielerisch die 3 Schriftsysteme: "
                "Hiragana (rund, Grundalphabet, 46 Zeichen), "
                "Katakana (eckig, Fremdwoerter), "
                "Kanji (komplex, aus China). "
                "Analogie: 'Stell dir vor, Deutsch haette 3 Alphabete...' "
                "Lernziel: Nach dieser Lektion die ersten 10 Hiragana lesen und sich begruessen koennen."
            ),
            difficulty="Anfaenger",
            keywords="Hiragana, Katakana, Kanji, Schriftsysteme, Japan, Narita, Yuki, konversationell, warm, Deutsch"
        )
        if "error" not in text_result:
            content = LessonContent(
                lesson_id=lesson.id, content_type='text', page_number=1, order_index=order_idx,
                title="Willkommen in Japan!",
                content_text=text_result.get("generated_text", ""),
            )
            db.session.add(content)
            order_idx += 1
            print("  Text erstellt")
        else:
            print(f"  Text-Fehler: {text_result['error']}")

        db.session.flush()

        # ------------------------------------------------------------------
        # SEITE 2: Hiragana あ-お (Vokale)
        # ------------------------------------------------------------------
        print("\n--- Seite 2: Hiragana Vokale ---")

        # Einleitungstext
        intro_text = (
            "<h2>Die 5 Vokale: あ い う え お</h2>"
            "<p>Yuki beginnt mit <strong>Hiragana</strong> — dem Grundalphabet. "
            "Jedes Zeichen steht fuer genau <strong>einen Klang</strong>. "
            "Fuenf Vokale bilden die Basis — wie A, E, I, O, U im Deutschen.</p>"
            "<p>Tipp: Jede Hiragana-Reihe kombiniert einen Konsonanten mit diesen 5 Vokalen. "
            "Also: <strong>ka, ki, ku, ke, ko</strong> — immer das gleiche Muster!</p>"
        )
        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=2, order_index=order_idx,
            title="Die 5 Vokale", content_text=intro_text,
        )
        db.session.add(content)
        order_idx += 1

        # Kana Flip-Cards: あ い う え お
        for i, kd in enumerate(KANA_DATA[:5]):
            kana_content = LessonContent(
                lesson_id=lesson.id, content_type='kana', page_number=2, order_index=order_idx,
                content_id=kana_ids[kd["character"]],
                title=f"{kd['character']} ({kd['romanization']})",
                content_text=f"Eselsbruecke: {kd['mnemonic']}",
            )
            db.session.add(kana_content)
            order_idx += 1

            # Audio generieren
            if tts:
                audio_result = tts.generate_kana_audio(kd["character"], kd["romanization"], audio_dir)
                if "error" not in audio_result:
                    # Audio als separater Content
                    rel_audio = os.path.join('lessons', 'audio', f'lesson_{lesson.id}', f"kana_{kd['romanization']}.mp3").replace('\\', '/')
                    audio_content = LessonContent(
                        lesson_id=lesson.id, content_type='audio', page_number=2, order_index=order_idx,
                        title=f"Aussprache: {kd['character']} ({kd['romanization']})",
                        file_path=rel_audio, file_type='audio/mpeg',
                    )
                    db.session.add(audio_content)
                    order_idx += 1

        print(f"  5 Kana-Cards + Audio erstellt")

        # ------------------------------------------------------------------
        # SEITE 3: Hiragana か-こ (K-Reihe)
        # ------------------------------------------------------------------
        print("\n--- Seite 3: Hiragana K-Reihe ---")

        intro_k = (
            "<h2>Die K-Reihe: か き く け こ</h2>"
            "<p>Jetzt kommt die <strong>ka-Reihe</strong>! Das Muster: "
            "<strong>K + jeder Vokal</strong> = か(ka) き(ki) く(ku) け(ke) こ(ko).</p>"
            "<p>Dieses Muster gilt fuer <strong>alle Reihen</strong> im Hiragana! "
            "In den naechsten Lektionen fuellen wir die Tabelle Reihe fuer Reihe.</p>"
        )
        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=3, order_index=order_idx,
            title="Die K-Reihe", content_text=intro_k,
        )
        db.session.add(content)
        order_idx += 1

        # Kana Flip-Cards: か き く け こ
        for kd in KANA_DATA[5:]:
            kana_content = LessonContent(
                lesson_id=lesson.id, content_type='kana', page_number=3, order_index=order_idx,
                content_id=kana_ids[kd["character"]],
                title=f"{kd['character']} ({kd['romanization']})",
                content_text=f"Eselsbruecke: {kd['mnemonic']}",
            )
            db.session.add(kana_content)
            order_idx += 1

            if tts:
                audio_result = tts.generate_kana_audio(kd["character"], kd["romanization"], audio_dir)
                if "error" not in audio_result:
                    rel_audio = os.path.join('lessons', 'audio', f'lesson_{lesson.id}', f"kana_{kd['romanization']}.mp3").replace('\\', '/')
                    audio_content = LessonContent(
                        lesson_id=lesson.id, content_type='audio', page_number=3, order_index=order_idx,
                        title=f"Aussprache: {kd['character']} ({kd['romanization']})",
                        file_path=rel_audio, file_type='audio/mpeg',
                    )
                    db.session.add(audio_content)
                    order_idx += 1

        # Zusammenfassungstext
        summary_text = (
            "<h2>Das Hiragana-Muster</h2>"
            "<p>Schau dir die Struktur an:</p>"
            "<table style='border-collapse:collapse; width:100%; text-align:center;'>"
            "<tr style='background:#f0f0f0;'><th></th><th>a</th><th>i</th><th>u</th><th>e</th><th>o</th></tr>"
            "<tr><td><strong>-</strong></td><td>あ</td><td>い</td><td>う</td><td>え</td><td>お</td></tr>"
            "<tr style='background:#e8f5e9;'><td><strong>k</strong></td><td>か</td><td>き</td><td>く</td><td>け</td><td>こ</td></tr>"
            "<tr><td><strong>s</strong></td><td style='color:#ccc;'>さ</td><td style='color:#ccc;'>し</td>"
            "<td style='color:#ccc;'>す</td><td style='color:#ccc;'>せ</td><td style='color:#ccc;'>そ</td></tr>"
            "<tr><td><strong>...</strong></td><td colspan='5' style='color:#ccc;'>kommt in den naechsten Lektionen!</td></tr>"
            "</table>"
            "<p>Gruen = was du schon kannst! In Lektion 2 kommt die <strong>S-Reihe</strong>.</p>"
        )
        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=3, order_index=order_idx,
            title="Das Hiragana-Muster", content_text=summary_text,
        )
        db.session.add(content)
        order_idx += 1
        print(f"  5 Kana-Cards + Tabelle erstellt")

        # ------------------------------------------------------------------
        # SEITE 4: Erste Worte — Begrüssungen
        # ------------------------------------------------------------------
        print("\n--- Seite 4: Begrüssungen ---")

        # Bild: Yuki trifft Tanaka
        print("  Bild generieren...")
        img4 = generator.generate_single_image(IMAGE_PROMPTS["page_4"], "1024x1024", "standard")
        if "error" not in img4:
            img_path, img_size = save_image(img4, lesson.id, "yuki_tanaka_meeting", app)
            if img_path:
                content = LessonContent(
                    lesson_id=lesson.id, content_type='image', page_number=4, order_index=order_idx,
                    title="Yuki trifft Tanaka-san",
                    file_path=img_path, file_size=img_size, file_type='image/png',
                )
                db.session.add(content)
                order_idx += 1

        # Kontext-Text
        context_text = (
            "<p>Am Informationsschalter trifft Yuki den freundlichen <strong>Tanaka-san</strong>. "
            "Jetzt braucht sie die wichtigsten Woerter...</p>"
        )
        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=4, order_index=order_idx,
            title="Am Informationsschalter", content_text=context_text,
        )
        db.session.add(content)
        order_idx += 1

        # Vocabulary Flip-Cards
        for vd in VOCABULARY_DATA:
            vocab_content = LessonContent(
                lesson_id=lesson.id, content_type='vocabulary', page_number=4, order_index=order_idx,
                content_id=vocab_ids[vd["word"]],
                title=f"{vd['word']} ({vd['reading']})",
            )
            db.session.add(vocab_content)
            order_idx += 1

            # Audio
            if tts:
                audio_result = tts.generate_vocabulary_audio(vd["word"], vd["reading"], audio_dir)
                if "error" not in audio_result:
                    rel_audio = os.path.join('lessons', 'audio', f'lesson_{lesson.id}', f"vocab_{vd['reading'].replace(' ', '_')}.mp3").replace('\\', '/')
                    audio_content = LessonContent(
                        lesson_id=lesson.id, content_type='audio', page_number=4, order_index=order_idx,
                        title=f"Aussprache: {vd['word']}",
                        file_path=rel_audio, file_type='audio/mpeg',
                    )
                    db.session.add(audio_content)
                    order_idx += 1

        # Kulturnotiz
        culture_text = (
            "<h2>Kulturnotiz: Verbeugung</h2>"
            "<p>In Japan verbeugt man sich zur Begruessung — je tiefer, desto respektvoller. "
            "Ein leichtes Nicken (etwa 15 Grad) reicht unter Gleichaltrigen. "
            "Bei aelteren Personen oder im Geschaeft verbeugt man sich tiefer (30-45 Grad).</p>"
            "<p><strong>Gut zu wissen:</strong> <em>すみません</em> (sumimasen) ist ein Allround-Wort! "
            "Es bedeutet 'Entschuldigung', aber auch 'Pardon' um jemanden anzusprechen, "
            "und sogar 'Danke' in bestimmten Situationen.</p>"
        )
        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=4, order_index=order_idx,
            title="Kulturnotiz", content_text=culture_text,
        )
        db.session.add(content)
        order_idx += 1
        print(f"  6 Vokabel-Cards + Kulturnotiz erstellt")

        # ------------------------------------------------------------------
        # SEITE 5: Dialog
        # ------------------------------------------------------------------
        print("\n--- Seite 5: Dialog ---")

        # Bild
        print("  Bild generieren...")
        img5 = generator.generate_single_image(IMAGE_PROMPTS["page_5"], "1024x1024", "standard")
        if "error" not in img5:
            img_path, img_size = save_image(img5, lesson.id, "yuki_tanaka_dialogue", app)
            if img_path:
                content = LessonContent(
                    lesson_id=lesson.id, content_type='image', page_number=5, order_index=order_idx,
                    title="Dialog: Am Informationsschalter",
                    file_path=img_path, file_size=img_size, file_type='image/png',
                )
                db.session.add(content)
                order_idx += 1

        # Dialog als formatierter Text (bis dialogue-Typ implementiert)
        dialogue_html = "<h2>Dialog: Am Informationsschalter</h2>\n"
        dialogue_html += '<div style="background:#f8f9fa; border-radius:12px; padding:20px; margin:10px 0;">\n'

        for line in DIALOGUE:
            is_yuki = line["speaker"] == "Yuki"
            align = "right" if is_yuki else "left"
            bg_color = "#e3f2fd" if is_yuki else "#fff3e0"
            speaker_color = "#1565c0" if is_yuki else "#e65100"

            dialogue_html += f'<div style="text-align:{align}; margin:12px 0;">\n'
            dialogue_html += f'  <div style="display:inline-block; background:{bg_color}; border-radius:12px; padding:12px 16px; max-width:80%; text-align:left;">\n'
            dialogue_html += f'    <strong style="color:{speaker_color};">{line["speaker"]}:</strong><br>\n'
            dialogue_html += f'    <span style="font-size:1.3em;">{line["jp"]}</span><br>\n'
            dialogue_html += f'    <span style="color:#666; font-size:0.9em;">({line["romaji"]})</span><br>\n'
            dialogue_html += f'    <span style="color:#888; font-size:0.85em;">{line["de"]}</span>\n'
            dialogue_html += f'  </div>\n'
            dialogue_html += f'</div>\n'

        dialogue_html += '</div>\n'
        dialogue_html += (
            '<p><strong>Beachte:</strong> <em>いいえ</em> (iie) heisst eigentlich "Nein", '
            'wird hier aber als "Keine Ursache" / "Gern geschehen" verwendet. '
            'Japanisch ist stark <strong>kontextabhaengig</strong>!</p>'
        )

        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=5, order_index=order_idx,
            title="Dialog: Am Informationsschalter", content_text=dialogue_html,
        )
        db.session.add(content)
        order_idx += 1

        # Dialog-Audio
        if tts:
            for i, line in enumerate(DIALOGUE):
                voice = 'female' if line["speaker"] == "Yuki" else 'male'
                audio_result = tts.generate_dialogue_audio(line["jp"], i + 1, audio_dir, voice=voice)
                if "error" not in audio_result:
                    rel_audio = os.path.join('lessons', 'audio', f'lesson_{lesson.id}', f"dialogue_{i+1:02d}_{voice}.mp3").replace('\\', '/')
                    audio_content = LessonContent(
                        lesson_id=lesson.id, content_type='audio', page_number=5, order_index=order_idx,
                        title=f"{line['speaker']}: {line['jp']}",
                        file_path=rel_audio, file_type='audio/mpeg',
                    )
                    db.session.add(audio_content)
                    order_idx += 1
            print(f"  {len(DIALOGUE)} Dialog-Audio-Clips erstellt")

        print(f"  Dialog erstellt")

        # ------------------------------------------------------------------
        # SEITE 6: Quiz
        # ------------------------------------------------------------------
        print("\n--- Seite 6: Quiz ---")

        quiz_intro = (
            "<h2>Jetzt bist du dran!</h2>"
            "<p>Teste dein Wissen! Du brauchst mindestens 80% richtig, "
            "um zur naechsten Lektion weiterzugehen.</p>"
        )
        content = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            title="Quiz-Einleitung", content_text=quiz_intro,
        )
        db.session.add(content)
        order_idx += 1

        # Quiz 1: Matching — Kana あ-お → Romaji
        quiz_content_1 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Kana-Quiz: Vokale",
        )
        db.session.add(quiz_content_1)
        db.session.flush()
        order_idx += 1

        q1 = QuizQuestion(
            lesson_content_id=quiz_content_1.id,
            question_type='matching',
            question_text='Ordne die Hiragana-Vokale den richtigen Lesungen zu:',
            explanation='Die 5 Vokale あいうえお sind die Basis aller Hiragana-Reihen.',
            difficulty_level=1, points=2,
        )
        db.session.add(q1)
        db.session.flush()

        vowel_pairs = [("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o")]
        for idx, (kana_char, romaji) in enumerate(vowel_pairs):
            opt = QuizOption(question_id=q1.id, option_text=kana_char, is_correct=True, feedback=romaji, order_index=idx)
            db.session.add(opt)

        # Quiz 2: Matching — Kana か-こ → Romaji
        quiz_content_2 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Kana-Quiz: K-Reihe",
        )
        db.session.add(quiz_content_2)
        db.session.flush()
        order_idx += 1

        q2 = QuizQuestion(
            lesson_content_id=quiz_content_2.id,
            question_type='matching',
            question_text='Ordne die K-Reihe den richtigen Lesungen zu:',
            explanation='Die K-Reihe folgt dem Muster: K + Vokal = ka, ki, ku, ke, ko.',
            difficulty_level=1, points=2,
        )
        db.session.add(q2)
        db.session.flush()

        k_pairs = [("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko")]
        for idx, (kana_char, romaji) in enumerate(k_pairs):
            opt = QuizOption(question_id=q2.id, option_text=kana_char, is_correct=True, feedback=romaji, order_index=idx)
            db.session.add(opt)

        # Quiz 3: Multiple Choice — はじめまして
        quiz_content_3 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Begrüssungs-Quiz 1",
        )
        db.session.add(quiz_content_3)
        db.session.flush()
        order_idx += 1

        q3 = QuizQuestion(
            lesson_content_id=quiz_content_3.id,
            question_type='multiple_choice',
            question_text='Was bedeutet はじめまして (hajimemashite)?',
            explanation='はじめまして wird bei der allerersten Begegnung mit jemandem verwendet.',
            difficulty_level=1, points=1,
        )
        db.session.add(q3)
        db.session.flush()

        mc_options_3 = [
            ("Auf Wiedersehen", False, "Das waere さようなら (sayounara)."),
            ("Freut mich (bei erster Begegnung)", True, "Richtig! はじめまして verwendet man bei der ersten Begegnung."),
            ("Guten Morgen", False, "Das waere おはようございます (ohayou gozaimasu)."),
            ("Entschuldigung", False, "Das waere すみません (sumimasen)."),
        ]
        for idx, (text, correct, feedback) in enumerate(mc_options_3):
            opt = QuizOption(question_id=q3.id, option_text=text, is_correct=correct, feedback=feedback, order_index=idx)
            db.session.add(opt)

        # Quiz 4: Multiple Choice — Welches Zeichen ist 'ka'?
        quiz_content_4 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Kana-Erkennung",
        )
        db.session.add(quiz_content_4)
        db.session.flush()
        order_idx += 1

        q4 = QuizQuestion(
            lesson_content_id=quiz_content_4.id,
            question_type='multiple_choice',
            question_text='Welches Zeichen liest man "ka"?',
            explanation='か ist das erste Zeichen der K-Reihe: ka, ki, ku, ke, ko.',
            difficulty_level=1, points=1,
        )
        db.session.add(q4)
        db.session.flush()

        mc_options_4 = [
            ("こ", False, "Das ist 'ko' — das letzte der K-Reihe."),
            ("く", False, "Das ist 'ku'."),
            ("か", True, "Richtig! か = ka."),
            ("き", False, "Das ist 'ki'."),
        ]
        for idx, (text, correct, feedback) in enumerate(mc_options_4):
            opt = QuizOption(question_id=q4.id, option_text=text, is_correct=correct, feedback=feedback, order_index=idx)
            db.session.add(opt)

        # Quiz 5: True/False — Schriftsysteme
        quiz_content_5 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Schriftsysteme-Quiz",
        )
        db.session.add(quiz_content_5)
        db.session.flush()
        order_idx += 1

        q5 = QuizQuestion(
            lesson_content_id=quiz_content_5.id,
            question_type='true_false',
            question_text='Japanisch hat 2 Schriftsysteme.',
            explanation='Falsch! Japanisch hat 3 Schriftsysteme: Hiragana, Katakana und Kanji.',
            difficulty_level=1, points=1,
        )
        db.session.add(q5)
        db.session.flush()

        opt_true = QuizOption(question_id=q5.id, option_text='True', is_correct=False, feedback='Falsch! Es sind 3: Hiragana, Katakana und Kanji.', order_index=0)
        opt_false = QuizOption(question_id=q5.id, option_text='False', is_correct=True, feedback='Richtig! Japanisch hat 3 Schriftsysteme.', order_index=1)
        db.session.add_all([opt_true, opt_false])

        # Quiz 6: Multiple Choice — Situation
        quiz_content_6 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Situationsquiz",
        )
        db.session.add(quiz_content_6)
        db.session.flush()
        order_idx += 1

        q6 = QuizQuestion(
            lesson_content_id=quiz_content_6.id,
            question_type='multiple_choice',
            question_text='Yuki moechte sich entschuldigen. Was sagt sie?',
            explanation='すみません (sumimasen) ist das Wort fuer "Entschuldigung" und auch "Pardon".',
            difficulty_level=1, points=1,
        )
        db.session.add(q6)
        db.session.flush()

        mc_options_6 = [
            ("ありがとう", False, "Das bedeutet 'Danke'."),
            ("はい", False, "Das bedeutet 'Ja'."),
            ("すみません", True, "Richtig! すみません = Entschuldigung."),
            ("こんにちは", False, "Das bedeutet 'Guten Tag'."),
        ]
        for idx, (text, correct, feedback) in enumerate(mc_options_6):
            opt = QuizOption(question_id=q6.id, option_text=text, is_correct=correct, feedback=feedback, order_index=idx)
            db.session.add(opt)

        # Quiz 7: Fill-in-the-blank
        quiz_content_7 = LessonContent(
            lesson_id=lesson.id, content_type='text', page_number=6, order_index=order_idx,
            is_interactive=True, quiz_type='standard', passing_score=80,
            title="Lueckentext",
        )
        db.session.add(quiz_content_7)
        db.session.flush()
        order_idx += 1

        q7 = QuizQuestion(
            lesson_content_id=quiz_content_7.id,
            question_type='fill_blank',
            question_text='Vervollstaendige die Begruessung: こんにち___',
            explanation='こんにちは (konnichiwa) — Guten Tag! Das は wird hier "wa" ausgesprochen.',
            hint='Tipp: Es ist ein Hiragana-Zeichen, das normalerweise "ha" gelesen wird.',
            difficulty_level=1, points=1,
        )
        db.session.add(q7)
        db.session.flush()

        opt_correct = QuizOption(question_id=q7.id, option_text='は', is_correct=True, feedback='Richtig! こんにちは — das は wird hier als "wa" ausgesprochen.', order_index=0)
        db.session.add(opt_correct)

        print(f"  7 Quiz-Fragen erstellt")

        # ------------------------------------------------------------------
        # FINAL COMMIT
        # ------------------------------------------------------------------
        db.session.commit()
        print("\n" + "=" * 60)
        print(f"LEKTION ERFOLGREICH ERSTELLT!")
        print(f"  ID: {lesson.id}")
        print(f"  Titel: {lesson.title}")
        print(f"  Seiten: {len(PAGES)}")
        print(f"  Kana: {len(KANA_DATA)} Zeichen")
        print(f"  Vokabeln: {len(VOCABULARY_DATA)} Phrasen")
        print(f"  Quiz: 7 Fragen")
        print(f"  Audio: {'Ja' if tts else 'Nein (TTS nicht verfuegbar)'}")
        print("=" * 60)

        return lesson.id


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    app = create_app()
    lesson_id = create_premium_lesson(app)
    if lesson_id:
        print(f"\nLektion unter http://localhost:5000/lesson/{lesson_id} ansehen")

"""Repariert Lesson 142 nach Claudios Feedback:
1. HTML-Tags aus content_text entfernen (lesson_view.html nutzt | nl2br).
2. Vocabulary.romaji fuer alle 10 Woerter der Lesson setzen.
3. example_sentence_english um Romaji-Prefix ergaenzen.
4. Grammar.example_sentences ebenfalls um Romaji aufraeumen (schon ok, nur pruefen).
"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import Lesson, LessonContent, Vocabulary, Grammar

LESSON_ID = 142
HTML_TAG_RE = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")

# Vocabulary Updates: (word, romaji, example_en_with_romaji)
VOCAB_UPDATES = [
    ("レストラン", "resutoran",
        "Resutoran de bangohan wo tabemasu. — I eat dinner at a restaurant."),
    ("メニュー", "menyuu",
        "Menyuu wo kudasai. — Please give me the menu."),
    ("水", "mizu",
        "Mizu wo nomimasu. — I drink water."),
    ("お茶", "o-cha",
        "O-cha wa atsui desu. — The tea is hot."),
    ("ご飯", "gohan",
        "Gohan wo tabemasu. — I eat rice (a meal)."),
    ("肉", "niku",
        "Niku wa oishii desu. — The meat is delicious."),
    ("魚", "sakana",
        "Sakana wo tabemasu ka? — Do you eat fish?"),
    ("飲み物", "nomimono",
        "Nomimono wa nan desu ka? — What is the drink?"),
    ("食べ物", "tabemono",
        "Nihon no tabemono ga suki desu. — I like Japanese food."),
    ("美味しい", "oishii",
        "Kono gohan wa oishii desu. — This rice is delicious."),
]

# Neue Plaintext-content_texts (aus vorherigem Draft, HTML entfernt,
# \n\n fuer Absaetze, 「…」-Anfuehrungen, Romaji in Klammern)
PLAINTEXT_CONTENT = {
    "Willkommen im Restaurant": (
        "In dieser Lektion lernst du, wie du in Japan im Restaurant bestellst. "
        "Dort begruesst dich das Personal meist mit 「いらっしゃいませ」 "
        "(irasshaimase, 'Willkommen'). Gleich darauf bekommst du die Speisekarte "
        "(メニュー / menyuu) und wirst gefragt, was du moechtest.\n\n"
        "Lerne zuerst die zehn wichtigsten Woerter. Danach lernst du die hoefliche "
        "Phrase, mit der du alles bestellen kannst."
    ),
    "「〜をください」 — Ich hätte gern ~": (
        "Wenn du in Japan etwas bestellen oder hoeflich um etwas bitten moechtest, "
        "nutzt du das Muster 「〜をください」 (~ wo kudasai). Es entspricht ungefaehr "
        "'Ich haette gern ~' oder 'Bitte geben Sie mir ~'.\n\n"
        "Das Partikel 「を」 (wo, wird 'o' ausgesprochen) markiert das Objekt, "
        "das du haben moechtest. 「ください」 ist die hoefliche Bitte-Form "
        "von 「くれる」 (kureru, 'geben').\n\n"
        "Diese Phrase funktioniert in Restaurants, Laeden und ueberall, "
        "wo du hoeflich um etwas bittest."
    ),
    "Quiz": (
        "Sieben Fragen zu Vokabeln und Grammatik. Viel Erfolg!"
    ),
    "Was du jetzt kannst": (
        "Du kannst jetzt:\n\n"
        "- zehn Grundvokabeln rund ums Restaurant erkennen: "
        "レストラン, メニュー, 水, お茶, ご飯, 肉, 魚, 飲み物, 食べ物, 美味しい,\n"
        "- mit der hoeflichen Formel 「〜をください」 (~ wo kudasai) alles bestellen, "
        "was auf der Karte steht,\n"
        "- positiv auf gutes Essen reagieren mit 「おいしいです」 (oishii desu).\n\n"
        "Naechster Schritt: In der naechsten Lektion lernst du Zahlen und wie du "
        "die Rechnung verlangst (「おかいけいを ください」 / o-kaikei wo kudasai — "
        "'Die Rechnung bitte').\n\n"
        "Tipp: Wiederhole die neuen Vokabeln noch heute im Kartensystem — "
        "so bleiben sie am besten haengen."
    ),
}

app = create_app()

with app.app_context():
    fixed_count = 0

    # 1. content_text HTML entfernen
    contents = (
        db.session.query(LessonContent)
        .filter(LessonContent.lesson_id == LESSON_ID, LessonContent.content_type == "text")
        .all()
    )
    for c in contents:
        if not c.title or not c.content_text:
            continue
        if c.title in PLAINTEXT_CONTENT:
            old_had_tags = bool(HTML_TAG_RE.search(c.content_text))
            c.content_text = PLAINTEXT_CONTENT[c.title]
            print(f"[FIX] content_text '{c.title}' (HTML entfernt: {old_had_tags})")
            fixed_count += 1
        else:
            print(f"[SKIP] content_text '{c.title}' (kein Plaintext definiert)")

    # 2. Vocabulary.romaji + example_sentence_english
    for word, romaji, ex_en in VOCAB_UPDATES:
        v = db.session.query(Vocabulary).filter_by(word=word).first()
        if not v:
            print(f"[WARN] Vocabulary '{word}' nicht gefunden")
            continue
        v.romaji = romaji
        v.example_sentence_english = ex_en
        print(f"[FIX] Vocabulary '{word}' → romaji='{romaji}'")
        fixed_count += 1

    db.session.commit()
    print(f"\n[OK] {fixed_count} Updates committed.")

"""Lesson-142-Fix #2: Umlaute wiederherstellen, Romaji in allen Texten und
Grammar-Feldern ergaenzen (Claudios Feedback 2026-04-24 21:30).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import LessonContent, Grammar

LESSON_ID = 142

PLAINTEXT_CONTENT_V2 = {
    "Willkommen im Restaurant": (
        "In dieser Lektion lernst du, wie du in Japan im Restaurant bestellst. "
        "Dort begrüßt dich das Personal meist mit 「いらっしゃいませ」 "
        "(irasshaimase, 'Willkommen'). Gleich darauf bekommst du die Speisekarte "
        "(メニュー / menyuu) und wirst gefragt, was du möchtest.\n\n"
        "Lerne zuerst die zehn wichtigsten Wörter. Danach lernst du die höfliche "
        "Phrase, mit der du alles bestellen kannst."
    ),
    "「〜をください」 — Ich hätte gern ~": (
        "Wenn du in Japan etwas bestellen oder höflich um etwas bitten möchtest, "
        "nutzt du das Muster 「〜をください」 (~ wo kudasai). Es entspricht ungefähr "
        "'Ich hätte gern ~' oder 'Bitte geben Sie mir ~'.\n\n"
        "Das Partikel 「を」 (wo, wird 'o' ausgesprochen) markiert das Objekt, "
        "das du haben möchtest. 「ください」 (kudasai) ist die höfliche Bitte-Form "
        "von 「くれる」 (kureru, 'geben').\n\n"
        "Diese Phrase funktioniert in Restaurants, Läden und überall, "
        "wo du höflich um etwas bittest."
    ),
    "Quiz": (
        "Sieben Fragen zu Vokabeln und Grammatik. Viel Erfolg!"
    ),
    "Was du jetzt kannst": (
        "Du kannst jetzt:\n\n"
        "- zehn Grundvokabeln rund ums Restaurant erkennen: "
        "レストラン (resutoran), メニュー (menyuu), 水 (mizu), お茶 (o-cha), "
        "ご飯 (gohan), 肉 (niku), 魚 (sakana), 飲み物 (nomimono), "
        "食べ物 (tabemono), 美味しい (oishii),\n"
        "- mit der höflichen Formel 「〜をください」 (~ wo kudasai) alles bestellen, "
        "was auf der Karte steht,\n"
        "- positiv auf gutes Essen reagieren mit 「おいしいです」 (oishii desu).\n\n"
        "Nächster Schritt: In der nächsten Lektion lernst du Zahlen und wie du "
        "die Rechnung verlangst (「おかいけいを ください」 / o-kaikei wo kudasai — "
        "'Die Rechnung bitte').\n\n"
        "Tipp: Wiederhole die neuen Vokabeln noch heute im Kartensystem — "
        "so bleiben sie am besten hängen."
    ),
}

GRAMMAR_FIX = {
    "〜をください (höfliche Bitte)": {
        "new_title": "〜をください (~ wo kudasai — höfliche Bitte)",
        "structure": "[Nomen] + を + ください  ([Nomen] + wo + kudasai)",
        "romaji": "[Nomen] + wo + kudasai",
        "explanation": (
            "「〜をください」 (~ wo kudasai) ist die Standard-Formel, um in Japan höflich "
            "um etwas zu bitten. Das Partikel 「を」 (wo, ausgesprochen 'o') markiert "
            "das Objekt der Bitte, 「ください」 (kudasai) ist die höfliche Bitte-Form "
            "des Verbs 「くれる」 (kureru, 'geben'). "
            "Du nutzt diese Phrase im Restaurant, um Essen oder Getränke zu bestellen, "
            "aber auch in Geschäften, um nach einer Ware zu fragen. "
            "Sie ist in allen Alltagssituationen sicher und höflich."
        ),
        "example_sentences": (
            "みずを ください。\n"
            "  (Mizu wo kudasai.)\n"
            "  → Wasser, bitte.\n\n"
            "おちゃを ください。\n"
            "  (O-cha wo kudasai.)\n"
            "  → Ich hätte gern grünen Tee.\n\n"
            "メニューを ください。\n"
            "  (Menyuu wo kudasai.)\n"
            "  → Die Speisekarte, bitte."
        ),
    }
}


app = create_app()

with app.app_context():
    fixed = 0

    # content_text v2
    for c in db.session.query(LessonContent).filter_by(
        lesson_id=LESSON_ID, content_type="text"
    ).all():
        if c.title in PLAINTEXT_CONTENT_V2:
            c.content_text = PLAINTEXT_CONTENT_V2[c.title]
            print(f"[FIX] content_text '{c.title}'")
            fixed += 1

    # Grammar (global — wird in anderen Lessons mitverwendet, ist OK)
    for old_title, patch in GRAMMAR_FIX.items():
        g = db.session.query(Grammar).filter_by(title=old_title).first()
        if not g:
            print(f"[WARN] Grammar '{old_title}' nicht gefunden")
            continue
        # title ist unique — neuen title nur setzen, wenn nicht schon anderer Eintrag existiert
        if patch.get("new_title") and patch["new_title"] != g.title:
            collide = db.session.query(Grammar).filter_by(title=patch["new_title"]).first()
            if not collide:
                g.title = patch["new_title"]
        g.structure = patch["structure"]
        g.romaji = patch["romaji"]
        g.explanation = patch["explanation"]
        g.example_sentences = patch["example_sentences"]
        print(f"[FIX] Grammar #{g.id} title, structure, explanation, example_sentences")
        fixed += 1

    db.session.commit()
    print(f"\n[OK] {fixed} updates committed.")

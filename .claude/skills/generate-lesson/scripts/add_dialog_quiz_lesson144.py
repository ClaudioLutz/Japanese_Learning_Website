"""Fuegt Verstaendnisfragen-Quiz zur Dialog-Page von Lesson 144 hinzu.

User-Direktive 2026-04-25: Auf der Dialog-Seite sollen Verstaendnisfragen
zum Inhalt direkt im Anschluss als Quiz angeboten werden.

4 Fragen zum Tanaka-Lisa-Dialog (Lesson 144, Page 5):
- Q1 (MC): Wieviele Personen hat Tanakas Familie?
- Q2 (MC): Wie alt ist Tanakas aeltere Schwester?
- Q3 (MC): Wo wohnen Tanakas Eltern?
- Q4 (TF): Lisa hat zwei juengere Brueder.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app import create_app, db
from app.models import LessonContent, QuizQuestion, QuizOption

app = create_app()
with app.app_context():
    # Pruefe ob bereits ein Quiz auf Page 5 existiert
    existing = LessonContent.query.filter_by(
        lesson_id=144, page_number=5, content_type='quiz'
    ).first()
    if existing:
        print(f"[SKIP] Quiz auf Page 5 existiert bereits (id={existing.id}).")
        sys.exit(0)

    # Neues Quiz-LessonContent (order_index=4, nach Slideshow + Text)
    lc = LessonContent(
        lesson_id=144,
        page_number=5,
        content_type='quiz',
        title='Verstaendnisfragen zum Dialog',
        content_text='Pruefe dein Verstaendnis des Dialogs zwischen Tanaka und Lisa.',
        order_index=4,
        is_interactive=True,
        quiz_type='standard',
        max_attempts=3,
        passing_score=75,
        generated_by_ai=True,
    )
    db.session.add(lc)
    db.session.flush()

    questions = [
        {
            "type": "multiple_choice",
            "text": "Wieviele Personen hat Tanakas Familie?",
            "hint": "Tanaka sagt es ganz am Anfang.",
            "explanation": "Tanaka sagt: 「watashi no kazoku wa yo-nin desu」 (わたしの かぞくは 四人です) — vier Personen: Vater, Mutter, ältere Schwester und er selbst.",
            "options": [
                ("Drei Personen", False, "Falsch — Tanaka sagt vier (yo-nin)."),
                ("Vier Personen", True, "Richtig! 「四人です」 (yo-nin desu)."),
                ("Fünf Personen", False, "Lisas Familie hat fünf, nicht Tanakas."),
                ("Sechs Personen", False, "Falsch — die Antwort steht im ersten Satz."),
            ],
        },
        {
            "type": "multiple_choice",
            "text": "Wie alt ist Tanakas ältere Schwester (おねえさん, oneesan)?",
            "hint": "Eine Zahl mit 「さい」 (sai) am Ende.",
            "explanation": "Tanaka sagt: 「ane wa sanjuugo-sai desu」 (あねは さんじゅうごさいです) — 35 Jahre alt.",
            "options": [
                ("25 Jahre alt", False, "Falsch — nicht ni-juu-go-sai."),
                ("30 Jahre alt", False, "Falsch — nicht san-juu-sai."),
                ("35 Jahre alt", True, "Richtig! 「sanjuugo-sai」 = 35."),
                ("40 Jahre alt", False, "Falsch — nicht yon-juu-sai."),
            ],
        },
        {
            "type": "multiple_choice",
            "text": "Wo wohnen Tanakas Eltern (りょうしん, ryoushin)?",
            "hint": "Tanaka erwähnt eine grosse japanische Stadt.",
            "explanation": "Tanaka sagt: 「ryoushin wa Oosaka ni imasu」 (りょうしんは おおさかに います) — in Osaka. Beachte: 「imasu」 (Lebewesen), nicht 「arimasu」 (Dinge).",
            "options": [
                ("In Tokyo (とうきょう, Toukyou)", False, "In Tokyo lebt nur seine ältere Schwester."),
                ("In Osaka (おおさか, Oosaka)", True, "Richtig! Die Eltern leben in Osaka."),
                ("In Kyoto (きょうと, Kyouto)", False, "Falsch — Kyoto wird im Dialog nicht erwähnt."),
                ("In Zürich (チューリッヒ, Chuurihhi)", False, "Falsch — Tanaka selbst arbeitet in Zürich, aber seine Eltern sind in Japan."),
            ],
        },
        {
            "type": "true_false",
            "text": "Lisas Familie besteht aus fünf Personen, darunter zwei jüngere Brüder (おとうと, otouto).",
            "hint": "Schau dir Lisas Antwort am Ende des Dialogs an.",
            "explanation": "Stimmt. Lisa sagt: 「watashi no kazoku wa go-nin desu. ryoushin to otouto ga futari imasu」 (わたしの かぞくは 五人です。 りょうしんと おとうとが 二人 います) — 5 Personen: Eltern + 2 jüngere Brüder + sie selbst.",
            "options": [
                ("Richtig", True, "Korrekt — 5 Personen: Lisa + Eltern + 2 おとうと (otouto)."),
                ("Falsch", False, "Doch — Lisa sagt go-nin desu mit 2 otouto."),
            ],
        },
    ]

    for idx, q in enumerate(questions, start=1):
        qq = QuizQuestion(
            lesson_content_id=lc.id,
            question_type=q["type"],
            question_text=q["text"],
            hint=q.get("hint"),
            explanation=q.get("explanation"),
            difficulty_level=2,
            points=1,
            order_index=idx,
        )
        db.session.add(qq)
        db.session.flush()
        for opt_idx, (text, is_correct, feedback) in enumerate(q["options"], start=1):
            db.session.add(QuizOption(
                question_id=qq.id,
                option_text=text,
                is_correct=is_correct,
                feedback=feedback,
                order_index=opt_idx,
            ))

    db.session.commit()
    print(f"[OK] Quiz LessonContent {lc.id} angelegt mit {len(questions)} Fragen.")

#!/usr/bin/env python3
"""Fix remaining untranslated quiz questions."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.models import QuizQuestion, QuizOption

FIXES = {
    3411: {
        "q": "Sie sind im Kaufhaus und möchten die Toilette finden. Welcher Satz ist die natürlichste Art zu fragen?",
        "e": "Um nach dem Ort zu fragen, verwendet man das Muster '[Nomen] wa doko desu ka (～はどこですか)'. 'Sumimasen' (すみません) wird verwendet, um höflich die Aufmerksamkeit zu erlangen.",
        "fb": {
            "Ikura (いくら) asks for price. You are asking 'How much is the toilet?'": "Ikura (いくら) fragt nach dem Preis. Sie fragen 'Wie viel kostet die Toilette?'",
            "Correct! Doko (どこ) means 'where' and is used to ask for locations.": "Richtig! Doko (どこ) bedeutet 'wo' und wird für Ortsfragen verwendet.",
            "Nan (なん) means 'what'. This asks 'What is a toilet?'": "Nan (なん) bedeutet 'was'. Das fragt 'Was ist eine Toilette?'",
            "This is a statement ('The toilet is this way'), not a question.": "Das ist eine Aussage ('Die Toilette ist hier entlang'), keine Frage.",
        }
    },
    3412: {
        "q": "Sie sehen ein Paar Schuhe (くつ), das Ihnen gefällt. Wie fragen Sie nach dem Preis?",
        "e": "Das Wort für Schuhe ist 'kutsu' (くつ). Um nach dem Preis zu fragen, verwendet man 'ikura desu ka' (いくらですか).",
        "fb": {
            "Perfect! Kutsu (くつ) means shoes and ikura (いくら) means how much.": "Perfekt! Kutsu (くつ) bedeutet Schuhe und ikura (いくら) bedeutet wie viel.",
            "Nekutai (ネクタイ) means necktie, not shoes.": "Nekutai (ネクタイ) bedeutet Krawatte, nicht Schuhe.",
            "Nangai (なんがい) asks 'what floor', which doesn't apply to the price of shoes.": "Nangai (なんがい) fragt 'welcher Stock', was nicht auf den Preis von Schuhen zutrifft.",
            "This asks 'Where are these shoes?' rather than the price.": "Das fragt 'Wo sind diese Schuhe?' statt nach dem Preis.",
        }
    },
    3413: {
        "q": "Wählen Sie die korrekte höfliche Antwort, wenn jemand fragt, wo das Büro (じむしょ) ist, und auf einen Ort weit von Ihnen beiden zeigt.",
        "e": "Kochira/Sochira/Achira/Dochira sind die höflichen Entsprechungen von Koko/Soko/Asoko/Doko. 'Achira' wird für Orte verwendet, die weit von Sprecher und Zuhörer entfernt sind.",
        "fb": {
            "Kochira (こちら) refers to a place near the speaker.": "Kochira (こちら) bezeichnet einen Ort nahe beim Sprecher.",
            "Sochira (そちら) refers to a place near the listener.": "Sochira (そちら) bezeichnet einen Ort nahe beim Zuhörer.",
            "Correct! Achira (あちら) is the polite equivalent of asoko (あそこ), referring to a place far from both people.": "Richtig! Achira (あちら) ist die höfliche Entsprechung von asoko (あそこ) für einen Ort weit von beiden.",
            "This is a question asking 'Where is it?', not an answer.": "Das ist eine Frage ('Wo ist es?'), keine Antwort.",
        }
    },
    3414: {
        "q": "Ein Kollege fragt: 'かいぎしつは なんがいですか (Kaigishitsu wa nangai desu ka)'. Was fragt er?",
        "e": "Kaigishitsu (会議室) bedeutet Konferenzraum. Nangai (何階) ist das Fragewort, um nach dem Stockwerk zu fragen.",
        "fb": {
            "The question word for 'who' is 'dare' (だれ).": "Das Fragewort für 'wer' ist 'dare' (だれ).",
            "Exactly! Nangai (なんがい) means 'what floor'.": "Genau! Nangai (なんがい) bedeutet 'welcher Stock'.",
            "While 'doko' (where) is similar, 'nangai' specifically asks for the floor number.": "Obwohl 'doko' (wo) ähnlich ist, fragt 'nangai' spezifisch nach der Stockwerknummer.",
            "The question word for 'what time' is 'nan-ji' (なんじ).": "Das Fragewort für 'wie spät' ist 'nan-ji' (なんじ).",
        },
        "opt_text": {
            "Who is in the conference room?": "Wer ist im Konferenzraum?",
            "What floor is the conference room on?": "Auf welchem Stock ist der Konferenzraum?",
            "Where is the conference room located?": "Wo befindet sich der Konferenzraum?",
            "What time is the meeting in the conference room?": "Um wie viel Uhr ist die Besprechung im Konferenzraum?",
        }
    },
    3422: {
        "q": "Vervollständigen Sie den Dialog:\nKimura: すみません、お手洗いは どこですか。(Sumimasen, otearai wa doko desu ka.)\nMitarbeiter: お手洗いは ______ です。(Otearai wa ______ desu.)\nKimura: ありがとうございます。(Arigatou gozaimasu.)",
        "e": "In diesem Kontext ist 'chika' (地下 - Untergeschoss) die logische Antwort für einen Ort innerhalb eines Gebäudes wie Kaufhaus oder Büro.",
        "fb": {
            "Sankai (さんかい) means the 3rd floor.": "Sankai (さんかい) bedeutet 3. Stock.",
            "Kaidan (かいだん) means stairs. While a location, the prompt suggests a specific floor level.": "Kaidan (かいだん) bedeutet Treppen. Obwohl ein Ort, verlangt die Frage eine bestimmte Etage.",
            "Correct! 'Chika' (地下) means basement or below ground level.": "Richtig! 'Chika' (地下) bedeutet Untergeschoss.",
            "Uchi (うち) means home/house, which doesn't fit a public facility context.": "Uchi (うち) bedeutet Zuhause/Haus, was nicht zu einem öffentlichen Gebäude passt.",
        }
    },
    3433: {
        "q": "Wählen Sie die richtige Partikel für einen bestimmten Zeitpunkt:\n「わたしは　まいにち　6じ (___) おきます。」\n(Watashi wa mainichi 6-ji (...) okimasu. / Ich stehe jeden Tag um 6 Uhr auf.)",
        "e": "Die Partikel に (ni) wird nach einer bestimmten Uhrzeit verwendet, um anzuzeigen, wann eine Handlung stattfindet. 6じに おきます (roku-ji ni okimasu) bedeutet 'um 6 Uhr aufstehen'.",
        "fb": {
            "Correct! に (ni) is the particle used to indicate the specific time an action happens.": "Richtig! に (ni) ist die Partikel, die den genauen Zeitpunkt einer Handlung angibt.",
            "Incorrect. を (wo) is used for direct objects, not for time points.": "Falsch. を (wo) wird für direkte Objekte verwendet, nicht für Zeitpunkte.",
            "Incorrect. は (wa) is the topic marker. While '6-ji wa' could be used in specific contexts for contrast, 'ni' is the standard particle for 'at a specific time'.": "Falsch. は (wa) ist der Themenmarker. Obwohl '6-ji wa' in bestimmten Kontexten verwendet werden könnte, ist 'ni' die Standardpartikel für 'zu einer bestimmten Zeit'.",
            "Incorrect. も (mo) means 'also' or 'too'.": "Falsch. も (mo) bedeutet 'auch'.",
        }
    },
    3446: {
        "q": "Wählen Sie die richtige Verbform für diesen Dialog über gestern:\nTanaka: 'Kinou (Gestern) benkyou shimashita ka?'\nSato: 'Iie, ___________.'",
        "e": "Wenn man eine Frage in der Vergangenheit (~mashita ka) mit 'Nein' beantwortet, muss das Verb in der vergangenen Verneinungsform konjugiert werden: ~masen deshita (~ませんでした).",
        "fb": {
            "This is the non-past negative (present/future). You need the past negative form.": "Das ist die Gegenwarts-/Zukunftsverneinung. Man braucht die vergangene Verneinungsform.",
            "This is the past affirmative. Since Sato said 'Iie' (No), a negative form is required.": "Das ist die vergangene Bejahung. Da Sato 'Iie' (Nein) sagte, ist eine Verneinungsform nötig.",
            "Correct! ~Masen deshita (~ませんでした) is the polite past negative form.": "Richtig! ~Masen deshita (~ませんでした) ist die höfliche vergangene Verneinungsform.",
            "This is the polite present/future form. It does not match the past context or the 'No' response.": "Das ist die höfliche Gegenwarts-/Zukunftsform. Passt nicht zum Vergangenheitskontext.",
        }
    },
    3448: {
        "q": "Lesen Sie die Situation und wählen Sie die beste Gesprächsantwort:\nA: 'Mori-san wa maiasa yo-ji ni okimasu. Juu-ji ni nemasu. Mainichi hatarakimasu.'\nB: '___________'",
        "e": "Taihen desu ne (たいへんですね) ist der Standardausdruck, um Mitgefühl zu zeigen, wenn jemand eine schwierige Situation beschreibt.",
        "fb": {
            "While this means 'I see' or 'That's right', it's a bit too neutral for such an intense schedule.": "Das bedeutet zwar 'Ach so', ist aber etwas zu neutral für so einen intensiven Zeitplan.",
            "Correct! This phrase is used to show sympathy when someone has a difficult or busy situation.": "Richtig! Dieser Ausdruck zeigt Mitgefühl bei einer schwierigen oder geschäftigen Situation.",
            "This means 'Please' and is used for requests, not as a reaction to a schedule.": "Das bedeutet 'Bitte' und wird für Bitten verwendet, nicht als Reaktion auf einen Zeitplan.",
            "This means 'Good night'. It doesn't fit as a reaction to hearing someone's daily routine.": "Das bedeutet 'Gute Nacht'. Passt nicht als Reaktion auf den Tagesablauf einer Person.",
        }
    },
}

app = create_app()
with app.app_context():
    for qid, fix in FIXES.items():
        q = db.session.get(QuizQuestion, qid)
        if not q:
            print(f"Q {qid} nicht gefunden")
            continue
        q.question_text = fix["q"]
        q.explanation = fix["e"]

        opts = QuizOption.query.filter_by(question_id=qid).all()
        for o in opts:
            # Fix feedback
            if o.feedback and o.feedback in fix.get("fb", {}):
                o.feedback = fix["fb"][o.feedback]
            # Fix option text (for English-text options)
            if o.option_text and o.option_text in fix.get("opt_text", {}):
                o.option_text = fix["opt_text"][o.option_text]

        print(f"Q {qid} uebersetzt: {fix['q'][:60]}...")

    db.session.commit()
    print("\nAlle Fixes angewendet!")

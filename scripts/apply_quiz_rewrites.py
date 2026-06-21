"""Wendet die 3 Quiz-Umbauten aus dem Audit an (L153 Dakuten-Vorgriff, L176 x2).

Aendert nur question_text/explanation/option_text; is_correct bleibt (die jeweils
richtige Option behaelt ihre Position). Jedes UPDATE gegen den Ist-Wert (WHERE)
abgesichert; Commit nur bei exakt 20 Zeilen (4 Fragen + 16 Optionen).
"""
from app import create_app, db
from sqlalchemy import text

QUESTIONS = [
    (3622,
     "Wie liest man das Wort 「ラジオ」?",
     "Wie liest man das Wort 「レストラン」?",
     "「レ」 (re) + 「ス」 (su) + 「ト」 (to) + 「ラ」 (ra) + 「ン」 (n) = **resutoran** — Restaurant. "
     "Alle Zeichen sind dakuten-freie Grundzeichen aus Katakana 1–3."),
    (3628,
     "Wie liest man 「ヨガ」?",
     "Wie liest man das Wort 「カメラ」?",
     "「カ」 (ka) + 「メ」 (me) + 「ラ」 (ra) = **kamera** — Kamera. "
     "Alle Zeichen sind Grundzeichen aus Katakana 1–3 (kein Dakuten)."),
    (3965,
     "Welche Form benutzt du gegenüber deinem Chef abends beim Verlassen des Büros?",
     "Welcher Gruss passt zum Schlafengehen am Abend (zu Hause)?",
     "「おやすみなさい」 (Oyasumi nasai — Gute Nacht) sagt man abends vor dem Schlafengehen. "
     "「ただいま」 = „Ich bin zurück\", 「おかえりなさい」 = „Willkommen zurück\", "
     "「いってきます」 = „Ich gehe dann mal\" — alle für andere Situationen."),
    (3951,
     "Warum nutzt Yuki gegenüber Mama 「おはよう」 (kurz), aber gegenüber dem Vater abends 「おやすみなさい」 (lang)?",
     "Wie begrüsst du morgens höflich (z.B. eine Lehrerin oder deinen Chef)?",
     "「おはようございます」 ist die höfliche Morgenbegrüssung. 「おはよう」 ist die lockere Form "
     "(Familie/Freunde). 「こんにちは」 = Guten Tag, 「こんばんは」 = Guten Abend."),
]

OPTIONS = [
    # L153 Q3622
    (12953, "rajio", "resutoran"),
    (12954, "rashio", "resutaran"),
    (12955, "ranio", "resotoran"),
    (12956, "rasio", "retsuturan"),
    # L153 Q3628
    (12973, "yoga", "kamera"),
    (12974, "yoka", "kamira"),
    (12975, "yogi", "kanera"),
    (12976, "raga", "kamora"),
    # L176 Q3965
    (14167, "おさきに しつれいします。 (Osaki ni shitsurei shimasu.)", "おやすみなさい。 (Oyasumi nasai.)"),
    (14168, "おやすみなさい。 (Oyasumi nasai.)", "ただいま。 (Tadaima.)"),
    (14169, "ただいま。 (Tadaima.)", "おかえりなさい。 (Okaeri nasai.)"),
    (14170, "おかえりなさい。 (Okaeri nasai.)", "いってきます。 (Ittekimasu.)"),
    # L176 Q3951
    (14117, "Höherer Respekt gegenüber dem Vater (Familienoberhaupt)", "おはようございます。 (Ohayou gozaimasu.)"),
    (14118, "Weil es Abend ist und nicht Morgen", "おはよう。 (Ohayou.)"),
    (14119, "Weil Yuki müde ist", "こんにちは。 (Konnichiwa.)"),
    (14120, "Weil おはよう (ohayou) keine höfliche Form hat", "こんばんは。 (Konbanwa.)"),
]

app = create_app()
with app.app_context():
    n = 0
    for qid, oqt, nqt, nexpl in QUESTIONS:
        r = db.session.execute(text(
            "UPDATE quiz_question SET question_text=:nqt, explanation=:ne "
            "WHERE id=:i AND question_text=:oqt"),
            {"nqt": nqt, "ne": nexpl, "i": qid, "oqt": oqt})
        print("Q", qid, "rows", r.rowcount)
        n += r.rowcount
    for oid, oold, onew in OPTIONS:
        r = db.session.execute(text(
            "UPDATE quiz_option SET option_text=:n WHERE id=:i AND option_text=:o"),
            {"n": onew, "i": oid, "o": oold})
        print("O", oid, "rows", r.rowcount)
        n += r.rowcount
    if n == 20:
        db.session.commit()
        print("COMMIT ok, updates =", n)
    else:
        db.session.rollback()
        print("ROLLBACK — erwartet 20, war", n)

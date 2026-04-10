#!/usr/bin/env python3
"""
Kopiert alle MNN Beginner I Lektionen und übersetzt sie ins Deutsche.
Einmalig ausführen: python scripts/translate_lessons_to_german.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    Lesson, LessonContent, LessonPage, LessonCategory,
    QuizQuestion, QuizOption
)
import json
from copy import deepcopy

# ── Übersetzungen: Lektions-Titel ────────────────────────────────────
LESSON_TITLES = {
    131: "MNN L1: Lektion 1 – Selbstvorstellung",
    132: "MNN L2: Lektion 2 – Demonstrativpronomen",
    133: "MNN L3: Lektion 3 – Orte und Preise",
    134: "MNN L4: Lektion 4 – Uhrzeit und Tagesablauf",
    135: "MNN L5: Lektion 5 – Gehen und Kommen",
}

# ── Übersetzungen: Seiten-Titel ──────────────────────────────────────
PAGE_TITLES = {
    "Vocabulary": "Vokabeln",
    "Grammar": "Grammatik",
    "Conversation": "Konversation",
    "Practice": "Übungen",
    "Test": "Test",
}

# ── Übersetzungen: Content-Titel ─────────────────────────────────────
CONTENT_TITLES = {
    # Text titles
    "Lesson 1 — Vocabulary": "Lektion 1 — Vokabeln",
    "Lesson 1 — Grammar": "Lektion 1 — Grammatik",
    "Lesson 2 — Vocabulary": "Lektion 2 — Vokabeln",
    "Lesson 2 — Grammar": "Lektion 2 — Grammatik",
    "Lesson 3 — Vocabulary": "Lektion 3 — Vokabeln",
    "Lesson 3 — Grammar": "Lektion 3 — Grammatik",
    "Lesson 4 — Vocabulary": "Lektion 4 — Vokabeln",
    "Lesson 4 — Grammar": "Lektion 4 — Grammatik",
    "Lesson 5 — Vocabulary": "Lektion 5 — Vokabeln",
    "Lesson 5 — Grammar": "Lektion 5 — Grammatik",
    # Audio titles (already German)
    "Vokabeln (Audio)": "Vokabeln (Audio)",
    "Beispielsätze (Audio)": "Beispielsätze (Audio)",
    "Satzmuster (Audio)": "Satzmuster (Audio)",
    "Konversation (Audio)": "Konversation (Audio)",
    "Übung (Audio)": "Übung (Audio)",
    "Test (Audio)": "Test (Audio)",
    # Conversation text titles
    "How do you do? -- はじめまして": "Wie geht es Ihnen? -- はじめまして",
    "This is my book -- これはわたしのほんです": "Das ist mein Buch -- これはわたしのほんです",
    "Where is the elevator? -- エレベーターはどこですか": "Wo ist der Aufzug? -- エレベーターはどこですか",
    "Telephone number is? -- でんわばんごうは？": "Wie ist die Telefonnummer? -- でんわばんごうは？",
    # Practice titles (already German)
    "Übungen (Renshuu)": "Übungen (Renshuu)",
    # Image
    "test": "test",
}

# ── Übersetzungen: Text-Body ─────────────────────────────────────────
TEXT_BODIES = {
    "Vokabeln aus Minna No Nihongo Beginner I, Lektion 1.":
        "Vokabeln aus Minna No Nihongo Beginner I, Lektion 1.",
    "Grammatik aus Minna No Nihongo Beginner I, Lektion 1.":
        "Grammatik aus Minna No Nihongo Beginner I, Lektion 1.",
    "Vokabeln aus Minna No Nihongo Beginner I, Lektion 2.":
        "Vokabeln aus Minna No Nihongo Beginner I, Lektion 2.",
    "Grammatik aus Minna No Nihongo Beginner I, Lektion 2.":
        "Grammatik aus Minna No Nihongo Beginner I, Lektion 2.",
    "Vokabeln aus Minna No Nihongo Beginner I, Lektion 3.":
        "Vokabeln aus Minna No Nihongo Beginner I, Lektion 3.",
    "Grammatik aus Minna No Nihongo Beginner I, Lektion 3.":
        "Grammatik aus Minna No Nihongo Beginner I, Lektion 3.",
    "Vokabeln aus Minna No Nihongo Beginner I, Lektion 4.":
        "Vokabeln aus Minna No Nihongo Beginner I, Lektion 4.",
    "Grammatik aus Minna No Nihongo Beginner I, Lektion 4.":
        "Grammatik aus Minna No Nihongo Beginner I, Lektion 4.",
    "Vokabeln aus Minna No Nihongo Beginner I, Lektion 5.":
        "Vokabeln aus Minna No Nihongo Beginner I, Lektion 5.",
    "Grammatik aus Minna No Nihongo Beginner I, Lektion 5.":
        "Grammatik aus Minna No Nihongo Beginner I, Lektion 5.",
    "Höre die Übungen und sprich nach. Die Übungen C1–C3 trainieren die Satzmuster aus dieser Lektion.":
        "Höre die Übungen und sprich nach. Die Übungen C1–C3 trainieren die Satzmuster aus dieser Lektion.",
}

# ── Quiz-Übersetzungen nach Lektion ─────────────────────────────────
# Format: { original_question_text: { "q": deutsch, "e": deutsch, "options": {orig_feedback: deutsch} } }
# Japanische Begriffe (Kana, Kanji, Romaji) bleiben unverändert.
# True/False-Optionen: "True" → "Wahr", "False" → "Falsch"

QUIZ_TRANSLATIONS = {}

# ═══════════════════════════════════════════════════════════════════════
# LEKTION 1 – Selbstvorstellung
# ═══════════════════════════════════════════════════════════════════════

QUIZ_TRANSLATIONS["When you are a regular employee of a company and want to state your general occupation, which Japanese term is used?"] = {
    "q": "Wenn Sie regulärer Angestellter einer Firma sind und Ihren allgemeinen Beruf angeben möchten, welcher japanische Begriff wird verwendet?",
    "e": "In Lektion 1 wird かいしゃいん (kaishain) für einen allgemeinen Firmenangestellten verwendet. Wenn Sie sich als Mitarbeiter einer bestimmten Firma vorstellen, verwenden Sie しゃいん (shain) nach dem Firmennamen, z.B. IMCのしゃいん (IMC no shain).",
    "fb": {
        "Incorrect. せんせい (sensei) is used for teachers or instructors.": "Falsch. せんせい (sensei) wird für Lehrer oder Dozenten verwendet.",
        "Incorrect. がくせい (gakusei) refers to a student.": "Falsch. がくせい (gakusei) bezeichnet einen Studenten.",
        "Correct! かいしゃいん (kaishain) is the general term for a company employee.": "Richtig! かいしゃいん (kaishain) ist der allgemeine Begriff für einen Firmenangestellten.",
        "Incorrect. いしゃ (isha) refers to a medical doctor.": "Falsch. いしゃ (isha) bezeichnet einen Arzt.",
    }
}

QUIZ_TRANSLATIONS["During a first meeting, which phrase is used politely to preface an inquiry about someone's name, meaning 'Excuse me, but...'?"] = {
    "q": "Bei einer ersten Begegnung, welcher Ausdruck wird höflich vorangestellt, um nach dem Namen zu fragen (Bedeutung: 'Entschuldigen Sie, aber...')?",
    "e": "しつれいですが (shitsurei desu ga) ist ein wichtiges Höflichkeitselement im Japanischen, das vor persönlichen Fragen verwendet wird. Es folgt typischerweise おなまえは？ (o-namae wa? - Wie heissen Sie?).",
    "fb": {
        "Incorrect. はじめまして (hajimemashite) means 'How do you do?' and is used at the very beginning of an introduction.": "Falsch. はじめまして (hajimemashite) bedeutet 'Freut mich' und wird ganz am Anfang einer Vorstellung verwendet.",
        "Correct! しつれいですが (shitsurei desu ga) is a polite way to preface an inquiry like asking for a name.": "Richtig! しつれいですが (shitsurei desu ga) ist eine höfliche Einleitung für Fragen wie die nach dem Namen.",
        "Incorrect. どうぞよろしく (douzo yoroshiku) means 'Pleased to meet you' and is said at the end of the introduction.": "Falsch. どうぞよろしく (douzo yoroshiku) bedeutet 'Freut mich, Sie kennenzulernen' und wird am Ende der Vorstellung gesagt.",
        "Incorrect. はい (hai) simply means 'yes'.": "Falsch. はい (hai) bedeutet einfach 'ja'.",
    }
}

QUIZ_TRANSLATIONS["Which word is the more polite, respectful version of あのひと (ano hito) when referring to 'that person' or 'he/she'?"] = {
    "q": "Welches Wort ist die höflichere, respektvollere Version von あのひと (ano hito) für 'diese Person' oder 'er/sie'?",
    "e": "Im Japanischen gibt es oft formelle Entsprechungen für alltägliche Wörter, um Respekt auszudrücken. So wie あのかた (ano kata) höflicher als あのひと (ano hito) ist, ist どなた (donata) die höfliche Entsprechung von だれ (dare) für das Wort 'wer'.",
    "fb": {
        "Incorrect. あなた (anata) means 'you'.": "Falsch. あなた (anata) bedeutet 'Sie/du'.",
        "Correct! あのかた (ano kata) is the polite way to say 'that person'.": "Richtig! あのかた (ano kata) ist die höfliche Form für 'diese Person'.",
        "Incorrect. みなさん (minasan) means 'everyone' or 'all of you'.": "Falsch. みなさん (minasan) bedeutet 'alle' oder 'Sie alle'.",
        "Incorrect. だれ (dare) means 'who'.": "Falsch. だれ (dare) bedeutet 'wer'.",
    }
}

QUIZ_TRANSLATIONS["In Japanese grammar, to change the sentence 'Mirā-san wa gakusei desu' (Mr. Miller is a student) into a negative statement, you replace 'desu' (です) with 'ja arimasen' (じゃ ありません)."] = {
    "q": "In der japanischen Grammatik wird der Satz 'Mirā-san wa gakusei desu' (Herr Miller ist Student) verneint, indem man 'desu' (です) durch 'ja arimasen' (じゃ ありません) ersetzt.",
    "e": "Um einen verneinenden Satz mit einem Nomen zu bilden, wird 'desu' (です - ist) zu 'ja arimasen' (じゃ ありません - ist nicht). 'Mirā-san wa gakusei ja arimasen' (ミラーさんは がくせい じゃ ありません) bedeutet 'Herr Miller ist kein Student'.",
    "fb": {}
}

QUIZ_TRANSLATIONS["The particle 'no' (の) is used to connect two nouns, where the first noun modifies or shows possession of the second noun, such as 'IMC no shain' (an employee of IMC)."] = {
    "q": "Die Partikel 'no' (の) verbindet zwei Nomen, wobei das erste Nomen das zweite näher bestimmt oder Besitz anzeigt, z.B. 'IMC no shain' (ein Angestellter von IMC).",
    "e": "Die Partikel 'no' (の) funktioniert wie das deutsche 'von' oder der Genitiv. Im Ausdruck 'IMC no shain' (IMC の しゃいん) ist 'IMC' die Organisation und 'shain' (しゃいん) der Angestellte — die Person gehört zu dieser Firma.",
    "fb": {}
}

QUIZ_TRANSLATIONS["""Look at the following conversation:

Person A: 'Satō-san wa kaishain desu.' (Ms. Sato is a company employee.)
Person B: 'Mirā-san ___ kaishain desu.' (Mr. Miller is also a company employee.)

Which particle correctly fills the blank to express 'also' or 'too'?"""] = {
    "q": """Betrachten Sie das folgende Gespräch:

Person A: 'Satō-san wa kaishain desu.' (Frau Sato ist Firmenangestellte.)
Person B: 'Mirā-san ___ kaishain desu.' (Herr Miller ist auch Firmenangestellter.)

Welche Partikel füllt die Lücke korrekt, um 'auch' auszudrücken?""",
    "e": "Im Japanischen ersetzt die Partikel 'mo' (も) die Partikel 'wa' (は), wenn man sagen möchte, dass ein Subjekt dieselbe Eigenschaft wie ein zuvor genanntes teilt. 'Mirā-san mo kaishain desu' (ミラーさんも かいしゃいん です) bedeutet 'Herr Miller ist auch Firmenangestellter'.",
    "fb": {
        "'Wa' (は) is the topic particle, but here we need to indicate that Mr. Miller is ALSO an employee like Ms. Sato.": "'Wa' (は) ist die Themenpartikel, aber hier müssen wir ausdrücken, dass Herr Miller AUCH Angestellter ist wie Frau Sato.",
        "'Ka' (か) is used at the end of a sentence to turn it into a question.": "'Ka' (か) wird am Satzende verwendet, um eine Frage zu bilden.",
        "Correct! 'Mo' (も) is used when the predicate is the same as the previous sentence, meaning 'also' or 'too'.": "Richtig! 'Mo' (も) wird verwendet, wenn das Prädikat gleich ist wie im vorherigen Satz — Bedeutung: 'auch'.",
        "'No' (の) is used to connect two nouns to show possession or affiliation.": "'No' (の) wird verwendet, um zwei Nomen zu verbinden und Besitz oder Zugehörigkeit anzuzeigen.",
    }
}

QUIZ_TRANSLATIONS["In the dialogue, when Mr. Miller is introduced to Ms. Sato (Satou), which phrase does he use first to signify 'How do you do?'"] = {
    "q": "Im Dialog, als Herr Miller Frau Sato (Satou) vorgestellt wird, welchen Ausdruck verwendet er zuerst für 'Freut mich, Sie kennenzulernen'?",
    "e": "Bei einer japanischen Selbstvorstellung ist die Reihenfolge sehr formell. Man beginnt mit 'Hajimemashite' (はじめまして - Freut mich), gefolgt vom Namen und Informationen, und schliesst mit 'Douzo yoroshiku onegaishimasu' (どうぞ よろしく おねがいします - Bitte behandeln Sie mich gut). Herr Miller folgt diesem Muster, nachdem er von Herrn Yamada vorgestellt wurde.",
    "fb": {
        "Ohayou gozaimasu (おはようございます) means 'Good morning'. It is a general morning greeting, not the specific phrase for starting a first-time introduction.": "Ohayou gozaimasu (おはようございます) bedeutet 'Guten Morgen'. Es ist ein allgemeiner Morgengruss, nicht der spezifische Ausdruck für den Beginn einer Erstvorstellung.",
        "Correct! Hajimemashite (はじめまして) is derived from the word meaning 'to begin' and is the standard way to say 'How do you do?' when meeting someone for the first time.": "Richtig! Hajimemashite (はじめまして) leitet sich vom Wort für 'beginnen' ab und ist die Standardformel bei der ersten Begegnung.",
        "This means 'Nice to meet you' or 'Please be kind to me'. While important, it is used at the end of the introduction to close the greeting, not as the opening 'How do you do?'.": "Das bedeutet 'Freut mich' oder 'Bitte seien Sie gut zu mir'. Obwohl wichtig, wird es am Ende der Vorstellung verwendet, nicht als Eröffnung.",
        "This phrase means 'This is Mr. Miller'. This is what Mr. Yamada (Yamada-san) says to introduce Mr. Miller to Ms. Sato (Satou-san).": "Dieser Ausdruck bedeutet 'Das ist Herr Miller'. So stellt Herr Yamada (Yamada-san) Herrn Miller Frau Sato (Satou-san) vor.",
    }
}

QUIZ_TRANSLATIONS["Choose the correct word to complete the sentence: 'Tanaka-san wa [ ] desu.' (Mr. Tanaka is a medical doctor.)"] = {
    "q": "Wählen Sie das richtige Wort: 'Tanaka-san wa [ ] desu.' (Herr Tanaka ist Arzt.)",
    "e": "In Lektion 1 ist いしゃ (isha) das Vokabelwort für Arzt. Tanaka-san wa isha desu (Herr Tanaka ist Arzt).",
    "fb": {
        "Correct! いしゃ (isha) means medical doctor.": "Richtig! いしゃ (isha) bedeutet Arzt.",
        "Incorrect. ぎんこういん (ginkouin) means bank employee.": "Falsch. ぎんこういん (ginkouin) bedeutet Bankangestellter.",
        "Incorrect. きょうし (kyoushi) means teacher/instructor.": "Falsch. きょうし (kyoushi) bedeutet Lehrer/Dozent.",
        "Incorrect. エンジニア (enjinia) means engineer.": "Falsch. エンジニア (enjinia) bedeutet Ingenieur.",
    }
}

QUIZ_TRANSLATIONS["If Miller-san is a student and you are also a student, which particle should you use? 'Miraa-san wa gakusei desu. Watashi [ ] gakusei desu.'"] = {
    "q": "Wenn Miller-san Student ist und Sie auch Student sind, welche Partikel verwenden Sie? 'Miraa-san wa gakusei desu. Watashi [ ] gakusei desu.'",
    "e": "Die Partikel も (mo) ersetzt は (wa), wenn man 'auch' sagen möchte. Watashi mo gakusei desu (Ich bin auch Student).",
    "fb": {
        "Incorrect. は (wa) is the general topic particle, but there is a more specific one for 'also'.": "Falsch. は (wa) ist die allgemeine Themenpartikel, aber es gibt eine spezifischere für 'auch'.",
        "Incorrect. の (no) is used for possession or connection.": "Falsch. の (no) wird für Besitz oder Verbindung verwendet.",
        "Correct! も (mo) is used when the same thing applies to a second subject, meaning 'also' or 'too'.": "Richtig! も (mo) wird verwendet, wenn dasselbe für ein zweites Subjekt gilt — Bedeutung: 'auch'.",
        "Incorrect. か (ka) is the question particle.": "Falsch. か (ka) ist die Fragepartikel.",
    }
}

QUIZ_TRANSLATIONS["Which of the following is the polite way to say 'I am NOT a researcher'?"] = {
    "q": "Welche der folgenden Möglichkeiten ist die höfliche Form für 'Ich bin KEIN Forscher'?",
    "e": "Um in Lektion 1 einen verneinenden Satz zu bilden, ersetzen Sie です (desu) durch じゃ ありません (ja arimasen). Kenkyuusha (Forscher) ja arimasen (ist nicht).",
    "fb": {
        "Incorrect. This means 'I AM a researcher'.": "Falsch. Das bedeutet 'Ich BIN Forscher'.",
        "Correct! じゃ ありません (ja arimasen) is the negative form of です (desu).": "Richtig! じゃ ありません (ja arimasen) ist die Verneinungsform von です (desu).",
        "Incorrect. This sounds like an incomplete question.": "Falsch. Das klingt wie eine unvollständige Frage.",
        "Incorrect. The particle の (no) is not used this way for negation.": "Falsch. Die Partikel の (no) wird nicht so für die Verneinung verwendet.",
    }
}

QUIZ_TRANSLATIONS["When introducing yourself, which of these is considered grammatically and socially CORRECT in Japanese?"] = {
    "q": "Bei der Selbstvorstellung, welche Variante gilt als grammatisch und sozial KORREKT im Japanischen?",
    "e": "Im Japanischen ist das Suffix ～さん (-san) ein Höflichkeitstitel für andere. Es für sich selbst zu verwenden gilt als seltsam oder arrogant. Sagen Sie einfach '[Name] desu'.",
    "fb": {
        "Incorrect. You should never add ～さん (-san) to your own name.": "Falsch. Man fügt niemals ～さん (-san) an den eigenen Namen an.",
        "Correct! You state your name without ～さん (-san) when referring to yourself.": "Richtig! Man nennt seinen Namen ohne ～さん (-san), wenn man sich selbst vorstellt.",
        "Incorrect. This means 'You are Miller', not an introduction of yourself.": "Falsch. Das bedeutet 'Sie sind Miller', keine Selbstvorstellung.",
        "Incorrect. This structure is grammatically incorrect for a self-introduction.": "Falsch. Diese Struktur ist grammatisch falsch für eine Selbstvorstellung.",
    }
}

QUIZ_TRANSLATIONS["Which phrase is used at the very BEGINNING of a self-introduction, before you say your name?"] = {
    "q": "Welcher Ausdruck wird ganz am ANFANG einer Selbstvorstellung verwendet, bevor man seinen Namen sagt?",
    "e": "Eine Standardvorstellung folgt dem Ablauf: はじめまして (Hajimemashite) → Name + desu → どうぞ よろしく (Douzo yoroshiku).",
    "fb": {
        "Incorrect. This is used at the END of an introduction.": "Falsch. Das wird am ENDE einer Vorstellung verwendet.",
        "Correct! はじめまして (Hajimemashite) is the standard way to start an introduction.": "Richtig! はじめまして (Hajimemashite) ist die Standardformel zum Beginn einer Vorstellung.",
        "Incorrect. This is used to politely interrupt or ask a personal question.": "Falsch. Das wird verwendet, um höflich zu unterbrechen oder eine persönliche Frage zu stellen.",
        "Incorrect. This means 'What is your name?' and is not how you start your own introduction.": "Falsch. Das bedeutet 'Wie heissen Sie?' und ist nicht der Beginn einer Selbstvorstellung.",
    }
}

QUIZ_TRANSLATIONS["The phrase 'IMC の しゃいん' (IMC no shain) translates to 'an employee of IMC'."] = {
    "q": "Der Ausdruck 'IMC の しゃいん' (IMC no shain) bedeutet 'ein Angestellter von IMC'.",
    "e": "Richtig. Die Partikel の (no) verbindet zwei Nomen, wobei N1 (IMC) N2 (shain/Angestellter) näher bestimmt oder besitzt. IMC no shain bedeutet ein Angestellter, der zu IMC gehört.",
    "fb": {}
}

QUIZ_TRANSLATIONS["In polite conversation, you should use 'だれ' (dare) instead of 'どなた' (donata) when asking for someone's name."] = {
    "q": "In höflicher Konversation sollte man 'だれ' (dare) statt 'どなた' (donata) verwenden, wenn man nach jemandes Namen fragt.",
    "e": "Falsch. どなた (donata) ist die höfliche Version von だれ (dare). Im Kontext von Minna no Nihongo Lektion 1 wird どなた (donata) für höfliche soziale Situationen bevorzugt.",
    "fb": {}
}

QUIZ_TRANSLATIONS["The phrase 'しつれいですが' (shitsurei desu ga) is used when you are about to ask someone for personal information, such as their name or address."] = {
    "q": "Der Ausdruck 'しつれいですが' (shitsurei desu ga) wird verwendet, wenn man jemanden nach persönlichen Informationen wie Name oder Adresse fragen möchte.",
    "e": "Richtig. しつれいですが (shitsurei desu ga) bedeutet 'Entschuldigen Sie, aber...' und wird verwendet, um die Wirkung einer persönlichen Frage abzumildern, wie おなまえは？ (O-namae wa? - Wie heissen Sie?).",
    "fb": {}
}

QUIZ_TRANSLATIONS["Match the Japanese vocabulary words with their correct English meanings."] = {
    "q": "Ordnen Sie die japanischen Vokabeln den richtigen deutschen Bedeutungen zu.",
    "e": "わたしたち (watashitachi) bedeutet 'wir' (Plural von ich). だいがく (daigaku) ist Universität. なんさい (nansai) ist das Fragewort für das Alter. びょういん (byouin) ist ein Krankenhaus.",
    "fb": {
        "we": "wir",
        "university": "Universität",
        "how old": "wie alt",
        "hospital": "Krankenhaus",
    }
}

QUIZ_TRANSLATIONS["""Choose the correct ending for a negative sentence. 'Mr. Miller is NOT a doctor.'
ミラーさんは いしゃ (__________)。"""] = {
    "q": """Wählen Sie die richtige Endung für einen verneinenden Satz. 'Herr Miller ist KEIN Arzt.'
ミラーさんは いしゃ (__________)。""",
    "e": "Um einen verneinenden Satz zu bilden (N1 wa N2...), ersetzen Sie 'desu' (です - ist) durch 'ja arimasen' (じゃ ありません - ist nicht). 'Miraa-san wa isha ja arimasen' (ミラーさんは いしゃ じゃ ありません) bedeutet 'Herr Miller ist kein Arzt.'",
    "fb": {
        "This is the affirmative form ('is'). We need the negative form ('is not').": "Das ist die bejahende Form ('ist'). Wir brauchen die verneinende Form ('ist nicht').",
        "Correct! 'Ja arimasen' (じゃ ありません) is the negative form of 'desu' (です).": "Richtig! 'Ja arimasen' (じゃ ありません) ist die Verneinungsform von 'desu' (です).",
        "'Ka' (か) is the question particle, not a negative marker.": "'Ka' (か) ist die Fragepartikel, kein Verneinungsmarker.",
        "'No' (の) is a possessive/modifying particle.": "'No' (の) ist eine Besitz-/Bestimmungspartikel.",
    }
}

QUIZ_TRANSLATIONS["""Which particle correctly connects a company name to an employee's title?
ミラーさんは IMC (__________) しゃいんです。"""] = {
    "q": """Welche Partikel verbindet den Firmennamen mit der Berufsbezeichnung?
ミラーさんは IMC (__________) しゃいんです。""",
    "e": "Die Partikel 'no' (の) verbindet zwei Nomen (N1 no N2). Bei der Beschreibung des Arbeitsplatzes sagt man '[Firma] no [Angestellter/Titel]'. 'IMC no shain' (IMCのしゃいん) bedeutet 'ein Angestellter von IMC'.",
    "fb": {
        "The topic particle 'wa' (は) already appears after Miller.": "Die Themenpartikel 'wa' (は) steht bereits nach Miller.",
        "'Mo' (も) means 'also/too'. It doesn't connect the company to the employee title.": "'Mo' (も) bedeutet 'auch'. Es verbindet nicht den Firmennamen mit der Berufsbezeichnung.",
        "Exactly! 'No' (の) connects two nouns, showing that Miller is an employee *of* IMC.": "Genau! 'No' (の) verbindet zwei Nomen und zeigt, dass Miller Angestellter *von* IMC ist.",
        "'Desu' (です) belongs at the end of the sentence.": "'Desu' (です) gehört ans Satzende.",
    }
}

QUIZ_TRANSLATIONS["""Select the pair that completes the most polite version of 'Who is that person?'
(__________) は (__________) ですか。"""] = {
    "q": """Wählen Sie das Paar, das die höflichste Version von 'Wer ist diese Person?' vervollständigt.
(__________) は (__________) ですか。""",
    "e": "In Lektion 1 lernen wir, dass 'ano kata' (あのかた) die höfliche Version von 'ano hito' (あのひと - diese Person) ist, und 'donata' (どなた) die höfliche Version von 'dare' (だれ - wer). Beide zusammen ergeben ein einheitliches Höflichkeitsniveau.",
    "fb": {
        "While grammatically correct, this is the standard/plain form, not the most polite version.": "Zwar grammatisch korrekt, aber dies ist die Standard-/einfache Form, nicht die höflichste Version.",
        "Correct! Both 'ano kata' (あのかた) and 'donata' (どなた) are the polite equivalents of 'ano hito' and 'dare'.": "Richtig! Sowohl 'ano kata' (あのかた) als auch 'donata' (どなた) sind die höflichen Entsprechungen von 'ano hito' und 'dare'.",
        "Using 'anata' (you) while asking 'who' is socially awkward and rarely used this way.": "'Anata' (du/Sie) zusammen mit 'wer' zu verwenden ist sozial unpassend und wird selten so benutzt.",
        "This is inconsistent; it mixes a polite subject with a plain question word.": "Das ist inkonsistent — es mischt ein höfliches Subjekt mit einem einfachen Fragewort.",
    }
}

QUIZ_TRANSLATIONS["""Read the dialogue and fill in the blank:
A: 佐藤さんは ぎんこういんです。(Satou-san wa ginkouin desu.)
B: 山田さん (__________) ぎんこういんです。"""] = {
    "q": """Lesen Sie den Dialog und füllen Sie die Lücke:
A: 佐藤さんは ぎんこういんです。(Satou-san wa ginkouin desu.)
B: 山田さん (__________) ぎんこういんです。""",
    "e": "Die Partikel 'mo' (も) wird verwendet, wenn dasselbe für ein neues Thema gilt. Da Sato Bankangestellte ist und Yamada ebenfalls, verwenden wir 'Yamada-san mo ginkouin desu' (山田さんもぎんこういんです).",
    "fb": {
        "While grammatically possible, it doesn't emphasize that Yamada is *also* a bank employee.": "Zwar grammatisch möglich, aber es betont nicht, dass Yamada *auch* Bankangestellter ist.",
        "Perfect! 'Mo' (も) replaces 'wa' (は) to indicate 'also' or 'too'.": "Perfekt! 'Mo' (も) ersetzt 'wa' (は), um 'auch' auszudrücken.",
        "'No' (の) would imply Yamada 'belongs' to the bank employee, which doesn't make sense here.": "'No' (の) würde bedeuten, dass Yamada dem Bankangestellten 'gehört', was hier keinen Sinn ergibt.",
        "This would change the sentence to 'is not', but particles like 'wa' or 'mo' are still needed as subjects.": "Das würde den Satz zu 'ist nicht' ändern, aber Partikel wie 'wa' oder 'mo' werden trotzdem als Themenmarker benötigt.",
    }
}

QUIZ_TRANSLATIONS["""You are a teacher at Sakura University. How should you introduce yourself?
わたしは さくらだいがくの (__________) です。"""] = {
    "q": """Sie sind Lehrer an der Sakura-Universität. Wie stellen Sie sich vor?
わたしは さくらだいがくの (__________) です。""",
    "e": "Im Japanischen ist 'sensei' (せんせい) ein Ehrentitel. Man verwendet Ehrentitel nicht für sich selbst. Stattdessen benutzt man den Berufsbegriff 'kyoushi' (きょうし), wenn man den eigenen Beruf nennt.",
    "fb": {
        "'Sensei' (せんせい) is usually used as a title for others or when addressing a teacher, not for one's own job title.": "'Sensei' (せんせい) wird normalerweise als Titel für andere verwendet oder um einen Lehrer anzusprechen, nicht als eigene Berufsbezeichnung.",
        "Correct! 'Kyoushi' (きょうし) is the word used to describe your own occupation as a teacher.": "Richtig! 'Kyoushi' (きょうし) ist das Wort, um den eigenen Beruf als Lehrer zu beschreiben.",
        "'Gakusei' (がくせい) means student, not teacher.": "'Gakusei' (がくせい) bedeutet Student, nicht Lehrer.",
        "'Kenkyuusha' (けんきゅうしゃ) means researcher. While similar, it's not the same as teacher.": "'Kenkyuusha' (けんきゅうしゃ) bedeutet Forscher. Zwar ähnlich, aber nicht dasselbe wie Lehrer.",
    }
}

QUIZ_TRANSLATIONS["In a self-introduction, it is polite and correct to say: 'Watashi wa Miraa-san desu' (わたしは ミラーさんです)."] = {
    "q": "Bei einer Selbstvorstellung ist es höflich und korrekt zu sagen: 'Watashi wa Miraa-san desu' (わたしは ミラーさんです).",
    "e": "Man fügt niemals das Höflichkeitssuffix '-san' (〜さん) an den eigenen Namen an. Es wird nur für andere verwendet. Man sagt 'Watashi wa Miraa desu' (わたしは ミラーです).",
    "fb": {}
}

QUIZ_TRANSLATIONS["The phrase 'Shitsurei desu ga, o-namae wa?' (しつれいですが、おなまえは？) is a polite way to ask for someone's name."] = {
    "q": "Der Ausdruck 'Shitsurei desu ga, o-namae wa?' (しつれいですが、おなまえは？) ist eine höfliche Art, nach jemandes Namen zu fragen.",
    "e": "'Shitsurei desu ga' (しつれいですが) bedeutet wörtlich 'Es ist unhöflich, aber...' und wird verwendet, um die Bitte abzumildern, wenn man nach persönlichen Informationen wie dem Namen fragt (O-namae wa?).",
    "fb": {}
}

QUIZ_TRANSLATIONS["If someone asks 'Anata wa gakusei desu ka?' (あなたは がくせいですか) and you are NOT a student, it is correct to respond: 'Hai, gakusei ja arimasen' (はい、がくせい じゃ ありません)."] = {
    "q": "Wenn jemand fragt 'Anata wa gakusei desu ka?' (あなたは がくせいですか) und Sie KEIN Student sind, ist die korrekte Antwort: 'Hai, gakusei ja arimasen' (はい、がくせい じゃ ありません).",
    "e": "Wenn die Aussage falsch ist, muss man mit 'Iie' (いいえ - Nein) beginnen. 'Hai' (はい) bedeutet 'Ja'. Die korrekte Antwort ist 'Iie, gakusei ja arimasen' (いいえ、がくせい じゃ ありません).",
    "fb": {}
}

QUIZ_TRANSLATIONS["Match the Japanese occupations to their English equivalents."] = {
    "q": "Ordnen Sie die japanischen Berufe ihren deutschen Entsprechungen zu.",
    "e": "Die Vokabeln für Lektion 1 umfassen verschiedene Berufe: 'ginkouin' (ぎんこういん - Bankangestellter), 'kenkyuusha' (けんきゅうしゃ - Forscher), 'kaishain' (かいしゃいん - Firmenangestellter) und 'isha' (いしゃ - Arzt).",
    "fb": {
        "Bank employee": "Bankangestellter",
        "Researcher": "Forscher",
        "Company employee": "Firmenangestellter",
        "Medical doctor": "Arzt",
    }
}

# ═══════════════════════════════════════════════════════════════════════
# LEKTION 2 – Demonstrativpronomen
# ═══════════════════════════════════════════════════════════════════════

QUIZ_TRANSLATIONS["You want to refer to a 'pocket notebook' or 'personal planner' in Japanese. Which word is correct?"] = {
    "q": "Sie möchten auf Japanisch ein 'Notizbüchlein' oder einen 'persönlichen Planer' bezeichnen. Welches Wort ist richtig?",
    "e": "In Lektion 2 unterscheiden wir verschiedene Schreibwaren. てちょう (techou) ist ein Taschenplaner, während ノート (nooto) ein normales Notizbuch ist, めいし (meishi) eine Visitenkarte und じしょ (jisho) ein Wörterbuch.",
    "fb": {
        "Close! ノート (nooto) refers to a standard notebook, usually for school or general notes.": "Fast! ノート (nooto) bezeichnet ein normales Notizbuch, meist für Schule oder allgemeine Notizen.",
        "Correct! てちょう (techou) specifically refers to a pocket-sized notebook or personal planner.": "Richtig! てちょう (techou) bezeichnet speziell ein Taschennotizbuch oder einen persönlichen Planer.",
        "めいし (meishi) means 'business card'.": "めいし (meishi) bedeutet 'Visitenkarte'.",
        "じしょ (jisho) means 'dictionary'.": "じしょ (jisho) bedeutet 'Wörterbuch'.",
    }
}

QUIZ_TRANSLATIONS["How do you correctly say 'this bag' in Japanese when the bag is right next to you?"] = {
    "q": "Wie sagt man korrekt 'diese Tasche' auf Japanisch, wenn die Tasche direkt neben Ihnen liegt?",
    "e": "Im Japanischen stehen Pronomen wie これ (kore), それ (sore) und あれ (are) allein als Subjekt. Um ein bestimmtes Nomen zu bestimmen, muss man die vorangestellten Formen verwenden: この (kono), その (sono) und あの (ano). Also ist 'diese Tasche' = この かばん (kono kaban).",
    "fb": {
        "Incorrect. これ (kore) is a pronoun and cannot be followed directly by a noun.": "Falsch. これ (kore) ist ein Pronomen und kann nicht direkt von einem Nomen gefolgt werden.",
        "Incorrect. それ (sore) is used for objects near the listener, and it cannot be followed directly by a noun.": "Falsch. それ (sore) wird für Objekte beim Zuhörer verwendet und kann nicht direkt von einem Nomen gefolgt werden.",
        "Correct! この (kono) is used to modify a noun (bag) that is close to the speaker.": "Richtig! この (kono) wird verwendet, um ein Nomen (Tasche) in der Nähe des Sprechers zu bestimmen.",
        "その (sono) refers to a bag near the listener, not near the speaker ('this bag').": "その (sono) bezieht sich auf eine Tasche beim Zuhörer, nicht beim Sprecher ('diese Tasche').",
    }
}

QUIZ_TRANSLATIONS["You are handing a gift (omiyage) to someone. Which phrase should you use while offering it?"] = {
    "q": "Sie überreichen jemandem ein Geschenk (omiyage). Welchen Ausdruck verwenden Sie dabei?",
    "e": "Beim Überreichen eines おみやげ (omiyage - Mitbringsel) ist es höflich, どうぞ (douzo) zu sagen, was 'Bitte schön' oder 'Hier, bitte' bedeutet. Der Empfänger antwortet dann mit どうも (doumo) oder ありがとう (arigatou).",
    "fb": {
        "Correct! どうぞ (douzo) is used when offering something, meaning 'Please' or 'Here you go'.": "Richtig! どうぞ (douzo) wird beim Anbieten verwendet — Bedeutung: 'Bitte schön' oder 'Hier, bitte'.",
        "どうも (doumo) is a casual way to say 'Thanks', usually used by the person receiving the gift.": "どうも (doumo) ist eine lockere Art 'Danke' zu sagen, meist vom Empfänger des Geschenks verwendet.",
        "ちがいます (chigaimasu) means 'No, that's wrong' or 'It's different'.": "ちがいます (chigaimasu) bedeutet 'Nein, das ist falsch' oder 'Das ist anders'.",
        "そうですか (sou desu ka) means 'I see' or 'Is that so?'": "そうですか (sou desu ka) bedeutet 'Ach so' oder 'Ist das so?'",
    }
}

QUIZ_TRANSLATIONS["In Japanese grammar, the word 'kono' (この) can be used by itself as a subject, such as in the sentence: 'Kono wa jisho desu' (この は じしょ です) meaning 'This is a dictionary.'"] = {
    "q": "In der japanischen Grammatik kann das Wort 'kono' (この) allein als Subjekt verwendet werden, z.B. im Satz: 'Kono wa jisho desu' (この は じしょ です) = 'Das ist ein Wörterbuch.'",
    "e": "Die Wörter 'kono' (この), 'sono' (その) und 'ano' (あの) sind Demonstrativbestimmer und müssen immer von einem Nomen gefolgt werden (z.B. 'Kono hon' / このほん). Um 'dies' als eigenständiges Subjekt zu verwenden, muss man 'kore' (これ) benutzen. Der korrekte Satz wäre 'Kore wa jisho desu' (これ は じしょ です).",
    "fb": {}
}

QUIZ_TRANSLATIONS["The particle 'no' (の) is used to connect two nouns to show possession or relationship, such as in 'Yamada-san no kuruma' (やまださん の くるま), which means 'Mr. Yamada's car.'"] = {
    "q": "Die Partikel 'no' (の) verbindet zwei Nomen und zeigt Besitz oder Beziehung, z.B. 'Yamada-san no kuruma' (やまださん の くるま) = 'Herr Yamadas Auto.'",
    "e": "In der Struktur 'N1 no N2' (N1 の N2) zeigt die Partikel 'no' (の), dass N2 zu N1 gehört oder damit zusammenhängt. 'Yamada-san no kuruma' (やまださん の くるま) identifiziert das Auto korrekt als Herrn Yamada gehörend.",
    "fb": {}
}

QUIZ_TRANSLATIONS["You are looking at a small object and you aren't sure if it is a '1' (ichi) or a '7' (nana). Which is the correct way to ask: 'Is this a \"1\" or a \"7\"?'"] = {
    "q": "Sie betrachten ein kleines Objekt und sind unsicher, ob es eine '1' (ichi) oder '7' (nana) ist. Wie fragt man korrekt: 'Ist das eine 1 oder eine 7?'",
    "e": "Für eine Auswahlfrage im Japanischen verwendet man das Muster 'N1 desu ka, N2 desu ka' (N1 ですか、N2 ですか). Man benutzt kein Wort für 'oder' — die Wiederholung der Fragepartikel 'ka' (か) erzeugt die 'oder'-Bedeutung.",
    "fb": {
        "Correct! To ask a choice question (N1 or N2?), you state both options followed by 'desu ka' (ですか).": "Richtig! Für eine Auswahlfrage (N1 oder N2?) nennt man beide Optionen gefolgt von 'desu ka' (ですか).",
        "Incorrect. Using 'no' (の) suggests a relationship like 'the 7 of 1', which doesn't make sense here.": "Falsch. 'No' (の) würde eine Beziehung wie 'die 7 der 1' suggerieren, was hier keinen Sinn ergibt.",
        "Incorrect. 'Kono' (この) cannot be used alone without a noun following it. You should use 'Kore' (これ).": "Falsch. 'Kono' (この) kann nicht allein ohne folgendes Nomen verwendet werden. Verwenden Sie 'Kore' (これ).",
        "Incorrect. This sounds like a statement rather than a polite question. The standard 'N1 desu ka, N2 desu ka' pattern is required.": "Falsch. Das klingt wie eine Aussage statt einer höflichen Frage. Das Standardmuster 'N1 desu ka, N2 desu ka' ist erforderlich.",
    }
}

QUIZ_TRANSLATIONS["In the conversation, Tanaka-san asks, 'Ano kasa wa dare no desu ka' (Whose umbrella is that over there?). According to Suzuki-san's reply, whose umbrella is it?"] = {
    "q": "Im Gespräch fragt Tanaka-san: 'Ano kasa wa dare no desu ka' (Wessen Regenschirm ist das dort drüben?). Laut Suzuki-sans Antwort, wem gehört der Regenschirm?",
    "e": "Im Dialog zeigt Tanaka-san auf einen entfernten Regenschirm und fragt 'Ano kasa wa dare no desu ka' (Wessen Regenschirm ist das dort drüben?). Suzuki-san antwortet 'Are wa watashi no desu' (Das ist meiner). Das bestätigt, dass der Regenschirm Suzuki-san gehört.",
    "fb": {
        "Correct! Suzuki-san replies 'Are wa watashi no desu' (That is mine), which means it belongs to Suzuki-san.": "Richtig! Suzuki-san antwortet 'Are wa watashi no desu' (Das ist meiner), was bedeutet, dass er Suzuki-san gehört.",
        "Incorrect. Suzuki-san mentions that a bag (kaban) belongs to Yamada-san, but not the umbrella.": "Falsch. Suzuki-san erwähnt, dass eine Tasche (kaban) Yamada-san gehört, aber nicht der Regenschirm.",
        "Incorrect. Tanaka-san is the person asking 'Whose is it?' and does not claim ownership of the umbrella.": "Falsch. Tanaka-san ist die Person, die fragt 'Wem gehört das?' und beansprucht den Regenschirm nicht.",
        "Incorrect. Suzuki-san clearly identifies it as her own.": "Falsch. Suzuki-san identifiziert ihn eindeutig als ihren eigenen.",
    }
}

QUIZ_TRANSLATIONS["Speaker A is pointing to an object right next to Speaker B. How should Speaker A ask what that object is?"] = {
    "q": "Sprecher A zeigt auf einen Gegenstand direkt neben Sprecher B. Wie sollte Sprecher A fragen, was dieser Gegenstand ist?",
    "e": "Im Japanischen bezieht sich それ (sore) auf Objekte in der Nähe des Gesprächspartners. それ (sore) は なん (nan) ですか (desu ka) bedeutet 'Was ist das (bei Ihnen)?'",
    "fb": {
        "これ (kore) is used for things near the speaker.": "これ (kore) wird für Dinge in der Nähe des Sprechers verwendet.",
        "Correct! それ (sore) is used for objects near the listener.": "Richtig! それ (sore) wird für Objekte beim Zuhörer verwendet.",
        "あれ (are) is used for objects far from both the speaker and listener.": "あれ (are) wird für Objekte verwendet, die von beiden entfernt sind.",
        "その (sono) must be followed by a noun (e.g., その ほん sono hon).": "その (sono) muss von einem Nomen gefolgt werden (z.B. その ほん sono hon).",
    }
}

QUIZ_TRANSLATIONS["Which sentence correctly says 'That umbrella over there is mine'?"] = {
    "q": "Welcher Satz sagt korrekt 'Der Regenschirm dort drüben ist meiner'?",
    "e": "Die Demonstrativbestimmer この (kono), その (sono) und あの (ano) müssen von einem Nomen gefolgt werden. Für ein Objekt weit entfernt von beiden Personen verwendet man あの (ano) + Nomen.",
    "fb": {
        "あれ (are) cannot be followed directly by a noun without a particle; you need 'ano'.": "あれ (are) kann nicht direkt von einem Nomen gefolgt werden; man braucht 'ano'.",
        "Correct! あの (ano) is the modifier form used before a noun to indicate something far away.": "Richtig! あの (ano) ist die Bestimmungsform vor einem Nomen für etwas weit Entferntes.",
        "その (sono) refers to something near the listener, not 'over there'.": "その (sono) bezieht sich auf etwas beim Zuhörer, nicht 'dort drüben'.",
        "あの (ano) must be followed by a noun. It cannot be the subject by itself.": "あの (ano) muss von einem Nomen gefolgt werden. Es kann nicht allein Subjekt sein.",
    }
}

QUIZ_TRANSLATIONS["""Choose the correct phrase to complete the dialogue:
Tanaka: それは [ ] の じしょ ですか。
Suzuki: はい、わたし の です。"""] = {
    "q": """Wählen Sie den richtigen Ausdruck, um den Dialog zu vervollständigen:
Tanaka: それは [ ] の じしょ ですか。
Suzuki: はい、わたし の です。""",
    "e": "だれ (dare) bedeutet 'wer'. Mit der Partikel の (no) wird es zu だれの (dare no) = 'wessen'. Das passt zu Suzukis Antwort 'watashi no' (meines).",
    "fb": {
        "なん (nan) means 'what', but the answer refers to a person.": "なん (nan) bedeutet 'was', aber die Antwort bezieht sich auf eine Person.",
        "そう (sou) means 'so/that's right', which doesn't fit a question about ownership.": "そう (sou) bedeutet 'so/richtig', was nicht zu einer Besitzfrage passt.",
        "Correct! だれ (dare) means 'who', and だれの (dare no) means 'whose'.": "Richtig! だれ (dare) bedeutet 'wer' und だれの (dare no) bedeutet 'wessen'.",
        "あのう (anou) is a hesitation filler like 'um' or 'well'.": "あのう (anou) ist ein Zögerungswort wie 'ähm' oder 'also'.",
    }
}

QUIZ_TRANSLATIONS["You see a writing tool and you're not sure if it's a pencil or a mechanical pencil. How do you ask 'Is this a pencil or a mechanical pencil?'"] = {
    "q": "Sie sehen ein Schreibgerät und sind unsicher, ob es ein Bleistift oder ein Druckbleistift ist. Wie fragen Sie 'Ist das ein Bleistift oder ein Druckbleistift?'",
    "e": "Für eine Auswahlfrage nennt man die erste Option + ですか (desu ka), gefolgt von der zweiten Option + ですか (desu ka).",
    "fb": {
        "This asks if it is 'a pencil AND a mechanical pencil'.": "Das fragt, ob es 'ein Bleistift UND ein Druckbleistift' ist.",
        "Correct! This is the standard pattern for offering a choice between two nouns.": "Richtig! Das ist das Standardmuster für eine Auswahl zwischen zwei Nomen.",
        "This implies a 'pencil's mechanical pencil', which doesn't make sense.": "Das impliziert 'der Druckbleistift des Bleistifts', was keinen Sinn ergibt.",
        "While 'ka' can mean 'or', the 'desu ka, desu ka' pattern is the one taught for choices in Lesson 2.": "Obwohl 'ka' 'oder' bedeuten kann, ist das 'desu ka, desu ka'-Muster das in Lektion 2 gelehrte Auswahl-Muster.",
    }
}

QUIZ_TRANSLATIONS["If someone gives you an 'omiyage' (souvenir) and you want to acknowledge the information politely, what do you say?"] = {
    "q": "Wenn jemand Ihnen ein 'omiyage' (Mitbringsel) gibt und Sie die Information höflich bestätigen möchten, was sagen Sie?",
    "e": "そうですか (Sou desu ka) ist ein vielseitiger Ausdruck, um zu zeigen, dass man eine neue Information verstanden hat.",
    "fb": {
        "Correct! This means 'I see' or 'Is that so?' and acknowledges new information.": "Richtig! Das bedeutet 'Ach so' oder 'Ist das so?' und bestätigt neue Informationen.",
        "ちがいます (chigaimasu) means 'No, it's wrong' or 'It's different'.": "ちがいます (chigaimasu) bedeutet 'Nein, das ist falsch' oder 'Das ist anders'.",
        "どうぞ (douzo) is used when offering something, not receiving information.": "どうぞ (douzo) wird beim Anbieten verwendet, nicht beim Empfangen von Informationen.",
        "そう です (sou desu) means 'That's right', used to agree with a statement.": "そう です (sou desu) bedeutet 'Das stimmt' und wird verwendet, um einer Aussage zuzustimmen.",
    }
}

QUIZ_TRANSLATIONS["True or False: The words 'kono' (この), 'sono' (その), and 'ano' (あの) can stand alone as the subject of a sentence (e.g., 'Kono wa watashi no desu')."] = {
    "q": "Wahr oder Falsch: Die Wörter 'kono' (この), 'sono' (その) und 'ano' (あの) können allein als Satzsubjekt stehen (z.B. 'Kono wa watashi no desu').",
    "e": "Falsch. この (kono), その (sono) und あの (ano) sind vorangestellte Bestimmer und müssen immer von einem Nomen gefolgt werden. Um 'dies', 'das' oder 'jenes' als eigenständiges Subjekt zu verwenden, muss man これ (kore), それ (sore) oder あれ (are) benutzen.",
    "fb": {}
}

QUIZ_TRANSLATIONS["True or False: In the phrase 'Eigo no teppou' (えいご の てちょう), the particle 'no' (の) can be used to describe what a notebook is about (e.g., an English notebook/planner)."] = {
    "q": "Wahr oder Falsch: Im Ausdruck 'Eigo no techou' (えいご の てちょう) kann die Partikel 'no' (の) beschreiben, worum es in einem Notizbuch geht (z.B. ein Englisch-Notizbuch).",
    "e": "Wahr. Die Partikel の (no) wird nicht nur für Besitz (mein Buch) verwendet, sondern auch um zu zeigen, worum es bei einem Nomen geht oder in welcher Beziehung es steht (ein Notizbuch für die englische Sprache).",
    "fb": {}
}

QUIZ_TRANSLATIONS["True or False: When someone says 'Doumo arigatou gozaimasu' (どうも ありがとうございます), responding with 'Douzo' (どうぞ) is the correct way to say 'You're welcome'."] = {
    "q": "Wahr oder Falsch: Wenn jemand 'Doumo arigatou gozaimasu' (どうも ありがとうございます) sagt, ist 'Douzo' (どうぞ) die richtige Antwort für 'Bitte schön/Gern geschehen'.",
    "e": "Falsch. どうぞ (douzo) bedeutet 'bitte' oder 'hier, bitte' beim Anbieten eines Gegenstands oder einer Handlung. Es wird nicht als 'Bitte schön/Gern geschehen' verwendet.",
    "fb": {}
}

QUIZ_TRANSLATIONS["Match the Japanese vocabulary words related to office/school supplies to their English meanings."] = {
    "q": "Ordnen Sie die japanischen Vokabeln für Büro-/Schulbedarf den deutschen Bedeutungen zu.",
    "e": "Das sind häufige Nomen aus Lektion 2: しんぶん (shinbun - Zeitung), めいし (meishi - Visitenkarte), とけい (tokei - Uhr), und じしょ (jisho - Wörterbuch).",
    "fb": {
        "Newspaper": "Zeitung",
        "Business card": "Visitenkarte",
        "Watch / Clock": "Uhr",
        "Dictionary": "Wörterbuch",
    }
}

QUIZ_TRANSLATIONS["Speaker A is holding a pen. Speaker B (standing across the room) asks: '___ wa nan desu ka.' What is the correct demonstrative to use for the item near the listener?"] = {
    "q": "Sprecher A hält einen Stift. Sprecher B (steht auf der anderen Seite des Raums) fragt: '___ wa nan desu ka.' Welches Demonstrativpronomen ist korrekt für den Gegenstand beim Zuhörer?",
    "e": "Im Japanischen bezieht sich sore (それ) auf Objekte in der Nähe des Zuhörers. Da der Stift in Sprecher As Hand ist und Sprecher B fragt, muss B sore (それ) verwenden.",
    "fb": {
        "Kore (これ) is used for things near the speaker. Since Speaker B is asking about something Speaker A is holding, B should use the 'near you' form.": "Kore (これ) wird für Dinge beim Sprecher verwendet. Da Sprecher B nach etwas fragt, das Sprecher A hält, sollte B die 'bei-Ihnen'-Form verwenden.",
        "Correct! Sore (それ) is used for objects near the listener (Speaker A).": "Richtig! Sore (それ) wird für Objekte beim Zuhörer (Sprecher A) verwendet.",
        "Are (あれ) is used for objects far from both the speaker and the listener.": "Are (あれ) wird für Objekte verwendet, die von beiden Sprechern weit entfernt sind.",
        "Dono (どの) is a modifier meaning 'which' and must be followed by a noun.": "Dono (どの) ist ein Bestimmer für 'welcher' und muss von einem Nomen gefolgt werden.",
    }
}

QUIZ_TRANSLATIONS["Choose the correct sentence to ask: 'Is that (over there) a Japanese newspaper?'"] = {
    "q": "Wählen Sie den korrekten Satz: 'Ist das (dort drüben) eine japanische Zeitung?'",
    "e": "Um die Eigenschaft eines Objekts zu beschreiben (wie die Sprache einer Zeitung), verwenden wir N1 no N2 (z.B. nihongo no shinbun). 'Are' ist das richtige Pronomen für etwas, das von beiden Parteien weit entfernt ist.",
    "fb": {
        "Correct! Are (あれ) is 'that over there', and nihongo no shinbun (にほんごの しんぶん) uses 'no' to describe the type of newspaper.": "Richtig! Are (あれ) ist 'das dort drüben' und nihongo no shinbun (にほんごの しんぶん) verwendet 'no' um die Art der Zeitung zu beschreiben.",
        "Sore (それ) refers to something near the listener, but the question asks for 'that over there'.": "Sore (それ) bezieht sich auf etwas beim Zuhörer, aber die Frage verlangt 'das dort drüben'.",
        "While grammatically possible, this means 'Is that newspaper [over there] Japanese language?' rather than 'Is that a Japanese newspaper?'": "Zwar grammatisch möglich, aber das bedeutet 'Ist diese Zeitung [dort drüben] japanischsprachig?' statt 'Ist das eine japanische Zeitung?'",
        "Kore (これ) means 'this' and the particle 'no' (の) is missing between 'nihongo' and 'shinbun'.": "Kore (これ) bedeutet 'dies' und die Partikel 'no' (の) fehlt zwischen 'nihongo' und 'shinbun'.",
    }
}

QUIZ_TRANSLATIONS["""Complete the conversation.
Tanaka: '___ nooto wa Suzuki-san no desu ka, Yamada-san no desu ka.'
Suzuki: 'Watashi no desu.'"""] = {
    "q": """Vervollständigen Sie das Gespräch.
Tanaka: '___ nooto wa Suzuki-san no desu ka, Yamada-san no desu ka.'
Suzuki: 'Watashi no desu.'""",
    "e": "Kono, sono und ano (この/その/あの) sind Demonstrativbestimmer. Sie werden immer von einem Nomen gefolgt. Pronomen wie kore, sore und are (これ/それ/あれ) stehen allein als Subjekt.",
    "fb": {
        "Kore (これ) is a pronoun and cannot be followed directly by a noun like 'nooto'.": "Kore (これ) ist ein Pronomen und kann nicht direkt von einem Nomen wie 'nooto' gefolgt werden.",
        "Correct! Kono (この) is a demonstrative modifier that must be followed by a noun (nooto).": "Richtig! Kono (この) ist ein Demonstrativbestimmer, der von einem Nomen (nooto) gefolgt werden muss.",
        "Sore (それ) is a pronoun and cannot be followed directly by a noun.": "Sore (それ) ist ein Pronomen und kann nicht direkt von einem Nomen gefolgt werden.",
        "Are (あれ) is a pronoun and cannot be followed directly by a noun.": "Are (あれ) ist ein Pronomen und kann nicht direkt von einem Nomen gefolgt werden.",
    }
}

QUIZ_TRANSLATIONS["Which response is most appropriate when someone offers you a gift by saying 'Douzo' (どうぞ)?"] = {
    "q": "Welche Antwort ist am passendsten, wenn jemand Ihnen ein Geschenk mit 'Douzo' (どうぞ) anbietet?",
    "e": "Wenn man etwas mit 'Douzo' (Bitte schön) angeboten bekommt, ist die höfliche Antwort, der Person mit 'Arigatou gozaimasu' oder 'Doumo' zu danken.",
    "fb": {
        "Sou desu ka (そうですか) means 'I see' or 'Is that so?', which is not a natural way to accept a gift.": "Sou desu ka (そうですか) bedeutet 'Ach so' — keine natürliche Art, ein Geschenk anzunehmen.",
        "Chigaimasu (ちがいます) means 'It's different' or 'No, it's not', which would be rude when receiving a gift.": "Chigaimasu (ちがいます) bedeutet 'Das ist falsch' — wäre unhöflich beim Empfang eines Geschenks.",
        "Correct! This is a polite way to say 'Thank you very much' when receiving something.": "Richtig! Das ist eine höfliche Art 'Vielen Dank' zu sagen, wenn man etwas erhält.",
        "Anou (あのう) is a filler word used when hesitant or trying to get someone's attention.": "Anou (あのう) ist ein Füllwort für Zögern oder um Aufmerksamkeit zu erlangen.",
    }
}

QUIZ_TRANSLATIONS["How do you say 'This is not my dictionary' using the grammar from Lesson 2?"] = {
    "q": "Wie sagt man 'Das ist nicht mein Wörterbuch' mit der Grammatik aus Lektion 2?",
    "e": "Um 'mein Wörterbuch' zu sagen, verwendet man 'watashi no jisho'. Um den Satz 'Das ist...' zu verneinen, ändert man 'desu' zu 'ja arimasen' oder 'dewa arimasen'.",
    "fb": {
        "Correct! 'Watashi no jisho' (my dictionary) + 'ja arimasen' (is not).": "Richtig! 'Watashi no jisho' (mein Wörterbuch) + 'ja arimasen' (ist nicht).",
        "This means 'This dictionary is me', which is incorrect.": "Das bedeutet 'Dieses Wörterbuch ist ich', was falsch ist.",
        "The word order is incorrect. The noun must come before 'desu' or its negative form.": "Die Wortstellung ist falsch. Das Nomen muss vor 'desu' oder seiner Verneinungsform stehen.",
        "This means 'That is my dictionary', but the question asked for 'This' and a negative statement.": "Das bedeutet 'Das ist mein Wörterbuch', aber gefragt war nach 'Dies' und einem verneinenden Satz.",
    }
}

QUIZ_TRANSLATIONS["The phrase 'Kore wa Yamada-san no desu' (これは 山田さんのです) is a complete and correct sentence meaning 'This is Mr. Yamada's [thing]'."] = {
    "q": "Der Satz 'Kore wa Yamada-san no desu' (これは 山田さんのです) ist ein vollständiger und korrekter Satz mit der Bedeutung 'Das ist Herrn Yamadas [Gegenstand]'.",
    "e": "Wahr. Wenn das besessene Nomen aus dem Kontext klar ist, kann man es weglassen und einfach 'Person no desu' (Es gehört Person) sagen.",
    "fb": {}
}

QUIZ_TRANSLATIONS["When you want to say 'That car over there', you should use 'Sono kuruma' (その くるま)."] = {
    "q": "Wenn man 'Das Auto dort drüben' sagen möchte, sollte man 'Sono kuruma' (その くるま) verwenden.",
    "e": "Falsch. 'Sono' (その) wird für etwas beim Zuhörer verwendet. Für 'dort drüben' (weit von beiden) muss man 'Ano' (あの) verwenden, also 'Ano kuruma'.",
    "fb": {}
}

QUIZ_TRANSLATIONS["The expression 'Sou desu ka' (そうですか) can be used to show you have understood new information, similar to 'I see' in English."] = {
    "q": "Der Ausdruck 'Sou desu ka' (そうですか) kann verwendet werden, um zu zeigen, dass man neue Informationen verstanden hat, ähnlich wie 'Ach so' im Deutschen.",
    "e": "Wahr. 'Sou desu ka' ist eine häufige Gesprächsreaktion, um zu zeigen, dass man neue Informationen aufgenommen und verstanden hat.",
    "fb": {}
}

QUIZ_TRANSLATIONS["Match the Japanese items with their appropriate English translations."] = {
    "q": "Ordnen Sie die japanischen Gegenstände den richtigen deutschen Übersetzungen zu.",
    "e": "Das sind häufige persönliche Gegenstände aus Lektion 2: techou (Taschennotizbuch/Planer), meishi (Visitenkarte), tokei (Uhr) und kagi (Schlüssel).",
    "fb": {
        "pocket notebook / planner": "Taschennotizbuch / Planer",
        "business card": "Visitenkarte",
        "watch / clock": "Uhr",
        "key": "Schlüssel",
    }
}

# ═══════════════════════════════════════════════════════════════════════
# LEKTION 3 – Orte und Preise
# ═══════════════════════════════════════════════════════════════════════

QUIZ_TRANSLATIONS["You are talking to a friend and want to point out a building that is far away from both of you. Which word should you use to refer to 'over there'?"] = {
    "q": "Sie sprechen mit einem Freund und möchten auf ein Gebäude zeigen, das weit von Ihnen beiden entfernt ist. Welches Wort verwenden Sie für 'dort drüben'?",
    "e": "Bei den japanischen Demonstrativa steht ここ (koko) für nahe beim Sprecher, そこ (soko) für nahe beim Zuhörer und あそこ (asoko) für weit von beiden. どこ (doko) ist das Fragewort für 'wo'.",
    "fb": {
        "ここ (koko) means 'here' and refers to a place close to the speaker.": "ここ (koko) bedeutet 'hier' und bezeichnet einen Ort nahe beim Sprecher.",
        "そこ (soko) means 'there' and refers to a place close to the listener.": "そこ (soko) bedeutet 'da' und bezeichnet einen Ort nahe beim Zuhörer.",
        "Correct! あそこ (asoko) is used for a location far from both the speaker and the listener.": "Richtig! あそこ (asoko) wird für einen Ort verwendet, der von beiden Sprechern weit entfernt ist.",
        "どこ (doko) is the question word meaning 'where'.": "どこ (doko) ist das Fragewort für 'wo'.",
    }
}

QUIZ_TRANSLATIONS["You are visiting a Japanese company (kaisha) and need to find the reception desk. Which word should you look for on the directory?"] = {
    "q": "Sie besuchen eine japanische Firma (kaisha) und müssen den Empfang finden. Welches Wort suchen Sie auf dem Wegweiser?",
    "e": "うけつけ (uketsuke) ist der japanische Begriff für Empfang. Weitere häufige Bürobereiche sind じむしょ (jimusho - Büro) und かいぎしつ (kaigishitsu - Konferenzraum).",
    "fb": {
        "じむしょ (jimusho) means 'office'.": "じむしょ (jimusho) bedeutet 'Büro'.",
        "Correct! うけつけ (uketsuke) means 'reception desk' or 'information desk'.": "Richtig! うけつけ (uketsuke) bedeutet 'Empfang' oder 'Informationsschalter'.",
        "かいぎしつ (kaigishitsu) means 'conference room' or 'meeting room'.": "かいぎしつ (kaigishitsu) bedeutet 'Konferenzraum' oder 'Besprechungsraum'.",
        "しょくどう (shokudou) means 'dining hall' or 'cafeteria'.": "しょくどう (shokudou) bedeutet 'Kantine' oder 'Mensa'.",
    }
}

QUIZ_TRANSLATIONS["You see a beautiful tie (nekutai) at a department store and want to ask the price. What is the correct way to say 'How much is this?'"] = {
    "q": "Sie sehen eine schöne Krawatte (nekutai) im Kaufhaus und möchten den Preis erfragen. Wie fragt man korrekt 'Wie viel kostet das?'",
    "e": "Um nach dem Preis eines Artikels zu fragen, verwendet man den Ausdruck いくら ですか (ikura desu ka). Die Partikel は (wa) markiert das Thema der Frage.",
    "fb": {
        "なんばん (nanban) means 'what number'. This asks 'What number is this?'": "なんばん (nanban) bedeutet 'welche Nummer'. Das fragt 'Welche Nummer ist das?'",
        "どこ (doko) means 'where'. This asks 'Where is this?'": "どこ (doko) bedeutet 'wo'. Das fragt 'Wo ist das?'",
        "Correct! いくら (ikura) is the interrogative word for 'how much' regarding price.": "Richtig! いくら (ikura) ist das Fragewort für 'wie viel' bezüglich des Preises.",
        "なん (nan) means 'what'. This asks 'What is this?'": "なん (nan) bedeutet 'was'. Das fragt 'Was ist das?'",
    }
}

QUIZ_TRANSLATIONS["If you are at a department store and want to ask the price of a necktie (nekutai), which sentence should you use?"] = {
    "q": "Wenn Sie im Kaufhaus den Preis einer Krawatte (nekutai) erfragen möchten, welchen Satz verwenden Sie?",
    "e": "Um nach dem Preis zu fragen, ist die Struktur 'N (Nomen) wa ikura desu ka?'. 'Ikura' (いくら) bedeutet 'wie viel' und die Partikel 'wa' (は) markiert das Thema.",
    "fb": {
        "No, 'nan-gai' (なんがい) asks which floor the necktie is on, not its price.": "Nein, 'nan-gai' (なんがい) fragt, auf welchem Stockwerk die Krawatte ist, nicht nach dem Preis.",
        "Correct! 'Ikura' (いくら) is the question word used to ask 'how much' something costs.": "Richtig! 'Ikura' (いくら) ist das Fragewort für 'wie viel' etwas kostet.",
        "No, this means 'Is this place a necktie?', which doesn't make sense in this context.": "Nein, das bedeutet 'Ist dieser Ort eine Krawatte?', was in diesem Kontext keinen Sinn ergibt.",
        "No, 'doko' (どこ) asks for the location (where), not the price.": "Nein, 'doko' (どこ) fragt nach dem Ort (wo), nicht nach dem Preis.",
    }
}

QUIZ_TRANSLATIONS["In the sentence 'Jimusho wa ni-kai desu' (じむしょは にかいです), the speaker is stating that the office is on the second floor."] = {
    "q": "Im Satz 'Jimusho wa ni-kai desu' (じむしょは にかいです) sagt der Sprecher, dass das Büro im zweiten Stock ist.",
    "e": "Diese Aussage ist wahr. 'Jimusho' (じむしょ) bedeutet Büro, 'wa' (は) ist die Themenpartikel, 'ni-kai' (にかい) bedeutet zweiter Stock und 'desu' (です) ist die höfliche Kopula 'ist'. Um daraus eine Frage zu machen ('Auf welchem Stock ist das Büro?') würde man sagen 'Jimusho wa nan-gai desu ka?' (じむしょは なんがいですか？).",
    "fb": {}
}

QUIZ_TRANSLATIONS["The word 'koko' (ここ) refers to a location that is far away from both the speaker and the listener."] = {
    "q": "Das Wort 'koko' (ここ) bezeichnet einen Ort, der weit entfernt von Sprecher und Zuhörer ist.",
    "e": "Falsch. 'Koko' (ここ) bezeichnet einen Ort nahe beim Sprecher. Das Wort für einen Ort weit von beiden ist 'asoko' (あそこ), während 'soko' (そこ) einen Ort nahe beim Zuhörer bezeichnet.",
    "fb": {}
}

QUIZ_TRANSLATIONS["Based on the conversation between Kimura and Hayashi, where is the 会議室 (kaigishitsu - conference room) located?"] = {
    "q": "Basierend auf dem Gespräch zwischen Kimura und Hayashi, wo befindet sich der 会議室 (kaigishitsu - Konferenzraum)?",
    "e": "Im Dialog werden mehrere Orte festgelegt: die 食堂 (shokudou - Kantine) ist im 地下 (chika - Untergeschoss), die トイレ (toire - Toilette) im 二階 (nikai - zweiten Stock) und der 会議室 (kaigishitsu - Konferenzraum) im 三階 (sankai - dritten Stock). Das Erkennen bestimmter Stockwerknummern ist eine Schlüsselkompetenz für Lektion 3.",
    "fb": {
        "いいえ (Iie - No). The 地下 (chika - basement) is where the 食堂 (shokudou - cafeteria) is located.": "いいえ (Iie - Nein). Im 地下 (chika - Untergeschoss) befindet sich die 食堂 (shokudou - Kantine).",
        "いいえ (Iie - No). The 二階 (nikai - second floor) is where the トイレ (toire - restroom) is located.": "いいえ (Iie - Nein). Im 二階 (nikai - zweiten Stock) befindet sich die トイレ (toire - Toilette).",
        "はい、そうです (Hai, sou desu - Yes, that's right)! Hayashi confirms: '会議室は 三階です' (Kaigishitsu wa sankai desu - The conference room is on the third floor).": "はい、そうです (Hai, sou desu - Ja, richtig)! Hayashi bestätigt: '会議室は 三階です' (Kaigishitsu wa sankai desu - Der Konferenzraum ist im dritten Stock).",
        "いいえ (Iie - No). While Hayashi says 'あそこです' (Asoko desu - It is over there), he is specifically referring to the エレベーター (erebeetaa - elevator), not the floor of the room.": "いいえ (Iie - Nein). Obwohl Hayashi 'あそこです' (Asoko desu - Dort drüben) sagt, bezieht er sich auf den エレベーター (erebeetaa - Aufzug), nicht auf das Stockwerk des Raums.",
    }
}

# L3 remaining questions - using a more compact format for True/False and matching
QUIZ_TRANSLATIONS["Politely asking someone's country of origin uses the phrase 'Okuni wa doko desu ka?' (おくには どこですか). Which alternative question word is MORE polite for this specific phrase?"] = {
    "q": "Die höfliche Frage nach dem Herkunftsland verwendet 'Okuni wa doko desu ka?' (おくには どこですか). Welches alternative Fragewort ist HÖFLICHER für diesen spezifischen Ausdruck?",
    "e": "In Lektion 3 wird 'dochira' (どちら) als höfliche Alternative zu 'doko' (どこ) eingeführt. Bei der Frage nach dem Herkunftsland ('Okuni wa dochira desu ka?') wird 'dochira' bevorzugt.",
    "fb": {
        "'Doko' is grammatically okay, but 'dochira' is more polite and expected for this specific phrase.": "'Doko' ist grammatisch korrekt, aber 'dochira' ist höflicher und wird bei diesem spezifischen Ausdruck erwartet.",
        "Correct! 'Okuni wa dochira desu ka' is the set polite phrase for 'Where are you from?'": "Richtig! 'Okuni wa dochira desu ka' ist die feste höfliche Wendung für 'Woher kommen Sie?'",
        "Nanban (なんばん) asks for a number.": "Nanban (なんばん) fragt nach einer Nummer.",
        "Ikura (いくら) asks for a price.": "Ikura (いくら) fragt nach einem Preis.",
    }
}

QUIZ_TRANSLATIONS["In Japanese, the word 'じどうはんばいき' (jidouhanbaiki) means 'elevator'."] = {
    "q": "Im Japanischen bedeutet das Wort 'じどうはんばいき' (jidouhanbaiki) 'Aufzug'.",
    "e": "Falsch. 'Jidouhanbaiki' (じどうはんばいき) bedeutet 'Getränkeautomat'. Das Wort für Aufzug ist 'erebeetaa' (エレベーター).",
    "fb": {}
}

QUIZ_TRANSLATIONS["The particle 'も' (mo) can be used to say 'also'. For example, if the cafeteria is in the basement, and the restroom is also there, you can say 'トイレも ちかです' (Toire mo chika desu)."] = {
    "q": "Die Partikel 'も' (mo) kann verwendet werden, um 'auch' zu sagen. Zum Beispiel: Wenn die Kantine im Untergeschoss ist und die Toilette auch dort, kann man sagen 'トイレも ちかです' (Toire mo chika desu).",
    "e": "Wahr. Die Partikel 'mo' (も) ersetzt 'wa' (は), um anzuzeigen, dass dieselbe Beschreibung für ein neues Subjekt gilt.",
    "fb": {}
}

QUIZ_TRANSLATIONS["To ask for someone's telephone number, the correct phrase is 'でんわばんごうは なんばんですか' (Denwa bangou wa nanban desu ka)."] = {
    "q": "Um nach der Telefonnummer zu fragen, ist der korrekte Ausdruck 'でんわばんごうは なんばんですか' (Denwa bangou wa nanban desu ka).",
    "e": "Wahr. 'Nanban' (なんばん) bedeutet 'welche Nummer' und wird für Telefonnummern, Zimmernummern usw. verwendet.",
    "fb": {}
}

QUIZ_TRANSLATIONS["Match the Japanese locations/items to their English meanings."] = {
    "q": "Ordnen Sie die japanischen Orte/Gegenstände den deutschen Bedeutungen zu.",
    "e": "Uketsuke (うけつけ) ist Empfang, Shokudou (しょくどう) ist Kantine/Mensa, Kaidan (かいだん) sind Treppen und Wain (ワイン) ist Wein (Lehnwort).",
    "fb": {
        "Reception desk": "Empfang",
        "Dining hall / Cafeteria": "Kantine / Mensa",
        "Stairs": "Treppen",
        "Wine": "Wein",
    }
}

QUIZ_TRANSLATIONS["A customer is at a department store and wants to ask politely where the necktie counter is located. Which of the following is the MOST appropriate question?"] = {
    "q": "Ein Kunde im Kaufhaus möchte höflich fragen, wo die Krawattenabteilung ist. Welche Frage ist am PASSENDSTEN?",
    "e": "In Lektion 3 lernen wir, dass 'dochira' (どちら) die höfliche Alternative zu 'doko' (どこ) ist. Im Gespräch mit Personal oder in formellen Situationen ist 'dochira' angemessener.",
    "fb": {
        "While grammatically correct, 'doko' is less polite than 'dochira' in a formal store setting.": "Zwar grammatisch korrekt, aber 'doko' ist weniger höflich als 'dochira' in einem formellen Kaufhaus.",
        "Correct! 'Dochira' (どちら) is the polite version of 'doko' (where) and is standard in customer-staff interactions.": "Richtig! 'Dochira' (どちら) ist die höfliche Version von 'doko' (wo) und Standard im Kunden-Personal-Kontakt.",
        "This asks 'What is the necktie counter?', not where it is.": "Das fragt 'Was ist die Krawattenabteilung?', nicht wo sie ist.",
        "This asks 'How much is the necktie counter?', which is incorrect context.": "Das fragt 'Wie viel kostet die Krawattenabteilung?', was im falschen Kontext steht.",
    }
}

QUIZ_TRANSLATIONS["Look at the price tag: ¥18,500. How would the shop assistant say this amount in Japanese?"] = {
    "q": "Sehen Sie das Preisschild: ¥18'500. Wie würde der Verkäufer diesen Betrag auf Japanisch sagen?",
    "e": "Japanisch verwendet die Einheit 'man' (万) für 10'000. Daher wird 18'500 aufgeteilt in 1 (ichi) man + 8'000 (hassen) + 500 (gohyaku).",
    "fb": {
        "This is 1,850 yen. You missed the 'ten thousand' (man) unit.": "Das sind 1'850 Yen. Die 'Zehntausender'-Einheit (man) fehlt.",
        "Correct! 18,500 is one 'man' (10,000) + 'hassen' (8,000) + 'gohyaku' (500).": "Richtig! 18'500 ist ein 'man' (10'000) + 'hassen' (8'000) + 'gohyaku' (500).",
        "In Japanese, you cannot say '18-thousand' (juuhassen). You must use 'man' for the 10,000 unit.": "Im Japanischen kann man nicht '18-tausend' (juuhassen) sagen. Man muss 'man' für die 10'000er-Einheit verwenden.",
        "This is 10,850 yen. You missed the 'eight thousand' (hassen) part.": "Das sind 10'850 Yen. Der 'achttausend'-Teil (hassen) fehlt.",
    }
}

QUIZ_TRANSLATIONS["""Complete the dialogue based on the location:
Kimura: すみません、お手洗いは どこですか。(Sumimasen, otearai wa doko desu ka.)
Staff: お手洗いは ______ です。(Otearai wa ______ desu.)
Kimura: ありがとうございます。(Arigatou gozaimasu.)"""] = {
    "q": """Vervollständigen Sie den Dialog:
Kimura: すみません、お手洗いは どこですか。(Sumimasen, otearai wa doko desu ka.)
Mitarbeiter: お手洗いは ______ です。(Otearai wa ______ desu.)
Kimura: ありがとうございます。(Arigatou gozaimasu.)""",
    "e": "In diesem Kontext ist 'chika' (地下 - Untergeschoss) die logische Antwort für einen Ort innerhalb eines Gebäudes wie Kaufhaus oder Büro.",
    "fb": {
        "Sankai (さんかい) means the 3rd floor.": "Sankai (さんかい) bedeutet 3. Stock.",
        "Kaidan (かいだん) means stairs. While a location, the prompt suggests a specific floor level.": "Kaidan (かいだん) bedeutet Treppen. Obwohl ein Ort, verlangt die Frage eine bestimmte Etage.",
        "Correct! 'Chika' (地下) means basement or below ground level.": "Richtig! 'Chika' (地下) bedeutet Untergeschoss.",
        "Uchi (うち) means home/house, which doesn't fit a public facility context.": "Uchi (うち) bedeutet Zuhause/Haus, was nicht zu einem öffentlichen Gebäude passt.",
    }
}

QUIZ_TRANSLATIONS["Which question word should be used to ask for a company's telephone number (denwa bangou)?"] = {
    "q": "Welches Fragewort verwendet man, um nach der Telefonnummer (denwa bangou) einer Firma zu fragen?",
    "e": "Um nach einer Telefonnummer (denwa bangou - 電話番号) zu fragen, verwendet man '...wa nanban desu ka?' (何番ですか).",
    "fb": {
        "Doko (どこ) asks for 'where', not a number.": "Doko (どこ) fragt nach 'wo', nicht nach einer Nummer.",
        "Correct! 'Nanban' (何番) is used to ask for numbers, such as telephone numbers or room numbers.": "Richtig! 'Nanban' (何番) wird verwendet, um nach Nummern zu fragen, z.B. Telefon- oder Zimmernummern.",
        "Ikura (いくら) is used to ask for prices.": "Ikura (いくら) wird verwendet, um nach Preisen zu fragen.",
        "Dochira (どちら) is used to ask for directions or polite locations.": "Dochira (どちら) wird verwendet, um höflich nach Richtungen oder Orten zu fragen.",
    }
}

QUIZ_TRANSLATIONS["""A: 会議室は どこですか。(Kaigishitsu wa doko desu ka.)
B: 3階です。受付も 3階です。(Sankai desu. Uketsuke mo sankai desu.)
What does Speaker B mean?"""] = {
    "q": """A: 会議室は どこですか。(Kaigishitsu wa doko desu ka.)
B: 3階です。受付も 3階です。(Sankai desu. Uketsuke mo sankai desu.)
Was meint Sprecher B?""",
    "e": "Die Partikel 'mo' (も) ersetzt 'wa', um anzuzeigen, dass das Subjekt dieselbe Eigenschaft teilt (hier: denselben Standort).",
    "fb": {
        "The conference room is on the 3rd floor, but the reception is not.": "Der Konferenzraum ist im 3. Stock, aber der Empfang nicht.",
        "The conference room is on the 3rd floor, and the reception is also on the 3rd floor.": "Der Konferenzraum ist im 3. Stock und der Empfang ist auch im 3. Stock.",
        "The conference room is on the 3rd floor, and the reception is on the 1st floor.": "Der Konferenzraum ist im 3. Stock und der Empfang im 1. Stock.",
        "Neither the conference room nor the reception are on the 3rd floor.": "Weder der Konferenzraum noch der Empfang sind im 3. Stock.",
    }
}

QUIZ_TRANSLATIONS["The question word used to ask which floor something is on is 'Nangai' (なんがい), and the 'kai' (階) sound changes to 'gai' (がい) after 'nan' (なん)."] = {
    "q": "Das Fragewort für 'welcher Stock' ist 'Nangai' (なんがい), und der 'kai' (階)-Laut ändert sich nach 'nan' (なん) zu 'gai' (がい).",
    "e": "Wahr. Während die meisten Stockwerke 'kai' verwenden (z.B. nikai, yonkai), beinhalten die Frage 'welcher Stock' (nangai) und 'dritter Stock' (sankai/sangai) oft phonetische Veränderungen.",
    "fb": {}
}

QUIZ_TRANSLATIONS["In the sentence 'Koko wa jimusho desu' (ここ は じむしょ です), 'koko' refers to a place near the person being spoken to."] = {
    "q": "Im Satz 'Koko wa jimusho desu' (ここ は じむしょ です) bezieht sich 'koko' auf einen Ort nahe der angesprochenen Person.",
    "e": "Falsch. 'Koko' (ここ) bezeichnet den Ort, wo der Sprecher ist. 'Soko' (そこ) bezeichnet den Ort, wo der Zuhörer ist.",
    "fb": {}
}

QUIZ_TRANSLATIONS["The word 'Otearai' (おてあらい) is a more polite way to say 'restroom' than 'Toire' (トイレ)."] = {
    "q": "Das Wort 'Otearai' (おてあらい) ist eine höflichere Art 'Toilette' zu sagen als 'Toire' (トイレ).",
    "e": "Wahr. 'Otearai' bedeutet wörtlich 'Händewaschplatz' und gilt als feiner/höflicher als das Lehnwort 'toire'.",
    "fb": {}
}

QUIZ_TRANSLATIONS["Match the Japanese locations or items to their correct descriptions."] = {
    "q": "Ordnen Sie die japanischen Orte oder Gegenstände den richtigen Beschreibungen zu.",
    "e": "Jidouhanbaiki (じどうはんばいき) ist ein Getränkeautomat. Shokudou (しょくどう) ist eine Kantine. Uketsuke (うけつけ) ist der Empfang. Kaigishitsu (かいぎしつ) ist der Konferenzraum.",
    "fb": {
        "Vending machine": "Getränkeautomat",
        "Dining hall / Cafeteria": "Kantine / Mensa",
        "Reception desk": "Empfang",
        "Conference room": "Konferenzraum",
    }
}

# ═══════════════════════════════════════════════════════════════════════
# LEKTION 4 – Uhrzeit und Tagesablauf (kompakte Form)
# ═══════════════════════════════════════════════════════════════════════

L4_Q = QUIZ_TRANSLATIONS

L4_Q["""Which Japanese verb best completes this sentence about a typical job schedule?

Watashi wa (I) mainichi (every day) 9-ji kara 5-ji made [_____]."""] = {
    "q": """Welches japanische Verb vervollständigt diesen Satz über einen typischen Arbeitsalltag?

Watashi wa (ich) mainichi (jeden Tag) 9-ji kara 5-ji made [_____].""",
    "e": "Im Japanischen wird はたらきます (hatarakimasu) für 'arbeiten' verwendet. '9-ji kara 5-ji made hatarakimasu' bedeutet 'Ich arbeite von 9 bis 5 Uhr'.",
    "fb": {
        "Okimasu means 'to get up' or 'to wake up'.": "Okimasu bedeutet 'aufstehen' oder 'aufwachen'.",
        "Correct! Hatarakimasu means 'to work'.": "Richtig! Hatarakimasu bedeutet 'arbeiten'.",
        "Nemasu means 'to sleep' or 'to go to bed'.": "Nemasu bedeutet 'schlafen' oder 'ins Bett gehen'.",
        "Benkyoushimasu means 'to study', which is usually for students rather than a 9-to-5 job.": "Benkyoushimasu bedeutet 'lernen/studieren', was eher für Studenten als für einen 9-bis-5-Job ist.",
    }
}

L4_Q["""If someone asks 'Ima (now) nan-ji (what time) desu ka?', and you want to reply that it is 'half past seven' in the evening, which word fills the blank?

'Gogo (PM) 7-ji [_____] desu.'"""] = {
    "q": """Wenn jemand fragt 'Ima (jetzt) nan-ji (wie viel Uhr) desu ka?' und Sie antworten möchten, dass es 'halb acht' abends ist, welches Wort füllt die Lücke?

'Gogo (PM) 7-ji [_____] desu.'""",
    "e": "Um 'halb' nach einer Stunde auszudrücken, fügt man はん (han) nach dem Stundenzähler じ (ji) hinzu. 7-ji han (7:30) bedeutet wörtlich 'sieben Uhr halb'.",
    "fb": {
        "Fun (or pun) is the counter for minutes in general.": "Fun (oder pun) ist der allgemeine Minutenzähler.",
        "Ban means 'evening' or 'night', but it isn't used to indicate the 30-minute mark.": "Ban bedeutet 'Abend' oder 'Nacht', wird aber nicht für die 30-Minuten-Marke verwendet.",
        "Correct! Han means 'half' and is used to say 'half past' the hour.": "Richtig! Han bedeutet 'halb' und wird für 'halb nach' der Stunde verwendet.",
        "Mae means 'before' or 'ago' (not part of this lesson's core time-telling vocabulary for half-past).": "Mae bedeutet 'vor' oder 'vorher' (nicht Teil des Kernvokabulars dieser Lektion für 'halb').",
    }
}

L4_Q["""Which word correctly expresses the frequency in this routine?

'Tanaka-san wa [_____] 6-ji ni okimasu.' (Mr. Tanaka wakes up at 6:00 every morning.)"""] = {
    "q": """Welches Wort drückt die Häufigkeit in dieser Routine korrekt aus?

'Tanaka-san wa [_____] 6-ji ni okimasu.' (Herr Tanaka steht jeden Morgen um 6:00 auf.)""",
    "e": "まいあさ (maiasa) ist die Kombination aus まい (mai - jeder) und あさ (asa - Morgen). Es beschreibt Gewohnheiten, die jeden Morgen stattfinden.",
    "fb": {
        "Maiban means 'every night'.": "Maiban bedeutet 'jeden Abend'.",
        "Correct! Maiasa means 'every morning'.": "Richtig! Maiasa bedeutet 'jeden Morgen'.",
        "Kesa means 'this morning' (specific to today), not 'every morning'.": "Kesa bedeutet 'heute Morgen' (spezifisch für heute), nicht 'jeden Morgen'.",
        "Ashita means 'tomorrow'.": "Ashita bedeutet 'morgen'.",
    }
}

L4_Q["In Japanese, to change a verb like 働きます (hatarakimasu - to work) into the past negative form (did not work), you change the ending to ませんでした."] = {
    "q": "Im Japanischen ändert man bei einem Verb wie 働きます (hatarakimasu - arbeiten) die Endung zu ませんでした, um die vergangene Verneinungsform (hat nicht gearbeitet) zu bilden.",
    "e": "Um ein höfliches Verb in die vergangene Verneinung zu konjugieren, ändert man die ~ます (~masu)-Endung zu ~ませんでした (~masen deshita). Zum Beispiel: 働きます (hatarakimasu - arbeiten) wird zu 働きませんでした (hatarakimasen deshita - hat nicht gearbeitet).",
    "fb": {}
}

L4_Q["""Choose the correct particle to complete the sentence indicating a specific point in time:
「わたしは　まいにち　6じ (___) おきます。」
(Watashi wa mainichi 6-ji (...) okimasu. / I wake up at 6 o'clock every day.)"""] = {
    "q": """Wählen Sie die richtige Partikel für einen bestimmten Zeitpunkt:
「わたしは　まいにち　6じ (___) おきます。」
(Watashi wa mainichi 6-ji (...) okimasu. / Ich stehe jeden Tag um 6 Uhr auf.)""",
    "e": "Die Partikel に (ni) wird nach einer bestimmten Uhrzeit (wie Stunden oder Minuten) verwendet, um anzuzeigen, wann eine Handlung stattfindet. 6じに おきます (roku-ji ni okimasu) bedeutet 'um 6 Uhr aufstehen'.",
    "fb": {
        "Correct! に (ni) is the particle used to indicate the specific time an action happens.": "Richtig! に (ni) ist die Partikel, die den genauen Zeitpunkt einer Handlung angibt.",
        "Incorrect. を (wo) is used for direct objects, not for time points.": "Falsch. を (wo) wird für direkte Objekte verwendet, nicht für Zeitpunkte.",
        "Incorrect. は (wa) is the topic marker. While '6-ji wa' could be used in specific contexts for contrast, 'ni' is the standard particle for 'at a specific time'.": "Falsch. は (wa) ist der Themenmarker. Obwohl '6-ji wa' in bestimmten Kontexten für Kontrast verwendet werden könnte, ist 'ni' die Standardpartikel für 'zu einer bestimmten Zeit'.",
        "Incorrect. も (mo) means 'also' or 'too'.": "Falsch. も (mo) bedeutet 'auch'.",
    }
}

L4_Q["In the sentence 「ぎんこうは　9じから　3じまでです」 (Ginkou wa 9-ji kara 3-ji made desu), the word から (kara) means 'until' and the word まで (made) means 'from'."] = {
    "q": "Im Satz 「ぎんこうは　9じから　3じまでです」 (Ginkou wa 9-ji kara 3-ji made desu) bedeutet から (kara) 'bis' und まで (made) 'von'.",
    "e": "Es ist umgekehrt. から (kara) bedeutet 'von' (Startpunkt) und まで (made) bedeutet 'bis' (Endpunkt). 9じから 3じまで (9-ji kara 3-ji made) bedeutet 'von 9:00 bis 3:00'.",
    "fb": {}
}

L4_Q["Based on the conversation, what is Ito-san's (伊藤さん) work schedule?"] = {
    "q": "Basierend auf dem Gespräch, wie ist Ito-sans (伊藤さん) Arbeitszeit?",
    "e": "Im Dialog sagt Ito-san nach Mori-sans Erklärung: 'Watashi wa kuji kara rokuji made hatarakimasu' (わたしは 九時から 六時まで 働きます) = 'Ich arbeite von neun bis sechs.' Die Partikeln 'kara' (von) und 'made' (bis) geben Start- und Endzeit an.",
    "fb": {
        "Incorrect. This is Mori-san's (森さん) work schedule, from 8:00 to 5:00.": "Falsch. Das ist Mori-sans (森さん) Arbeitszeit, von 8:00 bis 5:00.",
        "Correct! Ito-san says she works from 9:00 (kuji) to 6:00 (rokuji).": "Richtig! Ito-san sagt, sie arbeitet von 9:00 (kuji) bis 6:00 (rokuji).",
        "Incorrect. This refers to the lunch break (hiruyasumi) time mentioned in the dialogue.": "Falsch. Das bezieht sich auf die Mittagspause (hiruyasumi), die im Dialog erwähnt wird.",
        "Incorrect. 6:30 (Rokuji han) is the time Mori-san gets up in the morning.": "Falsch. 6:30 (Rokuji han) ist die Zeit, zu der Mori-san morgens aufsteht.",
    }
}

L4_Q["If it is currently 8:30, how do you say the time in Japanese?"] = {
    "q": "Wenn es gerade 8:30 ist, wie sagt man die Uhrzeit auf Japanisch?",
    "e": "Im Japanischen wird 'halb nach' der Stunde durch Hinzufügen von 半 (han) nach der Stundenziffer (ji) ausgedrückt. 8:30 ist Hachiji-han (八時半).",
    "fb": {
        "Correct! 'Han' (半) means half past the hour.": "Richtig! 'Han' (半) bedeutet halb nach der Stunde.",
        "Incorrect. 'Fun' (分) is used for minutes, but you need a specific number or 'han' for half.": "Falsch. 'Fun' (分) wird für Minuten verwendet, aber man braucht eine bestimmte Zahl oder 'han' für halb.",
        "Incorrect. 'Mae' (前) means 'before', which is not the standard way to say 8:30 in this lesson.": "Falsch. 'Mae' (前) bedeutet 'vor', was in dieser Lektion nicht die Standardform für 8:30 ist.",
        "Incorrect. This means 8:15.": "Falsch. Das bedeutet 8:15.",
    }
}

L4_Q["Choose the correct particle to complete the sentence: わたしは 毎日 7時___ 起きます。(Watashi wa mainichi shichiji ___ okimasu.)"] = {
    "q": "Wählen Sie die richtige Partikel: わたしは 毎日 7時___ 起きます。(Watashi wa mainichi shichiji ___ okimasu.)",
    "e": "Die Partikel に (ni) folgt einem Nomen, das eine bestimmte Zeit angibt (wie 7 Uhr), wenn das Verb ein Handlungsverb wie おきます (okimasu - aufstehen) ist.",
    "fb": {
        "Incorrect. 'O' is an object marker, not used for time.": "Falsch. 'O' ist ein Objektmarker, nicht für Zeitangaben.",
        "Correct! The particle 'ni' is used after specific time nouns to indicate when an action happens.": "Richtig! Die Partikel 'ni' wird nach bestimmten Zeitnomen verwendet, um anzugeben, wann eine Handlung stattfindet.",
        "Incorrect. 'E' is a direction particle.": "Falsch. 'E' ist eine Richtungspartikel.",
        "Incorrect. 'De' indicates a location of action or a means, not a specific time point.": "Falsch. 'De' gibt den Handlungsort oder ein Mittel an, nicht einen bestimmten Zeitpunkt.",
    }
}

L4_Q["Answer the question in the negative: きのう 勉強しましたか。(Kinou benkyou shimashita ka?)"] = {
    "q": "Beantworten Sie die Frage verneinend: きのう 勉強しましたか。(Kinou benkyou shimashita ka?)",
    "e": "Um die vergangene Verneinungsform eines Verbs zu bilden, ändert man die ~ます (~masu)-Endung zu ~ませんでした (~masen deshita). Da 'kinou' (gestern) verwendet wurde, ist die vergangene Verneinung erforderlich.",
    "fb": {
        "Incorrect. This is the present/future negative form.": "Falsch. Das ist die gegenwärtige/zukünftige Verneinungsform.",
        "Incorrect. This is the past affirmative form.": "Falsch. Das ist die vergangene bejahende Form.",
        "Correct! '~masen deshita' is the polite past negative form.": "Richtig! '~masen deshita' ist die höfliche vergangene Verneinungsform.",
        "Incorrect. 'Hai' (Yes) does not match 'shimasen' (don't).": "Falsch. 'Hai' (Ja) passt nicht zu 'shimasen' (nicht).",
    }
}

L4_Q["Complete the sentence about office hours: 郵便局は 9時___ 5時___ です。(Yuubinkyoku wa kuji ___ goji ___ desu.)"] = {
    "q": "Vervollständigen Sie den Satz über Öffnungszeiten: 郵便局は 9時___ 5時___ です。(Yuubinkyoku wa kuji ___ goji ___ desu.)",
    "e": "～から (kara) bedeutet 'von' und ～まで (made) bedeutet 'bis'. Zusammen drücken sie einen Zeitraum aus.",
    "fb": {
        "Correct! 'Kara' means from and 'made' means until/to.": "Richtig! 'Kara' bedeutet von und 'made' bedeutet bis.",
        "Incorrect. This would mean 'Until 9:00, from 5:00'.": "Falsch. Das würde 'Bis 9:00, von 5:00' bedeuten.",
        "Incorrect. 'Ni' marks a specific point, but 'kara/made' is used for a range.": "Falsch. 'Ni' markiert einen bestimmten Punkt, aber 'kara/made' wird für einen Bereich verwendet.",
        "Incorrect. 'To' means 'and'.": "Falsch. 'To' bedeutet 'und'.",
    }
}

L4_Q["If someone tells you they work from 8:00 AM until 11:00 PM every day, what is the most sympathetic response?"] = {
    "q": "Wenn jemand Ihnen erzählt, dass er jeden Tag von 8:00 bis 23:00 Uhr arbeitet, was ist die mitfühlendste Antwort?",
    "e": "たいへんですね (Taihen desu ne) ist ein häufiger Ausdruck, um Mitgefühl zu zeigen, wenn jemand eine schwierige, anstrengende Situation beschreibt.",
    "fb": {
        "Incorrect. While polite, it's just 'Is that so?' and lacks the sympathy required for such a long schedule.": "Falsch. Zwar höflich, aber nur 'Ach so?' ohne das nötige Mitgefühl für so einen langen Arbeitstag.",
        "Incorrect. This means 'That's good/nice', which is inappropriate for a stressful schedule.": "Falsch. Das bedeutet 'Das ist schön', was für einen stressigen Arbeitsplan unangemessen ist.",
        "Correct! This means 'That's tough' or 'That's hard on you'.": "Richtig! Das bedeutet 'Das ist hart' oder 'Das ist anstrengend'.",
        "Incorrect. This means 'I understood'.": "Falsch. Das bedeutet 'Ich habe verstanden'.",
    }
}

L4_Q["The Japanese word for 'Wednesday' is 土曜日 (Doyoubi)."] = {
    "q": "Das japanische Wort für 'Mittwoch' ist 土曜日 (Doyoubi).",
    "e": "Doyoubi (土曜日) ist Samstag. Mittwoch ist Suiyoubi (水曜日).",
    "fb": {}
}

L4_Q["The word 午後 (gogo) refers to 'P.M.' or 'afternoon'."] = {
    "q": "Das Wort 午後 (gogo) bezieht sich auf 'nachmittags' oder 'PM'.",
    "e": "Korrekt. Gozen (午前) ist vormittags (AM) und Gogo (午後) ist nachmittags (PM).",
    "fb": {}
}

L4_Q["The phrase 'hiruyasumi' (昼休み) specifically refers to a lunch break."] = {
    "q": "Der Ausdruck 'hiruyasumi' (昼休み) bezeichnet speziell eine Mittagspause.",
    "e": "Korrekt. 'Hiru' (Mittag/Tageszeit) + 'yasumi' (Ruhe/Pause) ergibt das Wort für Mittagspause.",
    "fb": {}
}

L4_Q["Match the Japanese locations to their English translations."] = {
    "q": "Ordnen Sie die japanischen Orte den deutschen Übersetzungen zu.",
    "e": "Die Zuordnungen sind: 銀行 (ginkou - Bank), 図書館 (toshokan - Bibliothek), 美術館 (bijutsukan - Kunstmuseum) und 郵便局 (yuubinkyoku - Post).",
    "fb": {
        "bank": "Bank",
        "library": "Bibliothek",
        "art museum": "Kunstmuseum",
        "post office": "Post",
    }
}

L4_Q["Look at the time: 10:30 PM. How would you describe this current time in Japanese?"] = {
    "q": "Sehen Sie die Uhrzeit: 22:30 (10:30 PM). Wie beschreiben Sie diese Zeit auf Japanisch?",
    "e": "Für abendliche Zeitangaben verwendet man Gogo (ごご - PM) + [Stunde]ji (時) + Han (半 - halb) oder Sanjuppun (三十分 - 30 Minuten) + Desu (です).",
    "fb": {
        "Gozen (ごぜん) means AM. For 10:30 PM, you need Gogo (ごご).": "Gozen (ごぜん) bedeutet vormittags. Für 22:30 braucht man Gogo (ごご).",
        "Correct! Gogo (ごご) is PM, Juuji (十時) is 10 o'clock, and Han (半) is half past.": "Richtig! Gogo (ごご) ist nachmittags, Juuji (十時) ist 10 Uhr und Han (半) ist halb.",
        "Juppun (十分) means 10 minutes. 10:30 requires 'han' (半) or 'sanjuppun' (三十分).": "Juppun (十分) bedeutet 10 Minuten. 10:30 erfordert 'han' (半) oder 'sanjuppun' (三十分).",
        "Kuji (九時) is 9 o'clock. You need Juuji (十時) for 10 o'clock.": "Kuji (九時) ist 9 Uhr. Man braucht Juuji (十時) für 10 Uhr.",
    }
}

L4_Q["""Choose the correct verb form to complete this dialogue about yesterday:
Tanaka: 'Kinou (Yesterday) benkyou shimashita ka?'
Sato: 'Iie, ___________.'"""] = {
    "q": """Wählen Sie die richtige Verbform für diesen Dialog über gestern:
Tanaka: 'Kinou (Gestern) benkyou shimashita ka?'
Sato: 'Iie, ___________.'""",
    "e": "Wenn man eine Frage in der Vergangenheit (~mashita ka) mit 'Nein' beantwortet, muss das Verb in der vergangenen Verneinungsform konjugiert werden: ~masen deshita (~ませんでした).",
    "fb": {
        "This is the non-past negative (present/future). You need the past negative form.": "Das ist die Gegenwarts-/Zukunftsverneinung. Man braucht die vergangene Verneinungsform.",
        "This is the past affirmative. Since Sato said 'Iie' (No), a negative form is required.": "Das ist die vergangene Bejahung. Da Sato 'Iie' (Nein) sagte, ist eine Verneinungsform nötig.",
        "Correct! ~Masen deshita (~ませんでした) is the polite past negative form.": "Richtig! ~Masen deshita (~ませんでした) ist die höfliche vergangene Verneinungsform.",
        "This is the polite present/future form. It does not match the past context or the 'No' response.": "Das ist die höfliche Gegenwarts-/Zukunftsform. Sie passt nicht zum Vergangenheitskontext oder zur 'Nein'-Antwort.",
    }
}

L4_Q["Select the correct particle sequence for this sentence: 'Watashi wa asa hachiji ( ) kuji ( ) hatarakimasu.' (I work from 8:00 to 9:00 in the morning.)"] = {
    "q": "Wählen Sie die richtige Partikelfolge: 'Watashi wa asa hachiji ( ) kuji ( ) hatarakimasu.' (Ich arbeite morgens von 8:00 bis 9:00.)",
    "e": "Die Struktur [Zeit A] kara [Zeit B] made (～から～まで) drückt eine Zeitspanne vom Start- zum Endpunkt aus.",
    "fb": {
        "The particle 'ni' marks a specific point in time, not a range from start to finish.": "Die Partikel 'ni' markiert einen bestimmten Zeitpunkt, keinen Bereich von Anfang bis Ende.",
        "Perfect! Kara (から) means 'from' and Made (まで) means 'until/to'.": "Perfekt! Kara (から) bedeutet 'von' und Made (まで) bedeutet 'bis'.",
        "This would mean 'until 8:00 from 9:00', which is logically backwards.": "Das würde 'bis 8:00 von 9:00' bedeuten, was logisch verkehrt ist.",
        "While 'made' is correct for 'until', 'ni' does not mean 'from'.": "Obwohl 'made' korrekt für 'bis' ist, bedeutet 'ni' nicht 'von'.",
    }
}

L4_Q["""Read the following situation and choose the best conversational response:
A: 'Mori-san wa maiasa yo-ji ni okimasu. Juu-ji ni nemasu. Mainichi hatarakimasu.'
B: '___________'"""] = {
    "q": """Lesen Sie die Situation und wählen Sie die beste Gesprächsantwort:
A: 'Mori-san wa maiasa yo-ji ni okimasu. Juu-ji ni nemasu. Mainichi hatarakimasu.'
B: '___________'""",
    "e": "Taihen desu ne (たいへんですね) ist der Standardausdruck, um Mitgefühl zu zeigen, wenn jemand eine schwierige oder anstrengende Situation beschreibt.",
    "fb": {
        "While this means 'I see' or 'That's right', it's a bit too neutral for such an intense schedule.": "Das bedeutet zwar 'Ach so' oder 'Stimmt', ist aber etwas zu neutral für so einen intensiven Zeitplan.",
        "Correct! This phrase is used to show sympathy when someone has a difficult or busy situation.": "Richtig! Dieser Ausdruck wird verwendet, um Mitgefühl bei einer schwierigen oder geschäftigen Situation zu zeigen.",
        "This means 'Please' and is used for requests, not as a reaction to a schedule.": "Das bedeutet 'Bitte' und wird für Bitten verwendet, nicht als Reaktion auf einen Zeitplan.",
        "This means 'Good night'. It doesn't fit as a reaction to hearing someone's daily routine.": "Das bedeutet 'Gute Nacht'. Es passt nicht als Reaktion auf den Tagesablauf einer Person.",
    }
}

L4_Q["How do you correctly ask: 'What day of the week is the library's holiday (day off)?'"] = {
    "q": "Wie fragt man korrekt: 'An welchem Wochentag hat die Bibliothek geschlossen?'",
    "e": "Um nach dem Wochentag zu fragen, verwendet man Nan-youbi (なんようび). Das Wort für Bibliothek ist Toshokan (としょかん) und Ruhetag ist Yasumi (やすみ).",
    "fb": {
        "Nan-ji (なんじ) asks 'what time'. You need 'what day of the week'.": "Nan-ji (なんじ) fragt 'wie spät'. Man braucht 'welcher Wochentag'.",
        "Correct! Nan-youbi (なんようび) is used to ask for the day of the week.": "Richtig! Nan-youbi (なんようび) wird verwendet, um nach dem Wochentag zu fragen.",
        "Bijutsukan (びじゅつかん) means Art Museum. The question asked for Library (としょかん).": "Bijutsukan (びじゅつかん) bedeutet Kunstmuseum. Gefragt war nach Bibliothek (としょかん).",
        "This asks 'What day of the week does the library work?', which is unnatural phrasing for a facility's schedule.": "Das fragt 'An welchem Tag arbeitet die Bibliothek?', was eine unnatürliche Formulierung für den Öffnungsplan einer Einrichtung ist.",
    }
}

L4_Q["In the sentence 'Maiasa (まいあさ) shichi-ji ni okimasu,' you can optionally add the particle 'ni' (に) after the word 'Maiasa' to be more formal."] = {
    "q": "Im Satz 'Maiasa (まいあさ) shichi-ji ni okimasu' kann man optional die Partikel 'ni' (に) nach 'Maiasa' hinzufügen, um formeller zu sein.",
    "e": "Falsch. Relative Zeitwörter (wie maiasa - jeden Morgen, kinou - gestern, ashita - morgen) nehmen NICHT die Partikel 'ni'. 'Ni' wird nur mit konkreten Uhrzeiten wie 'shichi-ji' (7 Uhr) oder bestimmten Wochentagen verwendet.",
    "fb": {}
}

L4_Q["The Japanese word 'Yasumi' (やすみ) is a noun meaning 'holiday' or 'break', while 'Yasumimasu' (やすみます) is the verb form meaning 'to rest' or 'to take a day off'."] = {
    "q": "Das japanische Wort 'Yasumi' (やすみ) ist ein Nomen für 'Feiertag' oder 'Pause', während 'Yasumimasu' (やすみます) die Verbform für 'ruhen' oder 'einen Tag freinehmen' ist.",
    "e": "Korrekt. In Lektion 4 unterscheiden wir zwischen dem Nomen 'Yasumi' (z.B. 'Ginkou no yasumi' - der Ruhetag der Bank) und dem Verb 'Yasumimasu' (z.B. 'Doyoubi ni yasumimasu' - Ich ruhe am Samstag).",
    "fb": {}
}

L4_Q["The sentence 'Kesa (けさ) kuji ni hatarakimashita' translates to 'I worked at 9:00 this morning' and is grammatically correct."] = {
    "q": "Der Satz 'Kesa (けさ) kuji ni hatarakimashita' bedeutet 'Ich habe heute Morgen um 9:00 gearbeitet' und ist grammatisch korrekt.",
    "e": "Korrekt. 'Kesa' (heute Morgen) bezieht sich auf eine vergangene Zeit (vorausgesetzt, es ist jetzt Nachmittag oder Abend), daher ist die Vergangenheitsform 'hatarakimashita' korrekt mit dem Zeitmarker 'ni' verwendet.",
    "fb": {}
}

L4_Q["Match the Japanese public institutions to their English meanings."] = {
    "q": "Ordnen Sie die japanischen öffentlichen Einrichtungen den deutschen Bedeutungen zu.",
    "e": "Das sind häufige Orte-Vokabeln in Lektion 4: Ginkou (ぎんこう - Bank), Yuubinkyoku (ゆうびんきょく - Post), Toshokan (としょかん - Bibliothek) und Bijutsukan (びじゅつかん - Kunstmuseum).",
    "fb": {
        "Bank": "Bank",
        "Post Office": "Post",
        "Library": "Bibliothek",
        "Art Museum": "Kunstmuseum",
    }
}

# ═══════════════════════════════════════════════════════════════════════
# LEKTION 5 – Gehen und Kommen (kompakte Form)
# ═══════════════════════════════════════════════════════════════════════

L5_Q = QUIZ_TRANSLATIONS

L5_Q["Select the correct verb to complete this sentence: 'Watashi wa uchi e _______.' (I am returning home.)"] = {
    "q": "Wählen Sie das richtige Verb: 'Watashi wa uchi e _______.' (Ich gehe nach Hause zurück.)",
    "e": "In Lektion 5 lernen wir drei Bewegungsverben: ikimasu (いきます - gehen), kimasu (きます - kommen) und kaerimasu (かえります - zurückkehren). 'Uchi' (Zuhause) wird natürlich mit 'kaerimasu' kombiniert.",
    "fb": {
        "Ikimasu means 'to go'. While grammatically possible, Japanese speakers usually use a specific verb for returning home.": "Ikimasu bedeutet 'gehen'. Zwar grammatisch möglich, aber Japaner verwenden normalerweise ein spezifisches Verb für die Heimkehr.",
        "Kimasu means 'to come'. This wouldn't be used to describe going back to your own home.": "Kimasu bedeutet 'kommen'. Das würde nicht für die Rückkehr nach Hause verwendet.",
        "Correct! Kaerimasu (to return/go home) is the standard verb used when going back to your house or home country.": "Richtig! Kaerimasu (zurückkehren) ist das Standardverb für die Rückkehr nach Hause oder ins Heimatland.",
        "Ohanami means 'cherry blossom viewing' and is a noun/event, not a verb of movement.": "Ohanami bedeutet 'Kirschblütenschau' und ist ein Nomen/Ereignis, kein Bewegungsverb.",
    }
}

L5_Q["Most transportation methods use the particle 'de' (e.g., 'basu de' - by bus). Which of the following is the exception and does NOT use 'de' to mean 'on foot'?"] = {
    "q": "Die meisten Transportmittel verwenden die Partikel 'de' (z.B. 'basu de' - mit dem Bus). Welche der folgenden ist die Ausnahme und verwendet NICHT 'de' für 'zu Fuss'?",
    "e": "Während Fahrzeuge wie densha (でんしゃ - Zug) oder takushii (タクシー - Taxi) die Partikel 'de' (で) für das Transportmittel verwenden, ist 'aruite' (あるいて - zu Fuss) die te-Form des Verbs 'aruku' (gehen) und nimmt kein 'de'.",
    "fb": {
        "Jitensha (bicycle) uses 'de' to indicate the means of transport.": "Jitensha (Fahrrad) verwendet 'de' für das Transportmittel.",
        "Correct! 'Aruite' (walking/on foot) is used alone without the particle 'de' to describe the method of travel.": "Richtig! 'Aruite' (zu Fuss) wird allein ohne die Partikel 'de' verwendet.",
        "Chikatetsu (subway) follows the standard 'noun + de' pattern.": "Chikatetsu (U-Bahn) folgt dem Standard-Muster 'Nomen + de'.",
        "Shinkansen (bullet train) follows the standard 'noun + de' pattern.": "Shinkansen (Schnellzug) folgt dem Standard-Muster 'Nomen + de'.",
    }
}

L5_Q["Tanaka-san asks: '_______ Nihon e kimasu ka?' (When are you coming to Japan?). Which question word fits the blank?"] = {
    "q": "Tanaka-san fragt: '_______ Nihon e kimasu ka?' (Wann kommen Sie nach Japan?). Welches Fragewort passt in die Lücke?",
    "e": "'Itsu' (いつ) ist das allgemeine Fragewort für 'wann'. Es wird für Fragen nach Daten, Uhrzeiten oder Zeiträumen verwendet.",
    "fb": {
        "Correct! Itsu (いつ) means 'when' and is used to ask about time or dates.": "Richtig! Itsu (いつ) bedeutet 'wann' und wird für Fragen nach Zeit oder Daten verwendet.",
        "Doko (どこ) means 'where'. Since the destination 'Nihon' (Japan) is already mentioned, 'where' does not fit here.": "Doko (どこ) bedeutet 'wo'. Da das Ziel 'Nihon' (Japan) bereits genannt ist, passt 'wo' hier nicht.",
        "Dare (だれ) means 'who'. This doesn't fit the context of the travel sentence.": "Dare (だれ) bedeutet 'wer'. Das passt nicht zum Kontext des Reisesatzes.",
        "Nan (なん) means 'what'. While it is used in 'nan-ji' (what time), by itself it doesn't mean 'when'.": "Nan (なん) bedeutet 'was'. Obwohl es in 'nan-ji' (wie spät) verwendet wird, bedeutet es allein nicht 'wann'.",
    }
}

L5_Q["In the sentence 「わたしは しんかんせん [ ? ] おおさかへ いきます」(Watashi wa shinkansen [ ? ] Oosaka e ikimasu - I go to Osaka by Shinkansen), which particle correctly fills the blank to indicate the means of transport?"] = {
    "q": "Im Satz 「わたしは しんかんせん [ ? ] おおさかへ いきます」(Watashi wa shinkansen [ ? ] Oosaka e ikimasu - Ich fahre mit dem Shinkansen nach Osaka), welche Partikel füllt die Lücke korrekt für das Transportmittel?",
    "e": "Die Partikel 「で」 (de) folgt einem Fahrzeug oder Transportmittel und bedeutet 'mit' (z.B. 「くるまで」 kurumade - mit dem Auto). Die Partikel 「へ」 (he/e) zeigt die Richtung zu einem Ort an.",
    "fb": {
        "「に」 (ni) is used for specific times or destinations, but not for the means of transport in this context.": "「に」 (ni) wird für bestimmte Zeiten oder Ziele verwendet, aber nicht für Transportmittel in diesem Kontext.",
        "Correct! The particle 「で」 (de) is used to indicate the means or method of transportation, such as 「でんしゃで」 (densha de - by train).": "Richtig! Die Partikel 「で」 (de) gibt das Transportmittel an, z.B. 「でんしゃで」 (densha de - mit dem Zug).",
        "「を」 (wo) is the direct object marker and is not used to indicate transport methods.": "「を」 (wo) ist der Objektmarker und wird nicht für Transportmittel verwendet.",
        "「へ」 (he/e) is used to indicate the direction or destination (like Osaka), not the vehicle used.": "「へ」 (he/e) zeigt die Richtung oder das Ziel an (wie Osaka), nicht das verwendete Fahrzeug.",
    }
}

L5_Q["To ask 'When are you going to the bank?', the correct word order and usage of the interrogative 'when' is 「いつ ぎんこうへ いきますか」 (Itsu ginkou e ikimasuka)."] = {
    "q": "Um 'Wann gehen Sie zur Bank?' zu fragen, ist die korrekte Wortstellung 「いつ ぎんこうへ いきますか」 (Itsu ginkou e ikimasuka).",
    "e": "Wahr. 「いつ」 (itsu - wann) wird am Satzanfang oder vor der Verbphrase verwendet. Anders als bei konkreten Daten oder Uhrzeiten (wie 'Montag' oder '3 Uhr') braucht 「いつ」 normalerweise keine Partikel 「に」 danach.",
    "fb": {}
}

L5_Q["If you are going to the store alone, you should use the particle 「と」 (to) and say 「ひとりと いきます」 (Hitori to ikimasu)."] = {
    "q": "Wenn Sie allein zum Laden gehen, sollten Sie die Partikel 「と」 (to) verwenden und 「ひとりと いきます」 (Hitori to ikimasu) sagen.",
    "e": "Falsch. Während 「と」 (to) für 'mit' einer Person verwendet wird (z.B. 「ともだちと」 tomodachi to - mit einem Freund), ist der Ausdruck für 'allein' 「ひとりで」 (hitori de). Man verwendet 「と」 nicht, wenn man etwas allein tut.",
    "fb": {}
}

L5_Q["According to the conversation, how will Nakamura and Ogawa travel to the zoo (doubutsuen)?"] = {
    "q": "Laut dem Gespräch, wie werden Nakamura und Ogawa zum Zoo (doubutsuen) fahren?",
    "e": "Im Dialog beantwortet Nakamura die Frage 'Nan de ikimasu ka' (Wie fahrt ihr?) mit 'Densha de ikimasu' (Wir fahren mit dem Zug) und erwähnt dann 'Eki kara basu de juppun desu' (Vom Bahnhof sind es zehn Minuten mit dem Bus).",
    "fb": {
        "Correct! Nakamura says they will go by train (densha) and then take a bus (basu) from the station.": "Richtig! Nakamura sagt, sie fahren mit dem Zug (densha) und nehmen dann einen Bus (basu) vom Bahnhof.",
        "Incorrect. Nakamura specifies public transportation, not a car (kuruma).": "Falsch. Nakamura nennt öffentliche Verkehrsmittel, kein Auto (kuruma).",
        "Incorrect. While they meet at the station, they use a train and bus rather than walking (aruite) the whole way.": "Falsch. Obwohl sie sich am Bahnhof treffen, benutzen sie Zug und Bus statt den ganzen Weg zu Fuss zu gehen (aruite).",
        "Incorrect. A taxi (takushii) is not mentioned in the dialogue.": "Falsch. Ein Taxi (takushii) wird im Dialog nicht erwähnt.",
    }
}

L5_Q["Choose the correct particle to complete the sentence: らいしゅう (Raishuu) ぎんこう (ginkou) [ ] いきます (ikimasu)."] = {
    "q": "Wählen Sie die richtige Partikel: らいしゅう (Raishuu) ぎんこう (ginkou) [ ] いきます (ikimasu).",
    "e": "Die Partikel へ (e) folgt einem Ortsnomen und zeigt die Richtung oder das Ziel an, wenn Bewegungsverben wie いきます (ikimasu - gehen), きます (kimasu - kommen) und かえります (kaerimasu - zurückkehren) verwendet werden.",
    "fb": {
        "で (de) is used for means of transportation or location of action, not destination.": "で (de) wird für Transportmittel oder Handlungsort verwendet, nicht für das Ziel.",
        "Correct! へ (e) is used with movement verbs like いきます (ikimasu) to indicate destination.": "Richtig! へ (e) wird mit Bewegungsverben wie いきます (ikimasu) für das Ziel verwendet.",
        "と (to) is used to mean 'with' a person.": "と (to) wird für 'mit' einer Person verwendet.",
        "を (o) marks the direct object, which is not used for destinations with movement verbs.": "を (o) markiert das direkte Objekt, was nicht für Ziele bei Bewegungsverben verwendet wird.",
    }
}

L5_Q["Fill in the blank: なんで (Nan de) きょうと (Kyouto) へ (e) いきますか (ikimasu ka). ... [ ] で (de) いきます (ikimasu)."] = {
    "q": "Füllen Sie die Lücke: なんで (Nan de) きょうと (Kyouto) へ (e) いきますか (ikimasu ka). ... [ ] で (de) いきます (ikimasu).",
    "e": "Die Partikel で (de) gibt das Mittel oder Werkzeug an. Bei Bewegungsverben bezeichnet sie das Transportmittel (z.B. Shinkansen de ikimasu).",
    "fb": {
        "ともだち (tomodachi) is a person. You would use と (to) for people, not で (de).": "ともだち (tomodachi) ist eine Person. Man verwendet と (to) für Personen, nicht で (de).",
        "Correct! しんかんせん (shinkansen - bullet train) is a means of transportation used with the particle で (de).": "Richtig! しんかんせん (shinkansen - Schnellzug) ist ein Transportmittel, das mit der Partikel で (de) verwendet wird.",
        "きょねん (kyonen) means 'last year', which is a time expression.": "きょねん (kyonen) bedeutet 'letztes Jahr' — ein Zeitausdruck.",
        "ひとりで (hitori de) already includes a particle and means 'alone'; it doesn't fit before another で (de).": "ひとりで (hitori de) enthält bereits eine Partikel und bedeutet 'allein'; es passt nicht vor ein weiteres で (de).",
    }
}

L5_Q["Select the correct phrase to complete the question: [ ] ともだち (tomodachi) と (to) にほん (Nihon) へ (e) きましたか (kimashita ka)."] = {
    "q": "Wählen Sie den richtigen Ausdruck: [ ] ともだち (tomodachi) と (to) にほん (Nihon) へ (e) きましたか (kimashita ka).",
    "e": "いつ (itsu) ist das Fragewort für 'wann'. Da die Antwort eine Zeitangabe ist ('letzten September'), ist 'itsu' das richtige Fragewort.",
    "fb": {
        "どこ (doko) means 'where'.": "どこ (doko) bedeutet 'wo'.",
        "だれ (dare) means 'who'. Since 'tomodachi' (friend) is already in the sentence, this doesn't fit.": "だれ (dare) bedeutet 'wer'. Da 'tomodachi' (Freund) bereits im Satz steht, passt das nicht.",
        "Correct! いつ (itsu) means 'when' and is used to ask about time without needing the particle に (ni).": "Richtig! いつ (itsu) bedeutet 'wann' und wird ohne die Partikel に (ni) verwendet.",
        "なん (nan) means 'what'.": "なん (nan) bedeutet 'was'.",
    }
}

L5_Q["Choose the most appropriate response to this invitation: いっしょに (issho ni) こうえん (kouen) へ (e) いきませんか (ikimasen ka)."] = {
    "q": "Wählen Sie die passendste Antwort auf diese Einladung: いっしょに (issho ni) こうえん (kouen) へ (e) いきませんか (ikimasen ka).",
    "e": "Bei einer Einladung mit 〜ませんか (masen ka) zeigt die Antwort いいですね (ii desu ne - Das klingt gut) oder ええ (ee - Ja/Klar) Begeisterung und Zustimmung.",
    "fb": {
        "Correct! This means 'That sounds nice' and shows agreement to a suggestion.": "Richtig! Das bedeutet 'Das klingt gut' und zeigt Zustimmung zu einem Vorschlag.",
        "さようなら (Sayounara) means 'Goodbye'.": "さようなら (Sayounara) bedeutet 'Auf Wiedersehen'.",
        "This is used for making requests, not usually for accepting invitations to go somewhere.": "Das wird für Bitten verwendet, normalerweise nicht um Einladungen anzunehmen.",
        "This is used to apologize or get attention, though it can start a refusal, 'Ii desu ne' is the standard lesson 5 positive response.": "Das wird zum Entschuldigen oder Aufmerksamkeit-Erregen verwendet. Obwohl es eine Ablehnung einleiten kann, ist 'Ii desu ne' die Standard-Positivantwort in Lektion 5.",
    }
}

L5_Q["Identify the correct sentence structure for: 'I return home alone.'"] = {
    "q": "Identifizieren Sie die korrekte Satzstruktur für: 'Ich gehe allein nach Hause.'",
    "e": "Um auszudrücken, dass man etwas 'mit' jemandem tut, verwendet man [Person] と (to). Der Ausdruck für 'allein' ist jedoch die feste Wendung ひとりで (hitori de).",
    "fb": {
        "We use ひとりで (hitori de) for 'alone', not ひとりと (hitori to).": "Wir verwenden ひとりで (hitori de) für 'allein', nicht ひとりと (hitori to).",
        "Correct! ひとりで (hitori de) is the fixed expression for doing something alone.": "Richtig! ひとりで (hitori de) ist die feste Wendung für 'etwas allein tun'.",
        "いきまず (ikimasu) means 'to go'. 'To return home' specifically uses かえります (kaerimasu).": "いきます (ikimasu) bedeutet 'gehen'. Für 'nach Hause zurückkehren' verwendet man speziell かえります (kaerimasu).",
        "This is grammatically incorrect for expressing 'alone'.": "Das ist grammatisch falsch für den Ausdruck 'allein'.",
    }
}

L5_Q["To say you are going somewhere 'on foot', you should say あるいて (aruite) and you do NOT add the particle で (de)."] = {
    "q": "Um zu sagen, dass man 'zu Fuss' irgendwohin geht, sagt man あるいて (aruite) und fügt NICHT die Partikel で (de) hinzu.",
    "e": "Korrekt. Während Fahrzeuge die Partikel で (de) nehmen (z.B. basu de), ist あるいて (aruite) die te-Form des Verbs 'gehen' und funktioniert als Adverb für 'zu Fuss'. で (de) hinzuzufügen (aruite de) ist ein häufiger Fehler.",
    "fb": {}
}

L5_Q["In the sentence 'Senshuu (last week) Toukyou e ikimasu', the verb is in the correct tense."] = {
    "q": "Im Satz 'Senshuu (letzte Woche) Toukyou e ikimasu' ist das Verb in der richtigen Zeitform.",
    "e": "Falsch. せんしゅう (Senshuu) bedeutet 'letzte Woche', was in der Vergangenheit liegt. Daher sollte das Verb in der Vergangenheit stehen: いきました (ikimashita).",
    "fb": {}
}

L5_Q["Based on the lesson conversation, Nakamura and Ogawa are going to the zoo by bus the whole way from their starting point."] = {
    "q": "Laut dem Lektionsgespräch fahren Nakamura und Ogawa den ganzen Weg mit dem Bus zum Zoo.",
    "e": "Falsch. Nakamura sagt 'Densha de ikimasu' (Wir fahren mit dem Zug) und erklärt dann 'Eki kara basu de juppun' (Vom Bahnhof zehn Minuten mit dem Bus).",
    "fb": {}
}

L5_Q["Match the Japanese transportation terms to their English meanings."] = {
    "q": "Ordnen Sie die japanischen Transportbegriffe den deutschen Bedeutungen zu.",
    "e": "Das sind häufige Transportmittel aus Lektion 5: ちかてつ (chikatetsu - U-Bahn), じてんしゃ (jitensha - Fahrrad), きゅうこう (kyuukou - Schnellzug) und ふね (fune - Schiff/Boot).",
    "fb": {
        "Subway": "U-Bahn",
        "Bicycle": "Fahrrad",
        "Express train": "Schnellzug",
        "Ship / Boat": "Schiff / Boot",
    }
}

L5_Q["Choose the correct particles to complete this sentence: 「らいねん の ４がつ に ひこうき ___ 日本 ___ いきます。」 (Rainen no shigatsu ni hikouki ___ Nihon ___ ikimasu.)"] = {
    "q": "Wählen Sie die richtigen Partikeln: 「らいねん の ４がつ に ひこうき ___ 日本 ___ いきます。」 (Rainen no shigatsu ni hikouki ___ Nihon ___ ikimasu.)",
    "e": "Die Partikel で (de) gibt das Mittel (Transportmittel) an, und へ (e) zeigt die Richtung oder das Ziel der Bewegung.",
    "fb": {
        "Correct! 'de' indicates the means of transport (airplane) and 'e' indicates the direction/destination (Japan).": "Richtig! 'de' gibt das Transportmittel (Flugzeug) an und 'e' die Richtung/das Ziel (Japan).",
        "Incorrect. 'o' is for direct objects and 'ni' is for specific times or destinations, but 'de' is specifically required for the method of travel.": "Falsch. 'o' ist für direkte Objekte und 'ni' für bestimmte Zeiten, aber 'de' wird speziell für das Reisemittel benötigt.",
        "Incorrect. The order is wrong. The means (airplane) takes 'de' and the destination (Japan) takes 'e'.": "Falsch. Die Reihenfolge ist verkehrt. Das Mittel (Flugzeug) nimmt 'de' und das Ziel (Japan) nimmt 'e'.",
        "Incorrect. 'to' is used for people you go with, not for vehicles like airplanes.": "Falsch. 'to' wird für Personen verwendet, mit denen man reist, nicht für Fahrzeuge wie Flugzeuge.",
    }
}

L5_Q["Which question word appropriately fills the blank? 「___ 日本 へ きましたか。」「きょねん の ９がつ に きました。」 (___ Nihon e kimashita ka? Kyonen no kugatsu ni kimashita.)"] = {
    "q": "Welches Fragewort füllt die Lücke passend? 「___ 日本 へ きましたか。」「きょねん の ９がつ に きました。」 (___ Nihon e kimashita ka? Kyonen no kugatsu ni kimashita.)",
    "e": "いつ (itsu) ist das Fragewort für 'wann'. Da die Antwort eine bestimmte Zeit ist (letzten September), ist 'itsu' das richtige Fragewort.",
    "fb": {
        "Incorrect. 'doko' means 'where', but the answer is a time.": "Falsch. 'doko' bedeutet 'wo', aber die Antwort ist eine Zeitangabe.",
        "Incorrect. 'dare' means 'who', but the answer is a time.": "Falsch. 'dare' bedeutet 'wer', aber die Antwort ist eine Zeitangabe.",
        "Correct! 'itsu' means 'when' and is used to ask about dates or times.": "Richtig! 'itsu' bedeutet 'wann' und wird für Fragen nach Daten oder Zeiten verwendet.",
        "Incorrect. 'nan' means 'what'. While 'nan-gatsu' (what month) works, 'itsu' is the general interrogative for 'when'.": "Falsch. 'nan' bedeutet 'was'. Obwohl 'nan-gatsu' (welcher Monat) funktioniert, ist 'itsu' das allgemeine Fragewort für 'wann'.",
    }
}

L5_Q["Select the correct way to say 'I go to the supermarket alone' in Japanese."] = {
    "q": "Wählen Sie die korrekte Art, 'Ich gehe allein zum Supermarkt' auf Japanisch zu sagen.",
    "e": "Um auszudrücken, dass man etwas allein tut, verwendet man ひとりで (hitori de). Anders als bei Personen, wo man 'Person + と (to)' sagt, ist 'hitori de' ein adverbialer Ausdruck.",
    "fb": {
        "Correct! 'hitori de' means 'alone' or 'by oneself'.": "Richtig! 'hitori de' bedeutet 'allein' oder 'für sich'.",
        "Incorrect. 'hitotsu' is a counter for objects, not for people.": "Falsch. 'hitotsu' ist ein Zähler für Objekte, nicht für Personen.",
        "Incorrect. We do not say 'hitori to'. 'hitori de' is the fixed expression for alone.": "Falsch. Man sagt nicht 'hitori to'. 'hitori de' ist die feste Wendung für 'allein'.",
        "Incorrect. This means 'I go with a friend', not alone.": "Falsch. Das bedeutet 'Ich gehe mit einem Freund', nicht allein.",
    }
}

L5_Q["Based on the conversation, how are Nakamura, Tanaka, and Ogawa getting to the zoo from the station?"] = {
    "q": "Laut dem Gespräch, wie kommen Nakamura, Tanaka und Ogawa vom Bahnhof zum Zoo?",
    "e": "Im Gespräch sagt Nakamura ausdrücklich: 'Eki kara basu de juppun desu' (駅から バスで 十分です) = sie nehmen einen Bus vom Bahnhof.",
    "fb": {
        "Incorrect. Nakamura mentions it takes ten minutes, but by a specific vehicle.": "Falsch. Nakamura erwähnt zehn Minuten, aber mit einem bestimmten Fahrzeug.",
        "Incorrect. A taxi is not mentioned in the dialogue.": "Falsch. Ein Taxi wird im Dialog nicht erwähnt.",
        "Correct! Nakamura says 'Eki kara basu de juppun desu' (It's 10 minutes by bus from the station).": "Richtig! Nakamura sagt 'Eki kara basu de juppun desu' (Vom Bahnhof 10 Minuten mit dem Bus).",
        "Incorrect. Shinkansen is a bullet train; they are taking a bus from the local station.": "Falsch. Shinkansen ist ein Schnellzug; sie nehmen einen Bus vom lokalen Bahnhof.",
    }
}

L5_Q["Identify the correct response to complete this exchange: 「いつ かぞく と 日本 へ きますか。」 (Itsu kazoku to Nihon e kimasu ka?)"] = {
    "q": "Identifizieren Sie die korrekte Antwort: 「いつ かぞく と 日本 へ きますか。」 (Itsu kazoku to Nihon e kimasu ka?)",
    "e": "Die Frage lautet 'Wann' (itsu). 'Raigetsu' (nächsten Monat) ist ein Zeitausdruck. Beachten Sie, dass relative Zeitwörter wie 'raigetsu' oder 'ashita' nicht die Partikel 'ni' oder 'e' nehmen.",
    "fb": {
        "Correct! 'raigetsu' (next month) correctly answers the 'itsu' (when) question.": "Richtig! 'raigetsu' (nächsten Monat) beantwortet die 'itsu' (wann)-Frage korrekt.",
        "Incorrect. Time expressions like 'raigetsu' do not take the direction particle 'e'.": "Falsch. Zeitausdrücke wie 'raigetsu' nehmen nicht die Richtungspartikel 'e'.",
        "Incorrect. This answers 'Who with?', not 'When?'.": "Falsch. Das beantwortet 'Mit wem?', nicht 'Wann?'.",
        "Incorrect. This answers 'How?', not 'When?'.": "Falsch. Das beantwortet 'Wie?', nicht 'Wann?'.",
    }
}

L5_Q["When you say you are going somewhere on foot, the correct phrase is 「あるいて で いきます」 (aruite de ikimasu)."] = {
    "q": "Wenn man sagt, dass man zu Fuss irgendwohin geht, ist der korrekte Ausdruck 「あるいて で いきます」 (aruite de ikimasu).",
    "e": "Falsch. 'Aruite' (zu Fuss gehen) ist die Gerundiumform und wird als Adverb verwendet. Es nimmt NICHT die Partikel 'de'. Man sagt einfach 'Aruite ikimasu' (歩いて 行きます).",
    "fb": {}
}

L5_Q["In Japanese train terminology, a 「ふつう」 (futsuu) train is faster than a 「きゅうこう」 (kyuukou) train."] = {
    "q": "In der japanischen Zugterminologie ist ein 「ふつう」 (futsuu)-Zug schneller als ein 「きゅうこう」 (kyuukou)-Zug.",
    "e": "Falsch. 'Futsuu' (普通) bedeutet 'Nahverkehrs-' oder 'Bummelzug', der an jeder Station hält. 'Kyuukou' (急行) bedeutet 'Schnellzug', der schneller ist, weil er einige Stationen überspringt.",
    "fb": {}
}

L5_Q["According to the conversation, Ogawa-san and Nakamura-san are meeting at the station at 9:00."] = {
    "q": "Laut dem Gespräch treffen sich Ogawa-san und Nakamura-san um 9:00 am Bahnhof.",
    "e": "Wahr. Nakamura-san sagt 'Kuji ni eki e ikimasu' (九時に 駅へ 行きます) und Ogawa-san stimmt dieser Zeit zu.",
    "fb": {}
}

L5_Q["Match the Japanese time and place words to their correct English translations."] = {
    "q": "Ordnen Sie die japanischen Zeit- und Ortswörter den richtigen deutschen Übersetzungen zu.",
    "e": "Senshuu (letzte Woche) und Rainen (nächstes Jahr) sind relative Zeitausdrücke. Doubutsuen (Zoo) ist ein Ort und Chikatetsu (U-Bahn) ein Transportmittel.",
    "fb": {
        "Last week": "Letzte Woche",
        "Next year": "Nächstes Jahr",
        "Zoo": "Zoo",
        "Subway": "U-Bahn",
    }
}


# ═══════════════════════════════════════════════════════════════════════
# Conversation text bodies (L1 - need translation of English parts)
# ═══════════════════════════════════════════════════════════════════════

CONVERSATION_BODIES = {
    # L1 conversation
    """Sato: おはようございます。
  (Ohayou gozaimasu.)
  -> Good morning.

Yamada: おはようございます。佐藤さん、こちらは ミラーさんです。
  (Ohayou gozaimasu. Satou-san, kochira wa Miraa-san desu.)
  -> Good morning. Ms. Sato, this is Mr. Miller.

Miller: はじめまして。マイク・ミラーです。アメリカから きました。どうぞ よろしく おねがいします。
  (Hajimemashite. Maiku Miraa desu. Amerika kara kimashita. Douzo yoroshiku onegaishimasu.)
  -> How do you do? I am Mike Miller. I am from the United States of America. Nice to meet you.

Sato: 佐藤 けいこです。どうぞ よろしく。
  (Satou Keiko desu. Douzo yoroshiku.)
  -> I am Sato Keiko. Nice to meet you.""":

    """Sato: おはようございます。
  (Ohayou gozaimasu.)
  -> Guten Morgen.

Yamada: おはようございます。佐藤さん、こちらは ミラーさんです。
  (Ohayou gozaimasu. Satou-san, kochira wa Miraa-san desu.)
  -> Guten Morgen. Frau Sato, das ist Herr Miller.

Miller: はじめまして。マイク・ミラーです。アメリカから きました。どうぞ よろしく おねがいします。
  (Hajimemashite. Maiku Miraa desu. Amerika kara kimashita. Douzo yoroshiku onegaishimasu.)
  -> Freut mich. Ich bin Mike Miller. Ich komme aus den Vereinigten Staaten. Freut mich, Sie kennenzulernen.

Sato: 佐藤 けいこです。どうぞ よろしく。
  (Satou Keiko desu. Douzo yoroshiku.)
  -> Ich bin Sato Keiko. Freut mich.""",
}


# ═══════════════════════════════════════════════════════════════════════
# HAUPTSKRIPT
# ═══════════════════════════════════════════════════════════════════════

def translate_text(text, lookup_dict):
    """Sucht Übersetzung in lookup_dict, gibt Original zurück wenn nicht gefunden."""
    if text is None:
        return None
    return lookup_dict.get(text, text)


def translate_feedback(original_fb, quiz_trans):
    """Übersetzt Quiz-Feedback anhand der Übersetzungstabelle."""
    if original_fb is None:
        return None
    fb_map = quiz_trans.get("fb", {})
    return fb_map.get(original_fb, original_fb)


def translate_option_text(text):
    """Übersetzt True/False, lässt japanische Texte unverändert."""
    if text == "True":
        return "Wahr"
    if text == "False":
        return "Falsch"
    return text  # Japanese options stay unchanged


def main():
    app = create_app()
    with app.app_context():
        # 1. Kategorie erstellen
        existing = LessonCategory.query.filter_by(name="MNN Beginner I (Deutsch)").first()
        if existing:
            print(f"Kategorie 'MNN Beginner I (Deutsch)' existiert bereits (ID {existing.id}). Überspringe.")
            new_cat_id = existing.id
        else:
            new_cat = LessonCategory(name="MNN Beginner I (Deutsch)", description="Minna No Nihongo Beginner I — Deutsche Unterrichtssprache")
            db.session.add(new_cat)
            db.session.flush()
            new_cat_id = new_cat.id
            print(f"Kategorie 'MNN Beginner I (Deutsch)' erstellt (ID {new_cat_id})")

        # 2. Für jede Lektion: kopieren und übersetzen
        source_ids = [131, 132, 133, 134, 135]

        for src_id in source_ids:
            src = db.session.get(Lesson, src_id)
            if not src:
                print(f"Lektion {src_id} nicht gefunden, überspringe.")
                continue

            # Prüfen ob deutsche Version schon existiert
            de_title = LESSON_TITLES.get(src_id, src.title)
            existing_lesson = Lesson.query.filter_by(title=de_title).first()
            if existing_lesson:
                print(f"  Lektion '{de_title}' existiert bereits (ID {existing_lesson.id}), überspringe.")
                continue

            # Neue Lektion erstellen
            new_lesson = Lesson(
                title=de_title,
                description=src.description,  # descriptions are already in German
                lesson_type=src.lesson_type,
                category_id=new_cat_id,
                difficulty_level=src.difficulty_level,
                estimated_duration=src.estimated_duration,
                order_index=src.order_index,
                is_published=src.is_published,
                allow_guest_access=src.allow_guest_access,
                instruction_language='german',
                thumbnail_url=src.thumbnail_url,
                background_image_url=src.background_image_url,
                background_image_path=src.background_image_path,
                video_intro_url=src.video_intro_url,
                price=src.price,
                is_purchasable=src.is_purchasable,
            )
            db.session.add(new_lesson)
            db.session.flush()
            new_lesson_id = new_lesson.id
            print(f"  Lektion '{de_title}' erstellt (ID {new_lesson_id})")

            # Seiten kopieren
            src_pages = LessonPage.query.filter_by(lesson_id=src_id).order_by(LessonPage.page_number).all()
            for sp in src_pages:
                new_page = LessonPage(
                    lesson_id=new_lesson_id,
                    page_number=sp.page_number,
                    title=translate_text(sp.title, PAGE_TITLES),
                    description=sp.description,
                    page_type=sp.page_type,
                )
                db.session.add(new_page)
            print(f"    {len(src_pages)} Seiten kopiert")

            # Content kopieren
            src_contents = LessonContent.query.filter_by(lesson_id=src_id).order_by(LessonContent.page_number, LessonContent.order_index).all()
            content_count = 0
            quiz_count = 0

            for sc in src_contents:
                # Titel übersetzen
                new_title = sc.title
                if sc.title and sc.title in CONTENT_TITLES:
                    new_title = CONTENT_TITLES[sc.title]
                elif sc.title and sc.title.startswith("Quiz:"):
                    # Quiz titles are auto-generated, keep short
                    new_title = sc.title  # Will be regenerated from question text

                # Content-Text übersetzen
                new_content_text = sc.content_text
                if sc.content_text and sc.content_text in TEXT_BODIES:
                    new_content_text = TEXT_BODIES[sc.content_text]
                elif sc.content_text and sc.content_text in CONVERSATION_BODIES:
                    new_content_text = CONVERSATION_BODIES[sc.content_text]

                new_content = LessonContent(
                    lesson_id=new_lesson_id,
                    content_type=sc.content_type,
                    content_id=sc.content_id,  # Same reference (kana/kanji/vocab/grammar)
                    title=new_title,
                    content_text=new_content_text,
                    page_number=sc.page_number,
                    order_index=sc.order_index,
                    file_path=sc.file_path,  # Same files
                    media_url=sc.media_url,
                    is_optional=sc.is_optional,
                    is_interactive=sc.is_interactive,
                )
                db.session.add(new_content)
                db.session.flush()
                content_count += 1

                # Quiz-Fragen kopieren und übersetzen
                if sc.content_type == 'interactive':
                    src_questions = QuizQuestion.query.filter_by(lesson_content_id=sc.id).order_by(QuizQuestion.order_index).all()
                    for sq in src_questions:
                        # Übersetzung suchen
                        trans = QUIZ_TRANSLATIONS.get(sq.question_text, None)

                        new_q_text = trans["q"] if trans else sq.question_text
                        new_explanation = trans["e"] if trans else sq.explanation

                        # Quiz title from question text
                        if trans:
                            q_preview = trans["q"][:60]
                            new_content.title = f"Quiz: {q_preview}"

                        new_q = QuizQuestion(
                            lesson_content_id=new_content.id,
                            question_type=sq.question_type,
                            question_text=new_q_text,
                            explanation=new_explanation,
                            hint=sq.hint,
                            difficulty_level=sq.difficulty_level,
                            points=sq.points,
                            order_index=sq.order_index,
                        )
                        db.session.add(new_q)
                        db.session.flush()
                        quiz_count += 1

                        # Optionen kopieren und übersetzen
                        src_options = QuizOption.query.filter_by(question_id=sq.id).order_by(QuizOption.id).all()
                        for so in src_options:
                            new_opt_text = translate_option_text(so.option_text)
                            new_feedback = translate_feedback(so.feedback, trans) if trans else so.feedback

                            new_opt = QuizOption(
                                question_id=new_q.id,
                                option_text=new_opt_text,
                                is_correct=so.is_correct,
                                feedback=new_feedback,
                            )
                            db.session.add(new_opt)

            print(f"    {content_count} Content-Items kopiert, {quiz_count} Quiz-Fragen übersetzt")

        # Commit
        db.session.commit()
        print("\n=== Alle Lektionen erfolgreich kopiert und übersetzt! ===")

        # Verifizierung
        de_lessons = Lesson.query.filter_by(instruction_language='german').all()
        print(f"\nDeutsche Lektionen: {len(de_lessons)}")
        for l in de_lessons:
            contents = LessonContent.query.filter_by(lesson_id=l.id).count()
            quizzes = QuizQuestion.query.join(LessonContent).filter(LessonContent.lesson_id == l.id).count()
            print(f"  {l.title}: {contents} Inhalte, {quizzes} Quiz-Fragen")


if __name__ == "__main__":
    main()

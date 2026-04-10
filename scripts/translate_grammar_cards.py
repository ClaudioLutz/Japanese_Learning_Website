#!/usr/bin/env python3
"""
Grammatik-Karten und Konversationen der deutschen Lektionen uebersetzen.

1. Neue deutsche Grammar-Eintraege erstellen (Duplikate der englischen)
2. lesson_content.content_id auf die neuen DE-Eintraege umbiegen
3. Konversations-Titel und -Texte uebersetzen
"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Grammar, LessonContent, Lesson

# ══════════════════════════════════════════════════════════════════════
# 1. GRAMMATIK-UEBERSETZUNGEN
# ══════════════════════════════════════════════════════════════════════

GRAMMAR_TRANSLATIONS = {
    4: {
        "title": "N は N です (Themenpartikel は + です)",
        "explanation": (
            "Die Partikel は zeigt an, dass das Wort davor das Thema des Satzes ist. "
            "Man waehlt ein Nomen, ueber das man sprechen moechte, fuegt は hinzu, um es als Thema "
            "zu markieren, und macht eine Aussage darueber. "
            "Nomen mit です bilden das Praedikat. です drueckt eine Feststellung oder Behauptung aus "
            "und signalisiert gleichzeitig, dass der Sprecher hoeflich zum Zuhoerer ist."
        ),
    },
    5: {
        "title": "N じゃ ありません (Verneinung)",
        "explanation": (
            "じゃ ありません ist die Verneinungsform von です. "
            "Diese Form wird in der Alltagssprache verwendet. "
            "In formeller Sprache oder Schriftsprache wird stattdessen では ありません benutzt."
        ),
    },
    6: {
        "title": "S か (Fragepartikel か)",
        "explanation": (
            "Die Partikel か drueckt Zweifel, eine Frage oder Unsicherheit des Sprechers aus. "
            "Eine Frage wird gebildet, indem man einfach か an das Satzende anfuegt. "
            "Die Frage wird mit steigender Intonation gesprochen. Die Wortstellung aendert sich nicht. "
            "Fragen, ob eine Aussage korrekt ist: Antwort mit はい oder いいえ. "
            "Fragen mit Fragewort: Das Fragewort ersetzt den Teil des Satzes, nach dem gefragt wird, "
            "und か wird am Ende angefuegt."
        ),
    },
    7: {
        "title": "N も (Partikel も — auch, ebenfalls)",
        "explanation": (
            "も wird nach einem Thema anstelle von は verwendet, "
            "wenn die Aussage ueber das Thema dieselbe ist wie beim vorherigen Thema. "
            "Es bedeutet 'auch' oder 'ebenfalls'."
        ),
    },
    8: {
        "title": "N の N (Besitz/Zugehoerigkeit の)",
        "explanation": (
            "の verbindet zwei Nomen miteinander. N₁ bestimmt N₂ naeher. "
            "In Lektion 1 bezeichnet N₁ eine Organisation oder Gruppe, der N₂ angehoert."
        ),
    },
    9: {
        "title": "〜さん (Hoeflichkeitssuffix)",
        "explanation": (
            "さん wird an den Namen des Gespraechspartners oder einer dritten Person angefuegt, "
            "um Respekt auszudruecken. Es darf nie mit dem eigenen Namen verwendet werden. "
            "Wenn man den Namen des Gespraechspartners kennt, wird anstelle von あなた (Sie/du) "
            "ueblicherweise der Familienname mit さん verwendet."
        ),
    },
    10: {
        "title": "これ/それ/あれ (Demonstrativpronomen fuer Dinge)",
        "explanation": (
            "これ bezeichnet einen Gegenstand in der Naehe des Sprechers. "
            "それ bezeichnet einen Gegenstand in der Naehe des Zuhoerers. "
            "あれ bezeichnet einen Gegenstand, der von beiden weit entfernt ist. "
            "Diese Woerter werden als Pronomen verwendet, um auf Dinge hinzuweisen."
        ),
    },
    11: {
        "title": "この/その/あの N (Demonstrative Bestimmungswoerter)",
        "explanation": (
            "この, その und あの bestimmen Nomen naeher und koennen nicht allein stehen. "
            "この + Nomen bezieht sich auf etwas in der Naehe des Sprechers. "
            "その + Nomen bezieht sich auf etwas in der Naehe des Zuhoerers. "
            "あの + Nomen bezieht sich auf etwas, das von beiden weit entfernt ist."
        ),
    },
    12: {
        "title": "N₁ですか、N₂ですか (Auswahlfragen)",
        "explanation": (
            "Dieses Muster wird verwendet, um den Zuhoerer zwischen zwei oder mehr "
            "Optionen waehlen zu lassen. Die Antwort ist nicht はい oder いいえ, "
            "sondern eine der vorgegebenen Optionen."
        ),
    },
    13: {
        "title": "N₁ の N₂ (Besitz und Zugehoerigkeit — erweitert)",
        "explanation": (
            "In Lektion 2 wird die Verwendung von の erweitert. "
            "N₁ kann den Besitzer angeben (watashi no hon = mein Buch), "
            "das Herkunftsland oder die Sprache, oder das Themengebiet. "
            "Wenn der Kontext das zweite Nomen offensichtlich macht, kann es weggelassen werden: "
            "わたしのです bedeutet 'Es gehoert mir'."
        ),
    },
    14: {
        "title": "ここ/そこ/あそこ (Demonstrative Ortswoerter)",
        "explanation": (
            "ここ bezeichnet den Ort, an dem sich der Sprecher befindet. "
            "そこ bezeichnet den Ort, an dem sich der Zuhoerer befindet. "
            "あそこ bezeichnet einen Ort, der von beiden weit entfernt ist. "
            "Diese Woerter werden verwendet, um Orte anzugeben. "
            "どこ ist das Fragewort fuer Orte."
        ),
    },
    15: {
        "title": "N は Ort です (Ortsangabe fuer Dinge/Personen)",
        "explanation": (
            "Dieses Muster gibt an, wo sich etwas oder jemand befindet. "
            "Das Thema (N) wird von は gefolgt, und der Ort steht vor です. "
            "Die hoeflichen Formen こちら, そちら, あちら und どちら koennen anstelle von "
            "ここ, そこ, あそこ und どこ verwendet werden."
        ),
    },
    16: {
        "title": "N はいくらですか (Nach dem Preis fragen)",
        "explanation": (
            "いくら wird verwendet, um nach dem Preis von etwas zu fragen. "
            "Die Antwort verwendet den Zaehler 円 (en, Yen). "
            "Zahlen werden mit 円 kombiniert, um Preise anzugeben."
        ),
    },
    17: {
        "title": "何階 (Stockwerk-Zaehler)",
        "explanation": (
            "何階 (nangai) wird verwendet, um nach dem Stockwerk zu fragen. "
            "Der Zaehler ～階 (kai/gai) wird fuer Stockwerke eines Gebaeudes verwendet. "
            "Beachten Sie die Lautveraenderungen: 三階 ist sankai (nicht sangai) "
            "und 何階 ist nangai."
        ),
    },
    18: {
        "title": "今 ～時 ～分 です (Uhrzeit angeben)",
        "explanation": (
            "Die Uhrzeit wird mit den Zaehlern 時 (ji, Uhr) und 分 (fun/pun, Minuten) "
            "ausgedrueckt. 今 (ima) bedeutet 'jetzt'. 半 (han) bedeutet 'halb'. "
            "Beachten Sie die besonderen Lesungen: 4時 ist yoji (nicht yonji), "
            "7時 ist shichiji, 9時 ist kuji. "
            "Bei Minuten gibt es Lautveraenderungen: "
            "1分 ippun, 3分 sanpun, 6分 roppun, 8分 happun, 10分 juppun."
        ),
    },
    19: {
        "title": "V ます / V ません / V ました / V ませんでした (Verbkonjugation — hoefliche Form)",
        "explanation": (
            "ます ist die hoefliche Gegenwartsform (auch Zukunft) in der Bejahung. "
            "ません ist die hoefliche Gegenwartsform in der Verneinung. "
            "ました ist die hoefliche Vergangenheitsform in der Bejahung. "
            "ませんでした ist die hoefliche Vergangenheitsform in der Verneinung. "
            "Diese vier Formen decken alle grundlegenden Kombinationen von "
            "Zeitform und Bejahung/Verneinung in der hoeflichen Sprache ab."
        ),
    },
    20: {
        "title": "Uhrzeit に V ます (Zeitpartikel に)",
        "explanation": (
            "Die Partikel に gibt den genauen Zeitpunkt an, zu dem eine Handlung stattfindet. "
            "Sie wird mit Uhrzeiten, Wochentagen und Datumsangaben verwendet. "
            "に wird jedoch NICHT mit relativen Zeitwoertern wie きょう (heute), "
            "きのう (gestern), あした (morgen), けさ (heute Morgen), "
            "まいにち (jeden Tag) oder いつ (wann) verwendet."
        ),
    },
    21: {
        "title": "～から ～まで (Von ~ Bis ~)",
        "explanation": (
            "から zeigt einen Anfangspunkt an (von/ab) und まで einen Endpunkt (bis). "
            "Sie koennen mit Zeitangaben, Tagen und Orten verwendet werden. "
            "から und まで koennen jeweils allein stehen und muessen nicht immer zusammen vorkommen."
        ),
    },
    22: {
        "title": "Ort へ 行きます/来ます/帰ります (Bewegungsverben mit へ)",
        "explanation": (
            "Die Partikel へ (ausgesprochen 'e') gibt die Richtung oder das Ziel "
            "einer Bewegung an. Sie wird mit den Verben 行きます (gehen), "
            "来ます (kommen) und 帰ります (zurueckkehren) verwendet. "
            "Die Partikel に kann bei diesen Verben mit gleicher Bedeutung "
            "anstelle von へ verwendet werden."
        ),
    },
    23: {
        "title": "Verkehrsmittel で 行きます (Transportmittel — Partikel で)",
        "explanation": (
            "Die Partikel で gibt das verwendete Transportmittel an. "
            "Wenn man zu Fuss geht, wird statt Nomen + で der Ausdruck "
            "歩いて (aruite, zu Fuss) verwendet."
        ),
    },
    24: {
        "title": "Person と V ます (Etwas mit jemandem tun)",
        "explanation": (
            "Die Partikel と gibt die Person an, mit der man etwas gemeinsam tut. "
            "Wenn man etwas allein tut, verwendet man 一人で (hitori de, allein) "
            "anstelle von Person と."
        ),
    },
    25: {
        "title": "いつ (Wann — Fragewort)",
        "explanation": (
            "いつ ist das Fragewort fuer 'wann'. "
            "Es benoetigt keine Partikel に. "
            "Es kann an der Stelle des Zeitausdrucks im Satz eingesetzt werden."
        ),
    },
}

# ══════════════════════════════════════════════════════════════════════
# 2. KONVERSATIONS-UEBERSETZUNGEN
# ══════════════════════════════════════════════════════════════════════

CONVERSATION_FIXES = {
    5848: {
        "title": "Wessen Regenschirm ist das?",
        "content_text": """Tanaka: すみません。それは わたしの かばんですか。
  (Sumimasen. Sore wa watashi no kaban desu ka.)
  → Entschuldigung. Ist das meine Tasche?

Suzuki: これですか。いいえ、ちがいます。これは 山田さんのです。
  (Kore desu ka. Iie, chigaimasu. Kore wa Yamada-san no desu.)
  → Diese hier? Nein, das stimmt nicht. Das ist die von Frau Yamada.

Tanaka: そうですか。あの かさは だれのですか。
  (Sou desu ka. Ano kasa wa dare no desu ka.)
  → Ach so. Wessen Regenschirm ist das dort drueben?

Suzuki: あれは わたしのです。
  (Are wa watashi no desu.)
  → Der gehoert mir.

Tanaka: あのう、この ノートは 鈴木さんのですか、山田さんのですか。
  (Anou, kono nooto wa Suzuki-san no desu ka, Yamada-san no desu ka.)
  → Aehm, gehoert dieses Notizbuch Ihnen oder Frau Yamada?

Suzuki: わたしのです。どうも。
  (Watashi no desu. Doumo.)
  → Es gehoert mir. Danke.

Yamada: 田中さん、これは 田中さんの かばんですか。
  (Tanaka-san, kore wa Tanaka-san no kaban desu ka.)
  → Herr Tanaka, ist das Ihre Tasche?

Tanaka: はい、わたしのです。ありがとうございます。
  (Hai, watashi no desu. Arigatou gozaimasu.)
  → Ja, sie gehoert mir. Vielen Dank.""",
    },
    5928: {
        "title": "Wo ist die Kantine?",
        "content_text": """Kimura: すみません。食堂は どこですか。
  (Sumimasen. Shokudou wa doko desu ka.)
  → Entschuldigung. Wo ist die Kantine?

Hayashi: 食堂は 地下です。
  (Shokudou wa chika desu.)
  → Die Kantine ist im Untergeschoss.

Kimura: そうですか。トイレも 地下ですか。
  (Sou desu ka. Toire mo chika desu ka.)
  → Ach so. Ist die Toilette auch im Untergeschoss?

Hayashi: いいえ、トイレは 二階です。
  (Iie, toire wa nikai desu.)
  → Nein, die Toilette ist im zweiten Stock.

Kimura: 会議室は 何階ですか。
  (Kaigishitsu wa nangai desu ka.)
  → In welchem Stock ist der Konferenzraum?

Hayashi: 会議室は 三階です。エレベーターは あそこです。
  (Kaigishitsu wa sankai desu. Erebeetaa wa asoko desu.)
  → Der Konferenzraum ist im dritten Stock. Der Aufzug ist dort drueben.

Kimura: ありがとうございます。
  (Arigatou gozaimasu.)
  → Vielen Dank.

Hayashi: いいえ。
  (Iie.)
  → Gern geschehen.""",
    },
    6010: {
        "title": "Um wie viel Uhr stehen Sie auf?",
        "content_text": """Mori: 森さんは 毎朝 何時に 起きますか。
  (Mori-san wa maiasa nanji ni okimasu ka.)
  → Um wie viel Uhr stehen Sie jeden Morgen auf, Herr Mori?

Mori: 六時半に 起きます。
  (Rokuji han ni okimasu.)
  → Ich stehe um halb sieben auf.

Ito: 仕事は 何時からですか。
  (Shigoto wa nanji kara desu ka.)
  → Ab wie viel Uhr arbeiten Sie?

Mori: 八時から 五時までです。
  (Hachiji kara goji made desu.)
  → Von acht bis fuenf.

Ito: 昼休みは 何時からですか。
  (Hiruyasumi wa nanji kara desu ka.)
  → Ab wann ist die Mittagspause?

Mori: 十二時から 一時までです。伊藤さんは？
  (Juuniji kara ichiji made desu. Itou-san wa?)
  → Von zwoelf bis eins. Und bei Ihnen, Frau Ito?

Ito: わたしは 九時から 六時まで 働きます。
  (Watashi wa kuji kara rokuji made hatarakimasu.)
  → Ich arbeite von neun bis sechs.

Mori: 大変ですね。
  (Taihen desu ne.)
  → Das ist aber anstrengend.

Ito: そうですね。でも、土曜日は 休みです。
  (Sou desu ne. Demo, doyoubi wa yasumi desu.)
  → Ja, stimmt. Aber am Samstag habe ich frei.""",
    },
    6089: {
        "title": "Gehen wir zusammen?",
        "content_text": """Nakamura: 来週の 土曜日、動物園へ 行きませんか。
  (Raishuu no doyoubi, doubutsuen e ikimasen ka.)
  → Wollen wir naechsten Samstag in den Zoo gehen?

Ogawa: いいですね。だれと 行きますか。
  (Ii desu ne. Dare to ikimasu ka.)
  → Das klingt gut. Mit wem gehen Sie?

Nakamura: 田中さんと 行きます。小川さんも いっしょに いきませんか。
  (Tanaka-san to ikimasu. Ogawa-san mo issho ni ikimasen ka.)
  → Ich gehe mit Herrn Tanaka. Kommen Sie auch mit, Frau Ogawa?

Ogawa: ええ、ぜひ。何で 行きますか。
  (Ee, zehi. Nan de ikimasu ka.)
  → Ja, sehr gern. Wie fahren wir hin?

Nakamura: 電車で 行きます。駅から バスで 十分です。
  (Densha de ikimasu. Eki kara basu de juppun desu.)
  → Wir fahren mit dem Zug. Vom Bahnhof sind es zehn Minuten mit dem Bus.

Ogawa: 何時に 駅へ 行きますか。
  (Nanji ni eki e ikimasu ka.)
  → Um wie viel Uhr gehen wir zum Bahnhof?

Nakamura: 九時に 駅へ 行きます。
  (Kuji ni eki e ikimasu.)
  → Wir treffen uns um neun am Bahnhof.

Ogawa: わかりました。土曜日に。
  (Wakarimashita. Doyoubi ni.)
  → Verstanden. Bis Samstag.""",
    },
}

# ══════════════════════════════════════════════════════════════════════
# AUSFUEHRUNG
# ══════════════════════════════════════════════════════════════════════

app = create_app()
with app.app_context():
    # --- 1. Grammatik: Deutsche Duplikate erstellen ---
    print("=== Grammatik-Eintraege duplizieren und uebersetzen ===")

    # Finde alle lesson_content-Eintraege fuer Grammatik in deutschen Lektionen
    german_grammar_contents = (
        db.session.query(LessonContent)
        .join(Lesson, LessonContent.lesson_id == Lesson.id)
        .filter(
            Lesson.instruction_language == 'german',
            LessonContent.content_type == 'grammar',
        )
        .all()
    )

    for lc in german_grammar_contents:
        old_grammar_id = lc.content_id
        if old_grammar_id not in GRAMMAR_TRANSLATIONS:
            print(f"  WARNUNG: Grammar ID {old_grammar_id} nicht in Uebersetzungen!")
            continue

        trans = GRAMMAR_TRANSLATIONS[old_grammar_id]
        old_grammar = db.session.get(Grammar, old_grammar_id)
        if not old_grammar:
            print(f"  WARNUNG: Grammar ID {old_grammar_id} nicht in DB!")
            continue

        # Pruefen ob schon ein DE-Duplikat existiert (Titel endet mit gleicher Struktur)
        existing = Grammar.query.filter_by(title=trans["title"]).first()
        if existing:
            # Bereits uebersetzt — nur content_id umbiegen
            lc.content_id = existing.id
            print(f"  Grammar {old_grammar_id} -> {existing.id} (bereits vorhanden): {trans['title'][:50]}")
            continue

        # Neuen DE-Eintrag erstellen
        new_grammar = Grammar(
            title=trans["title"],
            explanation=trans["explanation"],
            structure=old_grammar.structure,
            jlpt_level=old_grammar.jlpt_level,
            status=old_grammar.status,
        )
        db.session.add(new_grammar)
        db.session.flush()  # ID zuweisen

        # lesson_content auf neuen Eintrag umbiegen
        lc.content_id = new_grammar.id
        print(f"  Grammar {old_grammar_id} -> {new_grammar.id} (neu): {trans['title'][:50]}")

    # --- 2. Konversations-Titel und -Texte uebersetzen ---
    print("\n=== Konversationen uebersetzen ===")

    for content_id, fix in CONVERSATION_FIXES.items():
        content = db.session.get(LessonContent, content_id)
        if not content:
            print(f"  WARNUNG: Content ID {content_id} nicht gefunden!")
            continue

        content.title = fix["title"]
        content.content_text = fix["content_text"]
        print(f"  Content {content_id}: {fix['title']}")

    db.session.commit()
    print("\nAlle Uebersetzungen angewendet!")

    # --- Verifikation ---
    print("\n=== Verifikation ===")
    remaining_en = (
        db.session.query(Grammar.id, Grammar.title)
        .join(LessonContent, LessonContent.content_id == Grammar.id)
        .join(Lesson, LessonContent.lesson_id == Lesson.id)
        .filter(
            Lesson.instruction_language == 'german',
            LessonContent.content_type == 'grammar',
            Grammar.explanation.like('%The %'),
        )
        .all()
    )
    if remaining_en:
        print(f"  WARNUNG: {len(remaining_en)} Grammatik-Eintraege noch auf Englisch:")
        for g in remaining_en:
            print(f"    ID {g.id}: {g.title}")
    else:
        print("  Alle Grammatik-Eintraege uebersetzt!")

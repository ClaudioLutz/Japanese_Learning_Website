"""Backfill `vocabulary.example_sentence_japanese` mit kurzen N5-Beispielsaetzen.

Fuer jede Vokabel-Karte soll der Audio-Button einen kompletten japanischen Satz
vorlesen statt nur des Wortes. Dieses Skript:

1. Bereinigt bestehende Saetze, an denen Klammer-Romaji haengen
   (z.B. "わたしは...です。 (watashi wa ... desu.)" -> "わたしは...です。"),
   damit /api/tts mit lang=ja sie nicht ablehnt.
2. Fuellt fehlende Beispielsaetze fuer die wichtigsten N5-Vokabeln aus
   einer kuratierten Mapping-Tabelle (MNN-Lektion-1-Stil).

Aufruf:
    python -m scripts.backfill_vocab_examples            # nur Report (dry-run)
    python -m scripts.backfill_vocab_examples --apply    # tatsaechlich schreiben
    python -m scripts.backfill_vocab_examples --force    # auch nicht-leere ueberschreiben
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Vocabulary  # noqa: E402

# Hiragana, Katakana, CJK Unified, Halfwidth Katakana, JP-Satzzeichen + Common Punct.
JAPANESE_RE = re.compile(r'[぀-ゟ゠-ヿ一-鿿ｦ-ﾟ]')
SENTENCE_END_RE = re.compile(r'[。！？]')
# Klammer-Block am Satzende, der mit lateinischem Buchstaben beginnt — z.B.
# "...です。 (watashi wa ... desu.)" -> wird gestrippt.
TRAILING_LATIN_PAREN_RE = re.compile(r'\s*[（(]\s*[A-Za-zĀ-ž][^)）]*[)）]\s*$')
# Saubere Vokabel-Saetze sind kurz: 6-80 Zeichen Faustregel.
MIN_LEN, MAX_LEN = 4, 200


def strip_trailing_romaji(text: str) -> str:
    """Entferne trailing Klammer-Romaji / -Uebersetzungen am Satzende.

    Idempotent: mehrfacher Aufruf liefert dasselbe Ergebnis.
    """
    if not text:
        return text
    cleaned = text.strip()
    while True:
        new = TRAILING_LATIN_PAREN_RE.sub('', cleaned).strip()
        if new == cleaned:
            return cleaned
        cleaned = new


def is_pure_japanese_sentence(text: str) -> bool:
    """True, wenn der Text ein TTS-tauglicher JP-Satz ist:
    - enthaelt japanische Zeichen
    - hat ein JP-Satzende (。/！/？)
    - keine lateinischen Buchstaben (Romaji-frei)
    - sinnvolle Laenge.
    """
    if not text:
        return False
    if not (MIN_LEN <= len(text) <= MAX_LEN):
        return False
    if not JAPANESE_RE.search(text):
        return False
    if not SENTENCE_END_RE.search(text):
        return False
    # Lateinische Buchstaben deuten auf Romaji oder Mischtext hin -> abweisen.
    if re.search(r'[A-Za-zĀ-ž]', text):
        return False
    return True


# Kuratierte Beispielsaetze fuer N5-Vokabular (MNN-Lektion-1-Stil).
# Schluessel = Vocabulary.id; Wert = (japanisch, romaji, deutsch).
# - JP: TTS-tauglich (rein japanisch, mit 。/！/？). Lest der Audio-Button vor.
# - Romaji: Hepburn, Kleinschreibung, Trennstriche bei zusammengesetzten Lesungen.
# - Deutsch: kurz, sinngemaess, dem N5-Niveau angemessen.
# Werden auf der Karten-Rueckseite als 3 Zeilen unter "Beispiel:" dargestellt.
MANUAL_SENTENCE_ENTRIES: dict[int, tuple[str, str, str]] = {
    # MNN L1 — Personen / Berufe / Begruessung
    20: ('わたしは スイスから きました。',
         'Watashi wa Suisu kara kimashita.',
         'Ich komme aus der Schweiz.'),
    21: ('あした、わたしたちは こうえんへ いきます。',
         'Ashita, watashitachi wa kōen e ikimasu.',
         'Morgen gehen wir in den Park.'),
    22: ('あなたの おしごとは なんですか。',
         'Anata no oshigoto wa nan desu ka.',
         'Was ist Ihr Beruf?'),
    23: ('あのひとは とても しんせつです。',
         'Ano hito wa totemo shinsetsu desu.',
         'Diese Person ist sehr nett.'),
    24: ('あのかたが しゃちょうの すずきさんです。',
         'Ano kata ga shachō no Suzuki-san desu.',
         'Das ist Herr Suzuki, der Firmenchef.'),
    25: ('みなさん、こんばんは。きょうも おつかれさまでした。',
         'Minasan, konbanwa. Kyō mo otsukaresama deshita.',
         'Guten Abend, alle zusammen. Auch heute war es ein anstrengender Tag.'),
    26: ('せんせいに しつもんが あります。',
         'Sensei ni shitsumon ga arimasu.',
         'Ich habe eine Frage an die Lehrerin.'),
    27: ('あねは ちゅうがっこうの きょうしです。',
         'Ane wa chūgakkō no kyōshi desu.',
         'Meine ältere Schwester ist Lehrerin an einer Mittelschule.'),
    28: ('がくせいは まいにち がっこうへ いきます。',
         'Gakusei wa mainichi gakkō e ikimasu.',
         'Studierende gehen jeden Tag zur Schule.'),
    29: ('あには とうきょうの かいしゃいんです。',
         'Ani wa Tōkyō no kaishain desu.',
         'Mein älterer Bruder ist Angestellter in Tokio.'),
    30: ('あの しゃいんは いつも しんせつです。',
         'Ano shain wa itsumo shinsetsu desu.',
         'Dieser Mitarbeiter ist immer freundlich.'),
    31: ('あには ぎんこういんに なりました。',
         'Ani wa ginkōin ni narimashita.',
         'Mein älterer Bruder ist Bankangestellter geworden.'),
    32: ('あには おおさかの いしゃです。',
         'Ani wa Ōsaka no isha desu.',
         'Mein älterer Bruder ist Arzt in Osaka.'),
    33: ('けんきゅうしゃは だいがくで はたらきます。',
         'Kenkyūsha wa daigaku de hatarakimasu.',
         'Forschende arbeiten an der Universität.'),
    34: ('あには コンピューターの エンジニアです。',
         'Ani wa konpyūtā no enjinia desu.',
         'Mein älterer Bruder ist Computeringenieur.'),
    35: ('わたしは とうきょうの だいがくで べんきょうします。',
         'Watashi wa Tōkyō no daigaku de benkyō shimasu.',
         'Ich studiere an einer Universität in Tokio.'),
    36: ('あした びょういんへ いきます。',
         'Ashita byōin e ikimasu.',
         'Morgen gehe ich ins Krankenhaus.'),
    37: ('へやの でんきを つけて ください。',
         'Heya no denki o tsukete kudasai.',
         'Schalten Sie bitte das Licht im Zimmer ein.'),
    38: ('それは だれの かさですか。',
         'Sore wa dare no kasa desu ka.',
         'Wessen Regenschirm ist das?'),
    39: ('すみません、どなたですか。',
         'Sumimasen, donata desu ka.',
         'Entschuldigung, wer sind Sie (höflich)?'),
    40: ('むすこは じゅっさいに なりました。',
         'Musuko wa jussai ni narimashita.',
         'Mein Sohn ist zehn Jahre alt geworden.'),
    41: ('おこさんは なんさいですか。',
         'Okosan wa nansai desu ka.',
         'Wie alt ist Ihr Kind?'),
    42: ('しつれいですが、すずきさんですか。',
         'Shitsurei desu ga, Suzuki-san desu ka.',
         'Entschuldigung, sind Sie Herr/Frau Suzuki?'),
    43: ('はじめまして。おなまえは？',
         'Hajimemashite. O-namae wa?',
         'Freut mich. Wie heissen Sie?'),
    44: ('リーです。どうぞよろしく。',
         'Rī desu. Dōzo yoroshiku.',
         'Ich heisse Lee. Sehr erfreut.'),

    # MNN L1 — Laender (Variation: Verben, Adjektive, Kontext)
    45: ('らいねん アメリカへ りょこうします。',
         'Rainen Amerika e ryokō shimasu.',
         'Nächstes Jahr reise ich nach Amerika.'),
    46: ('イギリスは おちゃが ゆうめいです。',
         'Igirisu wa o-cha ga yūmei desu.',
         'England ist berühmt für seinen Tee.'),
    47: ('インドの カレーは とても からいです。',
         'Indo no karē wa totemo karai desu.',
         'Indisches Curry ist sehr scharf.'),
    48: ('インドネシアは とても あつい くにです。',
         'Indoneshia wa totemo atsui kuni desu.',
         'Indonesien ist ein sehr heisses Land.'),
    49: ('らいげつ かんこくへ いきます。',
         'Raigetsu Kankoku e ikimasu.',
         'Nächsten Monat fahre ich nach Südkorea.'),
    51: ('ちゅうごくの りょうりが すきです。',
         'Chūgoku no ryōri ga suki desu.',
         'Ich mag chinesische Küche.'),
    52: ('わたしの ともだちは ドイツに すんで います。',
         'Watashi no tomodachi wa Doitsu ni sunde imasu.',
         'Mein Freund wohnt in Deutschland.'),
    53: ('にほんで にほんごを べんきょうしています。',
         'Nihon de Nihongo o benkyō shite imasu.',
         'In Japan lerne ich Japanisch.'),

    # MNN L2 — Demonstrativpronomen / -bestimmungswoerter
    56: ('これは わたしの ほんです。',
         'Kore wa watashi no hon desu.',
         'Das ist mein Buch.'),
    57: ('すみません、それを とって ください。',
         'Sumimasen, sore o totte kudasai.',
         'Entschuldigung, geben Sie mir das bitte.'),
    58: ('あれは なんの たてものですか。',
         'Are wa nan no tatemono desu ka.',
         'Was für ein Gebäude ist das dort drüben?'),
    59: ('この えいがは とても おもしろかったです。',
         'Kono eiga wa totemo omoshirokatta desu.',
         'Dieser Film war sehr interessant.'),
    60: ('その かばんは いくらですか。',
         'Sono kaban wa ikura desu ka.',
         'Wie viel kostet diese Tasche?'),
    61: ('あの レストランは おいしいですよ。',
         'Ano resutoran wa oishii desu yo.',
         'Das Restaurant dort drüben schmeckt richtig gut.'),

    # MNN L2 — Dinge / Floskeln / Getraenke
    76: ('これは わたしの あたらしい かばんです。',
         'Kore wa watashi no atarashii kaban desu.',
         'Das ist meine neue Tasche.'),
    84: ('まいあさ コーヒーを のみます。',
         'Maiasa kōhī o nomimasu.',
         'Jeden Morgen trinke ich Kaffee.'),
    88: ('ええ、そうですね。',
         'Ē, sō desu ne.',
         'Ja, das stimmt.'),
    93: ('プレゼントを どうも ありがとう。',
         'Purezento o dōmo arigatō.',
         'Vielen Dank für das Geschenk.'),
    94: ('おちゃを どうぞ。',
         'O-cha o dōzo.',
         'Hier, bitte ein Tee.'),

    # MNN L3 — Zahlen / Geld
    122: ('この ほんは せんごひゃくえんです。',
          'Kono hon wa sen-go-hyaku-en desu.',
          'Dieses Buch kostet 1\'500 Yen.'),
    124: ('りんごを ひゃくえんで かいました。',
          'Ringo o hyaku-en de kaimashita.',
          'Ich habe einen Apfel für 100 Yen gekauft.'),
    125: ('せんえんを かして ください。',
          'Sen-en o kashite kudasai.',
          'Können Sie mir 1\'000 Yen leihen?'),
    126: ('この とけいは いちまんえんです。',
          'Kono tokei wa ichi-man-en desu.',
          'Diese Uhr kostet 10\'000 Yen.'),
    134: ('でんわばんごうを おしえて ください。',
          'Denwa-bangō o oshiete kudasai.',
          'Sagen Sie mir bitte Ihre Telefonnummer.'),
    135: ('おへやは なんばんですか。',
          'O-heya wa nanban desu ka.',
          'Welche Zimmernummer haben Sie?'),

    # MNN L5 — Verkehr / Orte
    185: ('ちかくの スーパーで やさいを かいます。',
          'Chikaku no sūpā de yasai o kaimasu.',
          'Im Supermarkt in der Nähe kaufe ich Gemüse.'),
    190: ('まいあさ バスで かいしゃへ いきます。',
          'Maiasa basu de kaisha e ikimasu.',
          'Jeden Morgen fahre ich mit dem Bus zur Arbeit.'),
    191: ('あめでしたから、タクシーで かえりました。',
          'Ame deshita kara, takushī de kaerimashita.',
          'Es hat geregnet, deshalb bin ich mit dem Taxi nach Hause gefahren.'),
    213: ('デパートで ははの プレゼントを かいました。',
          'Depāto de haha no purezento o kaimashita.',
          'Im Kaufhaus habe ich ein Geschenk für meine Mutter gekauft.'),
    217: ('ともだちと レストランで ばんごはんを たべました。',
          'Tomodachi to resutoran de bangohan o tabemashita.',
          'Mit einem Freund habe ich im Restaurant zu Abend gegessen.'),
}

# Abwaertskompatibel — alter MANUAL_SENTENCES-Name. Tests/alte Aufrufer nutzen
# nur den JP-Satz; das Trio (jp, romaji, de) wird in main() gelesen.
MANUAL_SENTENCES: dict[int, str] = {
    vid: entry[0] for vid, entry in MANUAL_SENTENCE_ENTRIES.items()
}


def derive_sentence(v: Vocabulary) -> str | None:
    """Liefert einen kuratierten Beispielsatz fuer eine Vokabel — oder None,
    wenn (noch) keiner hinterlegt ist."""
    sentence = MANUAL_SENTENCES.get(v.id)
    if sentence and is_pure_japanese_sentence(sentence):
        return sentence
    return None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Schreibt Aenderungen in die DB')
    parser.add_argument('--force', action='store_true',
                        help='Auch nicht-leere Felder ueberschreiben (nur fuer Manual-Overrides relevant)')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        all_vocab = Vocabulary.query.order_by(Vocabulary.id).all()
        total = len(all_vocab)

        cleaned: list[tuple[int, str, str, str]] = []   # (id, word, before, after)
        filled: list[tuple[int, str, str]] = []          # (id, word, sentence)
        gaps: list[tuple[int, str, str]] = []            # (id, word, meaning_de)
        skipped_existing = 0

        for v in all_vocab:
            current = (v.example_sentence_japanese or '').strip()

            # 1) Cleanup: Klammer-Romaji aus bestehendem Satz strippen.
            if current:
                cleaned_text = strip_trailing_romaji(current)
                if cleaned_text != current and is_pure_japanese_sentence(cleaned_text):
                    cleaned.append((v.id, v.word, current, cleaned_text))
                    if args.apply:
                        v.example_sentence_japanese = cleaned_text
                    current = cleaned_text

            # 2) Backfill: leere Felder (oder mit --force alle) aus Manual-Overrides fuellen.
            need_fill = (not current) or args.force
            if not need_fill:
                skipped_existing += 1
                continue

            sentence = derive_sentence(v)
            if sentence:
                filled.append((v.id, v.word, sentence))
                if args.apply:
                    v.example_sentence_japanese = sentence
                # Wenn fuer dieses Vokabel auch Romaji + DE im Manual-Override
                # liegen, gleich example_sentence_english im Karten-Format
                # "Romaji — Deutsche Uebersetzung" setzen, ueberschreibend bei
                # --force, sonst nur wenn Feld leer/sehr kurz.
                entry = MANUAL_SENTENCE_ENTRIES.get(v.id)
                if entry and len(entry) == 3:
                    _, romaji, de = entry
                    new_en = f'{romaji} — {de}'
                    cur_en = (v.example_sentence_english or '').strip()
                    if args.apply and (args.force or not cur_en):
                        v.example_sentence_english = new_en
            else:
                gaps.append((v.id, v.word, v.meaning_de or ''))

        if args.apply:
            db.session.commit()

        mode = 'APPLY' if args.apply else 'DRY-RUN'
        print(f"=== Vocabulary-Beispielsatz-Backfill ({mode}) ===")
        print(f"Total: {total} | bereinigt: {len(cleaned)} | "
              f"neu gefuellt: {len(filled)} | bereits gesetzt (skip): {skipped_existing} | "
              f"Luecken: {len(gaps)}")

        if cleaned:
            print()
            print("Bereinigt (Klammer-Romaji entfernt):")
            for vid, word, before, after in cleaned[:5]:
                print(f"  [{vid}] {word}")
                print(f"      vor:  {before}")
                print(f"      nach: {after}")
            if len(cleaned) > 5:
                print(f"  ... +{len(cleaned) - 5} weitere")

        if filled:
            print()
            print("Neu gefuellt (erste 10):")
            for vid, word, sentence in filled[:10]:
                print(f"  [{vid}] {word:12} -> {sentence}")
            if len(filled) > 10:
                print(f"  ... +{len(filled) - 10} weitere")

        if gaps:
            print()
            print(f"Luecken (kein Satz im MANUAL_SENTENCES) — {len(gaps)} Eintraege:")
            for vid, word, de in gaps[:30]:
                print(f"  [{vid}] {word:14} ({de[:40]})")
            if len(gaps) > 30:
                print(f"  ... +{len(gaps) - 30} weitere")

        return 0


if __name__ == '__main__':
    sys.exit(main())

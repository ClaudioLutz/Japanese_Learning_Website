"""Backfill: ersetzt englische Translations in
`vocabulary.example_sentence_english` durch deutsche Uebersetzungen.

Plattform-Sprache ist Deutsch. Vor diesem Backfill landeten ueberwiegend
englische Saetze auf der Karten-Rueckseite, weil das Feld noch
"Romaji — English" enthielt. Format hier konsistent
"Romaji — Deutsche Uebersetzung" (Em-Dash), parsbar von der Property
Vocabulary.example_sentence_translation.

Aufruf:
    python -m scripts.backfill_vocab_translations_de            # Dry-Run
    python -m scripts.backfill_vocab_translations_de --apply    # tatsaechlich schreiben

Idempotent: laeuft das Skript erneut, ueberschreibt es nur Eintraege, deren
aktueller Inhalt vom vorgesehenen Override abweicht — sonst skip.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Vocabulary  # noqa: E402

# Schluessel = Vocabulary.id; Wert = vollstaendiges
# "Romaji-Satz — Deutsche Uebersetzung" (Em-Dash ` — ` als Trenner).
# Wurde manuell aus den vorigen englischen Translations uebersetzt.
TRANSLATIONS: dict[int, str] = {
    # Wegbeschreibung / Begruessung — alte Eintraege ohne Romaji-Praefix
    9: 'Sumimasen, chotto ii desu ka? — Entschuldigung, haben Sie kurz Zeit?',
    12: 'Eki wa doko desu ka? — Wo ist der Bahnhof?',
    17: 'Tsugi no kōsaten o migi ni magatte kudasai. — Bitte biegen Sie an der nächsten Kreuzung rechts ab.',
    18: 'Shingō o hidari ni magatte kudasai. — Bitte biegen Sie an der Ampel links ab.',
    19: 'Hashi o watatte kudasai. — Bitte überqueren Sie die Brücke.',

    # Zahlen
    231: 'Kotae wa zero desu. — Die Antwort ist null.',
    232: 'Ichi kara hajimemashou. — Lass uns bei eins anfangen.',
    233: 'Ringo ga ni-ko arimasu. — Es gibt zwei Äpfel.',
    234: 'Kazoku wa san-nin desu. — Meine Familie hat drei Personen.',
    239: 'Hachi-ji kara hatarakimasu. — Ich arbeite ab acht Uhr.',
    241: 'Juu-pun de dekimasu. — Es ist in zehn Minuten fertig.',
    242: 'Juuichi-ji ni hirugohan desu. — Mittagessen ist um elf Uhr.',
    243: 'Ani wa nijuugo-sai desu. — Mein älterer Bruder ist fünfundzwanzig Jahre alt.',
    244: 'Kono hon wa gojuu-peeji desu. — Dieses Buch hat fünfzig Seiten.',

    # Familie
    245: 'Watashi no kazoku wa yo-nin desu. — Meine Familie hat vier Personen.',
    246: 'Chichi wa enjinia desu. — Mein Vater ist Ingenieur.',
    247: 'Haha wa sensei desu. — Meine Mutter ist Lehrerin.',
    248: 'Ani wa Toukyou ni imasu. — Mein älterer Bruder ist in Tokio.',
    249: 'Ane wa daigakusei desu. — Meine ältere Schwester ist Studentin.',
    250: 'Otouto wa hassai desu. — Mein jüngerer Bruder ist acht Jahre alt.',
    251: 'Imouto wa gakusei desu. — Meine jüngere Schwester ist Schülerin.',
    252: 'Kyoudai wa san-nin desu. — Ich habe drei Geschwister.',
    253: 'Ryoushin wa Oosaka ni imasu. — Meine Eltern sind in Osaka.',
    254: 'Watashi wa gakusei desu. — Ich bin Studentin.',
    255: 'Tanaka-san no otousan wa sensei desu. — Herr Tanakas Vater ist Lehrer.',
    256: 'Risa-san no okaasan wa isha desu. — Lisas Mutter ist Ärztin.',
    257: 'Oniisan wa nansai desu ka. — Wie alt ist Ihr älterer Bruder?',
    258: 'Oneesan wa doko ni imasu ka. — Wo ist Ihre ältere Schwester?',
    259: 'Kodomo wa futari imasu. — Ich habe zwei Kinder.',
    260: 'Ano otoko no hito wa dare desu ka. — Wer ist der Mann dort drüben?',
    261: 'Ano onna no hito wa haha desu. — Diese Frau dort drüben ist meine Mutter.',
    262: 'Otoko no ko ga hitori imasu. — Es gibt einen Jungen.',
    263: 'Onna no ko wa go-sai desu. — Das Mädchen ist fünf Jahre alt.',
    264: 'Tomodachi to eiga wo mimasu. — Ich schaue mit meinem Freund einen Film.',
    265: 'Ano hito wa tomodachi desu. — Diese Person ist mein Freund.',
    266: 'Ani wa hitori de kimashita. — Mein älterer Bruder ist allein gekommen.',
    267: 'Ryoushin wa futari tomo gakusei deshita. — Beide meine Eltern waren Studenten.',

    # Tagesablauf
    268: 'Ima, nan-ji desu ka? — Wie spät ist es jetzt?',
    269: 'Asa, koohii o nomimasu. — Am Morgen trinke ich Kaffee.',
    271: 'Yoru, hon o yomimasu. — Am Abend lese ich ein Buch.',
    274: 'Ima shichi-ji han desu. — Es ist jetzt halb acht.',
    281: 'Asa, koohii o nomimasu. — Am Morgen trinke ich Kaffee.',
    282: 'Watashi wa hachi-ji kara hatarakimasu. — Ich arbeite ab acht Uhr.',
    284: 'Yoru, nihongo o benkyou shimasu. — Am Abend lerne ich Japanisch.',

    # Berufe / Personen
    288: 'Ane wa eigo no sensei desu. — Meine ältere Schwester ist Englischlehrerin.',
    289: 'Watashi wa gakusei desu. — Ich bin Studentin.',
    290: 'Chichi wa isha desu. — Mein Vater ist Arzt.',
    291: 'Ano hito wa keikan desu. — Diese Person ist Polizist.',
    292: 'Watashi wa Doitsu no ryuugakusei desu. — Ich bin Austauschstudentin aus Deutschland.',
    293: 'Chichi no kaisha wa Tōkyō ni arimasu. — Die Firma meines Vaters ist in Tōkyō.',
    294: 'Ani wa ginkou de hatarakimasu. — Mein älterer Bruder arbeitet bei einer Bank.',
    295: 'Kono mise wa totemo kirei desu. — Dieses Geschäft ist sehr schön.',
    297: 'Watashi wa gaikokujin desu. — Ich bin Ausländerin.',
    298: 'Sensei no okusan wa totemo shizuka desu. — Die Frau des Lehrers ist sehr ruhig.',
    299: 'Kodomo-tachi wa genki desu. — Die Kinder sind munter.',
    300: 'Kono mise wa kirei desu. — Dieses Geschäft ist hübsch.',
    301: 'Ginkou wa shizuka desu. — Die Bank ist ruhig.',
    302: 'Kono hon wa omoshiroi desu. — Dieses Buch ist interessant.',
    303: 'Ano gakusei wa wakai desu. — Diese Studentin ist jung.',
    304: 'Chichi no kaisha wa ookii desu. — Die Firma meines Vaters ist gross.',
    305: 'Kono mise wa chiisai desu. — Dieses Geschäft ist klein.',

    # Essen
    306: 'Asagohan ni tamago wo tabemasu. — Zum Frühstück esse ich ein Ei.',
    312: 'Asa wa kōcha wo nomitai desu. — Am Morgen möchte ich schwarzen Tee trinken.',
    314: 'Chawan ni gohan wo iremasu. — Ich gebe Reis in die Schale.',
    316: 'Haha wa karē wo tsukurimasu. — Meine Mutter macht Curry.',
    317: 'Gakkō no shokudō de tabemasu. — Ich esse in der Schulkantine.',
    319: 'Hashi de gohan wo tabemasu. — Ich esse Reis mit Stäbchen.',
    321: 'Chichi wa kōcha ga kirai desu. — Mein Vater mag keinen schwarzen Tee.',
    322: 'Tsumetai ocha ga oishii desu. — Kalter Tee schmeckt gut.',

    # Telefon / Begruessung
    323: 'Haha ni denwa wo shimasu. — Ich rufe meine Mutter an.',
    324: 'Moshi moshi, Tanaka desu ga. — Hallo, hier spricht Tanaka.',
    325: 'Denwa-bangou wa nanban desu ka. — Wie lautet die Telefonnummer?',
    326: 'Onamae wa nan desu ka. — Wie heissen Sie?',
    328: 'Tomodachi to denwa de hanashimasu. — Ich spreche mit einem Freund am Telefon.',
    329: 'Watashi wa Tanaka to iimasu. — Ich heisse Tanaka.',
    332: 'Tanaka-san wa imasu ka. — Ist Herr Tanaka da?',
    333: 'Sensei ni shitsumon wo kikimasu. — Ich stelle der Lehrerin eine Frage.',
    334: 'Konban, denwa shimasu. — Heute Abend rufe ich an.',
    335: 'Ato de denwa wo kakemasu. — Ich rufe später an.',
    336: 'Tabun, konban kimasu. — Vielleicht kommt er heute Abend.',
    337: 'Ani wa ichiban se ga takai desu. — Mein älterer Bruder ist am grössten.',

    # Adjektive / Floskeln
    340: 'Densha ga osoi desu. — Der Zug ist langsam.',
    341: 'Ani wa hayai desu. — Mein älterer Bruder ist schnell.',
    342: 'Namae wo wasuremashita. — Ich habe den Namen vergessen.',
    343: 'Mō tabemashita. — Ich habe schon gegessen.',
    344: 'Mada kite imasen. — Er/Sie ist noch nicht gekommen.',

    # Geschenke / Phrasen
    345: 'Haha ni purezento wo kaimashita. — Ich habe meiner Mutter ein Geschenk gekauft.',
    346: 'Hana ga kirei desu. — Die Blumen sind schön.',
    348: 'Hankachi wo dōzo. — Hier, ein Taschentuch.',
    349: 'Chiisai hako no naka ni purezento ga arimasu. — In der kleinen Schachtel ist ein Geschenk.',
    350: 'Tomodachi wa taisetsu na hito desu. — Ein Freund ist eine wichtige Person.',
    352: 'Mondai wa arimasen. — Es gibt kein Problem.',

    # Bewegungs- und Existenz-Verben
    353: 'Ashita, gakkō e ikimasu. — Morgen gehe ich zur Schule.',
    354: 'Tomodachi ga kimashita. — Mein Freund ist gekommen.',
    355: 'Heya ni hairimasu. — Ich gehe ins Zimmer.',
    356: 'Shichi-ji ni ie wo demashita. — Ich habe das Haus um sieben verlassen.',
    359: 'Namae wo kaite kudasai. — Bitte schreiben Sie Ihren Namen.',
    360: 'Tomodachi ni aimashita. — Ich habe meinen Freund getroffen.',
    361: 'Heya ni neko ga imasu. — Im Zimmer ist eine Katze.',
    362: 'Tsukue no ue ni hon ga arimasu. — Auf dem Tisch liegt ein Buch.',

    # Raum / Position
    363: 'Watashi no heya wa chiisai desu. — Mein Zimmer ist klein.',
    364: 'Roku-ji ni ie ni kaerimasu. — Um sechs gehe ich nach Hause.',
    365: 'Kyōshitsu ni gakusei ga imasu. — Im Klassenzimmer sind Studierende.',
    366: 'Isu ni suwatte kudasai. — Bitte setzen Sie sich auf den Stuhl.',
    367: 'Tsukue no ue ni nōto ga arimasu. — Auf dem Tisch liegt ein Heft.',
    368: 'Tsukue no ue ni pen ga arimasu. — Auf dem Tisch liegt ein Stift.',
    369: 'Tsukue no shita ni kaban ga arimasu. — Unter dem Tisch ist eine Tasche.',
    370: 'Hako no naka ni purezento ga arimasu. — In der Schachtel ist ein Geschenk.',
    372: 'Shukudai o shite, nemasu. — Ich mache meine Hausaufgaben und gehe (dann) ins Bett.',
    373: 'Mainichi nihongo o benkyou shite imasu. — Ich lerne jeden Tag Japanisch.',

    # Orte
    376: 'Yuubinkyoku wa asoko desu. — Die Post ist dort drüben.',
    377: 'Kodomo wa kouen de asobimasu. — Die Kinder spielen im Park.',
    378: 'Toshokan de hon o yomimasu. — In der Bibliothek lese ich Bücher.',
    379: 'Hoteru wa eki no mae desu. — Das Hotel ist vor dem Bahnhof.',
    380: 'Ashita byouin ni ikimasu. — Morgen gehe ich ins Krankenhaus.',
    382: 'Toukyou no chikatetsu wa fukuzatsu desu. — Tokios U-Bahn ist kompliziert.',
    383: 'Kono machi wa shizuka desu. — Diese Stadt ist ruhig.',
    384: 'Kono michi wa hiroi desu. — Diese Strasse ist breit.',
    385: 'Konbini wa hoteru no chikaku desu. — Der Convenience-Store ist nahe beim Hotel.',

    # Wetter
    386: 'Kyou no tenki wa ii desu. — Das Wetter heute ist gut.',
    387: 'Ashita ame desu. — Morgen regnet es.',
    388: 'Hokkaidou wa yuki ga ooi desu. — In Hokkaido gibt es viel Schnee.',
    389: 'Ashita wa hare desu. — Morgen wird es sonnig.',
    390: 'Kyou wa kumori desu. — Heute ist es bewölkt.',
    391: 'Kyou wa kaze ga tsuyoi desu. — Der Wind ist heute stark.',
    392: 'Sora ga kirei desu. — Der Himmel ist schön.',
    393: 'Natsu wa totemo atsui desu. — Der Sommer ist sehr heiss.',
    394: 'Fuyu wa samui desu. — Der Winter ist kalt.',

    # Jahreszeiten
    395: 'Haru wa atatakai desu. — Der Frühling ist warm.',
    396: 'Natsu, umi ni ikimasu. — Im Sommer fahre ich ans Meer.',
    397: 'Aki wa suzushii desu. — Der Herbst ist kühl.',
    399: 'Kesa wa suzushii desu ne. — Heute Morgen ist es kühl, oder?',

    # Zahlen-Counter
    403: 'Neko ga ni-hiki imasu. — Es gibt zwei Katzen.',
    405: 'Shigatsu ni Nihon ni ikimasu. — Im April fahre ich nach Japan.',
    406: 'Go-nin de ikimasu. — Wir gehen zu fünft.',
    408: 'Shichigatsu wa atsui desu. — Der Juli ist heiss.',
    409: 'Hachi-ji no densha ni norimasu. — Ich nehme den Zug um acht Uhr.',
    413: 'Nisen-en arimasu ka. — Haben Sie 2\'000 Yen?',
    415: 'Kore wa gohyaku-en desu. — Das kostet 500 Yen.',
    416: 'Kotoshi wa nisen-ni-juu-roku-nen desu. — Dieses Jahr ist 2026.',

    # Hobbys / Reisen
    417: 'Watashi no shumi wa ongaku desu. — Mein Hobby ist Musik.',
    422: 'Natsu ni Nihon e ryokou shimasu. — Im Sommer reise ich nach Japan.',
    426: 'Otouto wa geemu ga suki desu. — Mein jüngerer Bruder mag Videospiele.',
    427: 'Tomodachi to karaoke ni ikimasu. — Ich gehe mit einem Freund ins Karaoke.',
    428: 'Haha wa ryouri ga jouzu desu. — Meine Mutter kocht gut.',
    429: 'Watashi wa uta ga heta desu. — Ich kann nicht gut singen.',

    # Wegbeschreibung 2
    431: 'Tsugi no shingou de magarimasu. — Ich biege an der nächsten Ampel ab.',
    432: 'Ano kado wo migi ni magatte kudasai. — Bitte biegen Sie an der Ecke dort drüben rechts ab.',
    433: 'Tsugi no kado wo migi ni magatte kudasai. — Bitte biegen Sie an der nächsten Ecke rechts ab.',
    434: 'Hashi wo watarimasu. — Ich überquere die Brücke.',
    435: 'Eki made arukimasu. — Ich gehe zu Fuss zum Bahnhof.',
    436: 'Chizu wo misete kudasai. — Bitte zeigen Sie mir die Karte.',
    437: 'Eki no higashi-guchi de aimashou. — Treffen wir uns am Ostausgang des Bahnhofs.',
    438: 'Nishi-gawa wa achira desu. — Die Westseite ist dort drüben.',
    439: 'Hokkaidou wa Nihon no kita desu. — Hokkaido liegt im Norden Japans.',
    440: 'Okinawa wa Nihon no minami desu. — Okinawa liegt im Süden Japans.',

    # Wochentage / Daten
    441: 'Nichi-yōbi ni tomodachi to aimasu. — Am Sonntag treffe ich einen Freund.',
    442: 'Getsu-yōbi kara shigoto desu. — Ab Montag arbeite ich.',
    443: 'Ka-yōbi ni byōin ni ikimasu. — Am Dienstag gehe ich ins Krankenhaus.',
    444: 'Sui-yōbi wa yasumi desu. — Mittwoch ist mein freier Tag.',
    445: 'Moku-yōbi ni Nihongo no kurasu ga arimasu. — Am Donnerstag habe ich Japanisch-Unterricht.',
    446: 'Kin-yōbi no yoru, eiga o mimasu. — Am Freitagabend schaue ich einen Film.',
    447: 'Do-yōbi ni yama ni ikimasu. — Am Samstag gehe ich in die Berge.',
    448: 'Watashi no tanjōbi wa shichi-gatsu desu. — Mein Geburtstag ist im Juli.',
    449: 'Kongetsu wa shigoto ga ōi desu. — Diesen Monat habe ich viel Arbeit.',

    # Natur / Kanji
    451: 'Niwa ni ōkii ki ga arimasu. — Im Garten steht ein grosser Baum.',
    452: 'Okane ga arimasen. — Ich habe kein Geld.',
    453: 'Ano ko wa otoko no ko desu. — Dieses Kind ist ein Junge.',
    454: 'Haha wa Nihon-jin desu. — Meine Mutter ist Japanerin.',
    455: 'Ano yama wa takai desu. — Dieser Berg ist hoch.',
    456: 'Kawa no mizu wa tsumetai desu. — Das Flusswasser ist kalt.',
    457: 'Yamada-san wa tomodachi desu. — Yamada-san ist ein Freund.',
    458: 'Do-yōbi ni umi ni ikimasu. — Am Samstag gehe ich ans Meer.',
    461: 'Chiisana kodomo ga imasu. — Es gibt ein kleines Kind.',
    463: 'Watashi wa shimai ga futari imasu. — Ich habe zwei Schwestern.',
    464: 'Otouto-san wa nan-sai desu ka? — Wie alt ist Ihr jüngerer Bruder?',
    465: 'Tanaka-san no imouto-san wa koukousei desu. — Tanaka-sans jüngere Schwester ist Oberschülerin.',

    # Preise / Zeit
    466: 'Onigiri wa sanbyaku-en desu. — Der Onigiri kostet 300 Yen.',
    468: 'Keeki wa happyaku-en desu. — Der Kuchen kostet 800 Yen.',
    469: 'Ima, ku-ji desu. — Es ist jetzt 9 Uhr.',
    471: 'Ima, nan-ji desu ka? — Wie spät ist es jetzt?',
    472: 'Koko kara eki made nanpun desu ka? — Wie viele Minuten von hier bis zum Bahnhof?',

    # Adjektive 2
    474: 'Kono furui hon wa chichi no hon desu. — Dieses alte Buch ist das Buch meines Vaters.',
    475: 'Kono tokei wa takai desu. — Diese Uhr ist teuer.',
    476: 'Kono mise no pan wa yasui desu. — Das Brot in diesem Geschäft ist günstig.',
    477: 'Haha no kami wa nagai desu. — Das Haar meiner Mutter ist lang.',
    478: 'Kono eiga wa mijikai desu. — Dieser Film ist kurz.',
    479: 'Kouen ni kodomo ga ooi desu. — Im Park sind viele Kinder.',
    480: 'Kyou wa hito ga sukunai desu. — Heute sind nur wenige Leute da.',
    482: 'Kono hon wa ii desu. — Dieses Buch ist gut.',

    # Erste Saetze
    483: 'O-namae wa nan desu ka. — Wie heissen Sie?',
    484: 'Yoroshiku onegai shimasu. — Sehr erfreut, Sie kennenzulernen.',
    486: 'Chichi wa kaisha-in desu. — Mein Vater ist Firmenangestellter.',
    487: 'Watashi wa Suisu-jin desu. — Ich bin Schweizerin.',
    488: 'Watashi wa Risa desu. — Ich bin Lisa.',
    489: 'Watashi wa sensei ja arimasen. — Ich bin keine Lehrerin.',
    491: 'Kore wa nan desu ka. — Was ist das?',
    492: 'Ano hito wa dare desu ka. — Wer ist diese Person?',
    493: 'Ano otoko no hito wa sensei desu. — Dieser Mann ist Lehrer.',
    494: 'Ano onna no hito wa Risa-san desu. — Diese Frau ist Lisa.',
    495: 'Watashi wa kyoushi desu. — Ich bin Lehrerin.',
    496: 'Watashi mo gakusei desu. — Ich bin auch Studentin.',
    499: 'Konbanwa. Genki desu ka. — Guten Abend. Wie geht es Ihnen?',
    504: 'Itterasshai, Yuki-chan. — Komm gut wieder, Yuki.',

    # Demonstrativpronomen / Dinge
    509: 'Dore ga anata no hon desu ka. — Welches ist Ihr Buch?',
    510: 'Dono hon ga ii desu ka. — Welches Buch ist gut?',
    511: 'Sono pen wa watashi no desu. — Dieser Stift gehört mir.',
    512: 'Ano enpitsu wa Yuki-chan no desu. — Dieser Bleistift dort drüben gehört Yuki.',
    513: 'Are wa Suisu no tokei desu. — Das dort drüben ist eine Schweizer Uhr.',
    514: 'Tanaka-san no kuruma wa are desu. — Tanakas Auto ist das dort drüben.',
    515: 'Kono jisho wa Nihongo no jisho desu. — Dieses Wörterbuch ist ein japanisches Wörterbuch.',
    516: 'Risa-san no hon desu. — Es ist Lisas Buch.',
    518: 'Ban, roku-ji ni kaerimasu. — Am Abend gehe ich um 6 Uhr nach Hause.',
    519: 'Ku-ji kara go-ji made desu. — Es ist von 9 bis 5 Uhr.',
}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Schreibt Aenderungen in die DB')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        updated: list[tuple[int, str, str]] = []  # (id, word, before, after) — only id+word reported
        skipped = 0
        missing = []

        for vid, new_value in TRANSLATIONS.items():
            v = Vocabulary.query.get(vid)
            if v is None:
                missing.append(vid)
                continue
            current = (v.example_sentence_english or '').strip()
            if current == new_value:
                skipped += 1
                continue
            updated.append((vid, v.word, new_value))
            if args.apply:
                v.example_sentence_english = new_value

        if args.apply:
            db.session.commit()

        mode = 'APPLY' if args.apply else 'DRY-RUN'
        print(f"=== Vocabulary-Translation EN -> DE ({mode}) ===")
        print(f"Override-Eintraege: {len(TRANSLATIONS)} | "
              f"updated: {len(updated)} | bereits korrekt (skip): {skipped} | "
              f"DB nicht gefunden: {len(missing)}")
        if updated:
            print()
            print("Updates (erste 8):")
            for vid, word, new in updated[:8]:
                print(f"  [{vid}] {word:14} -> {new[:90]}")
            if len(updated) > 8:
                print(f"  ... +{len(updated) - 8} weitere")
        if missing:
            print(f"\nFehlende IDs (nicht in lokaler DB): {missing}")
        return 0


if __name__ == '__main__':
    sys.exit(main())

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
# Schluessel = Vocabulary.id; Wert = einfacher JP-Satz mit dem Wort,
# der zu /api/tts lang=ja passt (rein japanisch, mit JP-Satzende).
# Fokus: aktiv in publizierten Lektionen verwendete Vokabeln zuerst.
MANUAL_SENTENCES: dict[int, str] = {
    # MNN L1 — Personen / Berufe / Begruessung
    # Bewusste Strukturvielfalt: Kopula, Verb (~ます/~ました), Adjektiv,
    # Frage und Mini-Szene wechseln sich ab — die Karten sollen nicht alle
    # gleich klingen.
    20: 'わたしは スイスから きました。',                     # わたし
    21: 'あした、わたしたちは こうえんへ いきます。',         # わたしたち
    22: 'あなたの おしごとは なんですか。',                   # あなた
    23: 'あのひとは とても しんせつです。',                   # あのひと
    24: 'あのかたが しゃちょうの すずきさんです。',           # あのかた
    25: 'みなさん、こんばんは。きょうも おつかれさまでした。', # みなさん
    26: 'せんせいに しつもんが あります。',                   # せんせい
    27: 'あねは ちゅうがっこうの きょうしです。',             # きょうし
    28: 'がくせいは まいにち がっこうへ いきます。',          # がくせい
    29: 'あには とうきょうの かいしゃいんです。',             # かいしゃいん
    30: 'あの しゃいんは いつも しんせつです。',              # しゃいん
    31: 'あには ぎんこういんに なりました。',                 # ぎんこういん
    32: 'あには おおさかの いしゃです。',                     # いしゃ  (Bugfix: kein "はは は")
    33: 'けんきゅうしゃは だいがくで はたらきます。',         # けんきゅうしゃ
    34: 'あには コンピューターの エンジニアです。',           # エンジニア
    35: 'わたしは とうきょうの だいがくで べんきょうします。', # だいがく
    36: 'あした びょういんへ いきます。',                     # びょういん
    37: 'へやの でんきを つけて ください。',                  # でんき
    38: 'それは だれの かさですか。',                         # だれ
    39: 'すみません、どなたですか。',                         # どなた
    40: 'むすこは じゅっさいに なりました。',                 # さい
    41: 'おこさんは なんさいですか。',                        # なんさい
    42: 'しつれいですが、すずきさんですか。',                 # しつれいですが
    43: 'はじめまして。おなまえは？',                         # おなまえは？
    44: 'リーです。どうぞよろしく。',                         # どうぞよろしく

    # MNN L1 — Laender (Variation: Verben, Adjektive, Kontext)
    45: 'らいねん アメリカへ りょこうします。',               # アメリカ
    46: 'イギリスは おちゃが ゆうめいです。',                 # イギリス
    47: 'インドの カレーは とても からいです。',              # インド
    48: 'インドネシアは とても あつい くにです。',            # インドネシア
    49: 'らいげつ かんこくへ いきます。',                     # 韓国
    51: 'ちゅうごくの りょうりが すきです。',                 # 中国
    52: 'わたしの ともだちは ドイツに すんで います。',       # ドイツ
    53: 'にほんで にほんごを べんきょうしています。',         # 日本

    # MNN L2 — Demonstrativpronomen / -bestimmungswoerter
    56: 'これは わたしの ほんです。',                         # これ
    57: 'すみません、それを とって ください。',               # それ
    58: 'あれは なんの たてものですか。',                     # あれ
    59: 'この えいがは とても おもしろかったです。',          # この
    60: 'その かばんは いくらですか。',                       # その
    61: 'あの レストランは おいしいですよ。',                 # あの

    # MNN L2 — Dinge / Floskeln / Getraenke
    76: 'これは わたしの あたらしい かばんです。',            # かばん
    84: 'まいあさ コーヒーを のみます。',                     # コーヒー
    88: 'ええ、そうですね。',                                 # そう
    93: 'プレゼントを どうも ありがとう。',                   # どうも
    94: 'おちゃを どうぞ。',                                  # どうぞ

    # MNN L3 — Zahlen / Geld
    122: 'この ほんは せんごひゃくえんです。',                # えん
    124: 'りんごを ひゃくえんで かいました。',                # ひゃく
    125: 'せんえんを かして ください。',                      # せん
    126: 'この とけいは いちまんえんです。',                  # まん
    134: 'でんわばんごうを おしえて ください。',              # でんわばんごう
    135: 'おへやは なんばんですか。',                         # なんばん

    # MNN L5 — Verkehr / Orte
    185: 'ちかくの スーパーで やさいを かいます。',           # スーパー
    190: 'まいあさ バスで かいしゃへ いきます。',             # バス
    191: 'あめでしたから、タクシーで かえりました。',         # タクシー
    213: 'デパートで ははの プレゼントを かいました。',       # デパート
    217: 'ともだちと レストランで ばんごはんを たべました。', # レストラン
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

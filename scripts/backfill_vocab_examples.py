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
    20: 'わたしは がくせいです。',                           # わたし
    21: 'わたしたちは にほんごを べんきょうします。',       # わたしたち
    22: 'あなたは せんせいですか。',                         # あなた
    23: 'あのひとは わたしの ともだちです。',                # あのひと
    24: 'あのかたは やまださんです。',                       # あのかた
    25: 'みなさん、おはようございます。',                    # みなさん
    26: 'たなかせんせいは やさしいです。',                   # せんせい
    27: 'ちちは きょうしです。',                             # きょうし
    28: 'わたしは だいがくの がくせいです。',                # がくせい
    29: 'やまださんは かいしゃいんです。',                   # かいしゃいん
    30: 'ちちは ぎんこうの しゃいんです。',                  # しゃいん
    31: 'ちちは ぎんこういんです。',                         # ぎんこういん
    32: 'はは は いしゃです。',                              # いしゃ
    33: 'かれは けんきゅうしゃです。',                       # けんきゅうしゃ
    34: 'マイクさんは エンジニアです。',                     # エンジニア
    35: 'わたしの だいがくは とうきょうに あります。',       # だいがく
    36: 'びょういんは えきの ちかくです。',                  # びょういん
    37: 'でんきを つけてください。',                         # でんき
    38: 'あのひとは だれですか。',                           # だれ
    39: 'どなたですか。',                                    # どなた
    40: 'わたしは にじゅうごさいです。',                     # さい
    41: 'おこさんは なんさいですか。',                       # なんさい

    # MNN L1 — Laender
    45: 'アメリカに ともだちが います。',                    # アメリカ
    46: 'イギリスは ヨーロッパに あります。',                # イギリス
    47: 'インドは おおきい くにです。',                      # インド
    48: 'インドネシアの りょうりは おいしいです。',          # インドネシア
    49: 'かんこくの えいがを みました。',                    # 韓国
    51: 'ちゅうごくは ひろい くにです。',                    # 中国
    52: 'ドイツは ヨーロッパに あります。',                  # ドイツ
    53: 'にほんは アジアに あります。',                      # 日本

    # MNN L2 — Demonstrativpronomen / -bestimmungswoerter
    56: 'これは ほんです。',                                 # これ
    57: 'それは わたしの かばんです。',                      # それ
    58: 'あれは なんですか。',                               # あれ
    59: 'この ほんは おもしろいです。',                      # この
    60: 'その ペンを ください。',                            # その
    61: 'あの ひとは せんせいです。',                        # あの

    # MNN L2 — Dinge / Floskeln / Getraenke
    76: 'これは わたしの かばんです。',                      # かばん
    84: 'コーヒーを のみます。',                             # コーヒー
    88: 'そうです、にほんじんです。',                        # そう
    93: 'どうも ありがとうございます。',                     # どうも
    94: 'どうぞ、おすわりください。',                        # どうぞ

    # MNN L3 — Zahlen / Geld
    122: 'コーヒーは さんびゃくえんです。',                  # えん
    124: 'これは ひゃくえんです。',                          # ひゃく
    125: 'いちまんは せんの じゅうばいです。',               # せん
    126: 'いちまんえんを はらいました。',                    # まん
    134: 'でんわばんごうを おしえてください。',              # でんわばんごう
    135: 'へやの なんばんですか。',                          # なんばん

    # MNN L5 — Verkehr / Orte
    185: 'スーパーで やさいを かいます。',                   # スーパー
    190: 'バスで かいしゃへ いきます。',                     # バス
    191: 'タクシーで えきへ いきました。',                   # タクシー
    213: 'デパートで ふくを かいました。',                   # デパート
    217: 'レストランで ばんごはんを たべます。',             # レストラン

    # Weitere haeufige Begruessungen / Floskeln
    42: 'しつれいですが、おなまえは なんですか。',           # しつれいですが
    43: 'すみません、おなまえは？',                          # おなまえは？
    44: 'はじめまして、どうぞよろしく。',                    # どうぞよろしく
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

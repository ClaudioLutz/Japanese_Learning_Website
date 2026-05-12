"""Kana-Reihen-Mapping (Gojuon + Erweiterungen).

Zentralisiert die Information, welche Mora zu welcher Reihe gehoert
(a-Reihe, k-Reihe, s-Reihe, ...). Wird sowohl von der TTS-Pause-Heuristik
(`app/routes.py::_maybe_spell_out_kana_row`) als auch vom Kana-Grid-Spiel
verwendet.

Die `_KANA_ROWS`-Liste enthaelt 30 Reihen (15 Hiragana + 15 Katakana inkl.
Dakuten/Handakuten). Yoon-Kombinationen (きゃ/しゃ/...) und die einzelnen
Konsonanten ん/ン sind hier bewusst NICHT enthalten — sie sind keine
"Reihe" im Gojuon-Sinn.
"""
import re
from typing import Optional

# ── Hiragana/Katakana-Reihen (jeweils a-i-u-e-o) ───────────────────────
_KANA_ROWS = [
    # Hiragana — Vokale + Konsonanten-Reihen
    set('あいうえお'), set('かきくけこ'), set('さしすせそ'),
    set('たちつてと'), set('なにぬねの'), set('はひふへほ'),
    set('まみむめも'), set('やゆよ'), set('らりるれろ'), set('わを'),
    # Hiragana — Dakuten + Handakuten
    set('がぎぐげご'), set('ざじずぜぞ'), set('だぢづでど'),
    set('ばびぶべぼ'), set('ぱぴぷぺぽ'),
    # Katakana — Vokale + Konsonanten-Reihen
    set('アイウエオ'), set('カキクケコ'), set('サシスセソ'),
    set('タチツテト'), set('ナニヌネノ'), set('ハヒフヘホ'),
    set('マミムメモ'), set('ヤユヨ'), set('ラリルレロ'), set('ワヲ'),
    # Katakana — Dakuten + Handakuten
    set('ガギグゲゴ'), set('ザジズゼゾ'), set('ダヂヅデド'),
    set('バビブベボ'), set('パピプペポ'),
]

# Regex fuer zusammenhaengende Kana-Bloecke (4-7 Mora) — wird von der
# TTS-Pause-Heuristik benutzt. 4-7 schuetzt Woerter aus EINER Reihe
# (z.B. `あおい` = 3 Vokale) vor faelschlicher Pause-Trennung.
_KANA_BLOCK_RE = re.compile(r'[ぁ-ゖァ-ヺ]{4,7}')

# ── Reihen-Schluessel + Labels (fuer UI) ───────────────────────────────
# Index: Reihen-Schluessel (technisch), Wert: (Label DE, Romaji-Liste)
# Geordnet wie die Gojuon-Tabelle gelesen wird.
ROW_KEYS = [
    'vowels', 'k', 's', 't', 'n', 'h', 'm', 'y', 'r', 'w', 'n_kons',
    'g', 'z', 'd', 'b', 'p',
]

ROW_LABELS = {
    'vowels': 'Vokale',
    'k': 'K-Reihe',
    's': 'S-Reihe',
    't': 'T-Reihe',
    'n': 'N-Reihe',
    'h': 'H-Reihe',
    'm': 'M-Reihe',
    'y': 'Y-Reihe',
    'r': 'R-Reihe',
    'w': 'W-Reihe',
    'n_kons': 'N-Konsonant',
    'g': 'G-Reihe (Dakuten)',
    'z': 'Z-Reihe (Dakuten)',
    'd': 'D-Reihe (Dakuten)',
    'b': 'B-Reihe (Dakuten)',
    'p': 'P-Reihe (Handakuten)',
}

# Romaji pro Reihe (in Gojuon-Reihenfolge a-i-u-e-o)
ROMAJI_ROWS = {
    'vowels': ['a', 'i', 'u', 'e', 'o'],
    'k': ['ka', 'ki', 'ku', 'ke', 'ko'],
    's': ['sa', 'shi', 'su', 'se', 'so'],
    't': ['ta', 'chi', 'tsu', 'te', 'to'],
    'n': ['na', 'ni', 'nu', 'ne', 'no'],
    'h': ['ha', 'hi', 'fu', 'he', 'ho'],
    'm': ['ma', 'mi', 'mu', 'me', 'mo'],
    'y': ['ya', 'yu', 'yo'],
    'r': ['ra', 'ri', 'ru', 're', 'ro'],
    'w': ['wa', 'wo'],
    'n_kons': ['n'],
    'g': ['ga', 'gi', 'gu', 'ge', 'go'],
    'z': ['za', 'ji', 'zu', 'ze', 'zo'],
    'd': ['da', 'ji', 'zu', 'de', 'do'],  # Hinweis: ji/zu sind Homophone mit z-Reihe
    'b': ['ba', 'bi', 'bu', 'be', 'bo'],
    'p': ['pa', 'pi', 'pu', 'pe', 'po'],
}

# Hiragana pro Reihe (a-i-u-e-o)
HIRAGANA_ROWS = {
    'vowels': ['あ', 'い', 'う', 'え', 'お'],
    'k': ['か', 'き', 'く', 'け', 'こ'],
    's': ['さ', 'し', 'す', 'せ', 'そ'],
    't': ['た', 'ち', 'つ', 'て', 'と'],
    'n': ['な', 'に', 'ぬ', 'ね', 'の'],
    'h': ['は', 'ひ', 'ふ', 'へ', 'ほ'],
    'm': ['ま', 'み', 'む', 'め', 'も'],
    'y': ['や', 'ゆ', 'よ'],
    'r': ['ら', 'り', 'る', 'れ', 'ろ'],
    'w': ['わ', 'を'],
    'n_kons': ['ん'],
    'g': ['が', 'ぎ', 'ぐ', 'げ', 'ご'],
    'z': ['ざ', 'じ', 'ず', 'ぜ', 'ぞ'],
    'd': ['だ', 'ぢ', 'づ', 'で', 'ど'],
    'b': ['ば', 'び', 'ぶ', 'べ', 'ぼ'],
    'p': ['ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ'],
}

# Katakana pro Reihe (a-i-u-e-o)
KATAKANA_ROWS = {
    'vowels': ['ア', 'イ', 'ウ', 'エ', 'オ'],
    'k': ['カ', 'キ', 'ク', 'ケ', 'コ'],
    's': ['サ', 'シ', 'ス', 'セ', 'ソ'],
    't': ['タ', 'チ', 'ツ', 'テ', 'ト'],
    'n': ['ナ', 'ニ', 'ヌ', 'ネ', 'ノ'],
    'h': ['ハ', 'ヒ', 'フ', 'ヘ', 'ホ'],
    'm': ['マ', 'ミ', 'ム', 'メ', 'モ'],
    'y': ['ヤ', 'ユ', 'ヨ'],
    'r': ['ラ', 'リ', 'ル', 'レ', 'ロ'],
    'w': ['ワ', 'ヲ'],
    'n_kons': ['ン'],
    'g': ['ガ', 'ギ', 'グ', 'ゲ', 'ゴ'],
    'z': ['ザ', 'ジ', 'ズ', 'ゼ', 'ゾ'],
    'd': ['ダ', 'ヂ', 'ヅ', 'デ', 'ド'],
    'b': ['バ', 'ビ', 'ブ', 'ベ', 'ボ'],
    'p': ['パ', 'ピ', 'プ', 'ペ', 'ポ'],
}


def row_for_romanization(rom: str) -> Optional[str]:
    """Bestimmt die Reihe (vowels/k/s/...) anhand der Romaji-Lesung.

    Beispiel: 'ka' -> 'k', 'a' -> 'vowels', 'gya' -> None (Yoon).
    """
    if not rom:
        return None
    rom_lower = rom.strip().lower()
    for key, romaji_list in ROMAJI_ROWS.items():
        if rom_lower in romaji_list:
            return key
    return None


def row_for_kana(char: str) -> Optional[str]:
    """Bestimmt die Reihe anhand des Kana-Zeichens.

    Beispiel: 'か' -> 'k', 'シ' -> 's', 'きゃ' -> None (Yoon, mehr als 1 Zeichen).
    """
    if not char or len(char) != 1:
        return None
    for key, hira_list in HIRAGANA_ROWS.items():
        if char in hira_list:
            return key
    for key, kata_list in KATAKANA_ROWS.items():
        if char in kata_list:
            return key
    return None


def kana_rows_for_lesson(kana_objects):
    """Gruppiert Kana-Objekte nach Reihe in stabiler ROW_KEYS-Reihenfolge.

    Args:
        kana_objects: iterierbar von Kana-Modell-Instanzen (mit .character, .romanization)

    Returns:
        Liste von Dicts: [{'key': 'vowels', 'label': 'Vokale', 'kana': [<Kana>, ...]}, ...]
        Nur Reihen mit mindestens einem Treffer werden aufgenommen.
    """
    buckets: dict = {key: [] for key in ROW_KEYS}
    leftover = []
    for k in kana_objects:
        key = row_for_kana(k.character) or row_for_romanization(k.romanization)
        if key:
            buckets[key].append(k)
        else:
            leftover.append(k)
    result = []
    for key in ROW_KEYS:
        if buckets[key]:
            result.append({
                'key': key,
                'label': ROW_LABELS[key],
                'kana': buckets[key],
            })
    if leftover:
        result.append({
            'key': 'other',
            'label': 'Sonstige',
            'kana': leftover,
        })
    return result

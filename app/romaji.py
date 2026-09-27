"""Kana → Romaji (modifiziertes Hepburn, Konvention der Seite).

Deterministisch, ohne Modell und ohne pykakasi: gedacht fuer Texte, die schon
als reine Kana vorliegen (Lesung ``reading_kana`` im Rollenspiel, Nutzereingaben
in Kana). Kanji werden NICHT gelesen — dafuer braucht es die Lesung.

Konvention (wie Vokabeln/Beispielsaetze in der DB, z.B. „Tōkyō wa hito ga ōi
desu.“, „kōhī“, „onēsan“, „sen'en“, „kocchi“):

- shi / chi / tsu / fu / ji, Yōon kya/sha/cho …
- Langvokale mit Makron: おう/おお → ō, うう → ū, ああ → ā, ええ → ē;
  いい bleibt ii, えい bleibt ei (sensei). Katakana-Strich ー → Makron des
  vorigen Vokals (kōhī, kēki, takushī).
- Sokuon っ verdoppelt den Folgekonsonanten (gakkō), vor ch als c (kocchi).
- ん = n, vor Vokal oder y als n' (zen'in, kin'yōbi); vor b/m/p bleibt n (sanbyaku).
- Partikeln: は → wa, を → o, へ → e als eigenes Wort, wenn sie am Ende eines
  (durch Leerzeichen getrennten) Wortblocks stehen; ebenso werden が, に, で, も, です,
  ください und satzfinales か/ね/よ abgetrennt. Das Rollenspiel schreibt Kana mit
  Leerzeichen zwischen den Bloecken („わたしは コーヒーが すきです。“) — darauf
  stuetzt sich diese Heuristik. Ohne Leerzeichen bleibt ein Block zusammen.
- Wechsel Katakana → Hiragana trennt ebenfalls (コーヒーを → kōhī o);
  さん/くん/ちゃん/さま nach Katakana werden angehaengt (リサさん → Risa-san).
- Satzzeichen 。、？！ → . , ? !
"""
from __future__ import annotations

import re

__all__ = ['kana_to_romaji', 'is_kana_text', 'romaji_or_empty']

# ── Silbentabelle (Hiragana; Katakana wird vorher umgesetzt) ─────────────

_BASE: dict[str, str] = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'ゐ': 'i', 'ゑ': 'e', 'を': 'o',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'ゔ': 'vu',
    # kleine Vokale/Silben allein
    'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'ゎ': 'wa',
}

_YOON_STEM: dict[str, str] = {
    'き': 'ky', 'ぎ': 'gy', 'し': 'sh', 'じ': 'j', 'ち': 'ch', 'ぢ': 'j',
    'に': 'ny', 'ひ': 'hy', 'び': 'by', 'ぴ': 'py', 'み': 'my', 'り': 'ry',
}
_SMALL_Y = {'ゃ': 'a', 'ゅ': 'u', 'ょ': 'o'}

# Lehnwort-Kombinationen mit kleinen Vokalen (ティ, ファ, シェ …)
_EXTENDED: dict[str, str] = {
    'てぃ': 'ti', 'でぃ': 'di', 'とぅ': 'tu', 'どぅ': 'du', 'でゅ': 'dyu', 'てゅ': 'tyu',
    'ふぁ': 'fa', 'ふぃ': 'fi', 'ふぇ': 'fe', 'ふぉ': 'fo', 'ふゅ': 'fyu',
    'うぃ': 'wi', 'うぇ': 'we', 'うぉ': 'wo',
    'しぇ': 'she', 'じぇ': 'je', 'ちぇ': 'che',
    'つぁ': 'tsa', 'つぃ': 'tsi', 'つぇ': 'tse', 'つぉ': 'tso',
    'ゔぁ': 'va', 'ゔぃ': 'vi', 'ゔぇ': 've', 'ゔぉ': 'vo',
    'いぇ': 'ye', 'くぁ': 'kwa', 'ぐぁ': 'gwa',
}

_MACRON = {'a': 'ā', 'i': 'ī', 'u': 'ū', 'e': 'ē', 'o': 'ō'}
# Vokal + folgende Vokalsilbe → Langvokal (ii und ei bleiben, siehe Modul-Doku)
_LONG = {('a', 'a'): 'ā', ('u', 'u'): 'ū', ('e', 'e'): 'ē', ('o', 'u'): 'ō', ('o', 'o'): 'ō'}

_PUNCT: dict[str, str] = {
    '。': '.', '．': '.', '、': ',', '，': ',', '？': '?', '！': '!', '：': ':', '；': ';',
    '「': '"', '」': '"', '『': '"', '』': '"', '（': '(', '）': ')',
    '・': ' ', '…': '...', '〜': '~', '～': '~', '　': ' ',
}

_HIRA_RE = re.compile(r'[ぁ-ゟ]')
_KATA_RE = re.compile(r'[ァ-ヺー]')
# Erlaubt in „reiner Kana“: Hiragana, Katakana, ー, Leerzeichen, Satzzeichen
_KANA_ONLY_RE = re.compile(
    r'^[ぁ-ゟ゠-ヿ\s。．、，？！?!.,:;：；「」『』（）()・…〜～　"\'-]+$'
)
_SEGMENT_RE = re.compile(r'[ァ-ヺー]+|[ぁ-ゟー]+|.', re.S)

_HONORIFICS = ('さん', 'くん', 'ちゃん', 'さま')
_WHOLE_WORDS = {'こんにちは': 'konnichiwa', 'こんばんは': 'konbanwa'}
_COPULA = ('でしょう', 'でした', 'です')
_POLITE_ENDINGS = ('です', 'でした', 'でしょう', 'ます', 'ました', 'ません', 'ましょう', 'ませんでした')
_FINAL_PARTICLES = ('よね', 'か', 'ね', 'よ')
_NO_SPLIT_GA = {'えいが', 'まんが', 'しょうが'}
_NO_SPLIT_DE = {'うで', 'そで', 'ゆで'}
_NO_SPLIT_WA = {'はは'}
_NO_SPLIT_NI = {'なに', 'くに', 'かに', 'たに', 'わに'}
_NO_SPLIT_MO = {'いつも', 'とても', 'こども', 'でも', 'もも', 'くも', 'しも', 'けれども', 'けども'}


def _kata_to_hira(text: str) -> str:
    return ''.join(chr(ord(ch) - 0x60) if 'ァ' <= ch <= 'ヶ' else ch for ch in text)


def is_kana_text(text: str | None) -> bool:
    """True, wenn der Text nur aus Kana (plus Satzzeichen/Leerzeichen) besteht
    und mindestens ein Kana-Zeichen enthaelt. Kanji/Latein → False."""
    text = (text or '').strip()
    if not text or not _KANA_ONLY_RE.match(text):
        return False
    return bool(_HIRA_RE.search(text) or _KATA_RE.search(text))


def _syllables(kana: str) -> list[str]:
    """Hiragana (mit ー) → Liste von Silben-Romaji; っ als '*', ん als 'N', ー als '-'."""
    out: list[str] = []
    i, n = 0, len(kana)
    while i < n:
        ch = kana[i]
        pair = kana[i:i + 2]
        if pair in _EXTENDED:
            out.append(_EXTENDED[pair])
            i += 2
            continue
        if ch in _YOON_STEM and i + 1 < n and kana[i + 1] in _SMALL_Y:
            out.append(_YOON_STEM[ch] + _SMALL_Y[kana[i + 1]])
            i += 2
            continue
        if ch == 'っ':
            out.append('*')
        elif ch == 'ん':
            out.append('N')
        elif ch == 'ー':
            out.append('-')
        elif ch in _BASE:
            out.append(_BASE[ch])
        else:
            out.append(ch)
        i += 1
    return out


def _join_syllables(sylls: list[str]) -> str:
    res: list[str] = []
    for idx, s in enumerate(sylls):
        nxt = sylls[idx + 1] if idx + 1 < len(sylls) else ''
        if s == '*':
            if nxt and nxt[0].isalpha() and nxt[0] not in 'aiueoN*-':
                res.append('c' if nxt.startswith('ch') else nxt[0])
            continue
        if s == 'N':
            res.append("n'" if nxt and nxt[0] in 'aiueoy' else 'n')
            continue
        if s == '-':
            if res and res[-1] and res[-1][-1] in _MACRON:
                res[-1] = res[-1][:-1] + _MACRON[res[-1][-1]]
            continue
        if res and s in ('a', 'i', 'u', 'e', 'o') and res[-1] and res[-1][-1] in 'aiueo':
            long = _LONG.get((res[-1][-1], s))
            if long:
                res[-1] = res[-1][:-1] + long
                continue
        res.append(s)
    return ''.join(res)


def _plain(kana: str) -> str:
    """Kana-Block (ohne Leerzeichen/Satzzeichen) → Romaji, ohne Partikel-Logik."""
    return _join_syllables(_syllables(_kata_to_hira(kana)))


def _split_hiragana_block(block: str) -> list[str]:
    """Ein Hiragana-Block am Ende eines Wortblocks → [Wort, abgetrennte Endungen …] als Romaji."""
    if block in _WHOLE_WORDS:
        return [_WHOLE_WORDS[block]]
    tail: list[str] = []
    base = block
    stripped = False
    # satzfinales か/ね/よ nach höflicher Endung
    for p in _FINAL_PARTICLES:
        if base.endswith(p) and base[:-len(p)].endswith(_POLITE_ENDINGS):
            tail.insert(0, _plain(p))
            base = base[:-len(p)]
            stripped = True
            break
    # Kopula (です/でした/でしょう) abtrennen, wenn davor noch etwas steht
    for c in _COPULA:
        if base.endswith(c) and len(base) > len(c):
            tail.insert(0, _plain(c))
            base = base[:-len(c)]
            stripped = True
            break
    if not stripped and base.endswith('ください') and len(base) > 4:
        tail.insert(0, 'kudasai')
        base = base[:-4]
        stripped = True
    if not stripped:
        last = base[-1:]
        if last == 'は' and base not in _NO_SPLIT_WA:
            tail.insert(0, 'wa')
            base = base[:-1]
            for p in ('から', 'まで', 'に', 'で', 'と'):
                if base.endswith(p) and len(base) > len(p):
                    tail.insert(0, _plain(p))
                    base = base[:-len(p)]
                    break
        elif last == 'を':
            tail.insert(0, 'o')
            base = base[:-1]
        elif last == 'へ' and len(base) > 1:
            tail.insert(0, 'e')
            base = base[:-1]
        elif last == 'が' and len(base) > 1 and base not in _NO_SPLIT_GA:
            tail.insert(0, 'ga')
            base = base[:-1]
        elif last == 'も' and len(base) > 1 and base not in _NO_SPLIT_MO:
            tail.insert(0, 'mo')
            base = base[:-1]
        elif last == 'に' and len(base) > 1 and base not in _NO_SPLIT_NI:
            tail.insert(0, 'ni')
            base = base[:-1]
        elif (last == 'で' and len(base) > 1 and base not in _NO_SPLIT_DE
              and base[-2] not in 'んい'):     # のんで/たべないで = te-Form, nicht Partikel
            tail.insert(0, 'de')
            base = base[:-1]
    words = [_plain(base)] if base else []
    return words + tail


def _chunk_tokens(chunk: str) -> list[str]:
    """Ein Wortblock (zwischen Leerzeichen/Satzzeichen) → Romaji-Woerter."""
    segs = re.findall(r'[ァ-ヺ]+[ーァ-ヺ]*|[ぁ-ゟー]+', chunk)
    words: list[str] = []
    for k, seg in enumerate(segs):
        is_kata = bool(re.match(r'[ァ-ヺ]', seg))
        last = k == len(segs) - 1
        if not is_kata and k > 0 and words and re.match(r'[ァ-ヺ]', segs[k - 1]):
            hon = next((h for h in _HONORIFICS if seg.startswith(h)), None)
            if hon:
                words[-1] += '-' + _plain(hon)
                seg = seg[len(hon):]
                if not seg:
                    continue
        if is_kata:
            words.append(_plain(seg))
        elif last:
            words.extend(_split_hiragana_block(seg))
        else:
            words.append(_plain(seg))
    return [w for w in words if w]


def _capitalize_sentences(text: str) -> str:
    out: list[str] = []
    up = True
    for ch in text:
        if up and ch.isalpha():
            out.append(ch.upper())
            up = False
            continue
        out.append(ch)
        if ch in '.?!':
            up = True
    return ''.join(out)


def kana_to_romaji(text: str | None, capitalize: bool = False) -> str:
    """Kana-Text → Romaji (modifiziertes Hepburn, siehe Modul-Doku).

    Nicht-Kana-Zeichen (Kanji, Latein, Ziffern) werden unveraendert durchgereicht.
    ``capitalize=True``: Satzanfaenge gross (Beispielsatz-Stil der Seite).
    """
    text = (text or '').strip()
    if not text:
        return ''
    parts: list[str] = []
    chunk = ''

    def flush() -> None:
        nonlocal chunk
        if chunk:
            parts.append(' '.join(_chunk_tokens(chunk)))
            chunk = ''

    for ch in text:
        if _HIRA_RE.match(ch) or _KATA_RE.match(ch):
            chunk += ch
            continue
        flush()
        if ch in _PUNCT:
            mapped = _PUNCT[ch]
            parts.append(mapped if mapped.strip() else ' ')
        elif ch.isspace():
            parts.append(' ')
        else:
            parts.append(ch)
    flush()
    out = ''
    for p in parts:
        if p in ('.', ',', '?', '!', ':', ';', '...', ')'):
            out = out.rstrip(' ') + p + ' '
        elif p == '(':
            out += ' ('
        elif p == ' ':
            out += ' '
        else:
            if out and not out.endswith((' ', '(', '"')) and p[:1].isalnum() and out[-1:].isalnum():
                out += ' '
            out += p
    out = re.sub(r'\s{2,}', ' ', out).strip()
    out = re.sub(r'\(\s+', '(', out)
    return _capitalize_sentences(out) if capitalize else out


def romaji_or_empty(kana: str | None, capitalize: bool = True) -> str:
    """Romaji nur fuer reine Kana-Texte, sonst '' (z.B. Nutzer-Freitext mit Kanji)."""
    return kana_to_romaji(kana, capitalize=capitalize) if is_kana_text(kana) else ''

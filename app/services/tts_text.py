# -*- coding: utf-8 -*-
"""Zentrale Text-Aufbereitung für die DE/JP-Vorlese-Pipeline (TTS).

Single source of truth für (a) das Splitten eines gemischt deutsch/japanischen
Textes in Sprachsegmente (japanische Schrift → Gemini-Stimme, Lateinschrift →
deutsche Neural2-Stimme), (b) das Strippen von Markdown/Romaji-Lesehilfen und
(c) das Reinigen der Segmente, damit keine nicht-sprechbaren Zeichen
(Bindestriche, Pfeile, Klammern, Slashes ...) mitgelesen werden.

Hintergrund (Bug 2026-06-14): ``segment_by_language`` hängte neutrale Zeichen
(inkl. ``—`` / ``→`` / ``/``) an das laufende Segment; ``.strip()`` entfernte
nur Whitespace. Beispiel ``じ (ji) — Stunde`` wurde nach dem Romaji-Strip zu
``じ — Stunde`` und ergab das JP-Segment ``じ —`` → die generative Gemini-Stimme
las den Strich als „Minus" vor (die zuvor verwendete ``ja-JP-Neural2-B``-Stimme
verschluckte ihn noch als Pause, daher fiel es erst nach der Gemini-Migration
vom 2026-05-12 auf). Analog las die deutsche Stimme führende ``→``-Pfeile von
Übersetzungszeilen (``→ Ab wann ...``) als „Pfeil nach rechts" mit.

Dieses Modul ist bewusst ein reines Leaf-Modul (nur ``re``, keine App-/Flask-
Abhängigkeit), damit es schnell und isoliert in ``tests/unit/test_tts_text.py``
testbar ist. Der Block-Player (``gen_text_audio.py``) importiert von hier.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Markdown-Strip + Romaji-Strip
# ---------------------------------------------------------------------------
_MD_PATTERNS = [
    (re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE), ""),        # # Headings → Text
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), ""),                    # ![alt](url) → entfernt
    (re.compile(r"\[([^\]]+)\]\([^)]*\)"), r"\1"),               # [text](url) → text (URL weg!)
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),                        # **bold** → bold
    (re.compile(r"(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)"), r"\1"),   # *italic* → italic
    (re.compile(r"~~(.+?)~~"), r"\1"),                            # ~~strike~~ → strike
    (re.compile(r"`([^`\n]+)`"), r"\1"),                           # `code` → code
    (re.compile(r"^\s*>\s+", re.MULTILINE), ""),                   # > quote → quote
    (re.compile(r"^\s*[-*+]\s+", re.MULTILINE), ""),               # - list → list
    (re.compile(r"^\s*\d+\.\s+", re.MULTILINE), ""),               # 1. list → list
    (re.compile(r"^---+\s*$", re.MULTILINE), ""),                  # --- hr → leer
]

# Klammer direkt nach JP-Zeichen wird vor TTS entfernt — das ist eine Lesehilfe
# (Romaji, Bedeutung) und gehört nicht ins Audio. Erlaubt eine Ebene
# Verschachtelung, damit ``(ya, 'und (unter anderem)')`` und
# ``(い**がつ**, ichi-gatsu, Januar)`` komplett verschwinden.
#
# Die Lookbehind-Klasse umfasst NEBEN den Schrift-Ranges auch japanische
# Satzzeichen und Klammern (``。、！？…・「」 ...``). Hintergrund (Bug 2026-06-15,
# Lektion 145): endet die japanische Zeile auf ``。`` bevor der Romaji folgt
# (``…おきますか。 (Risa-san, … okimasu ka.)``), griff die alte Klasse nicht — der
# Romaji blieb stehen und wurde von der DEUTSCHEN Neural2-Stimme als Latein
# mitgelesen (klang wie „deutsche Stimme spricht japanisch"). ``。`` u.ä. liegen
# im CJK-Punktuation-Block (U+3000–U+303F), der von ``぀-ヿ`` NICHT erfasst wird.
_JP_LOOKBEHIND = "぀-ヿ㐀-鿿ｦ-ﾟ。、，！？…‥・「」『』【】〔〕《》〜～"
_ROMAJI_AFTER_JP = re.compile(rf"(?<=[{_JP_LOOKBEHIND}])\s*\((?:[^()]|\([^()]*\))*\)")


def strip_markdown(text: str) -> str:
    out = text
    for pat, repl in _MD_PATTERNS:
        out = pat.sub(repl, out)
    return out


def strip_romaji_after_jp(text: str) -> str:
    """Entfernt ``(romaji)`` direkt nach JP-Zeichen — Ohren brauchen sie nicht.

    Beispiele die GESTRIPPT werden:
      - 「ちち」 (chichi) → 「ちち」
      - 家族 (kazoku, Familie) → 家族
    Beispiele die BLEIBEN:
      - Eltern (beide zusammen) — keine JP davor → bleibt
    """
    return _ROMAJI_AFTER_JP.sub("", text)


# ---------------------------------------------------------------------------
# Zeichen-Klassifikation
# ---------------------------------------------------------------------------
_JP_RE = re.compile(r"[぀-ゟ゠-ヿ㐀-䶿一-鿿ｦ-ﾟ]")
_LATIN_RE = re.compile(r"[A-Za-zÀ-ſ]")


def char_lang(ch: str) -> str | None:
    """Klassifiziert ein Zeichen als 'ja' / 'de' / None (neutral: Ziffer, Space, Satzzeichen)."""
    if _JP_RE.match(ch):
        return "ja"
    if _LATIN_RE.match(ch):
        return "de"
    return None


# ---------------------------------------------------------------------------
# Segment-Reinigung (gegen vorgelesene Trennzeichen / „Minus" / „Pfeil")
# ---------------------------------------------------------------------------
# Global (an JEDER Position, nicht nur am Rand) entfernte, nie sprechbare Zeichen:
#   - Japanische Anführungs-/Schmuckklammern  「」『』【】〔〕《》
#   - Tilde / Wellenstrich  ~ (U+007E)  〜 (U+301C)  ～ (U+FF5E)
# Hintergrund (Bug 2026-06-15, Lektion 145): die Tilde wird in den Lektionen als
# PLATZHALTER benutzt (``～時 ～分``, ``～から ～まで``, ``～ます``). Landete sie in
# einem deutschen Segment (``…enden auf ～``, ``(von ~ bis ~)``), las die Neural2-
# Stimme sie wörtlich als „Tilde". Da sie reiner Platzhalter ist (nie Lautwert),
# wird sie in BEIDEN Sprachen entfernt. Der Chōon ``ー`` (U+30FC, Vokaldehnung in
# コーヒー) ist ein ANDERES Zeichen und bleibt unverändert sprechbar.
_DROP_GLOBAL_RE = re.compile(r"[「」『』【】〔〕《》~〜～]")

# Ein einzelnes Trenn-Symbol, das von Whitespace UMGEBEN ist (interner Trenner
# zwischen zwei Begriffen). Wird durch eine Pause ersetzt, damit z.B.
# ``あめ / かさ / みず`` oder ``H → B`` oder ``gut — schön`` nicht das Symbol
# vorlesen. Hyphen OHNE Spaces (Komposita wie ``T-Reihe``) bleibt unangetastet.
_INTERNAL_SEP_RE = re.compile(
    r"\s+[-‐-―−－→←↔⇒⇐⟶/／|｜・]\s+"
)

# Nicht-sprechbare Zeichen, die am ANFANG/ENDE eines Segments getrimmt werden.
# Bewusst NICHT enthalten (sprechbar / Prosodie / bedeutungstragend):
#   - Buchstaben, Ziffern, japanische Schrift
#   - Satz-Schluss-Zeichen  . , ! ? 。 、 ！ ？ …
#   - ー (Chōon), 々 ヽ ヾ ゝ ゞ (Iteration)
# (Die Tilde/Wellenstrich ~ 〜 ～ wird bereits durch _DROP_GLOBAL_RE entfernt.)
_BOUNDARY_STRIP = (
    " \t\n\r\f\v　"
    "-‐‑‒–—―−－"   # - ‐ ‑ ‒ – — ― − －
    "→←↔⇒⇐⟶➙➜"    # → ← ↔ ⇒ ⇐ ⟶ ➙ ➜
    "/／\\・·•"                          # / ／ \ ・ · •
    "|｜"                                              # | ｜
    ":：;；=＝*＊#＃+＋"          # : ： ; ； = ＝ * ＊ # ＃ + ＋
    ">＞<＜"                                       # > ＞ < ＜
    "()（）[]［］{}｛｝"          # ( ) （ ） [ ] ［ ］ { } ｛ ｝
    "«»“”‘’„‹›"  # « » “ ” ‘ ’ „ ‹ ›
    "゠"                                              # ゠ (Katakana-Doppelbindestrich)
)

# Mindestens ein „echtes" sprechbares Zeichen (Buchstabe / Ziffer / JP-Schrift).
_SPEAKABLE_RE = re.compile(r"[0-9A-Za-zÀ-ɏ぀-ヿ㐀-鿿一-龥ｦ-ﾟ]")


def clean_tts_segment(text: str, lang: str = "ja") -> str:
    """Bereinigt ein Sprachsegment vor dem TTS-Call.

    1. Japanische Anführungsklammern (「」『』 ...) werden global entfernt.
    2. Interne, von Whitespace umgebene Trenn-Symbole (`` — ``, `` → ``, `` / ``)
       werden durch eine Pause ersetzt (JP: ``、``, DE: ``, ``).
    3. Nicht-sprechbare Zeichen an den Rändern werden getrimmt.
    4. Bleibt danach kein sprechbares Zeichen übrig (reiner Satzzeichen-Rest),
       wird ein leerer String zurückgegeben → das Segment wird verworfen.

    Sprechbare/bedeutungstragende japanische Zeichen (``ー`` Chōon, ``々`` ...)
    bleiben erhalten (z.B. ``コーヒー`` bleibt ``コーヒー``). Die Tilde/Wellenstrich
    (``~ 〜 ～``, reiner Platzhalter) wird dagegen entfernt.
    """
    if not text:
        return ""
    text = text.strip()
    pause = "、" if lang == "ja" else ", "
    out = _DROP_GLOBAL_RE.sub("", text)
    out = _INTERNAL_SEP_RE.sub(pause, out)
    out = out.strip(_BOUNDARY_STRIP)
    if not _SPEAKABLE_RE.search(out):
        return ""
    return out


def segment_by_language(text: str) -> list[tuple[str, str]]:
    """Splittet einen Text in ``[(lang, segment)]``-Tupel (gereinigt).

    Neutrale Zeichen (Ziffern, Leerzeichen, Satzzeichen) werden dem aktuellen
    Segment angehängt; ein Wechsel von 'ja' nach 'de' (oder umgekehrt) startet
    ein neues Segment. Jedes Segment durchläuft ``clean_tts_segment`` —
    nicht-sprechbare Rand-/Trennzeichen werden entfernt und reine
    Satzzeichen-Segmente verworfen.
    """
    segments: list[tuple[str, str]] = []
    current_lang: str | None = None
    buf: list[str] = []

    for ch in text:
        lang = char_lang(ch)
        if lang is None:
            buf.append(ch)
            continue
        if current_lang is None:
            current_lang = lang
            buf.append(ch)
        elif lang == current_lang:
            buf.append(ch)
        else:
            seg = clean_tts_segment("".join(buf), current_lang)
            if seg:
                segments.append((current_lang, seg))
            current_lang = lang
            buf = [ch]
    if buf and current_lang:
        seg = clean_tts_segment("".join(buf), current_lang)
        if seg:
            segments.append((current_lang, seg))
    return segments

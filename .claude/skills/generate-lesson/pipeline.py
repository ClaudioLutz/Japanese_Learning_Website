"""
generate-lesson pipeline — Persistiert Claude-generierte Lektionen in Postgres.

Claude produziert JSON-Drafts (siehe SKILL.md §5 für Schema).
Dieses Script validiert, persistiert, und loggt.

Subcommands:
  status                 # DB-Gap-Analyse: welche JLPT-Themen fehlen?
  validate <draft.json>  # Prüft Constraints (STRENG: Niveau-Mix-Verbot via canonical list)
  images   <draft.json>  # Generiert Nano-Banana-Bilder für Thumbnail/Vokabeln
  insert   <draft.json>  # Transaktionaler INSERT, gibt lesson_id zurück
  text-audio <lesson_id> # Block-Player pro Text (DE+JA, Gemini/Neural2)
  slideshow <lesson_id>  # Pro-Zeile Slideshow (TTS + Nano Banana)
  coverage [level]       # JLPT-Coverage-Dashboard: DB vs. canonical list (default: 5)
  used-words             # Report: welche Vokabeln werden ueber wie viele Lektionen genutzt
  commit   <lesson_id>   # Git-add/commit/push (nur Metadaten, kein App-Code)
  export <lesson_id> <out.json>  # Lektion (komplett) aus DB ins Migrations-JSON
  import <in.json>       # Migrations-JSON in die (Ziel-)DB importieren (Dev->Prod)

JLPT-Leitprinzip (Mayuko-Direktive 2026-04-25, siehe improve-jpl §1.5):
  Eine N5-Lektion enthaelt NUR N5-Inhalte. Vokabel-Wort nicht in canonical
  N5-Liste → ERROR. Kanji im example_sentence_japanese nicht in canonical
  N5-Kanji-Set → ERROR. Source: sources/jlpt_n5_canonical.json (elzup MIT
  + AnchorI permissive, derived from Tanos).

Usage: python .claude/skills/generate-lesson/pipeline.py <subcommand> [args]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# --- Projekt-Setup ---
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env laden, damit Subcommands (images/text-audio/slideshow) die API-Keys + DATABASE_URL
# sehen, BEVOR der App-Kontext erstellt wird (cmd_images prueft GOOGLE_AI_API_KEY direkt,
# noch vor create_app — ohne dies SKIP trotz gesetztem Key in der .env).
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass
# os.chdir(PROJECT_ROOT) passiert in main() — beim Import KEIN Seiteneffekt
# (sonst nicht test-importierbar; Tests laufen aus dem Repo-Root).


# ========================================================================
# VALIDATION
# ========================================================================

# Harte Constraints aus SKILL.md §3
ALLOWED_QUIZ_TYPES = {"multiple_choice", "true_false", "matching"}
ALLOWED_JLPT = {4, 5}
ALLOWED_CONTENT_TYPES = {"kana", "kanji", "vocabulary", "grammar", "text", "image", "video", "audio"}
ALLOWED_PAGE_TYPES = {"normal", "quiz_carousel"}

REQUIRED_LESSON_FIELDS = ["title", "description", "jlpt_level", "topic", "pages"]
REQUIRED_VOCAB_FIELDS = [
    "word", "reading", "romaji", "meaning", "meaning_de", "jlpt_level",
    # Pflicht-Feld fuer den Audio-Button auf der Vokabel-Karte:
    # genau EIN rein japanischer Satz, der von der ja-JP-Stimme vorgelesen
    # wird (siehe SKILL.md "Vocabulary.example_sentence_japanese").
    "example_sentence_japanese",
]
REQUIRED_GRAMMAR_FIELDS = ["title", "explanation", "structure", "romaji", "jlpt_level", "tts_example_jp"]

# Hiragana, Katakana, CJK Unified, Halfwidth Katakana — fuer tts_example_jp-Validierung.
_JP_CHAR_RE = re.compile(r'[぀-ゟ゠-ヿ一-鿿ｦ-ﾟ]')
# Lateinische Buchstaben — sollen NICHT in tts_example_jp vorkommen, sonst spricht
# die ja-JP-Stimme den Romaji aus oder die Route lehnt mit 400 ab.
_LATIN_LETTER_RE = re.compile(r'[A-Za-zĀ-ž]')
REQUIRED_KANA_FIELDS = ["character", "romanization", "type"]

# Lesson-Kind-Discriminator (default: vocabulary). 'kana' = Schreibsystem-Lektion
# (Hiragana/Katakana). Bei 'kana' werden Vocabulary/Grammar/N5-Canonical-Checks
# uebersprungen; statt dessen werden Kana-Eintraege validiert und inseriert.
ALLOWED_LESSON_KINDS = {"vocabulary", "kana"}
ALLOWED_KANA_TYPES = {"hiragana", "katakana"}

# Kern-Funktionswoerter, deren Wiederverwendung ueber mehrere Lektionen
# paedagogisch ERWUENSCHT ist (Spaced Repetition struktureller Bausteine).
# Diese loesen KEINE Wiederverwendungs-Warnung aus (siehe reused_words_warning).
# Bewusst konservativ gehalten: Inhaltswoerter (Nomen/Verben/Adjektive) sollen
# weiterhin als "schon in anderer Lektion unterrichtet" gemeldet werden, damit
# neue Lektionen primaer NEUE Lern-Vokabeln einfuehren (User-Direktive 2026-06-21).
CORE_FUNCTION_WORDS = {
    # Personalpronomen
    "わたし", "私", "あなた", "かれ", "彼", "かのじょ", "彼女", "わたしたち",
    # Demonstrativa (kosoado)
    "これ", "それ", "あれ", "この", "その", "あの", "どれ", "どの",
    "ここ", "そこ", "あそこ", "どこ", "こちら", "そちら", "あちら", "どちら",
    # Kopula / Hilfsverben / strukturelle Verben
    "です", "ます", "でした", "だ", "ある", "いる", "する", "なる",
    # Frageworte
    "なに", "何", "だれ", "誰", "いつ", "いくつ", "いくら", "どう", "どうして",
    # Bejahung / Verneinung
    "はい", "いいえ",
}

# Roher HTML in content_text ist verboten (auch wenn Bleach in markdown_safe
# strippt — Verschwendung). Markdown-Bausteine sind erlaubt: ## Headlines, **bold**,
# *italic*, - Listen, > Blockquote, `code`, --- hr.
HTML_TAG_RE = __import__("re").compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
# Heuristik fuer Markdown-Hierarchie (User-Direktive 2026-04-25: jeder text-Block
# braucht visuelle Differenzierung, sonst sieht alles gleich aus).
MD_HEADING_RE = __import__("re").compile(r"^#{2,4}\s+\S", __import__("re").MULTILINE)
MD_BOLD_RE = __import__("re").compile(r"\*\*[^*\n]+\*\*")
MD_LIST_RE = __import__("re").compile(r"^\s*(?:[-*]|\d+\.)\s+\S", __import__("re").MULTILINE)
MD_BLOCKQUOTE_RE = __import__("re").compile(r"^>\s+\S", __import__("re").MULTILINE)

# Kanji-Range fuer Tokenisierung von Beispielsaetzen
KANJI_RE = __import__("re").compile(r"[一-鿿]")
KANA_ONLY_RE = __import__("re").compile(r"^[぀-ヿ\s　、。「」々ー]+$")


class ValidationError(Exception):
    pass


# ========================================================================
# CANONICAL JLPT LISTS (Mayuko-Direktive 2026-04-25: strenger Niveau-Mix)
# ========================================================================

_CANONICAL_CACHE: dict[int, dict] = {}


def load_canonical(level: int) -> dict:
    """Laedt canonical JLPT-Level-Daten (Vokabeln, Kanji, Grammatik).

    Liefert dict mit Schluesseln 'vocab_set', 'kanji_set', 'vocab_list', 'kanji_list'.
    Cached pro Level. Wirft FileNotFoundError, wenn die canonical JSON fehlt.
    """
    if level in _CANONICAL_CACHE:
        return _CANONICAL_CACHE[level]
    path = SKILL_DIR / "sources" / f"jlpt_n{level}_canonical.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Canonical JLPT-N{level}-Liste fehlt: {path}\n"
            f"Aktuell verfuegbar: nur N5. Andere Levels brauchen Manual-Import."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    cache = {
        "raw": data,
        "vocab_list": data.get("vocab", []),
        "kanji_list": data.get("kanji", []),
        "vocab_set": {v["word"] for v in data.get("vocab", [])},
        "vocab_reading_set": {(v["word"], v["reading"]) for v in data.get("vocab", [])},
        "kanji_set": {k["char"] for k in data.get("kanji", [])},
    }
    _CANONICAL_CACHE[level] = cache
    return cache


def is_pure_kana(s: str) -> bool:
    """True wenn String nur Hiragana/Katakana/Satzzeichen enthaelt (keine Kanji)."""
    return bool(KANA_ONLY_RE.match(s)) if s else True


def extract_kanji(text: str) -> set[str]:
    """Gibt Set aller Kanji-Zeichen im Text zurueck."""
    return set(KANJI_RE.findall(text or ""))


_QUIZ_JP_RE = re.compile(r"[぀-ゟ゠-ヿｦ-ﾟ一-鿿]")
_QUIZ_ASCII_RE = re.compile(r"[A-Za-z]")
_QUIZ_BRACKET_RE = re.compile(r"[「」『』【】\[\]\s]")


def _needs_romaji_in_quiz(text: str) -> bool:
    """True, wenn Quiz-Text japanische Schrift enthaelt aber kein lateinisches
    Alphabet (= kein Romaji). Skippt 1-2-Zeichen Kana-only (z.B. Partikel-
    Optionen wie 「は」/「が」 — der Lerner kann sie selbst lesen)."""
    if not text:
        return False
    if not _QUIZ_JP_RE.search(text):
        return False
    if _QUIZ_ASCII_RE.search(text):
        return False
    core = _QUIZ_BRACKET_RE.sub("", text)
    has_kanji = bool(re.search(r"[一-鿿]", core))
    if not has_kanji and len(core) <= 2:
        return False
    return True


def validate_draft(draft: dict) -> list[str]:
    """Validiert den Draft. Gibt Liste von Fehlern zurueck (leer = OK)."""
    errors = []

    # Lesson-Meta
    for f in REQUIRED_LESSON_FIELDS:
        if f not in draft:
            errors.append(f"Lesson fehlt Feld: {f}")

    jlpt = draft.get("jlpt_level")
    if jlpt not in ALLOWED_JLPT:
        errors.append(f"jlpt_level={jlpt} nicht erlaubt. Erlaubt: {sorted(ALLOWED_JLPT)}")

    # Lesson-Kind-Discriminator: 'vocabulary' (default) oder 'kana'
    kind = draft.get("kind", "vocabulary")
    if kind not in ALLOWED_LESSON_KINDS:
        errors.append(f"kind={kind} nicht erlaubt. Erlaubt: {sorted(ALLOWED_LESSON_KINDS)}")

    pages = draft.get("pages", [])
    if len(pages) < 3:
        errors.append(f"Mindestens 3 Pages erforderlich, hat {len(pages)}")

    # Quiz-Carousel muss vorhanden sein
    if not any(p.get("page_type") == "quiz_carousel" for p in pages):
        errors.append("Mindestens eine Page muss page_type='quiz_carousel' sein")

    # Pages + Content
    vocab_count = 0
    grammar_count = 0
    kana_count = 0
    quiz_count = 0
    quiz_types_seen = set()

    for p_idx, page in enumerate(pages, start=1):
        pt = page.get("page_type", "normal")
        if pt not in ALLOWED_PAGE_TYPES:
            errors.append(f"Page {p_idx}: page_type={pt} nicht erlaubt")

        for c_idx, item in enumerate(page.get("contents", []), start=1):
            ct = item.get("content_type")
            if ct not in ALLOWED_CONTENT_TYPES:
                errors.append(f"Page {p_idx}.{c_idx}: content_type={ct} nicht erlaubt")
                continue

            # HTML-Tag-Check fuer text-Content: roher HTML bleibt verboten
            # (markdown_safe nutzt Bleach-Whitelist, alles andere wird gestrippt).
            if ct == "text":
                data = item.get("data", {})
                ctext = data.get("content_text", "")
                tags = HTML_TAG_RE.findall(ctext)
                if tags:
                    errors.append(
                        f"Page {p_idx}.{c_idx} text: roher HTML verboten "
                        f"(markdown_safe rendert Markdown — `<p>`/`<div>`/`<script>` werden gestrippt). "
                        f"Gefunden: {tags[:3]}. Nutze Markdown: ## Headline, **bold**, - Liste, > Quote."
                    )
                # Markdown-Hierarchie-Pflicht (User-Direktive 2026-04-25):
                # Skip Quiz-Intro (sehr kurz) und Dialog-Block (Speaker: ... Format).
                # Heuristik: >=4 Zeilen, die mit "Name:" beginnen, ist ein Dialog.
                speaker_lines = sum(
                    1 for line in ctext.split("\n")
                    if line.strip() and ":" in line.split()[0]
                )
                # Dialog erkannt an bekannten Namen ODER >=4 Sprecher-Zeilen (beliebige Namen).
                is_dialog = (
                    "Tanaka:" in ctext or "Lisa:" in ctext or "Speaker:" in ctext
                    or speaker_lines >= 4
                )
                # Heuristik: wenn >=4 Sprecher-Zeilen, ist es ein Dialog → keine Heading-Pflicht
                if not is_dialog and len(ctext) >= 200:
                    has_heading = bool(MD_HEADING_RE.search(ctext))
                    bold_count = len(MD_BOLD_RE.findall(ctext))
                    has_list_or_quote = bool(MD_LIST_RE.search(ctext) or MD_BLOCKQUOTE_RE.search(ctext))
                    missing = []
                    if not has_heading:
                        missing.append("mind. 1× ## Headline")
                    if bold_count < 2:
                        missing.append(f"mind. 2× **bold** (gefunden: {bold_count})")
                    if not has_list_or_quote:
                        missing.append("mind. 1× Liste (- ...) oder Blockquote (> ...)")
                    if missing:
                        errors.append(
                            f"Page {p_idx}.{c_idx} text: Markdown-Hierarchie unvollstaendig — {', '.join(missing)}. "
                            f"Reine Prosa-Bloecke sind verboten (User-Direktive 2026-04-25: 'sieht alles gleich aus')."
                        )

            if ct == "kana":
                data = item.get("data", {})
                kana_count += 1
                for f in REQUIRED_KANA_FIELDS:
                    if f not in data:
                        errors.append(f"Page {p_idx}.{c_idx} Kana fehlt: {f}")
                ktype = data.get("type")
                if ktype not in ALLOWED_KANA_TYPES:
                    errors.append(
                        f"Page {p_idx}.{c_idx} Kana '{data.get('character')}': "
                        f"type={ktype} ungueltig. Erlaubt: {sorted(ALLOWED_KANA_TYPES)}"
                    )
                # Character muss zu type passen (Hiragana/Katakana-Range)
                ch = data.get("character", "")
                if ch and ktype == "hiragana":
                    import re as _re
                    if not _re.match(r"^[぀-ゟ]+$", ch):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Kana '{ch}': nicht in Hiragana-Range"
                        )
                elif ch and ktype == "katakana":
                    import re as _re
                    if not _re.match(r"^[゠-ヿ]+$", ch):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Kana '{ch}': nicht in Katakana-Range"
                        )

            elif ct == "vocabulary":
                data = item.get("data", {})
                vocab_count += 1
                for f in REQUIRED_VOCAB_FIELDS:
                    if f not in data:
                        errors.append(f"Page {p_idx}.{c_idx} Vocabulary fehlt: {f}")
                v_jlpt = data.get("jlpt_level")
                if v_jlpt is not None and v_jlpt < jlpt:
                    # Niedriger ist OK (z.B. N5-Vokabel in N4-Lektion)
                    pass
                elif v_jlpt is not None and v_jlpt > jlpt:
                    errors.append(
                        f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                        f"jlpt_level={v_jlpt} > Lesson-Level {jlpt}"
                    )

                # Mayuko-Direktive 2026-04-25: STRENG, Niveau-Mix verboten.
                # Vokabel-Wort MUSS in canonical-Liste des Lesson-Levels stehen,
                # ausser explizit als is_proper_noun=true markiert (Namen) oder
                # is_canonical_override=true (selten, mit Begruendung in source_note).
                if jlpt == 5 and not data.get("is_proper_noun") and not data.get("is_canonical_override"):
                    try:
                        canon = load_canonical(5)
                        word = data.get("word", "")
                        if word and word not in canon["vocab_set"]:
                            errors.append(
                                f"Page {p_idx}.{c_idx} Vocabulary '{word}' "
                                f"NICHT in canonical N5-Liste (sources/jlpt_n5_canonical.json). "
                                f"Mayuko-Direktive: kein Niveau-Mix in N5. "
                                f"Falls Eigenname → data.is_proper_noun=true; "
                                f"falls bewusste Ausnahme → data.is_canonical_override=true + source_note."
                            )
                    except FileNotFoundError as e:
                        errors.append(f"Canonical-Liste fehlt: {e}")

                # example_sentence_japanese: rein Japanisch + Satzende — sonst
                # lehnt /api/tts mit lang=ja den Text ab und der Audio-Button
                # auf der Karte bleibt stumm. Identische Regel wie Grammar.tts_example_jp.
                ex_jp = data.get("example_sentence_japanese", "")
                if isinstance(ex_jp, str) and ex_jp.strip():
                    if not _JP_CHAR_RE.search(ex_jp):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                            f"example_sentence_japanese enthaelt keine japanischen Zeichen — "
                            f"die ja-JP-Stimme kann das nicht vorlesen."
                        )
                    if _LATIN_LETTER_RE.search(ex_jp):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                            f"example_sentence_japanese enthaelt lateinische Buchstaben "
                            f"(Romaji/Uebersetzung). Erlaubt: nur reine JP-Schrift."
                        )
                    if not re.search(r'[。！？]', ex_jp):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                            f"example_sentence_japanese muss mit 。 / ！ / ？ enden "
                            f"(genau ein vollstaendiger Satz)."
                        )

                # example_sentence_english: Format "Romaji — Deutsche Uebersetzung".
                # Em-Dash (` — `) trennt Romaji-Praefix von der deutschen Uebersetzung.
                # Die Karten-Rueckseite zerlegt den String in zwei Zeilen unter dem
                # JP-Beispielsatz; ohne Trenner bleibt die Romaji-Zeile leer.
                ex_en = data.get("example_sentence_english", "")
                if isinstance(ex_en, str) and ex_en.strip():
                    if ' — ' not in ex_en:
                        errors.append(
                            f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                            f"example_sentence_english muss Format 'Romaji — Deutsche Uebersetzung' "
                            f"haben (Em-Dash ' — ' als Trenner). Sonst kann die Karten-Rueckseite "
                            f"Romaji und Uebersetzung nicht getrennt anzeigen."
                        )
                    elif _JP_CHAR_RE.search(ex_en.split(' — ', 1)[0]):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Vocabulary '{data.get('word')}': "
                            f"Romaji-Teil von example_sentence_english enthaelt japanische "
                            f"Zeichen — der Praefix vor ' — ' muss reines Hepburn-Romaji sein."
                        )

            elif ct == "grammar":
                data = item.get("data", {})
                grammar_count += 1
                for f in REQUIRED_GRAMMAR_FIELDS:
                    if f not in data:
                        errors.append(f"Page {p_idx}.{c_idx} Grammar fehlt: {f}")
                # Grammatik-Level-Check (analog zu Vocabulary)
                g_jlpt = data.get("jlpt_level")
                if g_jlpt is not None and g_jlpt > jlpt:
                    errors.append(
                        f"Page {p_idx}.{c_idx} Grammar '{data.get('title')}': "
                        f"jlpt_level={g_jlpt} > Lesson-Level {jlpt}"
                    )
                # tts_example_jp: rein Japanisch + Satzende — sonst lehnt
                # /api/tts mit lang=ja den Text mit HTTP 400 ab.
                tts = data.get("tts_example_jp", "")
                if isinstance(tts, str) and tts.strip():
                    if not _JP_CHAR_RE.search(tts):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Grammar '{data.get('title')}': "
                            f"tts_example_jp enthaelt keine japanischen Zeichen — "
                            f"die ja-JP-Stimme kann das nicht vorlesen."
                        )
                    if _LATIN_LETTER_RE.search(tts):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Grammar '{data.get('title')}': "
                            f"tts_example_jp enthaelt lateinische Buchstaben "
                            f"(Romaji/Uebersetzung). Erlaubt: nur reine JP-Schrift."
                        )
                    if not re.search(r'[。！？]', tts):
                        errors.append(
                            f"Page {p_idx}.{c_idx} Grammar '{data.get('title')}': "
                            f"tts_example_jp muss mit 。 / ！ / ？ enden "
                            f"(genau ein vollstaendiger Satz)."
                        )

            # Quiz-Fragen (in quiz_carousel)
            for q_idx, q in enumerate(item.get("quiz_questions", []), start=1):
                qt = q.get("question_type")
                if qt not in ALLOWED_QUIZ_TYPES:
                    errors.append(
                        f"Page {p_idx}.{c_idx}.Q{q_idx}: question_type={qt} "
                        f"VERBOTEN. Erlaubt: {sorted(ALLOWED_QUIZ_TYPES)}"
                    )
                else:
                    quiz_types_seen.add(qt)
                quiz_count += 1

                if qt == "multiple_choice":
                    opts = q.get("options", [])
                    if len(opts) != 4:
                        errors.append(
                            f"Page {p_idx}.{c_idx}.Q{q_idx}: multiple_choice braucht "
                            f"genau 4 Optionen, hat {len(opts)}"
                        )
                    correct = sum(1 for o in opts if o.get("is_correct"))
                    if correct != 1:
                        errors.append(
                            f"Page {p_idx}.{c_idx}.Q{q_idx}: multiple_choice braucht "
                            f"genau 1 richtige Option, hat {correct}"
                        )

                # Romaji-Pflicht in Quiz-Texten (User-Direktive 2026-04-28):
                # Jeder japanische Quiz-Inhalt MUSS Romaji enthalten (Pattern:
                # `JP-Text (romaji)` oder `Kanji (kana, romaji)`). Sonst ist die
                # Aufgabe fuer N5/N4-Lerner nicht lesbar. Erkannt: japanisches
                # Zeichen vorhanden, aber kein lateinisches Alphabet.
                # Skipt 1-2-Zeichen-Kana-only (Particle-Fragen, sind selbsterklaerend).
                qtxt = q.get("question_text") or ""
                if _needs_romaji_in_quiz(qtxt):
                    errors.append(
                        f"Page {p_idx}.{c_idx}.Q{q_idx}: question_text enthaelt "
                        f"japanischen Text aber kein Romaji. Pflicht: '... (romaji)' "
                        f"oder '漢字 (kana, romaji)'. Text: {qtxt[:60]}"
                    )
                for o_idx, o in enumerate(q.get("options", []), start=1):
                    otxt = o.get("option_text") or ""
                    if _needs_romaji_in_quiz(otxt):
                        errors.append(
                            f"Page {p_idx}.{c_idx}.Q{q_idx}.O{o_idx}: option_text "
                            f"enthaelt japanischen Text aber kein Romaji. "
                            f"Text: {otxt[:60]}"
                        )

    # Budget-Checks aus SKILL.md §4 (angepasst 2026-04-24: groessere Lektionen).
    # Bei kind=kana gelten andere Budgets (Schreibsystem-Lektion ohne Vocab/Grammar).
    if kind == "kana":
        if not (5 <= kana_count <= 35):
            errors.append(f"Kana-Count {kana_count} ausserhalb [5,35] (kind=kana)")
        if not (8 <= quiz_count <= 16):
            errors.append(f"Quiz-Count {quiz_count} ausserhalb [8,16] (kind=kana)")
        if len(quiz_types_seen) < 2:
            errors.append(
                f"Mind. 2 verschiedene Quiz-Typen erforderlich, nur {quiz_types_seen} verwendet"
            )
        if len(pages) < 4:
            errors.append(f"Mindestens 4 Pages erforderlich (kind=kana), hat {len(pages)}")
        if vocab_count > 0:
            errors.append(
                f"kind=kana: Vocabulary-Eintraege ({vocab_count}) nicht erlaubt. "
                f"Wenn Lese-Drill-Woerter noetig sind, in Markdown-Text als Beispiele schreiben."
            )
        if grammar_count > 0:
            errors.append(
                f"kind=kana: Grammar-Eintraege ({grammar_count}) nicht erlaubt. "
                f"Aussprache/Strichfolge gehoeren in Markdown-Text-Pages."
            )
    else:
        if not (15 <= vocab_count <= 25):
            errors.append(f"Vocabulary-Count {vocab_count} ausserhalb [15,25]")
        if not (2 <= grammar_count <= 4):
            errors.append(f"Grammar-Count {grammar_count} ausserhalb [2,4]")
        if not (10 <= quiz_count <= 18):
            errors.append(f"Quiz-Count {quiz_count} ausserhalb [10,18]")
        if len(quiz_types_seen) < 2:
            errors.append(
                f"Mind. 2 verschiedene Quiz-Typen erforderlich, nur {quiz_types_seen} verwendet"
            )
        if len(pages) < 5:
            errors.append(f"Mindestens 5 Pages erforderlich (Einfuehrung/Vokabeln/Grammar/Dialog/Quiz/Zusammenfassung), hat {len(pages)}")

    # Bilder-Pflicht: thumbnail_url im Lesson-Header
    if not draft.get("thumbnail_url"):
        errors.append(
            "thumbnail_url fehlt. Pipeline-Schritt `images` muss vor `insert` laufen "
            "(Nano-Banana-Thumbnail). Notfalls manuell URL setzen."
        )

    # Mayuko-Direktive 2026-04-25 (Kanji-Disziplin):
    # Alle Kanji in JP-Texten der Lektion (Beispielsaetze, Dialog, Grammatik-
    # Beispiele) muessen im canonical-Set des Lesson-Levels stehen.
    # Bei kind=kana wird der Check uebersprungen — eine reine Hiragana/Katakana-
    # Lektion enthaelt strukturell keine Kanji-Beispielsaetze.
    if jlpt == 5 and kind != "kana":
        try:
            canon = load_canonical(5)
            n5_kanji_set = set(canon["kanji_set"])
            # Lesson-Level-Override fuer Kanji-Lessons, die explizit Zeichen
            # ausserhalb des elzup-canonical-Sets lehren (z.B. 兄/姉/弟/妹 — in
            # Tanos-Liste klassisch N5, in elzup-Liste nicht). Pflicht: source_note.
            extra = draft.get("additional_n5_kanji") or []
            if extra:
                if not draft.get("additional_n5_kanji_source_note"):
                    errors.append(
                        "additional_n5_kanji gesetzt, aber additional_n5_kanji_source_note fehlt. "
                        "Begruende Override (z.B. 'In Tanos-N5-Liste, in elzup nicht — Standard-Familie-Kanji')."
                    )
                n5_kanji_set |= set(extra)
            jp_text_blobs: list[tuple[str, str]] = []  # (location, text)
            for p_idx, page in enumerate(draft.get("pages", []), start=1):
                for c_idx, item in enumerate(page.get("contents", []), start=1):
                    data = item.get("data", {}) or {}
                    if item.get("content_type") == "text":
                        jp_text_blobs.append(
                            (f"Page{p_idx}.{c_idx}.text.content_text",
                             data.get("content_text", "") or "")
                        )
                    elif item.get("content_type") == "vocabulary":
                        jp_text_blobs.append(
                            (f"Page{p_idx}.{c_idx}.vocab.example_sentence_japanese",
                             data.get("example_sentence_japanese", "") or "")
                        )
                    elif item.get("content_type") == "grammar":
                        ex = data.get("example_sentences") or ""
                        if isinstance(ex, list):
                            ex = "\n".join(str(x) for x in ex)
                        jp_text_blobs.append(
                            (f"Page{p_idx}.{c_idx}.grammar.example_sentences", ex)
                        )
            offending: dict[str, set[str]] = {}
            for location, text in jp_text_blobs:
                bad = extract_kanji(text) - n5_kanji_set
                if bad:
                    offending[location] = bad
            for loc, kanji in offending.items():
                errors.append(
                    f"{loc}: enthaelt Kanji ausserhalb canonical N5-Set: "
                    f"{sorted(kanji)}. Mayuko-Direktive: keine N4+ Kanji in N5-Lektion. "
                    f"Schreibe das Wort in Hiragana oder ersetze durch N5-Kanji-Wort."
                )
        except FileNotFoundError as e:
            errors.append(f"Canonical-Liste fehlt: {e}")

    # Umlaut-Fallback-Check (hart) — erkennt ASCII-Ersatz fuer Umlaute
    # in ALLEN deutschen Fliesstexten des Drafts.
    blob = json.dumps(draft, ensure_ascii=False)
    # Regex: typische deutsche Woerter, die bei Umlaut-Fallback erscheinen
    umlaut_fallback_re = __import__("re").compile(
        r"\b("
        r"hoeflich|Hoeflich|"
        r"fuer|Fuer|ueber|Ueber|"
        r"koennen|Koennen|koennt|muessen|Muessen|"
        r"hoeren|Hoeren|nuetzlich|Nuetzlich|"
        r"Schueler|schuelerin|Schuelerin|Gruesse|gruesse|"
        r"Einfuehrung|einfuehrung|Uebung|uebung|Uebersicht|uebersicht|"
        r"Getraenk|getraenk|koestlich|Koestlich|spaet|Spaet|"
        r"Waehrung|waehrung|Erklaerung|erklaerung|Uebersetzung|uebersetzung"
        r")\b"
    )
    for m in umlaut_fallback_re.finditer(blob):
        errors.append(
            f"ASCII-Umlaut-Fallback verboten: '{m.group(0)}' — "
            f"nutze Umlaute (ue → ü, oe → ö, ae → ä)."
        )

    # Romaji-in-Text-Check: Wenn ein content_text japanische Zeichen enthaelt,
    # muss in naher Umgebung auch Romaji (lateinische Klammer-Passage) stehen.
    jp_char_re = __import__("re").compile(r"[぀-ヿ一-鿿]")
    romaji_hint_re = __import__("re").compile(r"\([a-zA-Z][a-zA-Z \-'?!.,]{1,}\)")
    for p_idx, page in enumerate(draft.get("pages", []), start=1):
        for c_idx, item in enumerate(page.get("contents", []), start=1):
            if item.get("content_type") != "text":
                continue
            ctext = item.get("data", {}).get("content_text", "")
            if jp_char_re.search(ctext) and not romaji_hint_re.search(ctext):
                errors.append(
                    f"Page {p_idx}.{c_idx} text enthaelt JP-Zeichen, "
                    f"aber keine Romaji in Klammern. Regel: jedes JP-Wort "
                    f"im Fliesstext muss mit Romaji `(romaji)` annotiert sein."
                )

    return errors


# ========================================================================
# DB-GAP-ANALYSE (status)
# ========================================================================

def db_status():
    """Zeigt DB-Gaps fuer naechsten Lesson-Vorschlag."""
    try:
        from app import create_app, db
        from app.models import Lesson, Vocabulary, LessonCategory
    except ImportError as e:
        print(f"[FEHLER] App-Import fehlgeschlagen: {e}")
        print("Tipp: venv aktivieren und docker compose up db -d")
        return

    app = create_app()
    with app.app_context():
        total_lessons = db.session.query(Lesson).count()
        n5_lessons = db.session.query(Lesson).filter(Lesson.difficulty_level <= 2).count()
        n4_lessons = db.session.query(Lesson).filter(
            Lesson.difficulty_level.in_([3, 4])
        ).count()

        n5_vocab = db.session.query(Vocabulary).filter_by(jlpt_level=5).count()
        n4_vocab = db.session.query(Vocabulary).filter_by(jlpt_level=4).count()

        print("=" * 60)
        print("  DB-Gap-Analyse")
        print("=" * 60)
        print(f"  Lessons gesamt:       {total_lessons}")
        print(f"    davon N5 (diff 1-2): {n5_lessons}")
        print(f"    davon N4 (diff 3-4): {n4_lessons}")
        print("  Vocabulary:")
        print(f"    N5:                  {n5_vocab}")
        print(f"    N4:                  {n4_vocab}")

        # Themen-Verteilung ueber Kategorien
        categories = db.session.query(LessonCategory).all()
        print(f"\n  Kategorien ({len(categories)}):")
        for cat in categories:
            cat_lesson_count = db.session.query(Lesson).filter_by(
                category_id=cat.id
            ).count()
            print(f"    {cat.name}: {cat_lesson_count} Lessons")

        print("\n  Vorgeschlagene Themen (noch wenig abgedeckt):")
        # Heuristik: vergleiche gegen Standard-N5-Themen
        standard_topics = [
            "Begruessung", "Zahlen", "Familie", "Uhrzeit", "Essen",
            "Wohnen", "Transport", "Wetter", "Hobbys", "Einkaufen"
        ]
        missing = []
        for topic in standard_topics:
            exists = db.session.query(Lesson).filter(
                Lesson.title.ilike(f"%{topic}%")
            ).first()
            if not exists:
                missing.append(topic)
        for t in missing[:5]:
            print(f"    - {t} (keine Lesson mit diesem Titel-Fragment gefunden)")


# ========================================================================
# JLPT-COVERAGE-DASHBOARD (coverage)
# ========================================================================

def jlpt_coverage(level: int = 5, show_missing: int = 30):
    """Vergleicht DB-Inhalt vs. canonical JLPT-Liste fuer ein Level.

    Zeigt prozentuale Coverage und (Top-N) fehlende Items, damit Claudio
    weiss welche Vokabeln/Kanji noch generiert werden muessen.
    """
    try:
        canon = load_canonical(level)
    except FileNotFoundError as e:
        print(f"[FEHLER] {e}")
        return

    try:
        from app import create_app, db
        from app.models import Vocabulary, Kanji
    except ImportError as e:
        print(f"[FEHLER] App-Import fehlgeschlagen: {e}")
        print("Tipp: venv aktivieren und docker compose up db -d")
        return

    app = create_app()
    with app.app_context():
        # Vokabeln in DB mit jlpt_level=level (Match auf word)
        db_vocab_words = {
            v.word for v in db.session.query(Vocabulary).filter_by(jlpt_level=level).all()
        }
        canon_vocab_words = canon["vocab_set"]
        # Auch Vokabeln ohne jlpt_level mitzaehlen, falls Wort in canonical-Liste
        all_db_vocab = {v.word for v in db.session.query(Vocabulary).all()}
        covered_vocab = canon_vocab_words & (db_vocab_words | all_db_vocab)
        missing_vocab = canon_vocab_words - all_db_vocab

        # Kanji in DB mit jlpt_level=level
        db_kanji_chars = {
            k.character for k in db.session.query(Kanji).filter_by(jlpt_level=level).all()
        }
        all_db_kanji = {k.character for k in db.session.query(Kanji).all()}
        canon_kanji_chars = canon["kanji_set"]
        covered_kanji = canon_kanji_chars & (db_kanji_chars | all_db_kanji)
        missing_kanji = canon_kanji_chars - all_db_kanji

        v_total = len(canon_vocab_words)
        v_cov = len(covered_vocab)
        v_pct = (100.0 * v_cov / v_total) if v_total else 0.0

        k_total = len(canon_kanji_chars)
        k_cov = len(covered_kanji)
        k_pct = (100.0 * k_cov / k_total) if k_total else 0.0

        canon["raw"].get("counts", {}).get("grammar", 0)

        print("=" * 70)
        print(f"  JLPT-N{level} Coverage-Dashboard")
        print(f"  Source: {canon['raw'].get('sources', {}).get('vocab', {}).get('origin', '?')}")
        print("=" * 70)
        print(f"  Vokabeln:   {v_cov:>4} / {v_total:<4} = {v_pct:5.1f}%")
        print(f"  Kanji:      {k_cov:>4} / {k_total:<4} = {k_pct:5.1f}%")
        print(f"  Grammatik:  (canonical-Liste fuer N{level} noch nicht maschinell importiert)")
        print()
        if missing_vocab:
            print(f"  Fehlende Vokabeln (Top {min(show_missing, len(missing_vocab))} von {len(missing_vocab)}):")
            # Sortiert nach canonical-Reihenfolge wenn moeglich
            ordered_missing = [
                v["word"] for v in canon["vocab_list"] if v["word"] in missing_vocab
            ]
            for w in ordered_missing[:show_missing]:
                # Lookup reading + meaning fuer Zeile
                entry = next((v for v in canon["vocab_list"] if v["word"] == w), None)
                if entry:
                    print(f"    - {w}  {entry.get('reading', ''):<10}  {entry.get('meaning_en', '')[:50]}")
                else:
                    print(f"    - {w}")
            if len(missing_vocab) > show_missing:
                print(f"    ... ({len(missing_vocab) - show_missing} weitere)")
        else:
            print("  Vokabeln: 100% gedeckt 🎉")

        print()
        if missing_kanji:
            print(f"  Fehlende Kanji ({len(missing_kanji)} von {k_total}):")
            ordered_missing_k = [
                k["char"] for k in canon["kanji_list"] if k["char"] in missing_kanji
            ]
            print(f"    {' '.join(ordered_missing_k[:show_missing])}")
            if len(missing_kanji) > show_missing:
                print(f"    ... ({len(missing_kanji) - show_missing} weitere)")
        else:
            print("  Kanji: 100% gedeckt 🎉")

        print()
        print("  Mayuko-Direktive: N5 zuerst auf 100%, bevor N4 begonnen wird.")
        print("=" * 70)


# ========================================================================
# WORT-WIEDERVERWENDUNG (used-words Report + validate-Warnung)
# ========================================================================
# Das Datenmodell dedupliziert Vokabeln global (Vocabulary.word ist Schluessel);
# eine Lektion referenziert ueber LessonContent.content_id. Dadurch kann dasselbe
# Wort von beliebig vielen Lektionen unterrichtet werden — ungeprueft. Diese
# Helfer machen die Wiederverwendung SICHTBAR (Report) und WARNEN beim validate,
# damit neue Lektionen primaer neue Lern-Vokabeln einfuehren (User-Direktive
# 2026-06-21). Bewusste Wiederholung bleibt erlaubt — es ist eine Warnung, kein
# Abbruch; Kern-Funktionswoerter (CORE_FUNCTION_WORDS) sind ausgenommen.

def _load_used_vocab_map():
    """Liest aus der DB, welche Vokabel-Woerter bereits in Lektionen vorkommen.

    Gibt {word: {'lessons': set[int], 'published': set[int]}} zurueck, oder
    None wenn die DB nicht erreichbar ist (z.B. `validate` offline) — dann
    wird der Check sauber uebersprungen statt zu crashen.
    """
    try:
        from app import create_app, db
        from app.models import Lesson, LessonContent, Vocabulary
    except ImportError:
        return None
    try:
        app = create_app()
        with app.app_context():
            rows = (
                db.session.query(
                    Vocabulary.word, LessonContent.lesson_id, Lesson.is_published
                )
                .join(LessonContent, LessonContent.content_id == Vocabulary.id)
                .filter(LessonContent.content_type == "vocabulary")
                .join(Lesson, Lesson.id == LessonContent.lesson_id)
                .all()
            )
    except Exception:
        return None
    used: dict[str, dict] = {}
    for word, lesson_id, is_published in rows:
        entry = used.setdefault(word, {"lessons": set(), "published": set()})
        entry["lessons"].add(lesson_id)
        if is_published:
            entry["published"].add(lesson_id)
    return used


def compute_reused_words(draft: dict, used_map: dict, allowlist=CORE_FUNCTION_WORDS):
    """Reiner Kern (testbar ohne DB).

    Gibt (reused, distinct) zurueck:
      reused   = nach Lektions-Zahl absteigend sortierte Liste (word, n_lessons)
                 der Draft-Lern-Vokabeln, die bereits in anderen Lektionen
                 unterrichtet werden — Allowlist (Kern-Funktionswoerter) raus.
      distinct = alle distinkten Vokabel-Woerter des Drafts (Reihenfolge erhalten).
    """
    distinct: list[str] = []
    seen: set[str] = set()
    for page in draft.get("pages", []):
        for item in page.get("contents", []):
            if item.get("content_type") == "vocabulary":
                word = (item.get("data") or {}).get("word")
                if word and word not in seen:
                    seen.add(word)
                    distinct.append(word)
    reused: list[tuple[str, int]] = []
    for word in distinct:
        if word in allowlist:
            continue
        info = used_map.get(word)
        if info:
            n = len(info["lessons"]) if isinstance(info, dict) else int(info)
            reused.append((word, n))
    reused.sort(key=lambda t: (-t[1], t[0]))
    return reused, distinct


def reused_words_warning(draft: dict) -> None:
    """Druckt beim `validate` eine Wiederverwendungs-Warnung (kein Abbruch)."""
    used_map = _load_used_vocab_map()
    if used_map is None:
        print("[HINWEIS] Wort-Wiederverwendungs-Check uebersprungen "
              "(DB nicht erreichbar — venv aktiv? `docker compose up db -d`?).")
        return
    reused, distinct = compute_reused_words(draft, used_map)
    total = len(distinct)
    if total == 0:
        return
    if not reused:
        print(f"[OK] Wort-Neuheit: alle {total} Lern-Vokabeln sind neu "
              "(in keiner anderen Lektion bereits unterrichtet).")
        return
    print(f"[WARNUNG] Wort-Wiederverwendung: {len(reused)}/{total} Lern-Vokabeln "
          "werden bereits in anderen Lektionen unterrichtet "
          "(Kern-Funktionswoerter ausgenommen):")
    for word, n in reused:
        print(f"  - {word}  (in {n} Lektion{'en' if n != 1 else ''})")
    print("  Tipp: Wo moeglich NEUE Lern-Vokabeln waehlen, statt vorhandene zu "
          "doppeln. Bewusste Wiederholung ist OK — diese Warnung blockiert nicht.")


def used_words_report(top: int = 30, min_lessons: int = 2):
    """Report (read-only): welche Vokabeln werden ueber wie viele Lektionen genutzt."""
    used_map = _load_used_vocab_map()
    if used_map is None:
        print("[FEHLER] DB nicht erreichbar. Tipp: venv aktivieren und "
              "`docker compose up db -d`.")
        return
    items = [
        (word, len(info["lessons"]), len(info["published"]))
        for word, info in used_map.items()
    ]
    total_words = len(items)
    multi = sorted(
        (it for it in items if it[1] >= min_lessons),
        key=lambda t: (-t[1], t[0]),
    )
    print("=" * 70)
    print("  Vokabel-Wiederverwendung ueber Lektionen")
    print("=" * 70)
    print(f"  Distinkte Vokabeln in Lektionen genutzt:  {total_words}")
    print(f"  davon in >= {min_lessons} Lektionen:            {len(multi)}")
    if total_words:
        avg = sum(it[1] for it in items) / total_words
        print(f"  Schnitt Lektionen pro Wort:               {avg:.2f}")
    print()
    if not multi:
        print(f"  Keine Vokabel wird in >= {min_lessons} Lektionen genutzt. 🎉")
        print("=" * 70)
        return
    print(f"  Meist-wiederverwendete Woerter (Top {top}):")
    for word, n, npub in multi[:top]:
        print(f"    {word}\t{n:>2} Lektionen  ({npub} publiziert)")
    if len(multi) > top:
        print(f"    ... ({len(multi) - top} weitere mit >= {min_lessons} Lektionen)")
    print("=" * 70)


# ========================================================================
# INSERT
# ========================================================================

def _get_or_create_kana(db, Kana, data: dict) -> int:
    """Duplicate-safe: gibt bestehende ID zurueck oder erstellt neu.

    Match ueber `character` (UNIQUE constraint in der DB). Aktualisiert KEINE
    bestehenden Eintraege — wenn ein Zeichen schon existiert, wird die ID
    der existierenden Zeile zurueckgegeben. Das schuetzt manuelle Edits.
    """
    existing = db.session.query(Kana).filter_by(character=data["character"]).first()
    if existing:
        return existing.id
    k = Kana(
        character=data["character"],
        romanization=data["romanization"],
        type=data["type"],
        stroke_order_info=data.get("stroke_order_info"),
        example_sound_url=data.get("example_sound_url"),
    )
    db.session.add(k)
    db.session.flush()
    return k.id


def _get_or_create_vocab(db, Vocabulary, data: dict) -> int:
    """Duplicate-safe: gibt bestehende ID zurueck oder erstellt neu."""
    existing = db.session.query(Vocabulary).filter_by(word=data["word"]).first()
    if existing:
        return existing.id
    v = Vocabulary(
        word=data["word"],
        reading=data["reading"],
        romaji=data.get("romaji"),
        meaning=data["meaning"],
        meaning_de=data.get("meaning_de"),
        jlpt_level=data.get("jlpt_level"),
        example_sentence_japanese=data.get("example_sentence_japanese"),
        example_sentence_english=data.get("example_sentence_english"),
        image_url=data.get("image_url"),
        status="approved",
        created_by_ai=True,
    )
    db.session.add(v)
    db.session.flush()
    return v.id


def _get_or_create_kanji(db, Kanji, data: dict) -> int:
    """Duplicate-safe: gibt bestehende ID zurueck oder erstellt neu.

    Match ueber `character` (UNIQUE constraint). Aktualisiert KEINE
    bestehenden Eintraege.
    """
    existing = db.session.query(Kanji).filter_by(character=data["character"]).first()
    if existing:
        return existing.id
    k = Kanji(
        character=data["character"],
        meaning=data["meaning"],
        onyomi=data.get("onyomi"),
        kunyomi=data.get("kunyomi"),
        jlpt_level=data.get("jlpt_level"),
        stroke_count=data.get("stroke_count"),
        radical=data.get("radical"),
        stroke_order_info=data.get("stroke_order_info"),
        status="approved",
        created_by_ai=True,
    )
    db.session.add(k)
    db.session.flush()
    return k.id


def _get_or_create_grammar(db, Grammar, data: dict) -> int:
    existing = db.session.query(Grammar).filter_by(title=data["title"]).first()
    if existing:
        return existing.id
    g = Grammar(
        title=data["title"],
        explanation=data["explanation"],
        structure=data.get("structure"),
        romaji=data.get("romaji"),
        jlpt_level=data.get("jlpt_level"),
        example_sentences=data.get("example_sentences"),
        # Pflicht-Feld fuer den Audio-Button auf der Grammatik-Karte:
        # genau EIN rein japanischer Satz, der von der ja-JP-Stimme
        # vorgelesen wird (siehe SKILL.md "Grammar.tts_example_jp").
        tts_example_jp=data.get("tts_example_jp"),
        status="approved",
        created_by_ai=True,
    )
    db.session.add(g)
    db.session.flush()
    return g.id


# ========================================================================
# EXPORT / IMPORT — Dev->Prod Lektions-Migration (siehe SKILL.md §11)
# ========================================================================
# Vollstaendige Migration EINER Lektion zwischen DBs (z.B. Windows-Dev ->
# hp-ubuntu-Prod). Erfasst ALLE LessonContent-Typen (inkl. generierter
# audio/slideshow/image mit content_text/media_url) + referenzierte
# Vocab/Kanji/Kana/Grammar (dedupt) + Quiz. NICHT nur die Draft-Typen, die
# insert_draft kennt. Beide Funktionen laufen IN einem App-Kontext.

_EXPORT_SCHEMA = "jpl-lesson-export/1"
_REF_FIELDS = {
    "vocabulary": ["word", "reading", "romaji", "meaning", "meaning_de", "jlpt_level",
                   "example_sentence_japanese", "example_sentence_english", "image_url"],
    "kanji": ["character", "meaning", "onyomi", "kunyomi", "jlpt_level", "stroke_count",
              "radical", "stroke_order_info", "image_url"],
    "kana": ["character", "romanization", "type", "stroke_order_info", "example_sound_url"],
    "grammar": ["title", "explanation", "structure", "romaji", "jlpt_level",
                "example_sentences", "tts_example_jp"],
}


def _jlpt_from_difficulty(diff: int | None) -> int:
    return 5 if (diff or 1) <= 2 else 4


def export_lesson(lesson_id: int) -> dict:
    """Liest eine komplette Lektion aus der DB ins Migrations-JSON.

    Muss in einem App-Kontext laufen. Wirft ValueError, wenn die Lektion fehlt.
    """
    from app import db
    from app.models import (
        Lesson, LessonPage, LessonContent, LessonCategory, Vocabulary, Grammar,
        Kana, Kanji, QuizQuestion, QuizOption,
    )

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        raise ValueError(f"Lesson {lesson_id} nicht gefunden")

    cat_slug = None
    if lesson.category_id:
        cat = db.session.get(LessonCategory, lesson.category_id)
        cat_slug = cat.slug if cat else None

    ref_models = {"vocabulary": Vocabulary, "kanji": Kanji, "kana": Kana, "grammar": Grammar}

    pages_out = []
    pages = (db.session.query(LessonPage)
             .filter_by(lesson_id=lesson_id).order_by(LessonPage.page_number).all())
    for page in pages:
        contents_out = []
        lcs = (db.session.query(LessonContent)
               .filter_by(lesson_id=lesson_id, page_number=page.page_number)
               .order_by(LessonContent.order_index, LessonContent.id).all())
        for lc in lcs:
            item = {"content_type": lc.content_type, "is_interactive": bool(lc.is_interactive)}
            if lc.content_type in ref_models and lc.content_id:
                row = db.session.get(ref_models[lc.content_type], lc.content_id)
                item["data"] = (
                    {f: getattr(row, f, None) for f in _REF_FIELDS[lc.content_type]} if row else {}
                )
            else:
                item["data"] = {
                    "title": lc.title,
                    "content_text": lc.content_text,
                    "media_url": lc.media_url,
                    "file_path": lc.file_path,
                    "file_type": lc.file_type,
                    "file_size": lc.file_size,
                    "ai_generation_details": lc.ai_generation_details,
                }
            qs = (db.session.query(QuizQuestion)
                  .filter_by(lesson_content_id=lc.id).order_by(QuizQuestion.order_index).all())
            if qs:
                item["quiz_questions"] = []
                for q in qs:
                    opts = (db.session.query(QuizOption)
                            .filter_by(question_id=q.id).order_by(QuizOption.order_index).all())
                    item["quiz_questions"].append({
                        "question_type": q.question_type,
                        "question_text": q.question_text,
                        "explanation": q.explanation,
                        "hint": q.hint,
                        "difficulty_level": q.difficulty_level,
                        "points": q.points,
                        "options": [
                            {"option_text": o.option_text, "is_correct": bool(o.is_correct),
                             "feedback": o.feedback}
                            for o in opts
                        ],
                    })
            contents_out.append(item)
        pages_out.append({
            "title": page.title, "description": page.description,
            "page_type": page.page_type, "contents": contents_out,
        })

    return {
        "schema": _EXPORT_SCHEMA,
        "title": lesson.title,
        "description": lesson.description,
        "jlpt_level": _jlpt_from_difficulty(lesson.difficulty_level),
        "difficulty_level": lesson.difficulty_level,
        "thumbnail_url": lesson.thumbnail_url,
        "allow_guest_access": bool(lesson.allow_guest_access),
        "instruction_language": lesson.instruction_language,
        "lesson_type": lesson.lesson_type,
        "category_slug": cat_slug,
        "pages": pages_out,
    }


def import_lesson(data: dict) -> int:
    """Schreibt eine via export_lesson() exportierte Lektion in die (Ziel-)DB.

    Dedupt Vocab/Kanji/Kana/Grammar via _get_or_create_*; generierte
    Content-Typen (text/audio/image/dialog_slideshow) werden mit
    content_text/media_url/file_* 1:1 uebernommen. Lektion wird mit
    is_published=False angelegt. Muss in einem App-Kontext laufen.
    """
    from app import db
    from app.models import (
        Lesson, LessonPage, LessonContent, LessonCategory, Vocabulary, Grammar,
        Kana, Kanji, QuizQuestion, QuizOption,
    )

    creators = {
        "kana": (Kana, _get_or_create_kana),
        "vocabulary": (Vocabulary, _get_or_create_vocab),
        "kanji": (Kanji, _get_or_create_kanji),
        "grammar": (Grammar, _get_or_create_grammar),
    }

    category_id = None
    if data.get("category_slug"):
        cat = db.session.query(LessonCategory).filter_by(slug=data["category_slug"]).first()
        category_id = cat.id if cat else None

    difficulty = data.get("difficulty_level") or (1 if data.get("jlpt_level") == 5 else 3)
    lesson = Lesson(
        title=data["title"],
        description=data.get("description"),
        lesson_type=data.get("lesson_type", "free"),
        difficulty_level=difficulty,
        is_published=False,
        allow_guest_access=bool(data.get("allow_guest_access", False)),
        instruction_language=data.get("instruction_language", "german"),
        thumbnail_url=data.get("thumbnail_url"),
        category_id=category_id,
        price=0.0,
        is_purchasable=False,
    )
    db.session.add(lesson)
    db.session.flush()

    for page_num, page in enumerate(data.get("pages", []), start=1):
        lp = LessonPage(
            lesson_id=lesson.id, page_number=page_num,
            title=page.get("title"), description=page.get("description"),
            page_type=page.get("page_type", "normal"),
        )
        db.session.add(lp)
        db.session.flush()

        for order_idx, item in enumerate(page.get("contents", []), start=1):
            ct = item["content_type"]
            d = item.get("data", {}) or {}
            is_interactive = bool(item.get("is_interactive") or item.get("quiz_questions"))
            if ct in creators:
                Model, creator = creators[ct]
                lc = LessonContent(
                    lesson_id=lesson.id, content_type=ct,
                    content_id=creator(db, Model, d),
                    order_index=order_idx, page_number=page_num,
                    is_interactive=is_interactive, quiz_type="standard",
                    generated_by_ai=True,
                    ai_generation_details={"generator": "import_lesson"},
                )
            else:
                lc = LessonContent(
                    lesson_id=lesson.id, content_type=ct, content_id=None,
                    title=d.get("title"), content_text=d.get("content_text"),
                    media_url=d.get("media_url"), file_path=d.get("file_path"),
                    file_type=d.get("file_type"), file_size=d.get("file_size"),
                    order_index=order_idx, page_number=page_num,
                    is_interactive=is_interactive, quiz_type="standard",
                    generated_by_ai=True,
                    ai_generation_details=d.get("ai_generation_details") or {"generator": "import_lesson"},
                )
            db.session.add(lc)
            db.session.flush()

            for q_idx, q in enumerate(item.get("quiz_questions", []), start=1):
                qq = QuizQuestion(
                    lesson_content_id=lc.id,
                    question_type=q["question_type"],
                    question_text=q["question_text"],
                    explanation=q.get("explanation"),
                    hint=q.get("hint"),
                    difficulty_level=q.get("difficulty_level", 1),
                    points=q.get("points", 1),
                    order_index=q_idx,
                )
                db.session.add(qq)
                db.session.flush()
                for o_idx, opt in enumerate(q.get("options", []), start=1):
                    db.session.add(QuizOption(
                        question_id=qq.id,
                        option_text=opt["option_text"],
                        is_correct=bool(opt.get("is_correct", False)),
                        order_index=o_idx,
                        feedback=opt.get("feedback"),
                    ))

    db.session.commit()
    return lesson.id


def cmd_export(lesson_id: int, out_path: Path) -> None:
    from app import create_app
    app = create_app()
    with app.app_context():
        data = export_lesson(lesson_id)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Lesson {lesson_id} exportiert -> {out_path} ({len(data['pages'])} Pages)")


def cmd_import(json_path: Path) -> int:
    from app import create_app
    app = create_app()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if data.get("schema") != _EXPORT_SCHEMA:
        print(f"[WARN] unerwartetes schema={data.get('schema')!r} (erwartet {_EXPORT_SCHEMA})")
    with app.app_context():
        new_id = import_lesson(data)
    print(f"[OK] Lesson importiert -> id={new_id} (is_published=False, vor Publish verifizieren)")
    return new_id


def insert_draft(draft_path: Path) -> int:
    """Transaktionaler INSERT einer Lektion. Gibt lesson_id zurueck."""
    errors = validate_draft(json.loads(draft_path.read_text(encoding="utf-8")))
    if errors:
        print("[ABBRUCH] Validation-Fehler:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    from app import create_app, db
    from app.models import (
        Lesson, LessonPage, LessonContent, Vocabulary, Grammar, Kana, Kanji,
        QuizQuestion, QuizOption,
    )

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    app = create_app()

    with app.app_context():
        try:
            # Map JLPT → difficulty_level (N5=1, N4=3)
            jlpt = draft["jlpt_level"]
            difficulty_level = 1 if jlpt == 5 else 3

            lesson = Lesson(
                title=draft["title"],
                description=draft["description"],
                lesson_type="free",
                difficulty_level=difficulty_level,
                is_published=False,  # erst nach Verifikation True
                allow_guest_access=draft.get("allow_guest_access", False),
                instruction_language=draft.get("instruction_language", "german"),
                thumbnail_url=draft.get("thumbnail_url"),
                price=0.0,
                is_purchasable=False,
            )
            db.session.add(lesson)
            db.session.flush()
            lesson_id = lesson.id

            for page_num, page_data in enumerate(draft["pages"], start=1):
                page = LessonPage(
                    lesson_id=lesson_id,
                    page_number=page_num,
                    title=page_data.get("title"),
                    description=page_data.get("description"),
                    page_type=page_data.get("page_type", "normal"),
                )
                db.session.add(page)
                db.session.flush()

                for order_idx, item in enumerate(page_data.get("contents", []), start=1):
                    ct = item["content_type"]
                    content_id = None
                    content_text = None
                    title = None

                    if ct == "kana":
                        content_id = _get_or_create_kana(db, Kana, item["data"])
                    elif ct == "vocabulary":
                        content_id = _get_or_create_vocab(db, Vocabulary, item["data"])
                    elif ct == "kanji":
                        content_id = _get_or_create_kanji(db, Kanji, item["data"])
                    elif ct == "grammar":
                        content_id = _get_or_create_grammar(db, Grammar, item["data"])
                    elif ct == "text":
                        content_text = item.get("data", {}).get("content_text")
                        title = item.get("data", {}).get("title")

                    lc = LessonContent(
                        lesson_id=lesson_id,
                        content_type=ct,
                        content_id=content_id,
                        title=title,
                        content_text=content_text,
                        order_index=order_idx,
                        page_number=page_num,
                        is_interactive=bool(item.get("quiz_questions")),
                        quiz_type="standard",
                        generated_by_ai=True,
                        ai_generation_details={"generator": "claude", "draft": draft_path.name},
                    )
                    db.session.add(lc)
                    db.session.flush()

                    # Quiz-Fragen
                    for q_idx, q in enumerate(item.get("quiz_questions", []), start=1):
                        qq = QuizQuestion(
                            lesson_content_id=lc.id,
                            question_type=q["question_type"],
                            question_text=q["question_text"],
                            explanation=q.get("explanation"),
                            hint=q.get("hint"),
                            difficulty_level=q.get("difficulty_level", 1),
                            points=q.get("points", 1),
                            order_index=q_idx,
                        )
                        db.session.add(qq)
                        db.session.flush()

                        for o_idx, opt in enumerate(q.get("options", []), start=1):
                            qo = QuizOption(
                                question_id=qq.id,
                                option_text=opt["option_text"],
                                is_correct=opt.get("is_correct", False),
                                order_index=o_idx,
                                feedback=opt.get("feedback"),
                            )
                            db.session.add(qo)

            db.session.commit()
            print(f"[OK] Lesson inserted: id={lesson_id}, title='{draft['title']}'")

            # Generated-lessons.jsonl anhaengen
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "lesson_id": lesson_id,
                "title": draft["title"],
                "jlpt_level": jlpt,
                "topic": draft.get("topic"),
                "draft_file": str(draft_path),
            }
            log_path = SKILL_DIR / "generated-lessons.jsonl"
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            return lesson_id

        except Exception as e:
            db.session.rollback()
            print(f"[FEHLER] Rollback wegen: {e}")
            raise


# ========================================================================
# GIT COMMIT
# ========================================================================

def git_commit(lesson_id: int):
    """Committet nur Skill-Metadata (keine App-Code-Aenderungen)."""
    files = [
        ".claude/skills/generate-lesson/generated-lessons.jsonl",
        ".claude/skills/generate-lesson/learnings.md",
    ]
    subprocess.run(["git", "add", *files], cwd=PROJECT_ROOT, check=True)
    msg = f"Lektion generiert via Skill (Lesson ID {lesson_id})"
    subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_ROOT, check=True)
    subprocess.run(["git", "push"], cwd=PROJECT_ROOT, check=True)
    print("[OK] Git push abgeschlossen.")


# ========================================================================
# Nano Banana Images (Gemini 2.5 Flash Image — benoetigt GOOGLE_AI_API_KEY)
# ========================================================================

def _scene_from_vocab(data: dict) -> str | None:
    """Szenen-Beschreibung fuers Karten-Bild aus dem Beispielsatz (Direktive
    2026-06-21: Bild zum SATZ statt zum Wort).

    `example_sentence_english` hat das Format 'Romaji — Deutsche Uebersetzung'
    (Em-Dash ` — `). Wir nehmen die deutsche Seite als Szene. Gibt None zurueck,
    wenn kein Satz / keine Uebersetzung vorhanden ist (dann Icon-Fallback).
    """
    ex = (data.get("example_sentence_english") or "").strip()
    if " — " in ex:
        de = ex.split(" — ", 1)[1].strip()
        if de:
            return de
    return None


def generate_images(draft_path: Path):
    """Erweitert den Draft mit Bild-URLs (Thumbnail + Vokabel-Icons).

    Lektionsbilder laufen ueber gemini-2.5-flash-image ("Nano Banana"),
    NICHT mehr ueber OpenAI/DALL-E (User-Direktive, siehe SKILL.md §7).
    """
    if not (os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print("[SKIP] GOOGLE_AI_API_KEY/GEMINI_API_KEY nicht gesetzt — keine Bilder generiert.")
        return

    # Bestehenden Service verwenden (Nano-Banana-Methoden generate_*_nb)
    from app.ai_services import AILessonContentGenerator
    from app import create_app

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    app = create_app()

    import hashlib
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with app.app_context():
        gen = AILessonContentGenerator()

        # --- (1) Thumbnail ------------------------------------------------
        if not draft.get("thumbnail_url"):
            topic = draft.get("topic", draft["title"])
            prompt = (
                f"minimalist flat illustration of '{topic}', "
                f"soft pastels, no text, Japanese aesthetic"
            )
            result = gen.generate_single_image_nb(prompt=prompt, aspect_ratio="16:9")
            if result and result.get("image_bytes"):
                thumb_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "generated"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                slug = draft.get("topic", "lesson").lower().replace(" ", "_")
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"thumbnail_{slug}_{ts}.png"
                (thumb_dir / filename).write_bytes(result["image_bytes"])
                # Relativ zu UPLOAD_FOLDER — url_for('routes.uploaded_file')
                # baut sonst einen doppelten /uploads-Pfad.
                draft["thumbnail_url"] = f"generated/{filename}"
                print(f"[OK] Thumbnail -> {draft['thumbnail_url']}")
            else:
                err = (result or {}).get("error", "unbekannt")
                print(f"[FEHLER] Thumbnail-Generierung: {err}")
        else:
            print(f"[SKIP] Thumbnail vorhanden: {draft['thumbnail_url']}")

        # --- (2) Vokabel-Icons fuer JEDE Vokabel --------------------------
        vocab_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "vocab_generated"
        vocab_dir.mkdir(parents=True, exist_ok=True)

        vocab_items = [
            item
            for page in draft.get("pages", [])
            for item in page.get("contents", [])
            if item.get("content_type") == "vocabulary"
        ]
        todo = [it for it in vocab_items if not it.get("data", {}).get("image_url")]
        print(f"[INFO] {len(vocab_items)} Vokabeln — generiere {len(todo)} fehlende Icons (4 Worker)")

        def _gen_vocab_icon(item):
            data = item.get("data", {})
            word = data.get("word", "")
            meaning = data.get("meaning") or data.get("meaning_de") or word
            # Bild zum SATZ statt zum Wort (Direktive 2026-06-21): die deutsche
            # Uebersetzung des Beispielsatzes treibt das Szenenbild. Fallback auf
            # Icon-Stil (scene=None), wenn kein Satz/keine Uebersetzung vorhanden.
            scene = _scene_from_vocab(data)
            # current_app.logger im Service braucht App-Kontext pro Worker-Thread.
            with app.app_context():
                res = gen.generate_vocabulary_image_nb(word=word, meaning=meaning, scene=scene)
            if not res or "image_bytes" not in res:
                return item, None, (res or {}).get("error", "unbekannt")
            hash_suffix = hashlib.md5(word.encode()).hexdigest()[:8]
            filename = f"vocab_{hash_suffix}.png"
            (vocab_dir / filename).write_bytes(res["image_bytes"])
            # Pfad relativ zu UPLOAD_FOLDER (app/static/uploads/), damit
            # url_for('routes.uploaded_file', filename=...) passt.
            return item, f"vocab_generated/{filename}", None

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(_gen_vocab_icon, it) for it in todo]
            for done, fut in enumerate(as_completed(futures), start=1):
                item, url, err = fut.result()
                word = item.get("data", {}).get("word", "")
                if err:
                    print(f"  [{done:2d}/{len(todo)}] {word} [FEHLER] {err}")
                    continue
                item["data"]["image_url"] = url
                print(f"  [{done:2d}/{len(todo)}] {word} -> {url}")

        # Draft ueberschreiben mit gefuellten URLs
        draft_path.write_text(
            json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("[OK] Draft aktualisiert.")


# ========================================================================
# AUDIO (Google Cloud TTS fuer die Dialog-Page)
# ========================================================================

def generate_text_audio(lesson_id: int, force: bool = False, page: int | None = None) -> int:
    """Rendert pro text-LessonContent eine MP3 (DE+JA gemischt via Google TTS).

    Splittet Text in Sprachsegmente und nutzt de-DE-Voice fuer Lateinschrift,
    ja-JP-Voice fuer Hira/Kata/Kanji. So klingt der deutsche Teil nicht mehr
    mit japanischem Akzent (User-Direktive 2026-04-25).

    Setzt `LessonContent.media_url` — das Template rendert dann einen
    Mini-Player oberhalb des Markdown-Texts. Idempotent ueber text_hash.
    """
    script = SKILL_DIR / "scripts" / "gen_text_audio.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, str(script), str(lesson_id)]
    if force:
        cmd.append("--force")
    if page is not None:
        cmd.extend(["--page", str(page)])
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)
    return result.returncode


def generate_dialog_slideshow(lesson_id: int) -> int:
    """Baut pro Dialog-Zeile ein Slide mit TTS-Audio und Nano-Banana-Bild.

    Siehe scripts/gen_dialog_slideshow.py fuer die Details. Legt einen
    LessonContent(content_type='dialog_slideshow', content_text=JSON)
    auf der Dialog-Page an.
    """
    script = SKILL_DIR / "scripts" / "gen_dialog_slideshow.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script), str(lesson_id)],
        cwd=PROJECT_ROOT, env=env,
    )
    return result.returncode


# ========================================================================
# CLI
# ========================================================================

def main():
    os.chdir(PROJECT_ROOT)
    parser = argparse.ArgumentParser(description="generate-lesson pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="DB-Gap-Analyse")

    p_val = sub.add_parser("validate", help="Draft validieren (ohne insert)")
    p_val.add_argument("draft", type=Path)

    p_img = sub.add_parser("images", help="Nano-Banana-Bilder erzeugen")
    p_img.add_argument("draft", type=Path)

    p_ins = sub.add_parser("insert", help="Draft in DB persistieren")
    p_ins.add_argument("draft", type=Path)

    p_taud = sub.add_parser("text-audio", help="Pro text-LessonContent eine MP3 (DE+JA gemischt)")
    p_taud.add_argument("lesson_id", type=int)
    p_taud.add_argument("--page", type=int, default=None)
    p_taud.add_argument("--force", action="store_true")

    p_slide = sub.add_parser("slideshow", help="Dialog-Slideshow (TTS+Nano Banana pro Zeile) bauen")
    p_slide.add_argument("lesson_id", type=int)

    p_cov = sub.add_parser("coverage", help="JLPT-Coverage-Dashboard (DB vs. canonical list)")
    p_cov.add_argument("level", type=int, nargs="?", default=5,
                       help="JLPT-Level (default: 5)")
    p_cov.add_argument("--show-missing", type=int, default=30,
                       help="Anzahl fehlender Items zu zeigen (default: 30)")

    p_used = sub.add_parser("used-words",
                            help="Vokabel-Wiederverwendung ueber Lektionen (Report)")
    p_used.add_argument("--top", type=int, default=30,
                        help="Top-N meist-wiederverwendete Woerter (default: 30)")
    p_used.add_argument("--min-lessons", type=int, default=2,
                        help="Schwelle: ab wievielen Lektionen gilt ein Wort als "
                             "wiederverwendet (default: 2)")

    p_cmt = sub.add_parser("commit", help="Git-commit Skill-Metadata")
    p_cmt.add_argument("lesson_id", type=int)

    p_exp = sub.add_parser("export", help="Lektion (komplett) aus DB ins Migrations-JSON")
    p_exp.add_argument("lesson_id", type=int)
    p_exp.add_argument("out", type=Path)

    p_imp = sub.add_parser("import", help="Migrations-JSON in die (Ziel-)DB importieren")
    p_imp.add_argument("json_path", type=Path)

    args = parser.parse_args()

    if args.cmd == "status":
        db_status()
    elif args.cmd == "validate":
        draft = json.loads(args.draft.read_text(encoding="utf-8"))
        errors = validate_draft(draft)
        if errors:
            print("[FEHLER] Validation:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("[OK] Draft valide.")
        # Weiche Wiederverwendungs-Warnung (kein Abbruch, DB-optional).
        try:
            reused_words_warning(draft)
        except Exception as exc:  # nie validate wegen des Checks scheitern lassen
            print(f"[HINWEIS] Wiederverwendungs-Check fehlgeschlagen: {exc}")
    elif args.cmd == "images":
        generate_images(args.draft)
    elif args.cmd == "insert":
        insert_draft(args.draft)
    elif args.cmd == "text-audio":
        sys.exit(generate_text_audio(args.lesson_id, force=args.force, page=args.page))
    elif args.cmd == "slideshow":
        sys.exit(generate_dialog_slideshow(args.lesson_id))
    elif args.cmd == "coverage":
        jlpt_coverage(args.level, show_missing=args.show_missing)
    elif args.cmd == "used-words":
        used_words_report(top=args.top, min_lessons=args.min_lessons)
    elif args.cmd == "commit":
        git_commit(args.lesson_id)
    elif args.cmd == "export":
        cmd_export(args.lesson_id, args.out)
    elif args.cmd == "import":
        cmd_import(args.json_path)


if __name__ == "__main__":
    main()

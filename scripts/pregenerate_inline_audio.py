"""Vorgenerierung von Klick-Audio fuer Lesson-Texte (Gemini 2.5 Pro TTS).

Generiert pro `<p>` und `<li>` mit japanischem Anteil eine Audio-Datei,
attached `data-audio-url` ans HTML und speichert das augmentierte HTML in
`LessonContent.ai_generation_details.augmented_html`. Frontend kann dann
beim Klick instant abspielen ohne Live-TTS-Latenz.

Usage:
    python scripts/pregenerate_inline_audio.py 146           # eine Lesson
    python scripts/pregenerate_inline_audio.py --all         # alle published
    python scripts/pregenerate_inline_audio.py 146 --dry-run

Idempotent: gleicher Text-Hash → MP3 wird nicht neu generiert (Gemini-Calls
sind teuer und langsam).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import sys
import wave
from pathlib import Path

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5433/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")

import markdown as _md
import bleach as _bleach
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from app import create_app, db
from app.models import Lesson, LessonContent
from app.routes import _maybe_spell_out_kana_row

OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "inline_audio"
GEMINI_MODEL = "gemini-2.5-pro-preview-tts"
GEMINI_VOICE = "Leda"

_JP_RE = re.compile(r"[぀-ゟ゠-ヿ㐀-䶿一-鿿ｦ-ﾟ]")
_LATIN_RE = re.compile(r"[A-Za-zÀ-ſ]")

# Markdown-Pipeline replizieren (wie markdown_safe-Filter in app/__init__.py)
_MD_INSTANCE = _md.Markdown(extensions=["extra", "sane_lists", "smarty"])
_MD_ALLOWED_TAGS = {
    "p", "br", "strong", "em", "b", "i", "u", "s",
    "ul", "ol", "li", "blockquote", "code", "pre",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "span", "div", "hr",
    "table", "thead", "tbody", "tr", "th", "td",
}
_MD_ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
    "div": ["class"],
    "code": ["class"],
}


def render_markdown_html(text: str) -> str:
    _MD_INSTANCE.reset()
    html = _MD_INSTANCE.convert(text or "")
    cleaned = _bleach.clean(
        html, tags=_MD_ALLOWED_TAGS, attributes=_MD_ALLOWED_ATTRS, strip=True,
    )
    return cleaned


def text_hash(text: str) -> str:
    """Stabiler Hash fuer Cache-Key. SHA-1 erste 12 Hex = 48 Bit, kollisionssicher."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def has_japanese(text: str) -> bool:
    return bool(_JP_RE.search(text))


def is_de_only(text: str) -> bool:
    return _LATIN_RE.search(text) and not has_japanese(text)


_JP_SEQ_RE = re.compile(r"[぀-ヿ㐀-鿿]+")


def extract_speak_text(element) -> str:
    """Extrahiert den vorlese-relevanten JP-Text aus einem <p>/<li>-Element.

    Heuristik fuer Lerner-Klick: bei gemischten Texten wird **nur** der JP-Teil
    vorgelesen, nicht die deutsche Erklaerung. Das vermeidet, dass die japanische
    Stimme deutschen Text mit JP-Akzent liest. Der Block-Player oben kuemmert
    sich um die deutsche Erklaerung.

    Mehrere JP-Vorkommen werden mit `、` zu einem Audio verbunden — so klingt
    z.B. `「あおい」 — blau, 「いえ」 — Haus` wie `あおい、いえ`.

    Beispiele:
      `Die fünf Vokale: 「あいうえお」 (a, i, u, e, o)` → `あいうえお`
      `Sag 「あいうえお」 mehrmals hintereinander`     → `あいうえお`
      `「あおい」 — blau`                              → `あおい`
    """
    text = element.get_text(" ", strip=True)
    jp_parts = _JP_SEQ_RE.findall(text)
    if not jp_parts:
        return ""
    return "、".join(jp_parts)


def _gemini_call(client: genai.Client, contents: str) -> bytes:
    """Roher Gemini-TTS-Aufruf, raises bei leerer Response."""
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_VOICE)
                ),
            ),
        ),
    )
    cand = resp.candidates[0] if resp.candidates else None
    if cand is None or cand.content is None or not cand.content.parts:
        raise RuntimeError(
            f"Gemini leer (finish={getattr(cand, 'finish_reason', '?')})"
        )
    return cand.content.parts[0].inline_data.data


def synth_gemini_wav(client: genai.Client, text: str) -> bytes:
    """Generiert WAV-Bytes via Gemini, mit Retry-Prompt fuer kurze Wörter.

    Gemini blockt bei sehr kurzen Eingaben (2-3 Mora) oft mit FinishReason.OTHER
    (Safety-Filter). Workaround: zweiter Versuch mit Tutor-Wrapper, der dem
    Modell klar macht dass es eine Aussprache-Demo fuer Lerner ist.
    """
    # 1. Versuch: nackter Text (funktioniert bei laengeren Eingaben besser)
    try:
        pcm = _gemini_call(client, text)
    except RuntimeError as first_err:
        # 2. Versuch: Tutor-Wrapper, hilft bei kurzen Mora-Texten
        wrapped = f"Pronounce clearly for a Japanese learner: {text}"
        try:
            pcm = _gemini_call(client, wrapped)
        except RuntimeError:
            raise first_err

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    return buf.getvalue()


def synth_chirp_mp3(text: str) -> bytes:
    """Fallback: Chirp 3 HD Leda fuer Texte die Gemini nicht akzeptiert."""
    import base64
    import requests
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "ja-JP", "name": "ja-JP-Chirp3-HD-Leda"},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.85},
    }
    resp = requests.post(
        f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
        json=payload, timeout=15,
    )
    resp.raise_for_status()
    return base64.b64decode(resp.json()["audioContent"])


def process_lesson(lesson_id: int, dry_run: bool = False, force: bool = False) -> int:
    """Verarbeitet alle text-LessonContents einer Lesson. Returns: # generated."""
    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        print(f"[FEHLER] Lesson {lesson_id} nicht gefunden.")
        return 0

    rows = (
        db.session.query(LessonContent)
        .filter_by(lesson_id=lesson_id, content_type="text")
        .order_by(LessonContent.page_number, LessonContent.order_index)
        .all()
    )
    print(f"\n=== Lesson {lesson_id}: {lesson.title} — {len(rows)} text-Bloecke ===")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if not dry_run else None

    total_generated = 0
    total_reused = 0

    for lc in rows:
        text = lc.content_text or ""
        if not text.strip():
            continue
        html = render_markdown_html(text)
        soup = BeautifulSoup(html, "html.parser")

        # Alle <p> und <li> finden — bei verschachtelter <li><p> nur das innere <p>
        candidates = []
        for el in soup.find_all(["p", "li"]):
            if el.name == "li" and el.find("p"):
                continue
            candidates.append(el)

        page_audio_count = 0
        for el in candidates:
            speak_text = extract_speak_text(el)
            if len(speak_text) < 2:
                continue
            if not has_japanese(speak_text):
                # Nur DE — wir generieren erstmal NUR JP-Klick-Audio. DE-Texte
                # bleiben fuer den Block-Player oben. Spaeter optional auch DE.
                continue

            # Server wendet Pause-Heuristik an; pre-gen muss das ebenfalls tun
            tts_text_gemini = _maybe_spell_out_kana_row(speak_text, model="gemini")
            tts_text_chirp = _maybe_spell_out_kana_row(speak_text, model="chirp")
            h = text_hash(tts_text_gemini)

            # Vorhandene Files erkennen (Gemini WAV oder Chirp-Fallback MP3)
            existing_wav = OUT_DIR / f"{h}.wav"
            existing_mp3 = OUT_DIR / f"{h}.mp3"
            if existing_wav.exists() and not force:
                audio_url = f"/static/uploads/lessons/inline_audio/{h}.wav"
                total_reused += 1
            elif existing_mp3.exists() and not force:
                audio_url = f"/static/uploads/lessons/inline_audio/{h}.mp3"
                total_reused += 1
            elif dry_run:
                print(f"  [DRY] would generate: {speak_text[:60]!r} → {h}")
                audio_url = f"/static/uploads/lessons/inline_audio/{h}.wav"
            else:
                # Erst Gemini, bei Fehler Chirp-Fallback
                wav = None
                try:
                    wav = synth_gemini_wav(client, tts_text_gemini)
                    existing_wav.write_bytes(wav)
                    audio_url = f"/static/uploads/lessons/inline_audio/{h}.wav"
                    print(f"  [GEM] {speak_text[:60]!r} → {h}.wav ({len(wav)//1024} KB)")
                except Exception as e:
                    try:
                        mp3 = synth_chirp_mp3(tts_text_chirp)
                        existing_mp3.write_bytes(mp3)
                        audio_url = f"/static/uploads/lessons/inline_audio/{h}.mp3"
                        print(f"  [CHIRP] {speak_text[:60]!r} → {h}.mp3 ({len(mp3)//1024} KB) [Gemini: {e}]")
                    except Exception as e2:
                        print(f"  [ERR] {speak_text[:60]!r} → Gemini={e}, Chirp={e2}")
                        continue
                total_generated += 1

            el["data-audio-url"] = audio_url
            page_audio_count += 1

        if page_audio_count == 0:
            continue

        if dry_run:
            print(f"  [LC {lc.id} P{lc.page_number}] {page_audio_count} Audio-Tags wuerden gesetzt.")
            continue

        augmented = str(soup)
        details = dict(lc.ai_generation_details or {})
        details["augmented_html"] = augmented
        details["augmented_at_count"] = page_audio_count
        details["augmented_voice"] = f"gemini-2.5-pro:{GEMINI_VOICE}"
        lc.ai_generation_details = details
        db.session.commit()
        print(f"  [LC {lc.id} P{lc.page_number}] augmented_html gespeichert ({page_audio_count} Audios).")

    print(f"\n[FERTIG Lesson {lesson_id}] {total_generated} neu, {total_reused} wiederverwendet.")
    return total_generated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_id", type=int, nargs="?", default=None)
    ap.add_argument("--all", action="store_true", help="Alle published Lessons")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="MP3s auch bei Hash-Match neu generieren")
    args = ap.parse_args()

    if not args.lesson_id and not args.all:
        ap.error("Bitte lesson_id ODER --all angeben.")

    app = create_app()
    with app.app_context():
        if args.all:
            ids = [l.id for l in db.session.query(Lesson).filter_by(is_published=True).all()]
        else:
            ids = [args.lesson_id]

        total = 0
        for lid in ids:
            total += process_lesson(lid, dry_run=args.dry_run, force=args.force)

        print(f"\n=== ALLES FERTIG: {total} neue Audios ueber {len(ids)} Lesson(s) ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())

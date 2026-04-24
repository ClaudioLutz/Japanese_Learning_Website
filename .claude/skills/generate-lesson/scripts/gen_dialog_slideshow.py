"""Build a per-line slideshow for the Dialog-Page of a lesson.

Pro Dialog-Zeile:
  - 1 MP3 via Google Cloud TTS (Gender-korrekte Voice via SPEAKER_GENDER)
  - 1 PNG via OpenAI gpt-image-1-mini im Ghibli-Aquarell-Stil mit
    Charakter-Schablone und STRIKT ohne Text/Kanji/Ziffern
  - JSON-Eintrag mit jp, romaji, de, audio_path, image_path

Legt EIN LessonContent(content_type='dialog_slideshow') auf
order_index=1 an. Der bestehende Dialog-Text (content_type='text')
bleibt auf order_index=2 als Transcript-Fallback.

Idempotent: wenn bereits ein dialog_slideshow existiert, Refresh
statt Doppel-Insert.

Usage: python gen_dialog_slideshow.py <lesson_id>
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent
from app.ai_services import AILessonContentGenerator, GoogleCloudTTS

_MNN_SCRIPT = PROJECT_ROOT / "scripts"
if str(_MNN_SCRIPT) not in sys.path:
    sys.path.insert(0, str(_MNN_SCRIPT))
from generate_tts_audio import SPEAKER_GENDER, get_voice_for_speaker  # noqa: E402


# --- Charakter-Schablonen (wird pro Lektion zentral gepflegt) ---------------
# Die DALL-E-Prompts hängen eine Beschreibung der Dialog-Sprecher an,
# damit Tanaka nicht auf jedem Slide anders aussieht.
CHARACTER_SHEETS: dict[str, str] = {
    "Tanaka": (
        "Tanaka: Japanese man in his early 30s, short neat black hair, "
        "wearing a navy blazer over a white shirt, warm friendly smile"
    ),
    "Lisa": (
        "Lisa: young Western woman in her late 20s, chin-length blonde hair, "
        "wearing a pastel blue blouse, gentle curious expression"
    ),
    # Fallbacks fuer weitere Claude-Charaktere; der _character_brief()
    # erzeugt auch fuer Unbekannte ein generisches Portrait.
    "Mayuko": "Mayuko: Japanese woman in her 30s, long straight black hair, soft violet sweater, thoughtful expression",
    "Claudio": "Claudio: European man in his 30s, short brown hair, dark casual sweater, friendly engaged look",
    "Haruto": "Haruto: Japanese man in his late 20s, tousled black hair, olive jacket, calm smile",
}

NO_TEXT_BLOCK = (
    "ABSOLUTELY NO TEXT OF ANY KIND. No letters, no Japanese characters "
    "(kanji, hiragana, katakana), no Latin or German words, no numbers or "
    "digits, no signs, labels, signage, book titles, phone screens showing "
    "text, speech bubbles, captions, watermarks or logos. Pure visual "
    "imagery only."
)

STYLE_BLOCK = (
    "Studio Ghibli watercolor illustration blended with modern Japanese "
    "textbook art, soft warm palette, clean manga linework, gentle natural "
    "lighting, medium shot framing focusing on faces and gestures."
)


def _character_brief(speakers: list[str]) -> str:
    parts = []
    for s in speakers:
        if s in CHARACTER_SHEETS:
            parts.append(CHARACTER_SHEETS[s])
        else:
            gender = SPEAKER_GENDER.get(s, "female")
            if gender == "female":
                parts.append(f"{s}: woman in her late 20s, casual neat clothing, friendly expression")
            else:
                parts.append(f"{s}: man in his early 30s, casual neat clothing, friendly expression")
    return "Characters in every scene: " + "; ".join(parts) + "."


def _scene_brief(speaker: str, de_translation: str, all_speakers: list[str]) -> str:
    """Baut pro Zeile eine kurze Szenen-Beschreibung aus der DE-Uebersetzung."""
    other = next((s for s in all_speakers if s != speaker), "another person")
    # Heuristische, aber gut lesbare Szene ohne Worte
    return (
        f"Scene (medium shot, warm interior at a welcome party): "
        f"{speaker} is speaking to {other}. Visual focus on gestures and facial "
        f"expressions that suggest the meaning '{de_translation.strip()}'. "
        f"Cozy room with soft lights, blurred guests in background."
    )


def _build_prompt(speaker: str, de_translation: str, speakers: list[str]) -> str:
    return (
        f"{STYLE_BLOCK}\n\n"
        f"{_character_brief(speakers)}\n\n"
        f"{_scene_brief(speaker, de_translation, speakers)}\n\n"
        f"{NO_TEXT_BLOCK}"
    )


# --- Dialog-Parser (erkennt auch deutsche Uebersetzungszeile) ---------------

def parse_dialog_triplets(content_text: str) -> list[dict]:
    """Extract list of {speaker, jp, romaji, de} from MNN plaintext."""
    triplets: list[dict] = []
    current: dict = {}
    for raw in content_text.splitlines():
        line = raw.strip()
        if not line:
            if current.get("jp"):
                triplets.append(current)
                current = {}
            continue
        if line.startswith("(") and line.endswith(")"):
            current["romaji"] = line.strip("()")
            continue
        if line.startswith("->"):
            current["de"] = line[2:].strip()
            continue
        if ":" in line:
            speaker, _, jp = line.partition(":")
            current["speaker"] = speaker.strip()
            current["jp"] = jp.strip()
    if current.get("jp"):
        triplets.append(current)
    return triplets


# --- Audio pro Zeile --------------------------------------------------------

def _tts_line(tts: GoogleCloudTTS, text: str, voice_name: str, speed: float = 0.85) -> bytes | None:
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    ssml = f'<speak><prosody rate="{speed}">{esc(text)}</prosody></speak>'
    payload = {
        "input": {"ssml": ssml},
        "voice": {"languageCode": "ja-JP", "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    r = tts.requests.post(f"{tts.TTS_URL}?key={tts.api_key}", json=payload, timeout=30)
    if r.status_code != 200:
        print(f"      [TTS FEHLER] {r.status_code}: {r.text[:200]}")
        return None
    audio_b64 = r.json().get("audioContent")
    if not audio_b64:
        return None
    return base64.b64decode(audio_b64)


# --- Main -------------------------------------------------------------------

def find_dialog_page(lesson_id: int) -> LessonPage | None:
    pages = db.session.query(LessonPage).filter_by(lesson_id=lesson_id).order_by(LessonPage.page_number).all()
    for p in pages:
        t = (p.title or "").lower()
        if any(k in t for k in ("dialog", "konversation", "gespräch", "conversation")):
            return p
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python gen_dialog_slideshow.py <lesson_id>")
        return 2
    lesson_id = int(sys.argv[1])

    app = create_app()
    with app.app_context():
        lesson = db.session.get(Lesson, lesson_id)
        if not lesson:
            print(f"[FEHLER] Lesson {lesson_id} nicht gefunden")
            return 1

        dialog_page = find_dialog_page(lesson_id)
        if not dialog_page:
            print("[FEHLER] Keine Dialog-Page")
            return 1

        text_lc = (
            db.session.query(LessonContent)
            .filter_by(lesson_id=lesson_id, page_number=dialog_page.page_number, content_type="text")
            .first()
        )
        if not text_lc or not text_lc.content_text:
            print("[FEHLER] Kein Dialog-Text auf der Dialog-Page")
            return 1

        triplets = parse_dialog_triplets(text_lc.content_text)
        triplets = [t for t in triplets if t.get("jp") and t.get("speaker")]
        if not triplets:
            print("[FEHLER] Keine Dialog-Zeilen extrahiert")
            return 1

        speakers_ordered: list[str] = []
        for t in triplets:
            if t["speaker"] not in speakers_ordered:
                speakers_ordered.append(t["speaker"])

        print(f"[INFO] Lesson {lesson_id}: {len(triplets)} Zeilen, Sprecher: {', '.join(speakers_ordered)}")

        out_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "dialog_slideshow" / f"lesson_{lesson_id}"
        out_dir.mkdir(parents=True, exist_ok=True)

        tts = GoogleCloudTTS()
        if not tts.client:
            print("[FEHLER] Google TTS nicht konfiguriert")
            return 1
        gen = AILessonContentGenerator()
        if not gen.openai_client:
            print("[FEHLER] OpenAI nicht konfiguriert")
            return 1

        slides: list[dict] = []
        for i, t in enumerate(triplets, start=1):
            speaker = t["speaker"]
            jp = t["jp"]
            romaji = t.get("romaji", "")
            de = t.get("de", "")
            voice = get_voice_for_speaker(speaker, speakers_ordered)
            print(f"  [{i:2d}/{len(triplets)}] {speaker} ({voice.split('-')[-1]}): {jp[:40]}")

            # ---- Audio ----
            line_slug = f"line_{i:02d}"
            audio_path = out_dir / f"{line_slug}.mp3"
            if audio_path.exists():
                print("      [SKIP audio] bereits vorhanden")
            else:
                mp3 = _tts_line(tts, jp, voice)
                if mp3 is None:
                    print("      [FEHLER audio] abbruch")
                    return 1
                audio_path.write_bytes(mp3)
                print(f"      audio -> {audio_path.name} ({len(mp3)} bytes)")

            # ---- Bild ----
            image_path = out_dir / f"{line_slug}.png"
            if image_path.exists():
                print("      [SKIP image] bereits vorhanden")
            else:
                prompt = _build_prompt(speaker, de or jp, speakers_ordered)
                result = gen.generate_single_image(prompt=prompt, quality="hd")
                if not result or not result.get("image_bytes"):
                    err = (result or {}).get("error", "unbekannt")
                    print(f"      [FEHLER image] {err}")
                    return 1
                image_path.write_bytes(result["image_bytes"])
                print(f"      image -> {image_path.name} ({len(result['image_bytes'])} bytes)")

            # relative URL path fuer Jinja (/static/uploads/...):
            slides.append({
                "speaker": speaker,
                "voice": voice,
                "jp": jp,
                "romaji": romaji,
                "de": de,
                "audio": f"/static/uploads/lessons/dialog_slideshow/lesson_{lesson_id}/{line_slug}.mp3",
                "image": f"/static/uploads/lessons/dialog_slideshow/lesson_{lesson_id}/{line_slug}.png",
            })

        slideshow_json = json.dumps({
            "lesson_id": lesson_id,
            "speakers": speakers_ordered,
            "slides": slides,
        }, ensure_ascii=False, indent=2)

        existing = (
            db.session.query(LessonContent)
            .filter_by(
                lesson_id=lesson_id,
                page_number=dialog_page.page_number,
                content_type="dialog_slideshow",
            )
            .first()
        )
        if existing:
            existing.content_text = slideshow_json
            existing.title = "Konversation (Slideshow)"
            existing.generated_by_ai = True
            existing.ai_generation_details = {
                "generator": "dialog_slideshow_v1",
                "slides": len(slides),
            }
            db.session.commit()
            print(f"[OK] LessonContent {existing.id} aktualisiert (Slideshow refresh, {len(slides)} Slides)")
        else:
            # Bestehenden Text auf order_index=3 schieben (audio=1, slideshow=2, text=3)
            # Aber vorheriger Audio-Step legte Audio auf order_index=1 und Text=2.
            # Neue Reihenfolge: audio=1, slideshow=2, text=3.
            text_lc.order_index = 3
            audio_lc = (
                db.session.query(LessonContent)
                .filter_by(
                    lesson_id=lesson_id,
                    page_number=dialog_page.page_number,
                    content_type="audio",
                )
                .first()
            )
            if audio_lc:
                audio_lc.order_index = 1

            new_lc = LessonContent(
                lesson_id=lesson_id,
                content_type="dialog_slideshow",
                title="Konversation (Slideshow)",
                content_text=slideshow_json,
                page_number=dialog_page.page_number,
                order_index=2,
                generated_by_ai=True,
                ai_generation_details={
                    "generator": "dialog_slideshow_v1",
                    "slides": len(slides),
                },
            )
            db.session.add(new_lc)
            db.session.commit()
            print(f"[OK] LessonContent {new_lc.id} angelegt ({len(slides)} Slides)")

        return 0


if __name__ == "__main__":
    sys.exit(main())

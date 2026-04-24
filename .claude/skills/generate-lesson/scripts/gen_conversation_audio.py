"""Generate TTS audio for the dialog page of a lesson (Google Cloud TTS).

Usage:
  python gen_conversation_audio.py <lesson_id>

Pro Sprecher eine eigene Google-TTS-Voice (male/female rotierend). Die
einzelnen MP3-Fragmente werden byte-concat — das funktioniert, weil
Google-TTS-MP3 CBR (Constant Bitrate) ist und keine globalen Header hat.
Jedes Fragment enthaelt am Ende ein SSML `<break time="700ms"/>`, das die
Pause zwischen Sprechern garantiert.

Idempotent: wenn die Dialog-Page bereits ein audio-Content hat, Abbruch.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent
from app.ai_services import GoogleCloudTTS


# Voice-Rotation nach Sprecher-Reihenfolge. Google Cloud TTS ja-JP
# Neural2-Stimmen: B/C = female, D = male. Wir nehmen fuer Abwechslung
# B (female hell), D (male), C (female dunkler), D (male) ...
VOICE_POOL = [
    "ja-JP-Neural2-B",  # female
    "ja-JP-Neural2-D",  # male
    "ja-JP-Neural2-C",  # female (other)
    "ja-JP-Neural2-D",  # male
]


def find_dialog_page(lesson_id: int) -> LessonPage | None:
    pages = (
        db.session.query(LessonPage)
        .filter_by(lesson_id=lesson_id)
        .order_by(LessonPage.page_number)
        .all()
    )
    for p in pages:
        title = (p.title or "").lower()
        if "dialog" in title or "konversation" in title or "gespräch" in title or "conversation" in title:
            return p
    return None


def parse_dialog(content_text: str) -> list[tuple[str, str]]:
    """Extract (speaker, japanese_line) pairs from MNN-style plaintext.

    Returns list like [('Tanaka', 'はじめまして…'), ('Lisa', 'はじめまして…'), …].
    Ignores romaji '(...)' and translation '->' lines.
    """
    pairs = []
    for raw in content_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("(") or line.startswith("->"):
            continue
        if ":" in line:
            speaker, _, jp = line.partition(":")
            speaker = speaker.strip()
            jp = jp.strip()
            if jp and speaker:
                pairs.append((speaker, jp))
    return pairs


def assign_voices(pairs: list[tuple[str, str]]) -> dict[str, str]:
    """Map each unique speaker name to a voice, in order of first appearance."""
    mapping: dict[str, str] = {}
    for speaker, _ in pairs:
        if speaker not in mapping:
            mapping[speaker] = VOICE_POOL[len(mapping) % len(VOICE_POOL)]
    return mapping


def generate_line_mp3(tts: GoogleCloudTTS, text: str, voice_name: str, speed: float = 0.85) -> bytes | None:
    """Call Google Cloud TTS API directly with a specific voice_name and return MP3 bytes."""
    # Escape XML
    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    ssml = f'<speak><prosody rate="{speed}">{esc(text)}<break time="700ms"/></prosody></speak>'
    payload = {
        "input": {"ssml": ssml},
        "voice": {"languageCode": "ja-JP", "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    import base64
    response = tts.requests.post(
        f"{tts.TTS_URL}?key={tts.api_key}",
        json=payload,
        timeout=30,
    )
    if response.status_code != 200:
        print(f"      [TTS FEHLER] {response.status_code}: {response.text[:200]}")
        return None
    audio_b64 = response.json().get("audioContent")
    if not audio_b64:
        return None
    return base64.b64decode(audio_b64)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python gen_conversation_audio.py <lesson_id>")
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
            print(f"[FEHLER] Keine Dialog-Page in Lesson {lesson_id} gefunden.")
            return 1

        # Idempotency check — allow 'refresh' arg to overwrite (simple: delete existing row)
        existing_audio = (
            db.session.query(LessonContent)
            .filter_by(
                lesson_id=lesson_id,
                page_number=dialog_page.page_number,
                content_type="audio",
            )
            .first()
        )

        text_lc = (
            db.session.query(LessonContent)
            .filter_by(
                lesson_id=lesson_id,
                page_number=dialog_page.page_number,
                content_type="text",
            )
            .order_by(LessonContent.order_index)
            .first()
        )
        if not text_lc or not text_lc.content_text:
            print(f"[FEHLER] Kein Dialog-Text auf Page {dialog_page.page_number}.")
            return 1

        pairs = parse_dialog(text_lc.content_text)
        if not pairs:
            print("[FEHLER] Keine Sprecher-Zeilen extrahiert.")
            return 1

        voice_map = assign_voices(pairs)
        print(f"[INFO] {len(pairs)} Zeilen, {len(voice_map)} Sprecher:")
        for speaker, voice in voice_map.items():
            print(f"       {speaker} -> {voice}")

        tts = GoogleCloudTTS()
        if not tts.client:
            print("[FEHLER] Google TTS nicht konfiguriert (GOOGLE_API_KEY fehlt).")
            return 1

        # Generate each line as its own MP3 and concat
        mp3_chunks: list[bytes] = []
        for i, (speaker, jp_line) in enumerate(pairs, start=1):
            voice = voice_map[speaker]
            print(f"  [{i:2d}/{len(pairs)}] {speaker} ({voice.split('-')[-1]}): {jp_line[:40]}")
            mp3 = generate_line_mp3(tts, jp_line, voice)
            if mp3 is None:
                print(f"      [FEHLER] Zeile {i} hat kein MP3 geliefert — Abbruch.")
                return 1
            mp3_chunks.append(mp3)

        merged = b"".join(mp3_chunks)

        out_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "audio" / f"lesson_{lesson_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "conversation.mp3"
        out_path.write_bytes(merged)
        print(f"[OK] MP3: {out_path} ({len(merged)} bytes, concat aus {len(mp3_chunks)} Fragmenten)")

        rel_path = f"lessons/audio/lesson_{lesson_id}/conversation.mp3"
        ai_details = {
            "generator": "google_cloud_tts_multivoice",
            "voices": voice_map,
            "lines": len(pairs),
        }

        if existing_audio:
            # Refresh metadata + file_size (MP3 was replaced on disk)
            existing_audio.file_path = rel_path
            existing_audio.file_type = "audio/mpeg"
            existing_audio.file_size = len(merged)
            existing_audio.media_url = f"/static/uploads/{rel_path}"
            existing_audio.ai_generation_details = ai_details
            db.session.commit()
            print(f"[OK] LessonContent {existing_audio.id} aktualisiert (Multi-Voice).")
        else:
            text_lc.order_index = 2
            audio_lc = LessonContent(
                lesson_id=lesson_id,
                content_type="audio",
                title="Konversation (Audio)",
                page_number=dialog_page.page_number,
                order_index=1,
                file_path=rel_path,
                file_type="audio/mpeg",
                file_size=len(merged),
                media_url=f"/static/uploads/{rel_path}",
                generated_by_ai=True,
                ai_generation_details=ai_details,
            )
            db.session.add(audio_lc)
            db.session.commit()
            print(f"[OK] LessonContent {audio_lc.id} angelegt.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

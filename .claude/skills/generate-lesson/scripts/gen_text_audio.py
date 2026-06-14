"""Generate per-Text-Block TTS audio fuer eine Lesson (DE+JA gemischt).

Usage:
  python gen_text_audio.py <lesson_id> [--page <n>]

User-Direktive 2026-04-25: Vorlese-Stimme soll Deutsch nicht mit japanischem
Akzent sprechen. Loesung: Text-Block in Sprachsegmente splitten (Hira/Kata/
Kanji → ja-JP-Stimme, Lateinschrift → de-DE-Stimme), pro Segment einen
Google-Cloud-TTS-Call, MP3s byte-concat (Google MP3 ist CBR ohne globalen
Header — pro Sprecher-Wechsel ein neuer Stream funktioniert).

Pro Text-LessonContent eine eigene MP3 in
  app/static/uploads/lessons/text_audio/lesson_{id}/page_{n}_content_{cid}.mp3
und `LessonContent.media_url` wird auf den Pfad gesetzt — dann rendert das
Template einen Mini-Player oberhalb des `rich-text-content`.

Idempotent: existiert media_url + Datei mit identischem content_text-Hash
in `ai_generation_details.text_hash`, wird neu gerendert NUR mit `--force`.
Markdown wird vor TTS gestrippt: `**bold**`, `## H2`, Listen `- `, Code,
`(romaji)` direkt nach JP-Zeichen werden entfernt (Ohren brauchen sie nicht).

Skip-Heuristik: text-Bloecke unter 80 Zeichen (Quiz-Intro, Mini-Texte) und
Dialog-Bloecke (Speaker: ... Format) werden uebersprungen — fuer Dialoge
existiert bereits `pipeline.py audio` + `slideshow`.
"""
import argparse
import base64
import hashlib
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db  # noqa: E402
from app.models import Lesson, LessonContent  # noqa: E402
from app.ai_services import GoogleCloudTTS  # noqa: E402

# ---------------------------------------------------------------------------
# Voices
# ---------------------------------------------------------------------------
# JA: Gemini 2.5 Pro TTS Leda — Studio-Qualitaet, gleiche Stimme wie Klick-Audio
#     (= konsistente Lerner-Erfahrung zwischen Block-Player und Klick-Audio)
# DE: Google Cloud TTS Neural2-G — bleibt wie bisher (Gemini hat keine
#     deutsche Stimme die natuerlich klingen wuerde)
# Beide liefern 24 kHz mono 16-bit PCM, somit byte-konkatenierbar in WAV.
GEMINI_MODEL = "gemini-2.5-pro-preview-tts"
GEMINI_VOICE = "Leda"
DE_VOICE = "de-DE-Neural2-G"
SAMPLE_RATE = 24000

from app.services.tts_text import (  # noqa: E402
    segment_by_language,
    strip_markdown,
    strip_romaji_after_jp,
)


# ---------------------------------------------------------------------------
# TTS-Call
# ---------------------------------------------------------------------------
def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def synth_segment_de_pcm(tts: GoogleCloudTTS, text: str, speed: float = 0.95) -> bytes | None:
    """Cloud TTS Neural2-G fuer Deutsch — liefert 24kHz LINEAR16 PCM (kein WAV-Header)."""
    ssml = f'<speak><prosody rate="{speed}">{_xml_escape(text)}<break time="200ms"/></prosody></speak>'
    payload = {
        "input": {"ssml": ssml},
        "voice": {"languageCode": "de-DE", "name": DE_VOICE},
        "audioConfig": {
            "audioEncoding": "LINEAR16",
            "sampleRateHertz": SAMPLE_RATE,
        },
    }
    resp = tts.requests.post(
        f"{tts.TTS_URL}?key={tts.api_key}", json=payload, timeout=30,
    )
    if resp.status_code != 200:
        print(f"      [TTS FEHLER] {resp.status_code} (de): {resp.text[:160]}")
        return None
    audio_b64 = resp.json().get("audioContent")
    if not audio_b64:
        return None
    wav = base64.b64decode(audio_b64)
    # Cloud TTS LINEAR16 liefert WAV mit 44-byte Header. Strip header → reines PCM.
    if wav[:4] == b"RIFF":
        # Suche "data"-Chunk-Header und nimm nur Payload
        idx = wav.find(b"data")
        if idx >= 0:
            return wav[idx + 8:]
    return wav


def synth_segment_ja_pcm(text: str) -> bytes | None:
    """Gemini 2.5 Pro TTS Leda fuer Japanisch — liefert 24kHz mono PCM raw.

    Bei Safety-Block (FinishReason.OTHER) wird der Tutor-Prompt-Retry versucht,
    bei nochmaligem Fail ein leerer Bytes-Buf returned (besser als Crash).
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    # Hartes Timeout (60s): ohne dieses blockiert ein haengender Gemini-Request
    # endlos (kein Default-Timeout im SDK) und legt den ganzen Batch lahm.
    # Bei Timeout greift unten der Chirp-Fallback.
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60000),
    )

    def _call(contents):
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
            return None
        return cand.content.parts[0].inline_data.data

    try:
        pcm = _call(text)
    except Exception as e:
        print(f"      [GEMINI EXC] (ja): {text[:60]!r} — {e}")
        pcm = None
    if pcm is None:
        # Tutor-Prompt-Retry fuer kurze Mora-Texte
        try:
            pcm = _call(f"Pronounce clearly for a Japanese learner: {text}")
        except Exception:
            pcm = None
    if pcm is not None:
        return pcm

    # Fallback: Chirp 3 HD Leda LINEAR16 PCM (gleiche Persoenlichkeit, andere Engine)
    print(f"      [GEMINI leer fuer {text[:30]!r}] — Fallback Chirp 3 HD")
    return _synth_chirp_pcm_fallback(text)


def _synth_chirp_pcm_fallback(text: str) -> bytes | None:
    """Chirp 3 HD Leda als JP-PCM-Fallback wenn Gemini blockt."""
    import requests as http_requests
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "ja-JP", "name": "ja-JP-Chirp3-HD-Leda"},
        "audioConfig": {
            "audioEncoding": "LINEAR16",
            "sampleRateHertz": SAMPLE_RATE,
            "speakingRate": 0.85,
        },
    }
    try:
        resp = http_requests.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
            json=payload, timeout=15,
        )
        if resp.status_code != 200:
            print(f"      [CHIRP FALLBACK FEHLER] {resp.status_code}: {resp.text[:120]}")
            return None
        wav = base64.b64decode(resp.json().get("audioContent", ""))
        if wav[:4] == b"RIFF":
            idx = wav.find(b"data")
            if idx >= 0:
                return wav[idx + 8:]
        return wav
    except Exception as e:
        print(f"      [CHIRP FALLBACK EXC] {e}")
        return None


def synth_segment(tts: GoogleCloudTTS, lang: str, text: str, speed: float = 0.95) -> bytes | None:
    """Dispatcher: liefert 24kHz mono 16-bit PCM (kein WAV-Header) je Sprache."""
    if lang == "ja":
        return synth_segment_ja_pcm(text)
    return synth_segment_de_pcm(tts, text, speed)


def wrap_pcm_as_wav(pcm: bytes) -> bytes:
    """Verpackt rohe PCM-Daten in einen WAV-Container."""
    import wave
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Text-Auswahl
# ---------------------------------------------------------------------------
def is_dialog_block(text: str) -> bool:
    """Heuristik: Text enthaelt Speaker-Zeilen wie 'Tanaka: ...' oder 'Lisa: ...'."""
    speakers = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("(") or line.startswith("->"):
            continue
        # erste Token vor : ist potenziell Sprecher
        if ":" in line.split()[0] and len(line.split(":")[0]) <= 15:
            speakers += 1
    return speakers >= 4


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_id", type=int)
    ap.add_argument("--page", type=int, default=None,
                    help="Nur diese Page rendern (default: alle)")
    ap.add_argument("--force", action="store_true",
                    help="Bestehende MP3s neu erzeugen")
    ap.add_argument("--min-chars", type=int, default=80,
                    help="Mindestlaenge fuer Vorlese-MP3 (default: 80)")
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        lesson = db.session.get(Lesson, args.lesson_id)
        if not lesson:
            print(f"[FEHLER] Lesson {args.lesson_id} nicht gefunden.")
            return 1

        q = (
            db.session.query(LessonContent)
            .filter_by(lesson_id=args.lesson_id, content_type="text")
            .order_by(LessonContent.page_number, LessonContent.order_index)
        )
        if args.page is not None:
            q = q.filter(LessonContent.page_number == args.page)
        rows = q.all()
        if not rows:
            print(f"[FEHLER] Keine text-LessonContents in Lesson {args.lesson_id}.")
            return 1

        tts = GoogleCloudTTS()
        if not tts.client:
            print("[FEHLER] Google TTS nicht konfiguriert (GOOGLE_API_KEY/GOOGLE_TTS_API_KEY fehlt).")
            return 1

        out_root = (
            PROJECT_ROOT / "app" / "static" / "uploads"
            / "lessons" / "text_audio" / f"lesson_{args.lesson_id}"
        )
        out_root.mkdir(parents=True, exist_ok=True)

        rendered = 0
        skipped = 0
        for lc in rows:
            text = lc.content_text or ""
            if not text.strip():
                continue
            if len(text) < args.min_chars:
                print(f"[SKIP] LC {lc.id} (Page {lc.page_number}): zu kurz ({len(text)} < {args.min_chars}).")
                skipped += 1
                continue
            if is_dialog_block(text):
                print(f"[SKIP] LC {lc.id} (Page {lc.page_number}): Dialog — bereits via `audio`-Step abgedeckt.")
                skipped += 1
                continue

            new_hash = text_hash(text)
            existing_details = lc.ai_generation_details or {}
            if (
                not args.force
                and lc.media_url
                and existing_details.get("text_hash") == new_hash
            ):
                print(f"[SKIP] LC {lc.id} (Page {lc.page_number}): MP3 aktuell (hash {new_hash}).")
                skipped += 1
                continue

            # Markdown + Romaji weg
            tts_text = strip_markdown(text)
            tts_text = strip_romaji_after_jp(tts_text)

            segments = segment_by_language(tts_text)
            if not segments:
                print(f"[SKIP] LC {lc.id}: Nach Strip keine sprechbaren Segmente.")
                skipped += 1
                continue

            seg_summary = ", ".join(f"{lang}={len(t)}" for lang, t in segments[:8])
            print(f"[INFO] LC {lc.id} (Page {lc.page_number}, '{lc.title or ''}'): "
                  f"{len(segments)} Segmente ({seg_summary}{'...' if len(segments) > 8 else ''})")

            pcm_chunks: list[bytes] = []
            for i, (lang, seg) in enumerate(segments, start=1):
                pcm = synth_segment(tts, lang, seg)
                if pcm is None:
                    print(f"      [FEHLER] Segment {i} ({lang}) liefert kein Audio — Abbruch.")
                    return 1
                pcm_chunks.append(pcm)
                # 200ms Stille zwischen Segmenten fuer natuerliche Pause
                pcm_chunks.append(b"\x00\x00" * int(SAMPLE_RATE * 0.2))

            merged_pcm = b"".join(pcm_chunks)
            wav_bytes = wrap_pcm_as_wav(merged_pcm)
            out_name = f"page_{lc.page_number}_content_{lc.id}.wav"
            out_path = out_root / out_name
            out_path.write_bytes(wav_bytes)

            rel = f"lessons/text_audio/lesson_{args.lesson_id}/{out_name}"
            # /uploads/-Route hat GCS-Fallback (routes.py:4076), /static/uploads/ nicht.
            lc.media_url = f"/uploads/{rel}"
            lc.file_path = rel
            lc.file_type = "audio/wav"
            lc.file_size = len(wav_bytes)
            lc.ai_generation_details = {
                **existing_details,
                "tts_generator": "gemini_ja_neural2_de_split",
                "ja_voice": f"{GEMINI_MODEL}:{GEMINI_VOICE}",
                "de_voice": DE_VOICE,
                "text_hash": new_hash,
                "segments": len(segments),
            }
            db.session.commit()
            print(f"      [OK] {out_name} ({len(wav_bytes)} bytes, {len(segments)} Segmente).")
            rendered += 1

        print(f"\n[FERTIG] {rendered} MP3s neu gerendert, {skipped} uebersprungen.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

"""Gemeinsame TTS-Aufrufe mit hartem Timeout + einem Retry.

Hintergrund: Am 24.09.2026 hing ``scripts/pregenerate_inline_audio.py`` fast zwei
Tage in einem einzigen Gemini-TTS-Call — das google-genai SDK hat ohne
``http_options.timeout`` kein Default-Timeout. Alle TTS-Pfade (Gemini fuer
Japanisch, Cloud-TTS-REST fuer Deutsch und den Chirp-Fallback) laufen deshalb
ueber diese Helfer:

- ``make_gemini_client``: genai.Client mit hartem Timeout (Default 120 s).
- ``synth_gemini_pcm``: ein Gemini-TTS-Aufruf, bei Exception (Timeout, Netz,
  5xx) genau ein Retry; leere Antwort (Safety-Block) wird NICHT wiederholt,
  sondern als ``GeminiEmptyAudioError`` gemeldet (Aufrufer hat dafuer den
  Tutor-Prompt-Retry bzw. den Chirp-Fallback).
- ``post_cloud_tts``: Cloud-TTS-REST-POST mit Timeout und einem Retry bei
  Netzwerk-/Timeout-Fehlern.
- ``synth_gemini_pcm_robust``: Gemini mit Kurz-String-Behandlung (Anweisungs-
  Prompt-Versuche, wenn der nackte Text leer zurueckkommt).
- ``synth_chirp_wav`` / ``synth_chirp_pcm``: Chirp-3-HD-Fallback als LINEAR16
  (24 kHz WAV) statt MP3 — so bleibt der Hash-Dateiname ``.wav`` und die URL
  ist identisch mit dem Gemini-Pfad (29.09.2026).

Bewusst ohne Flask-Abhaengigkeit, damit Skripte und Routen es teilen koennen.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

GEMINI_TTS_MODEL = "gemini-2.5-pro-preview-tts"
GEMINI_TTS_VOICE = "Leda"
CLOUD_TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

# Batch-Skripte: 120 s pro Call, 1 Retry. Web-Requests nutzen kuerzere Werte.
TTS_TIMEOUT_S = 120
REST_TIMEOUT_S = 30
TTS_RETRIES = 1
SAMPLE_RATE = 24000

CHIRP_JA_VOICE = "ja-JP-Chirp3-HD-Leda"
CHIRP_SPEAKING_RATE = 0.85

# Kurz-Strings (Einzelwoerter, Zahlwoerter): Gemini-TTS liefert beim nackten
# Text oft finish=OTHER bzw. 400 "Model tried to generate text" — das Modell
# haelt "ちち" fuer einen Chat-Prompt. Probe 29.09.2026 auf hp-ubuntu (Pro-Quota
# erschoepft → gemini-2.5-flash-preview-tts als Stellvertreter; 14 Kurzwoerter
# inkl. ちち/はは/ひゃく, je 2-3 Aufrufe), Erfolgsquote pro Aufruf:
#   nackt 5/30, "ちち。" 0/6, "、ちち" 7/30, "「ちち」" 1/6, "、ちち。" 0/6,
#   "Pronounce clearly for a Japanese learner: …" 2/9,
#   "次の単語をはっきり読み上げてください：…" 7/12,
#   "Text-to-speech, Japanese, read exactly this and nothing else: …" 23/36.
# Keine Variante ist deterministisch → mehrere Anweisungs-Versuche. Gesprochen
# wird nur das Wort (0.5-1.3 s), die Anweisung nicht; zur Sicherheit verwirft
# _plausible_duration zu lange Ergebnisse. Satzzeichen-Polsterung bringt nichts.
GEMINI_SHORT_TEXT_PROMPTS: tuple[str, ...] = (
    "Text-to-speech, Japanese, read exactly this and nothing else: {text}",
    "次の単語をはっきり読み上げてください：{text}",
    "Text-to-speech, Japanese, read exactly this and nothing else: {text}",
)

# 400-Antwort, die inhaltlich eine leere Audio-Antwort ist (kein Retry noetig)
_TEXT_INSTEAD_OF_AUDIO_MARKER = "tried to generate text"


class GeminiEmptyAudioError(RuntimeError):
    """Gemini hat geantwortet, aber ohne Audio (z.B. Safety-Block)."""


def pcm_to_wav(pcm: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Verpackt rohes 16-bit-mono-PCM in einen WAV-Container."""
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def wav_to_pcm(data: bytes) -> bytes:
    """Entfernt einen RIFF/WAV-Header (Cloud-TTS LINEAR16) → rohes PCM."""
    if data[:4] == b"RIFF":
        idx = data.find(b"data")
        if idx >= 0:
            return data[idx + 8:]
    return data


def make_gemini_client(api_key: str | None, timeout_s: float = TTS_TIMEOUT_S) -> Any:
    """genai.Client mit hartem HTTP-Timeout (SDK erwartet Millisekunden)."""
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),
    )


def _speech_config(voice: str) -> Any:
    from google.genai import types

    return types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            ),
        ),
    )


def synth_gemini_pcm(
    client: Any,
    contents: str,
    *,
    model: str = GEMINI_TTS_MODEL,
    voice: str = GEMINI_TTS_VOICE,
    retries: int = TTS_RETRIES,
) -> bytes:
    """Ein Gemini-TTS-Aufruf → rohes 24-kHz-PCM.

    Raises:
        GeminiEmptyAudioError: Antwort ohne Audio (kein Retry).
        Exception: letzte Exception, wenn alle Versuche (1 + ``retries``)
            an Timeout/Netz/API-Fehlern scheitern.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = client.models.generate_content(
                model=model, contents=contents, config=_speech_config(voice),
            )
        except Exception as exc:  # Timeout, Netz, 5xx
            if _TEXT_INSTEAD_OF_AUDIO_MARKER in str(exc):
                # Kurz-String-Symptom, deterministisch genug: nicht wiederholen
                raise GeminiEmptyAudioError(
                    "Gemini leer (400: Modell wollte Text statt Audio erzeugen)"
                ) from exc
            last_exc = exc
            logger.warning(
                "Gemini-TTS Versuch %d/%d fehlgeschlagen: %s",
                attempt + 1, retries + 1, exc,
            )
            continue
        cand = resp.candidates[0] if resp.candidates else None
        if cand is None or cand.content is None or not cand.content.parts:
            raise GeminiEmptyAudioError(
                f"Gemini leer (finish={getattr(cand, 'finish_reason', '?')})"
            )
        return cand.content.parts[0].inline_data.data
    assert last_exc is not None
    raise last_exc


def post_cloud_tts(
    api_key: str | None,
    payload: dict,
    *,
    timeout_s: float = REST_TIMEOUT_S,
    retries: int = TTS_RETRIES,
    session: Any = None,
) -> Any:
    """POST auf Cloud-TTS-REST mit Timeout; Retry nur bei Netz-/Timeout-Fehlern.

    Gibt das ``requests.Response``-Objekt zurueck (Statuscode prueft der
    Aufrufer). Nach erschoepften Versuchen wird die letzte Exception geworfen.
    """
    import requests

    poster = session or requests
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return poster.post(
                f"{CLOUD_TTS_URL}?key={api_key}", json=payload, timeout=timeout_s,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            logger.warning(
                "Cloud-TTS Versuch %d/%d fehlgeschlagen: %s",
                attempt + 1, retries + 1, exc,
            )
    assert last_exc is not None
    raise last_exc


def synth_gemini_pcm_robust(
    client: Any,
    text: str,
    *,
    model: str = GEMINI_TTS_MODEL,
    voice: str = GEMINI_TTS_VOICE,
    retries: int = TTS_RETRIES,
    prompts: tuple[str, ...] = GEMINI_SHORT_TEXT_PROMPTS,
) -> bytes:
    """Gemini-TTS mit Kurz-String-Behandlung → rohes 24-kHz-PCM.

    Erst der nackte Text; kommt Gemini leer zurueck, nacheinander die
    Anweisungs-Prompts aus ``prompts``. Timeouts/Netzfehler werden NICHT
    abgefangen (dafuer ist der Retry in ``synth_gemini_pcm`` zustaendig).

    Raises:
        GeminiEmptyAudioError: alle Varianten leer — Aufrufer nimmt Chirp.
    """
    try:
        return synth_gemini_pcm(client, text, model=model, voice=voice, retries=retries)
    except GeminiEmptyAudioError as first_err:
        last_err = first_err
    for tpl in prompts:
        try:
            pcm = synth_gemini_pcm(
                client, tpl.format(text=text), model=model, voice=voice, retries=retries,
            )
        except GeminiEmptyAudioError as err:
            last_err = err
            continue
        if not _plausible_duration(pcm, text):
            # Anweisung vermutlich mitgesprochen → verwerfen, naechste Variante
            last_err = GeminiEmptyAudioError(
                f"Gemini-Prompt-Audio zu lang ({len(pcm) / (2 * SAMPLE_RATE):.1f} s)"
            )
            logger.warning("Gemini-TTS Prompt-Audio verworfen: %s", last_err)
            continue
        logger.info("Gemini-TTS Kurz-String via Prompt gerendert: %r", text[:30])
        return pcm
    raise last_err


def _plausible_duration(pcm: bytes, text: str) -> bool:
    """Grobe Obergrenze fuer die Sprechdauer von ``text`` (16-bit mono, 24 kHz).

    1.5 s Grundpuffer + 0.4 s pro Zeichen. Ein Kurzwort (2-4 Zeichen) liegt
    real bei 0.5-1.3 s; mitgesprochene Anweisung waere deutlich > 3 s.
    """
    seconds = len(pcm) / (2 * SAMPLE_RATE)
    return seconds <= 1.5 + 0.4 * len(text)


def synth_chirp_wav(
    api_key: str | None,
    text: str,
    *,
    voice_name: str = CHIRP_JA_VOICE,
    speaking_rate: float = CHIRP_SPEAKING_RATE,
    sample_rate: int = SAMPLE_RATE,
    session: Any = None,
) -> bytes:
    """Chirp-3-HD-Fallback als WAV (LINEAR16, 24 kHz mono) statt MP3.

    Gleiches Format wie der Gemini-Pfad → gleicher ``.wav``-Dateiname/URL.

    Raises:
        requests.HTTPError: Statuscode != 200.
        RuntimeError: Antwort ohne ``audioContent``.
    """
    import base64

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": voice_name[:5], "name": voice_name},
        "audioConfig": {
            "audioEncoding": "LINEAR16",
            "sampleRateHertz": sample_rate,
            "speakingRate": speaking_rate,
        },
    }
    resp = post_cloud_tts(api_key, payload, session=session)
    resp.raise_for_status()
    audio_b64 = (resp.json() or {}).get("audioContent")
    if not audio_b64:
        raise RuntimeError("Chirp-TTS ohne audioContent")
    # Cloud-TTS liefert bei LINEAR16 bereits einen WAV-Header; neu verpacken
    # garantiert einen sauberen Header mit der erwarteten Samplerate.
    return pcm_to_wav(wav_to_pcm(base64.b64decode(audio_b64)), sample_rate)


def synth_chirp_pcm(api_key: str | None, text: str, **kwargs: Any) -> bytes:
    """Wie ``synth_chirp_wav``, aber rohes PCM (zum Konkatenieren im Block-Player)."""
    return wav_to_pcm(synth_chirp_wav(api_key, text, **kwargs))

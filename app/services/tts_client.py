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


class GeminiEmptyAudioError(RuntimeError):
    """Gemini hat geantwortet, aber ohne Audio (z.B. Safety-Block)."""


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

"""Gemeinsame TTS-Aufrufe mit hartem Timeout + einem Retry.

Hintergrund: Am 24.09.2026 hing ``scripts/pregenerate_inline_audio.py`` fast zwei
Tage in einem einzigen Gemini-TTS-Call — das google-genai SDK hat ohne
``http_options.timeout`` kein Default-Timeout. Alle TTS-Pfade (Gemini fuer
Japanisch, Cloud-TTS-REST fuer Deutsch und den Chirp-Fallback) laufen deshalb
ueber diese Helfer:

- ``make_gemini_client``: genai.Client mit hartem Timeout (Default 120 s).
- ``synth_gemini_pcm``: ein Gemini-TTS-Aufruf, bei Exception (Timeout, Netz,
  5xx) genau ein Retry; leere Antwort (Safety-Block) wird NICHT wiederholt,
  sondern als ``GeminiEmptyAudioError`` gemeldet.
- ``post_cloud_tts``: Cloud-TTS-REST-POST mit Timeout und einem Retry bei
  Netzwerk-/Timeout-Fehlern. Der API-Key geht als Header ``X-Goog-Api-Key``
  mit, NIE als ``?key=`` in der URL (06.10.2026: requests-Fehlermeldungen
  enthalten die volle URL und landeten so in Logs).
- ``redact_secrets`` / ``safe_error``: Fehlermeldungen vor print/logging von
  ``key=…`` und ``AIza…``-Keys bereinigen.
- ``synth_gemini_pcm_robust``: Gemini mit Kurz-String-Behandlung (Anweisungs-
  Prompts nur fuer Kurz-Strings, laengere Texte wie bisher Tutor-Prompt).
- ``synth_chirp_wav`` / ``synth_chirp_pcm``: Chirp-3-HD-Fallback als LINEAR16
  (24 kHz) statt MP3 — so bleibt der Hash-Dateiname ``.wav`` und die URL
  ist identisch mit dem Gemini-Pfad (29.09.2026).

Bewusst ohne Flask-Abhaengigkeit, damit Skripte und Routen es teilen koennen.
"""
from __future__ import annotations

import logging
import re
import unicodedata
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
DE_NEURAL2_VOICE = "de-DE-Neural2-G"

# Engine-Kennungen (Manifest, augmented_voice, data-audio-engine)
ENGINE_GEMINI = "gemini"
ENGINE_CHIRP = "chirp"
ENGINE_UNKNOWN = "unknown"
ENGINE_LABELS = {
    ENGINE_GEMINI: f"{GEMINI_TTS_MODEL}:{GEMINI_TTS_VOICE}",
    ENGINE_CHIRP: CHIRP_JA_VOICE,
}

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
# _plausible_short_duration zu lange Ergebnisse. Satzzeichen-Polsterung bringt
# nichts. Die Prompts gelten NUR fuer Kurz-Strings (is_short_text): bei laengeren
# Texten ist eine mitgesprochene Anweisung an der Dauer nicht erkennbar.
GEMINI_SHORT_TEXT_PROMPTS: tuple[str, ...] = (
    "Text-to-speech, Japanese, read exactly this and nothing else: {text}",
    "次の単語をはっきり読み上げてください：{text}",
    "Text-to-speech, Japanese, read exactly this and nothing else: {text}",
)
# Laengere Texte: bisheriges Verhalten — ein Tutor-Prompt-Versuch, dann Chirp.
GEMINI_TUTOR_PROMPT = "Pronounce clearly for a Japanese learner: {text}"

# Kurz-String = hoechstens so viele Zeichen, ohne Satzzeichen/Leerraum
SHORT_TEXT_MAX_CHARS = 8
# Dauergrenze fuer Prompt-Audio bei Kurz-Strings: Grundpuffer + pro Zeichen.
# 2 Zeichen → 1.8 s (real 0.5-1.3 s), 8 Zeichen → 3.6 s; die kuerzeste
# Anweisung allein dauert gesprochen > 3.5 s.
SHORT_PROMPT_BASE_S = 1.2
SHORT_PROMPT_PER_CHAR_S = 0.3

# Obergrenze der Gemini-Aufrufe von synth_gemini_pcm_robust pro Text
# (nackt + Prompt-Varianten, je 1 + TTS_RETRIES Versuche) — Quota-Planung.
GEMINI_MAX_CALLS_ROBUST = (1 + len(GEMINI_SHORT_TEXT_PROMPTS)) * (1 + TTS_RETRIES)

# 400-Antwort, die inhaltlich eine leere Audio-Antwort ist (kein Retry noetig)
_TEXT_INSTEAD_OF_AUDIO_MARKER = "tried to generate text"

# key=<wert> in URLs/Meldungen und nackte Google-API-Keys (AIza…)
_KEY_PARAM_RE = re.compile(r"(?i)(key=)[^&\"'\s]+")
_GOOGLE_KEY_RE = re.compile(r"AIza[0-9A-Za-z_\-]{10,}")


class GeminiEmptyAudioError(RuntimeError):
    """Gemini hat geantwortet, aber ohne Audio (z.B. Safety-Block)."""


class CloudTtsError(RuntimeError):
    """Cloud-TTS (Chirp/Neural2) lieferte kein Audio (Meldung bereits bereinigt)."""


def redact_secrets(text: Any) -> str:
    """Entfernt API-Keys aus einer Meldung (``key=…`` und ``AIza…``)."""
    s = str(text)
    s = _KEY_PARAM_RE.sub(r"\1REDACTED", s)
    return _GOOGLE_KEY_RE.sub("REDACTED", s)


def safe_error(exc: BaseException | str) -> str:
    """Exception als Text fuer print/logging — garantiert ohne API-Key."""
    if isinstance(exc, BaseException):
        text = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
    else:
        text = exc
    return redact_secrets(text)


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


def _extract_audio(resp: Any) -> bytes:
    """Audio-Bytes aus einer Gemini-Antwort; sonst GeminiEmptyAudioError.

    Prueft alle Parts: ein Text-Part, fehlendes ``inline_data`` oder leere
    Daten gelten als leere Antwort (nicht None/AttributeError).
    """
    candidates = getattr(resp, "candidates", None) or []
    cand = candidates[0] if candidates else None
    content = getattr(cand, "content", None)
    parts = getattr(content, "parts", None) or []
    for part in parts:
        inline = getattr(part, "inline_data", None)
        data = getattr(inline, "data", None)
        if isinstance(data, (bytes, bytearray)) and data:
            return bytes(data)
    finish = getattr(cand, "finish_reason", "?")
    if parts:
        raise GeminiEmptyAudioError(f"Gemini ohne Audio-Daten (finish={finish})")
    raise GeminiEmptyAudioError(f"Gemini leer (finish={finish})")


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
                attempt + 1, retries + 1, safe_error(exc),
            )
            continue
        return _extract_audio(resp)
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

    Key per Header ``X-Goog-Api-Key`` (nie in der URL). Gibt das
    ``requests.Response``-Objekt zurueck (Statuscode prueft der Aufrufer).
    Nach erschoepften Versuchen wird die letzte Exception geworfen.
    """
    import requests

    poster = session or requests
    headers = {"X-Goog-Api-Key": api_key or ""}
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return poster.post(
                CLOUD_TTS_URL, json=payload, headers=headers, timeout=timeout_s,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            logger.warning(
                "Cloud-TTS Versuch %d/%d fehlgeschlagen: %s",
                attempt + 1, retries + 1, safe_error(exc),
            )
    assert last_exc is not None
    raise last_exc


def is_short_text(text: str) -> bool:
    """Kurz-String: ≤ SHORT_TEXT_MAX_CHARS Zeichen, ohne Satzzeichen/Leerraum."""
    t = text.strip()
    if not t or len(t) > SHORT_TEXT_MAX_CHARS:
        return False
    return not any(c.isspace() or unicodedata.category(c)[0] in "PZ" for c in t)


def _plausible_short_duration(pcm: bytes, text: str) -> bool:
    """Obergrenze der Sprechdauer eines Kurz-Strings (16-bit mono, 24 kHz)."""
    seconds = len(pcm) / (2 * SAMPLE_RATE)
    return seconds <= SHORT_PROMPT_BASE_S + SHORT_PROMPT_PER_CHAR_S * len(text)


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

    Erst der nackte Text. Kommt Gemini leer zurueck:
    - Kurz-String (``is_short_text``): nacheinander die Anweisungs-Prompts aus
      ``prompts``; Ergebnisse ueber der Kurz-String-Dauergrenze werden
      verworfen (Anweisung mitgesprochen).
    - laengerer Text: bisheriges Verhalten, ein Tutor-Prompt-Versuch.
    Timeouts/Netzfehler werden NICHT abgefangen (dafuer ist der Retry in
    ``synth_gemini_pcm`` zustaendig). Hoechstens ``GEMINI_MAX_CALLS_ROBUST``
    Aufrufe (bei Default-Prompts/-Retries).

    Raises:
        GeminiEmptyAudioError: alle Varianten leer — Aufrufer nimmt Chirp.
    """
    try:
        return synth_gemini_pcm(client, text, model=model, voice=voice, retries=retries)
    except GeminiEmptyAudioError as first_err:
        last_err = first_err

    if not is_short_text(text):
        try:
            return synth_gemini_pcm(
                client, GEMINI_TUTOR_PROMPT.format(text=text),
                model=model, voice=voice, retries=retries,
            )
        except GeminiEmptyAudioError as err:
            raise err from last_err

    for tpl in prompts:
        try:
            pcm = synth_gemini_pcm(
                client, tpl.format(text=text), model=model, voice=voice, retries=retries,
            )
        except GeminiEmptyAudioError as err:
            last_err = err
            continue
        if not _plausible_short_duration(pcm, text):
            # Anweisung vermutlich mitgesprochen → verwerfen, naechste Variante
            last_err = GeminiEmptyAudioError(
                f"Gemini-Prompt-Audio zu lang ({len(pcm) / (2 * SAMPLE_RATE):.1f} s)"
            )
            logger.warning("Gemini-TTS Prompt-Audio verworfen: %s", last_err)
            continue
        logger.info("Gemini-TTS Kurz-String via Prompt gerendert: %r", text[:30])
        return pcm
    raise last_err


def _synth_chirp_raw_pcm(
    api_key: str | None,
    text: str,
    *,
    voice_name: str = CHIRP_JA_VOICE,
    speaking_rate: float = CHIRP_SPEAKING_RATE,
    sample_rate: int = SAMPLE_RATE,
    session: Any = None,
) -> bytes:
    """Chirp-3-HD (LINEAR16) → rohes PCM. Fehlermeldungen ohne API-Key."""
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
    if resp.status_code != 200:
        # Bewusst kein raise_for_status(): dessen Meldung enthaelt die volle URL
        body = redact_secrets(getattr(resp, "text", "") or "")[:200]
        raise CloudTtsError(f"Chirp-TTS HTTP {resp.status_code}: {body}")
    audio_b64 = (resp.json() or {}).get("audioContent")
    if not audio_b64:
        raise CloudTtsError("Chirp-TTS ohne audioContent")
    # LINEAR16 kommt mit WAV-Header → auf rohes PCM reduzieren
    return wav_to_pcm(base64.b64decode(audio_b64))


def synth_chirp_wav(api_key: str | None, text: str, **kwargs: Any) -> bytes:
    """Chirp-3-HD-Fallback als WAV (LINEAR16, 24 kHz mono) statt MP3.

    Gleiches Format wie der Gemini-Pfad → gleicher ``.wav``-Dateiname/URL.

    Raises:
        CloudTtsError: Statuscode != 200 oder Antwort ohne ``audioContent``.
    """
    sample_rate = kwargs.get("sample_rate", SAMPLE_RATE)
    return pcm_to_wav(_synth_chirp_raw_pcm(api_key, text, **kwargs), sample_rate)


def synth_chirp_pcm(api_key: str | None, text: str, **kwargs: Any) -> bytes:
    """Wie ``synth_chirp_wav``, aber rohes PCM (zum Konkatenieren im Block-Player)."""
    return _synth_chirp_raw_pcm(api_key, text, **kwargs)

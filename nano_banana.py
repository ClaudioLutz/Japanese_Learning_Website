"""Gemeinsamer Nano-Banana-Helfer (Gemini 2.5 Flash Image, REST).

Eine einzige Definition des Bild-REST-Calls fuer BEIDE Aufrufpfade:
- app/ai_services.py (Flask-Kontext: Thumbnail/Vokabel/Kanji/Slideshow)
- scripts/generate_lesson_images.py (standalone: Seiten-/Slideshow-Szenen)

Bewusst nur stdlib (urllib/base64/json) und KEINE Flask-/App-Imports, damit
das Modul aus beiden Welten ohne Seiteneffekte importierbar ist.

User-Direktive: Lektionsbilder laufen ausschliesslich ueber Nano Banana,
NICHT ueber OpenAI/DALL-E. Listenpreis ~$0.039/Bild.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash-image"
_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)


class NanoBananaError(RuntimeError):
    """Endgueltiger Fehler bei der Nano-Banana-Bildgenerierung."""


def generate_nano_banana_image_bytes(
    prompt: str,
    api_key: str | None,
    *,
    aspect_ratio: str = "1:1",
    retries: int = 2,
    backoff: float = 5.0,
    timeout: float = 180.0,
) -> bytes:
    """Liefert PNG-Bytes von Nano Banana oder wirft ``NanoBananaError``.

    ``retries`` = Gesamtzahl Versuche bei **Netzwerk-/Timeout-Fehlern**
    (>=1). Ein Safety-Block (Antwort ohne Bilddaten) ist deterministisch und
    wird NICHT wiederholt — er wirft sofort ``NanoBananaError``.
    """
    if not api_key:
        raise NanoBananaError("kein API-Key (GOOGLE_AI_API_KEY/GEMINI_API_KEY)")

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        },
    }).encode()
    url = f"{_ENDPOINT}?key={api_key}"

    attempts = max(1, retries)
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, TimeoutError) as e:
            last_exc = e
            if attempt < attempts:
                time.sleep(backoff)
                continue
            raise NanoBananaError(
                f"Netzwerkfehler nach {attempt} Versuchen: {e}"
            ) from e

        parts = (
            data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        )
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        # Keine Bilddaten -> Safety-Block (deterministisch, kein Retry).
        raise NanoBananaError(
            f"keine Bilddaten (safety-block?): {json.dumps(data)[:200]}"
        )

    # unerreichbar (Schleife wirft oder returned), aber zur Sicherheit:
    raise NanoBananaError(str(last_exc) if last_exc else "unbekannter Fehler")

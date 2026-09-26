"""Audio-Metadaten serverseitig ermitteln, ohne die Datei auszuliefern.

Der Block-Player auf der Lektionsseite laedt sein Audio erst beim Play-Klick
(preload='none', siehe tests/integration/test_lesson_audio_lazy.py). Damit er
trotzdem vorab die Laenge anzeigen kann ("0:00 / 1:23" statt "0:00 / 0:00"),
liest der Server beim Rendern nur den WAV-Header (24 kHz PCM) und gibt die
Dauer als ``data-duration`` ins Markup.

Nur lokale Dateien unter ``UPLOAD_FOLDER``. MP3 wird nicht geparst; liegt aber
eine gleichnamige WAV daneben (Pipeline erzeugt beide), gilt deren Dauer.
Ergebnis pro (Pfad, mtime, Groesse) gecacht -> pro Request nur ein stat(),
der Header wird nur beim ersten Treffer bzw. nach einer Aenderung gelesen.
"""
from __future__ import annotations

import wave
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlparse

_URL_PREFIXES = ('/uploads/', '/static/uploads/')


def _local_path(url_or_path: str | None, upload_root: str | Path) -> Path | None:
    """Mappt eine Medien-URL bzw. einen DB-``file_path`` auf eine Datei unter upload_root."""
    if not url_or_path:
        return None
    raw = str(url_or_path).strip()
    if raw.startswith(('http://', 'https://', '//')):
        return None  # extern (z.B. GCS) -> kein lokaler Header
    rel = unquote(urlparse(raw).path)
    for prefix in _URL_PREFIXES:
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
            break
    else:
        if rel.startswith('/'):
            return None  # unbekannte Route, nicht raten
    root = Path(upload_root).resolve()
    full = (root / rel).resolve()
    if root != full and root not in full.parents:
        return None  # Path-Traversal
    return full


@lru_cache(maxsize=4096)
def _wav_seconds(path: str, mtime_ns: int, size: int) -> float | None:
    """Dauer einer WAV aus dem Header; Datengroesse als Plausibilitaets-Deckel."""
    try:
        with wave.open(path, 'rb') as w:
            rate = w.getframerate()
            frame_bytes = w.getnchannels() * w.getsampwidth()
            frames = w.getnframes()
    except (wave.Error, EOFError, OSError):
        return None
    if not rate or not frame_bytes:
        return None
    # Gestreamt geschriebene WAVs koennen einen ueberhohen/leeren Frame-Zaehler
    # tragen -> auf die tatsaechliche Dateigroesse deckeln.
    max_frames = max(0, size - 44) // frame_bytes
    if frames <= 0 or frames > max_frames:
        frames = max_frames
    seconds = frames / rate
    return round(seconds, 2) if seconds > 0 else None


def audio_duration_seconds(url_or_path: str | None, upload_root: str | Path) -> float | None:
    """Dauer in Sekunden oder None (Datei fehlt, extern, kein WAV lesbar)."""
    path = _local_path(url_or_path, upload_root)
    if path is None:
        return None
    candidates = [path]
    if path.suffix.lower() != '.wav':
        candidates = [path.with_suffix('.wav')]
    for cand in candidates:
        try:
            st = cand.stat()
        except OSError:
            continue
        return _wav_seconds(str(cand), st.st_mtime_ns, st.st_size)
    return None

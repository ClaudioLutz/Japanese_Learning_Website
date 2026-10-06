"""Sidecar-Manifest: welche TTS-Engine hat eine Audio-Datei erzeugt?

Seit 29.09.2026 schreiben Gemini und der Chirp-Fallback dieselbe
``<hash>.wav`` — an Dateiname/URL ist die Engine nicht mehr erkennbar. Das
Manifest ``_engines.json`` im jeweiligen Audio-Verzeichnis haelt sie fest
(``{"<hash>": "gemini" | "chirp"}``), ohne die URL zu aendern. Dateien ohne
Eintrag (Altbestand) gelten als ``unknown``.

Geschrieben wird atomar (tmp-Datei + ``os.replace``), damit ein Abbruch nie ein
halbes JSON hinterlaesst.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from app.services.tts_client import ENGINE_CHIRP, ENGINE_GEMINI, ENGINE_UNKNOWN

logger = logging.getLogger(__name__)

MANIFEST_NAME = "_engines.json"
KNOWN_ENGINES = (ENGINE_GEMINI, ENGINE_CHIRP)


def manifest_path(directory: Path) -> Path:
    return Path(directory) / MANIFEST_NAME


def load_manifest(directory: Path) -> dict[str, str]:
    """Liest das Manifest; fehlend/kaputt → leeres Dict (Warnung bei kaputt)."""
    path = manifest_path(directory)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Engine-Manifest %s unlesbar: %s", path, exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if v in KNOWN_ENGINES}


def save_manifest(directory: Path, manifest: dict[str, str]) -> None:
    """Schreibt das Manifest atomar (sortiert, stabile Diffs)."""
    path = manifest_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=0),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def record_engine(directory: Path, key: str, engine: str) -> dict[str, str]:
    """Traegt ``key → engine`` ein (frisch gelesen, atomar geschrieben)."""
    if engine not in KNOWN_ENGINES:
        raise ValueError(f"Unbekannte Engine: {engine!r}")
    manifest = load_manifest(directory)
    manifest[key] = engine
    save_manifest(directory, manifest)
    return manifest


def engine_for(manifest: dict[str, str], key: str) -> str:
    return manifest.get(key, ENGINE_UNKNOWN)

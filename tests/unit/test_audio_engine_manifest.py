"""app/services/audio_engine_manifest.py: Engine pro Audio-Datei (Befund 4)."""
import pytest

from app.services.audio_engine_manifest import (
    MANIFEST_NAME,
    engine_for,
    load_manifest,
    record_engine,
    save_manifest,
)


def test_leeres_verzeichnis(tmp_path):
    assert load_manifest(tmp_path) == {}
    assert engine_for({}, "abc") == "unknown"


def test_record_und_load(tmp_path):
    record_engine(tmp_path, "aaa", "gemini")
    record_engine(tmp_path, "bbb", "chirp")
    record_engine(tmp_path, "aaa", "chirp")
    assert load_manifest(tmp_path) == {"aaa": "chirp", "bbb": "chirp"}
    # atomar: keine tmp-Reste
    assert [p.name for p in tmp_path.iterdir()] == [MANIFEST_NAME]


def test_unbekannte_engine_abgelehnt(tmp_path):
    with pytest.raises(ValueError):
        record_engine(tmp_path, "aaa", "mp3")


def test_kaputtes_manifest_gilt_als_leer(tmp_path):
    (tmp_path / MANIFEST_NAME).write_text("{kaputt", encoding="utf-8")
    assert load_manifest(tmp_path) == {}


def test_fremde_werte_werden_ignoriert(tmp_path):
    save_manifest(tmp_path, {"a": "gemini", "b": "irgendwas"})
    assert load_manifest(tmp_path) == {"a": "gemini"}

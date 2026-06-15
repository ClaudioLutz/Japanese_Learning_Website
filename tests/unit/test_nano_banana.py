"""Smoke-Tests fuer den Nano-Banana-Bildpfad (Migration 2026-06-15).

Deckt den zentralen REST-Helfer (nano_banana) inkl. Retry/Safety-Logik ab
sowie die ai_services-Wrapper. Kein echter Netzwerk-Call, kein API-Key noetig.
"""
import base64
import json
import urllib.error

import pytest

import nano_banana
from nano_banana import NanoBananaError, generate_nano_banana_image_bytes


class _FakeResp:
    """Minimaler Context-Manager, der json.load(resp) bedient."""

    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, *a):
        return self._b


def _image_payload(raw: bytes):
    return {
        "candidates": [
            {"content": {"parts": [
                {"inlineData": {"data": base64.b64encode(raw).decode()}}
            ]}}
        ]
    }


def test_no_api_key_raises():
    with pytest.raises(NanoBananaError):
        generate_nano_banana_image_bytes("prompt", None)


def test_success_returns_decoded_bytes(monkeypatch):
    raw = b"\x89PNG-fake-bytes"
    monkeypatch.setattr(
        nano_banana.urllib.request, "urlopen",
        lambda req, timeout=0: _FakeResp(_image_payload(raw)),
    )
    assert generate_nano_banana_image_bytes("prompt", "key") == raw


def test_safety_block_raises_without_retry(monkeypatch):
    calls = {"n": 0}

    def no_image(req, timeout=0):
        calls["n"] += 1
        return _FakeResp({"candidates": [{"content": {"parts": []}}]})

    monkeypatch.setattr(nano_banana.urllib.request, "urlopen", no_image)
    with pytest.raises(NanoBananaError, match="safety"):
        generate_nano_banana_image_bytes("prompt", "key", retries=2, backoff=0)
    # Safety-Block ist deterministisch -> genau EIN Versuch, kein Retry.
    assert calls["n"] == 1


def test_retry_on_network_error_then_success(monkeypatch):
    raw = b"img"
    calls = {"n": 0}

    def flaky(req, timeout=0):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.URLError("transient")
        return _FakeResp(_image_payload(raw))

    monkeypatch.setattr(nano_banana.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(nano_banana.time, "sleep", lambda *_a: None)
    assert generate_nano_banana_image_bytes("prompt", "key", retries=2, backoff=0) == raw
    assert calls["n"] == 2


def test_aiservice_nb_methods_return_error_without_key(app):
    """Die ai_services-Wrapper liefern bei fehlendem Key sauber {'error': ...}."""
    from app.ai_services import AILessonContentGenerator

    gen = AILessonContentGenerator.__new__(AILessonContentGenerator)  # __init__ umgehen
    gen.gemini_api_key = None
    with app.app_context():
        assert "error" in gen._nano_banana_image("p")
        assert "error" in gen.generate_single_image_nb("p", aspect_ratio="16:9")
        assert "error" in gen.generate_vocabulary_image_nb("水", "Wasser")

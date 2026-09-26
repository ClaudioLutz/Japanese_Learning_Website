"""Tests fuer app/services/tts_client.py (Timeout + Retry der TTS-Aufrufe)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services import tts_client
from app.services.tts_client import (
    GeminiEmptyAudioError,
    make_gemini_client,
    post_cloud_tts,
    synth_gemini_pcm,
)


def _audio_response(data: bytes = b"PCM"):
    part = SimpleNamespace(inline_data=SimpleNamespace(data=data))
    cand = SimpleNamespace(content=SimpleNamespace(parts=[part]), finish_reason="STOP")
    return SimpleNamespace(candidates=[cand])


def _empty_response():
    cand = SimpleNamespace(content=None, finish_reason="OTHER")
    return SimpleNamespace(candidates=[cand])


class TestMakeGeminiClient:
    def test_setzt_timeout_in_millisekunden(self):
        with patch("google.genai.Client") as client_cls:
            make_gemini_client("key", timeout_s=30)
        kwargs = client_cls.call_args.kwargs
        assert kwargs["api_key"] == "key"
        assert kwargs["http_options"].timeout == 30_000

    def test_default_timeout_ist_120s(self):
        assert tts_client.TTS_TIMEOUT_S == 120
        with patch("google.genai.Client") as client_cls:
            make_gemini_client("key")
        assert client_cls.call_args.kwargs["http_options"].timeout == 120_000


class TestSynthGeminiPcm:
    def test_erfolg_beim_ersten_versuch(self):
        client = MagicMock()
        client.models.generate_content.return_value = _audio_response(b"abc")
        assert synth_gemini_pcm(client, "こんにちは") == b"abc"
        assert client.models.generate_content.call_count == 1

    def test_ein_retry_nach_timeout(self):
        client = MagicMock()
        client.models.generate_content.side_effect = [
            TimeoutError("read timeout"), _audio_response(b"ok"),
        ]
        assert synth_gemini_pcm(client, "テスト") == b"ok"
        assert client.models.generate_content.call_count == 2

    def test_nach_zwei_timeouts_wird_geworfen(self):
        client = MagicMock()
        client.models.generate_content.side_effect = TimeoutError("hang")
        with pytest.raises(TimeoutError):
            synth_gemini_pcm(client, "テスト")
        assert client.models.generate_content.call_count == 2  # 1 + 1 Retry

    def test_retries_null_ohne_wiederholung(self):
        client = MagicMock()
        client.models.generate_content.side_effect = TimeoutError("hang")
        with pytest.raises(TimeoutError):
            synth_gemini_pcm(client, "テスト", retries=0)
        assert client.models.generate_content.call_count == 1

    def test_leere_antwort_ohne_retry(self):
        client = MagicMock()
        client.models.generate_content.return_value = _empty_response()
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm(client, "あ")
        assert client.models.generate_content.call_count == 1


class TestPostCloudTts:
    def test_timeout_wird_uebergeben(self):
        session = MagicMock()
        session.post.return_value = SimpleNamespace(status_code=200)
        post_cloud_tts("k", {"x": 1}, session=session, timeout_s=12)
        assert session.post.call_args.kwargs["timeout"] == 12

    def test_ein_retry_bei_timeout(self):
        session = MagicMock()
        ok = SimpleNamespace(status_code=200)
        session.post.side_effect = [requests.Timeout("t"), ok]
        assert post_cloud_tts("k", {}, session=session) is ok
        assert session.post.call_count == 2

    def test_nach_retry_exception(self):
        session = MagicMock()
        session.post.side_effect = requests.ConnectionError("down")
        with pytest.raises(requests.ConnectionError):
            post_cloud_tts("k", {}, session=session)
        assert session.post.call_count == 2


class TestSynthesizeGeminiRoute:
    """Web-Pfad /api/tts: kurzes Timeout, kein Retry (Chirp-Fallback im Aufrufer)."""

    def test_route_nutzt_30s_timeout_ohne_retry(self, app):
        from app import routes

        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = TimeoutError("hang")
        with app.app_context(), patch(
            "app.services.tts_client.make_gemini_client", return_value=fake_client
        ) as factory:
            with pytest.raises(TimeoutError):
                routes._synthesize_gemini("こんにちは")
        assert factory.call_args.kwargs["timeout_s"] == 30
        assert fake_client.models.generate_content.call_count == 1

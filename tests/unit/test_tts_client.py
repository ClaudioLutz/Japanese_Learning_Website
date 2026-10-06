"""Tests fuer app/services/tts_client.py (Timeout + Retry, Kurz-Strings, Chirp-WAV)."""
import base64
import io
import wave
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services import tts_client
from app.services.tts_client import (
    GeminiEmptyAudioError,
    make_gemini_client,
    pcm_to_wav,
    post_cloud_tts,
    synth_chirp_pcm,
    synth_chirp_wav,
    synth_gemini_pcm,
    synth_gemini_pcm_robust,
    wav_to_pcm,
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

    def test_route_ohne_kurz_string_prompts(self, app):
        # Web-Pfad: leere Antwort → sofort Fehler (Chirp im Aufrufer), keine
        # zusaetzlichen Prompt-Versuche waehrend der Nutzer wartet.
        from app import routes

        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = _empty_response()
        with app.app_context(), patch(
            "app.services.tts_client.make_gemini_client", return_value=fake_client
        ):
            with pytest.raises(GeminiEmptyAudioError):
                routes._synthesize_gemini("ちち")
        assert fake_client.models.generate_content.call_count == 1

    def test_batch_nutzt_kurz_string_prompts(self, app):
        from app import routes

        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = [
            _empty_response(), _audio_response(_pcm(0.5)),
        ]
        with app.app_context(), patch(
            "app.services.tts_client.make_gemini_client", return_value=fake_client
        ) as factory:
            wav = routes._synthesize_gemini("ちち", batch=True)
        assert wav[:4] == b"RIFF"
        assert "timeout_s" not in factory.call_args.kwargs  # Batch-Default 120 s
        assert fake_client.models.generate_content.call_count == 2


# ---------------------------------------------------------------------------
# Kurz-String-Behandlung + Chirp-WAV-Fallback (29.09.2026)
# ---------------------------------------------------------------------------
def _pcm(seconds: float) -> bytes:
    return b"\x00\x00" * int(tts_client.SAMPLE_RATE * seconds)


class TestSynthGeminiPcmRobust:
    def test_nackter_text_reicht(self):
        client = MagicMock()
        client.models.generate_content.return_value = _audio_response(_pcm(0.8))
        assert synth_gemini_pcm_robust(client, "ちち") == _pcm(0.8)
        assert client.models.generate_content.call_count == 1
        assert client.models.generate_content.call_args.kwargs["contents"] == "ちち"

    def test_leer_dann_prompt_variante(self):
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _empty_response(), _audio_response(_pcm(0.7)),
        ]
        assert synth_gemini_pcm_robust(client, "はは") == _pcm(0.7)
        calls = client.models.generate_content.call_args_list
        assert calls[0].kwargs["contents"] == "はは"
        expected = tts_client.GEMINI_SHORT_TEXT_PROMPTS[0].format(text="はは")
        assert calls[1].kwargs["contents"] == expected
        assert expected.endswith("はは")

    def test_prompts_ohne_pause_markup(self):
        # [short pause]-Markup fuehrt bei Gemini zu Truncation (CLAUDE.md)
        assert tts_client.GEMINI_SHORT_TEXT_PROMPTS
        for tpl in tts_client.GEMINI_SHORT_TEXT_PROMPTS:
            assert "[" not in tpl and "{text}" in tpl

    def test_alle_varianten_leer_wirft(self):
        client = MagicMock()
        client.models.generate_content.return_value = _empty_response()
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm_robust(client, "ひゃく")
        assert client.models.generate_content.call_count == (
            1 + len(tts_client.GEMINI_SHORT_TEXT_PROMPTS)
        )

    def test_zu_langes_prompt_audio_wird_verworfen(self):
        # 8 s fuer "ちち" → Anweisung wurde mitgesprochen → naechste Variante
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _empty_response(), _audio_response(_pcm(8.0)), _audio_response(_pcm(0.9)),
        ]
        assert synth_gemini_pcm_robust(client, "ちち") == _pcm(0.9)
        assert client.models.generate_content.call_count == 3

    def test_400_text_statt_audio_gilt_als_leer_ohne_retry(self):
        client = MagicMock()
        client.models.generate_content.side_effect = [
            RuntimeError("400 INVALID_ARGUMENT. Model tried to generate text, but ..."),
            _audio_response(_pcm(0.6)),
        ]
        assert synth_gemini_pcm_robust(client, "ねこ") == _pcm(0.6)
        # kein Netz-Retry mit demselben Text, sondern direkt die Prompt-Variante
        assert client.models.generate_content.call_count == 2
        second = client.models.generate_content.call_args_list[1].kwargs["contents"]
        assert second != "ねこ"

    def test_400_text_statt_audio_in_synth_gemini_pcm(self):
        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError(
            "Model tried to generate text, but it should only be used for TTS"
        )
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm(client, "いち")
        assert client.models.generate_content.call_count == 1

    def test_timeout_wird_nicht_als_leer_behandelt(self):
        client = MagicMock()
        client.models.generate_content.side_effect = TimeoutError("hang")
        with pytest.raises(TimeoutError):
            synth_gemini_pcm_robust(client, "ちち")
        assert client.models.generate_content.call_count == 2  # 1 + 1 Retry


def _chirp_response(audio: bytes, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"audioContent": base64.b64encode(audio).decode()}
    resp.text = ""
    return resp


class TestChirpWav:
    def test_liefert_wav_24khz_und_fordert_linear16_an(self):
        session = MagicMock()
        # Cloud-TTS LINEAR16 kommt bereits mit RIFF-Header
        session.post.return_value = _chirp_response(pcm_to_wav(_pcm(0.5)))
        wav = synth_chirp_wav("k", "ちち", session=session)
        with wave.open(io.BytesIO(wav)) as wf:
            assert wf.getframerate() == 24000
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getnframes() == int(24000 * 0.5)
        payload = session.post.call_args.kwargs["json"]
        assert payload["audioConfig"]["audioEncoding"] == "LINEAR16"
        assert payload["audioConfig"]["sampleRateHertz"] == 24000
        assert payload["voice"] == {"languageCode": "ja-JP", "name": "ja-JP-Chirp3-HD-Leda"}
        assert payload["input"] == {"text": "ちち"}

    def test_rohes_pcm_wird_als_wav_verpackt(self):
        session = MagicMock()
        session.post.return_value = _chirp_response(_pcm(0.25))
        wav = synth_chirp_wav("k", "はは", session=session)
        assert wav[:4] == b"RIFF"
        assert wav_to_pcm(wav) == _pcm(0.25)

    def test_pcm_variante_ohne_header(self):
        session = MagicMock()
        session.post.return_value = _chirp_response(pcm_to_wav(_pcm(0.3)))
        pcm = synth_chirp_pcm("k", "ひゃく", session=session)
        assert pcm[:4] != b"RIFF"
        assert pcm == _pcm(0.3)

    def test_http_fehler_wirft(self):
        session = MagicMock()
        session.post.return_value = _chirp_response(b"", status=403)
        with pytest.raises(tts_client.CloudTtsError):
            synth_chirp_wav("k", "ちち", session=session)

    def test_leerer_audio_content_wirft(self):
        session = MagicMock()
        resp = _chirp_response(b"")
        resp.json.return_value = {}
        session.post.return_value = resp
        with pytest.raises(tts_client.CloudTtsError):
            synth_chirp_wav("k", "ちち", session=session)


# ---------------------------------------------------------------------------
# Review-Befunde 06.10.2026
# ---------------------------------------------------------------------------
FAKE_KEY = "AIzaSyFAKE_testkey_0123456789abcdefghijk"


class TestKeyNieInMeldungen:
    """Befund 1: API-Key per Header, nie in URL/Fehlermeldungen."""

    def test_key_als_header_nicht_in_url(self):
        session = MagicMock()
        session.post.return_value = SimpleNamespace(status_code=200)
        post_cloud_tts(FAKE_KEY, {"x": 1}, session=session)
        args, kwargs = session.post.call_args
        url = args[0]
        assert "key=" not in url and FAKE_KEY not in url
        assert kwargs["headers"]["X-Goog-Api-Key"] == FAKE_KEY

    def test_redact_secrets(self):
        msg = (f"403 Client Error: Forbidden for url: "
               f"https://texttospeech.googleapis.com/v1/text:synthesize?key={FAKE_KEY}&x=1")
        clean = tts_client.redact_secrets(msg)
        assert FAKE_KEY not in clean
        assert "key=REDACTED&x=1" in clean
        assert FAKE_KEY not in tts_client.redact_secrets(f"api key {FAKE_KEY} invalid")

    def test_safe_error_auf_exception(self):
        exc = requests.HTTPError(f"Forbidden for url: https://x/y?key={FAKE_KEY}")
        assert FAKE_KEY not in tts_client.safe_error(exc)
        assert "HTTPError" in tts_client.safe_error(exc)

    def test_chirp_http_fehler_ohne_key(self):
        session = MagicMock()
        resp = MagicMock(status_code=403)
        resp.text = f'{{"error": "API key not valid", "url": "?key={FAKE_KEY}"}}'
        session.post.return_value = resp
        with pytest.raises(tts_client.CloudTtsError) as exc_info:
            synth_chirp_wav(FAKE_KEY, "ちち", session=session)
        assert FAKE_KEY not in str(exc_info.value)
        assert "403" in str(exc_info.value)

    def test_netzfehler_meldung_ohne_key(self, caplog):
        session = MagicMock()
        session.post.side_effect = requests.ConnectionError(
            f"HTTPSConnectionPool: Max retries exceeded with url: /v1/text:synthesize?key={FAKE_KEY}"
        )
        with caplog.at_level("WARNING"), pytest.raises(requests.ConnectionError):
            synth_chirp_wav(FAKE_KEY, "ちち", session=session)
        assert FAKE_KEY not in caplog.text


class TestShortTextLogik:
    """Befund 3: Anweisungs-Prompts nur fuer Kurz-Strings."""

    @pytest.mark.parametrize("text,erwartet", [
        ("ちち", True),
        ("ひゃく", True),
        ("ラーメン", True),
        ("あいうえおかきく", True),           # 8 Zeichen
        ("あいうえおかきくけ", False),        # 9 Zeichen
        ("ちち。", False),
        ("さ、し、す", False),
        ("ちち はは", False),
        ("", False),
    ])
    def test_is_short_text(self, text, erwartet):
        assert tts_client.is_short_text(text) is erwartet

    def test_langer_text_ohne_anweisungs_prompts(self):
        satz = "わたしはがくせいです。"
        client = MagicMock()
        client.models.generate_content.return_value = _empty_response()
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm_robust(client, satz)
        contents = [c.kwargs["contents"] for c in client.models.generate_content.call_args_list]
        assert contents == [satz, tts_client.GEMINI_TUTOR_PROMPT.format(text=satz)]

    def test_langer_text_tutor_prompt_erfolg(self):
        satz = "きょうはいいてんきですね。"
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _empty_response(), _audio_response(_pcm(3.0)),
        ]
        assert synth_gemini_pcm_robust(client, satz) == _pcm(3.0)

    def test_kurzstring_strengere_dauergrenze(self):
        # 2 Zeichen: Grenze 1.2 + 2*0.3 = 1.8 s → 2.5 s wird verworfen
        client = MagicMock()
        client.models.generate_content.side_effect = [
            _empty_response(), _audio_response(_pcm(2.5)), _audio_response(_pcm(1.0)),
        ]
        assert synth_gemini_pcm_robust(client, "ちち") == _pcm(1.0)
        assert client.models.generate_content.call_count == 3

    def test_max_calls_konstante(self):
        assert tts_client.GEMINI_MAX_CALLS_ROBUST == 8
        client = MagicMock()
        client.models.generate_content.side_effect = TimeoutError("hang")
        with pytest.raises(TimeoutError):
            synth_gemini_pcm_robust(client, "ちち")
        assert client.models.generate_content.call_count <= tts_client.GEMINI_MAX_CALLS_ROBUST
        client = MagicMock()
        client.models.generate_content.return_value = _empty_response()
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm_robust(client, "ちち")
        assert client.models.generate_content.call_count <= tts_client.GEMINI_MAX_CALLS_ROBUST


class TestExtractAudio:
    """Befund 6: Text-Part / fehlende Daten → GeminiEmptyAudioError."""

    def _resp(self, *parts):
        cand = SimpleNamespace(content=SimpleNamespace(parts=list(parts)), finish_reason="STOP")
        return SimpleNamespace(candidates=[cand])

    def test_text_part_statt_audio(self):
        client = MagicMock()
        client.models.generate_content.return_value = self._resp(
            SimpleNamespace(text="Hallo", inline_data=None)
        )
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm(client, "ちち")

    def test_part_ohne_inline_data_attribut(self):
        client = MagicMock()
        client.models.generate_content.return_value = self._resp(SimpleNamespace(text="x"))
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm(client, "ちち")

    def test_leere_daten(self):
        client = MagicMock()
        client.models.generate_content.return_value = self._resp(
            SimpleNamespace(inline_data=SimpleNamespace(data=b""))
        )
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm(client, "ちち")

    def test_audio_im_zweiten_part(self):
        client = MagicMock()
        client.models.generate_content.return_value = self._resp(
            SimpleNamespace(text="note", inline_data=None),
            SimpleNamespace(inline_data=SimpleNamespace(data=b"PCM")),
        )
        assert synth_gemini_pcm(client, "ちち") == b"PCM"

    def test_keine_candidates(self):
        client = MagicMock()
        client.models.generate_content.return_value = SimpleNamespace(candidates=None)
        with pytest.raises(GeminiEmptyAudioError):
            synth_gemini_pcm(client, "ちち")
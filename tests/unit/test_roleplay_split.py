"""Unit-Tests: zweigeteilter Rollenspiel-Zug (Schemata, Prompts, Validierung,
Zeilen-Extraktion aus dem Stream, Provider-Stream der Bridge). Modell gemockt."""
import json

import pytest

from app.services import roleplay_service as svc

SUGG = [{"jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte."}] * 3


class TestSchemas:
    def test_line_schema_minimal(self):
        assert svc.LINE_SCHEMA["required"] == ["bot_line_jp", "done"]
        assert set(svc.LINE_SCHEMA["properties"]) == {"bot_line_jp", "done"}
        assert svc.LINE_SCHEMA["additionalProperties"] is False

    def test_details_schema_without_line(self):
        props = set(svc.DETAILS_SCHEMA["properties"])
        assert props == {"reading_kana", "de", "suggestions", "hint_de", "correction"}
        assert "bot_line_jp" not in props and "done" not in props   # Zeile ist unveraenderbar
        assert svc.DETAILS_SCHEMA["additionalProperties"] is False


class TestPrompts:
    def test_line_suffix(self):
        s = svc.line_suffix("STATUS: Zug 2 von höchstens 8 des Lernenden.")
        assert s.startswith("STATUS: Zug 2")
        assert "NUR deine nächste Zeile" in s and "bot_line_jp" in s

    def test_details_suffix(self):
        running = svc.details_suffix("STATUS: x", done=False)
        assert svc.DETAILS_USER_TEXT in running
        assert "ändere deine Zeile nicht" in running
        assert "genau drei suggestions" in running
        finished = svc.details_suffix("STATUS: x", done=True)
        assert "suggestions=[]" in finished and "correction" in finished

    def test_details_messages(self):
        base = [{"role": "user", "content": "（はじめましょう。）"}, {"role": "user", "content": "はい"}]
        out = svc.details_messages(base, "いらっしゃいませ。")
        assert out[:2] == base
        assert out[2] == {"role": "assistant", "content": "いらっしゃいませ。"}
        assert out[3] == {"role": "user", "content": svc.DETAILS_USER_TEXT}
        assert len(base) == 2   # Eingabe unveraendert


class TestValidation:
    def test_line_ok_ignores_extra(self):
        assert svc.validate_line_payload({"bot_line_jp": " はい。 ", "done": False, "de": "x"}) == \
            {"bot_line_jp": "はい。", "done": False}

    @pytest.mark.parametrize("data", [None, {}, {"bot_line_jp": "", "done": False},
                                      {"bot_line_jp": "はい", "done": "nein"}])
    def test_line_invalid(self, data):
        with pytest.raises(svc.SchemaError):
            svc.validate_line_payload(data)

    def test_merge_keeps_server_line_and_restores_katakana(self):
        out = svc.merge_details("コーヒーを どうぞ。", {
            "bot_line_jp": "ぜんぜん ちがう", "done": True,
            "reading_kana": "こーひーを どうぞ。", "de": "Bitte, Kaffee.",
            "suggestions": SUGG, "hint_de": "Danke sagen.", "correction": []}, done=False)
        assert out["bot_line_jp"] == "コーヒーを どうぞ。"
        assert out["done"] is False
        assert out["reading_kana"] == "コーヒーを どうぞ。"
        assert out["suggestions"] == SUGG

    def test_merge_needs_suggestions_while_running(self):
        with pytest.raises(svc.SchemaError):
            svc.merge_details("はい。", {"reading_kana": "", "de": "", "suggestions": [], "hint_de": "",
                                         "correction": []}, done=False)

    def test_merge_done_keeps_correction(self):
        corr = [{"original": "a", "better": "b", "explanation_de": "c"}]
        out = svc.merge_details("さようなら。", {"reading_kana": "さようなら。", "de": "Tschüss.",
                                                  "suggestions": SUGG, "hint_de": "", "correction": corr},
                                done=True)
        assert out["done"] is True and out["suggestions"] == [] and out["correction"] == corr

    def test_empty_details(self):
        assert svc.empty_details({"bot_line_jp": "はい。", "done": False}) == {
            "bot_line_jp": "はい。", "reading_kana": "", "de": "", "suggestions": [], "hint_de": "",
            "done": False, "correction": []}


class TestLineExtractor:
    def feed_all(self, parts):
        ex = svc.LineExtractor()
        return [ex.feed(p) for p in parts], ex

    def test_chunks(self):
        out, ex = self.feed_all(['{"bot_line_jp": "わ', 'かりました。', 'こうちゃですね。', '", "done": false}'])
        assert out == ["わ", "かりました。", "こうちゃですね。", ""]
        assert ex.finished

    def test_key_split_across_chunks_and_whitespace(self):
        out, _ = self.feed_all(['{"bot_li', 'ne_jp"', ' :  "は', 'い"'])
        assert "".join(out) == "はい"

    def test_escapes_across_chunks(self):
        out, _ = self.feed_all(['{"bot_line_jp": "「\\', '"A\\"」\\u30', 'b3\\n"'])
        assert "".join(out) == '「"A"」コ\n'

    def test_other_field_first(self):
        out, _ = self.feed_all(['{"done": false, "de": "\\"bot_line_jp\\"", ', '"bot_line_jp": "はい"}'])
        assert "".join(out) == "はい"

    def test_nothing_after_close(self):
        ex = svc.LineExtractor()
        ex.feed('{"bot_line_jp": "はい"')
        assert ex.feed(', "x": "もっと"}') == ""


class RecordingProvider(svc.RoleplayProvider):
    name = "rec"

    def __init__(self, data, stream_exc=None):
        self.data = data
        self.stream_exc = stream_exc
        self.calls = []

    def complete(self, system, messages, schema, *, system_suffix="", max_tokens=0, fast=False):
        self.calls.append({"mode": "complete", "schema": schema, "fast": fast, "suffix": system_suffix,
                           "messages": messages, "max_tokens": max_tokens})
        return svc.ProviderResult(data=self.data, usage=svc.Usage(tokens_in=5, tokens_out=3))

    def stream(self, system, messages, schema, *, system_suffix="", max_tokens=0, fast=False):
        self.calls.append({"mode": "stream", "schema": schema, "fast": fast})
        if self.stream_exc:
            raise self.stream_exc
        text = json.dumps(self.data, ensure_ascii=False)
        for i in range(0, len(text), 3):
            yield text[i:i + 3]
        return svc.ProviderResult(data=self.data, usage=svc.Usage(tokens_in=5, tokens_out=3))


class TestCalls:
    def test_call_line_small_schema_fast(self):
        prov = RecordingProvider({"bot_line_jp": "はい、どうぞ。", "done": False})
        result = svc.drain(svc.call_line("SYS", "STATUS: x", [{"role": "user", "content": "a"}], provider=prov))
        assert result.data == {"bot_line_jp": "はい、どうぞ。", "done": False}
        call = prov.calls[0]
        assert call["schema"] is svc.LINE_SCHEMA and call["fast"] is True
        assert call["max_tokens"] == svc.MAX_TOKENS_LINE
        assert "NUR deine nächste Zeile" in call["suffix"]

    def test_call_line_stream_yields_line(self):
        prov = RecordingProvider({"bot_line_jp": "はい、どうぞ。", "done": False})
        gen = svc.call_line("SYS", "STATUS", [{"role": "user", "content": "a"}], provider=prov, stream=True)
        pieces = []
        while True:
            try:
                pieces.append(next(gen))
            except StopIteration as stop:
                result = stop.value
                break
        assert "".join(pieces) == "はい、どうぞ。" and len(pieces) > 1
        assert result.data["bot_line_jp"] == "はい、どうぞ。"
        assert prov.calls[0]["mode"] == "stream" and prov.calls[0]["fast"] is True

    def test_stream_failure_falls_back_once(self):
        prov = RecordingProvider({"bot_line_jp": "はい。", "done": False},
                                 stream_exc=svc.ProviderError("bridge_stream_broken", retryable=True))
        result = svc.drain(svc.call_line("SYS", "S", [{"role": "user", "content": "a"}], provider=prov, stream=True))
        assert result.data["bot_line_jp"] == "はい。"
        assert [c["mode"] for c in prov.calls] == ["stream", "complete"]

    def test_stream_busy_no_fallback(self):
        prov = RecordingProvider({"bot_line_jp": "はい。", "done": False},
                                 stream_exc=svc.ProviderError("bridge_busy", busy=True))
        with pytest.raises(svc.UpstreamError):
            svc.drain(svc.call_line("SYS", "S", [{"role": "user", "content": "a"}], provider=prov, stream=True))
        assert len(prov.calls) == 1

    def test_call_details(self):
        prov = RecordingProvider({"reading_kana": "はい。", "de": "Ja.", "suggestions": SUGG, "hint_de": "h",
                                  "correction": []})
        result = svc.call_details("SYS", "STATUS", [{"role": "user", "content": "a"}], "はい。", provider=prov)
        assert result.data["bot_line_jp"] == "はい。" and result.data["suggestions"] == SUGG
        call = prov.calls[0]
        assert call["schema"] is svc.DETAILS_SCHEMA and call["fast"] is False
        assert call["messages"][-2:] == [{"role": "assistant", "content": "はい。"},
                                         {"role": "user", "content": svc.DETAILS_USER_TEXT}]

    def test_base_stream_uses_complete(self):
        class Plain(svc.RoleplayProvider):
            def complete(self, system, messages, schema, *, system_suffix="", max_tokens=0, fast=False):
                return svc.ProviderResult(data={"bot_line_jp": "やあ", "done": True})
        gen = Plain().stream("s", [], svc.LINE_SCHEMA, fast=True)
        chunk = next(gen)
        assert json.loads(chunk)["bot_line_jp"] == "やあ"


class FakeResp:
    def __init__(self, status=200, lines=None):
        self.status_code = status
        self._lines = lines or []
        self.closed = False

    def iter_lines(self, decode_unicode=True):
        yield from self._lines

    def close(self):
        self.closed = True


class FakeHttp:
    def __init__(self, resp):
        self.resp = resp
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.resp


def sse(event, data):
    return [f"event: {event}", f"data: {json.dumps(data, ensure_ascii=False)}", ""]


class TestBridgeProviderStream:
    def run(self, resp, fast=True):
        http = FakeHttp(resp)
        prov = svc.ClaudeCliBridgeProvider("http://bridge", "tok", http=http)
        gen = prov.stream("SYS", [{"role": "user", "content": "a"}], svc.LINE_SCHEMA, system_suffix="S", fast=fast)
        out = []
        while True:
            try:
                out.append(next(gen))
            except StopIteration as stop:
                return out, stop.value, http

    def test_deltas_and_result(self):
        lines = (sse("delta", {"partial_json": '{"bot_line_jp": "は'}) + sse("delta", {"partial_json": 'い"}'})
                 + sse("result", {"data": {"bot_line_jp": "はい", "done": False},
                                  "usage": {"input_tokens": 10, "output_tokens": 4}}))
        resp = FakeResp(lines=lines)
        out, result, http = self.run(resp)
        assert out == ['{"bot_line_jp": "は', 'い"}']
        assert result.data == {"bot_line_jp": "はい", "done": False} and result.usage.cost_usd == 0.0
        url, kwargs = http.calls[0]
        assert url == "http://bridge/complete_stream" and kwargs["stream"] is True
        assert kwargs["json"]["thinking"] is False and kwargs["json"]["system"] == "SYS\n\nS"
        assert resp.closed

    def test_no_thinking_flag_without_fast(self):
        lines = sse("result", {"data": {"bot_line_jp": "はい", "done": False}, "usage": {}})
        _, _, http = self.run(FakeResp(lines=lines), fast=False)
        assert "thinking" not in http.calls[0][1]["json"]

    def test_error_event(self):
        with pytest.raises(svc.ProviderError) as exc:
            self.run(FakeResp(lines=sse("error", {"error": "cli_timeout", "status": 504})))
        assert exc.value.reason == "bridge_cli_timeout" and not exc.value.retryable

    def test_incomplete_stream(self):
        with pytest.raises(svc.ProviderError) as exc:
            self.run(FakeResp(lines=sse("delta", {"partial_json": "{"})))
        assert exc.value.reason == "bridge_stream_incomplete"

    @pytest.mark.parametrize("status,busy", [(429, True), (502, False)])
    def test_http_errors(self, status, busy):
        with pytest.raises(svc.ProviderError) as exc:
            self.run(FakeResp(status=status))
        assert exc.value.busy is busy

    def test_complete_fast_flag(self):
        class R:
            status_code = 200

            def json(self):
                return {"data": {"bot_line_jp": "x", "done": False}, "usage": {}}
        http = FakeHttp(R())
        prov = svc.ClaudeCliBridgeProvider("http://bridge", "tok", http=http)
        prov.complete("SYS", [], svc.LINE_SCHEMA, fast=True)
        assert http.calls[0][1]["json"]["thinking"] is False
        prov.complete("SYS", [], svc.LINE_SCHEMA)
        assert "thinking" not in http.calls[1][1]["json"]


class TestSplitFlag:
    def test_default_off_in_tests_on_when_set(self, app, monkeypatch):
        with app.app_context():
            assert svc.split_enabled() is False
            monkeypatch.setitem(app.config, "ROLEPLAY_SPLIT_TURN", "1")
            assert svc.split_enabled() is True
            monkeypatch.setitem(app.config, "ROLEPLAY_SPLIT_TURN", "0")
            assert svc.split_enabled() is False

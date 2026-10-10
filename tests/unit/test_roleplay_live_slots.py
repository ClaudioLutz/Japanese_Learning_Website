"""Rollenspiel: begrenzte Live-Aufrufe pro Prozess (Schutz der Gunicorn-Threads)."""
import pytest

from app.services import roleplay_service as svc


@pytest.fixture
def one_slot(app):
    prev = app.config.get("ROLEPLAY_MAX_LIVE_CALLS")
    app.config["ROLEPLAY_MAX_LIVE_CALLS"] = 1
    with app.app_context():
        yield
    if prev is None:
        app.config.pop("ROLEPLAY_MAX_LIVE_CALLS", None)
    else:
        app.config["ROLEPLAY_MAX_LIVE_CALLS"] = prev


class FakeResp:
    status_code = 200

    def json(self):
        return {"data": {"ok": True}, "usage": {}}


class FakeHttp:
    def __init__(self):
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return FakeResp()


def test_zweiter_live_aufruf_ist_sofort_beschaeftigt(one_slot):
    with svc.live_call_slot("high"):
        with pytest.raises(svc.ProviderError) as exc:
            with svc.live_call_slot("high"):
                pass
        assert exc.value.busy is True
        # Hintergrund-Aufrufe zaehlen nicht mit
        with svc.live_call_slot("low"):
            pass
    # nach dem Ende ist der Platz wieder frei
    with svc.live_call_slot("high"):
        pass


def test_platz_wird_auch_bei_fehler_frei(one_slot):
    with pytest.raises(RuntimeError):
        with svc.live_call_slot("high"):
            raise RuntimeError("boom")
    with svc.live_call_slot("high"):
        pass


def test_bridge_meldet_beschaeftigt_ohne_http_aufruf(one_slot):
    http = FakeHttp()
    provider = svc.ClaudeCliBridgeProvider("http://bridge", "token", http=http)
    with svc.live_call_slot("high"):
        with pytest.raises(svc.UpstreamError) as exc:
            svc._complete_with_retry(provider, "sys", [], {}, lambda d: d,
                                     busy_message="beschäftigt", fail_message="kaputt")
    assert exc.value.message == "beschäftigt"
    assert http.calls == 0
    # frei: normaler Aufruf geht durch
    data, _usage = svc._complete_with_retry(provider, "sys", [], {}, lambda d: d,
                                            busy_message="beschäftigt", fail_message="kaputt")
    assert data == {"ok": True} and http.calls == 1


def test_vorausberechnung_ist_nicht_begrenzt(one_slot):
    http = FakeHttp()
    provider = svc.ClaudeCliBridgeProvider("http://bridge", "token", http=http)
    provider.priority = "low"
    with svc.live_call_slot("high"):
        result = provider.complete("sys", [], {})
    assert result.data == {"ok": True}


class FakeStreamResp:
    status_code = 200

    def iter_lines(self, decode_unicode=True):
        yield "event: delta"
        yield 'data: {"partial_json": "{\\"a\\""}'
        yield ""
        yield "event: result"
        yield 'data: {"data": {"a": 1}, "usage": {}}'
        yield ""

    def close(self):
        pass


class FakeStreamHttp:
    def post(self, *args, **kwargs):
        return FakeStreamResp()


def test_stream_haelt_platz_bis_zum_ende(one_slot):
    provider = svc.ClaudeCliBridgeProvider("http://bridge", "token", http=FakeStreamHttp())
    gen = provider.stream("sys", [], {})
    assert next(gen) == '{"a"'
    with pytest.raises(svc.ProviderError):   # waehrend des Streams ist der Platz belegt
        with svc.live_call_slot("high"):
            pass
    with pytest.raises(StopIteration) as stop:
        next(gen)
    assert stop.value.value.data == {"a": 1}
    with svc.live_call_slot("high"):         # danach wieder frei
        pass

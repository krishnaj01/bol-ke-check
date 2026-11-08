import asyncio
import json
from types import SimpleNamespace

import httpx
import openai
import pytest

from app.config import get_settings
from app.gnani import GnaniError, LLMUnavailable, http, llm, stt, tts


@pytest.fixture
def live_settings(monkeypatch: pytest.MonkeyPatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gnani_mock", False)
    monkeypatch.setattr(settings, "gnani_api_key", "test-key")
    monkeypatch.setattr(settings, "gnani_stt_url", "https://api.vachana.ai/stt/v3")
    monkeypatch.setattr(settings, "gnani_tts_url", "https://api.vachana.ai/api/v1/tts/inference")
    monkeypatch.setattr(settings, "llm_base_url", "http://evon.local/v1")
    return settings


def _route(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    monkeypatch.setattr(
        http, "make_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    monkeypatch.setattr(http._post.retry, "sleep", lambda _: asyncio.sleep(0))


def test_stt_sends_documented_request(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(url=str(request.url), key=request.headers["X-API-Key-ID"], body=request.content)
        return httpx.Response(200, json={"success": True, "transcript": "paisa double"})

    _route(monkeypatch, handler)
    result = asyncio.run(stt.transcribe(b"WAV", "hi-IN", keyterms=["गारंटी"]))
    assert result["text"] == "paisa double"
    assert seen["url"] == "https://api.vachana.ai/stt/v3" and seen["key"] == "test-key"
    for field in (b'name="audio_file"', b'name="language_code"', b"hi-IN", b"codemix"):
        assert field in seen["body"]
    assert "गारंटी".encode() in seen["body"]


def test_stt_failure_body_raises(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    body = {"success": False, "error": {"type": "EMPTY_AUDIO", "message": "x"}}
    _route(monkeypatch, lambda _: httpx.Response(200, json=body))
    with pytest.raises(GnaniError, match="EMPTY_AUDIO"):
        asyncio.run(stt.transcribe(b"WAV", "hi-IN"))


def test_retries_rate_limit_then_succeeds(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    calls = []

    def handler(_: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429)
        return httpx.Response(200, json={"success": True, "transcript": "ok"})

    _route(monkeypatch, handler)
    assert asyncio.run(stt.transcribe(b"WAV", "hi-IN"))["text"] == "ok"
    assert len(calls) == 2


def test_auth_error_is_not_retried(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    calls = []

    def handler(_: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, json={"error_code": "INVALID_API_KEY"})

    _route(monkeypatch, handler)
    with pytest.raises(GnaniError, match="401") as caught:
        asyncio.run(stt.transcribe(b"WAV", "hi-IN"))
    assert len(calls) == 1 and "test-key" not in str(caught.value)


def test_missing_key_fails_cleanly(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    monkeypatch.setattr(live_settings, "gnani_api_key", "")
    with pytest.raises(GnaniError, match="not configured"):
        asyncio.run(stt.transcribe(b"WAV", "hi-IN"))


def test_tts_sends_documented_body(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content), key=request.headers["X-API-Key-ID"])
        return httpx.Response(200, content=b"ID3audio", headers={"content-type": "audio/mpeg"})

    _route(monkeypatch, handler)
    assert asyncio.run(tts.speak("नमस्ते", "Nalini")) == b"ID3audio"
    assert seen["voice"] == "Nalini" and seen["language"] == "hi-IN"
    assert seen["model"] == "timbre-v2.5"
    assert seen["audio_config"]["container"] == "mp3" and seen["key"] == "test-key"


def _fake_openai(monkeypatch: pytest.MonkeyPatch, create) -> None:
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "make_client", lambda: fake)


def test_llm_uses_json_schema_and_zero_temperature(
    monkeypatch: pytest.MonkeyPatch, live_settings
) -> None:
    seen: dict = {}

    async def create(**kwargs):
        seen.update(kwargs)
        message = SimpleNamespace(content='<think>hmm {x}</think>\n```json\n{"flags": []}\n```')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    _fake_openai(monkeypatch, create)
    assert asyncio.run(llm.chat([{"role": "user", "content": "x"}], {"type": "object"})) == {
        "flags": []
    }
    assert seen["temperature"] == 0 and seen["max_tokens"] == 1500
    assert seen["response_format"]["type"] == "json_schema"
    assert seen["extra_body"]["reasoning_effort"] == "none"


def test_llm_prose_reply_raises_value_error() -> None:
    with pytest.raises(ValueError):
        llm.parse_json_reply("Sorry, I cannot do that.")


def test_llm_without_base_url_is_unavailable(
    monkeypatch: pytest.MonkeyPatch, live_settings
) -> None:
    monkeypatch.setattr(live_settings, "llm_base_url", "")
    with pytest.raises(LLMUnavailable):
        asyncio.run(llm.chat([], {}))


def test_llm_api_error_becomes_gnani_error(monkeypatch: pytest.MonkeyPatch, live_settings) -> None:
    async def create(**_):
        raise openai.APIConnectionError(request=httpx.Request("POST", "http://evon.local"))

    _fake_openai(monkeypatch, create)
    with pytest.raises(GnaniError, match="APIConnectionError"):
        asyncio.run(llm.chat([], {}))

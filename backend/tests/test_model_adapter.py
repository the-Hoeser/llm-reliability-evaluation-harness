import pytest

from app.services.model_adapter import ModelAdapterError, OpenAICompatibleAdapter


class FakeResponse:
    status_code = 200
    is_error = False

    def json(self):
        return {
            "choices": [{"message": {"content": "Paris"}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 2},
        }


def test_openai_compatible_adapter_sends_request_and_reads_usage(monkeypatch) -> None:
    monkeypatch.setenv("RELIABILITY_TEST_KEY", "test-secret")
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "payload": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("app.services.model_adapter.httpx.post", fake_post)

    adapter = OpenAICompatibleAdapter(
        model_id="test-model",
        endpoint_url="https://provider.example/v1/",
        api_key_env="RELIABILITY_TEST_KEY",
    )
    result = adapter.generate(
        input_text="What is the capital of France?",
        system_prompt="Answer in one word.",
        parameters={"temperature": 0, "unused_parameter": "ignored"},
    )

    assert captured["url"] == "https://provider.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-secret"
    assert captured["payload"]["messages"][0] == {
        "role": "system",
        "content": "Answer in one word.",
    }
    assert captured["payload"]["temperature"] == 0
    assert "unused_parameter" not in captured["payload"]
    assert "response_format" not in captured["payload"]
    assert result.output_text == "Paris"
    assert result.prompt_tokens == 7
    assert result.completion_tokens == 2


def test_adapter_can_request_json_mode(monkeypatch) -> None:
    monkeypatch.setenv("RELIABILITY_TEST_KEY", "test-secret")
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(json)
        return FakeResponse()

    monkeypatch.setattr("app.services.model_adapter.httpx.post", fake_post)
    adapter = OpenAICompatibleAdapter(
        model_id="test-model",
        endpoint_url="https://provider.example/v1",
        api_key_env="RELIABILITY_TEST_KEY",
    )
    adapter.generate(
        input_text="Return JSON.",
        system_prompt="Return a JSON object.",
        parameters={},
        json_mode=True,
    )
    assert captured["response_format"] == {"type": "json_object"}


def test_adapter_fails_clearly_when_credential_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("RELIABILITY_TEST_KEY", raising=False)
    adapter = OpenAICompatibleAdapter(
        model_id="test-model",
        endpoint_url="https://provider.example/v1",
        api_key_env="RELIABILITY_TEST_KEY",
    )

    with pytest.raises(ModelAdapterError, match="RELIABILITY_TEST_KEY"):
        adapter.generate(input_text="Hello", system_prompt=None, parameters={})

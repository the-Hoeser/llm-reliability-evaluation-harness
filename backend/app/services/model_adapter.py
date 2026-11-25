import os
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class ModelAdapterError(RuntimeError):
    """Raised when a configured model provider cannot return a valid response."""


@dataclass(frozen=True)
class ModelResponse:
    output_text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ModelAdapter(Protocol):
    def generate(
        self,
        *,
        input_text: str,
        system_prompt: str | None,
        parameters: dict[str, Any],
        json_mode: bool = False,
    ) -> ModelResponse: ...


class OpenAICompatibleAdapter:
    """Adapter for providers exposing the OpenAI Chat Completions API shape."""

    def __init__(
        self,
        *,
        model_id: str,
        endpoint_url: str,
        api_key_env: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.model_id = model_id
        self.endpoint_url = endpoint_url.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        *,
        input_text: str,
        system_prompt: str | None,
        parameters: dict[str, Any],
        json_mode: bool = False,
    ) -> ModelResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise ModelAdapterError(
                f"Missing provider credential. Set {self.api_key_env} in backend/.env."
            )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": input_text})

        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
        }
        allowed_parameters = {"temperature", "top_p", "max_tokens", "seed"}
        payload.update({key: value for key, value in parameters.items() if key in allowed_parameters})
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = httpx.post(
                f"{self.endpoint_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ModelAdapterError("The model provider request timed out.") from exc
        except httpx.HTTPError as exc:
            raise ModelAdapterError("The model provider could not be reached.") from exc

        if response.is_error:
            raise ModelAdapterError(
                f"The model provider returned HTTP {response.status_code}."
            )

        try:
            body = response.json()
            output_text = body["choices"][0]["message"]["content"]
            usage = body.get("usage") or {}
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ModelAdapterError(
                "The model provider returned an unexpected response shape."
            ) from exc

        if not isinstance(output_text, str):
            raise ModelAdapterError("The model provider returned non-text message content.")

        return ModelResponse(
            output_text=output_text,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )


def build_model_adapter(model_config: Any) -> ModelAdapter:
    if model_config.provider != "openai_compatible":
        raise ModelAdapterError(f"Unsupported provider: {model_config.provider}")
    return OpenAICompatibleAdapter(
        model_id=model_config.model_id,
        endpoint_url=model_config.endpoint_url,
        api_key_env=model_config.api_key_env,
    )

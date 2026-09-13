"""
Local LLM provider.

Designed for sovereign/on-premise inference.

The provider communicates with a locally hosted OpenAI-compatible
inference server such as:

    Ollama
    vLLM
    LM Studio
    other OpenAI-compatible local servers

No confidential task data is sent to a public cloud provider.
"""

from typing import Any

import httpx

from app.llm.base import BaseLLM, LLMResponse


class LocalLLM(BaseLLM):
    """
    OpenAI-compatible local LLM client.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3.1:8b",
        api_key: str = "local",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._model_name = model
        self.api_key = api_key
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------

    @property
    def model_name(self) -> str:
        return self._model_name

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """
        Generate a response using the local model.
        """

        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout,
            ) as client:

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )

        except httpx.TimeoutException as exc:

            raise RuntimeError(
                "Local LLM request timed out."
            ) from exc

        except httpx.HTTPError as exc:

            raise RuntimeError(
                f"Unable to connect to local LLM: {exc}"
            ) from exc

        if response.status_code >= 400:

            raise RuntimeError(
                "Local LLM returned an error "
                f"({response.status_code}): "
                f"{response.text[:1000]}"
            )

        try:
            data = response.json()

        except ValueError as exc:

            raise RuntimeError(
                "Local LLM returned invalid JSON."
            ) from exc

        try:
            content = (
                data["choices"][0]["message"]["content"]
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:

            raise RuntimeError(
                "Local LLM returned an unexpected response."
            ) from exc

        usage = data.get(
            "usage",
            {},
        )

        return LLMResponse(
            content=str(content),
            model=data.get(
                "model",
                self._model_name,
            ),
            confidence=0.0,
            usage=usage,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Check whether the local inference server is reachable.
        """

        try:

            async with httpx.AsyncClient(
                timeout=10.0,
            ) as client:

                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )

            return response.status_code < 400

        except (
            httpx.HTTPError,
            OSError,
        ):

            return False


# ----------------------------------------------------------------------
# Default local model
# ----------------------------------------------------------------------

local_llm = LocalLLM()
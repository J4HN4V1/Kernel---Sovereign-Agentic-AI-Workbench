"""
Base interface for all LLM providers.

The rest of the backend depends only on this interface.
This allows the system to switch between:

    - local open-weight models
    - remote models
    - different inference servers

without changing the agents.
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMResponse:
    """
    Standardized response returned by an LLM provider.
    """

    def __init__(
        self,
        content: str,
        model: str,
        confidence: float = 0.0,
        usage: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.content = content
        self.model = model
        self.confidence = max(
            0.0,
            min(1.0, confidence),
        )
        self.usage = usage or {}
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the response into a JSON-compatible dictionary.
        """

        return {
            "content": self.content,
            "model": self.model,
            "confidence": self.confidence,
            "usage": self.usage,
            "metadata": self.metadata,
        }


class BaseLLM(ABC):
    """
    Abstract interface implemented by every LLM backend.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Return the model identifier.
        """

        raise NotImplementedError

    @abstractmethod
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
        Generate a response from the model.
        """

        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check whether the model provider is available.
        """

        raise NotImplementedError

    async def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured JSON.

        Providers may override this for native structured-output
        support. The default implementation extracts JSON from the
        generated response.
        """

        import json

        response = await self.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )

        content = response.content.strip()

        # Remove markdown code fences if the model returned them.
        if content.startswith("```"):
            lines = content.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

            if content.lower().startswith("json"):
                content = content[4:].strip()

        try:
            result = json.loads(content)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "LLM JSON response must be an object."
            )

        return result
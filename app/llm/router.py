"""
LLM routing layer.

Selects the appropriate LLM provider for each request while keeping
agents independent from the underlying model implementation.

Primary design:
    Agent
      ↓
    LLMRouter
      ↓
    LocalLLM

The architecture is local-first to preserve the sovereign/on-premise
requirement.
"""

from typing import Any

from app.llm.base import BaseLLM, LLMResponse
from app.llm.local import local_llm


class LLMRouter:
    """
    Routes LLM requests to the appropriate provider.
    """

    def __init__(
        self,
        default_provider: BaseLLM | None = None,
    ) -> None:

        self.providers: dict[str, BaseLLM] = {
            "local": local_llm,
        }

        self.default_provider = (
            default_provider or local_llm
        )

    # ==================================================================
    # PROVIDER REGISTRATION
    # ==================================================================

    def register(
        self,
        name: str,
        provider: BaseLLM,
    ) -> None:
        """
        Register an LLM provider.
        """

        if not name.strip():
            raise ValueError(
                "Provider name cannot be empty."
            )

        self.providers[name.lower()] = provider

    # ==================================================================
    # PROVIDER SELECTION
    # ==================================================================

    def get_provider(
        self,
        provider: str | None = None,
    ) -> BaseLLM:
        """
        Return the requested provider.

        Falls back to the local provider.
        """

        if provider is None:
            return self.default_provider

        selected = self.providers.get(
            provider.lower()
        )

        if selected is None:
            raise ValueError(
                f"Unknown LLM provider: {provider}"
            )

        return selected

    # ==================================================================
    # GENERATION
    # ==================================================================

    async def generate(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """
        Generate text using the selected provider.
        """

        selected_provider = self.get_provider(
            provider
        )

        return await selected_provider.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )

    # ==================================================================
    # STRUCTURED GENERATION
    # ==================================================================

    async def generate_json(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response.
        """

        selected_provider = self.get_provider(
            provider
        )

        return await selected_provider.generate_json(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )

    # ==================================================================
    # HEALTH
    # ==================================================================

    async def health_check(
        self,
        provider: str | None = None,
    ) -> bool:
        """
        Check provider availability.
        """

        selected_provider = self.get_provider(
            provider
        )

        return await selected_provider.health_check()

    # ==================================================================
    # AVAILABLE PROVIDERS
    # ==================================================================

    def available_providers(
        self,
    ) -> list[str]:
        """
        Return registered provider names.
        """

        return list(
            self.providers.keys()
        )


# ======================================================================
# DEFAULT ROUTER
# ======================================================================

llm_router = LLMRouter()
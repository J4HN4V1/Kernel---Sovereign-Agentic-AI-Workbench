"""
Base abstractions for all Kernel agents.

Every specialized agent in the system inherits from BaseAgent.

This gives us a consistent production-style interface for:

    Planner Agent
    Reasoning Agent
    Document Agent
    Vision Agent
    Privacy Agent
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """
    Shared context passed between agents during a task.

    This object is intentionally generic so that agents can add
    information without tightly coupling themselves to one another.
    """

    task_id: UUID

    user_query: str

    input_data: dict[str, Any] = Field(default_factory=dict)

    metadata: dict[str, Any] = Field(default_factory=dict)

    previous_results: dict[str, Any] = Field(default_factory=dict)

    confidence: float = 0.0

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class AgentResult(BaseModel):
    """
    Standard result returned by every agent.
    """

    agent_id: UUID = Field(
        default_factory=uuid4
    )

    agent_name: str

    success: bool

    output: Any = None

    confidence: float = 0.0

    reasoning: str | None = None

    requires_external_capability: bool = False

    capability_request: dict[str, Any] | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    error: str | None = None

    started_at: datetime

    completed_at: datetime


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Each agent must implement:

        1. run()
        2. can_handle()

    Agents should remain independent from the HTTP/API layer.
    """

    name: str = "base_agent"

    description: str = "Base Kernel agent."

    confidence_threshold: float = 0.90

    def __init__(
        self,
        confidence_threshold: float | None = None,
    ) -> None:

        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute the agent against the supplied context.
        """
        raise NotImplementedError

    @abstractmethod
    async def can_handle(
        self,
        context: AgentContext,
    ) -> bool:
        """
        Determine whether this agent can handle the task.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def is_confident(
        self,
        confidence: float,
    ) -> bool:
        """
        Determine whether the agent's confidence is sufficient
        for autonomous execution.
        """

        return confidence >= self.confidence_threshold

    def build_result(
        self,
        *,
        context: AgentContext,
        success: bool,
        output: Any = None,
        confidence: float = 0.0,
        reasoning: str | None = None,
        requires_external_capability: bool = False,
        capability_request: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
        started_at: datetime,
    ) -> AgentResult:
        """
        Build a standardized AgentResult.
        """

        completed_at = datetime.now(UTC)

        return AgentResult(
            agent_name=self.name,
            success=success,
            output=output,
            confidence=confidence,
            reasoning=reasoning,
            requires_external_capability=(
                requires_external_capability
            ),
            capability_request=capability_request,
            metadata=metadata or {},
            error=error,
            started_at=started_at,
            completed_at=completed_at,
        )

    async def execute(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Safely execute the agent.

        This wrapper gives us one consistent execution boundary
        for logging, timing, and error handling.
        """

        started_at = datetime.now(UTC)

        try:
            if not await self.can_handle(context):
                return self.build_result(
                    context=context,
                    success=False,
                    confidence=0.0,
                    reasoning=(
                        f"{self.name} cannot handle this task."
                    ),
                    error="Agent cannot handle the supplied context.",
                    started_at=started_at,
                )

            result = await self.run(context)

            return result

        except Exception as exc:
            return self.build_result(
                context=context,
                success=False,
                confidence=0.0,
                reasoning=(
                    f"{self.name} encountered an execution error."
                ),
                error=str(exc),
                started_at=started_at,
            )
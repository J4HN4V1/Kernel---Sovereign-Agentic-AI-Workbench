"""
Reasoning agent.

Uses the configured local LLM to reason over the task context
and produce a final answer.
"""

from datetime import UTC, datetime
from typing import Any

from app.agents.base import (
    AgentContext,
    AgentResult,
    BaseAgent,
)
from app.llm.router import llm_router


class ReasoningAgent(BaseAgent):
    """
    Agent responsible for reasoning and final response generation.
    """

    name = "reasoning_agent"

    description = (
        "Uses the local LLM to reason over task context "
        "and generate a final response."
    )

    async def can_handle(
        self,
        context: AgentContext,
    ) -> bool:
        return bool(
            context.user_query
            and context.user_query.strip()
        )

    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:

        started_at = datetime.now(UTC)

        system_prompt = (
            "You are the reasoning agent of a sovereign "
            "on-premise enterprise AI workbench. "
            "Reason carefully using only the provided context. "
            "Do not invent facts. "
            "Give a concise, useful answer."
        )

        context_data: dict[str, Any] = {
            "input_data": context.input_data,
            "metadata": context.metadata,
            "previous_results": context.previous_results,
        }

        prompt = (
            f"User query:\n{context.user_query}\n\n"
            f"Available task context:\n{context_data}\n\n"
            "Provide the best possible answer."
        )

        try:
            response = await llm_router.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            return self.build_result(
                context=context,
                success=True,
                output=response,
                confidence=0.90,
                reasoning=(
                    "Response generated using the configured "
                    "local LLM."
                ),
                metadata={
                    "agent_version": "1.0.0",
                },
                started_at=started_at,
            )

        except Exception as exc:

            return self.build_result(
                context=context,
                success=False,
                confidence=0.0,
                reasoning="Local LLM generation failed.",
                error=str(exc),
                started_at=started_at,
            )
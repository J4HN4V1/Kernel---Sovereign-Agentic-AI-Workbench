"""
Planner Agent.

The Planner is the entry point of the multi-agent reasoning system.

Its job is NOT to solve the user's task directly.

It analyzes the request and creates an execution plan describing:

    - what type of task this is
    - which agents are required
    - whether documents/vision/RAG are needed
    - whether an external capability may be required
    - the expected execution order
"""

from datetime import UTC, datetime
from typing import Any

from app.agents.base import AgentContext, AgentResult, BaseAgent


class PlannerAgent(BaseAgent):
    """
    Converts a user request into an executable agent plan.
    """

    name = "planner_agent"

    description = (
        "Analyzes the task and determines the optimal agentic "
        "execution plan."
    )

    confidence_threshold = 0.80

    # ------------------------------------------------------------------
    # Task classification
    # ------------------------------------------------------------------

    def _classify_task(self, query: str) -> str:
        """
        Perform lightweight task classification.

        This is deliberately deterministic for the initial backend.

        Later, the local LLM will perform richer semantic planning.
        """

        query_lower = query.lower()

        vision_keywords = {
            "image",
            "drawing",
            "diagram",
            "photo",
            "scan",
            "scanned",
            "visual",
            "picture",
            "blueprint",
            "p&id",
        }

        document_keywords = {
            "document",
            "report",
            "pdf",
            "contract",
            "manual",
            "policy",
            "file",
            "report",
        }

        engineering_keywords = {
            "engineering",
            "equipment",
            "pipeline",
            "piping",
            "pump",
            "valve",
            "pressure",
            "temperature",
            "technical",
            "manufacturing",
        }

        if any(
            keyword in query_lower
            for keyword in vision_keywords
        ):
            return "vision"

        if any(
            keyword in query_lower
            for keyword in document_keywords
        ):
            return "document"

        if any(
            keyword in query_lower
            for keyword in engineering_keywords
        ):
            return "engineering"

        return "general"

    # ------------------------------------------------------------------
    # Agent selection
    # ------------------------------------------------------------------

    def _select_agents(
        self,
        task_type: str,
    ) -> list[str]:
        """
        Determine the initial agent execution sequence.
        """

        plans: dict[str, list[str]] = {
            "general": [
                "reasoning_agent",
                "privacy_agent",
            ],
            "document": [
                "document_agent",
                "reasoning_agent",
                "privacy_agent",
            ],
            "vision": [
                "vision_agent",
                "document_agent",
                "reasoning_agent",
                "privacy_agent",
            ],
            "engineering": [
                "document_agent",
                "reasoning_agent",
                "privacy_agent",
            ],
        }

        return plans.get(
            task_type,
            plans["general"],
        )

    # ------------------------------------------------------------------
    # External capability detection
    # ------------------------------------------------------------------

    def _determine_capability_need(
        self,
        task_type: str,
        query: str,
    ) -> dict[str, Any]:
        """
        Determine whether the task may require specialized
        external intelligence.

        This does NOT perform the purchase.

        The later workflow will make the actual decision after local
        processing and confidence evaluation.
        """

        if task_type == "engineering":
            return {
                "possible": True,
                "category": "engineering",
                "reason": (
                    "Engineering tasks may benefit from specialized "
                    "external analysis."
                ),
            }

        if task_type == "vision":
            return {
                "possible": True,
                "category": "vision",
                "reason": (
                    "Complex visual tasks may require specialized "
                    "external vision/OCR capabilities."
                ),
            }

        return {
            "possible": False,
            "category": None,
            "reason": (
                "No specialized external capability identified "
                "at planning stage."
            ),
        }

    # ------------------------------------------------------------------
    # Build plan
    # ------------------------------------------------------------------

    def _build_plan(
        self,
        context: AgentContext,
    ) -> dict[str, Any]:
        """
        Build the complete execution plan.
        """

        task_type = self._classify_task(
            context.user_query
        )

        agents = self._select_agents(
            task_type
        )

        capability = self._determine_capability_need(
            task_type,
            context.user_query,
        )

        return {
            "task_type": task_type,
            "agents": agents,
            "execution_mode": "sequential",
            "requires_rag": task_type in {
                "document",
                "engineering",
            },
            "requires_vision": task_type == "vision",
            "external_capability": capability,
            "policy_check_required": True,
            "payment_allowed_only_after_policy": True,
        }

    # ------------------------------------------------------------------
    # BaseAgent implementation
    # ------------------------------------------------------------------

    async def can_handle(
        self,
        context: AgentContext,
    ) -> bool:
        """
        Planner can handle any non-empty user request.
        """

        return bool(
            context.user_query
            and context.user_query.strip()
        )

    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Analyze the request and generate an execution plan.
        """

        started_at = datetime.now(UTC)

        plan = self._build_plan(context)

        confidence = 0.90

        return self.build_result(
            context=context,
            success=True,
            output=plan,
            confidence=confidence,
            reasoning=(
                "Task classified and an initial multi-agent "
                "execution plan was generated."
            ),
            requires_external_capability=(
                plan["external_capability"]["possible"]
            ),
            capability_request=(
                plan["external_capability"]
                if plan["external_capability"]["possible"]
                else None
            ),
            metadata={
                "planner_version": "1.0.0",
                "task_type": plan["task_type"],
                "agent_count": len(plan["agents"]),
            },
            started_at=started_at,
        )
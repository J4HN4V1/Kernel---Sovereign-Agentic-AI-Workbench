"""
Agent execution engine.

Responsible for executing individual agents safely and consistently.

The executor:
    - builds agent context
    - executes an agent
    - captures execution metadata
    - handles failures
    - records audit information
    - returns a normalized AgentResult

The executor does NOT decide which agent should run.
That responsibility belongs to graph.py.
"""

from datetime import UTC, datetime
from typing import Any

from app.agents.base import AgentContext, BaseAgent, AgentResult
from app.orchestration.state import (
    AgentExecution,
    TaskState,
)


class AgentExecutor:
    """
    Production execution wrapper around individual agents.
    """

    def __init__(self) -> None:
        self.max_execution_time = 120

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def build_context(
        self,
        state: TaskState,
    ) -> AgentContext:
        """
        Build the standardized context passed to every agent.
        """

        return AgentContext(
            task_id=state.task_id,
            user_query=state.user_query,
            input_data=state.input_data,
            metadata=state.metadata,
            previous_results=state.agent_results,
        )

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    async def execute(
        self,
        agent: BaseAgent,
        state: TaskState,
    ) -> AgentResult:
        """
        Execute one agent and normalize its lifecycle.
        """

        started_at = datetime.now(UTC)

        agent_name = getattr(
            agent,
            "name",
            agent.__class__.__name__,
        )

        state.add_audit_event(
            event_type="agent_execution_started",
            message=f"{agent_name} execution started.",
            metadata={
                "agent": agent_name,
                "task_id": str(state.task_id),
            },
        )

        try:
            context = self.build_context(
                state
            )

            # ----------------------------------------------------------
            # Capability check
            # ----------------------------------------------------------

            can_handle = await agent.can_handle(
                context
            )

            if not can_handle:

                result = AgentResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    reasoning=(
                        f"{agent_name} cannot handle this task."
                    ),
                    error=(
                        f"Agent {agent_name} cannot handle "
                        "the provided task."
                    ),
                    requires_external_capability=False,
                    capability_request=None,
                )

            else:

                # ------------------------------------------------------
                # Actual execution
                # ------------------------------------------------------

                result = await agent.run(
                    context
                )

            completed_at = datetime.now(UTC)

            # ----------------------------------------------------------
            # Record execution
            # ----------------------------------------------------------

            execution = AgentExecution(
                agent_name=agent_name,
                status=(
                    "completed"
                    if result.success
                    else "failed"
                ),
                started_at=started_at,
                completed_at=completed_at,
                confidence=result.confidence,
                output=result.output,
                error=result.error,
            )

            state.add_agent_execution(
                execution
            )

            state.store_agent_result(
                agent_name,
                result.model_dump(
                    mode="json"
                ),
            )

            state.add_audit_event(
                event_type="agent_execution_completed",
                message=(
                    f"{agent_name} execution completed."
                ),
                metadata={
                    "agent": agent_name,
                    "success": result.success,
                    "confidence": result.confidence,
                    "duration_ms": (
                        completed_at - started_at
                    ).total_seconds()
                    * 1000,
                },
            )

            return result

        except Exception as exc:

            completed_at = datetime.now(UTC)

            execution = AgentExecution(
                agent_name=agent_name,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                confidence=0.0,
                output=None,
                error=str(exc),
            )

            state.add_agent_execution(
                execution
            )

            state.add_audit_event(
                event_type="agent_execution_failed",
                message=(
                    f"{agent_name} execution failed."
                ),
                metadata={
                    "agent": agent_name,
                    "error": str(exc),
                },
            )

            raise


# ----------------------------------------------------------------------
# Default executor
# ----------------------------------------------------------------------

agent_executor = AgentExecutor()
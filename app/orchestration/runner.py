"""
Workflow runner.

This is the service boundary between the API layer and the
agentic orchestration layer.

API
 ↓
WorkflowRunner
 ↓
WorkflowGraph
 ↓
Agents / Capabilities / Payments
"""

from typing import Any
from uuid import UUID

from app.orchestration.graph import workflow_graph
from app.orchestration.state import TaskState


class WorkflowRunner:
    """
    High-level interface for creating and executing tasks.
    """

    def __init__(self) -> None:
        self.graph = workflow_graph

    # ==================================================================
    # CREATE TASK
    # ==================================================================

    def create_task(
        self,
        user_query: str,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskState:
        """
        Create a new task state without executing it.
        """

        if not user_query or not user_query.strip():
            raise ValueError(
                "user_query cannot be empty."
            )

        return TaskState(
            user_query=user_query.strip(),
            input_data=input_data or {},
            metadata=metadata or {},
        )

    # ==================================================================
    # EXECUTE
    # ==================================================================

    async def execute(
        self,
        user_query: str,
        input_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskState:
        """
        Create and execute a new task.
        """

        state = self.create_task(
            user_query=user_query,
            input_data=input_data,
            metadata=metadata,
        )

        return await self.execute_state(
            state
        )

    # ==================================================================
    # EXECUTE EXISTING STATE
    # ==================================================================

    async def execute_state(
        self,
        state: TaskState,
    ) -> TaskState:
        """
        Execute an existing task state through the workflow graph.
        """

        return await self.graph.run(
            state
        )

    # ==================================================================
    # RESUME
    # ==================================================================

    async def resume(
        self,
        state: TaskState,
    ) -> TaskState:
        """
        Resume an existing workflow.

        Completed and blocked tasks are not executed again.
        """

        if state.status.value == "completed":
            return state

        if state.status.value == "blocked":
            return state

        return await self.execute_state(
            state
        )

    # ==================================================================
    # SERIALIZE
    # ==================================================================

    def serialize(
        self,
        state: TaskState,
    ) -> dict[str, Any]:
        """
        Convert the task state into JSON-compatible data.
        """

        return state.model_dump(
            mode="json"
        )

    # ==================================================================
    # TASK ID
    # ==================================================================

    @staticmethod
    def get_task_id(
        state: TaskState,
    ) -> UUID:
        """
        Return the task identifier.
        """

        return state.task_id


# ======================================================================
# DEFAULT RUNNER
# ======================================================================

workflow_runner = WorkflowRunner()
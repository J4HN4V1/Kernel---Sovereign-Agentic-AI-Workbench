"""
Agentic workflow graph.

Controls the order in which agents execute.

Flow:

    Planner
       ↓
    Document / Vision
       ↓
    Reasoning
       ↓
    Privacy
       ↓
    Capability decision
       ↓
    Payment / external execution
       ↓
    Verification
       ↓
    Final response

The graph controls orchestration only.
Actual agent execution is handled by executor.py.
"""

from typing import Any

from app.agents.document import DocumentAgent
from app.agents.planner import PlannerAgent
from app.agents.privacy import PrivacyAgent
from app.agents.reasoning import ReasoningAgent
from app.agents.vision import VisionAgent

from app.orchestration.executor import agent_executor
from app.orchestration.state import TaskState, TaskStatus


class WorkflowGraph:
    """
    Main workflow controller.
    """

    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.document = DocumentAgent()
        self.vision = VisionAgent()
        self.reasoning = ReasoningAgent()
        self.privacy = PrivacyAgent()

    # ==================================================================
    # Planner
    # ==================================================================

    async def run_planner(
        self,
        state: TaskState,
    ) -> None:
        """
        Create the execution plan for the task.
        """

        state.update_status(
            TaskStatus.PLANNING
        )

        result = await agent_executor.execute(
            self.planner,
            state,
        )

        if not result.success:
            state.fail(
                error=result.error
                or "Planner agent failed.",
                error_code="PLANNER_FAILED",
            )
            return

        state.plan = result.output or {}

        state.add_audit_event(
            event_type="workflow_plan_created",
            message="Workflow plan created successfully.",
            metadata={
                "plan": state.plan,
            },
        )

    # ==================================================================
    # Document processing
    # ==================================================================

    async def run_document(
        self,
        state: TaskState,
    ) -> None:
        """
        Run document analysis when required.
        """

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return

        context = agent_executor.build_context(
            state
        )

        if not await self.document.can_handle(
            context
        ):
            return

        state.update_status(
            TaskStatus.PROCESSING
        )

        result = await agent_executor.execute(
            self.document,
            state,
        )

        if not result.success:
            state.fail(
                error=result.error
                or "Document processing failed.",
                error_code="DOCUMENT_PROCESSING_FAILED",
            )

    # ==================================================================
    # Vision processing
    # ==================================================================

    async def run_vision(
        self,
        state: TaskState,
    ) -> None:
        """
        Run vision processing when required.
        """

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return

        context = agent_executor.build_context(
            state
        )

        if not await self.vision.can_handle(
            context
        ):
            return

        state.update_status(
            TaskStatus.PROCESSING
        )

        result = await agent_executor.execute(
            self.vision,
            state,
        )

        if not result.success:
            state.fail(
                error=result.error
                or "Vision processing failed.",
                error_code="VISION_PROCESSING_FAILED",
            )

    # ==================================================================
    # Reasoning
    # ==================================================================

    async def run_reasoning(
        self,
        state: TaskState,
    ) -> None:
        """
        Perform local reasoning after preprocessing.
        """

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return

        state.update_status(
            TaskStatus.REASONING
        )

        result = await agent_executor.execute(
            self.reasoning,
            state,
        )

        if not result.success:
            state.fail(
                error=result.error
                or "Reasoning failed.",
                error_code="REASONING_FAILED",
            )
            return

        state.current_answer = result.output

        state.confidence = result.confidence

        state.add_audit_event(
            event_type="reasoning_completed",
            message="Local reasoning completed.",
            metadata={
                "confidence": result.confidence,
                "requires_external_capability": (
                    result.requires_external_capability
                ),
            },
        )

    # ==================================================================
    # Privacy
    # ==================================================================

    async def run_privacy(
        self,
        state: TaskState,
    ) -> None:
        """
        Run the privacy/security gate before any external operation.
        """

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return

        state.update_status(
            TaskStatus.PRIVACY_CHECK
        )

        result = await agent_executor.execute(
            self.privacy,
            state,
        )

        if not result.success:
            state.fail(
                error=result.error
                or "Privacy validation failed.",
                error_code="PRIVACY_FAILED",
            )
            return

        output = result.output or {}

        scan = output.get(
            "scan",
            {},
        )

        state.privacy.checked = True

        state.privacy.decision = output.get(
            "policy_decision",
            "unknown",
        )

        state.privacy.external_call_allowed = (
            output.get(
                "external_call_allowed",
                False,
            )
        )

        state.privacy.payment_allowed = (
            output.get(
                "payment_allowed",
                False,
            )
        )

        state.privacy.requires_redaction = (
            output.get(
                "requires_redaction",
                False,
            )
        )

        state.privacy.findings_count = scan.get(
            "total_findings",
            0,
        )

        state.privacy.critical_findings = scan.get(
            "critical_findings",
            0,
        )

        state.privacy.sanitized_query = output.get(
            "sanitized_query"
        )

        # --------------------------------------------------------------
        # Security block
        # --------------------------------------------------------------

        if not state.privacy.external_call_allowed:

            state.block(
                reason=(
                    "External execution was blocked by "
                    "the privacy policy."
                )
            )

            return

        state.add_audit_event(
            event_type="privacy_check_passed",
            message="Privacy gate approved workflow continuation.",
            metadata={
                "decision": state.privacy.decision,
                "external_call_allowed": (
                    state.privacy.external_call_allowed
                ),
                "payment_allowed": (
                    state.privacy.payment_allowed
                ),
            },
        )

    # ==================================================================
    # Determine whether external capability is required
    # ==================================================================

    def requires_external_capability(
        self,
        state: TaskState,
    ) -> bool:
        """
        Determine whether the reasoning agent requires an external
        capability.
        """

        result = state.agent_results.get(
            self.reasoning.name,
            {},
        )

        return bool(
            result.get(
                "requires_external_capability",
                False,
            )
        )

    # ==================================================================
    # Finalize
    # ==================================================================

    def finalize(
        self,
        state: TaskState,
    ) -> None:
        """
        Finalize a task when no external capability is required.
        """

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return

        state.complete(
            answer=state.current_answer,
            confidence=state.confidence,
        )

        state.add_audit_event(
            event_type="workflow_completed",
            message="Workflow completed locally.",
            metadata={
                "confidence": state.confidence,
            },
        )

    # ==================================================================
    # Main workflow
    # ==================================================================

    async def run(
        self,
        state: TaskState,
    ) -> TaskState:
        """
        Execute the agentic workflow.
        """

        state.add_audit_event(
            event_type="workflow_started",
            message="Agentic workflow started.",
        )

        # --------------------------------------------------------------
        # 1. Planner
        # --------------------------------------------------------------

        await self.run_planner(
            state
        )

        if state.status == TaskStatus.FAILED:
            return state

        # --------------------------------------------------------------
        # 2. Determine planned agents
        # --------------------------------------------------------------

        planned_agents = state.plan.get(
            "agents",
            [],
        )

        # --------------------------------------------------------------
        # 3. Document processing
        # --------------------------------------------------------------

        if (
            self.document.name
            in planned_agents
        ):
            await self.run_document(
                state
            )

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return state

        # --------------------------------------------------------------
        # 4. Vision processing
        # --------------------------------------------------------------

        if (
            self.vision.name
            in planned_agents
        ):
            await self.run_vision(
                state
            )

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return state

        # --------------------------------------------------------------
        # 5. Local reasoning
        # --------------------------------------------------------------

        await self.run_reasoning(
            state
        )

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return state

        # --------------------------------------------------------------
        # 6. Privacy gate
        # --------------------------------------------------------------

        await self.run_privacy(
            state
        )

        if state.status in {
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        }:
            return state

        # --------------------------------------------------------------
        # 7. External capability decision
        # --------------------------------------------------------------

        if self.requires_external_capability(
            state
        ):

            state.update_status(
                TaskStatus.CAPABILITY_SELECTION
            )

            state.add_audit_event(
                event_type="external_capability_required",
                message=(
                    "Local reasoning requires an "
                    "external capability."
                ),
                metadata={
                    "confidence": state.confidence,
                },
            )

            # The next stages will be connected through the existing
            # capabilities and payments architecture.

            return state

        # --------------------------------------------------------------
        # 8. Local completion
        # --------------------------------------------------------------

        self.finalize(
            state
        )

        return state


# ======================================================================
# Default workflow graph
# ======================================================================

workflow_graph = WorkflowGraph()
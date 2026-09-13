"""
Shared state for the agentic orchestration workflow.

This is the central state object passed through the multi-agent
pipeline.

Flow:

    User Request
         ↓
      Planner
         ↓
    Document / Vision
         ↓
     Reasoning
         ↓
      Privacy
         ↓
 Capability Selection
         ↓
      x402 Payment
         ↓
 External Capability
         ↓
    Verification
         ↓
       Final Answer
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# Task status
# ----------------------------------------------------------------------

class TaskStatus(str, Enum):
    """
    Lifecycle states for an agentic task.
    """

    CREATED = "created"

    PLANNING = "planning"

    PROCESSING = "processing"

    REASONING = "reasoning"

    PRIVACY_CHECK = "privacy_check"

    CAPABILITY_SELECTION = "capability_selection"

    PAYMENT_PENDING = "payment_pending"

    EXTERNAL_EXECUTION = "external_execution"

    VERIFYING = "verifying"

    COMPLETED = "completed"

    FAILED = "failed"

    BLOCKED = "blocked"


# ----------------------------------------------------------------------
# Agent execution record
# ----------------------------------------------------------------------

class AgentExecution(BaseModel):
    """
    Record of one agent execution.
    """

    execution_id: UUID = Field(
        default_factory=uuid4
    )

    agent_name: str

    status: str

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    completed_at: datetime | None = None

    confidence: float = 0.0

    output: Any = None

    error: str | None = None


# ----------------------------------------------------------------------
# Capability decision
# ----------------------------------------------------------------------

class CapabilityDecision(BaseModel):
    """
    Represents the decision to use an external capability.
    """

    required: bool = False

    capability_id: UUID | None = None

    capability_name: str | None = None

    category: str | None = None

    reason: str | None = None

    confidence_before: float = 0.0

    expected_confidence_after: float = 0.0

    estimated_cost: float = 0.0

    currency: str = "ALGO"

    privacy_approved: bool = False

    payment_approved: bool = False


# ----------------------------------------------------------------------
# Payment state
# ----------------------------------------------------------------------

class PaymentState(BaseModel):
    """
    State of an x402 payment associated with the task.
    """

    required: bool = False

    payment_id: UUID | None = None

    status: str = "not_required"

    amount: float = 0.0

    currency: str = "ALGO"

    network: str = "algorand-testnet"

    transaction_id: str | None = None

    verified: bool = False


# ----------------------------------------------------------------------
# Privacy state
# ----------------------------------------------------------------------

class PrivacyState(BaseModel):
    """
    Result of privacy/security evaluation.
    """

    checked: bool = False

    decision: str = "not_checked"

    external_call_allowed: bool = False

    payment_allowed: bool = False

    requires_redaction: bool = False

    findings_count: int = 0

    critical_findings: int = 0

    sanitized_query: str | None = None


# ----------------------------------------------------------------------
# Complete task state
# ----------------------------------------------------------------------

class TaskState(BaseModel):
    """
    Complete state of one agentic task.

    This object is the single source of truth for the orchestration
    workflow.
    """

    task_id: UUID = Field(
        default_factory=uuid4
    )

    user_query: str

    status: TaskStatus = TaskStatus.CREATED

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    # --------------------------------------------------------------
    # Input
    # --------------------------------------------------------------

    input_data: dict[str, Any] = Field(
        default_factory=dict
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    # --------------------------------------------------------------
    # Planning
    # --------------------------------------------------------------

    plan: dict[str, Any] = Field(
        default_factory=dict
    )

    # --------------------------------------------------------------
    # Agent execution
    # --------------------------------------------------------------

    agent_executions: list[AgentExecution] = Field(
        default_factory=list
    )

    agent_results: dict[str, Any] = Field(
        default_factory=dict
    )

    # --------------------------------------------------------------
    # Reasoning
    # --------------------------------------------------------------

    current_answer: Any = None

    final_answer: Any = None

    confidence: float = 0.0

    # --------------------------------------------------------------
    # Privacy
    # --------------------------------------------------------------

    privacy: PrivacyState = Field(
        default_factory=PrivacyState
    )

    # --------------------------------------------------------------
    # External capability
    # --------------------------------------------------------------

    capability: CapabilityDecision = Field(
        default_factory=CapabilityDecision
    )

    # --------------------------------------------------------------
    # Payment
    # --------------------------------------------------------------

    payment: PaymentState = Field(
        default_factory=PaymentState
    )

    # --------------------------------------------------------------
    # External execution
    # --------------------------------------------------------------

    external_result: Any = None

    external_provider: str | None = None

    # --------------------------------------------------------------
    # Error handling
    # --------------------------------------------------------------

    error: str | None = None

    error_code: str | None = None

    # --------------------------------------------------------------
    # Audit
    # --------------------------------------------------------------

    audit_events: list[dict[str, Any]] = Field(
        default_factory=list
    )

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def update_status(
        self,
        status: TaskStatus,
    ) -> None:
        """
        Update task status and timestamp.
        """

        self.status = status

        self.updated_at = datetime.now(UTC)

    def add_audit_event(
        self,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a structured audit event.
        """

        self.audit_events.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "message": message,
                "metadata": metadata or {},
            }
        )

        self.updated_at = datetime.now(UTC)

    def add_agent_execution(
        self,
        execution: AgentExecution,
    ) -> None:
        """
        Store an agent execution record.
        """

        self.agent_executions.append(
            execution
        )

        self.updated_at = datetime.now(UTC)

    def store_agent_result(
        self,
        agent_name: str,
        result: Any,
    ) -> None:
        """
        Store an agent result for downstream agents.
        """

        self.agent_results[agent_name] = result

        self.updated_at = datetime.now(UTC)

    def fail(
        self,
        error: str,
        error_code: str = "TASK_FAILED",
    ) -> None:
        """
        Mark the task as failed.
        """

        self.status = TaskStatus.FAILED

        self.error = error

        self.error_code = error_code

        self.updated_at = datetime.now(UTC)

        self.add_audit_event(
            event_type="task_failed",
            message=error,
            metadata={
                "error_code": error_code,
            },
        )

    def block(
        self,
        reason: str,
    ) -> None:
        """
        Block the task because policy/security requirements
        were not satisfied.
        """

        self.status = TaskStatus.BLOCKED

        self.error = reason

        self.error_code = "POLICY_BLOCKED"

        self.updated_at = datetime.now(UTC)

        self.add_audit_event(
            event_type="task_blocked",
            message=reason,
        )

    def complete(
        self,
        answer: Any,
        confidence: float,
    ) -> None:
        """
        Mark the task as successfully completed.
        """

        self.status = TaskStatus.COMPLETED

        self.final_answer = answer

        self.current_answer = answer

        self.confidence = confidence

        self.updated_at = datetime.now(UTC)

        self.add_audit_event(
            event_type="task_completed",
            message="Task completed successfully.",
            metadata={
                "confidence": confidence,
            },
        )
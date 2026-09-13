from __future__ import annotations

from enum import Enum
from typing import Any


class AuditEventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_CLASSIFIED = "document.classified"
    DOCUMENT_PROCESSED = "document.processed"

    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    CAPABILITY_DISCOVERED = "capability.discovered"
    CAPABILITY_SELECTED = "capability.selected"
    CAPABILITY_EXECUTED = "capability.executed"

    PRIVACY_CHECK = "privacy.check"
    PRIVACY_BLOCKED = "privacy.blocked"
    DATA_ANONYMIZED = "data.anonymized"

    PAYMENT_REQUESTED = "payment.requested"
    PAYMENT_VERIFIED = "payment.verified"
    PAYMENT_SETTLED = "payment.settled"
    PAYMENT_FAILED = "payment.failed"

    SECURITY_AUTHENTICATED = "security.authenticated"
    SECURITY_DENIED = "security.denied"

    SYSTEM_ERROR = "system.error"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent:
    """
    Standard structure for every auditable backend event.

    The audit layer is intentionally independent from the database
    so events can later be written to PostgreSQL, SIEM, files,
    or another observability system.
    """

    def __init__(
        self,
        event_type: AuditEventType | str,
        *,
        user_id: str | None = None,
        task_id: str | None = None,
        severity: AuditSeverity | str = AuditSeverity.INFO,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.event_type = (
            event_type.value
            if isinstance(event_type, AuditEventType)
            else event_type
        )

        self.user_id = user_id
        self.task_id = task_id

        self.severity = (
            severity.value
            if isinstance(severity, AuditSeverity)
            else severity
        )

        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "severity": self.severity,
            "details": self.details,
        }


def task_event(
    event_type: AuditEventType,
    task_id: str,
    *,
    user_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_type,
        user_id=user_id,
        task_id=task_id,
        details=details,
    )


def payment_event(
    event_type: AuditEventType,
    *,
    task_id: str | None = None,
    user_id: str | None = None,
    payment_id: str | None = None,
    transaction_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    payload = dict(details or {})

    if payment_id:
        payload["payment_id"] = payment_id

    if transaction_id:
        payload["transaction_id"] = transaction_id

    return AuditEvent(
        event_type,
        user_id=user_id,
        task_id=task_id,
        details=payload,
    )


def security_event(
    event_type: AuditEventType,
    *,
    user_id: str | None = None,
    details: dict[str, Any] | None = None,
    severity: AuditSeverity = AuditSeverity.INFO,
) -> AuditEvent:
    return AuditEvent(
        event_type,
        user_id=user_id,
        severity=severity,
        details=details,
    )
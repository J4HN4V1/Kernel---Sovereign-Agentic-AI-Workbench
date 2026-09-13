from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit.events import AuditEvent
from app.database.repositories import AuditRepository


logger = logging.getLogger("kernel.audit")


class AuditLogger:
    """
    Central audit logger for the entire backend.

    Every important action can be:
    1. written to application logs
    2. persisted in the database
    3. safely correlated using an event ID
    """

    def __init__(
        self,
        db: Session | None = None,
    ) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # LOG EVENT
    # ------------------------------------------------------------------

    def log(
        self,
        event: AuditEvent,
        *,
        persist: bool = True,
    ) -> str:
        event_id = uuid.uuid4().hex

        payload = {
            "event_id": event_id,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            **event.to_dict(),
        }

        # Application log
        logger.info(
            json.dumps(
                payload,
                default=str,
                separators=(",", ":"),
            )
        )

        # Database audit trail
        if persist and self.db is not None:
            try:
                repository = AuditRepository(
                    self.db
                )

                repository.create(
                    event_id=event_id,
                    event_type=event.event_type,
                    user_id=event.user_id,
                    task_id=event.task_id,
                    severity=event.severity,
                    details=event.details,
                )

            except Exception:
                # Audit failure must never crash the actual
                # business operation.
                logger.exception(
                    "Failed to persist audit event."
                )

        return event_id

    # ------------------------------------------------------------------
    # CONVENIENCE METHODS
    # ------------------------------------------------------------------

    def info(
        self,
        event_type: str,
        *,
        user_id: str | None = None,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        event = AuditEvent(
            event_type,
            user_id=user_id,
            task_id=task_id,
            severity="info",
            details=details,
        )

        return self.log(event)

    def warning(
        self,
        event_type: str,
        *,
        user_id: str | None = None,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        event = AuditEvent(
            event_type,
            user_id=user_id,
            task_id=task_id,
            severity="warning",
            details=details,
        )

        return self.log(event)

    def error(
        self,
        event_type: str,
        *,
        user_id: str | None = None,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        event = AuditEvent(
            event_type,
            user_id=user_id,
            task_id=task_id,
            severity="error",
            details=details,
        )

        return self.log(event)

    def critical(
        self,
        event_type: str,
        *,
        user_id: str | None = None,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        event = AuditEvent(
            event_type,
            user_id=user_id,
            task_id=task_id,
            severity="critical",
            details=details,
        )

        return self.log(event)


def get_audit_logger(
    db: Session | None = None,
) -> AuditLogger:
    """
    Factory used by API routes and services.
    """

    return AuditLogger(db=db)
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    prompt: Mapped[str] = mapped_column(
        Text,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default=TaskStatus.PENDING.value,
        index=True,
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    workflow: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(512),
    )

    content_type: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    sensitivity: Mapped[str] = mapped_column(
        String(32),
        default="internal",
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )


class CapabilityExecutionModel(Base):
    __tablename__ = "capability_executions"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    task_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    capability_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    execution_time_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    payment_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    transaction_id: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    capability_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    amount: Mapped[float] = mapped_column(
        Float,
    )

    currency: Mapped[str] = mapped_column(
        String(16),
        default="ALGO",
    )

    network: Mapped[str] = mapped_column(
        String(64),
        default="algorand-testnet",
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
    )

    transaction_id: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        index=True,
    )

    payment_proof: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    user_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    task_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(32),
        default="info",
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )
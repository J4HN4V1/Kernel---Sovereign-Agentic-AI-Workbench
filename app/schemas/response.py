from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard response envelope used by the backend.

    Keeping a consistent response structure makes frontend
    integration much easier.
    """

    success: bool = True
    message: str = "Request completed successfully."
    data: T | None = None
    request_id: str | None = None
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """
    Standard error response.
    """

    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(
        default_factory=list
    )
    request_id: str | None = None
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: bool
    llm: bool
    payments: bool
    capabilities: bool
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0
    has_next: bool = False


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T] = Field(
        default_factory=list
    )
    pagination: Pagination
    request_id: str | None = None
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class ExecutionMetadata(BaseModel):
    """
    Metadata returned after an agent/capability execution.
    """

    execution_id: str
    task_id: str | None = None
    capability_id: str | None = None

    execution_time_ms: float = 0.0

    agents_used: list[str] = Field(
        default_factory=list
    )

    capabilities_used: list[str] = Field(
        default_factory=list
    )

    payment_required: bool = False
    payment_id: str | None = None
    transaction_id: str | None = None


class AgentResponse(BaseModel):
    """
    Standard response from an individual agent.
    """

    agent: str
    success: bool

    output: Any = None
    error: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class WorkflowResponse(BaseModel):
    """
    Represents the result of the multi-agent workflow.
    """

    workflow_id: str
    task_id: str

    status: str

    final_output: Any = None

    agents: list[AgentResponse] = Field(
        default_factory=list
    )

    execution: ExecutionMetadata | None = None

    error: str | None = None
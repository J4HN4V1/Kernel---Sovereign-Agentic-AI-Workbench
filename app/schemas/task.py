from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=20_000,
        description="Natural-language task requested by the user.",
    )

    document_ids: list[str] = Field(
        default_factory=list,
        description="Documents that should be available to the workflow.",
    )

    capability_ids: list[str] = Field(
        default_factory=list,
        description="Optional capabilities requested by the user.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional task metadata.",
    )


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    result: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    prompt: str
    status: str
    result: str | None = None
    error: str | None = None
    workflow: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str
    payment_required: bool = False
    payment_id: str | None = None


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None
    error: str | None = None
    workflow: dict[str, Any] | None = None
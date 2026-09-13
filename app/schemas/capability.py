from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    category: str
    version: str = "1.0.0"

    provider: str | None = None

    paid: bool = False
    price: float = 0.0
    currency: str = "ALGO"

    x402_enabled: bool = True
    blockchain: str = "algorand"

    input_types: list[str] = Field(
        default_factory=list
    )

    output_types: list[str] = Field(
        default_factory=list
    )

    privacy_level: str = "internal"

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class CapabilityListResponse(BaseModel):
    capabilities: list[CapabilityResponse]
    total: int


class CapabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    task_id: str | None = None

    input_data: dict[str, Any] = Field(
        default_factory=dict
    )

    require_payment: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class CapabilityExecutionResponse(BaseModel):
    success: bool

    capability_id: str

    task_id: str | None = None

    result: Any = None

    error: str | None = None

    execution_time_ms: float = 0.0

    payment_required: bool = False

    payment_id: str | None = None

    transaction_id: str | None = None
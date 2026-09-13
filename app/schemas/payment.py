from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    task_id: str | None = None

    amount: float = Field(
        ...,
        gt=0,
    )

    currency: str = Field(
        default="ALGO",
        min_length=1,
        max_length=16,
    )

    network: str = Field(
        default="algorand-testnet",
        min_length=1,
        max_length=64,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class PaymentProof(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
    )

    proof: str = Field(
        ...,
        min_length=1,
    )


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str | None = None
    capability_id: str

    amount: float
    currency: str
    network: str

    status: str

    transaction_id: str | None = None

    created_at: datetime
    updated_at: datetime


class PaymentRequirementResponse(BaseModel):
    payment_required: bool
    payment_id: str | None = None

    capability_id: str

    amount: float | None = None
    currency: str | None = None
    network: str | None = None

    recipient: str | None = None
    expires_at: int | None = None


class PaymentVerificationResponse(BaseModel):
    success: bool
    payment_id: str

    verified: bool = False
    settled: bool = False

    transaction_id: str | None = None

    network: str | None = None

    error: str | None = None
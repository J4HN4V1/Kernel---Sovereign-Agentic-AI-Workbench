from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CapabilityType(str, Enum):
    ANALYSIS = "analysis"
    OCR = "ocr"
    VISION = "vision"
    ENGINEERING = "engineering"
    REASONING = "reasoning"
    TRANSFORMATION = "transformation"
    OTHER = "other"


class PaymentProtocol(str, Enum):
    NONE = "none"
    X402 = "x402"


class Blockchain(str, Enum):
    NONE = "none"
    ALGORAND = "algorand"


class Capability(BaseModel):
    id: str = Field(..., min_length=1, max_length=200)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)

    capability_type: CapabilityType = CapabilityType.OTHER

    endpoint: str | None = None
    provider: str = Field(default="local", max_length=200)
    version: str = Field(default="1.0.0", max_length=50)

    enabled: bool = True

    requires_payment: bool = False
    price: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="ALGO", max_length=20)

    payment_protocol: PaymentProtocol = PaymentProtocol.NONE
    blockchain: Blockchain = Blockchain.NONE

    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)

    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_paid(self) -> bool:
        return self.requires_payment and self.price > 0

    def requires_x402(self) -> bool:
        return (
            self.is_paid()
            and self.payment_protocol == PaymentProtocol.X402
        )

    def requires_algorand(self) -> bool:
        return (
            self.requires_x402()
            and self.blockchain == Blockchain.ALGORAND
        )


class CapabilityRequest(BaseModel):
    capability_id: str = Field(..., min_length=1)

    input_data: dict[str, Any] = Field(default_factory=dict)

    task_id: str | None = None
    user_id: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityResponse(BaseModel):
    capability_id: str

    success: bool

    result: Any = None

    error: str | None = None

    payment_required: bool = False
    payment_id: str | None = None
    transaction_id: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
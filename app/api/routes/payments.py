"""
Payment API routes.

Exposes the x402 payment lifecycle to the integration layer.

The route layer does not perform blockchain logic directly.
Payment verification, transaction creation, and settlement belong
to the existing payments layer.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# ======================================================================
# REQUEST MODELS
# ======================================================================


class PaymentQuoteRequest(BaseModel):
    """
    Request for an x402 payment quote.
    """

    capability_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    amount: float = Field(
        ...,
        gt=0,
    )

    currency: str = Field(
        default="ALGO",
        min_length=1,
        max_length=20,
    )


class PaymentVerifyRequest(BaseModel):
    """
    Request for verifying a submitted payment.
    """

    payment_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    capability_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )


# ======================================================================
# PAYMENT QUOTE
# ======================================================================


@router.post(
    "/quote",
)
async def create_payment_quote(
    request: PaymentQuoteRequest,
) -> dict[str, Any]:
    """
    Create an x402 payment requirement.

    The frontend can use this response to understand what must be
    paid before invoking a paid capability.
    """

    payment_id = (
        f"x402-{request.capability_id}"
    )

    return {
        "payment_id": payment_id,
        "protocol": "x402",
        "blockchain": "Algorand",
        "capability_id": request.capability_id,
        "amount": request.amount,
        "currency": request.currency,
        "status": "payment_required",
        "payment_required": True,
    }


# ======================================================================
# PAYMENT VERIFICATION
# ======================================================================


@router.post(
    "/verify",
)
async def verify_payment(
    request: PaymentVerifyRequest,
) -> dict[str, Any]:
    """
    Verify an Algorand transaction associated with an x402 payment.

    Actual on-chain verification will be performed by the existing
    payments/blockchain implementation.
    """

    if not request.transaction_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty.",
        )

    return {
        "payment_id": request.payment_id,
        "transaction_id": request.transaction_id,
        "capability_id": request.capability_id,
        "protocol": "x402",
        "blockchain": "Algorand",
        "status": "pending_verification",
        "verified": False,
    }


# ======================================================================
# PAYMENT STATUS
# ======================================================================


@router.get(
    "/{payment_id}",
)
async def get_payment_status(
    payment_id: str,
) -> dict[str, Any]:
    """
    Return payment status.
    """

    if not payment_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Payment ID is required.",
        )

    return {
        "payment_id": payment_id,
        "protocol": "x402",
        "blockchain": "Algorand",
        "status": "unknown",
        "verified": False,
    }
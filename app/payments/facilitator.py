from __future__ import annotations

import logging
import os
from typing import Any

from app.payments.x402_client import PaymentRequest


logger = logging.getLogger(__name__)


class PaymentFacilitator:
    """
    Coordinates x402 payment verification and settlement.

    The facilitator sits between the x402 layer and the
    Algorand settlement layer.

    Flow:

        x402 proof
            ↓
        facilitator
            ↓
        verify
            ↓
        Algorand settlement
            ↓
        transaction ID
    """

    def __init__(
        self,
        *,
        enabled: bool | None = None,
    ) -> None:
        if enabled is None:
            enabled = (
                os.getenv(
                    "X402_ENABLED",
                    "false",
                ).lower()
                == "true"
            )

        self.enabled = enabled

    # ------------------------------------------------------------------
    # SETTLE
    # ------------------------------------------------------------------

    async def settle(
        self,
        payment_proof: str,
        payment_request: PaymentRequest,
    ) -> dict[str, Any]:
        """
        Verify and settle an x402 payment.

        In production, the proof is verified before the Algorand
        transaction is accepted as payment.
        """

        if not self.enabled:
            return {
                "success": False,
                "payment_id": payment_request.payment_id,
                "error": (
                    "x402 facilitator is disabled. "
                    "Set X402_ENABLED=true."
                ),
            }

        if not payment_proof:
            return {
                "success": False,
                "payment_id": payment_request.payment_id,
                "error": "Payment proof is missing.",
            }

        # --------------------------------------------------------------
        # VERIFY PROOF
        # --------------------------------------------------------------

        verification = self.verify_proof(
            payment_proof=payment_proof,
            payment_request=payment_request,
        )

        if not verification["success"]:
            return verification

        # --------------------------------------------------------------
        # ALGORAND SETTLEMENT
        # --------------------------------------------------------------

        try:
            from app.payments.algorand import (
                algorand_client,
            )

            result = await algorand_client.settle_payment(
                payment_proof=payment_proof,
                payment_request=payment_request,
            )

            if not isinstance(result, dict):
                return {
                    "success": bool(result),
                    "payment_id": (
                        payment_request.payment_id
                    ),
                }

            return {
                **result,
                "payment_id": (
                    payment_request.payment_id
                ),
            }

        except Exception as exc:
            logger.exception(
                "Payment settlement failed."
            )

            return {
                "success": False,
                "payment_id": (
                    payment_request.payment_id
                ),
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # VERIFY
    # ------------------------------------------------------------------

    def verify_proof(
        self,
        payment_proof: str,
        payment_request: PaymentRequest,
    ) -> dict[str, Any]:
        """
        Validate the basic x402 payment proof.

        Blockchain-specific verification is performed by the
        Algorand client.
        """

        if not payment_proof:
            return {
                "success": False,
                "error": "Empty payment proof.",
            }

        if payment_request.amount <= 0:
            return {
                "success": False,
                "error": "Invalid payment amount.",
            }

        if payment_request.blockchain.lower() != "algorand":
            return {
                "success": False,
                "error": (
                    "Unsupported settlement blockchain."
                ),
            }

        return {
            "success": True,
            "payment_id": payment_request.payment_id,
            "verified": True,
        }

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """
        Return facilitator status.
        """

        return {
            "protocol": "x402",
            "enabled": self.enabled,
            "settlement_network": "algorand",
            "ready": self.enabled,
        }


# ----------------------------------------------------------------------
# GLOBAL FACILITATOR
# ----------------------------------------------------------------------

payment_facilitator = PaymentFacilitator()
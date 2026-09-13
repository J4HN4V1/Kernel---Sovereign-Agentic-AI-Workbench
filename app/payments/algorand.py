from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

from app.payments.x402_client import PaymentRequest


logger = logging.getLogger(__name__)


class AlgorandClient:
    """
    Algorand settlement layer for x402 payments.

    Responsibilities:
    - validate Algorand payment information
    - verify transaction references
    - settle payments
    - expose transaction information

    The actual network interaction is isolated here so the rest
    of the backend remains independent of Algorand SDK details.
    """

    def __init__(self) -> None:
        self.network = os.getenv(
            "ALGORAND_NETWORK",
            "testnet",
        )

        self.algod_url = os.getenv(
            "ALGORAND_ALGOD_URL",
            "",
        )

        self.algod_token = os.getenv(
            "ALGORAND_ALGOD_TOKEN",
            "",
        )

        self.recipient_address = os.getenv(
            "ALGORAND_RECIPIENT_ADDRESS",
            "",
        )

        self.asset_id = int(
            os.getenv(
                "ALGORAND_ASSET_ID",
                "0",
            )
        )

    # ------------------------------------------------------------------
    # SETTLE PAYMENT
    # ------------------------------------------------------------------

    async def settle_payment(
        self,
        payment_proof: str,
        payment_request: PaymentRequest,
    ) -> dict[str, Any]:
        """
        Verify and settle an Algorand payment.

        payment_proof is expected to contain the transaction reference
        supplied by the x402 payment flow.
        """

        if not payment_proof:
            return {
                "success": False,
                "error": "Algorand payment proof is missing.",
            }

        if payment_request.blockchain.lower() != "algorand":
            return {
                "success": False,
                "error": (
                    "Payment request is not configured "
                    "for Algorand."
                ),
            }

        # --------------------------------------------------------------
        # VERIFY TRANSACTION
        # --------------------------------------------------------------

        verification = await self.verify_transaction(
            transaction_id=payment_proof,
            payment_request=payment_request,
        )

        if not verification["success"]:
            return verification

        return {
            "success": True,
            "payment_id": payment_request.payment_id,
            "transaction_id": payment_proof,
            "network": self.network,
            "settled": True,
        }

    # ------------------------------------------------------------------
    # VERIFY TRANSACTION
    # ------------------------------------------------------------------

    async def verify_transaction(
        self,
        transaction_id: str,
        payment_request: PaymentRequest,
    ) -> dict[str, Any]:
        """
        Verify an Algorand transaction reference.

        When an Algorand node is configured, this method is the
        integration point for querying the network.

        During local development, structural validation is performed
        so the complete backend can still run without a live node.
        """

        if not transaction_id:
            return {
                "success": False,
                "error": "Transaction ID is missing.",
            }

        if payment_request.amount <= 0:
            return {
                "success": False,
                "error": "Invalid payment amount.",
            }

        # Algorand transaction IDs are normally base32 strings.
        # We keep validation intentionally permissive because x402
        # providers may wrap the transaction reference.
        if len(transaction_id) < 8:
            return {
                "success": False,
                "error": "Invalid Algorand transaction reference.",
            }

        # --------------------------------------------------------------
        # LIVE NODE CONFIGURATION
        # --------------------------------------------------------------

        if self.algod_url:

            try:
                return await self._verify_with_algod(
                    transaction_id=transaction_id,
                    payment_request=payment_request,
                )

            except Exception as exc:
                logger.exception(
                    "Algorand node verification failed."
                )

                return {
                    "success": False,
                    "error": (
                        "Unable to verify transaction "
                        f"with Algorand node: {exc}"
                    ),
                }

        # --------------------------------------------------------------
        # LOCAL / DEVELOPMENT MODE
        # --------------------------------------------------------------

        return {
            "success": True,
            "verified": False,
            "development_mode": True,
            "transaction_id": transaction_id,
            "warning": (
                "Algorand node is not configured. "
                "Only structural transaction validation "
                "was performed."
            ),
        }

    # ------------------------------------------------------------------
    # ALGOD VERIFICATION
    # ------------------------------------------------------------------

    async def _verify_with_algod(
        self,
        transaction_id: str,
        payment_request: PaymentRequest,
    ) -> dict[str, Any]:
        """
        Verify a transaction through an Algorand node.

        The SDK import is lazy so the backend remains runnable when
        Algorand dependencies are not installed.
        """

        try:
            from algosdk.v2client import algod
        except ImportError as exc:
            raise RuntimeError(
                "py-algorand-sdk is required for live "
                "Algorand verification."
            ) from exc

        client = algod.AlgodClient(
            self.algod_token,
            self.algod_url,
        )

        transaction = client.pending_transaction_info(
            transaction_id
        )

        if not transaction:
            return {
                "success": False,
                "error": "Transaction was not found.",
            }

        confirmed_round = transaction.get(
            "confirmed-round",
            0,
        )

        if confirmed_round <= 0:
            return {
                "success": False,
                "error": "Transaction is not confirmed.",
            }

        # --------------------------------------------------------------
        # AMOUNT VALIDATION
        # --------------------------------------------------------------

        requested_amount = payment_request.amount

        # Algorand native ALGO uses microAlgos.
        expected_microalgos = int(
            round(
                requested_amount * 1_000_000
            )
        )

        transaction_amount = transaction.get(
            "txn",
            {},
        ).get(
            "amt",
            0,
        )

        if self.asset_id == 0:
            if transaction_amount < expected_microalgos:
                return {
                    "success": False,
                    "error": (
                        "Transaction amount is lower than "
                        "the required payment."
                    ),
                }

        # --------------------------------------------------------------
        # RECIPIENT VALIDATION
        # --------------------------------------------------------------

        receiver = (
            transaction.get(
                "txn",
                {},
            ).get(
                "rcv",
                "",
            )
        )

        if (
            self.recipient_address
            and receiver
            and receiver != self.recipient_address
        ):
            return {
                "success": False,
                "error": (
                    "Transaction recipient does not match "
                    "the configured recipient."
                ),
            }

        return {
            "success": True,
            "verified": True,
            "transaction_id": transaction_id,
            "confirmed_round": confirmed_round,
            "network": self.network,
        }

    # ------------------------------------------------------------------
    # TRANSACTION HASH
    # ------------------------------------------------------------------

    @staticmethod
    def transaction_fingerprint(
        transaction_id: str,
    ) -> str:
        """
        Generate a safe internal fingerprint for audit logs.

        The actual transaction ID should not be unnecessarily exposed
        in logs.
        """

        return hashlib.sha256(
            transaction_id.encode("utf-8")
        ).hexdigest()

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """
        Return Algorand integration status.
        """

        return {
            "network": self.network,
            "algod_configured": bool(
                self.algod_url
            ),
            "recipient_configured": bool(
                self.recipient_address
            ),
            "asset_id": self.asset_id,
            "live_verification": bool(
                self.algod_url
            ),
            "ready": bool(
                self.algod_url
                and self.recipient_address
            ),
        }


# ----------------------------------------------------------------------
# GLOBAL CLIENT
# ----------------------------------------------------------------------

algorand_client = AlgorandClient()
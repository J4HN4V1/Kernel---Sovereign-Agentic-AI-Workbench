from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable

from app.capabilities.models import (
    Capability,
    CapabilityRequest,
    CapabilityResponse,
)


class CapabilityClient:
    """
    Executes registered capabilities.

    Local capabilities are executed directly.

    Remote/paid capabilities are routed through the payment-aware
    capability path. The actual x402 payment implementation remains
    inside app/payments/x402_client.py, keeping responsibilities
    separated.
    """

    def __init__(
        self,
        registry,
    ) -> None:
        self.registry = registry
        self._handlers: dict[
            str,
            Callable[..., Any],
        ] = {}

    # ------------------------------------------------------------------
    # REGISTER HANDLER
    # ------------------------------------------------------------------

    def register_handler(
        self,
        capability_id: str,
        handler: Callable[..., Any],
    ) -> None:
        """
        Attach an executable Python handler to a capability.
        """

        if not capability_id.strip():
            raise ValueError(
                "Capability ID cannot be empty."
            )

        if not callable(handler):
            raise TypeError(
                "Capability handler must be callable."
            )

        if not self.registry.exists(
            capability_id
        ):
            raise KeyError(
                f"Capability is not registered: {capability_id}"
            )

        self._handlers[capability_id] = handler

    # ------------------------------------------------------------------
    # EXECUTE
    # ------------------------------------------------------------------

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResponse:
        """
        Execute a capability request.
        """

        capability = self.registry.get(
            request.capability_id
        )

        if capability is None:
            return CapabilityResponse(
                capability_id=request.capability_id,
                success=False,
                error=(
                    f"Capability not found: "
                    f"{request.capability_id}"
                ),
            )

        if not capability.enabled:
            return CapabilityResponse(
                capability_id=capability.id,
                success=False,
                error="Capability is disabled.",
            )

        handler = self._handlers.get(
            capability.id
        )

        if handler is None:
            return CapabilityResponse(
                capability_id=capability.id,
                success=False,
                error=(
                    "No execution handler registered "
                    "for this capability."
                ),
            )

        # --------------------------------------------------------------
        # PAID CAPABILITY
        # --------------------------------------------------------------

        if capability.is_paid():

            payment_result = await self._handle_payment(
                capability,
                request,
            )

            if not payment_result["success"]:
                return CapabilityResponse(
                    capability_id=capability.id,
                    success=False,
                    error=payment_result.get(
                        "error",
                        "Payment failed.",
                    ),
                    payment_required=True,
                    payment_id=payment_result.get(
                        "payment_id"
                    ),
                    transaction_id=payment_result.get(
                        "transaction_id"
                    ),
                )

        # --------------------------------------------------------------
        # EXECUTE HANDLER
        # --------------------------------------------------------------

        try:
            result = handler(
                request.input_data
            )

            if inspect.isawaitable(result):
                result = await result

            return CapabilityResponse(
                capability_id=capability.id,
                success=True,
                result=result,
                payment_required=capability.is_paid(),
                metadata={
                    "provider": capability.provider,
                    "version": capability.version,
                },
            )

        except Exception as exc:
            return CapabilityResponse(
                capability_id=capability.id,
                success=False,
                error=str(exc),
                payment_required=capability.is_paid(),
            )

    # ------------------------------------------------------------------
    # SYNC EXECUTION
    # ------------------------------------------------------------------

    def execute_sync(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResponse:
        """
        Synchronous wrapper for non-async callers.
        """

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.execute(request)
            )

        raise RuntimeError(
            "execute_sync() cannot be called from an "
            "already-running event loop. Use await execute()."
        )

    # ------------------------------------------------------------------
    # PAYMENT
    # ------------------------------------------------------------------

    async def _handle_payment(
        self,
        capability: Capability,
        request: CapabilityRequest,
    ) -> dict[str, Any]:
        """
        Route payment through the x402 payment client.

        Import is intentionally lazy so the capability subsystem
        remains usable when payment configuration is unavailable.
        """

        if not capability.requires_x402():
            return {
                "success": False,
                "error": (
                    "Paid capability does not have "
                    "x402 configured."
                ),
            }

        try:
            from app.payments.x402_client import (
                x402_client,
            )
        except ImportError:
            return {
                "success": False,
                "error": (
                    "x402 payment client is unavailable."
                ),
            }

        try:
            result = x402_client.create_payment(
                capability=capability,
                request=request,
            )

            if inspect.isawaitable(result):
                result = await result

            if isinstance(result, dict):
                return result

            return {
                "success": bool(result),
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # CAPABILITY INFO
    # ------------------------------------------------------------------

    def get_capability(
        self,
        capability_id: str,
    ) -> Capability | None:
        """
        Return capability metadata.
        """

        return self.registry.get(
            capability_id
        )

    # ------------------------------------------------------------------
    # HANDLER STATUS
    # ------------------------------------------------------------------

    def has_handler(
        self,
        capability_id: str,
    ) -> bool:
        """
        Check whether a capability has an executable handler.
        """

        return capability_id in self._handlers

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def health(
        self,
    ) -> dict[str, Any]:
        """
        Return execution-layer health information.
        """

        capabilities = self.registry.list_all()

        return {
            "registered_capabilities": len(
                capabilities
            ),
            "handlers": len(
                self._handlers
            ),
            "ready": all(
                capability.id in self._handlers
                for capability in capabilities
                if capability.enabled
            ),
            "capabilities": [
                {
                    "id": capability.id,
                    "enabled": capability.enabled,
                    "handler_registered": (
                        capability.id
                        in self._handlers
                    ),
                    "paid": capability.is_paid(),
                    "x402": capability.requires_x402(),
                }
                for capability in capabilities
            ],
        }


# ----------------------------------------------------------------------
# IMPORT REGISTRY AFTER CLASS DEFINITION
# ----------------------------------------------------------------------

from app.capabilities.registry import (
    capability_registry,
)


capability_client = CapabilityClient(
    capability_registry
)
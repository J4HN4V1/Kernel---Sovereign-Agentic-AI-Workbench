from __future__ import annotations

from threading import RLock
from typing import Any

from app.capabilities.models import Capability


class CapabilityRegistry:
    """
    Central registry for all capabilities available to the system.

    The registry is responsible only for:
    - registering capabilities
    - removing capabilities
    - retrieving capabilities
    - listing capabilities
    - enabling/disabling capabilities

    It does NOT execute capabilities.
    Execution is handled by client.py.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._lock = RLock()

    # ------------------------------------------------------------------
    # REGISTER
    # ------------------------------------------------------------------

    def register(
        self,
        capability: Capability,
    ) -> Capability:
        """
        Register or replace a capability.
        """

        if not capability.id.strip():
            raise ValueError(
                "Capability ID cannot be empty."
            )

        with self._lock:
            self._capabilities[capability.id] = capability

        return capability

    # ------------------------------------------------------------------
    # UNREGISTER
    # ------------------------------------------------------------------

    def unregister(
        self,
        capability_id: str,
    ) -> bool:
        """
        Remove a capability from the registry.

        Returns True if removed, otherwise False.
        """

        with self._lock:
            if capability_id not in self._capabilities:
                return False

            del self._capabilities[capability_id]

            return True

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get(
        self,
        capability_id: str,
    ) -> Capability | None:
        """
        Retrieve a capability by ID.
        """

        with self._lock:
            return self._capabilities.get(
                capability_id
            )

    # ------------------------------------------------------------------
    # REQUIRE
    # ------------------------------------------------------------------

    def require(
        self,
        capability_id: str,
    ) -> Capability:
        """
        Retrieve a capability or raise an explicit error.
        """

        capability = self.get(
            capability_id
        )

        if capability is None:
            raise KeyError(
                f"Capability not found: {capability_id}"
            )

        return capability

    # ------------------------------------------------------------------
    # EXISTS
    # ------------------------------------------------------------------

    def exists(
        self,
        capability_id: str,
    ) -> bool:
        """
        Check whether a capability exists.
        """

        with self._lock:
            return capability_id in self._capabilities

    # ------------------------------------------------------------------
    # ENABLE / DISABLE
    # ------------------------------------------------------------------

    def enable(
        self,
        capability_id: str,
    ) -> Capability:
        """
        Enable a registered capability.
        """

        with self._lock:
            capability = self.require(
                capability_id
            )

            capability.enabled = True

            return capability

    def disable(
        self,
        capability_id: str,
    ) -> Capability:
        """
        Disable a registered capability.
        """

        with self._lock:
            capability = self.require(
                capability_id
            )

            capability.enabled = False

            return capability

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------

    def list_all(
        self,
        *,
        enabled_only: bool = False,
    ) -> list[Capability]:
        """
        Return all registered capabilities.
        """

        with self._lock:

            capabilities = list(
                self._capabilities.values()
            )

            if enabled_only:
                capabilities = [
                    capability
                    for capability in capabilities
                    if capability.enabled
                ]

            return capabilities

    # ------------------------------------------------------------------
    # FILTER
    # ------------------------------------------------------------------

    def find(
        self,
        *,
        capability_type: str | None = None,
        provider: str | None = None,
        tag: str | None = None,
        enabled_only: bool = True,
    ) -> list[Capability]:
        """
        Find capabilities matching the supplied filters.
        """

        capabilities = self.list_all(
            enabled_only=enabled_only
        )

        results: list[Capability] = []

        for capability in capabilities:

            if (
                capability_type is not None
                and capability.capability_type.value
                != capability_type
            ):
                continue

            if (
                provider is not None
                and capability.provider
                != provider
            ):
                continue

            if (
                tag is not None
                and tag not in capability.tags
            ):
                continue

            results.append(
                capability
            )

        return results

    # ------------------------------------------------------------------
    # COUNT
    # ------------------------------------------------------------------

    def count(
        self,
        *,
        enabled_only: bool = False,
    ) -> int:
        """
        Return number of registered capabilities.
        """

        return len(
            self.list_all(
                enabled_only=enabled_only
            )
        )

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Export the registry for diagnostics/API responses.
        """

        return {
            "total": self.count(),
            "enabled": self.count(
                enabled_only=True
            ),
            "capabilities": [
                capability.model_dump(
                    mode="json"
                )
                for capability in self.list_all()
            ],
        }


# Global registry used by the application.
capability_registry = CapabilityRegistry()
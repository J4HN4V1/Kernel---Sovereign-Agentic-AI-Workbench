from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any

from app.capabilities.models import Capability
from app.capabilities.registry import capability_registry


logger = logging.getLogger(__name__)


class CapabilityDiscovery:
    """
    Discovers capabilities available to the backend.

    Discovery sources:
    1. Built-in/local capabilities
    2. Capability packages inside /capabilities

    Discovery only registers capabilities.
    It does not execute them.
    """

    def __init__(
        self,
        capabilities_directory: str = "capabilities",
    ) -> None:
        self.capabilities_directory = Path(
            capabilities_directory
        )

    # ------------------------------------------------------------------
    # DISCOVER ALL
    # ------------------------------------------------------------------

    def discover(self) -> list[Capability]:
        """
        Discover and register all available capabilities.
        """

        discovered: list[Capability] = []

        if not self.capabilities_directory.exists():
            logger.warning(
                "Capabilities directory does not exist: %s",
                self.capabilities_directory,
            )
            return discovered

        for directory in sorted(
            self.capabilities_directory.iterdir()
        ):
            if not directory.is_dir():
                continue

            if directory.name.startswith("_"):
                continue

            try:
                capability = self._discover_package(
                    directory
                )

                if capability is None:
                    continue

                capability_registry.register(
                    capability
                )

                discovered.append(
                    capability
                )

                logger.info(
                    "Registered capability: %s",
                    capability.id,
                )

            except Exception:
                logger.exception(
                    "Failed to discover capability: %s",
                    directory,
                )

        return discovered

    # ------------------------------------------------------------------
    # DISCOVER PACKAGE
    # ------------------------------------------------------------------

    def _discover_package(
        self,
        directory: Path,
    ) -> Capability | None:
        """
        Discover a capability from a package directory.

        A capability package may expose:
            capability
        or
            get_capability()
        """

        package_name = directory.name

        init_file = directory / "__init__.py"

        if not init_file.exists():
            logger.warning(
                "Skipping %s: missing __init__.py",
                directory,
            )
            return None

        try:
            module = importlib.import_module(
                f"capabilities.{package_name}"
            )
        except Exception as exc:
            logger.error(
                "Unable to import capability %s: %s",
                package_name,
                exc,
            )
            return None

        # --------------------------------------------------------------
        # Preferred: capability object
        # --------------------------------------------------------------

        capability = getattr(
            module,
            "capability",
            None,
        )

        if isinstance(
            capability,
            Capability,
        ):
            return capability

        # --------------------------------------------------------------
        # Alternative: get_capability()
        # --------------------------------------------------------------

        factory = getattr(
            module,
            "get_capability",
            None,
        )

        if callable(factory):

            try:
                capability = factory()

                if isinstance(
                    capability,
                    Capability,
                ):
                    return capability

            except Exception:
                logger.exception(
                    "Capability factory failed: %s",
                    package_name,
                )

        # --------------------------------------------------------------
        # Automatic metadata discovery
        # --------------------------------------------------------------

        metadata = getattr(
            module,
            "CAPABILITY",
            None,
        )

        if isinstance(
            metadata,
            dict,
        ):
            try:
                return Capability(
                    **metadata
                )
            except Exception:
                logger.exception(
                    "Invalid CAPABILITY metadata: %s",
                    package_name,
                )

        logger.warning(
            "No valid capability definition found in %s",
            package_name,
        )

        return None

    # ------------------------------------------------------------------
    # DISCOVER SINGLE PACKAGE
    # ------------------------------------------------------------------

    def discover_one(
        self,
        capability_name: str,
    ) -> Capability | None:
        """
        Discover one specific capability.
        """

        directory = (
            self.capabilities_directory
            / capability_name
        )

        if not directory.exists():
            return None

        capability = self._discover_package(
            directory
        )

        if capability is not None:
            capability_registry.register(
                capability
            )

        return capability

    # ------------------------------------------------------------------
    # VALIDATE
    # ------------------------------------------------------------------

    @staticmethod
    def validate(
        capability: Capability,
    ) -> bool:
        """
        Validate a capability before registration.
        """

        if not capability.id.strip():
            return False

        if not capability.name.strip():
            return False

        if capability.price < 0:
            return False

        if capability.requires_payment:

            if not capability.payment_protocol.value:
                return False

        return True

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def health(
        self,
    ) -> dict[str, Any]:
        """
        Return capability discovery status.
        """

        capabilities = (
            capability_registry.list_all()
        )

        return {
            "directory": str(
                self.capabilities_directory
            ),
            "directory_exists": (
                self.capabilities_directory.exists()
            ),
            "registered": len(
                capabilities
            ),
            "enabled": len(
                [
                    capability
                    for capability in capabilities
                    if capability.enabled
                ]
            ),
            "capabilities": [
                {
                    "id": capability.id,
                    "name": capability.name,
                    "enabled": capability.enabled,
                    "provider": capability.provider,
                }
                for capability in capabilities
            ],
        }


# Global discovery service.
capability_discovery = CapabilityDiscovery()
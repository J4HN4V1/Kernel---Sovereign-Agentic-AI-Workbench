"""
Engineering analytics capability.

Provides local analysis of engineering text/data without sending
confidential enterprise information to external services.
"""

from __future__ import annotations

import math
import re
from typing import Any


CAPABILITY_ID = "engineering_analytics"
CAPABILITY_NAME = "Engineering Analytics"


class EngineeringAnalyticsService:
    """
    Local engineering analysis capability.

    Supports basic engineering calculations and structured analysis.
    """

    def execute(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute an engineering analysis request.
        """

        if not isinstance(data, dict):
            raise ValueError(
                "Engineering input must be an object."
            )

        operation = data.get(
            "operation",
            "analyze",
        )

        if operation == "stress":
            return self.calculate_stress(
                data
            )

        if operation == "strain":
            return self.calculate_strain(
                data
            )

        if operation == "factor_of_safety":
            return self.calculate_factor_of_safety(
                data
            )

        if operation == "power":
            return self.calculate_power(
                data
            )

        if operation == "analyze":
            return self.analyze(
                data
            )

        raise ValueError(
            f"Unsupported engineering operation: {operation}"
        )

    # ==================================================================
    # STRESS
    # ==================================================================

    @staticmethod
    def calculate_stress(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        force = float(
            data["force"]
        )

        area = float(
            data["area"]
        )

        if area <= 0:
            raise ValueError(
                "Area must be greater than zero."
            )

        stress = force / area

        return {
            "operation": "stress",
            "force": force,
            "area": area,
            "stress": stress,
            "unit": data.get(
                "stress_unit",
                "Pa",
            ),
        }

    # ==================================================================
    # STRAIN
    # ==================================================================

    @staticmethod
    def calculate_strain(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        change_in_length = float(
            data["change_in_length"]
        )

        original_length = float(
            data["original_length"]
        )

        if original_length <= 0:
            raise ValueError(
                "Original length must be greater than zero."
            )

        strain = (
            change_in_length
            / original_length
        )

        return {
            "operation": "strain",
            "change_in_length": change_in_length,
            "original_length": original_length,
            "strain": strain,
        }

    # ==================================================================
    # FACTOR OF SAFETY
    # ==================================================================

    @staticmethod
    def calculate_factor_of_safety(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        strength = float(
            data["material_strength"]
        )

        applied_stress = float(
            data["applied_stress"]
        )

        if applied_stress <= 0:
            raise ValueError(
                "Applied stress must be greater than zero."
            )

        factor = (
            strength
            / applied_stress
        )

        return {
            "operation": "factor_of_safety",
            "material_strength": strength,
            "applied_stress": applied_stress,
            "factor_of_safety": factor,
            "safe": factor >= 1.0,
        }

    # ==================================================================
    # POWER
    # ==================================================================

    @staticmethod
    def calculate_power(
        data: dict[str, Any],
    ) -> dict[str, Any]:

        voltage = float(
            data["voltage"]
        )

        current = float(
            data["current"]
        )

        power = (
            voltage
            * current
        )

        return {
            "operation": "power",
            "voltage": voltage,
            "current": current,
            "power": power,
            "unit": "W",
        }

    # ==================================================================
    # GENERAL ANALYSIS
    # ==================================================================

    @staticmethod
    def analyze(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Perform lightweight structural analysis of engineering input.
        """

        text = str(
            data.get(
                "text",
                ""
            )
        )

        numbers = [
            float(value)
            for value in re.findall(
                r"[-+]?\d*\.?\d+",
                text,
            )
        ]

        return {
            "operation": "analyze",
            "input_text": text,
            "numeric_values": numbers,
            "numeric_value_count": len(numbers),
            "statistics": (
                EngineeringAnalyticsService
                ._statistics(numbers)
            ),
        }

    @staticmethod
    def _statistics(
        values: list[float],
    ) -> dict[str, float | None]:

        if not values:
            return {
                "min": None,
                "max": None,
                "mean": None,
            }

        return {
            "min": min(values),
            "max": max(values),
            "mean": sum(values)
            / len(values),
        }


engineering_analytics_service = (
    EngineeringAnalyticsService()
)


def execute(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Entry point used by the capability registry.
    """

    return engineering_analytics_service.execute(
        data
    )
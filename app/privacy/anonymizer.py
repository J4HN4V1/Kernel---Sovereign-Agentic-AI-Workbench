from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnonymizationResult:
    """
    Result produced by the privacy anonymization layer.
    """

    text: str
    replacements: int
    detected_types: list[str] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class Anonymizer:
    """
    Local, deterministic PII anonymizer.

    Sensitive information is replaced before data is passed to
    downstream agents or external capabilities.
    """

    PATTERNS = {
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),

        "phone": re.compile(
            r"(?<!\d)"
            r"(?:\+?\d{1,3}[\s.-]?)?"
            r"(?:\(?\d{3}\)?[\s.-]?)?"
            r"\d{3}[\s.-]?\d{4}"
            r"(?!\d)"
        ),

        "credit_card": re.compile(
            r"\b(?:\d[ -]*?){13,19}\b"
        ),

        "aadhaar": re.compile(
            r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"
        ),

        "pan": re.compile(
            r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            re.IGNORECASE,
        ),

        "ip_address": re.compile(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        ),

        "url": re.compile(
            r"\bhttps?://[^\s]+",
            re.IGNORECASE,
        ),
    }

    # ------------------------------------------------------------------
    # ANONYMIZE
    # ------------------------------------------------------------------

    def anonymize(
        self,
        text: str,
    ) -> AnonymizationResult:
        """
        Replace detected sensitive values with typed placeholders.
        """

        if not text:
            return AnonymizationResult(
                text="",
                replacements=0,
            )

        result = text
        replacements = 0
        detected_types: list[str] = []

        # Order matters: more specific patterns first.
        ordered_types = [
            "credit_card",
            "aadhaar",
            "email",
            "pan",
            "phone",
            "ip_address",
            "url",
        ]

        for pii_type in ordered_types:

            pattern = self.PATTERNS[pii_type]

            def replace(
                match: re.Match[str],
                *,
                current_type: str = pii_type,
            ) -> str:

                nonlocal replacements

                replacements += 1

                if current_type not in detected_types:
                    detected_types.append(
                        current_type
                    )

                return self._placeholder(
                    current_type
                )

            result = pattern.sub(
                replace,
                result,
            )

        return AnonymizationResult(
            text=result,
            replacements=replacements,
            detected_types=detected_types,
            metadata={
                "anonymized": replacements > 0,
                "method": "local_regex",
            },
        )

    # ------------------------------------------------------------------
    # DE-ANONYMIZE
    # ------------------------------------------------------------------

    def anonymize_with_mapping(
        self,
        text: str,
    ) -> tuple[
        AnonymizationResult,
        dict[str, str],
    ]:
        """
        Replace sensitive values with unique placeholders.

        The returned mapping can be kept inside the trusted backend
        and must never be exposed to untrusted external services.
        """

        if not text:
            return (
                AnonymizationResult(
                    text="",
                    replacements=0,
                ),
                {},
            )

        result = text
        mapping: dict[str, str] = {}
        detected_types: list[str] = []
        counters: dict[str, int] = {}

        ordered_types = [
            "credit_card",
            "aadhaar",
            "email",
            "pan",
            "phone",
            "ip_address",
            "url",
        ]

        replacements = 0

        for pii_type in ordered_types:

            pattern = self.PATTERNS[pii_type]

            def replace(
                match: re.Match[str],
                *,
                current_type: str = pii_type,
            ) -> str:

                nonlocal replacements

                original = match.group(0)

                # Reuse an existing placeholder for duplicate values.
                for placeholder, value in mapping.items():
                    if value == original:
                        return placeholder

                counters[current_type] = (
                    counters.get(
                        current_type,
                        0,
                    )
                    + 1
                )

                placeholder = (
                    f"<{current_type.upper()}_"
                    f"{counters[current_type]}>"
                )

                mapping[placeholder] = original
                replacements += 1

                if current_type not in detected_types:
                    detected_types.append(
                        current_type
                    )

                return placeholder

            result = pattern.sub(
                replace,
                result,
            )

        return (
            AnonymizationResult(
                text=result,
                replacements=replacements,
                detected_types=detected_types,
                metadata={
                    "anonymized": replacements > 0,
                    "method": "local_regex",
                    "mapping_entries": len(mapping),
                },
            ),
            mapping,
        )

    # ------------------------------------------------------------------
    # RESTORE
    # ------------------------------------------------------------------

    @staticmethod
    def restore(
        text: str,
        mapping: dict[str, str],
    ) -> str:
        """
        Restore placeholders using a trusted local mapping.
        """

        if not text or not mapping:
            return text

        restored = text

        # Longest placeholders first prevents partial replacement.
        for placeholder in sorted(
            mapping,
            key=len,
            reverse=True,
        ):
            restored = restored.replace(
                placeholder,
                mapping[placeholder],
            )

        return restored

    # ------------------------------------------------------------------
    # DETECT
    # ------------------------------------------------------------------

    def detect(
        self,
        text: str,
    ) -> list[str]:
        """
        Return the types of sensitive information detected.
        """

        if not text:
            return []

        detected: list[str] = []

        for pii_type, pattern in self.PATTERNS.items():

            if pattern.search(text):
                detected.append(
                    pii_type
                )

        return detected

    # ------------------------------------------------------------------
    # PLACEHOLDER
    # ------------------------------------------------------------------

    @staticmethod
    def _placeholder(
        pii_type: str,
    ) -> str:
        """
        Create a stable placeholder for a detected PII type.
        """

        return (
            f"<{pii_type.upper()}>"
        )


# ----------------------------------------------------------------------
# GLOBAL PRIVACY SERVICE
# ----------------------------------------------------------------------

anonymizer = Anonymizer()
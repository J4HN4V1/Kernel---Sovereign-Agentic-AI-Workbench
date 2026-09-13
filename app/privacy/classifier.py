from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field


class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ClassificationResult(BaseModel):
    level: SensitivityLevel
    score: float = Field(ge=0.0, le=1.0)
    detected_categories: list[str] = Field(
        default_factory=list
    )
    reason: str


class PrivacyClassifier:
    """
    Local classifier for determining how sensitive a piece of
    enterprise data is.

    Higher sensitivity means stronger privacy controls should be
    applied before the data reaches an external capability.
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
        "aadhaar": re.compile(
            r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"
        ),
        "pan": re.compile(
            r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            re.IGNORECASE,
        ),
        "credit_card": re.compile(
            r"\b(?:\d[ -]*?){13,19}\b"
        ),
        "ip_address": re.compile(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        ),
    }

    SENSITIVE_KEYWORDS = {
        "confidential",
        "restricted",
        "secret",
        "classified",
        "proprietary",
        "internal only",
        "trade secret",
        "password",
        "api key",
        "private key",
        "access token",
        "authentication",
        "financial",
        "bank account",
        "salary",
        "vendor negotiation",
        "defence",
        "defense",
        "military",
        "security clearance",
    }

    # ------------------------------------------------------------------
    # CLASSIFY
    # ------------------------------------------------------------------

    def classify(
        self,
        text: str,
    ) -> ClassificationResult:
        """
        Classify text according to its sensitivity.
        """

        if not text or not text.strip():
            return ClassificationResult(
                level=SensitivityLevel.PUBLIC,
                score=0.0,
                detected_categories=[],
                reason="No sensitive content detected.",
            )

        normalized = text.lower()

        detected: list[str] = []
        score = 0.0

        # --------------------------------------------------------------
        # PII DETECTION
        # --------------------------------------------------------------

        for category, pattern in self.PATTERNS.items():

            if pattern.search(text):
                detected.append(category)

                if category in {
                    "aadhaar",
                    "credit_card",
                }:
                    score += 0.45
                else:
                    score += 0.20

        # --------------------------------------------------------------
        # SENSITIVE KEYWORDS
        # --------------------------------------------------------------

        for keyword in self.SENSITIVE_KEYWORDS:

            if keyword in normalized:

                category = f"keyword:{keyword}"

                detected.append(category)

                if keyword in {
                    "password",
                    "api key",
                    "private key",
                    "access token",
                    "classified",
                    "trade secret",
                }:
                    score += 0.45
                else:
                    score += 0.25

        # --------------------------------------------------------------
        # CAP SCORE
        # --------------------------------------------------------------

        score = min(
            1.0,
            score,
        )

        # --------------------------------------------------------------
        # DETERMINE LEVEL
        # --------------------------------------------------------------

        if score >= 0.75:
            level = SensitivityLevel.RESTRICTED

        elif score >= 0.45:
            level = SensitivityLevel.CONFIDENTIAL

        elif score >= 0.20:
            level = SensitivityLevel.INTERNAL

        else:
            level = SensitivityLevel.PUBLIC

        if detected:
            reason = (
                "Sensitive information detected: "
                + ", ".join(detected)
            )
        else:
            reason = (
                "No known sensitive information patterns "
                "were detected."
            )

        return ClassificationResult(
            level=level,
            score=score,
            detected_categories=detected,
            reason=reason,
        )

    # ------------------------------------------------------------------
    # CONVENIENCE METHODS
    # ------------------------------------------------------------------

    def is_sensitive(
        self,
        text: str,
    ) -> bool:
        """
        Return True when data should receive privacy protection.
        """

        result = self.classify(text)

        return result.level in {
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.RESTRICTED,
        }

    def requires_anonymization(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether anonymization should be applied.
        """

        result = self.classify(text)

        return bool(
            result.detected_categories
        )

    def requires_local_processing(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether the data should remain inside the
        trusted local environment.
        """

        result = self.classify(text)

        return result.level == SensitivityLevel.RESTRICTED


# ----------------------------------------------------------------------
# GLOBAL CLASSIFIER
# ----------------------------------------------------------------------

privacy_classifier = PrivacyClassifier()
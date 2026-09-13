from __future__ import annotations

from dataclasses import dataclass

from app.privacy.classifier import (
    ClassificationResult,
    SensitivityLevel,
    privacy_classifier,
)


@dataclass(frozen=True)
class PrivacyDecision:
    """
    Decision produced by the privacy policy engine.
    """

    allow_external: bool
    anonymize: bool
    require_local: bool
    allow_paid_capability: bool
    classification: ClassificationResult
    reason: str


class PrivacyPolicy:
    """
    Enforces privacy rules before data is sent to agents,
    capabilities, or paid external services.

    Core rule:

        PUBLIC / INTERNAL
            -> external processing may be allowed

        CONFIDENTIAL
            -> anonymize before external processing

        RESTRICTED
            -> keep processing local
    """

    # ------------------------------------------------------------------
    # EVALUATE
    # ------------------------------------------------------------------

    def evaluate(
        self,
        text: str,
        *,
        external: bool = False,
        paid: bool = False,
    ) -> PrivacyDecision:
        """
        Evaluate whether a piece of data can be processed by a
        requested execution path.
        """

        classification = (
            privacy_classifier.classify(text)
        )

        level = classification.level

        # --------------------------------------------------------------
        # PUBLIC
        # --------------------------------------------------------------

        if level == SensitivityLevel.PUBLIC:

            return PrivacyDecision(
                allow_external=True,
                anonymize=False,
                require_local=False,
                allow_paid_capability=True,
                classification=classification,
                reason="Public data can be processed normally.",
            )

        # --------------------------------------------------------------
        # INTERNAL
        # --------------------------------------------------------------

        if level == SensitivityLevel.INTERNAL:

            if external:
                return PrivacyDecision(
                    allow_external=True,
                    anonymize=False,
                    require_local=False,
                    allow_paid_capability=True,
                    classification=classification,
                    reason=(
                        "Internal data may be processed externally "
                        "when permitted by the application."
                    ),
                )

            return PrivacyDecision(
                allow_external=True,
                anonymize=False,
                require_local=False,
                allow_paid_capability=True,
                classification=classification,
                reason="Internal data is permitted.",
            )

        # --------------------------------------------------------------
        # CONFIDENTIAL
        # --------------------------------------------------------------

        if level == SensitivityLevel.CONFIDENTIAL:

            if external:

                # Confidential information must be anonymized
                # before leaving the trusted environment.
                return PrivacyDecision(
                    allow_external=True,
                    anonymize=True,
                    require_local=False,
                    allow_paid_capability=not paid,
                    classification=classification,
                    reason=(
                        "Confidential data requires anonymization "
                        "before external processing."
                    ),
                )

            return PrivacyDecision(
                allow_external=True,
                anonymize=False,
                require_local=False,
                allow_paid_capability=True,
                classification=classification,
                reason=(
                    "Confidential data can be processed locally "
                    "without anonymization."
                ),
            )

        # --------------------------------------------------------------
        # RESTRICTED
        # --------------------------------------------------------------

        return PrivacyDecision(
            allow_external=False,
            anonymize=False,
            require_local=True,
            allow_paid_capability=False,
            classification=classification,
            reason=(
                "Restricted data must remain inside the trusted "
                "local environment."
            ),
        )

    # ------------------------------------------------------------------
    # CHECK EXTERNAL ACCESS
    # ------------------------------------------------------------------

    def can_send_external(
        self,
        text: str,
    ) -> bool:
        """
        Check whether data may leave the local environment.
        """

        decision = self.evaluate(
            text,
            external=True,
        )

        return decision.allow_external

    # ------------------------------------------------------------------
    # CHECK PAYMENT
    # ------------------------------------------------------------------

    def can_use_paid_capability(
        self,
        text: str,
    ) -> bool:
        """
        Check whether a paid capability may process the data.
        """

        decision = self.evaluate(
            text,
            external=True,
            paid=True,
        )

        return decision.allow_external and (
            decision.allow_paid_capability
        )

    # ------------------------------------------------------------------
    # CHECK LOCAL PROCESSING
    # ------------------------------------------------------------------

    def must_process_locally(
        self,
        text: str,
    ) -> bool:
        """
        Check whether processing must remain local.
        """

        decision = self.evaluate(
            text,
            external=True,
        )

        return decision.require_local

    # ------------------------------------------------------------------
    # FULL POLICY CHECK
    # ------------------------------------------------------------------

    def enforce(
        self,
        text: str,
        *,
        external: bool = False,
        paid: bool = False,
    ) -> PrivacyDecision:
        """
        Evaluate and enforce the privacy policy.

        Raises PermissionError when an operation is explicitly
        forbidden.
        """

        decision = self.evaluate(
            text,
            external=external,
            paid=paid,
        )

        if external and not decision.allow_external:
            raise PermissionError(
                "External processing is forbidden for "
                f"{decision.classification.level.value} data."
            )

        if paid and not decision.allow_paid_capability:
            raise PermissionError(
                "Paid external capability is not permitted "
                "for this data."
            )

        return decision


# ----------------------------------------------------------------------
# GLOBAL POLICY
# ----------------------------------------------------------------------

privacy_policy = PrivacyPolicy()
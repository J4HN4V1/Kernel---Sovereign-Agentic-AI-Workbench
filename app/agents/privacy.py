"""
Privacy Agent.

The Privacy Agent is the security gate between confidential enterprise
data and any external capability.

Its primary responsibilities are:

    1. Inspect task data before external transmission.
    2. Detect potentially sensitive information.
    3. Remove/redact sensitive values when possible.
    4. Produce an auditable privacy decision.
    5. Prevent external calls when policy requirements are not met.

Architecture:

    Local Task
        ↓
    Privacy Agent
        ↓
    ┌───────────────┐
    │ Safe to share?│
    └───────┬───────┘
            │
       ┌────┴────┐
      YES        NO
       ↓          ↓
   x402/tool   Block request
       ↓
   External
   capability

IMPORTANT:
This agent does not perform payments.

Payment is only allowed after this privacy/policy gate succeeds.
"""

import re
from datetime import UTC, datetime
from typing import Any

from app.agents.base import AgentContext, AgentResult, BaseAgent


class PrivacyAgent(BaseAgent):
    """
    Security and privacy gate for agentic execution.
    """

    name = "privacy_agent"

    description = (
        "Detects sensitive information and controls what data "
        "may leave the sovereign environment."
    )

    confidence_threshold = 0.95

    # ------------------------------------------------------------------
    # Sensitive patterns
    # ------------------------------------------------------------------

    SENSITIVE_PATTERNS = {
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),

        "phone": re.compile(
            r"(?<!\d)"
            r"(?:\+?\d{1,3}[\s.-]?)?"
            r"(?:\d{10}|\d{3}[\s.-]\d{3}[\s.-]\d{4})"
            r"(?!\d)"
        ),

        "credit_card": re.compile(
            r"\b(?:\d[ -]*?){13,19}\b"
        ),

        "api_key": re.compile(
            r"\b(?:api[_-]?key|apikey|secret[_-]?key)"
            r"\s*[:=]\s*[A-Za-z0-9_\-]{12,}\b",
            re.IGNORECASE,
        ),

        "password": re.compile(
            r"\b(?:password|passwd|pwd)"
            r"\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),

        "private_key": re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?"
            r"PRIVATE KEY-----",
            re.IGNORECASE,
        ),
    }

    # ------------------------------------------------------------------
    # Sensitive keywords
    # ------------------------------------------------------------------

    SENSITIVE_KEYWORDS = {
        "confidential",
        "secret",
        "private",
        "internal only",
        "restricted",
        "classified",
        "proprietary",
        "vendor pricing",
        "salary",
        "employee data",
        "financial information",
        "bank account",
        "credentials",
        "access token",
        "authentication token",
    }

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def _scan_text(
        self,
        text: str,
    ) -> dict[str, Any]:
        """
        Scan text for potentially sensitive information.
        """

        findings: list[dict[str, Any]] = []

        if not text:
            return {
                "contains_sensitive_data": False,
                "findings": [],
            }

        # Pattern-based detection.
        for category, pattern in self.SENSITIVE_PATTERNS.items():

            matches = list(
                pattern.finditer(text)
            )

            if matches:
                findings.append(
                    {
                        "category": category,
                        "count": len(matches),
                        "severity": self._severity_for(
                            category
                        ),
                    }
                )

        # Keyword-based detection.
        lowered = text.lower()

        for keyword in self.SENSITIVE_KEYWORDS:

            if keyword in lowered:
                findings.append(
                    {
                        "category": "sensitive_keyword",
                        "keyword": keyword,
                        "count": 1,
                        "severity": "medium",
                    }
                )

        return {
            "contains_sensitive_data": bool(findings),
            "findings": findings,
        }

    # ------------------------------------------------------------------
    # Severity
    # ------------------------------------------------------------------

    def _severity_for(
        self,
        category: str,
    ) -> str:
        """
        Determine the privacy severity of a finding.
        """

        high_severity = {
            "password",
            "private_key",
            "api_key",
            "credit_card",
        }

        if category in high_severity:
            return "critical"

        if category in {
            "phone",
            "email",
        }:
            return "high"

        return "medium"

    # ------------------------------------------------------------------
    # Recursive data extraction
    # ------------------------------------------------------------------

    def _extract_text_values(
        self,
        value: Any,
    ) -> list[str]:
        """
        Recursively extract textual values from arbitrary task data.
        """

        values: list[str] = []

        if isinstance(value, str):
            values.append(value)

        elif isinstance(value, dict):
            for item in value.values():
                values.extend(
                    self._extract_text_values(item)
                )

        elif isinstance(value, list):
            for item in value:
                values.extend(
                    self._extract_text_values(item)
                )

        return values

    # ------------------------------------------------------------------
    # Full context scan
    # ------------------------------------------------------------------

    def _scan_context(
        self,
        context: AgentContext,
    ) -> dict[str, Any]:
        """
        Scan the entire agent context for sensitive information.
        """

        text_values = []

        text_values.extend(
            self._extract_text_values(
                context.user_query
            )
        )

        text_values.extend(
            self._extract_text_values(
                context.input_data
            )
        )

        text_values.extend(
            self._extract_text_values(
                context.previous_results
            )
        )

        all_findings: list[dict[str, Any]] = []

        for text in text_values:

            result = self._scan_text(text)

            all_findings.extend(
                result["findings"]
            )

        critical_findings = [
            finding
            for finding in all_findings
            if finding.get("severity") == "critical"
        ]

        high_findings = [
            finding
            for finding in all_findings
            if finding.get("severity") == "high"
        ]

        return {
            "scanned_values": len(text_values),
            "total_findings": len(all_findings),
            "findings": all_findings,
            "critical_findings": len(
                critical_findings
            ),
            "high_findings": len(
                high_findings
            ),
            "contains_sensitive_data": bool(
                all_findings
            ),
        }

    # ------------------------------------------------------------------
    # Redaction
    # ------------------------------------------------------------------

    def _redact_text(
        self,
        text: str,
    ) -> str:
        """
        Redact high-risk secrets before an external request.

        Note:
            Redaction is deliberately conservative.

        The production policy engine will decide whether data should
        be redacted, transformed, anonymized, or completely blocked.
        """

        if not text:
            return text

        redacted = text

        # Passwords.
        redacted = self.SENSITIVE_PATTERNS[
            "password"
        ].sub(
            "[REDACTED_PASSWORD]",
            redacted,
        )

        # API keys/secrets.
        redacted = self.SENSITIVE_PATTERNS[
            "api_key"
        ].sub(
            "[REDACTED_API_KEY]",
            redacted,
        )

        # Private keys.
        redacted = self.SENSITIVE_PATTERNS[
            "private_key"
        ].sub(
            "[REDACTED_PRIVATE_KEY]",
            redacted,
        )

        # Credit-card numbers.
        redacted = self.SENSITIVE_PATTERNS[
            "credit_card"
        ].sub(
            "[REDACTED_CARD]",
            redacted,
        )

        return redacted

    # ------------------------------------------------------------------
    # External-sharing policy
    # ------------------------------------------------------------------

    def _evaluate_external_sharing(
        self,
        scan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Decide whether information may leave the sovereign
        environment.

        Policy:

            Critical secrets
                -> BLOCK

            High-risk PII
                -> REQUIRE REDACTION

            Medium-risk findings
                -> ALLOW ONLY AFTER POLICY REVIEW

            No findings
                -> ALLOW
        """

        if scan["critical_findings"] > 0:
            return {
                "decision": "block",
                "reason": (
                    "Critical sensitive information was detected."
                ),
                "payment_allowed": False,
                "external_call_allowed": False,
            }

        if scan["high_findings"] > 0:
            return {
                "decision": "redact",
                "reason": (
                    "High-risk information was detected and "
                    "must be redacted before external transmission."
                ),
                "payment_allowed": True,
                "external_call_allowed": True,
            }

        if scan["contains_sensitive_data"]:
            return {
                "decision": "review",
                "reason": (
                    "Potentially sensitive information was detected "
                    "and requires policy evaluation."
                ),
                "payment_allowed": False,
                "external_call_allowed": False,
            }

        return {
            "decision": "allow",
            "reason": (
                "No sensitive information was detected by the "
                "current privacy scanner."
            ),
            "payment_allowed": True,
            "external_call_allowed": True,
        }

    # ------------------------------------------------------------------
    # BaseAgent implementation
    # ------------------------------------------------------------------

    async def can_handle(
        self,
        context: AgentContext,
    ) -> bool:
        """
        Privacy Agent can inspect every task.

        It should always run before external data transmission.
        """

        return True

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute the privacy/security evaluation.
        """

        started_at = datetime.now(UTC)

        scan = self._scan_context(
            context
        )

        policy = self._evaluate_external_sharing(
            scan
        )

        # --------------------------------------------------------------
        # Prepare sanitized query.
        # --------------------------------------------------------------

        sanitized_query = self._redact_text(
            context.user_query
        )

        requires_redaction = (
            sanitized_query != context.user_query
        )

        # --------------------------------------------------------------
        # Security result.
        # --------------------------------------------------------------

        output = {
            "policy_decision": policy["decision"],
            "reason": policy["reason"],
            "external_call_allowed": (
                policy["external_call_allowed"]
            ),
            "payment_allowed": (
                policy["payment_allowed"]
            ),
            "requires_redaction": requires_redaction,
            "sanitized_query": sanitized_query,
            "scan": scan,
        }

        # --------------------------------------------------------------
        # Confidence.
        # --------------------------------------------------------------

        if policy["decision"] == "block":
            confidence = 0.99

        elif policy["decision"] == "redact":
            confidence = 0.96

        elif policy["decision"] == "review":
            confidence = 0.94

        else:
            confidence = 0.97

        # --------------------------------------------------------------
        # Final result.
        # --------------------------------------------------------------

        return self.build_result(
            context=context,
            success=True,
            output=output,
            confidence=confidence,
            reasoning=(
                "Privacy policy evaluation completed before "
                "any external capability call."
            ),
            requires_external_capability=False,
            capability_request=None,
            metadata={
                "privacy_decision": (
                    policy["decision"]
                ),
                "sensitive_findings": (
                    scan["total_findings"]
                ),
                "critical_findings": (
                    scan["critical_findings"]
                ),
                "external_call_allowed": (
                    policy["external_call_allowed"]
                ),
                "payment_allowed": (
                    policy["payment_allowed"]
                ),
            },
            started_at=started_at,
        )
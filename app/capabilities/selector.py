from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.capabilities.models import Capability
from app.capabilities.registry import capability_registry


@dataclass
class CapabilitySelection:
    """
    Result of capability selection.
    """

    capability: Capability
    score: float
    reasons: list[str]


class CapabilitySelector:
    """
    Selects the most appropriate capability for a task.

    Selection is deterministic and explainable so that the
    orchestration layer can understand why a capability was chosen.
    """

    def __init__(
        self,
        registry=capability_registry,
    ) -> None:
        self.registry = registry

    # ------------------------------------------------------------------
    # SELECT
    # ------------------------------------------------------------------

    def select(
        self,
        task: str,
        *,
        capability_type: str | None = None,
        required_tags: list[str] | None = None,
        allow_paid: bool = True,
    ) -> CapabilitySelection | None:
        """
        Select the best capability for a task.
        """

        if not task or not task.strip():
            return None

        candidates = self.registry.find(
            capability_type=capability_type,
            enabled_only=True,
        )

        if not candidates:
            return None

        required_tags = required_tags or []

        best: CapabilitySelection | None = None

        for capability in candidates:

            if (
                not allow_paid
                and capability.is_paid()
            ):
                continue

            score, reasons = self._score(
                task=task,
                capability=capability,
                required_tags=required_tags,
            )

            selection = CapabilitySelection(
                capability=capability,
                score=score,
                reasons=reasons,
            )

            if (
                best is None
                or selection.score > best.score
            ):
                best = selection

        return best

    # ------------------------------------------------------------------
    # RANK
    # ------------------------------------------------------------------

    def rank(
        self,
        task: str,
        *,
        capability_type: str | None = None,
        required_tags: list[str] | None = None,
        allow_paid: bool = True,
        limit: int = 5,
    ) -> list[CapabilitySelection]:
        """
        Rank available capabilities for a task.
        """

        if limit <= 0:
            return []

        candidates = self.registry.find(
            capability_type=capability_type,
            enabled_only=True,
        )

        required_tags = required_tags or []

        selections: list[CapabilitySelection] = []

        for capability in candidates:

            if (
                not allow_paid
                and capability.is_paid()
            ):
                continue

            score, reasons = self._score(
                task=task,
                capability=capability,
                required_tags=required_tags,
            )

            selections.append(
                CapabilitySelection(
                    capability=capability,
                    score=score,
                    reasons=reasons,
                )
            )

        selections.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return selections[:limit]

    # ------------------------------------------------------------------
    # SCORING
    # ------------------------------------------------------------------

    @staticmethod
    def _score(
        task: str,
        capability: Capability,
        required_tags: list[str],
    ) -> tuple[float, list[str]]:
        """
        Calculate an explainable relevance score.
        """

        task_words = CapabilitySelector._tokenize(
            task
        )

        name_words = CapabilitySelector._tokenize(
            capability.name
        )

        description_words = CapabilitySelector._tokenize(
            capability.description
        )

        tag_words = {
            word.lower()
            for tag in capability.tags
            for word in CapabilitySelector._tokenize(tag)
        }

        score = 0.0
        reasons: list[str] = []

        # Name relevance.
        name_matches = (
            task_words & name_words
        )

        if name_matches:
            score += min(
                0.35,
                0.12 * len(name_matches),
            )

            reasons.append(
                "Task matches capability name."
            )

        # Description relevance.
        description_matches = (
            task_words & description_words
        )

        if description_matches:
            score += min(
                0.30,
                0.04 * len(
                    description_matches
                ),
            )

            reasons.append(
                "Task matches capability description."
            )

        # Tag relevance.
        tag_matches = (
            task_words & tag_words
        )

        if tag_matches:
            score += min(
                0.20,
                0.08 * len(tag_matches),
            )

            reasons.append(
                "Task matches capability tags."
            )

        # Required tags.
        if required_tags:

            capability_tags = {
                tag.lower()
                for tag in capability.tags
            }

            matched_required = [
                tag
                for tag in required_tags
                if tag.lower()
                in capability_tags
            ]

            if matched_required:

                score += min(
                    0.15,
                    0.15
                    * (
                        len(matched_required)
                        / len(required_tags)
                    ),
                )

                reasons.append(
                    "Required capability tags matched."
                )

            else:
                score -= 0.25

                reasons.append(
                    "Required tags were not matched."
                )

        # Local capabilities receive a small preference because
        # sensitive enterprise workloads should remain local whenever
        # possible.
        if capability.provider.lower() == "local":
            score += 0.05

            reasons.append(
                "Local capability preferred for data privacy."
            )

        # Keep score within a predictable range.
        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        if not reasons:
            reasons.append(
                "No strong semantic match found."
            )

        return score, reasons

    # ------------------------------------------------------------------
    # TOKENIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:
        """
        Convert text into normalized tokens.
        """

        if not text:
            return set()

        cleaned = (
            text.lower()
            .replace("/", " ")
            .replace("-", " ")
            .replace("_", " ")
        )

        tokens = {
            token.strip(".,!?():;[]{}\"'")
            for token in cleaned.split()
        }

        return {
            token
            for token in tokens
            if len(token) > 2
        }


# Global selector.
capability_selector = CapabilitySelector()
"""
Vision Agent.

Handles image-based and visual enterprise inputs such as:

    - scanned documents
    - engineering drawings
    - P&ID diagrams
    - equipment photographs
    - charts
    - blueprints

Architecture:

    Image
      ↓
    Local Vision Model / OCR
      ↓
    Structured visual information
      ↓
    Reasoning Agent

If the local vision model is not confident enough, the agent can
request a specialized external capability.

No external capability is paid for directly by this agent.
Payment is handled by the x402 payment layer after policy approval.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agents.base import AgentContext, AgentResult, BaseAgent


class VisionAgent(BaseAgent):
    """
    Processes visual inputs using the sovereign AI environment.
    """

    name = "vision_agent"

    description = (
        "Analyzes images, scanned documents, engineering drawings, "
        "and other visual enterprise data."
    )

    confidence_threshold = 0.90

    SUPPORTED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
    }

    # ------------------------------------------------------------------
    # Image discovery
    # ------------------------------------------------------------------

    def _find_images(
        self,
        context: AgentContext,
    ) -> list[dict[str, Any]]:
        """
        Find image references supplied with the task.

        Expected structure:

            input_data = {
                "images": [
                    {
                        "path": "/path/to/image.png"
                    }
                ]
            }
        """

        images = context.input_data.get(
            "images",
            [],
        )

        if not isinstance(images, list):
            return []

        return images

    # ------------------------------------------------------------------
    # Image validation
    # ------------------------------------------------------------------

    def _validate_image(
        self,
        image: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Validate an image before processing.
        """

        file_path = image.get("path")

        if not file_path:
            return False, "Image path is missing."

        path = Path(file_path)

        if not path.exists():
            return False, "Image file does not exist."

        if not path.is_file():
            return False, "Image path is not a file."

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return (
                False,
                f"Unsupported image type: {path.suffix}",
            )

        return True, None

    # ------------------------------------------------------------------
    # Local vision processing
    # ------------------------------------------------------------------

    async def _analyze_locally(
        self,
        image: dict[str, Any],
        context: AgentContext,
    ) -> dict[str, Any]:
        """
        Analyze an image using the local vision stack.

        The real implementation will call the local multimodal model.

        This abstraction is intentionally kept separate from the agent
        so that the model can later be replaced without changing the
        orchestration layer.
        """

        return {
            "image_path": image.get("path"),
            "analysis": (
                "Local vision analysis pipeline initialized."
            ),
            "detected_objects": [],
            "detected_text": "",
            "visual_relationships": [],
            "model": "local-vision-model-pending",
        }

    # ------------------------------------------------------------------
    # Engineering visual interpretation
    # ------------------------------------------------------------------

    def _identify_visual_task(
        self,
        query: str,
    ) -> str:
        """
        Identify the broad visual-analysis requirement.
        """

        query_lower = query.lower()

        if any(
            term in query_lower
            for term in {
                "p&id",
                "piping",
                "pipeline",
                "valve",
                "process diagram",
            }
        ):
            return "engineering_diagram"

        if any(
            term in query_lower
            for term in {
                "ocr",
                "scan",
                "scanned",
                "text",
                "read",
            }
        ):
            return "ocr"

        if any(
            term in query_lower
            for term in {
                "equipment",
                "machine",
                "component",
                "defect",
                "damage",
            }
        ):
            return "equipment_inspection"

        return "general_visual_analysis"

    # ------------------------------------------------------------------
    # Confidence estimation
    # ------------------------------------------------------------------

    def _estimate_confidence(
        self,
        result: dict[str, Any],
    ) -> float:
        """
        Estimate confidence of the local visual analysis.

        The production implementation will calculate this using
        model confidence, OCR quality, object detection confidence,
        and downstream verification.
        """

        if not result:
            return 0.0

        # Conservative value until the actual multimodal model is
        # connected.
        return 0.78

    # ------------------------------------------------------------------
    # External capability request
    # ------------------------------------------------------------------

    def _build_capability_request(
        self,
        context: AgentContext,
        task_type: str,
        confidence: float,
    ) -> dict[str, Any]:
        """
        Create a marketplace request when local visual reasoning
        is insufficient.
        """

        return {
            "category": "vision",
            "task_type": task_type,
            "task": context.user_query,
            "current_confidence": confidence,
            "required_confidence": self.confidence_threshold,
            "reason": (
                "Local vision confidence is below the autonomous "
                "execution threshold."
            ),
        }

    # ------------------------------------------------------------------
    # BaseAgent implementation
    # ------------------------------------------------------------------

    async def can_handle(
        self,
        context: AgentContext,
    ) -> bool:
        """
        Determine whether the task requires visual processing.
        """

        images = self._find_images(context)

        if images:
            return True

        query = context.user_query.lower()

        visual_keywords = {
            "image",
            "photo",
            "picture",
            "drawing",
            "diagram",
            "visual",
            "scan",
            "scanned",
            "blueprint",
            "p&id",
            "chart",
            "graph",
            "ocr",
        }

        return any(
            keyword in query
            for keyword in visual_keywords
        )

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute local visual analysis.
        """

        started_at = datetime.now(UTC)

        images = self._find_images(context)

        task_type = self._identify_visual_task(
            context.user_query
        )

        # --------------------------------------------------------------
        # No direct image supplied
        # --------------------------------------------------------------

        if not images:
            return self.build_result(
                context=context,
                success=True,
                output={
                    "task_type": task_type,
                    "images": [],
                    "message": (
                        "Visual analysis was requested, but no "
                        "image file was supplied."
                    ),
                },
                confidence=0.65,
                reasoning=(
                    "Vision capability was identified from the "
                    "user request, but direct image input is "
                    "currently unavailable."
                ),
                requires_external_capability=True,
                capability_request=(
                    self._build_capability_request(
                        context,
                        task_type,
                        0.65,
                    )
                ),
                metadata={
                    "images_processed": 0,
                    "task_type": task_type,
                },
                started_at=started_at,
            )

        # --------------------------------------------------------------
        # Process images
        # --------------------------------------------------------------

        analyses = []

        for image in images:

            valid, error = self._validate_image(
                image
            )

            if not valid:
                analyses.append(
                    {
                        "image": image,
                        "success": False,
                        "error": error,
                    }
                )
                continue

            try:
                analysis = await self._analyze_locally(
                    image,
                    context,
                )

                confidence = self._estimate_confidence(
                    analysis
                )

                analyses.append(
                    {
                        "image": image,
                        "success": True,
                        "analysis": analysis,
                        "confidence": confidence,
                    }
                )

            except Exception as exc:
                analyses.append(
                    {
                        "image": image,
                        "success": False,
                        "error": str(exc),
                    }
                )

        successful = [
            item
            for item in analyses
            if item.get("success")
        ]

        if successful:
            confidence = min(
                item.get("confidence", 0.0)
                for item in successful
            )
        else:
            confidence = 0.0

        needs_external = (
            confidence < self.confidence_threshold
        )

        capability_request = None

        if needs_external:
            capability_request = (
                self._build_capability_request(
                    context,
                    task_type,
                    confidence,
                )
            )

        # --------------------------------------------------------------
        # Final result
        # --------------------------------------------------------------

        return self.build_result(
            context=context,
            success=bool(successful),
            output={
                "task_type": task_type,
                "analyses": analyses,
                "images_processed": len(images),
                "successful_images": len(successful),
            },
            confidence=confidence,
            reasoning=(
                "Visual inputs were validated and processed "
                "through the local vision pipeline."
            ),
            requires_external_capability=needs_external,
            capability_request=capability_request,
            metadata={
                "task_type": task_type,
                "images_processed": len(images),
                "successful_images": len(successful),
                "local_vision": True,
            },
            started_at=started_at,
        )
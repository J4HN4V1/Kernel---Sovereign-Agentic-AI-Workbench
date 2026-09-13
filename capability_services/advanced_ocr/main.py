"""
Advanced OCR capability.

Provides a local OCR capability that can be discovered and executed
by the Kernel capability system.

Designed for confidential enterprise documents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.vision.ocr import ocr_service
from app.vision.image_processor import image_processor


CAPABILITY_ID = "advanced_ocr"
CAPABILITY_NAME = "Advanced OCR"


class AdvancedOCRService:
    """
    Advanced OCR capability implementation.
    """

    def execute(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute OCR on the supplied document/image.
        """

        if not isinstance(data, dict):
            raise ValueError(
                "OCR input must be an object."
            )

        source = data.get("source")

        if not source:
            raise ValueError(
                "OCR requires a 'source' field."
            )

        # Optional preprocessing.
        preprocess = data.get(
            "preprocess",
            True,
        )

        if preprocess:
            image = image_processor.prepare_for_ocr(
                source
            )

            text = self._run_ocr_on_image(
                image
            )
        else:
            text = ocr_service.extract_text(
                source
            )

        return {
            "capability_id": CAPABILITY_ID,
            "success": True,
            "text": text,
            "character_count": len(text),
        }

    @staticmethod
    def _run_ocr_on_image(
        image,
    ) -> str:

        try:
            import pytesseract
        except ImportError as exc:
            raise RuntimeError(
                "pytesseract is required for OCR."
            ) from exc

        text = pytesseract.image_to_string(
            image
        )

        return text.strip()


advanced_ocr_service = AdvancedOCRService()


def execute(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Entry point used by the capability registry.
    """

    return advanced_ocr_service.execute(
        data
    )
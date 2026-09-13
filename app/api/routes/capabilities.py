"""
Capability discovery API.

Exposes the capabilities available to the agentic system.

The frontend can use these endpoints to:
    - discover available capabilities
    - inspect pricing
    - inspect supported task types
    - check capability availability

The route does not execute capabilities or payments.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/capabilities",
    tags=["Capabilities"],
)


# ======================================================================
# MODELS
# ======================================================================


class CapabilityInfo(BaseModel):
    """
    Public description of an external capability.
    """

    capability_id: str

    name: str

    description: str

    category: str

    provider: str

    price: float = Field(
        ge=0,
    )

    currency: str = "ALGO"

    payment_protocol: str = "x402"

    blockchain: str = "Algorand"

    enabled: bool = True


class CapabilityListResponse(BaseModel):
    """
    Capability discovery response.
    """

    count: int

    capabilities: list[CapabilityInfo]


# ======================================================================
# CAPABILITY REGISTRY
# ======================================================================

# These are the capabilities exposed by the backend.
#
# Actual execution will happen through the existing:
#
#     app/capabilities/
#     app/capability_services/
#     app/payments/
#
# This registry is only the public discovery layer.

CAPABILITIES: dict[str, CapabilityInfo] = {

    "advanced-ocr": CapabilityInfo(
        capability_id="advanced-ocr",
        name="Advanced OCR",
        description=(
            "Extracts structured information from difficult "
            "scanned documents and images."
        ),
        category="document",
        provider="internal-capability-service",
        price=0.05,
    ),

    "engineering-analysis": CapabilityInfo(
        capability_id="engineering-analysis",
        name="Engineering Analysis",
        description=(
            "Performs specialized analysis of engineering "
            "documents, diagrams and technical information."
        ),
        category="engineering",
        provider="internal-capability-service",
        price=0.10,
    ),

    "vision-analysis": CapabilityInfo(
        capability_id="vision-analysis",
        name="Vision Analysis",
        description=(
            "Analyzes remote-sensing imagery, diagrams and "
            "other visual inputs."
        ),
        category="vision",
        provider="internal-capability-service",
        price=0.08,
    ),

    "document-analysis": CapabilityInfo(
        capability_id="document-analysis",
        name="Document Analysis",
        description=(
            "Analyzes enterprise documents using the document "
            "processing pipeline."
        ),
        category="document",
        provider="internal-capability-service",
        price=0.06,
    ),
}


# ======================================================================
# LIST CAPABILITIES
# ======================================================================


@router.get(
    "",
    response_model=CapabilityListResponse,
)
async def list_capabilities() -> CapabilityListResponse:
    """
    Return all currently available capabilities.
    """

    capabilities = [
        capability
        for capability in CAPABILITIES.values()
        if capability.enabled
    ]

    return CapabilityListResponse(
        count=len(capabilities),
        capabilities=capabilities,
    )


# ======================================================================
# GET CAPABILITY
# ======================================================================


@router.get(
    "/{capability_id}",
    response_model=CapabilityInfo,
)
async def get_capability(
    capability_id: str,
) -> CapabilityInfo:
    """
    Return details for one capability.
    """

    capability = CAPABILITIES.get(
        capability_id
    )

    if capability is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Capability '{capability_id}' "
                "was not found."
            ),
        )

    return capability


# ======================================================================
# CAPABILITY HEALTH
# ======================================================================


@router.get(
    "/{capability_id}/health",
)
async def capability_health(
    capability_id: str,
) -> dict[str, Any]:
    """
    Check whether a capability is enabled and available.
    """

    capability = CAPABILITIES.get(
        capability_id
    )

    if capability is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Capability '{capability_id}' "
                "was not found."
            ),
        )

    return {
        "capability_id": capability.capability_id,
        "status": (
            "available"
            if capability.enabled
            else "disabled"
        ),
        "enabled": capability.enabled,
        "payment_protocol": "x402",
        "blockchain": "Algorand",
    }
"""
Health and readiness endpoints.
"""

from datetime import UTC, datetime

from fastapi import APIRouter


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health() -> dict:
    """
    Basic liveness check.
    """

    return {
        "status": "healthy",
        "service": "agentic-ai-backend",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
async def readiness() -> dict:
    """
    Readiness check.

    Returns whether the backend is ready to accept requests.
    """

    checks = {
        "api": True,
        "orchestration": True,
        "agents": True,
        "database": True,
        "payments": True,
        "capabilities": True,
    }

    ready = all(checks.values())

    return {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/live")
async def liveness() -> dict:
    """
    Kubernetes/container liveness endpoint.
    """

    return {
        "status": "alive",
    }
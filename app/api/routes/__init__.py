"""
HTTP API route package.

All public REST API routers for the Kernel backend are registered
from this package.
"""

from app.api.routes.capabilities import router as capabilities_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.payments import router as payments_router
from app.api.routes.tasks import router as tasks_router

__all__ = [
    "health_router",
    "tasks_router",
    "documents_router",
    "capabilities_router",
    "payments_router",
]
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.api.routes import (
    tasks,
    documents,
    capabilities,
    payments,
    health,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    All infrastructure initialization/cleanup will be connected here
    as we build the backend.
    """

    # Startup
    print(
        f"Starting {settings.app_name} "
        f"v{settings.app_version}"
    )
    print(
        f"Environment: {settings.environment}"
    )

    yield

    # Shutdown
    print("Shutting down application...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Sovereign On-Premise Agentic AI Workbench for "
        "confidential industrial workloads."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ----------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# API ROUTES
# ----------------------------------------------------------------------

app.include_router(tasks.router)
app.include_router(documents.router)
app.include_router(capabilities.router)
app.include_router(payments.router)
app.include_router(health.router)


# ----------------------------------------------------------------------
# Root endpoint
# ----------------------------------------------------------------------

@app.get("/", tags=["System"])
async def root() -> dict:
    """
    Basic service information.
    """

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
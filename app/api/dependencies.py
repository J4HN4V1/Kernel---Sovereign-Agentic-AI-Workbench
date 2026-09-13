"""
FastAPI dependency providers.

This module centralizes access to application-wide services so that
API routes do not create infrastructure objects themselves.

Keeping dependencies here makes the backend easier to test, maintain,
and replace in production.
"""

from collections.abc import AsyncGenerator

from fastapi import Request

from app.config import Settings, settings


def get_settings() -> Settings:
    """
    Return the application settings.

    FastAPI routes can override this dependency during testing.
    """
    return settings


def get_app(request: Request):
    """
    Return the FastAPI application instance.

    Useful when a route needs access to application-level state
    initialized during startup.
    """
    return request.app


async def get_db_session() -> AsyncGenerator:
    """
    Provide a database session.

    The actual SQLAlchemy session implementation will be connected
    when we build the database layer.
    """
    from app.database.session import get_session

    async with get_session() as session:
        yield session
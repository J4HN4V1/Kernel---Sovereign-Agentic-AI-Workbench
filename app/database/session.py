from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./kernel.db",
)


# SQLite needs this for FastAPI's multi-threaded request handling.
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI database dependency.

    Opens one database session per request and guarantees that
    the session is closed afterward.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create database tables if they do not already exist.
    """

    from app.database.models import Base

    Base.metadata.create_all(
        bind=engine,
    )


def check_database() -> bool:
    """
    Verify that the database is reachable.
    """

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(
                "SELECT 1"
            )

        return True

    except Exception:
        return False
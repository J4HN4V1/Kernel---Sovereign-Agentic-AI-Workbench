"""
Task API routes.

Handles creation and execution of agentic tasks.

The route layer is intentionally thin:

    HTTP Request
        ↓
    TaskRequest validation
        ↓
    WorkflowRunner
        ↓
    WorkflowGraph
        ↓
    TaskResponse
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.orchestration.runner import workflow_runner


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


# ======================================================================
# REQUEST MODELS
# ======================================================================


class CreateTaskRequest(BaseModel):
    """
    Payload accepted when creating a new task.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Natural-language task/query.",
    )

    input_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured task input.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional request metadata.",
    )


# ======================================================================
# CREATE TASK
# ======================================================================


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
async def create_task(
    request: CreateTaskRequest,
) -> dict[str, Any]:
    """
    Create and execute an agentic task.

    The complete workflow is handled by WorkflowRunner.
    """

    try:
        state = await workflow_runner.execute(
            user_query=request.query,
            input_data=request.input_data,
            metadata=request.metadata,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task execution failed.",
        ) from exc

    return workflow_runner.serialize(
        state
    )


# ======================================================================
# GET TASK
# ======================================================================


@router.get(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
)
async def get_task(
    task_id: UUID,
) -> dict[str, Any]:
    """
    Retrieve a task.

    Persistent task storage will be connected through the existing
    database/repository layer.
    """

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Task {task_id} was not found."
        ),
    )


# ======================================================================
# RESUME TASK
# ======================================================================


@router.post(
    "/{task_id}/resume",
    status_code=status.HTTP_200_OK,
)
async def resume_task(
    task_id: UUID,
) -> dict[str, Any]:
    """
    Resume an interrupted task.

    The persistent state will be loaded from the database once the
    repository layer is connected.
    """

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Task {task_id} was not found."
        ),
    )
"""
Document API routes.

Handles document upload and document-analysis requests.

The actual processing is delegated to the existing document/vision
pipeline. This route only validates the request and starts the
workflow.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ======================================================================
# RESPONSE MODELS
# ======================================================================


class DocumentUploadResponse(BaseModel):
    """
    Response returned after accepting a document.
    """

    document_id: str

    filename: str

    content_type: str | None

    size_bytes: int

    status: str

    message: str


class DocumentAnalysisRequest(BaseModel):
    """
    Optional instructions for document analysis.
    """

    query: str = Field(
        default="Analyze this document.",
        min_length=1,
        max_length=5000,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# ======================================================================
# CONSTANTS
# ======================================================================


MAX_DOCUMENT_SIZE = 25 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "image/webp",
}


# ======================================================================
# UPLOAD
# ======================================================================


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Accept a document for processing.

    The file is validated here. Persistent storage will be connected
    through the existing database/storage architecture.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    content_type = file.content_type

    if (
        content_type
        and content_type not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported document type: "
                f"{content_type}"
            ),
        )

    content = await file.read()

    size_bytes = len(content)

    if size_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded document is empty.",
        )

    if size_bytes > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "Document exceeds the maximum allowed "
                "size of 25 MB."
            ),
        )

    document_id = str(
        uuid4()
    )

    # The actual persistence/storage layer will consume this data.
    #
    # We deliberately do not write temporary files here because the
    # storage implementation belongs to the existing database/storage
    # architecture.

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        content_type=content_type,
        size_bytes=size_bytes,
        status="accepted",
        message=(
            "Document accepted successfully and is ready "
            "for agentic processing."
        ),
    )


# ======================================================================
# DOCUMENT ANALYSIS
# ======================================================================


@router.post(
    "/analyze",
)
async def analyze_document(
    request: DocumentAnalysisRequest,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Submit a document directly for agentic analysis.

    This endpoint currently validates the document and returns the
    normalized input that the orchestration layer will consume.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    if (
        file.content_type
        and file.content_type not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported document type: "
                f"{file.content_type}"
            ),
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded document is empty.",
        )

    if len(content) > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "Document exceeds the maximum allowed "
                "size of 25 MB."
            ),
        )

    document_id = str(
        uuid4()
    )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "query": request.query,
        "metadata": request.metadata,
        "status": "accepted",
        "next_stage": "agentic_orchestration",
    }
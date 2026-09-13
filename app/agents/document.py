"""
Document Agent.

Responsible for understanding enterprise documents before the
Reasoning Agent processes them.

Pipeline:

    Document
        ↓
    Text extraction
        ↓
    Chunking
        ↓
    RAG retrieval
        ↓
    Structured document context
        ↓
    Reasoning Agent

The actual extraction and RAG implementations will be connected
through app/rag/ later.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agents.base import AgentContext, AgentResult, BaseAgent


class DocumentAgent(BaseAgent):
    """
    Processes document-based inputs for the agentic workflow.
    """

    name = "document_agent"

    description = (
        "Extracts and prepares information from enterprise "
        "documents for downstream reasoning."
    )

    confidence_threshold = 0.85

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".md",
        ".docx",
    }

    # ------------------------------------------------------------------
    # Document detection
    # ------------------------------------------------------------------

    def _find_documents(
        self,
        context: AgentContext,
    ) -> list[dict[str, Any]]:
        """
        Locate document references supplied to the task.

        Documents can be supplied through:
            input_data["documents"]
            input_data["document_ids"]
            input_data["file_paths"]
        """

        input_data = context.input_data

        documents = input_data.get(
            "documents",
            [],
        )

        if not isinstance(documents, list):
            documents = []

        return documents

    # ------------------------------------------------------------------
    # File validation
    # ------------------------------------------------------------------

    def _validate_document(
        self,
        document: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Validate a document reference before processing.
        """

        file_path = document.get("path")

        if not file_path:
            return False, "Document path is missing."

        path = Path(file_path)

        if not path.exists():
            return False, "Document file does not exist."

        if not path.is_file():
            return False, "Document path is not a file."

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return (
                False,
                f"Unsupported document type: {path.suffix}",
            )

        return True, None

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    async def _extract_text(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract text from a document.

        The production implementation will delegate to specialized
        parsers based on the document type.

        PDF:
            PDF text extraction

        DOCX:
            Word document extraction

        TXT/MD:
            Direct text reading

        Scanned PDFs:
            Vision/OCR pipeline
        """

        file_path = Path(
            document["path"]
        )

        extension = file_path.suffix.lower()

        if extension in {".txt", ".md"}:
            text = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            return {
                "text": text,
                "character_count": len(text),
                "extraction_method": "native_text",
            }

        # PDF/DOCX extraction will be connected through the
        # dedicated ingestion pipeline.
        return {
            "text": "",
            "character_count": 0,
            "extraction_method": "pending_parser",
            "requires_specialized_processing": True,
        }

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 150,
    ) -> list[str]:
        """
        Split extracted text into overlapping chunks.

        This provides a deterministic fallback implementation.

        The production RAG pipeline will use a dedicated chunking
        strategy based on document structure.
        """

        if not text:
            return []

        if chunk_size <= overlap:
            raise ValueError(
                "chunk_size must be greater than overlap."
            )

        chunks: list[str] = []

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = end - overlap

        return chunks

    # ------------------------------------------------------------------
    # Process documents
    # ------------------------------------------------------------------

    async def _process_documents(
        self,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Validate, extract and chunk all supplied documents.
        """

        processed_documents = []

        total_chunks = 0

        for document in documents:

            valid, error = self._validate_document(
                document
            )

            if not valid:
                processed_documents.append(
                    {
                        "document": document,
                        "success": False,
                        "error": error,
                    }
                )
                continue

            extracted = await self._extract_text(
                document
            )

            chunks = self._chunk_text(
                extracted["text"]
            )

            total_chunks += len(chunks)

            processed_documents.append(
                {
                    "document": document,
                    "success": True,
                    "extraction": extracted,
                    "chunks": chunks,
                    "chunk_count": len(chunks),
                }
            )

        return {
            "documents": processed_documents,
            "document_count": len(documents),
            "total_chunks": total_chunks,
        }

    # ------------------------------------------------------------------
    # BaseAgent implementation
    # ------------------------------------------------------------------

    async def can_handle(
        self,
        context: AgentContext,
    ) -> bool:
        """
        Determine whether the task contains document information.
        """

        documents = self._find_documents(
            context
        )

        query = context.user_query.lower()

        document_keywords = {
            "document",
            "pdf",
            "report",
            "manual",
            "contract",
            "file",
            "policy",
            "specification",
            "spec",
        }

        query_mentions_document = any(
            keyword in query
            for keyword in document_keywords
        )

        return bool(
            documents
            or query_mentions_document
        )

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Process all documents associated with the task.
        """

        started_at = datetime.now(UTC)

        documents = self._find_documents(
            context
        )

        if not documents:
            return self.build_result(
                context=context,
                success=True,
                output={
                    "documents": [],
                    "document_count": 0,
                    "total_chunks": 0,
                    "message": (
                        "No document objects were supplied. "
                        "The task may require document retrieval "
                        "through the RAG layer."
                    ),
                },
                confidence=0.70,
                reasoning=(
                    "Document processing was initialized, but "
                    "no direct document files were supplied."
                ),
                metadata={
                    "documents_processed": 0,
                },
                started_at=started_at,
            )

        result = await self._process_documents(
            documents
        )

        successful = sum(
            1
            for document in result["documents"]
            if document["success"]
        )

        confidence = (
            successful / result["document_count"]
            if result["document_count"] > 0
            else 0.0
        )

        return self.build_result(
            context=context,
            success=successful > 0,
            output=result,
            confidence=confidence,
            reasoning=(
                "Documents were validated, processed, "
                "and converted into chunks for downstream "
                "RAG and reasoning."
            ),
            metadata={
                "documents_processed": (
                    result["document_count"]
                ),
                "successful_documents": successful,
                "total_chunks": result["total_chunks"],
            },
            started_at=started_at,
        )
"""
Document ingestion pipeline for the local RAG system.

Responsibilities:
    - Read supported documents
    - Extract text
    - Clean text
    - Split text into useful chunks
    - Attach metadata
    - Prepare chunks for embedding/vector storage

No external API is used here.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ======================================================================
# DATA MODEL
# ======================================================================


@dataclass
class DocumentChunk:
    """
    A single chunk produced by the ingestion pipeline.
    """

    chunk_id: str
    document_id: str
    text: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ======================================================================
# INGESTION SERVICE
# ======================================================================


class DocumentIngestion:
    """
    Local document ingestion and chunking service.
    """

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".pdf",
        ".docx",
    }

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> None:

        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if (
            chunk_overlap < 0
            or chunk_overlap >= chunk_size
        ):
            raise ValueError(
                "chunk_overlap must be >= 0 and "
                "smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ==================================================================
    # DOCUMENT ID
    # ==================================================================

    @staticmethod
    def generate_document_id(
        file_path: Path,
    ) -> str:
        """
        Generate a deterministic document identifier.
        """

        stat = file_path.stat()

        raw = (
            f"{file_path.resolve()}:"
            f"{stat.st_size}:"
            f"{stat.st_mtime_ns}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    # ==================================================================
    # TEXT EXTRACTION
    # ==================================================================

    def extract_text(
        self,
        file_path: str | Path,
    ) -> str:
        """
        Extract text from a supported document.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {path}"
            )

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {extension}"
            )

        if extension in {
            ".txt",
            ".md",
            ".csv",
            ".json",
        }:
            return path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        if extension == ".pdf":
            return self._extract_pdf(
                path
            )

        if extension == ".docx":
            return self._extract_docx(
                path
            )

        raise ValueError(
            f"No extractor configured for {extension}"
        )

    # ==================================================================
    # PDF
    # ==================================================================

    @staticmethod
    def _extract_pdf(
        path: Path,
    ) -> str:
        """
        Extract text from a PDF using PyMuPDF.
        """

        try:
            import fitz

        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for PDF ingestion. "
                "Install it with: pip install pymupdf"
            ) from exc

        pages: list[str] = []

        with fitz.open(path) as document:

            for page_number, page in enumerate(
                document,
                start=1,
            ):

                text = page.get_text(
                    "text"
                )

                if text.strip():
                    pages.append(
                        f"[Page {page_number}]\n{text}"
                    )

        return "\n\n".join(pages)

    # ==================================================================
    # DOCX
    # ==================================================================

    @staticmethod
    def _extract_docx(
        path: Path,
    ) -> str:
        """
        Extract paragraphs and table contents from DOCX.
        """

        try:
            from docx import Document

        except ImportError as exc:
            raise RuntimeError(
                "python-docx is required for DOCX ingestion. "
                "Install it with: pip install python-docx"
            ) from exc

        document = Document(
            str(path)
        )

        sections: list[str] = []

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:
                sections.append(text)

        for table in document.tables:

            for row in table.rows:

                cells = [
                    cell.text.strip()
                    for cell in row.cells
                ]

                if any(cells):
                    sections.append(
                        " | ".join(cells)
                    )

        return "\n".join(sections)

    # ==================================================================
    # CLEANING
    # ==================================================================

    @staticmethod
    def clean_text(
        text: str,
    ) -> str:
        """
        Normalize extracted text.
        """

        if not text:
            return ""

        # Normalize line endings.
        text = text.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        # Remove excessive whitespace.
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Collapse excessive blank lines.
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    # ==================================================================
    # CHUNKING
    # ==================================================================

    def chunk_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        The splitter prefers paragraph/sentence boundaries before
        falling back to hard character boundaries.
        """

        text = self.clean_text(
            text
        )

        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []

        start = 0
        text_length = len(text)

        while start < text_length:

            end = min(
                start + self.chunk_size,
                text_length,
            )

            chunk = text[
                start:end
            ]

            # Prefer a natural boundary.
            if end < text_length:

                candidates = [
                    chunk.rfind("\n\n"),
                    chunk.rfind(". "),
                    chunk.rfind("? "),
                    chunk.rfind("! "),
                    chunk.rfind("; "),
                    chunk.rfind(" "),
                ]

                boundary = max(
                    candidates
                )

                minimum_boundary = int(
                    self.chunk_size * 0.5
                )

                if boundary >= minimum_boundary:
                    end = start + boundary + 1
                    chunk = text[
                        start:end
                    ]

            chunk = chunk.strip()

            if chunk:
                chunks.append(
                    chunk
                )

            if end >= text_length:
                break

            next_start = (
                end - self.chunk_overlap
            )

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    # ==================================================================
    # INGEST
    # ==================================================================

    def ingest(
        self,
        file_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """
        Extract, clean and chunk a document.
        """

        path = Path(file_path)

        document_id = self.generate_document_id(
            path
        )

        raw_text = self.extract_text(
            path
        )

        cleaned_text = self.clean_text(
            raw_text
        )

        if not cleaned_text:
            return []

        chunks = self.chunk_text(
            cleaned_text
        )

        base_metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "source": str(path),
        }

        if metadata:
            base_metadata.update(
                metadata
            )

        result: list[DocumentChunk] = []

        for index, chunk in enumerate(
            chunks
        ):

            chunk_id = hashlib.sha256(
                f"{document_id}:{index}:{chunk}".encode(
                    "utf-8"
                )
            ).hexdigest()

            chunk_metadata = {
                **base_metadata,
                "chunk_index": index,
                "total_chunks": len(chunks),
            }

            result.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk,
                    metadata=chunk_metadata,
                )
            )

        return result


# ======================================================================
# DEFAULT INGESTION SERVICE
# ======================================================================

document_ingestion = DocumentIngestion()
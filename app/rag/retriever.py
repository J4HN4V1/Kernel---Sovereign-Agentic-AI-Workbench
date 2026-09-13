"""
Retriever for the RAG pipeline.

Responsible for:
    - converting a user query into an embedding
    - searching the configured vector store
    - applying similarity thresholds
    - returning ranked document chunks
"""

from __future__ import annotations

from typing import Any

from app.rag.embeddings import embedding_service
from app.rag.vectorstore import VectorStore


class Retriever:
    """
    Semantic retriever built on top of the local vector store.
    """

    def __init__(
        self,
        vectorstore: VectorStore | None = None,
        top_k: int = 5,
        similarity_threshold: float = 0.35,
    ) -> None:
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                "similarity_threshold must be between 0 and 1."
            )

        self.vectorstore = (
            vectorstore
            or VectorStore()
        )

        self.top_k = top_k
        self.similarity_threshold = (
            similarity_threshold
        )

    # ==================================================================
    # SEARCH
    # ==================================================================

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic retrieval for a query.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        limit = top_k or self.top_k

        threshold = (
            self.similarity_threshold
            if similarity_threshold is None
            else similarity_threshold
        )

        if limit <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "similarity_threshold must be between 0 and 1."
            )

        query_embedding = embedding_service.embed(
            query
        )

        results = self.vectorstore.search(
            query_embedding=query_embedding,
            top_k=limit,
            filters=filters,
        )

        filtered_results: list[dict[str, Any]] = []

        for result in results:

            score = float(
                result.get(
                    "score",
                    0.0,
                )
            )

            if score < threshold:
                continue

            filtered_results.append(
                result
            )

        return filtered_results

    # ==================================================================
    # SEARCH WITH CONTEXT
    # ==================================================================

    def retrieve_context(
        self,
        query: str,
        *,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """
        Retrieve relevant chunks and combine them into context for
        an LLM.
        """

        results = self.search(
            query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            filters=filters,
        )

        if not results:
            return ""

        context_parts: list[str] = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            text = result.get(
                "text",
                "",
            )

            if not text:
                continue

            context_parts.append(
                f"[Source {index}]\n{text}"
            )

        return "\n\n".join(
            context_parts
        )

    # ==================================================================
    # SEARCH WITH SOURCES
    # ==================================================================

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Return both the retrieved chunks and a ready-to-use context.
        """

        results = self.search(
            query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            filters=filters,
        )

        context_parts: list[str] = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            text = result.get(
                "text",
                "",
            )

            if text:
                context_parts.append(
                    f"[Source {index}]\n{text}"
                )

        return {
            "query": query,
            "results": results,
            "context": "\n\n".join(
                context_parts
            ),
            "count": len(results),
        }

    # ==================================================================
    # HEALTH
    # ==================================================================

    def health(self) -> dict[str, Any]:
        return {
            "ready": self.vectorstore is not None,
            "top_k": self.top_k,
            "similarity_threshold": (
                self.similarity_threshold
            ),
        }


retriever = Retriever()
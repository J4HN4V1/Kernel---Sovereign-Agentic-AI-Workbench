"""
Vector store for the local RAG pipeline.

Uses ChromaDB for persistent, on-premise vector storage.

Responsibilities:
    - store document chunks and embeddings
    - perform similarity search
    - apply metadata filters
    - persist vectors locally
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class VectorStore:
    """
    Local persistent ChromaDB vector store.
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "enterprise_documents",
    ) -> None:

        self.persist_directory = Path(
            persist_directory
            or os.getenv(
                "VECTORSTORE_PATH",
                "./data/chroma_or_qdrant",
            )
        )

        self.collection_name = collection_name

        self._client = None
        self._collection = None

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def _initialize(self) -> None:
        """
        Lazily initialize ChromaDB.
        """

        if self._collection is not None:
            return

        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "chromadb is required for the vector store. "
                "Install it with: pip install chromadb"
            ) from exc

        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._client = chromadb.PersistentClient(
            path=str(
                self.persist_directory
            )
        )

        self._collection = (
            self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": (
                        "Local enterprise RAG document collection"
                    )
                },
            )
        )

    @property
    def collection(self):
        self._initialize()
        return self._collection

    # ==================================================================
    # ADD DOCUMENTS
    # ==================================================================

    def add(
        self,
        records: list[dict[str, Any]],
    ) -> None:
        """
        Add prepared ingestion records to the vector store.

        Each record should contain:
            id
            text
            embedding
            metadata
        """

        if not records:
            return

        ids: list[str] = []
        documents: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, Any]] = []

        for record in records:

            record_id = record.get("id")
            text = record.get("text")
            embedding = record.get("embedding")
            metadata = record.get(
                "metadata",
                {},
            )

            if not record_id:
                raise ValueError(
                    "Every vector record requires an id."
                )

            if not text:
                raise ValueError(
                    f"Record '{record_id}' has no text."
                )

            if not embedding:
                raise ValueError(
                    f"Record '{record_id}' has no embedding."
                )

            ids.append(str(record_id))
            documents.append(str(text))
            embeddings.append(
                list(embedding)
            )
            metadatas.append(
                self._sanitize_metadata(
                    metadata
                )
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    # ==================================================================
    # SEARCH
    # ==================================================================

    def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform vector similarity search.

        Chroma returns distances, so they are converted into a
        similarity score where larger values indicate greater
        similarity.
        """

        if not query_embedding:
            raise ValueError(
                "query_embedding cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query: dict[str, Any] = {
            "query_embeddings": [
                query_embedding
            ],
            "n_results": top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
                "embeddings",
            ],
        }

        if filters:
            query["where"] = filters

        response = self.collection.query(
            **query
        )

        return self._format_results(
            response
        )

    # ==================================================================
    # RESULT FORMATTING
    # ==================================================================

    @staticmethod
    def _format_results(
        response: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Convert Chroma's nested response into a simple list.
        """

        ids = (
            response.get("ids", [[]])[0]
        )

        documents = (
            response.get("documents", [[]])[0]
        )

        metadatas = (
            response.get("metadatas", [[]])[0]
        )

        distances = (
            response.get("distances", [[]])[0]
        )

        embeddings = (
            response.get("embeddings", [[]])[0]
            if response.get("embeddings")
            else []
        )

        results: list[dict[str, Any]] = []

        for index, record_id in enumerate(ids):

            distance = (
                float(distances[index])
                if index < len(distances)
                else 0.0
            )

            # For normalized embeddings, cosine distance is commonly
            # represented as 1 - cosine similarity.
            similarity = max(
                0.0,
                min(
                    1.0,
                    1.0 - distance,
                ),
            )

            result = {
                "id": record_id,
                "text": (
                    documents[index]
                    if index < len(documents)
                    else ""
                ),
                "metadata": (
                    metadatas[index]
                    if index < len(metadatas)
                    else {}
                ),
                "distance": distance,
                "score": similarity,
            }

            if embeddings and index < len(embeddings):
                result["embedding"] = (
                    embeddings[index]
                )

            results.append(result)

        return results

    # ==================================================================
    # GET
    # ==================================================================

    def get(
        self,
        record_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve a single stored chunk by ID.
        """

        response = self.collection.get(
            ids=[record_id],
            include=[
                "documents",
                "metadatas",
                "embeddings",
            ],
        )

        ids = response.get(
            "ids",
            [],
        )

        if not ids:
            return None

        return {
            "id": ids[0],
            "text": (
                response.get(
                    "documents",
                    [""],
                )[0]
            ),
            "metadata": (
                response.get(
                    "metadatas",
                    [{}],
                )[0]
            ),
            "embedding": (
                response.get(
                    "embeddings",
                    [None],
                )[0]
            ),
        }

    # ==================================================================
    # DELETE
    # ==================================================================

    def delete(
        self,
        record_ids: list[str],
    ) -> None:
        """
        Delete chunks from the vector store.
        """

        if not record_ids:
            return

        self.collection.delete(
            ids=record_ids
        )

    # ==================================================================
    # COUNT
    # ==================================================================

    def count(self) -> int:
        """
        Return the number of stored chunks.
        """

        return int(
            self.collection.count()
        )

    # ==================================================================
    # METADATA
    # ==================================================================

    @staticmethod
    def _sanitize_metadata(
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Chroma metadata values must be scalar types.
        """

        sanitized: dict[str, Any] = {}

        for key, value in metadata.items():

            if value is None:
                continue

            if isinstance(
                value,
                (str, int, float, bool),
            ):
                sanitized[str(key)] = value

            else:
                sanitized[str(key)] = str(
                    value
                )

        return sanitized

    # ==================================================================
    # HEALTH
    # ==================================================================

    def health(self) -> dict[str, Any]:
        try:
            count = self.count()

            return {
                "ready": True,
                "collection": self.collection_name,
                "persist_directory": str(
                    self.persist_directory
                ),
                "document_chunks": count,
            }

        except Exception as exc:
            return {
                "ready": False,
                "collection": self.collection_name,
                "error": str(exc),
            }


vector_store = VectorStore()
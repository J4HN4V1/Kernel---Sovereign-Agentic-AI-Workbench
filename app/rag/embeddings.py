"""
Embedding service for the RAG pipeline.

Uses a local sentence-transformer model so confidential enterprise
data remains on-premise.

The service provides:
    - single-text embeddings
    - batch embeddings
    - normalized vectors
    - embedding dimension information
"""

from functools import lru_cache
from typing import Sequence

import numpy as np


class EmbeddingService:
    """
    Local embedding model wrapper.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name
        self._model = None

    # ==================================================================
    # MODEL
    # ==================================================================

    def _load_model(self):
        """
        Lazily load the embedding model.

        Lazy loading keeps application startup lightweight.
        """

        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name
            )

        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for local "
                "embeddings. Install it with: "
                "pip install sentence-transformers"
            ) from exc

        return self._model

    # ==================================================================
    # SINGLE EMBEDDING
    # ==================================================================

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for one text.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot generate an embedding for empty text."
            )

        model = self._load_model()

        vector = model.encode(
            text.strip(),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return vector.astype(
            np.float32
        ).tolist()

    # ==================================================================
    # BATCH EMBEDDINGS
    # ==================================================================

    def embed_batch(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        """

        if not texts:
            return []

        cleaned = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not cleaned:
            return []

        model = self._load_model()

        vectors = model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False,
        )

        return [
            vector.astype(
                np.float32
            ).tolist()
            for vector in vectors
        ]

    # ==================================================================
    # DIMENSION
    # ==================================================================

    @property
    def dimension(self) -> int:
        """
        Return embedding vector dimension.
        """

        model = self._load_model()

        return int(
            model.get_sentence_embedding_dimension()
        )

    # ==================================================================
    # SIMILARITY
    # ==================================================================

    @staticmethod
    def cosine_similarity(
        vector_a: Sequence[float],
        vector_b: Sequence[float],
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        """

        if not vector_a or not vector_b:
            return 0.0

        if len(vector_a) != len(vector_b):
            raise ValueError(
                "Embedding dimensions do not match."
            )

        a = np.asarray(
            vector_a,
            dtype=np.float32,
        )

        b = np.asarray(
            vector_b,
            dtype=np.float32,
        )

        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)

        if a_norm == 0 or b_norm == 0:
            return 0.0

        similarity = np.dot(
            a,
            b,
        ) / (
            a_norm * b_norm
        )

        return float(
            np.clip(
                similarity,
                -1.0,
                1.0,
            )
        )


# ======================================================================
# DEFAULT SERVICE
# ======================================================================

embedding_service = EmbeddingService()
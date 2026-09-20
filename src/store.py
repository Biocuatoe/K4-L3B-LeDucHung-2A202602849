from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401
            self._use_chroma = False  # Force in-memory; chroma init skipped
        except Exception:
            self._use_chroma = False

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        metadata_copy = dict(doc.metadata) if doc.metadata else {}
        # Ensure doc_id is in metadata for delete_document to work
        metadata_copy["doc_id"] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata_copy,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        query_embedding = self._embedding_fn(query)

        scored: list[tuple[float, dict[str, Any]]] = []
        for record in records:
            rec_emb = record.get("embedding")
            if rec_emb is None:
                continue
            # Cosine similarity: normalized dot product
            score = compute_similarity(query_embedding, rec_emb)
            scored.append((score, record))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        top_k = max(1, top_k)
        results: list[dict[str, Any]] = []
        for score, record in scored[:top_k]:
            # Return content, score, metadata (omit raw embedding to keep output clean)
            results.append({
                "content": record.get("content", ""),
                "score": score,
                "metadata": record.get("metadata", {}),
                "id": record.get("id", ""),
            })
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        filtered = [
            rec for rec in self._store
            if all(
                rec.get("metadata", {}).get(k) == v
                for k, v in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        original_len = len(self._store)
        self._store = [
            rec for rec in self._store
            if rec.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < original_len

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """Retrieve chunks, build prompt, call llm_fn."""
        results = self.store.search(question, top_k)
        if not results:
            return "I don't know based on the available context."

        # Build numbered context with source info
        context_parts: list[str] = []
        for i, result in enumerate(results, start=1):
            meta = result.get("metadata", {})
            doc_id = meta.get("doc_id", "unknown")
            content = result.get("content", "")
            context_parts.append(f"[{i}] [{doc_id}] {content}")

        context_block = "\n---\n".join(context_parts)

        prompt = (
            "Context:\n"
            f"{context_block}\n\n"
            f"Question: {question}\n"
            "Answer concisely based on the context above. "
            "Cite the chunk number(s) when using information from the context."
        )

        return self.llm_fn(prompt)

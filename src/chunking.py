from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Split on sentence boundaries: ". ", "! ", "? ", ".\n"
        # Use lookbehind to keep the punctuation in the sentence
        import re as _re
        sentences = _re.split(r'(?<=[.!?])\s+', text)
        sentences = [s for s in sentences if s]

        if not sentences:
            return []

        max_sents = self.max_sentences_per_chunk
        chunks: list[str] = []
        for i in range(0, len(sentences), max_sents):
            chunk_text = ' '.join(sentences[i : i + max_sents])
            chunks.append(chunk_text.strip())

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: text fits within chunk_size
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return self._char_level_split(current_text)

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Empty separator: skip string.split() entirely, use character-level fallback
        if separator == "":
            return self._char_level_split(current_text)

        if separator not in current_text:
            return self._split(current_text, next_separators)

        # Split on separator; use a loop to handle oversized chunks
        parts = current_text.split(separator)
        result_chunks: list[str] = []
        buffer = ""

        for part in parts:
            candidate = (buffer + separator + part) if buffer else part
            if len(candidate) > self.chunk_size:
                if buffer:
                    result_chunks.append(buffer)
                sub_chunks = self._split(candidate, next_separators)
                result_chunks.extend(sub_chunks)
                buffer = ""
            else:
                buffer = candidate

        if buffer:
            if len(buffer) <= self.chunk_size:
                result_chunks.append(buffer)
            else:
                result_chunks.extend(self._split(buffer, next_separators))

        if not result_chunks:
            return [current_text]

        # Merge adjacent small chunks for coherence
        merged: list[str] = [result_chunks[0]]
        for chunk in result_chunks[1:]:
            if len(merged[-1]) + len(chunk) <= self.chunk_size:
                merged[-1] = merged[-1] + chunk
            else:
                merged.append(chunk)

        return merged

    def _char_level_split(self, text: str) -> list[str]:
        """Hard-split text by characters at chunk_size boundaries."""
        chunks: list[str] = []
        step = max(1, self.chunk_size - self.chunk_size // 10)
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            if chunk:
                chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks if chunks else [text]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    import math as _math
    norm_a = _math.sqrt(sum(x * x for x in vec_a))
    norm_b = _math.sqrt(sum(x * x for x in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    dot_prod = _dot(vec_a, vec_b)
    return dot_prod / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10)
        sentence = SentenceChunker(max_sentences_per_chunk=3)
        recursive = RecursiveChunker(chunk_size=chunk_size)

        def _stats(name: str, chunks: list[str]) -> dict:
            count = len(chunks)
            if count == 0:
                avg_len = 0.0
            else:
                avg_len = sum(len(c) for c in chunks) / count
            return {"count": count, "avg_length": avg_len, "chunks": chunks}

        return {
            "fixed_size": _stats("fixed_size", fixed.chunk(text)),
            "by_sentences": _stats("by_sentences", sentence.chunk(text)),
            "recursive": _stats("recursive", recursive.chunk(text)),
        }

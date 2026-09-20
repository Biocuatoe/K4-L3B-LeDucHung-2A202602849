"""
bench.py — Benchmark script for Shopee policy retrieval.
Runs 5 benchmark queries across 3 chunking strategies (FixedSize, Sentence, HeadingAware).
Compares filtered vs unfiltered search for the audience=seller query.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    KnowledgeBaseAgent,
    _mock_embed,
)


class HeadingAwareChunker:
    """
    Chunk text by markdown heading/section boundaries.
    Each ## or # heading starts a new chunk.
    Sections longer than chunk_size are recursively split with the heading prepended.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._recursive = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split on ## and # heading lines (keep the heading as part of the chunk)
        # Use regex to find heading lines
        pattern = r'(^#+\s+.+)$'
        parts = re.split(pattern, text, flags=re.MULTILINE)

        # Rebuild: each section starts with a heading
        chunks: list[str] = []
        i = 0
        while i < len(parts):
            part = parts[i]
            if re.match(r'^#+\s+', part):
                # This is a heading line — join with next part (content)
                heading = part.strip()
                if i + 1 < len(parts):
                    content = parts[i + 1].strip()
                    section_text = f"{heading}\n\n{content}" if content else heading
                    i += 2
                else:
                    section_text = heading
                    i += 1
            else:
                section_text = part.strip()
                i += 1

            if not section_text:
                continue

            if len(section_text) <= self.chunk_size:
                chunks.append(section_text)
            else:
                # Recursively split oversized sections
                sub_chunks = self._recursive.chunk(section_text)
                # Prepend heading to each sub-chunk if missing
                first_heading = ""
                for line in section_text.split('\n'):
                    if re.match(r'^#+\s+', line):
                        first_heading = line.strip()
                        break
                if first_heading:
                    sub_chunks = [
                        (first_heading + "\n\n" + c) if not re.match(r'^#+\s+', c.strip()) else c
                        for c in sub_chunks
                    ]
                chunks.extend(sub_chunks)

        return [c for c in chunks if c]


def parse_markdown_file(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from a markdown file."""
    text = path.read_text(encoding='utf-8')
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    metadata = {}
    body = text
    if fm_match:
        fm_text = fm_match.group(1)
        body = text[fm_match.end():]
        for line in fm_text.split('\n'):
            m = re.match(r'^(\w+):\s*(.*)$', line)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                metadata[key] = val
    return metadata, body.strip()


def load_documents(data_dir: Path, chunker) -> list[Document]:
    """Load .md files, chunk them, and return Document list."""
    docs = []
    mds = sorted(data_dir.glob('*.md'))
    for md_path in mds:
        if md_path.stem == 'sources':
            continue
        metadata, body = parse_markdown_file(md_path)
        chunks = chunker.chunk(body)
        doc_id = md_path.stem
        for idx, chunk_text in enumerate(chunks):
            chunk_meta = {**metadata, "doc_id": doc_id, "chunk_index": idx}
            docs.append(Document(
                id=f"{doc_id}#{idx}",
                content=chunk_text,
                metadata=chunk_meta,
            ))
    return docs


def run_benchmark(queries_path: Path, data_dir: Path, output_path: Path) -> None:
    """Run benchmark queries and write results."""
    queries = json.loads(queries_path.read_text(encoding='utf-8'))

    results_lines: list[str] = []
    results_lines.append("=" * 80)
    results_lines.append("KET QUA BENCHMARK - Shopee Policy Retrieval")
    results_lines.append(f"Timestamp: 2026-09-20")
    results_lines.append(f"Embedder: mock (MD5 hash-based, no semantic meaning)")
    results_lines.append("=" * 80)

    # Test 3 chunking strategies
    strategies = {
        "FixedSize (size=300, overlap=30)": FixedSizeChunker(chunk_size=300, overlap=30),
        "Sentence (max=3 sentences)": SentenceChunker(max_sentences_per_chunk=3),
        "HeadingAware (size=500)": HeadingAwareChunker(chunk_size=500),
    }

    all_results: dict[str, dict] = {}

    for strategy_name, chunker in strategies.items():
        results_lines.append(f"\n{'=' * 60}")
        results_lines.append(f"STRATEGY: {strategy_name}")
        results_lines.append(f"Chunker: {chunker.__class__.__name__}")
        results_lines.append('=' * 60)

        docs = load_documents(data_dir, chunker)
        results_lines.append(f"Total chunks indexed: {len(docs)}")

        store = EmbeddingStore(collection_name="shopee_bench", embedding_fn=_mock_embed)
        store.add_documents(docs)

        strategy_results: dict[str, list] = {}

        for q_idx, q in enumerate(queries, 1):
            query_text = q["query"]
            filter_dict = q.get("filter")
            gold_doc = q.get("expected_doc_id", "")

            results_lines.append(f"\n--- Query {q_idx}: {query_text[:80]}")
            results_lines.append(f"    Filter: {filter_dict}")
            results_lines.append(f"    Gold doc_id: {gold_doc}")

            if filter_dict:
                raw_results = store.search(query_text, top_k=5)
                filtered_results = store.search_with_filter(query_text, top_k=3, metadata_filter=filter_dict)
                results_lines.append(f"\n    [UNFILTERED - top 3 of {len(raw_results)}]:")
                for rank, r in enumerate(raw_results[:3], 1):
                    meta = r.get("metadata", {})
                    doc_id_short = meta.get("doc_id", "?")
                    content_snippet = r.get("content", "")[:100].replace('\n', ' ')
                    results_lines.append(f"      #{rank} score={r.get('score', 0):.4f} doc_id={doc_id_short}")
                    results_lines.append(f"          content: {content_snippet}...")
                results_lines.append(f"\n    [FILTERED - top 3]:")
                for rank, r in enumerate(filtered_results, 1):
                    meta = r.get("metadata", {})
                    doc_id_short = meta.get("doc_id", "?")
                    content_snippet = r.get("content", "")[:100].replace('\n', ' ')
                    in_gold = "[GOLD]" if doc_id_short == gold_doc else ""
                    results_lines.append(f"      #{rank} score={r.get('score', 0):.4f} doc_id={doc_id_short} {in_gold}")
                    results_lines.append(f"          content: {content_snippet}...")
                strategy_results[query_text] = filtered_results
            else:
                top_results = store.search(query_text, top_k=3)
                for rank, r in enumerate(top_results, 1):
                    meta = r.get("metadata", {})
                    doc_id_short = meta.get("doc_id", "?")
                    content_snippet = r.get("content", "")[:100].replace('\n', ' ')
                    in_gold = "[GOLD]" if doc_id_short == gold_doc else ""
                    results_lines.append(f"      #{rank} score={r.get('score', 0):.4f} doc_id={doc_id_short} {in_gold}")
                    results_lines.append(f"          content: {content_snippet}...")
                strategy_results[query_text] = top_results

        all_results[strategy_name] = strategy_results

    # A/B comparison: filter vs no-filter for audience=seller query
    results_lines.append(f"\n\n{'=' * 60}")
    results_lines.append("A/B COMPARISON: metadata_filter effect")
    results_lines.append("Query: Thời hạn phản hồi yêu cầu đổi trả của người bán")
    results_lines.append("Filter: audience=seller")
    results_lines.append('=' * 60)

    ab_query = queries[4]["query"]  # The seller filter query
    ab_filter = {"audience": "seller"}

    for strategy_name, chunker in strategies.items():
        docs = load_documents(data_dir, chunker)
        store = EmbeddingStore(collection_name=f"ab_{strategy_name[:10]}", embedding_fn=_mock_embed)
        store.add_documents(docs)

        unfiltered = store.search(ab_query, top_k=3)
        filtered = store.search_with_filter(ab_query, top_k=3, metadata_filter=ab_filter)

        results_lines.append(f"\n  {strategy_name}:")
        results_lines.append(f"    Without filter (top-3 doc_ids): {[r['metadata'].get('doc_id') for r in unfiltered]}")
        results_lines.append(f"    With filter    (top-3 doc_ids): {[r['metadata'].get('doc_id') for r in filtered]}")

    # Write results
    output_path.write_text('\n'.join(results_lines), encoding='utf-8')
    print(f"Results written to: {output_path}")
    print('\n'.join(results_lines[-30:]))  # Print last 30 lines


if __name__ == "__main__":
    repo_root = Path(__file__).parent
    queries_path = repo_root / "data" / "shopee-policies" / "benchmark_queries.json"
    data_dir = repo_root / "data" / "shopee-policies"
    output_path = repo_root / "ket_qua_benchmark.txt"

    run_benchmark(queries_path, data_dir, output_path)

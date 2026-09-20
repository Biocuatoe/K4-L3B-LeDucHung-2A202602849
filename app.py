"""
app.py — K4-L3B Shopee Policy RAG Demo
Gradio UI + Groq LLM + local sentence-transformer embeddings + EmbeddingStore RAG.
"""
from __future__ import annotations

import io
import hashlib
import functools
import time
import os
import re
import sys

# Fix Windows console encoding for emoji prints (UTF-8)
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import gradio as gr
import groq
from dotenv import load_dotenv

# Import existing lab codebase
import sys
sys.path.insert(0, str(Path(__file__).parent))
from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    compute_similarity,
    LocalEmbedder,
    _mock_embed,
)

load_dotenv(override=False)


# ─── HeadingAwareChunker (from bench.py, re-defined here) ────────────────────

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


# ─── Types ────────────────────────────────────────────────────────────────

@dataclass
class ConversationState:
    """Holds all mutable UI state."""
    audience_filter: str = "all"          # "all" | "buyer" | "seller"
    last_query: str = ""
    last_results: list[dict[str, Any]] = field(default_factory=list)
    groq_client: groq.Client | None = None
    embedder: Callable[[str], list[float]] | None = None
    store: EmbeddingStore | None = None
    is_loaded: bool = False
    error_message: str = ""


@dataclass
class IntentResult:
    """NLU intent classification result."""
    intent: str           # "query" | "filter_change" | "compare" | "show_chunks" | "stats" | "unknown"
    audience: str | None = None  # "buyer" | "seller" | None (for filter_change); default None makes dataclass forgiving
    ambiguity: bool = False
    raw_query: str = ""


@dataclass
class ChunkCard:
    """Represents a single corpus chunk for display."""
    chunk_id: str
    content: str
    doc_id: str
    title: str
    audience: str
    score: float = 0.0
    chunk_index: int = 0


# ─── Chat message helper (Gradio 6 dict format) ────────────────────────────

def _msg(role: str, content: str) -> dict:
    """Format a single chat message for Gradio 6 Chatbot (dict format)."""
    return {"role": role, "content": content}


# ─── Intent parser ─────────────────────────────────────────────────────────

BUYER_KEYWORDS = ["người mua", "buyer", "tôi mua", "khách hàng mua", "người tiêu dùng"]
SELLER_KEYWORDS = ["người bán", "seller", "tôi bán", "shop", "cửa hàng", "seller"]

COMPARISON_KEYWORDS = ["so sánh", "compare", "chunker", "cắt chunks", "heading", "sentence"]
SHOW_CHUNKS_KEYWORDS = ["xem chunks", "tất cả chunk", "show chunks", "tất cả đoạn", "danh sách chunk"]
STATS_KEYWORDS = ["thống kê", "stats", "bao nhiêu", "có bao", "tổng số", "số lượng"]


def detect_ambiguity(query_lower: str) -> bool:
    """Return True if query could apply to both buyer and seller."""
    has_buyer = any(kw in query_lower for kw in BUYER_KEYWORDS)
    has_seller = any(kw in query_lower for kw in SELLER_KEYWORDS)
    neutral_words = ["đổi trả", "hoàn tiền", "khiếu nại", "bảo hành", "chính sách"]
    has_neutral = any(w in query_lower for w in neutral_words)
    # Ambiguous if query mentions policy area but neither audience explicitly
    return has_neutral and not has_buyer and not has_seller


def parse_intent(user_message: str) -> IntentResult:
    """
    Classify user message into one of 6 intents.
    Priority: filter_change > compare > show_chunks > stats > query > unknown.
    """
    raw = user_message.strip()
    lower = raw.lower()

    # 1. filter_change: user explicitly says they are buyer or seller
    if any(kw in lower for kw in SELLER_KEYWORDS):
        return IntentResult(intent="filter_change", audience="seller", raw_query=raw)
    if any(kw in lower for kw in BUYER_KEYWORDS):
        return IntentResult(intent="filter_change", audience="buyer", raw_query=raw)

    # 2. compare mode
    if any(kw in lower for kw in COMPARISON_KEYWORDS):
        return IntentResult(intent="compare", audience=None, raw_query=raw)

    # 3. show chunks
    if any(kw in lower for kw in SHOW_CHUNKS_KEYWORDS):
        return IntentResult(intent="show_chunks", audience=None, raw_query=raw)

    # 4. stats
    if any(kw in lower for kw in STATS_KEYWORDS):
        return IntentResult(intent="stats", audience=None, raw_query=raw)

    # 5. query
    if len(lower) >= 3:
        ambiguity = detect_ambiguity(lower)
        return IntentResult(intent="query", ambiguity=ambiguity, audience=None, raw_query=raw)

    # 6. unknown
    return IntentResult(intent="unknown", audience=None, raw_query=raw)


# ─── 4 response renderers ─────────────────────────────────────────────────

def _score_bar(score: float, width: int = 300) -> str:
    """Render an animated score bar HTML."""
    pct = max(0, min(100, int(score * 100)))
    color = (
        "#10B981" if pct >= 70 else
        "#F59E0B" if pct >= 40 else
        "#EF4444"
    )
    return f"""
    <div class="score-bar-container">
        <div class="score-bar-label">📊 Relevance: <strong>{pct}%</strong></div>
        <div class="score-bar-track">
            <div class="score-bar-fill" style="width: 0%; background:{color};"
                 data-target-width="{pct}%"></div>
        </div>
    </div>
    """


def _citation_badge(doc_id: str, title: str, chunk_idx: int) -> str:
    """Render a clickable citation badge."""
    return (
        f'<span class="citation-badge" onclick="showChunks()">'
        f'📄 {title} · chunk #{chunk_idx + 1}'
        f'</span>'
    )


def _source_badge(audience: str) -> str:
    """Render an audience-colored badge."""
    color_map = {"buyer": "#EE4D2D", "seller": "#3B82F6", "both": "#6B7280"}
    label_map = {"buyer": "🛒 Người mua", "seller": "🏪 Người bán", "both": "📋 Chung"}
    color = color_map.get(audience, "#6B7280")
    label = label_map.get(audience, audience)
    return f'<span class="audience-badge" style="background:{color}">{label}</span>'


def render_type_t(results: list[dict], query: str) -> str:
    """
    Type T — Trả lời (Full answer from LLM).
    Called when store returns high-scoring results → LLM generates a natural answer.
    """
    if not results:
        return render_type_e("Không tìm thấy kết quả nào phù hợp.")

    top = results[0]
    score = top.get("score", 0.0)
    meta = top.get("metadata", {})
    title = meta.get("title", meta.get("doc_id", ""))
    audience = meta.get("audience", "unknown")
    chunk_idx = meta.get("chunk_index", 0)
    content = top.get("content", "")[:500]

    return f"""
    <div class="response-card type-t fade-in">
        <div class="card-header">
            <span class="type-badge type-badge-t">✅ Trả lời</span>
            {_source_badge(audience)}
        </div>
        <div class="card-body">
            <p class="answer-text">{content}</p>
            {_score_bar(score)}
            {_citation_badge(meta.get("doc_id", ""), title, chunk_idx)}
        </div>
    </div>
    """


def render_type_n(results: list[dict], query: str) -> str:
    """
    Type N — Nhiều kết quả (Navigation).
    Called when retrieval finds multiple relevant chunks → show ranked list with score bars.
    """
    if not results:
        return render_type_e("Không tìm thấy kết quả phù hợp.")

    rows_html = ""
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        title = meta.get("title", meta.get("doc_id", ""))
        audience = meta.get("audience", "unknown")
        score = r.get("score", 0.0)
        content_preview = r.get("content", "")[:150].replace("\n", " ")
        rows_html += f"""
        <div class="result-row">
            <div class="result-rank">#{i}</div>
            <div class="result-body">
                <div class="result-title">{_source_badge(audience)} {title}</div>
                <div class="result-preview">{content_preview}…</div>
                {_score_bar(score)}
            </div>
        </div>
        """

    return f"""
    <div class="response-card type-n fade-in">
        <div class="card-header">
            <span class="type-badge type-badge-n">🔍 Tìm thấy {len(results)} kết quả liên quan</span>
        </div>
        <div class="card-body">
            {rows_html}
        </div>
    </div>
    """


def render_type_a(ambiguity: bool, query: str) -> str:
    """
    Type A — Mơ hồ (Ambiguous).
    Called when query could apply to both buyer and seller without clear audience.
    Offers interactive audience selection buttons.
    """
    return f"""
    <div class="response-card type-a fade-in">
        <div class="card-header">
            <span class="type-badge type-badge-a">⚠️ Câu hỏi có thể áp dụng cho nhiều đối tượng</span>
        </div>
        <div class="card-body">
            <p>Câu hỏi <em>"{query[:80]}{'…' if len(query) > 80 else ''}"</em> có thể áp dụng cho cả
            <strong>người mua</strong> và <strong>người bán</strong>. Bạn muốn hỏi về:</p>
            <div class="ambiguous-buttons">
                <button class="gr-button gr-button-lg audience-btn" onclick="setAudience('buyer')"
                        style="background:#EE4D2D; color:white;">
                    🛒 Chính sách đổi trả cho NGƯỜI MUA
                </button>
                <button class="gr-button gr-button-lg audience-btn" onclick="setAudience('seller')"
                        style="background:#3B82F6; color:white;">
                    🏪 Chính sách đổi trả cho NGƯỜI BÁN
                </button>
                <button class="gr-button gr-button-lg" onclick="setAudience('all')"
                        style="background:#6B7280; color:white;">
                    🔍 Tìm kiếm cho cả hai
                </button>
            </div>
        </div>
    </div>
    """


def render_type_e(error_message: str) -> str:
    """
    Type E — Lỗi (Error).
    Called on any error (empty store, rate limit, API key missing, low scores).
    """
    return f"""
    <div class="response-card type-e shake">
        <div class="card-header">
            <span class="type-badge type-badge-e">❌ Đã xảy ra lỗi</span>
        </div>
        <div class="card-body">
            <p class="error-text">{error_message}</p>
            <div class="error-actions">
                <button class="gr-button" onclick="retryLastQuery()">🔄 Thử lại</button>
                <button class="gr-button" onclick="showChunks()">📋 Xem tất cả chunks</button>
            </div>
        </div>
    </div>
    """


# ─── Groq wrapper with cache and error handling ─────────────────────────────

class LLMError(Exception):
    """Raised when Groq API call fails."""
    pass


# ── LLM response cache (simple in-memory, resets on restart) ──────────────
_llm_cache: dict[str, str] = {}
_CACHE_MAX_SIZE = 100


def _cache_key(query: str, context: str, model: str) -> str:
    """Deterministic cache key from query + context hash."""
    raw = f"{model}:{query}:{hashlib.md5(context.encode()).hexdigest()[:16]}"
    return hashlib.sha256(raw.encode()).hexdigest()


def make_groq_client() -> groq.Client:
    """Build Groq client from .env GROQ_API_KEY."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise LLMError("GROQ_API_KEY not set in .env — get one at console.groq.com")
    return groq.Client(api_key=api_key)


def llm_answer(
    query: str,
    context_chunks: list[dict[str, Any]],
    client: groq.Client,
    model: str = "llama-3.1-70b-versatile",
    max_tokens: int = 512,
    temperature: float = 0.3,
) -> str:
    """
    Call Groq LLM with shopee policy context and return answer text.

    Caching: identical (query, context_hash) pairs return cached response.
    """
    if not context_chunks:
        return "Tôi không tìm thấy thông tin phù hợp trong cơ sở kiến thức hiện tại."

    # Build numbered context block
    context_parts: list[str] = []
    for i, r in enumerate(context_chunks[:5], start=1):  # max 5 chunks
        meta = r.get("metadata", {})
        doc_id = meta.get("doc_id", "unknown")
        content = r.get("content", "")
        context_parts.append(f"[{i}] [{doc_id}] {content}")

    context_block = "\n---\n".join(context_parts)

    # Load system prompt
    prompts_dir = Path(__file__).parent / "prompts"
    system_prompt_path = prompts_dir / "system_shopee.md"
    if system_prompt_path.exists():
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
    else:
        system_prompt = (
            "Bạn là trợ lý tiếng Việt trả lời về chính sách Shopee. "
            "Dựa trên ngữ cảnh được cung cấp, trả lời ngắn gọn bằng tiếng Việt. "
            "Trích dẫn nguồn khi dùng thông tin."
        )

    user_prompt = (
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n"
        f"Answer concisely in Vietnamese. Cite the chunk number(s) when using information."
    )

    # Check cache
    cache_key = _cache_key(query, context_block, model)
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        answer = response.choices[0].message.content or "Không có phản hồi từ model."

        # Cache result
        if len(_llm_cache) >= _CACHE_MAX_SIZE:
            # Simple eviction: clear oldest half
            keys_to_remove = list(_llm_cache.keys())[: _CACHE_MAX_SIZE // 2]
            for k in keys_to_remove:
                del _llm_cache[k]
        _llm_cache[cache_key] = answer
        return answer

    except groq.RateLimitError as e:
        raise LLMError(f"Groq rate limit exceeded (30 req/min free tier). Try again in a moment.") from e
    except groq.AuthenticationError as e:
        raise LLMError(f"Invalid GROQ_API_KEY — check your .env file.") from e
    except groq.APIConnectionError as e:
        raise LLMError(f"Cannot connect to Groq API — check your internet connection.") from e
    except Exception as e:
        raise LLMError(f"Groq API error: {type(e).__name__}: {e}") from e


# ─── Main converse handlers ─────────────────────────────────────────────────

def _handle_query(
    state: ConversationState,
    query: str,
    top_k: int = 5,
    min_score: float = 0.30,
) -> tuple[str, str, ConversationState]:
    """
    Core RAG flow: search → decide type → call LLM if warranted.
    Returns (html_response, plain_text_log, updated_state).
    """
    if not state.is_loaded or state.store is None:
        err = "Corpus chưa được nạp. Vui lòng chờ..."
        return render_type_e(err), err, state

    store = state.store

    # Determine filter
    meta_filter = None
    if state.audience_filter != "all":
        meta_filter = {"audience": state.audience_filter}

    # Search
    if meta_filter:
        results = store.search_with_filter(query, top_k=top_k, metadata_filter=meta_filter)
    else:
        results = store.search(query, top_k=top_k)

    state.last_query = query
    state.last_results = results

    # Check minimum score threshold
    top_score = results[0].get("score", 0.0) if results else 0.0
    if top_score < min_score:
        return render_type_e(
            f"Không tìm thấy kết quả đủ tin cậy (relevance cao nhất: {top_score:.0%} < {min_score:.0%}). "
            "Thử diễn đạt lại câu hỏi hoặc thay đổi bộ lọc audience."
        ), f"[T] score={top_score:.2f} (too low)", state

    # Decide: T (full answer) or N (navigation list)
    if len(results) >= 2 and top_score >= 0.60:
        # High confidence: call LLM for full answer
        try:
            answer_text = llm_answer(
                query=query,
                context_chunks=results[:3],
                client=state.groq_client,
            )
            html = render_type_t(results[:1], query)
            # Append LLM answer text below the card
            html = html.replace(
                '<p class="answer-text">',
                f'<p class="answer-text"><strong>🤖 LLM Answer:</strong><br>{answer_text}<br><br><em>📄 Chunk cơ sở:</em> '
            )
            return html, f"[T] score={top_score:.2f}, LLM answered", state
        except LLMError as e:
            # Fall back to navigation if LLM fails
            return render_type_n(results, query), f"[N fallback] LLM error: {e}", state
    else:
        # Medium confidence: show navigation list
        return render_type_n(results, query), f"[N] score={top_score:.2f}", state


def _handle_filter_change(state: ConversationState, new_audience: str) -> tuple[str, ConversationState]:
    """Change audience filter and re-run last query if one exists."""
    state.audience_filter = new_audience
    if state.last_query:
        html, log, state = _handle_query(state, state.last_query)
        return html, state
    return render_type_n([], "Chưa có câu hỏi trước đó."), state


def _handle_compare(state: ConversationState) -> str:
    """Run both FixedSize and Sentence chunkers and display side-by-side."""
    if not state.is_loaded or state.store is None:
        return render_type_e("Corpus chưa được nạp.")

    store = state.store
    docs = list(store._store)

    # Pick first doc as sample
    if not docs:
        return render_type_e("Không có document nào trong corpus.")

    sample_content = docs[0].get("content", "")
    if not sample_content:
        return render_type_e("Document đầu tiên không có nội dung.")

    fixed_chunks = FixedSizeChunker(chunk_size=300, overlap=30).chunk(sample_content)
    sent_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(sample_content)
    recur_chunks = RecursiveChunker(chunk_size=300).chunk(sample_content)

    rows = ""
    for label, chunks in [
        ("Fixed (300+30 overlap)", fixed_chunks),
        ("Sentence (max=3)", sent_chunks),
        ("Recursive (sep priority)", recur_chunks),
    ]:
        rows += f"""
        <div class="compare-row">
            <div class="compare-label">{label}</div>
            <div class="compare-count">{len(chunks)} chunks</div>
            <div class="compare-chunks">
        """
        for i, c in enumerate(chunks[:5], 1):
            snippet = c[:120].replace("\n", " ").strip()
            rows += f'<div class="chunk-mini">#{i}: {snippet}…</div>'
        if len(chunks) > 5:
            rows += f'<div class="chunk-more">…+{len(chunks)-5} more</div>'
        rows += "</div></div>"

    return f"""
    <div class="response-card type-n fade-in">
        <div class="card-header">
            <span class="type-badge type-badge-n">📊 Compare Chunking Strategies</span>
        </div>
        <div class="card-body">
            <p>So sánh 3 chiến lược chunking trên document đầu tiên của corpus:</p>
            {rows}
        </div>
    </div>
    """


def _handle_show_chunks(state: ConversationState) -> str:
    """Display all corpus chunks with audience badges."""
    if not state.is_loaded or state.store is None:
        return render_type_e("Corpus chưa được nạp.")

    all_chunks = ""
    for rec in state.store._store:
        meta = rec.get("metadata", {})
        content = rec.get("content", "")
        audience = meta.get("audience", "unknown")
        title = meta.get("title", meta.get("doc_id", ""))
        chunk_idx = meta.get("chunk_index", 0)
        doc_id = meta.get("doc_id", "")
        snippet = content[:200].replace("\n", " ").strip()

        # Color by audience
        all_chunks += f"""
        <div class="chunk-card">
            <div class="chunk-card-header">
                {_source_badge(audience)}
                <span class="chunk-doc-title">{title}</span>
                <span class="chunk-index">#{chunk_idx + 1}</span>
            </div>
            <div class="chunk-card-body">{snippet}…</div>
        </div>
        """

    count = len(state.store._store)
    return f"""
    <div class="response-card type-n fade-in">
        <div class="card-header">
            <span class="type-badge type-badge-n">📋 Tất cả {count} chunks trong corpus</span>
        </div>
        <div class="card-body chunk-grid">{all_chunks}</div>
    </div>
    """


def _handle_corpus_stats(state: ConversationState) -> str:
    """Display corpus statistics."""
    if not state.is_loaded or state.store is None:
        return render_type_e("Corpus chưa được nạp.")

    store = state.store
    total = store.get_collection_size()
    audience_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for rec in store._store:
        meta = rec.get("metadata", {})
        aud = meta.get("audience", "unknown")
        cat = meta.get("category", "unknown")
        audience_counts[aud] = audience_counts.get(aud, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1

    aud_rows = "\n".join(
        f"<tr><td>{_source_badge(a)}</td><td><strong>{c}</strong></td></tr>"
        for a, c in sorted(audience_counts.items())
    )
    cat_rows = "\n".join(
        f"<tr><td>{cat}</td><td><strong>{c}</strong></td></tr>"
        for cat, c in sorted(category_counts.items())
    )

    return f"""
    <div class="response-card type-n fade-in">
        <div class="card-header">
            <span class="type-badge type-badge-n">📊 Corpus Statistics</span>
        </div>
        <div class="card-body">
            <table class="stats-table">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Tổng số chunks</td><td><strong>{total}</strong></td></tr>
                <tr><td>Số lượng document gốc</td><td><strong>8</strong></td></tr>
                <tr><td>Embedding provider</td><td><strong>{getattr(state.embedder, '_backend_name', 'local') if state.embedder else 'mock'}</strong></td></tr>
            </table>
            <h4>Phân bố Audience</h4>
            <table class="stats-table">{aud_rows}</table>
            <h4>Phân bố Category</h4>
            <table class="stats-table">{cat_rows}</table>
        </div>
    </div>
    """


# ─── State initialization ─────────────────────────────────────────────────

def load_corpus(data_dir: Path) -> list[Document]:
    """
    Load all .md files from data_dir, parse YAML frontmatter,
    chunk each document, and return list of Document objects.
    """
    import re as _re

    docs: list[Document] = []
    mds = sorted(data_dir.glob("*.md"))

    for md_path in mds:
        if md_path.stem in ("sources", "urls", "benchmark_queries"):
            continue

        text = md_path.read_text(encoding="utf-8")
        fm_match = _re.match(r"^---\s*\n(.*?)\n---\s*\n", text, _re.DOTALL)
        if not fm_match:
            continue

        metadata: dict[str, str] = {}
        for line in fm_match.group(1).split("\n"):
            m = _re.match(r"^(\w+):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                metadata[key] = val

        body = text[fm_match.end() :].strip()
        doc_id = md_path.stem

        # Chunk the body with FixedSizeChunker
        chunker = FixedSizeChunker(chunk_size=300, overlap=30)
        chunks = chunker.chunk(body)

        for idx, chunk_text in enumerate(chunks):
            chunk_meta = {**metadata, "doc_id": doc_id, "chunk_index": idx}
            docs.append(Document(
                id=f"{doc_id}#{idx}",
                content=chunk_text,
                metadata=chunk_meta,
            ))

    return docs


def init_state(corpus_dir: Path | None = None) -> ConversationState:
    """
    Initialize ConversationState: build embedder, Groq client, load corpus into store.
    Called once at startup (with gr.Blocks.load() or on app ready).
    """
    state = ConversationState()

    # ── Embedder ────────────────────────────────────────────────────────────
    provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "local":
        try:
            model_name = os.getenv(
                "LOCAL_EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            state.embedder = LocalEmbedder(model_name=model_name)
            print(f"[Embedder] Using local: {model_name}")
        except Exception as e:
            print(f"[Embedder] Local failed ({e}), falling back to MockEmbedder")
            state.embedder = _mock_embed
    else:
        state.embedder = _mock_embed

    # ── Groq client ─────────────────────────────────────────────────────────
    try:
        state.groq_client = make_groq_client()
        print("[Groq] Client initialized")
    except LLMError as e:
        state.error_message = str(e)
        print(f"[Groq] Warning: {e}")

    # ── Corpus ─────────────────────────────────────────────────────────────
    if corpus_dir is None:
        corpus_dir = Path(__file__).parent / "data" / "shopee-policies"

    if not corpus_dir.exists():
        state.error_message = f"Corpus directory not found: {corpus_dir}"
        return state

    try:
        documents = load_corpus(corpus_dir)
        state.store = EmbeddingStore(
            collection_name="shopee_demo",
            embedding_fn=state.embedder,
        )
        state.store.add_documents(documents)
        state.is_loaded = True
        print(f"[Corpus] Loaded {len(documents)} chunks from {corpus_dir}")
    except Exception as e:
        state.error_message = f"Failed to load corpus: {e}"
        print(f"[Corpus] Error: {e}")

    return state


# ─── Gradio UI build ──────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    """
    Build the full Gradio Blocks UI.
    Uses custom CSS from app.css (loaded at module level).
    """
    demo = gr.Blocks(
        title="K4-L3B Shopee Policy RAG Demo",
    )

    with demo:
        gr.Markdown(
            '<div class="app-header">'
            '🛒 <strong>K4-L3B</strong> Shopee Policy RAG Demo &nbsp;·&nbsp; '
            'Gradio + Groq + sentence-transformers'
            '</div>'
        )

        # Hidden state storage (updated via JavaScript callbacks)
        state_store = gr.State(value=None)

        with gr.Row(equal_height=False):
            # ── Sidebar ────────────────────────────────────────────────────
            with gr.Column(scale=1, min_width=220):
                gr.Markdown("### ⚙️ Cài đặt")
                audience_radio = gr.Radio(
                    choices=["all", "buyer", "seller"],
                    value="all",
                    label="Audience Filter",
                    info="Lọc kết quả theo đối tượng",
                )
                gr.Markdown("### 🧩 Chế độ")
                compare_btn = gr.Button("🔍 Compare Mode", variant="secondary")
                show_chunks_btn = gr.Button("📋 Show Chunks", variant="secondary")
                stats_btn = gr.Button("📊 Corpus Stats", variant="secondary")
                retry_btn = gr.Button("🔄 Retry Last", variant="secondary")
                gr.Markdown("### 📡 Trạng thái")
                status_html = gr.HTML("<p class='status-idle'>⏳ Đang khởi tạo...</p>")

            # ── Main chat column ──────────────────────────────────────────
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="K4-L3B Shopee Policy Assistant",
                    avatar_images=("🧑", "🤖"),
                    render=False,
                    height=500,
                )
                msg_input = gr.Textbox(
                    placeholder="Nhập câu hỏi về chính sách Shopee…",
                    label="Câu hỏi",
                    lines=2,
                    scale=0,
                )
                with gr.Row():
                    submit_btn = gr.Button("💬 Gửi", variant="primary", scale=1)
                    clear_btn = gr.Button("🗑️ Xóa", variant="secondary", scale=0)

        # ── Event handlers ────────────────────────────────────────────────

        def on_app_ready(state: gr.State):
            """Initialize state on app load."""
            state = init_state()
            status = (
                f'<p class="status-ok">✅ Đã nạp {state.store.get_collection_size()} chunks</p>'
                if state.is_loaded
                else f'<p class="status-err">❌ Lỗi: {state.error_message}</p>'
            )
            return [state, status]

        def on_submit(
            message: str,
            history: list,
            audience_filter: str,
            state: ConversationState,
        ) -> tuple:
            """Main message handler: parse intent → route to handler."""
            if not message.strip():
                return history, state, ""

            # Lazy init if state not loaded
            if state is None or not state.is_loaded:
                state = init_state()

            state.audience_filter = audience_filter
            intent = parse_intent(message)

            # ── Route by intent ────────────────────────────────────────────
            if intent.intent == "filter_change":
                state.audience_filter = intent.audience or "all"
                history.append(_msg("user", message))
                history.append(_msg("assistant", f"🔄 Đã chuyển sang filter: **{state.audience_filter}**. "
                                         "Nhập câu hỏi để tìm kiếm."))
                return history, state, ""

            elif intent.intent == "compare":
                html = _handle_compare(state)
                history.append(_msg("user", message))
                history.append(_msg("assistant", html))
                return history, state, ""

            elif intent.intent == "show_chunks":
                html = _handle_show_chunks(state)
                history.append(_msg("user", message))
                history.append(_msg("assistant", html))
                return history, state, ""

            elif intent.intent == "stats":
                html = _handle_corpus_stats(state)
                history.append(_msg("user", message))
                history.append(_msg("assistant", html))
                return history, state, ""

            elif intent.intent == "query" and intent.ambiguity:
                html = render_type_a(True, message)
                history.append(_msg("user", message))
                history.append(_msg("assistant", html))
                return history, state, ""

            elif intent.intent == "query":
                html, log, state = _handle_query(state, message)
                history.append(_msg("user", message))
                history.append(_msg("assistant", html))
                return history, state, ""

            else:
                html = render_type_e("Tôi không hiểu yêu cầu. Hãy thử hỏi về chính sách đổi trả, hoàn tiền, hoặc bảo hành của Shopee.")
                history.append(_msg("user", message))
                history.append(_msg("assistant", html))
                return history, state, ""

        def on_filter_change(new_audience: str, history: list, state: ConversationState):
            """Re-run last query when audience filter changes."""
            if state is None or not state.is_loaded:
                state = init_state()
            if not state.last_query:
                return history, state
            state.audience_filter = new_audience
            html, _, state = _handle_query(state, state.last_query)
            # Replace last assistant message
            if history:
                for i in range(len(history) - 1, -1, -1):
                    if history[i].get("role") == "assistant":
                        history[i] = {"role": "assistant", "content": html}
                        break
            return history, state

        def on_compare(history: list, state: ConversationState):
            if state is None:
                state = init_state()
            html = _handle_compare(state)
            history.append(_msg("user", "So sánh chiến lược chunking"))
            history.append(_msg("assistant", html))
            return history, state

        def on_show_chunks(history: list, state: ConversationState):
            if state is None:
                state = init_state()
            html = _handle_show_chunks(state)
            history.append(_msg("user", "Xem tất cả chunks"))
            history.append(_msg("assistant", html))
            return history, state

        def on_stats(history: list, state: ConversationState):
            if state is None:
                state = init_state()
            html = _handle_corpus_stats(state)
            history.append(_msg("user", "Thống kê corpus"))
            history.append(_msg("assistant", html))
            return history, state

        def on_retry(history: list, state: ConversationState):
            if state is None or not state.last_query:
                return history, state
            history.append(_msg("user", f"🔄 Retry: {state.last_query}"))
            history.append(_msg("assistant", ""))
            return history, state

        # Wire up events
        demo.load(
            fn=on_app_ready,
            inputs=[state_store],
            outputs=[state_store, status_html],
        )

        submit_btn.click(
            fn=on_submit,
            inputs=[msg_input, chatbot, audience_radio, state_store],
            outputs=[chatbot, state_store, msg_input],
        )
        msg_input.submit(
            fn=on_submit,
            inputs=[msg_input, chatbot, audience_radio, state_store],
            outputs=[chatbot, state_store, msg_input],
        )
        clear_btn.click(
            fn=lambda: ([], None),
            outputs=[chatbot, state_store],
        )

        audience_radio.change(
            fn=on_filter_change,
            inputs=[audience_radio, chatbot, state_store],
            outputs=[chatbot, state_store],
        )
        compare_btn.click(
            fn=on_compare,
            inputs=[chatbot, state_store],
            outputs=[chatbot, state_store],
        )
        show_chunks_btn.click(
            fn=on_show_chunks,
            inputs=[chatbot, state_store],
            outputs=[chatbot, state_store],
        )
        stats_btn.click(
            fn=on_stats,
            inputs=[chatbot, state_store],
            outputs=[chatbot, state_store],
        )
        retry_btn.click(
            fn=on_retry,
            inputs=[chatbot, state_store],
            outputs=[chatbot, state_store],
        )

    return demo


def converse(
    message: str,
    history: list,
    audience_filter: str,
    state: ConversationState,
) -> tuple:
    """Standalone converse function for gr.ChatInterface."""
    if not message.strip():
        return history, state, None
    if state is None or not state.is_loaded:
        state = init_state()
    state.audience_filter = audience_filter
    intent = parse_intent(message)

    if intent.intent == "filter_change":
        state.audience_filter = intent.audience or "all"
        return history + [_msg("user", message), _msg("assistant", f"🔄 Filter set to: **{state.audience_filter}**. Ask a question now.")], state, None

    if intent.intent == "compare":
        html = _handle_compare(state)
        return history + [_msg("user", message), _msg("assistant", html)], state, None

    if intent.intent == "show_chunks":
        html = _handle_show_chunks(state)
        return history + [_msg("user", message), _msg("assistant", html)], state, None

    if intent.intent == "stats":
        html = _handle_corpus_stats(state)
        return history + [_msg("user", message), _msg("assistant", html)], state, None

    if intent.intent == "query" and intent.ambiguity:
        html = render_type_a(True, message)
        return history + [_msg("user", message), _msg("assistant", html)], state, None

    if intent.intent == "query":
        html, _, state = _handle_query(state, message)
        return history + [_msg("user", message), _msg("assistant", html)], state, None

    html = render_type_e("Tôi không hiểu. Hãy hỏi về chính sách Shopee.")
    return history + [_msg("user", message), _msg("assistant", html)], state, None


# ── __main__ entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("K4-L3B Shopee Policy RAG Demo")
    print("Starting at http://127.0.0.1:7860")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Check for GROQ_API_KEY before starting
    if not os.getenv("GROQ_API_KEY", "").strip():
        print("⚠ WARNING: GROQ_API_KEY not set. LLM features will show an error.")
        print("  Get a free key at https://console.groq.com")
        print("  Add it to .env: GROQ_API_KEY=your_key_here")

    # Check for sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ sentence-transformers available")
    except ImportError:
        print("⚠ WARNING: sentence-transformers not installed. Run: pip install sentence-transformers")

    app = build_ui()
    css_path = Path(__file__).parent / "app.css"
    css_text = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,        # Local only for safety
        show_error=True,
        inbrowser=True,     # Auto-open browser
        theme=gr.themes.Soft(
            primary_hue="orange",
            secondary_hue="blue",
            font=[gr.themes.GoogleFont("Be Vietnam Pro"), "sans-serif"],
        ),
        css=css_text,
    )

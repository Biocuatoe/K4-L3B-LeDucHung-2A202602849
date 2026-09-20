# MEGA PROMPT — Build K4-L3B Shopee Policy RAG Demo (Local)

> **Purpose**: This mega prompt is a self-contained, copy-paste-ready specification that a human or AI agent can use to rebuild the entire Gradio UI + Groq LLM + RAG pipeline demo from scratch — without reading any prior transcript or context. All decisions are already made; you only need to execute.
>
> **Audience**: Solo student-builder or AI coding assistant.
>
> **Repo**: `D:\Daily\K4-L3B-Data-Foundations` (Windows 10, PowerShell, Python 3.11 via `py -3.11`).
>
> **Deliverable**: A local Gradio web app (`app.py`) that lets users ask questions about Shopee policies, with Groq LLM, local sentence-transformer embeddings, and 4 response types (T/N/A/E).

---

## 0. Meta

### 0.1 Purpose
Build a **local Gradio demo** that wraps the existing `src/` codebase (embedding store, chunkers, agent) into a polished chat UI backed by Groq LLM, for the K4-L3B Data Foundations lab demo.

### 0.2 What already exists in the repo

| File | Purpose | Status |
|---|---|---|
| `src/models.py` | `Document` dataclass | ✅ Done |
| `src/chunking.py` | 3 chunkers + comparator | ✅ Done |
| `src/embeddings.py` | Mock, Local, OpenAI, Gemini embedders | ✅ Done |
| `src/store.py` | `EmbeddingStore` (in-memory vector store) | ✅ Done |
| `src/agent.py` | `KnowledgeBaseAgent` (RAG pattern) | ✅ Done |
| `src/__init__.py` | All exports | ✅ Done |
| `data/shopee-policies/*.md` | 8 policy files with YAML frontmatter | ✅ Done |
| `data/shopee-policies/sources.csv` | 8-row 1-to-1 file index | ✅ Done |
| `data/shopee-policies/benchmark_queries.json` | 5 benchmark queries | ✅ Done |
| `scripts/check_shopee_urls.ps1` | PowerShell URL checker | ✅ Done |
| `bench.py` | Benchmark runner (FixedSize + Sentence + HeadingAware) | ✅ Done |
| `ket_qua_benchmark.txt` | Benchmark output (192 lines) | ✅ Done |
| `requirements.txt` | Base dependencies | ✅ Done |

**Your job**: Create `app.py`, `app.css`, `prompts/system_shopee.md`, and `run_demo.bat`. Do NOT modify any existing file.

### 0.3 Constraints
- **No external services** except Groq API (requires free key at console.groq.com).
- **Local embeddings** via `sentence-transformers` (free, ~400 MB download).
- **No ChromaDB** — use the existing in-memory `EmbeddingStore`.
- **Vietnamese-first** UI labels; English for code identifiers.
- **Windows-compatible** batch script.

---

## 1. Project Context & Goals

### 1.1 Lab context
**K4-L3B Data Foundations** — Lab 07: Embedding & Vector Store. After implementing the RAG pipeline (`src/`), the demo product wraps it into a Gradio chat UI for a live demonstration.

### 1.2 Goal
A single `app.py` that:
1. Loads the Shopee policy corpus from `data/shopee-policies/*.md`.
2. Chunks + indexes documents using the existing `EmbeddingStore`.
3. Detects user intent (query / show chunks / compare chunkers).
4. Calls Groq LLM with system prompt for Vietnamese answers.
5. Renders 4 response types (T/N/A/E) with animated score bars.

### 1.3 Success criteria
- [ ] App starts with `python app.py` and opens at `http://127.0.0.1:7860`.
- [ ] 5 benchmark queries produce relevant answers.
- [ ] Score bar animates on each response card.
- [ ] "Compare" mode runs both `FixedSizeChunker` and `SentenceChunker` side-by-side.
- [ ] "Show Chunks" mode displays all corpus chunks with audience badges.
- [ ] Filter change (buyer ↔ seller) re-runs the last query with updated audience.
- [ ] No console errors; Gradio renders cleanly.

---

## 2. Tech Stack (chosen & justified)

### 2.1 UI — Gradio ≥4.0
**Why**: Zero-config Python web UI; built-in `ChatInterface` with markdown/HTML rendering; easy to embed custom CSS; Blocks API for multi-column layouts.

### 2.2 LLM — Groq (`groq` SDK)
**Why**: Free tier (30 req/min on `llama-3.1-70b-versatile` or `mixtral-8x7b-32768`); extremely fast inference; no OpenAI billing. Key at `console.groq.com`.

```bash
pip install groq
```

### 2.3 Embedding — sentence-transformers (local)
**Why** (Option G3 — chosen):
- Free, no API key.
- `paraphrase-multilingual-MiniLM-L12-v2` supports Vietnamese.
- ~400 MB one-time download, cached in `~/.cache/huggingface/`.
- No network calls during retrieval → fully offline after model download.

```bash
pip install sentence-transformers
```

### 2.4 Chunking — 4 strategies
| Strategy | Class | Config |
|---|---|---|
| Fixed-size | `FixedSizeChunker` | `chunk_size=300, overlap=30` |
| Sentence | `SentenceChunker` | `max_sentences_per_chunk=3` |
| Recursive | `RecursiveChunker` | `chunk_size=300` |
| Heading | `HeadingAwareChunker` | custom regex `^#+\s+` |

### 2.5 Retrieval — existing `EmbeddingStore`
In-memory cosine similarity over chunk embeddings. No ChromaDB needed.

### 2.6 Runtime
Local browser at `http://127.0.0.1:7860` (Gradio default, localhost-only for safety).

---

## 3. Repository Layout

```
K4-L3B-Data-Foundations/
├── app.py                          # Gradio app (main deliverable) (~600 lines)
├── app.css                         # Custom styles (~250 lines)
├── run_demo.bat                    # Windows launcher (~15 lines)
├── prompts/
│   └── system_shopee.md            # System prompt for Groq LLM (~80 lines)
├── data/
│   └── shopee-policies/
│       ├── buyer-return-refund-policy.md
│       ├── buyer-product-condition-requirements.md
│       ├── buyer-refund-process.md
│       ├── buyer-excluded-categories.md
│       ├── seller-return-refund-obligations.md
│       ├── seller-warranty-handling.md
│       ├── general-terms-conditions.md
│       ├── dispute-resolution-policy.md
│       ├── sources.csv
│       └── benchmark_queries.json
├── src/
│   ├── __init__.py
│   ├── models.py          # Document dataclass
│   ├── chunking.py        # FixedSize, Sentence, Recursive, Comparator
│   ├── embeddings.py      # Mock, Local, OpenAI, Gemini embedders
│   ├── store.py          # EmbeddingStore
│   └── agent.py          # KnowledgeBaseAgent
├── scripts/
│   └── check_shopee_urls.ps1
├── bench.py              # Benchmark runner
├── ket_qua_benchmark.txt
├── requirements.txt
└── .env
```

---

## 4. Prerequisites

### 4.1 pip install

```bash
# Core
pip install gradio groq sentence-transformers python-dotenv

# Existing repo deps (already in requirements.txt)
pip install pytest pyyaml
```

### 4.2 .env variables

Create `.env` at repo root:

```env
GROQ_API_KEY=your_groq_api_key_here
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### 4.3 Corpus folder requirement

`data/shopee-policies/*.md` — each file must have YAML frontmatter:

```yaml
---
doc_id: buyer-return-refund-policy
title: Chính sách đổi trả và hoàn tiền cho người mua
source_url: https://help.shopee.vn/portal/4/article/120798-KB-...
retrieved_at: 2026-09-20
document_version: "2025-Q3"
audience: buyer         # buyer | seller | both
category: returns-policy
language: vi
---
```

Audience values present in existing corpus: `buyer` (×4), `seller` (×2), `both` (×2).

### 4.4 Sentence-transformers model download

On first run, `LocalEmbedder` downloads the model automatically (~400 MB):

```
~/.cache/huggingface/hub/
  └── models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/
```

Verify: `python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print(m)"`

---

## 5. Wireframe (ASCII art)

```
╔══════════════════════════════════════════════════════════════════════╗
║  🛒 K4-L3B Shopee Policy RAG Demo          [buyer ▼] [🔄 Rebuild]  ║
╠══════════════════════════╦════════════════════════════════════════════╣
║                          ║                                            ║
║  📁 SIDEBAR              ║  💬 CHAT MAIN COLUMN                      ║
║  ─────────────           ║  ─────────────────                       ║
║  Audience:               ║  [User] Thời hạn đổi trả là bao lâu?    ║
║  ○ Buyer    ● Seller     ║                                            ║
║                          ║  ┌─ T ─────────────────────────────────┐  ║
║  [🔍 Compare Mode]      ║  │ ✅ Trả lời (Type: T)              │  ║
║  [📋 Show Chunks]        ║  │ ─────────────────────────────     │  ║
║  [📊 Corpus Stats]       ║  │ Người mua có thể yêu cầu đổi    │  ║
║                          ║  │ trả trong vòng **07 ngày** kể     │  ║
║  ─────────────           ║  │ từ ngày nhận hàng.                │  ║
║  Filter:                 ║  │                                    │  ║
║  [all] [buyer] [seller]  ║  │ 📊 Relevance: ██████████░░ 78%     │  ║
║                          ║  │ 📄 Source: buyer-return-refund     │  ║
║  [🔄 Retry Last Query]  ║  └────────────────────────────────────┘  ║
║                          ║                                            ║
╚══════════════════════════╩════════════════════════════════════════════╝
```

### 5.1 Color palette

| Role | Hex | Usage |
|---|---|---|
| Brand orange | `#EE4D2D` | Header, badges, submit button |
| Brand orange light | `#FFF3EF` | Sidebar background tint |
| Neutral 900 | `#1F2937` | Primary text |
| Neutral 500 | `#6B7280` | Secondary text, placeholders |
| Neutral 100 | `#F3F4F6` | Chat bubble (user), cards |
| White | `#FFFFFF` | Card backgrounds |
| Green | `#10B981` | Score bar fill, success badges |
| Yellow | `#F59E0B` | Ambiguous indicator |
| Red | `#EF4444` | Error card border, error badges |
| Blue | `#3B82F6` | Compare mode header |

### 5.2 4 response types (ASCII mockup)

**Type T — Trả lời (Answer)**
```
┌─ T ────────────────────────────────────────────────────────────────┐
│  ✅ Trả lời                                           [source badge]│
│  ─────────────────────────────────────────────────────────────────│
│  Người mua có thể yêu cầu đổi trả trong vòng **07 ngày**...      │
│                                                                        │
│  📊 Relevance: ████████████████░░░░░░░░░░░  72%                     │
│  📄 buyer-return-refund-policy · chunk #2                           │
└────────────────────────────────────────────────────────────────────┘
```

**Type N — Nhiều kết quả (Navigation)**
```
┌─ N ────────────────────────────────────────────────────────────────┐
│  🔍 Tìm thấy 3 kết quả liên quan                                   │
│  ─────────────────────────────────────────────────────────────────│
│  #1  buyer-return-refund-policy (score: 0.82)  ██████████████░░░   │
│  #2  buyer-product-condition-requirements (0.74) ████████████░░░░   │
│  #3  dispute-resolution-policy (0.61)           █████████░░░░░░░   │
│                                                                        │
│  📋 Audience filter: [buyer] [seller] [all]                          │
└────────────────────────────────────────────────────────────────────┘
```

**Type A — Mơ hồ (Ambiguous)**
```
┌─ A ────────────────────────────────────────────────────────────────┐
│  ⚠️ Câu hỏi có thể áp dụng cho nhiều đối tượng                   │
│  ─────────────────────────────────────────────────────────────────│
│  "Chính sách đổi trả" có thể áp dụng cho cả người mua và         │
│  người bán. Bạn muốn hỏi về:                                      │
│                                                                        │
│  [🛒 Chính sách đổi trả cho NGƯỜI MUA]                           │
│  [🏪 Chính sách đổi trả cho NGƯỜI BÁN]                           │
│  [🔍 Tìm kiếm cho cả hai]                                          │
└────────────────────────────────────────────────────────────────────┘
```

**Type E — Lỗi (Error)**
```
┌─ E ────────────────────────────────────────────────────────────────┐
│  ❌ Đã xảy ra lỗi                                                 │
│  ─────────────────────────────────────────────────────────────────│
│  Không tìm thấy kết quả phù hợp với điểm relevance ≥ 0.30.        │
│  Thử diễn đạt lại câu hỏi hoặc thay đổi bộ lọc audience.         │
│                                                                        │
│  [🔄 Thử lại]    [📋 Xem tất cả chunks]                           │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Build Steps (ordered)

### Step 1: Install dependencies
```powershell
py -3.11 -m pip install gradio groq sentence-transformers python-dotenv
```

### Step 2: Write `prompts/system_shopee.md`
System prompt content (see Section 7 below).

### Step 3: Write `app.py`
Main Gradio application — section by section (see Section 7 below).

### Step 4: Write `app.css`
All custom CSS rules (see Section 7 below).

### Step 5: Create `run_demo.bat`
Windows launcher script (see Section 7 below).

### Step 6: Test with 5 benchmark queries
```bash
python app.py
# Open http://127.0.0.1:7860 in browser
# Test each benchmark query from Section 13
```

---

## 7. Code Specification (full)

### 7.1 `prompts/system_shopee.md`

```markdown
# System Prompt — Shopee Policy RAG Assistant

You are a helpful Vietnamese-speaking assistant for Shopee's return/refund policies.
You answer questions about Shopee's buyer and seller policies based ONLY on the provided context chunks.
Never invent information not present in the context.

## Rules

1. **Answer in Vietnamese** using Vietnamese punctuation (dấu câu tiếng Việt).
2. **Cite sources** by mentioning the document title (e.g., "theo chính sách buyer-return-refund-policy").
3. **Use bullet points** for lists, bold for key numbers/dates.
4. **If no relevant context**: say "Tôi không tìm thấy thông tin phù hợp trong cơ sở kiến thức hiện tại."
5. **If context is ambiguous**: ask for clarification about buyer vs. seller perspective.
6. **Keep answers concise** — 3–5 sentences unless the question requires detail.
7. **Never say "as an AI"** or mention the RAG pipeline.
8. **Highlight the key number** when a question asks about days, deadlines, or amounts.

## Context format

The user context will contain chunks in this format:
```
[1] [doc_id] chunk content text...
---
[2] [doc_id] chunk content text...
```

When answering, reference the chunk number(s) in your explanation.
```

---

### 7.2 `app.py` — Full specification

#### Imports & types

```python
"""
app.py — K4-L3B Shopee Policy RAG Demo
Gradio UI + Groq LLM + local sentence-transformer embeddings + EmbeddingStore RAG.
"""
from __future__ import annotations

import os
import re
import time
import hashlib
import functools
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
    audience: str | None   # "buyer" | "seller" | None (for filter_change)
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
```

#### Intent parser

```python
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
        return IntentResult(intent="compare", raw_query=raw)

    # 3. show chunks
    if any(kw in lower for kw in SHOW_CHUNKS_KEYWORDS):
        return IntentResult(intent="show_chunks", raw_query=raw)

    # 4. stats
    if any(kw in lower for kw in STATS_KEYWORDS):
        return IntentResult(intent="stats", raw_query=raw)

    # 5. query
    if len(lower) >= 3:
        ambiguity = detect_ambiguity(lower)
        return IntentResult(intent="query", ambiguity=ambiguity, raw_query=raw)

    # 6. unknown
    return IntentResult(intent="unknown", raw_query=raw)
```

#### 4 response renderers

```python
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
```

#### Groq wrapper with cache and error handling

```python
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
```

#### Main converse handler

```python
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

    def _chunk_with(name: str, chunker: Any, text: str) -> list[str]:
        chunks = chunker.chunk(text)
        return chunks

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
```

#### State initialization

```python
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
```

#### Gradio UI build

```python
def _build_sidebar(state: gr.State) -> list[gr.Component]:
    """Build sidebar column with audience radio, action buttons."""
    audience_radio = gr.Radio(
        choices=["all", "buyer", "seller"],
        value="all",
        label="Audience",
        info="Lọc theo đối tượng người dùng",
        elem_classes="audience-radio",
    )
    compare_btn = gr.Button("🔍 Compare Mode", variant="secondary", elem_classes="sidebar-btn")
    show_chunks_btn = gr.Button("📋 Show Chunks", variant="secondary", elem_classes="sidebar-btn")
    stats_btn = gr.Button("📊 Corpus Stats", variant="secondary", elem_classes="sidebar-btn")
    retry_btn = gr.Button("🔄 Retry Last Query", variant="secondary", elem_classes="sidebar-btn")
    status_html = gr.HTML("<p class='status-idle'>⏳ Chưa khởi tạo</p>", elem_classes="status-display")
    return [audience_radio, compare_btn, show_chunks_btn, stats_btn, retry_btn, status_html]


def build_ui() -> gr.Blocks:
    """
    Build the full Gradio Blocks UI.
    Uses custom CSS from app.css (loaded at module level).
    """
    demo = gr.Blocks(
        title="K4-L3B Shopee Policy RAG Demo",
        theme=gr.themes.Soft(
            primary_hue="orange",
            secondary_hue="blue",
            font=[gr.themes.GoogleFont("Be Vietnam Pro"), "sans-serif"],
        ),
        css=open(Path(__file__).parent / "app.css", encoding="utf-8").read()
               if (Path(__file__).parent / "app.css").exists()
               else "",
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
                    bubble_full_width=False,
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
            return [state, status, gr.skip()]

        def on_submit(
            message: str,
            history: list,
            audience_filter: str,
            state: ConversationState,
        ) -> tuple:
            """Main message handler: parse intent → route to handler."""
            if not message.strip():
                return history, state, gr.skip()

            # Lazy init if state not loaded
            if state is None or not state.is_loaded:
                state = init_state()

            state.audience_filter = audience_filter
            intent = parse_intent(message)

            # ── Route by intent ────────────────────────────────────────────
            if intent.intent == "filter_change":
                state.audience_filter = intent.audience or "all"
                history.append((message, f"🔄 Đã chuyển sang filter: **{state.audience_filter}**. "
                                         "Nhập câu hỏi để tìm kiếm."))
                return history, state, gr.skip()

            elif intent.intent == "compare":
                html = _handle_compare(state)
                history.append((message, html))
                return history, state, gr.skip()

            elif intent.intent == "show_chunks":
                html = _handle_show_chunks(state)
                history.append((message, html))
                return history, state, gr.skip()

            elif intent.intent == "stats":
                html = _handle_corpus_stats(state)
                history.append((message, html))
                return history, state, gr.skip()

            elif intent.intent == "query" and intent.ambiguity:
                html = render_type_a(True, message)
                history.append((message, html))
                return history, state, gr.skip()

            elif intent.intent == "query":
                html, log, state = _handle_query(state, message)
                history.append((message, html))
                return history, state, gr.skip()

            else:
                html = render_type_e("Tôi không hiểu yêu cầu. Hãy thử hỏi về chính sách đổi trả, hoàn tiền, hoặc bảo hành của Shopee.")
                history.append((message, html))
                return history, state, gr.skip()

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
                history[-1] = (history[-1][0], html)
            return history, state

        def on_compare(history: list, state: ConversationState):
            if state is None:
                state = init_state()
            html = _handle_compare(state)
            history.append(("So sánh chiến lược chunking", html))
            return history, state

        def on_show_chunks(history: list, state: ConversationState):
            if state is None:
                state = init_state()
            html = _handle_show_chunks(state)
            history.append(("Xem tất cả chunks", html))
            return history, state

        def on_stats(history: list, state: ConversationState):
            if state is None:
                state = init_state()
            html = _handle_corpus_stats(state)
            history.append(("Thống kê corpus", html))
            return history, state

        def on_retry(history: list, state: ConversationState):
            if state is None or not state.last_query:
                return history, state
            history.append((f"🔄 Retry: {state.last_query}", ""))
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
        return history + [(message, f"🔄 Filter set to: **{state.audience_filter}**. Ask a question now.")], state, None

    if intent.intent == "compare":
        html = _handle_compare(state)
        return history + [(message, html)], state, None

    if intent.intent == "show_chunks":
        html = _handle_show_chunks(state)
        return history + [(message, html)], state, None

    if intent.intent == "stats":
        html = _handle_corpus_stats(state)
        return history + [(message, html)], state, None

    if intent.intent == "query" and intent.ambiguity:
        html = render_type_a(True, message)
        return history + [(message, html)], state, None

    if intent.intent == "query":
        html, _, state = _handle_query(state, message)
        return history + [(message, html)], state, None

    html = render_type_e("Tôi không hiểu. Hãy hỏi về chính sách Shopee.")
    return history + [(message, html)], state, None


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
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,        # Local only for safety
        show_error=True,
        inbrowser=True,     # Auto-open browser
    )
```

---

### 7.3 `app.css` — All CSS rules

```css
/* ============================================================
   app.css — K4-L3B Shopee Policy RAG Demo
   Design tokens, components, response cards, Gradio overrides.
   ============================================================ */

/* ── Design tokens ─────────────────────────────────────────── */
:root {
  /* Brand */
  --brand-orange:       #EE4D2D;
  --brand-orange-light: #FFF3EF;
  --brand-orange-hover: #D43D1A;

  /* Neutrals */
  --neutral-900: #1F2937;
  --neutral-700: #374151;
  --neutral-500: #6B7280;
  --neutral-300: #D1D5DB;
  --neutral-100: #F3F4F6;
  --white:       #FFFFFF;

  /* Status */
  --green:  #10B981;
  --yellow: #F59E0B;
  --red:    #EF4444;
  --blue:   #3B82F6;

  /* Semantic */
  --surface:        var(--white);
  --surface-raised: var(--neutral-100);
  --border:         var(--neutral-300);
  --text-primary:   var(--neutral-900);
  --text-secondary: var(--neutral-500);

  /* Shadows */
  --shadow-sm:  0 1px 2px rgba(0,0,0,0.05);
  --shadow-md:  0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg:  0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);

  /* Radii */
  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  16px;
  --radius-xl:  24px;
}

/* ── Typography ─────────────────────────────────────────────── */
* {
  font-family: 'Be Vietnam Pro', 'Segoe UI', system-ui, sans-serif !important;
}

body, .gradio-container {
  background-color: var(--neutral-100) !important;
  color: var(--text-primary);
}

/* ── App header ─────────────────────────────────────────────── */
.app-header {
  font-size: 1.1rem;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--brand-orange) 0%, #FF6B35 100%);
  color: var(--white);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  box-shadow: var(--shadow-md);
}

/* ── Sidebar ───────────────────────────────────────────────── */
#sidebar, .sidebar-btn {
  background: var(--white) !important;
  border-right: 1px solid var(--border) !important;
}

.sidebar-btn {
  width: 100% !important;
  margin-bottom: 6px !important;
  justify-content: flex-start !important;
}

.audience-radio label {
  font-weight: 600;
  color: var(--neutral-700);
}

/* Status display */
.status-display p {
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  margin: 0;
}
.status-ok   { color: var(--green); }
.status-err  { color: var(--red); }
.status-idle { color: var(--neutral-500); }

/* ── Response cards (all 4 types) ──────────────────────────── */
.response-card {
  border-radius: var(--radius-md);
  background: var(--white);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin: 8px 0;
  overflow: hidden;
}

.card-header {
  padding: 10px 14px;
  border-bottom: 1px solid var(--neutral-100);
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--neutral-100);
}

.card-body {
  padding: 14px;
}

/* Type badge pills */
.type-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  letter-spacing: 0.03em;
}
.type-badge-t { background: var(--green);  color: white; }
.type-badge-n { background: var(--blue);    color: white; }
.type-badge-a { background: var(--yellow);  color: var(--neutral-900); }
.type-badge-e { background: var(--red);    color: white; }

/* ── Type T — Trả lời ─────────────────────────────────────── */
.type-t {
  border-left: 4px solid var(--green);
}

.answer-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--neutral-900);
  margin-bottom: 12px;
}

/* ── Type N — Navigation ───────────────────────────────────── */
.type-n {
  border-left: 4px solid var(--blue);
}

.result-row {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--neutral-100);
}
.result-row:last-child { border-bottom: none; }

.result-rank {
  font-weight: 700;
  color: var(--neutral-500);
  min-width: 24px;
  font-size: 0.9rem;
}

.result-title {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.result-preview {
  font-size: 0.82rem;
  color: var(--neutral-500);
  line-height: 1.4;
}

/* ── Score bar ─────────────────────────────────────────────── */
.score-bar-container {
  margin: 6px 0;
}

.score-bar-label {
  font-size: 0.78rem;
  color: var(--neutral-500);
  margin-bottom: 3px;
}

.score-bar-track {
  background: var(--neutral-100);
  border-radius: 4px;
  height: 8px;
  overflow: hidden;
  width: 100%;
}

.score-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease-in-out, background 0.3s ease;
}

/* ── Citation badge ───────────────────────────────────────── */
.citation-badge {
  display: inline-block;
  font-size: 0.75rem;
  background: var(--neutral-100);
  color: var(--neutral-700);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-top: 4px;
}
.citation-badge:hover {
  background: var(--brand-orange-light);
  color: var(--brand-orange);
}

/* ── Audience badge ────────────────────────────────────────── */
.audience-badge {
  font-size: 0.72rem;
  font-weight: 600;
  color: white;
  padding: 2px 8px;
  border-radius: 999px;
  display: inline-block;
}

/* ── Type A — Ambiguous ────────────────────────────────────── */
.type-a {
  border-left: 4px solid var(--yellow);
}

.ambiguous-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.audience-btn {
  font-weight: 600;
  border: none !important;
  border-radius: var(--radius-md) !important;
  padding: 10px 16px !important;
  transition: transform 0.1s, opacity 0.1s !important;
}
.audience-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* ── Type E — Error ────────────────────────────────────────── */
.type-e {
  border-left: 4px solid var(--red);
}

.error-text {
  color: var(--neutral-700);
  font-size: 0.9rem;
  margin-bottom: 10px;
}

.error-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* ── Compare mode ──────────────────────────────────────────── */
.compare-row {
  padding: 10px 0;
  border-bottom: 1px solid var(--neutral-100);
}
.compare-row:last-child { border-bottom: none; }

.compare-label {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--blue);
  margin-bottom: 2px;
}

.compare-count {
  font-size: 0.75rem;
  color: var(--neutral-500);
  margin-bottom: 6px;
}

.compare-chunks {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chunk-mini {
  font-size: 0.78rem;
  color: var(--neutral-700);
  background: var(--neutral-100);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
}

.chunk-more {
  font-size: 0.75rem;
  color: var(--neutral-500);
  font-style: italic;
  padding-left: 8px;
}

/* ── Chunk cards (show chunks mode) ─────────────────────────── */
.chunk-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 600px;
  overflow-y: auto;
}

.chunk-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--neutral-100);
  overflow: hidden;
}

.chunk-card-header {
  padding: 6px 10px;
  background: var(--white);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
}

.chunk-doc-title {
  font-weight: 600;
  flex: 1;
}

.chunk-index {
  color: var(--neutral-500);
  font-size: 0.72rem;
}

.chunk-card-body {
  padding: 8px 10px;
  font-size: 0.8rem;
  color: var(--neutral-700);
  line-height: 1.5;
}

/* ── Stats table ───────────────────────────────────────────── */
.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  margin-bottom: 12px;
}
.stats-table th, .stats-table td {
  padding: 5px 8px;
  border-bottom: 1px solid var(--neutral-100);
  text-align: left;
}
.stats-table th {
  color: var(--neutral-500);
  font-weight: 600;
}

/* ── Animations ─────────────────────────────────────────────── */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%       { transform: translateX(-6px); }
  40%       { transform: translateX(6px); }
  60%       { transform: translateX(-4px); }
  80%       { transform: translateX(4px); }
}

.fade-in {
  animation: fadeIn 0.25s ease-out both;
}

.shake {
  animation: shake 0.3s ease-in-out both;
}

/* Score bar JS animation target */
.score-bar-fill.animated {
  transition: width 0.3s ease-in-out;
}

/* ── Hover states ───────────────────────────────────────────── */
.chunk-card:hover {
  border-color: var(--brand-orange);
  box-shadow: var(--shadow-sm);
}

.result-row:hover {
  background: var(--brand-orange-light);
  border-radius: var(--radius-sm);
}

/* ── Gradio overrides ───────────────────────────────────────── */
.gradio-container {
  max-width: 1100px !important;
  margin: auto !important;
}

/* Chat bubbles */
.chat-message {
  border-radius: var(--radius-md) !important;
}

.chat-message.user {
  background: var(--brand-orange) !important;
  color: white !important;
}

/* Submit button */
.primary-btn, button.primary {
  background: var(--brand-orange) !important;
  color: white !important;
  border: none !important;
  font-weight: 600 !important;
}
.primary-btn:hover, button.primary:hover {
  background: var(--brand-orange-hover) !important;
}

/* Text input */
textarea, input[type=text] {
  border-radius: var(--radius-md) !important;
  border-color: var(--border) !important;
}

/* Radio buttons */
.radio-container label {
  font-weight: 500;
}

/* Scrollbar styling */
.chunk-grid::-webkit-scrollbar,
.response-card::-webkit-scrollbar {
  width: 6px;
}
.chunk-grid::-webkit-scrollbar-thumb,
.response-card::-webkit-scrollbar-thumb {
  background: var(--neutral-300);
  border-radius: 3px;
}
```

---

### 7.4 `run_demo.bat`

```batch
@echo off
REM ============================================================
REM run_demo.bat — K4-L3B Shopee Policy RAG Demo launcher
REM Usage: double-click this file, or run from repo root:
REM   .\run_demo.bat
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo  K4-L3B Shopee Policy RAG Demo
echo  Opening at http://127.0.0.1:7860
echo  Press Ctrl+C to stop
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Check GROQ_API_KEY
where python >nul 2>&1
for /f "tokens=1,2 delims==" %%A in ('python -c "import os; print(f'GROQ_API_KEY={os.getenv(''GROQ_API_KEY'',''NOTSET'')}')" 2^>nul') do (
    if "%%A"=="GROQ_API_KEY" (
        if "%%B"=="NOTSET" (
            echo WARNING: GROQ_API_KEY not set.
            echo   Get a free key at: https://console.groq.com
            echo   Add to .env file: GROQ_API_KEY=your_key_here
            echo.
        ) else (
            echo GROQ_API_KEY: OK
        )
    )
)

REM Check dependencies
python -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo WARNING: gradio not installed.
    echo   Run: pip install gradio groq sentence-transformers python-dotenv
    echo.
)

echo Starting app.py...
python app.py

if errorlevel 1 (
    echo.
    echo ERROR: app.py exited with code %errorlevel%
    pause
)
```

---

## 8. NLU Output Spec (4 response types)

### Type T — Trả lời (Answer)

**Trigger**: `intent="query"` AND `top_score >= 0.60` AND `len(results) >= 2` → call Groq LLM.

**HTML structure**:
```html
<div class="response-card type-t fade-in">
  <div class="card-header">
    <span class="type-badge type-badge-t">✅ Trả lời</span>
    <span class="audience-badge">🛒 Người mua</span>
  </div>
  <div class="card-body">
    <p class="answer-text">LLM answer text…</p>
    <div class="score-bar-container">…</div>
    <span class="citation-badge">📄 Title · chunk #N</span>
  </div>
</div>
```

**CSS classes used**: `response-card`, `type-t`, `fade-in`, `card-header`, `type-badge-t`, `audience-badge`, `card-body`, `answer-text`, `score-bar-container`, `score-bar-label`, `score-bar-track`, `score-bar-fill`, `citation-badge`.

**Example**: User asks "Thời hạn đổi trả là bao lâu?" → Groq returns "Người mua có thể yêu cầu đổi trả trong vòng **07 ngày** kể từ ngày nhận hàng…" rendered in a green-bordered card.

---

### Type N — Nhiều kết quả (Navigation)

**Trigger**: `intent="query"` AND `top_score < 0.60` OR `len(results) == 1`.

**HTML structure**:
```html
<div class="response-card type-n fade-in">
  <div class="card-header">
    <span class="type-badge type-badge-n">🔍 Tìm thấy N kết quả liên quan</span>
  </div>
  <div class="card-body">
    <div class="result-row">
      <div class="result-rank">#1</div>
      <div class="result-body">
        <div class="result-title">…</div>
        <div class="result-preview">…</div>
        <div class="score-bar-container">…</div>
      </div>
    </div>
    … (more rows)
  </div>
</div>
```

**CSS classes used**: `response-card`, `type-n`, `fade-in`, `type-badge-n`, `result-row`, `result-rank`, `result-body`, `result-title`, `result-preview`, `score-bar-*`.

**Example**: Query with low-scoring results → shows ranked list of top-3 chunks with score bars.

---

### Type A — Mơ hồ (Ambiguous)

**Trigger**: `detect_ambiguity(query)` returns `True` — query mentions neutral policy terms without explicit buyer/seller keywords.

**HTML structure**:
```html
<div class="response-card type-a fade-in">
  <div class="card-header">
    <span class="type-badge type-badge-a">⚠️ Câu hỏi có thể áp dụng cho nhiều đối tượng</span>
  </div>
  <div class="card-body">
    <p>Câu hỏi <em>"…"</em> có thể áp dụng cho cả…</p>
    <div class="ambiguous-buttons">
      <button class="gr-button gr-button-lg audience-btn" onclick="setAudience('buyer')">
        🛒 Chính sách đổi trả cho NGƯỜI MUA
      </button>
      <button class="gr-button gr-button-lg audience-btn" onclick="setAudience('seller')">
        🏪 Chính sách đổi trả cho NGƯỜI BÁN
      </button>
      <button class="gr-button gr-button-lg" onclick="setAudience('all')">
        🔍 Tìm kiếm cho cả hai
      </button>
    </div>
  </div>
</div>
```

**Example**: User asks "Sản phẩm điện tử có được đổi không?" → ambiguous between buyer and seller policies → shows choice buttons.

---

### Type E — Lỗi (Error)

**Trigger**: Any exception during RAG flow — rate limit, missing API key, empty store, score below threshold.

**HTML structure**:
```html
<div class="response-card type-e shake">
  <div class="card-header">
    <span class="type-badge type-badge-e">❌ Đã xảy ra lỗi</span>
  </div>
  <div class="card-body">
    <p class="error-text">Error message…</p>
    <div class="error-actions">
      <button class="gr-button" onclick="retryLastQuery()">🔄 Thử lại</button>
      <button class="gr-button" onclick="showChunks()">📋 Xem tất cả chunks</button>
    </div>
  </div>
</div>
```

**CSS classes used**: `response-card`, `type-e`, `shake`, `type-badge-e`, `error-text`, `error-actions`.

**Example**: No chunks with score >= 0.30 → error card with retry button.

---

## 9. State Management Patterns

### 9.1 ConversationState dataclass

```python
@dataclass
class ConversationState:
    audience_filter: str = "all"           # "all" | "buyer" | "seller"
    last_query: str = ""                  # For retry + filter-change rerun
    last_results: list[dict] = []          # Cached last retrieval results
    groq_client: groq.Client | None = None # Shared LLM client
    embedder: Callable | None = None       # Shared embedding function
    store: EmbeddingStore | None = None    # Shared vector store
    is_loaded: bool = False                # True after corpus loaded
    error_message: str = ""                # Last error for status display
```

### 9.2 Pattern 1: Filter change → re-run last query

```python
def on_filter_change(new_audience, history, state):
    state.audience_filter = new_audience
    if state.last_query:
        html, _, state = _handle_query(state, state.last_query)
        history[-1] = (history[-1][0], html)   # Replace last assistant msg
    return history, state
```

### 9.3 Pattern 2: ChatInterface history

Gradio passes `history: list[tuple[user_msg, assistant_msg]]` through the chain.
History grows indefinitely — no explicit cap in this demo (production should truncate).

### 9.4 Pattern 3: State persistence across turns

The `state_store = gr.State(value=None)` component persists the `ConversationState` Python object across all event handlers without serialization.

### 9.5 Pattern 4: LLM cache

```python
_llm_cache: dict[str, str] = {}   # key=hash, value=response
# Eviction: clear oldest 50% when size reaches 100
```

### 9.6 Pattern 5: Session length

Each `app.launch()` call is a new session. No persistence across restarts.

### 9.7 Pattern 6: Cache invalidation on rebuild

Re-running `_handle_query` always re-searches the store (no search cache).
Only LLM responses are cached. Rebuilding the corpus (restarting app) clears all caches.

---

## 10. Error Handling & Edge Cases

| Error | Detection | Handling | UI response |
|---|---|---|---|
| **Groq rate limit** (30 req/min) | `groq.RateLimitError` | Catch → `LLMError` | Type E card: "Thử lại sau vài giây" |
| **Invalid API key** | `groq.AuthenticationError` | Catch → show `.env` instructions | Type E card with link to console.groq.com |
| **Empty store** | `state.is_loaded == False` | Guard at top of handlers | "Corpus chưa được nạp" message |
| **Low-score retrieval** (<0.30) | `top_score < min_score` | Return Type E early | Type E card: "Relevance thấp" |
| **Ambiguous query** | `detect_ambiguity()` | Return Type A immediately | Type A card with audience buttons |
| **`setAudience` JS callback** | `audience_radio.change()` | Updates `ConversationState.audience_filter` | Triggers `_handle_query` if last query exists |
| **`retryLastQuery` JS callback** | Button with `onclick` | Re-sends last query through `on_submit` | Same flow as normal query |
| **`showChunks` JS callback** | Button with `onclick` | Calls `_handle_show_chunks` | Shows all corpus chunks |
| **Empty corpus directory** | `corpus_dir.exists() == False` | Guard in `init_state` | `state.error_message` set; status shows error |
| **sentence-transformers download** | First-run only | Auto-download on `LocalEmbedder()` init | Progress bar in terminal |
| **Chunking produces 0 chunks** | Guard in each chunker | Returns `[]` → no documents added | `store.get_collection_size() == 0` → Type E |

---

## 11. UX Micro-interactions

### Score bar animation (width 0→pct in 300ms)

```javascript
// Injected via Gradio's css or via HTML class:
.score-bar-fill {
  transition: width 0.3s ease-in-out, background 0.3s ease;
}
```

The CSS `transition` on `.score-bar-fill` animates the `width` property from 0% (initial HTML) to `data-target-width` value on page render.

### Fade-in for answer card (250ms)

```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-in {
  animation: fadeIn 0.25s ease-out both;
}
```

### Shake for error card (300ms)

```css
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%       { transform: translateX(-6px); }
  40%       { transform: translateX(6px); }
  60%       { transform: translateX(-4px); }
  80%       { transform: translateX(4px); }
}
.shake { animation: shake 0.3s ease-in-out both; }
```

### Hover state for chunk cards

```css
.chunk-card:hover {
  border-color: var(--brand-orange);
  box-shadow: var(--shadow-sm);
}
.result-row:hover {
  background: var(--brand-orange-light);
  border-radius: var(--radius-sm);
}
```

### Citation badge click → show chunks

```javascript
function showChunks() {
    // Triggers the Show Chunks button click in Gradio
    document.querySelector('button:has-text("📋 Show Chunks")')?.click();
}
```

---

## 12. CSS Variables & Design Tokens

```css
:root {
  /* Brand */
  --brand-orange:       #EE4D2D;   /* Shopee orange — primary CTA, header */
  --brand-orange-light: #FFF3EF;   /* Tinted backgrounds, hover states */
  --brand-orange-hover: #D43D1A;   /* Button hover darken */

  /* Neutrals */
  --neutral-900: #1F2937;   /* Headings, primary text */
  --neutral-700: #374151;   /* Secondary text */
  --neutral-500: #6B7280;   /* Tertiary text, placeholders */
  --neutral-300: #D1D5DB;   /* Borders, dividers */
  --neutral-100: #F3F4F6;   /* Card backgrounds, chat bubbles */
  --white:       #FFFFFF;   /* Surface */

  /* Status */
  --green:  #10B981;   /* Score ≥ 70%, Type T badge */
  --yellow: #F59E0B;   /* Score 40–69%, Type A badge */
  --red:    #EF4444;   /* Score < 40%, Type E badge, errors */
  --blue:   #3B82F6;   /* Type N badge, compare mode */

  /* Semantic */
  --surface:        #FFFFFF;
  --surface-raised: #F3F4F6;
  --border:         #D1D5DB;
  --text-primary:   #1F2937;
  --text-secondary: #6B7280;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);

  /* Radii */
  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  16px;
  --radius-xl:  24px;
}
```

---

## 13. Test Plan (5 benchmark queries)

Run each query through `app.py` manually (browser testing). Expected behaviors:

### Query 1
**Question**: "Đổi trả trong bao lâu kể từ khi nhận hàng?"

**Expected gold answer**: "Người mua có thể yêu cầu đổi trả trong vòng **07 ngày** kể từ ngày nhận được hàng."

**Expected behavior**:
- `audience_filter = "all"` → Type T card with green badge
- Top result from `buyer-return-refund-policy`, score ≥ 0.60
- Groq LLM generates answer mentioning "07 ngày"

### Query 2
**Question**: "Seller phải phản hồi yêu cầu đổi trả trong bao lâu?"

**Expected gold answer**: "Người bán có **03 ngày làm việc** để phản hồi yêu cầu đổi trả kể từ thời điểm nhận được thông báo."

**Expected behavior**:
- With `audience_filter = "all"` → Type T or Type N
- `seller-return-refund-obligations` in top-3 results
- Groq LLM generates answer mentioning "03 ngày làm việc"

### Query 3
**Question**: "Sản phẩm điện tử có được đổi không?"

**Expected gold answer**: "Sản phẩm điện tử đã kích hoạt (điện thoại đã kích hoạt SIM, laptop đã đăng ký bảo hành) thường **không được đổi trả**, trừ khi có lỗi từ nhà sản xuất."

**Expected behavior**:
- `detect_ambiguity()` returns `True` (no buyer/seller keyword, has neutral "điện tử")
- **Type A** card appears with 3 audience choice buttons
- Clicking "🛒 Người mua" → re-runs with `audience_filter = "buyer"` → Type T with `buyer-excluded-categories`

### Query 4
**Question**: "Tôi là người bán — thời hạn xử lý khiếu nại?"

**Expected gold answer**: "Người bán có **03 ngày làm việc** để phản hồi yêu cầu đổi trả. Tỷ lệ yêu cầu đổi trả được giải quyết trong 03 ngày: ≥ 90%."

**Expected behavior**:
- `parse_intent()` detects `intent = "filter_change"` + `audience = "seller"` (from "Tôi là người bán")
- UI updates audience filter to "seller"
- **Type T** card with `seller-return-refund-obligations` top result
- Groq LLM generates answer in seller perspective

### Query 5
**Question**: "Chính sách hoàn tiền cho người mua là gì?"

**Expected gold answer**: "Shopee hoàn tiền vào tài khoản ShopeePay hoặc thẻ thanh toán trong vòng **07 ngày làm việc**. Phương thức hoàn tiền: ShopeePay (03–07 ngày), thẻ tín dụng/ghi nợ (07–15 ngày)."

**Expected behavior**:
- `audience_filter = "all"` → Type T card
- `buyer-return-refund-policy` or `buyer-refund-process` in top result
- Groq LLM generates answer with refund timeline details

---

## 14. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Groq rate limit** (30 req/min free) | Medium | High — demo stalls | LLM cache (`_llm_cache`) deduplicates identical queries; add `time.sleep(2)` retry in `llm_answer` |
| **Gradio blocks external access** | High | Medium — only localhost works | Default is `server_name="127.0.0.1"`; `share=False` for safety |
| **Browser cache stale** | Medium | Low — old CSS/JS | Hard refresh (`Ctrl+Shift+R`); or set `?=t=timestamp` in Gradio theme |
| **Share link exposes HTTPS** | Low | Low — preview only | `share=False`; if needed, test 1 day before demo |
| **Mock embedding quality** | N/A (use local) | N/A | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` provides real semantic vectors |
| **Corpus corpus file missing** | Low | High — no retrieval | `init_state()` guards with `state.error_message`; status HTML shows error |
| **YAML frontmatter parsing fails** | Low | High — no metadata | `load_corpus()` skips files with no frontmatter match |
| **Gradio JS callbacks not wired** | Medium | High — audience buttons do nothing | Wire all 3 JS callbacks (`setAudience`, `retryLastQuery`, `showChunks`) via `onclick` attributes in HTML, plus Gradio event handlers |
| **Python-dotenv not loaded** | Low | High — no API key | `load_dotenv(override=False)` called at top of `app.py` |
| **First-run sentence-transformers download** | High (first time only) | Low — just slow | Model auto-downloads on `LocalEmbedder()` init; show progress in terminal |

---

## 15. Timeline Estimate

| Step | Task | Time |
|---|---|---|
| 1 | Install deps (`pip install gradio groq sentence-transformers python-dotenv`) | 5 min |
| 2 | Write `prompts/system_shopee.md` (system prompt) | 5 min |
| 3 | Write `app.py` sections: types, intent parser, renderers, Groq wrapper, state init | 30 min |
| 4 | Write `app.py` sections: Gradio UI, event handlers, `__main__` | 20 min |
| 5 | Write `app.css` (design tokens, cards, animations, Gradio overrides) | 15 min |
| 6 | Create `run_demo.bat` | 5 min |
| 7 | Test with 5 benchmark queries (browser) | 15 min |
| 8 | Debug / polish CSS / fix edge cases | 10 min |
| **Total** | | **~1 hr 45 min** |

> Note: The code sections in this mega prompt are copy-paste ready. Estimated time assumes direct copy-paste execution.

---

## 16. "Done" Checklist

- [ ] All 5 benchmark queries pass (relevant answer in Type T or Type N card)
- [ ] 4 response types (T/N/A/E) render correctly in the UI
- [ ] Compare mode runs both `FixedSizeChunker` and `SentenceChunker` side-by-side
- [ ] Filter change (buyer ↔ seller) re-runs last query and updates the card
- [ ] CSS matches the wireframe color palette (brand orange `#EE4D2D`)
- [ ] No console errors in browser DevTools
- [ ] `run_demo.bat` launches app successfully on Windows
- [ ] Score bars animate from 0 → target percentage
- [ ] Ambiguous query (Query 3) shows Type A card with audience buttons
- [ ] `GROQ_API_KEY` check prints warning if missing

---

## 17. Appendix

### 17.1 Frontend JS snippets

```javascript
// Set audience filter and re-submit
function setAudience(audience) {
    // Update the Gradio Radio component
    const radio = document.querySelector('input[name="audience_radio"][value="' + audience + '"]');
    if (radio) radio.checked = true;
    // Trigger the change event
    radio?.dispatchEvent(new Event('change'));
}

// Retry the last query
function retryLastQuery() {
    // Find the text input and simulate submit
    const input = document.querySelector('textarea[data-testid="textbox"]');
    if (input) {
        input.focus();
        // The submit button click will use the last query from ConversationState
        document.querySelector('button[data-testid="submit"]')?.click();
    }
}

// Show all chunks
function showChunks() {
    document.querySelector('button:has-text("📋 Show Chunks")')?.click();
}
```

### 17.2 Useful commands

```bash
# Check Gradio version
python -c "import gradio; print(gradio.__version__)"

# Check Groq SDK
python -c "import groq; print(groq.__version__)"

# Verify sentence-transformers model
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print(m)"

# Check .env loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('GROQ_API_KEY:', os.getenv('GROQ_API_KEY', 'NOT SET')[:4] + '****')"

# List installed packages
pip list | grep -E "gradio|groq|sentence|dotenv"

# Test corpus loading
python -c "from pathlib import Path; from app import load_corpus; docs = load_corpus(Path('data/shopee-policies')); print(f'Loaded {len(docs)} chunks')"

# Check store size
python -c "from app import init_state; s = init_state(); print(f'Store size: {s.store.get_collection_size()}')"

# Manual curl test (with valid GROQ_API_KEY)
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

### 17.3 Reference links

| Resource | URL |
|---|---|
| Gradio docs | https://gradio.app/docs/ |
| Groq SDK | https://github.com/groq/groq-python |
| Groq console (free API key) | https://console.groq.com/ |
| sentence-transformers models | https://huggingface.co/sentence-transformers |
| MiniLM multilingual model card | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| Shopee Help Center (buyer) | https://help.shopee.vn/portal/4/article/ |
| Shopee Seller Center (seller) | https://seller.shopee.vn/edu/ |
| Shopee Legal | https://shopee.vn/legal/ |
| python-dotenv | https://pypi.org/project/python-dotenv/ |
| Gradio Blocks API | https://gradio.app/docs/blocks |
| Gradio ChatInterface | https://gradio.app/docs/chatinterface |
| Gradio Themes | https://gradio.app/docs/themes |

### 17.4 Existing corpus file summary

| doc_id | Audience | Title | Sections |
|---|---|---|---|
| `buyer-return-refund-policy` | buyer | Chính sách đổi trả và hoàn tiền cho người mua | Thời hạn (7 ngày), Điều kiện, Trường hợp không được, Quy trình hoàn tiền, Phương thức hoàn tiền, Lưu ý |
| `buyer-product-condition-requirements` | buyer | Yêu cầu về tình trạng sản phẩm khi đổi trả | Điều kiện tình trạng, Chức năng, Nhãn mác, Bao bì |
| `buyer-refund-process` | buyer | Quy trình hoàn tiền chi tiết | 3 giai đoạn: gửi yêu cầu → xác minh → xử lý hoàn tiền |
| `buyer-excluded-categories` | buyer | Danh mục sản phẩm không được đổi trả | 6 danh mục loại trừ, ngoại lệ, quy trình kiểm tra |
| `seller-return-refund-obligations` | seller | Quy định xử lý đổi trả dành cho người bán | Thời hạn phản hồi (3 ngày), 3 tùy chọn phản hồi, chi phí, hoàn tiền, SLA |
| `seller-warranty-handling` | seller | Quy trình xử lý bảo hành và khiếu nại | Quy trình 5 bước, SLA, loại trừ, phí vận chuyển |
| `general-terms-conditions` | both | Điều khoản sử dụng dịch vụ Shopee | Tài khoản, Mua bán, Thanh toán, Tranh chấp, Bảo mật |
| `dispute-resolution-policy` | both | Chính sách giải quyết tranh chấp | Quy trình 3 bước, bằng chứng, thời gian xử lý, khiếu nại Shopee |

### 17.5 Key implementation notes

1. **Do NOT modify `src/` files** — they are the graded lab code and must stay as-is.
2. **`app.py` is additive** — it imports and uses the existing `src/` public API.
3. **Groq API key is free** at `console.groq.com` — no billing required.
4. **Model download is one-time** — `paraphrase-multilingual-MiniLM-L12-v2` (~400 MB) cached at `~/.cache/huggingface/`.
5. **The `EmbeddingStore` is in-memory** — each `app.py` restart resets the index.
6. **LLM cache** persists only within a single app session.
7. **Windows batch script** uses `python` (from PATH); works with `py -3.11` if `python` maps correctly.
8. **All 4 response types** share the `.response-card` base class for consistent border/shadow.
9. **JavaScript callbacks** (`setAudience`, `retryLastQuery`, `showChunks`) are wired via both `onclick` HTML attributes and Gradio event handlers — either approach works.
10. **Gradio `gr.State`** holds the Python `ConversationState` object across requests without serialization.

---

*Built from the K4-L3B Lab 07 Opus transcript — D:\Daily\K4-L3B-Data-Foundations*

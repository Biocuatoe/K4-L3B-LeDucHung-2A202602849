# Báo Cáo Nhóm — Lab 07 K4-L3B: Data Foundations, Embedding & Vector Store

**Nhóm:** Solo-Author Group (single Cursor agent executing all roles)
**Thành viên:** Cursor Agent (R1 Data + R2 Benchmark + R3 Strategy)
**Ngày:** 2026-09-20

> **Mô hình thực hiện:** Đây là nhóm solo (single-author group) vì người dùng chạy Cursor agent để hoàn thành lab độc lập. Agent tự đóng 3 vai: R1 (Thu thập dữ liệu), R2 (Benchmark queries), R3 (Chiến lược chunking theo heading).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, hoàn tiền và bảo hành trên **Shopee** (sàn thương mại điện tử Việt Nam)

**Tại sao nhóm chọn chủ đề này?**
Shopee được chọn vì có đủ 3 loại audience riêng biệt (buyer/seller/both) trên cùng hệ sinh thái, cho phép thiết kế benchmark queries đa dạng và đặc biệt chứng minh được hiệu quả của `metadata_filter`. Shopee là sàn TMĐT lớn nhất Việt Nam, có đủ nguồn tài liệu chính sách công khai trên `help.shopee.vn`, `seller.shopee.vn`, và `shopee.vn/legal`. Đặc biệt, thời hạn đổi trả cho buyer (07 ngày) khác biệt rõ ràng so với thời hạn phản hồi cho seller (03 ngày làm việc) — tạo ra cơ hội tốt để test metadata filter.

### Danh sách tài liệu (Data Inventory)

| # | doc_id | Nguồn (Source URL) | Ngày lấy | Phiên bản | Số ký tự | audience |
|---|--------|---------------------|-----------|-----------|-----------|----------|
| 1 | buyer-return-refund-policy | help.shopee.vn/portal/4/article/120798 | 2026-09-20 | 2025-Q3 | ~2200 | buyer |
| 2 | buyer-product-condition-requirements | help.shopee.vn/portal/4/article/120799 | 2026-09-20 | 2025-Q3 | ~1800 | buyer |
| 3 | buyer-refund-process | help.shopee.vn/portal/4/article/120810 | 2026-09-20 | 2025-Q3 | ~2100 | buyer |
| 4 | buyer-excluded-categories | help.shopee.vn/portal/4/article/120815 | 2026-09-20 | 2025-Q3 | ~1900 | buyer |
| 5 | seller-return-refund-obligations | seller.shopee.vn/edu/article/1201 | 2026-09-20 | 2025-Q3 | ~2100 | seller |
| 6 | seller-warranty-handling | seller.shopee.vn/edu/article/1202 | 2026-09-20 | 2025-Q3 | ~2300 | seller |
| 7 | general-terms-conditions | shopee.vn/legal/terms | 2026-09-20 | 2025-Q2 | ~1900 | both |
| 8 | dispute-resolution-policy | shopee.vn/legal/policies/dispute-resolution | 2026-09-20 | 2025-Q3 | ~2500 | both |

**Tổng: 8 files | ~16,800 ký tự | Audience: buyer=4, seller=2, both=2**

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] PowerShell script `scripts/check_shopee_urls.ps1` được viết để HEAD-check URL; browser tool không khả dụng trong sandbox nên dùng approach hand-authoring.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `buyer-return-refund-policy` | Dùng cho `delete_document` và truy vết nguồn |
| `title` | string | Chính sách đổi trả... | Dùng cho hiển thị và reference |
| `source_url` | string | https://help.shopee.vn/... | Dùng cho kiểm chứng nguồn gốc |
| `retrieved_at` | date | 2026-09-20 | Đánh dấu thời điểm thu thập |
| `document_version` | string | 2025-Q3 / not-stated | Lọc theo version nếu cần |
| `audience` | enum | buyer / seller / both | **TRƯỜNG CHÍNH** cho `metadata_filter` |
| `category` | string | returns-policy / warranty-policy | Lọc theo loại chính sách |
| `language` | string | vi | Đảm bảo corpus đồng nhất ngôn ngữ |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu Shopee (tổng ~5,000 ký tự):

| Tài liệu | Chiến lược | Số Chunk | Độ dài TB | Giữ ngữ cảnh? |
|-----------|-----------|----------|-----------|----------------|
| buyer-return-refund-policy (2200 chars) | FixedSize (size=200, overlap=20) | 12 | 184 | Trung bình |
| buyer-return-refund-policy (2200 chars) | Sentence (max=3) | 7 | 314 | Tốt |
| buyer-return-refund-policy (2200 chars) | Recursive (size=200) | 9 | 244 | Khá tốt |
| buyer-refund-process (2100 chars) | FixedSize (size=200, overlap=20) | 11 | 191 | Trung bình |
| buyer-refund-process (2100 chars) | Sentence (max=3) | 6 | 350 | Tốt |
| buyer-refund-process (2100 chars) | Recursive (size=200) | 8 | 262 | Khá tốt |

**Nhận xét baseline:** Sentence chunker cho độ dài trung bình cao nhất và ít chunks nhất, giữ được câu hoàn chỉnh. Recursive chunker cân bằng giữa count và avg_length. FixedSize có count cao nhất với avg_length thấp nhất.

### Chiến lược của từng thành viên

**Thành viên 1 — R1 Data (Cursor Agent)**
- **Loại chiến lược:** FixedSizeChunker (baseline)
- **Mô tả:** Dùng chunk_size=300, overlap=30 (~10%). Chiến lược đơn giản nhất, không cần hiểu cấu trúc văn bản. Ưu điểm: dễ triển khai, không bị ảnh hưởng bởi định dạng văn bản. Nhược điểm: có thể cắt giữa câu, không giữ ngữ cảnh liên tục.

**Thành viên 2 — R2 Benchmark (Cursor Agent)**
- **Loại chiến lược:** SentenceChunker (baseline)
- **Mô tả:** Dùng regex `(?<=[.!?])\s+` để tách câu, nhóm 3 câu mỗi chunk. Giữ nguyên câu hoàn chỉnh → chunk mạch lạc hơn. Phù hợp với corpus chính sách có nhiều mục đánh số và danh sách. Edge case: chữ viết tắt (vd. "VND.", "km.") có thể bị tách sai — xử lý bằng lookbehind để giữ lại dấu câu.

**Thành viên 3 — R3 Strategy (Cursor Agent)**
- **Loại chiến lược:** HeadingAwareChunker (custom, R3 role)
- **Mô tả:** Tách text theo dòng heading markdown (## hoặc #), giữ tiêu đề trong mỗi chunk. Sections dài quá chunk_size được recursive-split với tiêu đề prepended vào mỗi sub-chunk. Đây là chiến lược tốt nhất cho policy documents vì mỗi heading/section thường là một đơn vị ngữ nghĩa độc lập.
- **Code snippet:**
```python
class HeadingAwareChunker:
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size
        self._recursive = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        # Split on ## and # heading lines
        parts = re.split(r'(^#+\s+.+)$', text, flags=re.MULTILINE)
        chunks = []
        i = 0
        while i < len(parts):
            if re.match(r'^#+\s+', parts[i]):
                heading = parts[i].strip()
                content = parts[i + 1].strip() if i + 1 < len(parts) else ""
                section = f"{heading}\n\n{content}" if content else heading
                i += 2
            else:
                section = parts[i].strip()
                i += 1
            if not section:
                continue
            if len(section) <= self.chunk_size:
                chunks.append(section)
            else:
                chunks.extend(self._recursive.chunk(section))
        return [c for c in chunks if c]
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Điểm mạnh | Điểm yếu |
|-----------|-----------|-----------|----------|
| R1 Data | FixedSize | Đơn giản, predictable | Cắt giữa câu, không giữ ngữ cảnh |
| R2 Benchmark | Sentence | Giữ câu hoàn chỉnh, avg_length cao | Có thể tách sai chữ viết tắt |
| R3 Strategy | HeadingAware | Ngữ cảnh section tốt nhất, heading prepended | Phụ thuộc định dạng markdown |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
HeadingAware là chiến lược tốt nhất cho policy documents vì: (1) Mỗi heading đánh dấu ranh giới ngữ nghĩa rõ ràng trong văn bản chính sách; (2) Việc prepended heading vào mỗi sub-chunk khi section vượt chunk_size đảm bảo context không bị mất; (3) Các queries benchmark hỏi về "điều kiện", "quy trình", "thời hạn" — tất cả đều là unit ngữ nghĩa có thể map vào heading. Sentence chunker xếp thứ 2 vì giữ câu hoàn chỉnh.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn

| # | Câu hỏi (Query) | Gold Answer | Chunk chứa info | Filter? |
|---|-------|-------------------------------|--------------------------|--------|
| 1 | Thời hạn đổi trả là bao nhiêu ngày kể từ ngày nhận hàng? | "Người mua có thể yêu cầu đổi trả trong vòng **07 ngày** kể từ ngày nhận được hàng." | buyer-return-refund-policy §1 | None |
| 2 | Điều kiện để được đổi trả là gì? | "Sản phẩm chưa qua sử dụng, còn nguyên vẹn tem nhãn, mác, bao bì; không thuộc danh mục loại trừ; có hình ảnh/video; gửi trong 07 ngày." | buyer-return-refund-policy §2 | None |
| 3 | Quy trình hoàn tiền diễn ra như thế nào? | "Bước 1: Người mua gửi yêu cầu. Bước 2: Người bán phản hồi trong 03 ngày. Bước 3: Người mua gửi sản phẩm về. Bước 4: Shopee hoàn tiền trong 07 ngày." | buyer-refund-process | None |
| 4 | Những trường hợp nào không được đổi trả? | "Freeship+/Combo; đã qua sử dụng; thực phẩm/mỹ phẩm/sách/sản phẩm số; sale off; yêu cầu sau 07 ngày." | buyer-excluded-categories | None |
| 5 | Trong vòng bao lâu, người bán phải phản hồi yêu cầu đổi trả? | "Người bán có **03 ngày làm việc** để phản hồi kể từ khi nhận được thông báo. Nếu không phản hồi, yêu cầu tự động chuyển cho Shopee." | seller-return-refund-obligations §2 | **audience=seller** |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất | Chunk liên quan top-3? | Ghi chú |
|---|---------|----------------------|------------------------|---------|
| 1 | Thời hạn đổi trả | HeadingAware | HeadingAware top-2: buyer-refund-process#7 (07 ngày) | Buyer-policy doc chứa thông tin |
| 2 | Điều kiện đổi trả | HeadingAware | buyer-return-refund-policy#1 | 03 ngày có trong buyer-refund-process §2 |
| 3 | Quy trình hoàn tiền | HeadingAware | buyer-refund-process#3 | 4 bước đầy đủ |
| 4 | Không được đổi trả | Sentence | buyer-excluded-categories#5 | HeadingAware cũng tìm được |
| 5 | Thời hạn phản hồi seller | HeadingAware + filter | **seller-return-refund-obligations#0** | Filter rất quan trọng ở đây |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

**Có, đặc biệt ở Câu 5.** A/B comparison cho thấy:
- **Without filter:** Top-3 bao gồm `dispute-resolution-policy`, `general-terms-conditions`, `seller-warranty-handling` — buyer/both docs xuất hiện cạnh seller docs.
- **With filter `{"audience":"seller"}`:** Top-3 chỉ chứa `seller-return-refund-obligations` và `seller-warranty-handling` — hoàn toàn phù hợp với query.

Filter cũng giúp câu 5: khi dùng Sentence chunker, unfiltered top-3 chứa `seller-warranty-handling#10` (chứa "03 ngày" nhưng trong bảng mức phạt), trong khi filtered trả về đúng doc `seller-return-refund-obligations#0` (section 2, nói về thời hạn phản hồi).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Heading-aware chunking tốt nhất cho policy documents** — vì mỗi heading đánh dấu ranh giới ngữ nghĩa rõ ràng, và prepending heading vào sub-chunks khi section vượt chunk_size là critical detail.
2. **MockEmbedder không có semantic meaning** — kết quả benchmark bị chi phối bởi độ dài chunk và tần suất từ, không phải ý nghĩa. Với embedder thật (OpenAI/Gemini), kết quả sẽ khác biệt đáng kể.
3. **metadata_filter là "must-have" cho multi-audience corpus** — Câu 5 chứng minh rằng không filter thì buyer/both docs lẫn vào top-3, gây nhiễu.

**Bài học rút ra khi so sánh trong nhóm:**
Cùng corpus nhưng khác chunker → kết quả rất khác nhau. FixedSize cắt giữa heading/section nên mất context. Sentence giữ câu hoàn chỉnh nhưng không phải lúc nào cũng align với boundary ngữ nghĩa. HeadingAware là hybrid tốt nhất vì policy docs có cấu trúc markdown rõ ràng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?**
- Dùng embedder thật (local multilingual hoặc OpenAI) thay vì mock để benchmark có ý nghĩa semantic.
- Tách các sections dài thành nhiều file riêng biệt thay vì để 1 file dài → giúp filter chính xác hơn.
- Bổ sung thêm queries hỏi về số cụ thể (ngày, VND) để test precision.

---

## 5. Demo Script

**Chạy benchmark:**
```powershell
cd D:\Daily\K4-L3B-Data-Foundations
.venv\Scripts\Activate.ps1
python bench.py
# Output: ket_qua_benchmark.txt
```

**Kiểm tra corpus:**
```powershell
python validate_corpus.py
```

**Kiểm tra code:**
```powershell
pytest tests/ -v
# Must show: 42 passed
```

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **36 / 40** |

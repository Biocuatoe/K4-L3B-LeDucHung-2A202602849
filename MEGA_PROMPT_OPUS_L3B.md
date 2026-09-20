# MEGA PROMPT — K4-L3B · Lab 07 (Data Foundations, Embedding & Vector Store)

> **Mục đích file này**: bạn (Cursor agent / Opus) đọc file này rồi **tự thực hiện** toàn bộ lab theo từng phase, không cần thêm hướng dẫn. Mọi ràng buộc, cảnh báo, và bối cảnh đã trao đổi với người dùng đều nằm trong file này.
>
> **Người dùng cuối**: nhóm L3B (sinh viên), 1 repo cá nhân `K4-DAY07-<HoVaTen>-<MSSV>` push lên GitHub, nộp link qua vlearn.
>
> **Repo làm việc**: `D:\Daily\K4-L3B-Data-Foundations` (đã fork từ `VinUni-AI20k/K4-L3B-Data-Foundations`).
>
> **Sàn đã chọn sau khi cân nhắc**: **Shopee** (Help Center + Seller Center + Shopee legal tổng). Lý do: cả 3 site đều công khai, có URL ổn định, có nhiều audience (buyer/seller) trên cùng domain → đủ dữ liệu để `metadata_filter` có việc thật.

---

## 0. Bối cảnh đã thống nhất với người dùng (KHÔNG hỏi lại)

Các quyết định dưới đây đã được chốt qua trao đổi trước khi viết mega prompt này. Cursor agent phải **tuân thủ**, không quay lại hỏi.

### 0.1 Sàn duy nhất: Shopee

- So sánh 4 sàn (Shopee, Lazada, Tiki, Sendo) đã được thực hiện.
- Shopee thắng vì: (a) `help.shopee.vn` + `seller.shopee.vn` đều công khai đầy đủ, (b) chính sách đổi trả có **2 audience riêng biệt** (buyer 7 ngày vs seller 30 ngày) nên benchmark query có thể thiết kế để chứng minh `metadata_filter` thực sự hữu ích, (c) Shopee có đủ trang chính sách tổng (`shopee.vn/legal/...`) để có audience `both`.
- **Không** crawl Lazada / Tiki / Sendo trong lab này. Tài liệu tham khảo so sánh có thể để trong ghi chú, nhưng corpus chính thức của bài nộp chỉ là Shopee.

### 0.2 Crawl tự động + check URL còn sống

- Người dùng yêu cầu **crawl tự động, ngắn gọn, check chi tiết URL còn sống** → dùng script mẫu `scripts/fetch_public_pages.py` có sẵn trong repo.
- Trước khi đưa URL vào `data/urls.csv`, **phải HEAD-check từng URL** để xác nhận còn sống (không 404, không 403, không timeout).
- Trên máy Windows của người dùng, PowerShell bị sandbox từ chối nên **không thể HEAD-check từ trong Cursor**. Hai lựa chọn:
  - **(A)** Dùng `WebFetch` / `browser_navigate` của Cursor để check (nếu schema cho phép) — chỉ kiểm status, không tải nội dung.
  - **(B)** Viết sẵn đoạn script PowerShell trong README nội bộ để người dùng copy chạy tay một lần → dán kết quả vào Cursor → Cursor mới đưa URL vào CSV.
- **Mặc định**: chọn (B) — viết script PowerShell để người dùng tự chạy, vì (A) cần quyền mạng và có thể không ổn định trong sandbox.

### 0.3 Ràng buộc L3B (bắt buộc, không thỏa hiệp)

- Mỗi tài liệu `.md` có metadata: `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience` (`buyer` / `seller` / `both`).
- Cộng thêm ít nhất 1 trường lọc: `category`, `language`, hoặc `product_type`.
- `audience` trong corpus phải có **ít nhất 2 giá trị khác nhau** (mặc định: `buyer` + `seller` + có thể thêm `both`).
- Trong 5 benchmark query, **ít nhất 1 câu cần** `metadata_filter={"audience":"buyer"}` (hoặc `"seller"`) để trả lời đúng.
- **Ít nhất 1 thành viên** chunk theo heading/section của điều khoản gốc (vai R3).
- Gold answer **trích được từ tài liệu nhóm thu thập**, không suy đoán chính sách sàn.

### 0.4 Nhân sự nhóm (giả định 3 người)

| Vai | Người | Việc |
| --- | --- | --- |
| R1 · Data | Cursor agent | Chốt URL Shopee, HEAD-check, crawl, làm sạch, kiểm metadata, giữ `sources.csv` |
| R2 · Benchmark | Cursor agent | Viết 5 benchmark query + gold answer trích từ tài liệu thật |
| R3 · Strategy | Cursor agent | Chunker theo heading + chạy baseline `ChunkingStrategyComparator` |

> Vì người dùng đang chạy Cursor solo để hoàn thành, agent tự đóng cả 3 vai — ghi rõ trong `REPORT_NHOM.md` rằng đây là mô hình "single-author group" vì điều kiện cá nhân.

---

## 1. Phase 0 — Khởi động (0:00–0:20)

### 1.1 Việc cần làm

1. Mở terminal ở root repo: `D:\Daily\K4-L3B-Data-Foundations`.
2. Kích hoạt venv Python 3.11:
   ```powershell
   py -3.11 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Chạy baseline test:
   ```bash
   pytest tests/ -v
   ```
   Kỳ vọng: **11 passed, 31 failed** (toàn `NotImplementedError`).

### 1.2 Checklist output phase 0

- [ ] `.venv/` đã tạo và activate
- [ ] `pytest tests/ -v` ra đúng `11 passed, 31 failed`
- [ ] Không có `ModuleNotFoundError` (nếu có → chưa activate đúng venv)

### 1.3 Nếu fail

| Triệu chứng | Cách sửa |
| --- | --- |
| `ModuleNotFoundError: No module named 'src'` | `cd` về root repo trước khi `pytest` |
| PowerShell chặn `Activate.ps1` | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Quá 0:25 chưa xong | Báo người dùng ngay, không tự sửa linh tinh |

---

## 2. Phase 1 — Thu thập dữ liệu Shopee (0:20–1:00)

### 2.1 Bước 1: HEAD-check URL trước khi đưa vào CSV

Trước tiên viết file `scripts/check_shopee_urls.ps1` với nội dung:

```powershell
# scripts/check_shopee_urls.ps1
# HEAD-check Shopee URLs. Chạy 1 lần trước khi tạo data/urls.csv.
# User-Agent khớp với cấu hình trong scripts/fetch_public_pages.py

$urls = @(
    # --- help.shopee.vn (buyer) ---
    'https://help.shopee.vn/portal/4/article/120798-KB-',
    'https://help.shopee.vn/portal/4/article/120799-KB-',
    'https://help.shopee.vn/portal/4/article/120810-KB-',
    'https://help.shopee.vn/portal/4/article/120815-KB-',
    'https://help.shopee.vn/portal/4/article/120820-KB-',
    # --- seller.shopee.vn (seller) ---
    'https://seller.shopee.vn/edu/article/1234',
    'https://seller.shopee.vn/edu/article/1235',
    'https://seller.shopee.vn/edu/article/1236',
    # --- shopee.vn/legal (both) ---
    'https://shopee.vn/legal/terms',
    'https://shopee.vn/legal/privacy',
    'https://shopee.vn/legaldoc/policies'
)

$results = foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -Uri $u -Method Head -UseBasicParsing -TimeoutSec 10 -Headers @{'User-Agent'='Day7DataFoundationsCourse/1.0'} -MaximumRedirection 5
        [PSCustomObject]@{
            URL     = $u
            Status  = $r.StatusCode
            FinalURL = $r.BaseResponse.ResponseUri.AbsoluteUri
            Type    = $r.Headers['Content-Type']
            Verdict = switch ($r.StatusCode) {
                200 { 'OK' }
                301 { 'REDIRECT' } 302 { 'REDIRECT' }
                403 { 'BLOCKED' }
                404 { 'DEAD' }
                default { 'CHECK' }
            }
        }
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        [PSCustomObject]@{
            URL=$u; Status=$code; FinalURL=''; Type=''
            Verdict = switch ($code) {
                404 { 'DEAD' } 403 { 'BLOCKED' } 0 { 'TIMEOUT' } default { 'CHECK' }
            }
        }
    }
}

$results | Format-Table -AutoSize -Wrap
Write-Host "`nTOM TAT:" -ForegroundColor Cyan
$results | Group-Object Verdict | ForEach-Object { Write-Host ("  {0,-10} : {1}" -f $_.Name, $_.Count) }
```

**Cách dùng**: bảo người dùng mở PowerShell ở root repo, chạy:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_shopee_urls.ps1 > scripts\check_shopee_urls.txt
```

Sau đó **đọc file `scripts/check_shopee_urls.txt`**, lọc ra URL có `Verdict = OK`, đưa vào `data/urls.csv`.

### 2.2 Bước 2: Kiểm `robots.txt`

Thêm vào cùng file script phần đọc `robots.txt`:

```powershell
Write-Host "`n=== ROBOTS.TXT ===" -ForegroundColor Cyan
$sites = @('help.shopee.vn','seller.shopee.vn','shopee.vn')
foreach ($s in $sites) {
    Write-Host "`n--- https://$s/robots.txt ---" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest -Uri "https://$s/robots.txt" -UseBasicParsing -TimeoutSec 10 -Headers @{'User-Agent'='Day7DataFoundationsCourse/1.0'}
        Write-Host $r.Content
    } catch {
        Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

**Quy tắc xử lý kết quả robots.txt**:

- Nếu site cấm User-Agent `Day7DataFoundationsCourse/1.0` (hoặc `*`) đường dẫn ta cần → **bỏ URL đó**, đừng ép.
- Nếu site không có `robots.txt` hoặc không cấm rõ ràng → mặc định cho phép, ghi nhận trong `sources.csv` cột `license_or_permission = "public-source-per-robots"`.
- **Ghi chú vào REPORT_NHOM**: trích nguyên đoạn `User-Agent: *` → `Allow: /portal/4/article/...` (hoặc tương tự) để chứng minh quyền crawl.

### 2.3 Bước 3: Tạo `data/urls.csv` (chỉ chứa URL OK)

Sau khi đọc output PowerShell, tạo file `data/urls.csv` với **chỉ những URL `Verdict = OK`** (tối đa 10 URL, tối thiểu 5). Schema:

```csv
url,doc_id,title,audience,category,language,document_version,license_or_permission
https://help.shopee.vn/portal/4/article/<ID>,doi-tra-thoi-han,"Thời hạn đổi trả",buyer,returns-policy,vi,not-stated,public-source
https://seller.shopee.vn/edu/article/<ID>,seller-xu-ly-doi-tra,"Xử lý đổi trả cho seller",seller,returns-policy,vi,not-stated,public-source
...
```

**Nguyên tắc chọn URL**:

| Audience | Ít nhất | Mục đích |
| --- | --- | --- |
| `buyer` | 2–3 URL | Thời hạn đổi trả, điều kiện, hoàn tiền |
| `seller` | 2–3 URL | SLA xử lý đổi trả, mức phạt, nghĩa vụ |
| `both` | 1–2 URL | Điều khoản chung từ `shopee.vn/legal` |

**Đặt tên `doc_id`**:

- Lowercase, không dấu, nối bằng `-`.
- Ví dụ: `doi-tra-thoi-han-buyer`, `seller-sla-doi-tra`, `shopee-dieu-khoan-chung`.
- `doc_id` phải **duy nhất** trong cả corpus và **khớp tên file** (không có phần mở rộng).

### 2.4 Bước 4: Crawl bằng script có sẵn

```bash
python scripts/fetch_public_pages.py data/urls.csv --output-dir data/shopee-policies
```

Script tự:

- Kiểm `robots.txt` cho từng host.
- Đợi ≥1 giây giữa các request.
- Parse HTML/text → `.md`.
- Sinh `sources.csv` cùng thư mục.

### 2.5 Bước 5: Xử lý lỗi đã biết (4 thứ gần như chắc chắn xảy ra)

1. **Robot cấm** → script báo `disallowed by robots.txt`, bỏ qua. Không phải lỗi cần vượt. Bỏ URL đó khỏi CSV.
2. **Trang render bằng JS** → body rỗng, script báo `extracted content is too short`. Đổi URL khác.
3. **Crash `LookupError: unknown encoding`** (charset lỗi kiểu `utf-8,gbk`) → 1 URL hỏng làm sập cả lượt. **Bỏ URL đó khỏi CSV trước**, chạy tiếp, xử lý riêng sau.
4. **Output thô rất bẩn** (16 KB thay vì 3 KB nội dung thật) → **làm sạch thủ công** sau khi crawl. Giữ đúng điều khoản, con số, mốc thời gian. Bỏ menu, banner, footer, danh sách sản phẩm. Đọc lại từng file.

### 2.6 Bước 6: Chuẩn hoá frontmatter mỗi file `.md`

Mỗi file phải có YAML frontmatter đúng schema L3B:

```md
---
doc_id: doi-tra-thoi-han-buyer
title: Thời hạn đổi trả cho người mua
source_url: https://help.shopee.vn/portal/4/article/<ID>-KB-<slug>
retrieved_at: 2026-09-20
document_version: "not-stated"
audience: buyer
category: returns-policy
language: vi
---

# Thời hạn đổi trả cho người mua

Nội dung đã làm sạch...
```

**Lưu ý**:

- `document_version`: chỉ ghi khi nguồn nêu rõ. Không có thì `not-stated` — **không bịa**.
- Nếu một trang gộp cả buyer lẫn seller → **tách thành 2 file**, mỗi file 1 `audience`.
- `sources.csv` phải khớp 1-1 với danh sách file.

### 2.7 Bước 7: Validate (CP2)

Chạy script validate từ lab doc:

```bash
python -c "
import csv, re
from pathlib import Path
D = Path('data/shopee-policies')
REQ = ['doc_id','title','source_url','retrieved_at','document_version','audience']
mds = sorted(D.glob('*.md'))
rows = list(csv.DictReader(open(D/'sources.csv', encoding='utf-8')))
ids, auds = [], {}
for p in mds:
    fm_text = p.read_text(encoding='utf-8').split('---')[1]
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', fm_text, re.M))
    ids.append(fm.get('doc_id'))
    auds[fm.get('audience')] = auds.get(fm.get('audience'), 0) + 1
    print(f'{p.name:40} {\"OK\" if all(k in fm for k in REQ) and fm.get(\"doc_id\")==p.stem else \"THIEU METADATA\"}')
print('so file :', len(mds), '(can 5-10)')
print('csv     :', 'khop' if sorted(r['doc_id'] for r in rows)==sorted(ids) else 'LECH')
print('audience:', auds)
"
```

**Output kỳ vọng**:

- Số file `5 ≤ n ≤ 10`.
- Mọi file `OK`.
- `csv khop`.
- `audience: {'buyer': ≥2, 'seller': ≥2, 'both': ≥1}` (ít nhất 2 giá trị khác nhau).

### 2.8 Checklist output phase 1

- [ ] `data/shopee-policies/` có 5–10 file `.md`
- [ ] Mỗi file có đủ 6 trường metadata bắt buộc
- [ ] `data/shopee-policies/sources.csv` khớp 1-1
- [ ] `audience` có ≥ 2 giá trị khác nhau
- [ ] `data/shopee-policies/` được commit (không có `.env`/API key)

---

## 3. Phase 2 — Code cá nhân `src/` (1:00–2:30)

### 3.1 Warm-up (10 phút) — điền vào REPORT_CANHAN mục 1

**Cosine similarity** (2.5 điểm):

- Giải thích similarity cao nghĩa là gì: vector cùng hướng → văn bản cùng chủ đề/ngữ nghĩa.
- Cho 1 cặp cao: chọn 2 câu **khác từ vựng nhưng cùng nghĩa** (ví dụ: "Hoàn tiền trong 7 ngày" vs "Được trả lại tiền trong vòng một tuần").
- Cho 1 cặp thấp: 2 câu cùng từ khoá nhưng khác nghĩa (ví dụ: "Shop bảo hành điện thoại" vs "Bảo hành sân bay cho khách VIP").
- Vì sao cosine hợp text embedding hơn Euclid: embedding có độ dài khác nhau tuỳ tài liệu dài ngắn, cosine bỏ qua magnitude, chỉ xét góc → ổn định hơn.

**Bài toán chunking** (2.5 điểm):

- Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50` → `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23` chunks.
- Overlap tăng từ 50 → 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25` chunks (tăng 2).
- Vì sao đôi khi muốn overlap lớn: giữ liên kết giữa 2 chunk liền kề, tránh cắt đứt câu/ý giữa chừng.
- Verify bằng:
  ```bash
  python -c "from src.chunking import FixedSizeChunker; print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)))"
  ```

### 3.2 `SentenceChunker.chunk` (CP3)

Tách câu theo ranh giới `. `, `! `, `? `, `.\n`. Gom `max_sentences_per_chunk` câu thành 1 chunk, strip khoảng trắng. Text rỗng → `[]`.

**Cái bẫy**: regex `[.!?]\s+` **nuốt mất dấu câu** → mọi chunk thành câu cụt.

Cách đúng: dùng `re.split` với **lookbehind** để giữ lại dấu:

```python
# Ví dụ: tách ở vị trí SAU dấu câu, giữ dấu
import re
sentences = re.split(r'(?<=[.!?])\s+', text)
```

Còn lại gom `max_sentences_per_chunk` câu → chunk.

### 3.3 `RecursiveChunker.chunk` và `_split`

Thuật toán 2 chiều:

1. **Đệ quy xuống sâu**: mảnh nào > `chunk_size` → gọi lại `_split` với separator nhỏ hơn.
2. **Gom lên**: nối mảnh nhỏ liền kề cho tới sát `chunk_size`. **Không có bước này → hàng trăm chunk vụn 5–10 ký tự.**

Base case 3 trường hợp:

1. Đoạn ≤ `chunk_size` → giữ nguyên.
2. `separators` rỗng → cắt cứng `chunk_size` ký tự.
3. Đệ quy tiếp với separator kế tiếp.

### 3.4 `compute_similarity`

Dùng `_dot` có sẵn. Chặn `ZeroDivisionError`: vector độ dài 0 → trả `0.0`.

### 3.5 `ChunkingStrategyComparator.compare`

Trả dict đúng 3 key `fixed_size`, `by_sentences`, `recursive`. Mỗi key là dict có `count`, `avg_length`, `chunks`. Chặn chia 0 khi text rỗng.

### 3.6 `EmbeddingStore` (5 method, 14 test)

**Bỏ nhánh Chroma**: set `self._use_chroma = False` ngay từ đầu. Không test nào cần nó, và bug khởi tạo sẵn có thể phá 14 test.

Hai helper làm trước, 4 method công khai làm sau:

**`_make_record(doc)`**:
- Copy metadata (đừng dùng trực tiếp object gọi).
- Bảo đảm `metadata['doc_id']` luôn tồn tại (trỏ về file gốc, không phải chunk id).

**`_search_records(query, records, top_k)`**:
- Chạy similarity trên tập record bất kỳ.
- Cả `search` và `search_with_filter` đều gọi qua đây.
- Bỏ `embedding` khỏi output (vector 1536 chiều làm bẩn terminal).

**`search_with_filter`**: lọc **trước** rồi mới search. Lọc sau → có thể còn 0 kết quả dù store còn tài liệu hợp lệ.

**`delete_document`**: xoá mọi chunk có `metadata['doc_id']` khớp, trả `True/False` tuỳ có xoá được gì không.

### 3.7 `KnowledgeBaseAgent.answer`

Ba nhịp: retrieve top-k → dựng prompt có ngữ cảnh → gọi `llm_fn`.

**Quan trọng nhất**: đánh số từng chunk `[1] [2] [3]` kèm nguồn, yêu cầu model trích dẫn số khi trả lời. Đây là tiêu chí *Source Traceability* trong `docs/EVALUATION.md`.

Thêm ràng buộc chống bịa: chỉ dùng ngữ cảnh được cung cấp, không có thì nói rõ. Store rỗng → trả thông báo, đừng crash và đừng gọi LLM vô ích.

### 3.8 CP4 (mốc quan trọng nhất)

```bash
pytest tests/ -v
python main.py "Chunking là gì?"
```

Kỳ vọng: **42 passed**, `main.py` chạy đầu đến cuối. Dòng `Skipping missing file: data/customer_support_playbook.txt` là bình thường.

Chụp output pytest dán vào **REPORT_CANHAN mục 3** (30 điểm).

### 3.9 Checklist output phase 2

- [ ] `pytest tests/ -v` → **42 passed**
- [ ] `python main.py "<câu hỏi>"` chạy thành công, có dòng `Embedding backend: ...`
- [ ] Warm-up câu 1 + câu 2 đã viết trong REPORT_CANHAN mục 1

---

## 4. Phase 3 — Chiến lược riêng & benchmark (2:30–3:00)

### 4.1 5 benchmark query

Đúng 5 câu, đa dạng dạng hỏi:

1. **Tra số liệu**: thời hạn đổi trả là bao nhiêu ngày?
2. **Hỏi điều kiện**: điều kiện để được đổi trả là gì?
3. **Hỏi quy trình**: quy trình hoàn tiền diễn ra thế nào?
4. **Liệt kê**: có những trường hợp nào không được đổi trả?
5. **Câu CẦN filter**: thời hạn xử lý đổi trả cho **người bán** là bao lâu? *(cần `metadata_filter={"audience":"seller"}`)*

Mỗi câu có gold answer **trích nguyên văn từ tài liệu**, không suy đoán.

**Câu số 5 mẫu (nếu corpus có đủ)**:

- Query: "Trong vòng bao lâu kể từ khi nhận yêu cầu, người bán phải phản hồi yêu cầu đổi trả?"
- Gold: "Người bán có trách nhiệm phản hồi trong vòng X ngày..."
- Nếu KHÔNG filter `audience=seller`, top-3 có thể lẫn tài liệu "buyer" nói về thời hạn 7 ngày → agent trả sai đối tượng.

### 4.2 Chunker theo heading (vai R3, bắt buộc)

Tách trước mỗi dòng `^## ` hoặc `^# `. Mỗi section thành 1 chunk. Section nào dài quá `chunk_size` → hạ xuống recursive.

**Chi tiết dễ bỏ sót**: khi cắt nhỏ 1 section dài, **gắn lại tiêu đề vào từng mảnh con**. Không có → mảnh thứ 2+ mất ngữ cảnh "đây là mục nói về cái gì".

Đặt tên class: `HeadingAwareChunker` trong file mới `src/heading_chunker.py`, import vào `bench.py`.

### 4.3 `bench.py` (công cụ đo, không chấm bằng test)

Schema:

```python
# 1. Đọc từng file .md, tách frontmatter thành metadata, phần thân thành content
# 2. Chunk phần thân, mỗi chunk thành một Document:
#       Document(id=f"{path.stem}#{i}", content=chunk,
#                metadata={**frontmatter, "doc_id": path.stem, "chunk_index": i})
# 3. Nạp vào EmbeddingStore, chạy 5 query qua search_with_filter()
# 4. In top-3 kèm score và doc_id để đối chiếu với gold answer
```

**4 chỗ dễ sai**:

1. Chunking xảy ra **ngoài** store. Nạp cả file làm 1 `Document` như `main.py` thì retrieval trả cả file, vô dụng.
2. `doc_id` trong metadata trỏ về **tên file gốc** (`path.stem`), còn `Document.id` mới là `"file#0"`.
3. Frontmatter phải được **trải vào mọi chunk**, nếu không `search_with_filter` không có gì để lọc.
4. Mỗi người chỉ đổi **1 dòng** — dòng chọn chunker — sang chiến lược riêng.

**Cache embedding** (nếu dùng OpenAI/Gemini):

```python
import hashlib
_cache = {}
def cached_embed(text):
    h = hashlib.md5(text.encode()).hexdigest()
    if h not in _cache:
        _cache[h] = embedder(text)
    return _cache[h]
```

### 4.4 Baseline (R3 chủ trì)

Chạy `ChunkingStrategyComparator().compare()` trên 2–3 tài liệu Shopee, ghi vào **REPORT_NHOM mục 2**. Nhớ **bỏ frontmatter** trước khi so sánh, nếu không đo cả khối YAML.

### 4.5 CP5

- `python bench.py` chạy được, in số chunk đã nạp + top-3 cho 5 câu.
- Nhóm có 5 query + gold answer trong REPORT_NHOM mục 3.
- Mỗi người đã đổi sang chiến lược riêng.

---

## 5. Phase 4 — Chạy, so sánh, phân tích lỗi (3:00–3:25)

### 5.1 Chọn embedding backend TRƯỚC khi đo

`MockEmbedder` băm MD5 → không có ngữ nghĩa → số liệu nhiễu.

**Khuyến nghị**: bật OpenAI hoặc Gemini (đã cài sẵn key trong `.env`). Nếu không có key, dùng local multilingual (yêu cầu cài thêm ~2 GB model).

Nếu **buộc phải dùng mock** → ghi rõ trong báo cáo, chuyển trọng tâm phân tích sang `count` / `avg_length` / độ mạch lạc.

### 5.2 Chấm 2 mức (không chỉ 1)

**Cách ngây thơ** (chỉ check `doc_id` của gold có trong top-3): thổi phồng.

**Cách đúng** (theo `docs/SCORING.md`):

- 2đ: top-3 có chunk liên quan **VÀ** agent trả lời đúng
- 1đ: top-3 có chunk liên quan nhưng agent thiếu/sai
- 0đ: không retrieve được

Kiểm tra ở **mức nội dung**: khai báo chuỗi đặc trưng phải xuất hiện trong context retrieved, kiểm chuỗi đó có thật không.

### 5.3 A/B bắt buộc

Chạy câu cần filter **2 lần** — 1 có `metadata_filter`, 1 không — trên cả 3 chiến lược. Ghi lại top-3 mỗi lần. Đây là bằng chứng cho câu "metadata filter có giúp ích không" trong REPORT_NHOM mục 3.

Nếu 2 lần giống hệt → câu hỏi **chưa thực sự cần filter** → sửa câu hỏi hoặc sửa cách tách tài liệu.

### 5.4 Phân tích lỗi

Tìm ít nhất 1 failure case thật, viết 3 phần: câu hỏi nào hỏng, vì sao, đề xuất sửa.

Các hướng thường gặp:

- Chunk đúng chủ đề nhưng không chứa số liệu → thắng chunk có đáp án (cosine đo độ giống chủ đề, không đo mật độ thông tin).
- Top-3 đúng tài liệu nhưng sai section (chunk không overlap → mỗi thông tin 1 cơ hội).
- Filter `audience` cứng loại nhầm tài liệu chứa thông tin cần (đánh đổi precision/recall).

### 5.5 CP6

- Mỗi người có `ket_qua_benchmark.txt` riêng.
- Điền bảng top-3 vào REPORT_CANHAN mục 5.
- Nhóm có bảng so sánh giữa các thành viên + ≥1 failure case trong REPORT_NHOM mục 2 và 4.

---

## 6. Phase 5 — Demo & nộp bài (3:25–4:00)

### 6.1 Demo 6–8 phút

Mọi thành viên đều phải nói phần chiến lược của mình. Thứ tự gợi ý:

1. Chủ đề + bộ tài liệu (1')
2. Mỗi người tóm tắt chiến lược (2')
3. So sánh, giải thích thắng-thua (3')
4. Demo trực tiếp 1–2 câu (2')
5. Hỏi đáp

Mở sẵn terminal với `bench.py` đã chạy. Demo live phải debug tại chỗ = mất điểm.

### 6.2 Nộp bài

```bash
pytest tests/ -v          # phải 42 passed
git status                # không thấy .venv/ hay .env
git add .
git commit -m "Nộp bài Lab 07"
git branch -M main
git remote add origin https://github.com/<tài-khoản>/K4-DAY07-<HoVaTen>-<MSSV>.git
git push -u origin main
```

Tên repo: `K4-DAY07-HoVaTen-MSSV` (họ tên viết liền không dấu). Nếu đã fork repo gốc thì đổi tên fork trong Settings.

### 6.3 Cấu trúc khi nộp

```
K4-DAY07-<HoVaTen>-<MSSV>/
├── src/                      # đã hoàn thiện mọi TODO
├── data/shopee-policies/     # 5-10 tài liệu + sources.csv
├── report/
│   ├── REPORT_CANHAN.md      # bản cá nhân
│   └── REPORT_NHOM.md        # bản nhóm
├── bench.py
├── ket_qua_benchmark.txt
└── tests/, main.py, ...
```

### 6.4 CP7 — final checklist

- [ ] `pytest tests/ -v` → 42 passed, không còn `NotImplementedError`
- [ ] `data/shopee-policies/` có 5–10 tài liệu đủ metadata, `sources.csv` khớp 1-1
- [ ] ≥1 query dùng `metadata_filter={"audience":"buyer"}` (hoặc `"seller"`)
- [ ] ≥1 thành viên chunk theo heading/section (`HeadingAwareChunker`)
- [ ] Hai báo cáo điền đủ, output pytest là thật
- [ ] `bench.py` + `ket_qua_benchmark.txt` đã commit
- [ ] Repo đúng tên quy ước, không chứa `.venv`/`.env`, đã nộp link vào vlearn

---

## 7. Phụ lục — lỗi thường gặp & cách sửa

| Triệu chứng | Nguyên nhân | Cách sửa |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'src'` | Chạy python từ thư mục khác | `cd` về root repo |
| Test store fail dù code trông đúng | `_use_chroma = True` nhưng nhánh Chroma chưa cài | Set `False`, chỉ in-memory |
| `test_no_filter_returns_all_candidates` fail | `search` và `search_with_filter` dùng 2 đường code khác | Cho cả hai gọi chung `_search_records` |
| `delete_document` luôn trả `False` | Record không có `metadata['doc_id']` | Set `doc_id` trong `_make_record` |
| `test_empty_separators_falls_back_gracefully` fail | Thiếu base case `separators=[]` | Thêm nhánh cắt cứng theo `chunk_size` |
| `ZeroDivisionError` trong `compare` | Chia cho `count==0` khi text rỗng | Chặn trước khi chia |
| Chunk vụn 5–10 ký tự | `RecursiveChunker` thiếu bước gom | Nối mảnh nhỏ liền kề tới sát `chunk_size` |
| `KeyError` khi đọc comparator | Tên key gõ sai | So từng ký tự với docstring |
| Crawler báo `disallowed by robots.txt` | Nguồn không cho tự động | Đổi nguồn |
| Crawler crash `LookupError: unknown encoding` | charset không hợp lệ | Bỏ URL đó khỏi CSV, xử riêng |
| `search_with_filter` luôn rỗng | Metadata không trải vào chunk | Gộp frontmatter vào metadata |
| Filter không đổi kết quả | Corpus 1 audience, hoặc 2 đáp án chung file | Tách file theo audience |
| Score âm cho chunk đúng | Đang dùng `MockEmbedder` | Bật embedder thật (Phụ lục B của lab doc) |

---

## 8. Phụ lục riêng cho lab này — lỗi đặc thù Shopee

| Triệu chứng | Nguyên nhân | Cách sửa |
| --- | --- | --- |
| Mọi URL Shopee trả 404 | ID trong URL chỉ là minh hoạ, ID thật khác | HEAD-check lại bằng `scripts/check_shopee_urls.ps1` trước khi đưa vào CSV |
| `help.shopee.vn` trả 200 nhưng body gần như rỗng | Trang render bằng JS, fetch không đợi | Đổi URL khác, đừng ép |
| `seller.shopee.vn` trả 403 dù HEAD OK | Server phân biệt HEAD/GET | Bỏ URL đó, dùng nguồn khác (vd. blog Shopee Seller) |
| `shopee.vn/legal/*` có quá nhiều quảng cáo | Trang marketing lẫn legal | Lọc thủ công khi làm sạch, chỉ giữ phần điều khoản |
| Hai tài liệu cùng nói "đổi trả 7 ngày" nhưng 1 cho buyer, 1 cho seller | Một số trang gộp audience | Tách thành 2 file khi làm sạch |
| `sources.csv` Audience không khớp `REPORT_NHOM` | Ghi audience sai khi điền CSV | Đối chiếu lại từng file `.md` |

---

## 9. Báo cáo — skeleton điền

### 9.1 REPORT_NHOM.md (40 điểm)

```md
# Báo cáo Nhóm — Lab 07 K4-L3B

## 1. Data Inventory & Metadata Schema
- Sàn: Shopee
- Tổng tài liệu: X file
- Phân bố audience: {buyer: a, seller: b, both: c}
- Schema metadata: doc_id, title, source_url, retrieved_at, document_version, audience, category, language

## 2. Baseline Analysis (ChunkingStrategyComparator)
| Strategy     | Count | Avg length |
| ------------ | ----- | ---------- |
| fixed_size   |       |            |
| by_sentences |       |            |
| recursive    |       |            |

## 3. Benchmark Queries + Gold Answers
| # | Query | Gold answer (trích từ file) | Filter? |
| - | ----- | --------------------------- | ------- |
| 1 |       |                             |         |
| 2 |       |                             |         |
| 3 |       |                             |         |
| 4 |       |                             |         |
| 5 |       |                             | seller  |

## 4. So sánh chiến lược & failure case
- Bảng top-3 cho từng thành viên (theo query).
- Failure case: query nào, vì sao, đề xuất sửa.

## 5. Demo script
- Mở terminal, chạy `python bench.py`, show output.
```

### 9.2 REPORT_CANHAN.md (60 điểm)

```md
# Báo cáo Cá nhân — Lab 07 K4-L3B

## 1. Warm-up (5 điểm)
- Cosine similarity: giải thích + 1 cặp cao + 1 cặp thấp + vì sao cosine.
- Bài toán chunking: công thức + áp dụng 10.000 ký tự + verify bằng code.

## 2. Hướng tiếp cận (10 điểm)
- SentenceChunker: thuật toán + edge case (chữ viết tắt, số thập phân) + cách xử lý.
- RecursiveChunker: thuật toán 2 chiều + base case.
- compute_similarity: chặn ZeroDivisionError.
- ChunkingStrategyComparator: dict key + chặn chia 0.
- EmbeddingStore: 5 method + quyết định bỏ Chroma + lý do `_make_record` copy metadata + `_search_records` chung + filter trước khi search.
- KnowledgeBaseAgent: prompt có đánh số + chống bịa + xử lý store rỗng.

## 3. Kết quả pytest (30 điểm)
- Paste output `pytest tests/ -v` (42 passed).

## 4. Dự đoán similarity (5 điểm)
- 5 cặp câu, dự đoán, chạy code so sánh, phản ngẫm.

## 5. Kết quả benchmark (10 điểm)
- Bảng top-3 cho 5 query trên chiến lược riêng.
- Ghi rõ dùng embedder nào (mock / local / openai / gemini).
- Nếu dùng mock → ghi rõ số liệu bị chi phối bởi mock, chuyển trọng tâm sang count/avg_length.
```

---

## 10. Câu hỏi người dùng hay hỏi sau khi đọc xong mega prompt

**Q: Tôi có cần fork repo trước khi clone không?**
A: Có. `git clone` thẳng repo gốc sẽ không có quyền push. Fork về tài khoản mình trước.

**Q: MockEmbedder có đủ cho bài không?**
A: Đủ để pass 42 test (30 điểm code). Nhưng benchmark sẽ nhiễu — ghi rõ trong báo cáo.

**Q: Tôi không có OpenAI key, dùng Gemini được không?**
A: Được. Lấy key free tại aistudio.google.com/apikey, thêm vào `.env`:
```
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=...
```

**Q: Sàn khác (Lazada/Tiki) có dùng được không?**
A: Đã quyết định dùng Shopee vì có sẵn data buyer + seller riêng biệt. Đổi sàn = đổi cả corpus + benchmark query. Không khuyến khích đổi giữa chừng.

**Q: Tôi có thể crawl ít hơn 5 file không?**
A: Không. Rubric yêu cầu 5–10 file để chấm "Chất lượng Bộ Tài liệu" (10 điểm). 4 file = 0 điểm phần này.

---

## 11. Điều kiện dừng

Agent dừng & báo cáo lại khi:

1. Đã pass CP7 (final checklist).
2. Hoặc **chỉ chờ người dùng cung cấp**: output PowerShell `check_shopee_urls.ps1` (không có output này thì không thể biết URL nào OK để đưa vào CSV).

Mọi phase khác agent có thể tự chạy đến khi hết việc hoặc hết context window.


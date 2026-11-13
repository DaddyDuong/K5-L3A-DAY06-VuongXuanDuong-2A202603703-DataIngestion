# Báo cáo cá nhân — Day 06: Data Ingestion Engineering

- Họ tên: **Vương Xuân Dương**; MSSV: **2A202603703**; lớp: **L3A**.
- Chủ đề: truy xuất kiến thức Python Files và Data Science từ OpenStax.
- Repository đã cấu hình: https://github.com/DaddyDuong/K5-L3A-DAY06-VuongXuanDuong-2A202603703-DataIngestion
- Bản báo cáo này mô tả các lần chạy thực tế ngày **13/11/2026**, giờ Việt Nam.
- **Công cụ AI:** Codex hỗ trợ chọn phạm vi, viết code, xây benchmark, chạy thí nghiệm,
  đọc trace và soạn nhãn định tính sơ bộ. Học viên đã đọc lại toàn bộ nhãn
  coherence/grounding/metadata, đối chiếu với nguồn và xác nhận. Không dùng kết quả test
  để sửa pipeline.

## 1. Dữ liệu và pipeline

Nguồn là *Introduction to Python Programming*, OpenStax / Rice University, bản PDF
397 trang, copyright 2026, năm xuất bản gốc 2024. Chọn chương 14 **Files** (PDF 319–340,
trang in 309–330) và chương 15 **Data Science** (PDF 341–370, trang in 331–360).
Giữ 52 trang để bảo toàn ngữ cảnh. Đếm bảo thủ **42 trang nội dung**: loại khỏi số đếm
hai trang mở chương 319/341, bảy trang có phần tổng kết 338–340/367–370 và trang tiếp
nối bảng ít chữ 358. Không lấy bìa, mục lục, answer key, index để đạt số lượng.
Toàn bộ text sau chuẩn hóa có **92.316 ký tự**.

Giấy phép **CC BY-NC-SA 4.0** được đọc tại trang PDF 4; giữ ghi công và điều kiện phi
thương mại/chia sẻ cùng giấy phép cho nội dung dẫn xuất, lưu ý ngoại lệ của nội dung
bên thứ ba. PDF gốc được giữ nguyên. Footer ghi công trong text chuyển thành trường
`attribution` trên mỗi trang/chunk. Nguồn, thời điểm truy cập, danh sách trang và SHA-256
snapshot có trong [manifest](../../data/manifest.json), quy tắc chi tiết trong
[data/README.md](../../data/README.md).

Dùng Poppler `pdftotext -layout` để trích text theo trang; chuẩn hóa Unicode NFC,
bỏ soft hyphen, bỏ khoảng trắng cuối dòng và gộp dòng trống dư; giữ thụt dòng Python
và ranh giới đoạn. 52/52 trang có text; không cần OCR. Bảng nhiều cột vẫn bị trải theo
layout và code có thể ngắt dòng theo PDF. Header số trang còn giữ lại, gây chunk chỉ
có header ở cấu hình B/C; đây là lỗi đã quan sát, chưa sửa sau test.

Luồng chạy: `pages.jsonl` → `DocumentPage` → chunk theo A/B/C → embedding document →
PostgreSQL/pgvector → embedding câu hỏi → exact cosine search top-3 → lưu trace →
chấm evidence. Không gọi LLM sinh câu trả lời. Hàm đọc PDF tổng quát cũng được triển
khai nhưng thí nghiệm dùng snapshot JSONL đã chốt để không thay đổi gold/offset.

**Embedding:** `intfloat/multilingual-e5-small`, revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3`, 384 chiều, CPU, batch 16, 4 thread.
Document có prefix `passage: `, query có `query: `, vector chuẩn hóa L2. Giới hạn 512
token; báo lỗi nếu vượt thay vì cắt âm thầm. Cả ba cấu hình dùng cùng model/revision.
Không dùng vector ngẫu nhiên, TF-IDF hay mock thay cho model.

**Store:** PostgreSQL 16.16, pgvector 0.8.7, Docker Compose,
`127.0.0.1:55433`, database `day6_lab`, schema `day6_ingestion`, table `chunks`.
Dùng toán tử cosine `<=>`, exact search, không ANN index. JSONB filter áp dụng trước
top-k và có kiểm tra kiểu dữ liệu; giá trị được truyền bằng SQL parameters.
Dữ liệu lưu ở Docker named volume `day6_student_starter_pg_data`.

Metadata gồm `document_id`, `source`, `page` (trang vật lý PDF bắt đầu từ 1),
`printed_page`, `chapter` (số nguyên 14/15), `chapter_title`, `language=en`, offset
`start_char/end_char`, page ID và attribution. Chương được lấy từ heading/mục lục,
không suy đoán. `source` + `page` + offset giúp đối chiếu trực tiếp bằng chứng.

ID chunk ổn định theo tài liệu/trang/cấu hình/offset/text. Mỗi lần nạp thay toàn bộ
snapshot của một strategy trong transaction: xóa chunk lỗi thời cả khi tài liệu bị
loại bỏ, giữ nguyên strategy khác. Đã nạp hai lần và mở kết nối mới: số lượng vẫn là
**222/252/252**. Test tích hợp kiểm tra thay snapshot nhỏ hơn xóa được chunk cũ.

## 2. Ba cấu hình, benchmark và chọn chiến lược

| Cấu hình | Chunking | Metadata filter |
|---|---|---|
| A | 500 ký tự, overlap 50, không vượt trang | Không |
| B | Ưu tiên đoạn, tối đa 500 ký tự; đoạn dài chia theo dòng/từ, không overlap | Không |
| C | Chunk giống hệt B, đã kiểm tra byte/ID | `chapter` khi input câu hỏi có yêu cầu |

A–B thay chiến lược chunking, bao gồm cả ranh giới và overlap; không thể quy toàn
bộ chênh lệch cho riêng ranh giới đoạn. B–C chỉ đổi filter, là cặp so sánh kiểm soát
một yếu tố. Không thay corpus, query, model, store hoặc định nghĩa metric.

[Bộ benchmark](../../benchmark/questions.md) có 20 câu tiếng Việt, gold/evidence tiếng
Anh: q01–q15 dev, q16–q20 test; chốt trước retrieval. Có 3 câu filter: q06 chương 14,
q10 và q19 chương 15; q19 thuộc test. Filter là phạm vi được nêu trong câu hỏi, không
lấy source/trang/đáp án từ gold đưa vào truy xuất. Query embedding chỉ dùng `question`.
Có 10 alternative gold được ghi trước thử nghiệm. Đã kiểm tra 30 trích đoạn chính/
thay thế nằm trong text chuẩn hóa và text layer PDF. Rủi ro xuyên ngôn ngữ là một
phần của thiết kế; không thay ngôn ngữ giữa các cấu hình.

Test tập trung raise/constructor, missing data và visualization. Dev/test không
trùng trang gold chính nhưng cùng sách; EDA có mặt ở cả hai tập, phần tổng kết lặp
nội dung, một số câu trong sách tương tự benchmark. Hai câu test chung chủ đề và
hai câu chung trang: không coi 5 câu là 5 chủ đề độc lập.

Quy tắc đã chốt: ưu tiên **dev Evidence Hit@3**, sau đó dev Hit@1, sau đó ingest time
thấp hơn; nếu vẫn hòa thì A/B/C theo thứ tự. Run dev cuối chọn **C** lúc 17:34:08
ngày 13/11/2026 (UTC+7). B/C cùng retrieval; C ingest 6,330 giây so với B 6,465 giây.
Chênh lệch này nhỏ và nhiễu; không dùng nó để kết luận C có retrieval tốt hơn B.
Run dev đầu đã chọn B do thời gian khác; run cuối chỉ sửa định dạng CSV/đường dẫn,
không đổi model/chunking/corpus/benchmark. Giữ lịch sử cả hai run.

Test bắt đầu sau khi chốt C. Fingerprint code/config/corpus/benchmark của test khớp
dev; giữ nguyên lựa chọn C sau khi thấy test. Không tinh chỉnh và không chạy lại test.

## 3. Kết quả truy xuất và tài nguyên

Hit tự động yêu cầu một chunk cùng document/page gold và chứa đủ evidence chính
hoặc alternative đã chốt; chuẩn hóa whitespace. Đúng trang nhưng thiếu evidence vẫn
là miss. Kết quả dưới đây giữ nguyên output tự động, chưa áp dụng overlay định tính.

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Ingest (giây) | Chi phí dịch vụ |
|---|---|---|---|---|---|---|
| A | dev | 6/15 | 7/15 | 222 | 6.928 | 0 USD |
| B | dev | 9/15 | 11/15 | 252 | 6.465 | 0 USD |
| C | dev | 9/15 | 11/15 | 252 | 6.330 | 0 USD |
| A | test | 2/5 | 2/5 | 222 | 7.503 | 0 USD |
| B | test | 2/5 | 3/5 | 252 | 6.693 | 0 USD |
| C | test | 2/5 | 3/5 | 252 | 6.854 | 0 USD |

| Strategy | Độ dài min / median / max (ký tự) | Tổng ký tự chunk | Token document có prefix |
|---|---|---|---|
| A | 91 / 500 / 500 | 100816 | 21772 |
| B | 20 / 414 / 500 | 92316 | 20038 |
| C | 20 / 414 / 500 | 92316 | 20038 |

Thời gian ingest gồm chunking, document embedding và lần ghi đầu; không gồm model
load, query embedding hoặc nạp lại để kiểm tra. Model load của run test 8,341 giây,
query embedding cho 5 câu 0,145 giây. Token document tối đa 184 cho A, 180 cho B/C,
không vượt giới hạn. Ba cấu hình embed độc lập cả khi B/C cùng text.
Chi phí dịch vụ trả phí là 0 USD vì inference local; không bao gồm điện, phần cứng,
mạng và công sức. Số liệu thời gian chịu warm-up, thứ tự A/B/C, tải máy và cache.

### Đối chiếu evidence tương đương, giữ riêng kết quả tự động

Đọc cả 15 trường hợp test (5 câu × 3 cấu hình), phát hiện **A/q19/rank 2**, PDF 357,
chunk `1ee41a788790fb44fa2639ebd0d6ba24`, có ví dụ `df.fillna(df.mean())` kèm giải thích
thay Null bằng trung bình cột. Đây là bằng chứng tương đương đủ xác định hàm fillna(),
nhưng không chứa nguyên văn toàn bộ gold. Không dùng câu trắc nghiệm rank 1 làm đáp án.

| Strategy | Hit@1 test sau đối chiếu | Evidence Hit@3 test sau đối chiếu |
|---|---|---|
| A | 2/5 | 3/5 |
| B | 2/5 | 3/5 |
| C | 2/5 | 3/5 |

Chỉ có một override như trên; toàn bộ 15 trường hợp đều được đọc theo cùng tiêu chí.
Không sửa gold, không sửa raw trace, không dùng bảng đối chiếu để chọn lại chiến lược.
Đây là **overlay chấm thủ công sau test**, tách riêng khỏi metric tự động đã chốt. Chênh lệch strict Hit@3 giữa A và B/C biến mất trong mẫu
nhỏ này khi chấp nhận evidence tương đương. Dev chưa được audit ngữ nghĩa toàn bộ,
vì vậy không so trực tiếp dev strict với test overlay như cùng một phép đo.

## 4. Coherence, metadata và grounding

Nhãn dưới đây do Codex soạn sơ bộ kèm lý do, sau đó học viên đọc lại từng nhãn và
xác nhận. Quá trình chấm đã đọc text mẫu/trace, đối chiếu nguồn và xem ảnh PDF 324, 336,
337, 357, 361; script kiểm tra thêm text layer tại mọi trang xuất hiện trong test top-3.
Người chấm đã thấy metric nên không blind, và cũng là người xây pipeline/benchmark nên
có nguy cơ thiên lệch tự xác nhận. Chỉ có một người chấm, chưa đo inter-rater agreement.

Coherence dùng cùng 10 vị trí đã chốt trước retrieval: trang PDF 319–328, offset 0.
Chấm 0 = cắt ý/không hiểu độc lập, 1 = hiểu một phần/thiếu ngữ cảnh, 2 = giữ trọn ý
và tự hiểu. Vị trí đầu trang dễ chứa header, bảng hoặc phần tiếp nối nên mẫu có thiên
lệch và không đại diện toàn bộ 52 trang; không đổi mẫu sau khi thấy điểm.

Metadata được kiểm tra trên **15 bản ghi top-3 mỗi strategy**: document/source,
trang vật lý/trang in, chương, offset/text và ghi công. Mỗi bản ghi đều có nhãn/check
riêng trong CSV. Grounding dùng 5 câu test mỗi strategy: 0 không có bằng chứng,
1 liên quan nhưng thiếu điều kiện/ngữ cảnh, 2 đủ trả lời và truy nguồn. Không tự suy
điểm grounding từ cosine/Hit@3; A/q19 cho thấy hai phép đánh giá khác nhau.

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng | Top-3 tuân thủ phạm vi yêu cầu | Grounding số câu 0 / 1 / 2 | Grounding TB /2 |
|---|---|---|---|---|---|
| A | 0.90 (10) | 15/15 | 1/1 | 0 / 2 / 3 | 1.60 |
| B | 1.10 (10) | 15/15 | 1/1 | 0 / 2 / 3 | 1.60 |
| C | 1.10 (10) | 15/15 | 1/1 | 0 / 2 / 3 | 1.60 |

Filter compliance ở đây kiểm tra **phạm vi yêu cầu q19**, không đồng nghĩa backend
đã áp filter. A/B không áp filter nhưng tình cờ cả top-3 đều thuộc chương 15; chỉ C
thực sự áp `chapter=15`. Hai câu filter dev cũng chưa cho thấy lợi ích so với B.
Vì chỉ có 1 câu test cần filter, chưa có bằng chứng C cải thiện retrieval nhờ filter.

Metadata hữu ích: `source/page/offset` cho phép tìm đúng đoạn PDF; `chapter` giới hạn
không gian tìm kiếm theo input. Hạn chế: đúng chương/trang không đảm bảo có evidence
(q19 B/C có hai chunk chỉ là header). Cũng chưa kiểm tra được việc phân biệt nhiều
phiên bản/tài liệu bởi corpus chỉ dùng một sách. Không đồng nhất đủ trường với hữu ích.

Các mẫu coherence chỉ ra A cắt giữa từ/câu; B/C giữ ranh giới tốt hơn ở PDF 319/320
nhưng vẫn tách ví dụ code và bảng. PDF 324, B/C có chunk chỉ gồm header cột, nhận 0/2;
PDF 321 là ví dụ code đang tiếp nối, vẫn 1/2. Không phải cứ chunk theo đoạn là mạch lạc.

## 5. Phân tích lỗi, lựa chọn và đánh đổi

1. **q16, cả A/B/C, gold PDF 336:** top-3 quay về phần đã bắt FileNotFoundError ở
   PDF 333 và bảng try/except. Câu hỏi cần ngoại lệ *không được xử lý*, đủ cả thông
   báo lỗi và kết thúc; bằng chứng hiện tại chỉ liên quan nên grounding 1/2, Hit@3 miss.
   Đây là lỗi phân biệt điều kiện phủ định, không phải metadata sai.
2. **q19, B/C, gold PDF 357:** rank 1 là trắc nghiệm ở PDF 360 có cả đáp án đúng và
   distractor, không có nhãn đáp án. Rank 2/3 chỉ có header ở PDF 342/368. Đúng chương
   nhưng thiếu bằng chứng; grounding 1/2. Không chọn đáp án bằng kiến thức ngoài trace.
3. **q17:** A đúng ngay rank 1, B/C cần đến rank 2; cấu hình theo đoạn có top-1 là bài
   tập constructor khác trên cùng trang. Hit@3 không cho thấy sự suy giảm top-1 này.
4. **q20:** A tìm nhóm công cụ data science chung, thiếu Plotly; B/C giữ được đoạn
   liệt kê đủ ba thư viện ở PDF 361, đúng ngay rank 1. Đây là ví dụ lợi ích của ranh giới.
5. **A/q19:** strict matching bỏ sót bằng chứng tương đương. Cần báo lỗi metric cùng
   lỗi retrieval; không coi mọi strict miss là hệ thống hoàn toàn không có thông tin.

A→B: strict dev Hit@3 tăng 7/15 lên 11/15, test 2/5 lên 3/5; coherence mẫu tăng
0,90 lên 1,10. Sau đối chiếu evidence tương đương, test Hit@3 là 3/5 cho cả hai.
B có thêm 30 chunk nhưng tổng ký tự/token thấp hơn nhờ bỏ overlap; giảm số token
không có nghĩa ít row hơn. B vẫn có chunk ngắn vô ích và thiếu ngữ cảnh code/bảng.

B→C: chunk và toàn bộ top-3 test giống nhau, metric và nhãn cũng giống nhau. Filter
đã hoạt động đúng nhưng chưa đo được lợi ích trong tập câu hiện có. Chọn **C** theo
selection dev đã chốt; B là phương án tương đương trên corpus và benchmark này.
Không tuyên bố C tốt nhất tổng quát hoặc dùng test để đổi lựa chọn.

Nếu làm thí nghiệm mới: loại header trước chunking, xử lý riêng bảng/code và dùng
bộ câu hỏi nhiều tài liệu/phiên bản để stress filter; cân nhắc reranker/hybrid cho
phủ định. Những thay đổi đó **chưa được thực hiện** vì test đã mở; phải ghi thí nghiệm
mới và có tập test mới nếu muốn đánh giá độc lập.

## 6. Tái lập, artifacts và giới hạn bài nộp

Setup và lệnh chi tiết: [starter/README.md](../../starter/README.md), dependencies đầy
đủ trong [requirements-lock.txt](../../starter/requirements-lock.txt). Môi trường
Python 3.14.10, torch 2.15.0+cpu, sentence-transformers 5.7.0, transformers 5.22.2,
numpy 2.5.4, psycopg 3.3.8. Cấu hình/model revision và SHA-256 nằm trong run metadata.
Không dùng RNG trong chunking hoặc exact ranking; tie được sắp theo chunk ID.

```bash
cd starter
# Sau khi setup venv/database theo README:
.venv/bin/python scripts/check_setup.py
# Tái lập trong thư mục riêng vì tập test của bài nộp đã được mở:
.venv/bin/python -m src.run --split dev --output-root ../results/reproduction
.venv/bin/python -m src.run --split test --output-root ../results/reproduction
# Chỉ tổng hợp lại nhãn đã đọc/chấm, không chạy retrieval:
.venv/bin/python scripts/summarize_audit.py
```

Chạy lại cùng tập đã công bố là tái lập số liệu, không tạo holdout độc lập mới.
Đã chạy **11 unit/integration tests**, gồm source offset/độ phủ ký tự, Unicode,
alternative evidence, filter, ranking cosine, snapshot thay đổi, reconnect và batch
vector sai không làm mất dữ liệu. Vector cơ sở trong unit test chỉ kiểm tra store;
embedding của pipeline là model thật. Không có lỗi pipeline trong các run được báo;
HTTP 404 cho file cấu hình tùy chọn của model không làm inference thất bại. Có log
thực và `failure.json` nếu pipeline phát sinh lỗi, không fallback mock.

- Dev cuối: [summary](../../results/20261113T103339652250Z-dev/summary.md), [trace](../../results/20261113T103339652250Z-dev/traces.jsonl).
- Test duy nhất: [summary](../../results/20261113T103637017303Z-test/summary.md), [trace](../../results/20261113T103637017303Z-test/traces.jsonl).
- Audit: [phương pháp và nhãn](../../results/audit/README.md),
  [coherence](../../results/audit/coherence_labels.jsonl),
  [metadata](../../results/audit/metadata_labels.csv),
  [grounding](../../results/audit/grounding_labels.jsonl),
  [summary](../../results/audit/summary.json), [provenance](../../results/audit/provenance.json).
- [Nhật ký thí nghiệm](../../artifacts/experiment_log.csv),
  [selection trước test](../../results/selection.json), [test marker](../../results/test_started.json).

Giới hạn: một sách tiếng Anh, query tiếng Việt, test 5 câu có nhóm gần nhau,
gold dựa trên trích đoạn và có thể chưa liệt kê hết bằng chứng tương đương, mẫu
coherence thiên về đầu trang, một người chấm đồng thời là người xây pipeline,
không blind. Timing chỉ minh họa; chưa tính chi phí phần cứng. Grounding là độ đủ bằng
chứng truy xuất, **không phải độ chính xác câu trả lời LLM**.


**Access for free at openstax.org.** Nội dung sách/đoạn trích dẫn xuất theo
CC BY-NC-SA 4.0; báo cáo ghi rõ công cụ AI và cách kiểm tra, không giả lập kết quả
chưa chạy.

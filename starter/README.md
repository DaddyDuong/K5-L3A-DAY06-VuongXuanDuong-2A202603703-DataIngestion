# Pipeline lab — PostgreSQL + pgvector + E5 local

Pipeline đã triển khai trong `src/`: đọc corpus JSONL theo trang, chia chunk,
embedding thật trên CPU, lưu PostgreSQL/pgvector, tìm top-3 và đánh giá evidence.
Mặc định chỉ chạy **dev**. Không cần API key.

**Trạng thái bài hiện tại:** đã hoàn thành một run test và có [báo cáo](../report/individual/2A202603703_VuongXuanDuong.md),
[kết quả/audit](../results/README.md). Nhãn định tính do Codex soạn sơ bộ, học viên đã
đọc lại và xác nhận. Không thay tham số dựa trên test. Các lệnh mặc định dưới đây mô tả luồng
ban đầu; bản repo có `results/test_started.json` nên muốn tái lập cần dùng thư mục riêng:

```bash
python -m src.run --split dev --output-root ../results/reproduction
python -m src.run --split test --output-root ../results/reproduction
```

Đây là tái lập tập đã công bố, không phải holdout mới. Để chỉ tổng hợp nhãn audit đã
ghi nhận: `python scripts/summarize_audit.py` (không chạy lại retrieval).

## Dữ liệu và cấu hình

- Corpus: `../data/processed/pages.jsonl`, 52 trang được giữ, 42 trang được tính
  bảo thủ; nguồn và giấy phép tại [data/README.md](../data/README.md).
- Benchmark: `../benchmark/questions.jsonl`, 15 dev / 5 test đã chốt; quy tắc tại
  [benchmark/README.md](../benchmark/README.md).
- Tham số: [config.json](config.json).
- Model: [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small),
  revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, 384 chiều, CPU.
- Document dùng prefix `passage: `; query dùng `query: `; chuẩn hóa vector L2.
  Giới hạn 512 token, báo lỗi nếu vượt giới hạn thay vì âm thầm cắt.
- Vector store: PostgreSQL 16 + pgvector 0.8.7, metric cosine, **exact search**,
  không tạo ANN index. Filter JSONB được áp dụng trước khi lấy top-3.

| Cấu hình | Chia chunk | Filter |
|---|---|---|
| A | 500 ký tự, overlap 50 | Không |
| B | Ưu tiên ranh giới đoạn, tối đa 500 ký tự, không overlap | Không |
| C | Chunk giống hệt B | Theo chapter khi câu hỏi yêu cầu |

A–B so sánh hai chiến lược chunking (cả ranh giới và overlap thay đổi), không
quy mọi khác biệt cho riêng ranh giới đoạn. B–C chỉ đổi filter. Code kiểm tra ID
chunk B/C giống nhau. Cả ba dùng cùng model, snapshot, query và vector store.

## Setup tái lập

Đã chạy trên Linux x86_64, Python 3.14.10, PyTorch CPU. Cần Docker Compose;
Poppler (`pdftotext`, `pdfinfo`) để chuẩn bị/kiểm tra corpus.
Các lệnh dưới đây chạy từ thư mục `starter/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'torch==2.15.0+cpu' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-lock.txt
```

`requirements-lock.txt` lưu toàn bộ phiên bản đã cài trên môi trường thực nghiệm.
Nếu chọn môi trường khác, `requirements.txt` liệt kê dependencies chính; cần tự
chọn bản PyTorch phù hợp và ghi lại thay đổi. Lần tải model đầu cần mạng và dung
lượng đĩa. Model tải từ Hugging Face; inference chạy local, không gửi corpus hay
câu hỏi tới API embedding.

Chỉ copy `.env` nếu chưa có, để không ghi đè cấu hình cá nhân:

```bash
[ -f .env ] || cp .env.example .env
docker compose -p day6_student_starter up -d --wait
python scripts/check_setup.py
```

Database chỉ bind `127.0.0.1:55433`. Thông tin local mặc định ở `.env.example`;
`.env` bị gitignore. Volume Docker giữ dữ liệu khi dừng container. `init.sql` chỉ
chạy trên volume mới; không cần xóa volume để chạy pipeline.

Nếu tái lập corpus trên máy mới (chạy từ root repo):

```bash
python3 starter/scripts/prepare_corpus.py
python3 starter/scripts/check_benchmark.py
```

Đối chiếu checksum snapshot trong manifest; PDF nguồn có thể được nhà xuất bản
cập nhật. Không tự ghi đè benchmark lock để bỏ qua thay đổi dữ liệu.

## Chạy dev

Từ `starter/`, với venv đã kích hoạt:

```bash
python -m src.run --split dev
```

Lệnh kiểm tra benchmark/corpus, nạp vector cho A/B/C vào schema
`day6_ingestion`, chạy 15 câu dev và xuất thư mục có timestamp ở `../results/`.
Mỗi lần chạy giữ thư mục kết quả riêng, không ghi đè trace cũ.

Dữ liệu mỗi strategy trong database là một **snapshot đầy đủ**: nạp lại thay
snapshot đó trong transaction, xóa chunk cũ và tài liệu đã bị loại bỏ, giữ nguyên
các strategy khác. ID chunk ổn định theo tài liệu, trang, cấu hình, offset và
text. Pipeline tự nạp hai lần, kiểm tra số lượng không đổi, rồi mở kết nối mới
để kiểm tra số lượng đã lưu.

Model load và query embedding được báo riêng. Thời gian ingest gồm chunking,
document embedding và lần ghi đầu tiên; không gồm lần ghi kiểm tra nạp lại.
Ba cấu hình đều được embed độc lập để ghi thời gian, kể cả B/C có cùng text.
Warm-up và thứ tự A/B/C vẫn gây sai số; đây là một lần đo minh họa.
Chi phí dịch vụ trả phí là 0 USD; chưa tính điện, phần cứng, mạng và công sức.

## Đọc kết quả

Mỗi thư mục run có:

- `summary.md`, `summary.json`: Hit@1/Hit@3 dạng n/N; số chunk, phân bố độ dài,
  token, thời gian, chi phí và số bản ghi sau nạp lại.
- `traces.jsonl`: mọi câu của split đang chạy, top-3 text/score/metadata, gold,
  filter yêu cầu/filter thực sự áp dụng và nhãn exact-evidence.
- `chunks_A.jsonl`, `chunks_B.jsonl`, `chunks_C.jsonl`: chunk và offset nguồn.
- `run_metadata.json`: model/revision, phiên bản Python/thư viện/database,
  cấu hình và checksum dữ liệu/code.
- `coherence_samples.jsonl`: mẫu cùng 10 vị trí nguồn, **nhãn để trống**.
- `run.log`; nếu lỗi có `failure.json`, không fallback mock.

`../results/selection.json` ghi cấu hình được chọn theo dev: ưu tiên Hit@3,
Hit@1, thời gian ingest, rồi thứ tự A/B/C nếu vẫn hòa. Quy tắc này được ghi trong
benchmark trước retrieval. `../artifacts/experiment_log.csv` được cập nhật bằng
kết quả thực, cột test để trống khi chỉ chạy dev.

Hit tự động yêu cầu đúng document/page và chứa đầy đủ evidence chính hoặc một
alternative hợp lệ sau chuẩn hóa whitespace. Bằng chứng đúng nhưng diễn đạt
khác chưa ghi vào gold có thể bị bỏ sót; cần audit thủ công và ghi lý do nhất
quán. Nếu evidence bị cắt qua nhiều chunk, metric chính tính miss. Không suy ra
điểm coherence, metadata hay grounding từ Hit@3.

## Truy vấn thử

Sau dev, có thể tìm top-3 bằng câu hỏi riêng:

```bash
python -m src.query 'Trong chương Files, thư viện nào trích xuất thông tin từ PDF?' --strategy C --chapter 14
```

CLI chỉ tạo query embedding từ câu hỏi; không truy cập gold để tìm đáp án. Trả
về evidence cùng nguồn/trang/score, không gọi LLM sinh câu trả lời.

## Test holdout và chấm thủ công

Chưa cần chạy lệnh dưới đây trong giai đoạn phát triển. Khi đã cố định lựa chọn:

```bash
python -m src.run --split test
```

Lệnh yêu cầu selection dev tồn tại và checksum code/config/corpus/benchmark
không thay đổi. Xuất kết quả cho cả ba cấu hình, cùng file
`human_audit_samples.jsonl` để điền nhãn grounding/metadata. Sau khi mở test,
lệnh dev ở cùng output root bị chặn để tránh vô tình tiếp tục tinh chỉnh rồi
báo như holdout độc lập. Thí nghiệm mới phải được ghi nhận riêng.

Mẫu chấm thủ công mới là đầu vào để học viên đọc và ghi nhãn; pipeline không
điền thay nhãn con người. Báo cáo cá nhân, audit đầy đủ và phân tích lỗi vẫn cần
hoàn thiện theo GUIDE.md.

## Kiểm tra code

```bash
python -m unittest discover -s tests -v
RUN_DB_TESTS=1 python -m unittest discover -s tests -v
```

Lệnh thứ hai dùng PostgreSQL thật, tạo strategy riêng với ID ngẫu nhiên rồi dọn
chính các dòng đó. Vector cơ sở trong test chỉ kiểm tra toán/ranking của store;
pipeline thực dùng model E5. Test bao phủ offset và độ phủ nội dung, Unicode,
evidence/alternative, filter, nạp lại, xóa chunk cũ, kết nối lại và từ chối batch
vector sai mà không mất snapshot hiện có.

Dừng database nhưng giữ dữ liệu:

```bash
docker compose -p day6_student_starter stop
```

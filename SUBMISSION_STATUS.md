# Trạng thái bài nộp

Bài đã có pipeline, dev/test thực tế, nhãn định tính đã được học viên xác nhận và báo cáo cá nhân.
Bài đã được commit và push lên nhánh `main`; commit chốt ghi trong STUDENT.md.

| Thành phần | Minh chứng / trạng thái |
|---|---|
| Thông tin học viên | [STUDENT.md](STUDENT.md) |
| Corpus ≥30 trang | [Manifest](data/manifest.json), giữ 52 trang, đếm bảo thủ 42 trang |
| Nguồn, giấy phép, cách lấy | [Hồ sơ dữ liệu](data/README.md), PDF gốc và script tái tạo |
| Benchmark ≥20 câu | [20 câu, 15 dev / 5 test](benchmark/questions.md), 3 câu filter, trong đó 1 test |
| Embedding thật và store | E5 local 384 chiều, PostgreSQL/pgvector; [setup/run](starter/README.md) |
| Ba cấu hình kiểm soát | A fixed, B paragraph, C = B + chapter filter; config/code giữ nguyên giữa dev/test |
| Trace và số liệu dev/test | [Kết quả](results/README.md), full top-3 và model/time/cost |
| Audit coherence / grounding / metadata | [Nhãn và phương pháp](results/audit/README.md): 30 / 15 / 45 bản ghi; Codex soạn sơ bộ, **học viên đã đọc lại và xác nhận** |
| Năm khía cạnh và ví dụ lỗi | [Báo cáo cá nhân](report/individual/2A202603703_VuongXuanDuong.md) |
| Nhật ký thí nghiệm | [CSV](artifacts/experiment_log.csv), có dev và test, không giả lập số liệu |
| Re-ingestion và persistence | 222/252/252 chunk sau nạp lại/kết nối mới; 11 unit/integration tests đã đạt |
| Secret và môi trường | `.env` và `.venv` được gitignore; không đưa key vào code/artifacts do assistant tạo |
| Người học kiểm tra và giải thích bài | Học viên đã đọc, đối chiếu nhãn với nguồn và xác nhận |
| Commit/push/quyền truy cập/nộp link | Đã commit và push lên `main`, repo public; link và commit chốt trong STUDENT.md |

Giữ nguyên gold, raw metric và raw trace. Evidence tương đương A/q19 được ghi riêng
trong overlay thủ công; không dùng kết quả test để sửa pipeline hoặc chọn lại cấu hình.
Nội dung nguồn có ghi công và điều kiện CC BY-NC-SA 4.0 theo hồ sơ corpus.

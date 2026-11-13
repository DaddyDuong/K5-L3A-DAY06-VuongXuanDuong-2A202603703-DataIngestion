# Kết quả lab — dev, test và audit

- Dev chốt cấu hình: [20261113T103339652250Z-dev](20261113T103339652250Z-dev/summary.md).
- Test duy nhất: [20261113T103637017303Z-test](20261113T103637017303Z-test/summary.md).
- [Báo cáo cá nhân](../report/individual/2A202603703_VuongXuanDuong.md).
- [Phương pháp và nhãn audit](audit/README.md).

**Selection trước test: C. Code/config/corpus/benchmark giữ nguyên giữa dev và test.**

| Strategy | Dev Hit@1 | Dev strict Hit@3 | Test Hit@1 | Test strict Hit@3 | Test Hit@3 sau đối chiếu |
|---|---|---|---|---|---|
| A | 6/15 | 7/15 | 2/5 | 2/5 | 3/5 |
| B | 9/15 | 11/15 | 2/5 | 3/5 | 3/5 |
| C | 9/15 | 11/15 | 2/5 | 3/5 | 3/5 |

Strict metric khớp đầy đủ gold/evidence sau chuẩn hóa whitespace. Overlay thủ công
chấp nhận thêm một bằng chứng tương đương A/q19, giữ riêng raw metric; gold và
trace gốc không sửa. Grounding không phải độ chính xác câu trả lời LLM.

| Strategy | Coherence TB /2 | Metadata đúng | Top-3 đúng phạm vi yêu cầu | Grounding TB /2 |
|---|---|---|---|---|
| A | 0.90 (10 mẫu) | 15/15 | 1/1 | 1.60 (5 câu) |
| B | 1.10 (10 mẫu) | 15/15 | 1/1 | 1.60 (5 câu) |
| C | 1.10 (10 mẫu) | 15/15 | 1/1 | 1.60 (5 câu) |

**Nhãn định tính do Codex soạn sơ bộ, học viên đã đọc lại và xác nhận.**
A/B không áp filter nhưng q19 tình cờ đúng chương; C áp filter thật. B/C có
chunk và top-3 test giống nhau, chưa thấy lợi ích filter trên mẫu nhỏ này.

## Minh chứng và tái lập

- [Test trace top-3](20261113T103637017303Z-test/traces.jsonl): 15 trường hợp, 45 hit.
- [Metadata test run](20261113T103637017303Z-test/run_metadata.json): model/revision, phiên bản, fingerprint, chi phí.
- [Dev trace](20261113T103339652250Z-dev/traces.jsonl): 45 trường hợp, 135 hit.
- [Selection trước test](selection.json), [thời điểm mở test](test_started.json).
- [Audit summary](audit/summary.json), [nhãn và phương pháp](audit/README.md).
- [Query demo thật](query_demo.json).
- [Hướng dẫn setup/run](../starter/README.md).

Đã chạy 11 unit/integration tests với PostgreSQL thật; nạp lại và mở kết nối mới
giữ 222/252/252 chunk. Cả ba chạy embedding E5 local, chi phí dịch vụ trả phí 0 USD
(chưa tính điện/phần cứng/mạng/công sức). Không dùng mock inference.

Giữ hai run dev và một run test. Dev đầu kiểm tra pipeline; dev cuối xác nhận
code sau sửa CSV/đường dẫn, không đổi tham số thí nghiệm. Timing nhỏ và nhiễu làm
lựa chọn hòa khác nhau giữa hai dev run; lựa chọn cuối C đã chốt trước test.
Không chạy lại hoặc tinh chỉnh bằng test. Tái lập cùng tập công bố không tạo
holdout mới; dùng output root riêng theo starter README để giữ lịch sử.

Access for free at openstax.org. Đoạn sách trong trace/chunk theo CC BY-NC-SA 4.0.

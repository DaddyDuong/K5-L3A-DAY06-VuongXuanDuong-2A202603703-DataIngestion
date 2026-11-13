# Benchmark v1 — Python Files và Data Science

**Access for free at openstax.org.** Các đoạn trích từ OpenStax / Rice University,
*Introduction to Python Programming*, theo CC BY-NC-SA 4.0. Nguồn, snapshot và
điều kiện ghi công: [hồ sơ corpus](../data/README.md).

## Bộ câu hỏi đã chuẩn bị

- `questions.jsonl`: 20 câu hỏi tiếng Việt, đáp án tiếng Việt và bằng chứng tiếng
  Anh trích nguyên văn từ corpus. Mỗi dòng là một đối tượng JSON.
- `q01`–`q15`: dev (15 câu); `q16`–`q20`: test (5 câu).
- Câu có filter: `q06` (`chapter=14`), `q10` và `q19` (`chapter=15`). `q19`
  thuộc test. Các câu này nêu rõ chương trong câu hỏi; filter không lấy từ đáp án.
- Có 10 bằng chứng thay thế đã ghi nhận, chủ yếu từ phần tổng kết sách.
- `benchmark_lock.json`: mã SHA-256 của câu hỏi, corpus PDF và text theo trang,
  danh sách ID dev/test/filter và tiêu chí chọn cấu hình được chốt trước retrieval.

Các câu phủ đọc/ghi file, thư viện xử lý file, ngoại lệ, vòng đời khoa học dữ liệu,
NumPy, Pandas, indexing, filtering, dữ liệu thiếu và trực quan hóa. Có câu trực
tiếp, diễn đạt lại, so sánh, có điều kiện và có phạm vi metadata. Câu hỏi tiếng
Việt trên tài liệu tiếng Anh tạo thêm yêu cầu truy xuất xuyên ngôn ngữ; giữ
nguyên ngôn ngữ câu hỏi giữa cả ba cấu hình và ghi nhận yếu tố này trong báo cáo.

## Ý nghĩa các trường

| Trường | Cách dùng |
|---|---|
| `id`, `split` | ID ổn định và tập dev/test |
| `question` | Chuỗi được gửi để tạo query embedding |
| `expected_answer` | Đáp án tham chiếu, chỉ dùng đánh giá |
| `gold_source_id` | Khớp `document_id` trong corpus |
| `gold_page` | Trang PDF vật lý, bắt đầu từ 1 |
| `gold_printed_page` | Trang in trong sách để người đọc đối chiếu |
| `evidence_quote` | Đoạn bằng chứng nguyên văn từ text đã chuẩn hóa |
| `alternative_gold` | Các bộ nguồn/trang/evidence tương đương được chấp nhận |
| `filter` | `{}` nếu không lọc; nếu có thì lọc theo `chapter` số nguyên |
| `topic`, `type` | Phân tích độ phủ và loại lỗi, không dùng làm query/filter |
| `attribution` | Ghi công đi kèm nội dung dẫn xuất |

Không đưa `expected_answer`, gold, topic hoặc evidence vào embedding câu hỏi
hay bộ lọc. Với A và B, không áp dụng filter; với C, chỉ dùng trường `filter`
đã cung cấp. Câu không có filter chạy C không lọc.

## Chia tập và nguy cơ rò rỉ

Chia tập theo nhóm nội dung khi có thể. Test tập trung vào raise/constructor
(14.5), dữ liệu thiếu trong EDA (15.4) và công cụ visualization (15.5); dev dùng
các nội dung còn lại. Không có trang gold chính trùng giữa dev và test.

Đây không phải chia độc lập hoàn toàn theo tài liệu: hai tập cùng một sách,
phần tổng kết có thể lặp lại nội dung, và EDA xuất hiện trong cả hai tập ở các
tiểu chủ đề khác nhau. Hai câu test về ngoại lệ gần nhau, hai câu về dữ liệu
thiếu cùng trang; do đó 5 câu không phải 5 chủ đề độc lập. Không suy rộng kết quả
ngoài corpus này. Nội dung sách chứa các câu kiểm tra kiến thức tương tự; bộ
benchmark này chưa loại bỏ mọi tín hiệu đó khỏi index.

AI đã hỗ trợ soạn và kiểm chứng vị trí text; học viên cần đọc, hiểu và xác nhận
đáp án/evidence trước khi chốt bài nộp. Việc tác giả benchmark đọc test để viết
nhãn là một phần xây tập, khác với dùng kết quả test để tinh chỉnh retrieval.
Chưa chạy retrieval, chưa có điểm số hay nhãn chấm coherence/grounding.

## Quy tắc thí nghiệm đã chốt

1. Giữ corpus, model, vector store, câu hỏi và định nghĩa metric giống nhau.
2. Thử/chỉnh chiến lược chỉ trên dev.
3. Chọn cấu hình theo dev Evidence Hit@3 cao nhất; nếu bằng nhau, xét dev Hit@1;
   nếu vẫn bằng, xét thời gian ingest đo được thấp hơn; cuối cùng thứ tự A, B, C.
4. Cố định tham số, sau đó chạy test cho cả ba cấu hình để báo cáo. Không dùng
   test để đổi lựa chọn hoặc tham số.
5. Hit@1/Hit@3 yêu cầu một chunk đúng nguồn/trang và đủ evidence chính **hoặc**
   một bộ alternative hợp lệ. Bằng chứng tương đương chưa liệt kê có thể được
   chấp nhận qua xác nhận thủ công có ghi lý do. Không đòi khớp mọi gold cùng lúc.
6. Có thể chuẩn hóa whitespace khi đối chiếu evidence. Không coi trả đúng trang,
   khớp keyword hoặc điểm cosine cao là đủ. Nếu evidence bị chia qua nhiều chunk,
   ghi lỗi; đánh giá hợp nhiều chunk chỉ là chỉ số phụ.
7. Nếu sửa nhãn hoặc thêm nguồn hợp lệ sau khi đã xem test, lưu lịch sử thay đổi,
   lý do và đánh giá lại nhất quán mọi cấu hình; không gọi kết quả đã tinh chỉnh
   theo test là holdout độc lập. Không ghi đè checksum chỉ để bỏ qua cảnh báo.

## Kiểm tra lại

Từ root repo, với Python 3 và Poppler đã cài:

```bash
python3 starter/scripts/check_benchmark.py
```

Lệnh chỉ đọc: kiểm tra checksum, schema cơ bản, split, filter, số trang, và mỗi
đoạn trích có trong cả `pages.jsonl` lẫn text layer trích trực tiếp từ PDF.
Kiểm tra này xác nhận sự tồn tại của evidence, không tự chứng minh mọi đáp án
đúng ngữ nghĩa và không thay cho chấm grounding/coherence thủ công.

Chuẩn bị mẫu coherence trước khi chạy: dùng 10 page ID đầu theo thứ tự số trang
PDF trong corpus, mỗi trang lấy vị trí ký tự đầu của text. Chấm chunk bao phủ
vị trí đó với cùng tiêu chí cho A/B/C. Nếu có nhiều chunk cùng bao phủ, chấm tất
cả và ghi quy tắc tổng hợp. Audit metadata và grounding dùng cùng 5 câu test
cho cả ba cấu hình theo GUIDE.md.

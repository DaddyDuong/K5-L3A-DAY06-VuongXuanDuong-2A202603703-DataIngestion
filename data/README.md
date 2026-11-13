# Corpus: Python Files và Data Science

Corpus dùng cho lab là chương 14 **Files** và chương 15 **Data Science** của
*Introduction to Python Programming*, OpenStax / Rice University.

- Nguồn: https://assets.openstax.org/oscms-prodcms/media/documents/Introduction_to_Python_Programming-WEB.pdf
- Trang giới thiệu: https://openstax.org/details/books/introduction-python-programming
- Bản PDF tải về: `data/raw/Introduction_to_Python_Programming-WEB.pdf`.
- Snapshot, SHA-256, thời điểm lấy và danh sách từng trang: `data/manifest.json`.

## Phạm vi và cách đếm

| Chương | Trang vật lý PDF (bắt đầu từ 1) | Trang in trong sách |
|---|---|---|
| 14 — Files | 319–340 | 309–330 |
| 15 — Data Science | 341–370 | 331–360 |

Giữ **52 trang** để truy xuất, gồm **92.316 ký tự** sau chuẩn hóa bằng
phiên bản công cụ được ghi trong manifest. Đếm bảo thủ **42 trang nội dung**:

- Không tính hai trang mở chương: PDF 319, 341 (vẫn giữ nội dung để truy xuất).
- Không tính bảy trang có phần tổng kết: PDF 338–340, 367–370.
- Không tính PDF 358: trang ít chữ, chỉ tiếp nối bảng dữ liệu.
- Các trang còn lại có phần giải thích, code, ví dụ, bảng hoặc bài tập học tập.

Không dùng bìa, mục lục, answer key hay index của toàn sách làm corpus. Quy tắc
đếm trên cố ý chặt hơn việc giữ tất cả trang có nội dung. Mỗi trang có cờ
`counted_content_page`; kiểm tra chi tiết tại `data/processed/page_audit.csv`.
Không áp dụng ngưỡng 1.500 ký tự cho PDF; ngưỡng đó của đề dành cho cách chia
đơn vị nguồn đối với tài liệu không phân trang.

## Dữ liệu đã chuẩn bị

`data/processed/pages.jsonl`: mỗi dòng là một trang, có:

- `document_id`, `page_id`, `source`, `source_url`.
- `page`: số trang vật lý PDF, dùng cho truy vết và gold benchmark.
- `printed_page`: số trang in trong sách, để người đọc đối chiếu.
- `text`, `char_count` và `attribution`.
- `metadata.chapter`: số nguyên 14 hoặc 15, lấy từ cấu trúc thật của sách.
- `metadata.chapter_title`, `language`, `counted_content_page`.

Dùng `chapter` làm trường filter. Giá trị phải đến từ yêu cầu của câu hỏi hoặc
ngữ cảnh cung cấp trước truy xuất. Chưa có câu hỏi benchmark, gold hoặc kết quả
retrieval trong bước chuẩn bị này.

## Tái tạo

Chạy từ root repository, cần Python 3 và Poppler cung cấp `pdftotext`, `pdfinfo`:

```bash
python3 starter/scripts/prepare_corpus.py
```

Script tải PDF nếu chưa có, đọc snapshot hiện tại, chuẩn hóa Unicode NFC,
giữ thụt dòng code và ranh giới đoạn, xuất lại manifest và dữ liệu theo trang.
Footer ghi công được chuyển sang trường `attribution` của từng trang;
header số trang vẫn được giữ. Không cần API key hoặc embedding ở bước này.
Để tái lập đúng snapshot, đối chiếu SHA-256 trong manifest vì URL có thể cập nhật.

## Quyền sử dụng và giới hạn

**Access for free at openstax.org.**

OpenStax / Rice University, *Introduction to Python Programming*, bản PDF có
copyright 2026, năm xuất bản gốc 2024. Trang vật lý PDF 4 ghi giấy phép
**Creative Commons Attribution-NonCommercial-ShareAlike 4.0**:
https://creativecommons.org/licenses/by-nc-sa/4.0/ .

Giữ ghi công, chỉ chia sẻ/sử dụng theo điều kiện phi thương mại và áp dụng cùng
giấy phép cho phần nội dung chuyển đổi/phái sinh khi phân phối. PDF gốc giữ
nguyên thông báo quyền. `data/processed/source_license.txt` lưu phần thông báo
trích từ PDF. Không coi giấy phép sách là giấy phép chung cho mã nguồn repo;
logo, nhãn hiệu và nội dung bên thứ ba có thể có điều kiện riêng trong sách.
Khi hiển thị/xuất các trang hoặc chunk dẫn xuất, giữ dòng ghi công đi kèm.

Đã kiểm tra các trang được chọn đều có text và đối chiếu ranh giới chương.
Không có OCR. Bảng nhiều cột và hình có thể không được thể hiện đầy đủ khi trích
text; code có thể bị ngắt dòng theo bố cục PDF. Việc trích xuất thành công không
thay cho kiểm chứng evidence: khi xây benchmark phải đọc PDF và xác minh từng
đoạn trích sau chuẩn hóa, đặc biệt các câu liên quan bảng/hình.

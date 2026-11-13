# Audit định tính

**Người đánh giá: Vương Xuân Dương (học viên).** Codex soạn nhãn sơ bộ kèm lý do;
học viên đã đọc lại từng nhãn, đối chiếu nguồn và xác nhận.

Nhãn dựa trên việc đọc từng mẫu/trace và đối chiếu nguồn, không lấy điểm cosine hay
Hit@3 làm điểm coherence/grounding. Người chấm đã biết metric và cũng là người xây
pipeline/benchmark: không blind, có thể thiên lệch tự xác nhận.

## Phương pháp

- Coherence: cùng 10 trang PDF 319–328, offset 0, đã chốt trước retrieval; 30 mẫu A/B/C.
- 0: cắt ý/không hiểu độc lập; 1: hiểu một phần/thiếu ngữ cảnh; 2: trọn ý, tự hiểu.
- Grounding: 5 câu test × 3 cấu hình; 0 không có bằng chứng, 1 có nhưng thiếu điều kiện/ngữ cảnh, 2 đủ trả lời và truy nguồn.
- Đã đọc đủ 15 trường hợp top-3; đối chiếu text layer PDF của mọi trang được trả về.
- Đã xem ảnh gốc trang PDF 324, 336, 337, 357, 361 để kiểm tra layout và gold test.
- Metadata: 45 bản ghi, kiểm tra document/source, trang vật lý/trang in, chương, offset/text và attribution. Tất cả check đã đạt; mỗi bản ghi có nhãn riêng.
- Cùng chunk B/C được dùng cùng nhãn coherence; cùng top-3 được dùng cùng nhãn grounding sau khi xác nhận ID/text/metadata giống nhau.
- Mẫu đầu trang có nhiều header/bảng/phần tiếp nối và chỉ thuộc Files; không đại diện toàn corpus.

## File bằng chứng

- [Quyết định chấm và lý do gốc](review_decisions.json).
- [Coherence với toàn bộ text chunk](coherence_labels.jsonl).
- [45 nhãn metadata](metadata_labels.csv).
- [15 nhãn grounding và per-hit evidence](grounding_labels.jsonl).
- [Tổng hợp](summary.json), [checksum đầu vào và phương pháp](provenance.json).
- Tổng hợp lại bằng `starter/.venv/bin/python starter/scripts/summarize_audit.py` từ root; script không tự sinh nhãn định tính và không chạy retrieval.

Các file `human_audit_samples.jsonl` trong raw run là template do pipeline sinh ra
và được giữ nguyên; nhãn cuối cùng nằm trong thư mục `results/audit/` này.

## Coherence từng vị trí

| Strategy | Trang PDF | Điểm /2 | Lý do |
|---|---|---|---|
| A | 319 | 1 | Giữ được đoạn giới thiệu đọc/ghi file nhưng kết thúc ở "Reading and writing fi", cắt giữa từ và ý tiếp theo. |
| A | 320 | 1 | Câu hỏi mở file thứ nhất đủ lựa chọn, nhưng câu thứ hai bị cắt ở "Suppose that there is no file". |
| A | 321 | 1 | Phần read() đầu có đóng file, nhưng ví dụ tiếp theo bị cắt giữa comment "into a str"; chưa trọn ví dụ. |
| A | 322 | 1 | Có dữ liệu input và câu hỏi read(), nhưng phần trả lời/lựa chọn tiếp nối nằm ngoài chunk. |
| A | 323 | 1 | Mục tiêu Writing to files đầy đủ, nhưng đầu chunk là output của ví dụ trang trước chưa có ngữ cảnh giải thích. |
| A | 324 | 0 | Bảng mode bị cắt ở điều kiện "If the file does not"; các cột nhiều khoảng trắng làm hàng không trọn nghĩa. |
| A | 325 | 1 | Có giải thích close() và code ghi file, nhưng kết thúc giữa comment lưu thay đổi; ví dụ chưa đủ vòng đời file. |
| A | 326 | 1 | Có output và tiêu đề write()/close(); bài tập hỏi về các snippet nhưng chưa có snippet nào trong chunk. |
| A | 327 | 1 | Bài tập out.txt đầu đầy đủ; bài tập out.log tiếp theo bị cắt ở "after the cod". |
| A | 328 | 1 | Đọc được hàng Mac/Linux của bảng đường dẫn, nhưng hàng Windows bị cắt giữa lệnh open(). |
| B | 319 | 2 | Kết thúc đúng sau đoạn giới thiệu đọc/ghi file, giữ trọn câu và đủ chủ đề chương; không cắt sang đoạn sau. |
| B | 320 | 2 | Giữ trọn một câu hỏi mở file cùng ba lựa chọn, dừng trước câu tiếp theo; tự hiểu được yêu cầu. |
| B | 321 | 1 | Giữ nguyên các dòng code, nhưng chia giữa ví dụ: phần thứ hai mới mở infile2, chưa có thao tác đọc/đóng. |
| B | 322 | 1 | Giữ trọn phần dẫn và dữ liệu input.txt nhưng chưa có câu hỏi/thao tác cụ thể; cần chunk sau để hoàn tất bài tập. |
| B | 323 | 1 | Mục tiêu học tập đủ ý nhưng output đầu trang thuộc ví dụ trước, nên toàn chunk còn thiếu ngữ cảnh. |
| B | 324 | 0 | Chunk chỉ chứa số trang và tiêu đề cột Parameter/Mode name/Example, không có hàng nội dung nào. |
| B | 325 | 1 | Dừng tại ranh giới đoạn, không cắt từ, nhưng code ví dụ ghi file vẫn chưa có close()/append; cần phần tiếp nối. |
| B | 326 | 1 | Giữ hết câu dẫn bài tập nhưng chưa chứa snippet để đọc và trả lời; output đầu chunk cũng thiếu code gốc. |
| B | 327 | 1 | Giữ trọn bài tập out.txt, nhưng kết thúc bằng tiêu đề TRY IT trống của bài tiếp theo. |
| B | 328 | 1 | Giữ trọn hàng Mac/Linux; bảng còn hàng Windows ở chunk kế tiếp, nên chỉ hiểu được một phần bảng nguồn. |
| C | 319 | 2 | Kết thúc đúng sau đoạn giới thiệu đọc/ghi file, giữ trọn câu và đủ chủ đề chương; không cắt sang đoạn sau. |
| C | 320 | 2 | Giữ trọn một câu hỏi mở file cùng ba lựa chọn, dừng trước câu tiếp theo; tự hiểu được yêu cầu. |
| C | 321 | 1 | Giữ nguyên các dòng code, nhưng chia giữa ví dụ: phần thứ hai mới mở infile2, chưa có thao tác đọc/đóng. |
| C | 322 | 1 | Giữ trọn phần dẫn và dữ liệu input.txt nhưng chưa có câu hỏi/thao tác cụ thể; cần chunk sau để hoàn tất bài tập. |
| C | 323 | 1 | Mục tiêu học tập đủ ý nhưng output đầu trang thuộc ví dụ trước, nên toàn chunk còn thiếu ngữ cảnh. |
| C | 324 | 0 | Chunk chỉ chứa số trang và tiêu đề cột Parameter/Mode name/Example, không có hàng nội dung nào. |
| C | 325 | 1 | Dừng tại ranh giới đoạn, không cắt từ, nhưng code ví dụ ghi file vẫn chưa có close()/append; cần phần tiếp nối. |
| C | 326 | 1 | Giữ hết câu dẫn bài tập nhưng chưa chứa snippet để đọc và trả lời; output đầu chunk cũng thiếu code gốc. |
| C | 327 | 1 | Giữ trọn bài tập out.txt, nhưng kết thúc bằng tiêu đề TRY IT trống của bài tiếp theo. |
| C | 328 | 1 | Giữ trọn hàng Mac/Linux; bảng còn hàng Windows ở chunk kế tiếp, nên chỉ hiểu được một phần bảng nguồn. |

## Grounding từng câu test

| Strategy | Câu | Điểm /2 | Lý do |
|---|---|---|---|
| A | q16 | 1 | Top-3 mô tả trường hợp ĐÃ bắt FileNotFoundError và cấu trúc try/except; không có đủ cả thông báo lỗi lẫn kết thúc khi KHÔNG bắt ngoại lệ. |
| A | q17 | 2 | Rank 1, PDF 337, có câu nêu rõ raise trong constructor ngăn tạo đối tượng không hợp lệ, kèm ví dụ p1/p2. |
| A | q18 | 2 | Rank 1, PDF 357, nêu đủ Boolean DataFrame, cùng kích thước nguồn và True tại vị trí thiếu. |
| A | q19 | 2 | Rank 2, PDF 357, có ví dụ df.fillna(df.mean()) được giải thích là thay mọi Null bằng trung bình cột; đủ xác định fillna() là hàm thay thế. Rank 1 chỉ là trắc nghiệm, không được dùng làm bằng chứng quyết định. Đây là bằng chứng tương đương, không khớp toàn bộ gold nguyên văn. |
| A | q20 | 1 | Top-3 chỉ có nhóm thư viện data science/EDA hoặc câu hỏi công cụ; không thấy đủ bộ Matplotlib, Plotly và Seaborn để trả lời. |
| B | q16 | 1 | Top-3 nói về ngoại lệ được bắt và cách chạy try/except; thiếu kết luận đầy đủ về thông báo lỗi và kết thúc khi không xử lý. |
| B | q17 | 2 | Rank 2, PDF 337, giữ trọn câu về ngăn tạo đối tượng không hợp lệ. Rank 1 là bài tập constructor khác nên top-1 chưa đủ. |
| B | q18 | 2 | Rank 1, PDF 357, giữ đủ định nghĩa isnull(), kiểu/kích thước kết quả và ý nghĩa True; hai rank sau chỉ là bảng rời. |
| B | q19 | 1 | Rank 1, PDF 360, chỉ là câu trắc nghiệm fillna(0)/replacena(0)/fill(0) không kèm nhãn đáp án; rank 2 và 3 chỉ là header. Không dùng kiến thức ngoài corpus để chọn hộ đáp án. |
| B | q20 | 2 | Rank 1, PDF 361, có đủ ba framework Matplotlib, Plotly và Seaborn; nguồn và trang có thể truy vết. |
| C | q16 | 1 | Top-3 nói về ngoại lệ được bắt và cách chạy try/except; thiếu kết luận đầy đủ về thông báo lỗi và kết thúc khi không xử lý. |
| C | q17 | 2 | Rank 2, PDF 337, giữ trọn câu về ngăn tạo đối tượng không hợp lệ. Rank 1 là bài tập constructor khác nên top-1 chưa đủ. |
| C | q18 | 2 | Rank 1, PDF 357, giữ đủ định nghĩa isnull(), kiểu/kích thước kết quả và ý nghĩa True; hai rank sau chỉ là bảng rời. |
| C | q19 | 1 | Rank 1, PDF 360, chỉ là câu trắc nghiệm fillna(0)/replacena(0)/fill(0) không kèm nhãn đáp án; rank 2 và 3 chỉ là header. Không dùng kiến thức ngoài corpus để chọn hộ đáp án. |
| C | q20 | 2 | Rank 1, PDF 361, có đủ ba framework Matplotlib, Plotly và Seaborn; nguồn và trang có thể truy vết. |

## Evidence tương đương và giới hạn metric

A/q19/rank 2 ở PDF 357 có ví dụ fillna với giá trị trung bình cột được giải thích
rõ là thay Null. Nhận đây là bằng chứng tương đương trong overlay thủ công: strict Hit@3
A vẫn 2/5, Hit@3 sau đối chiếu của A là 3/5. B/C đều 3/5 theo cả hai cách.
Gold/alternative đã chốt, raw trace và lựa chọn C trước test được giữ nguyên.
Không chấp nhận câu trắc nghiệm không kèm đáp án là bằng chứng đủ chỉ vì người chấm
biết câu trả lời từ bên ngoài. Không áp dụng sửa metric không nhất quán giữa các cấu hình.

q19 của A/B/C đều có top-3 đúng chương: A/B không thực sự áp filter, C có áp filter.
Tỷ lệ tuân thủ phạm vi 1/1 vì vậy không chứng minh filter cải thiện retrieval.

Access for free at openstax.org. Nội dung dẫn xuất từ OpenStax / Rice University,
CC BY-NC-SA 4.0; chi tiết nguồn/quyền tại [data/README.md](../../data/README.md).

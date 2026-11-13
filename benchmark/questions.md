# Bộ 20 câu hỏi — bản đọc thuận tiện

Bản dữ liệu chuẩn để chạy: `questions.jsonl`. Quy tắc đánh giá: `README.md`.

Nguồn: OpenStax / Rice University, Introduction to Python Programming, CC BY-NC-SA 4.0.

## q01 — dev

read() và readline() khác nhau như thế nào về phần nội dung đọc từ file và kiểu giá trị trả về?

**Đáp án:** read() đọc nội dung file, còn readline() đọc dòng kế tiếp; cả hai trả về chuỗi.

**Nguồn:** trang PDF 320, trang in 310. **Filter:** `{}`.

**Bằng chứng:**

> The read() function reads the contents of a file and returns a string.
>         • The readline() function reads the next line in a file and returns a string.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 339.

## q02 — dev

Phương thức nào đọc tất cả các dòng của file thành danh sách chuỗi và giữ thứ tự dòng?

**Đáp án:** readlines() trả về danh sách chuỗi gồm mọi dòng theo thứ tự trong file.

**Nguồn:** trang PDF 320, trang in 310. **Filter:** `{}`.

**Bằng chứng:**

> The readlines() function reads the individual lines of a file and returns a string list containing all the
>             lines of the file in order.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 339.

## q03 — dev

Nếu muốn ghi một giá trị không phải chuỗi bằng write(), cần chuyển đổi giá trị như thế nào trước khi ghi?

**Đáp án:** Phải chuyển giá trị sang chuỗi; write() chỉ nhận tham số chuỗi.

**Nguồn:** trang PDF 324, trang in 314. **Filter:** `{}`.

**Bằng chứng:**

> The write() function is used to write to an already opened file. The write() function will only accept a string
>       parameter. Other variable types must be cast to string before writing using write().

Access for free at openstax.org.

## q04 — dev

write() có tự thêm ký tự xuống dòng giống print() không, và phải làm gì nếu cần xuống dòng?

**Đáp án:** Không; phải thêm tường minh ký tự xuống dòng \n vào chuỗi được ghi.

**Nguồn:** trang PDF 324, trang in 314. **Filter:** `{}`.

**Bằng chứng:**

> The write() function does not automatically add a newline character as the print() function does. A
>       newline must be added explicitly by adding a newline ('\n') character.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 339.

## q05 — dev

Theo phần Writing to files, close() thực hiện hai việc gì với file?

**Đáp án:** Hoàn tất các thay đổi và đóng file.

**Nguồn:** trang PDF 325, trang in 315. **Filter:** `{}`.

**Bằng chứng:**

> The close() function finalizes changes
> and closes the file.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 339.

## q06 — dev

Trong chương 14 — Files, sách giới thiệu thư viện nào để trích xuất thông tin từ PDF?

**Đáp án:** PyPDF.

**Nguồn:** trang PDF 331, trang in 321. **Filter:** `{"chapter": 14}`.

**Bằng chứng:**

> PyPDF (https://openstax.org/r/100readthedocs) is a popular library that can be used to extract information
>  from PDF files.

Access for free at openstax.org.

## q07 — dev

Theo danh sách runtime errors, tên file hoặc đường dẫn không hợp lệ có thể gây ngoại lệ nào?

**Đáp án:** FileNotFoundError.

**Nguồn:** trang PDF 331, trang in 321. **Filter:** `{}`.

**Bằng chứng:**

> FileNotFoundError: The filename or path is invalid.

Access for free at openstax.org.

## q08 — dev

Trong xử lý ngoại lệ, try và except đảm nhiệm những vai trò gì?

**Đáp án:** try chạy đoạn code có thể phát sinh ngoại lệ; except chạy code phản hồi ngoại lệ.

**Nguồn:** trang PDF 333, trang in 323. **Filter:** `{}`.

**Bằng chứng:**

> A try statement runs code that might
> raise an exception. An except clause runs code in response to the exception.

Access for free at openstax.org.

## q09 — dev

Hai giai đoạn đầu tiên của vòng đời khoa học dữ liệu được sách nêu theo thứ tự nào?

**Đáp án:** Thu thập dữ liệu (data acquisition), rồi khám phá dữ liệu (data exploration).

**Nguồn:** trang PDF 342, trang in 332. **Filter:** `{}`.

**Bằng chứng:**

> The data science life cycle is an iterative process
>       that starts with data acquisition, followed by data exploration.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 367.

## q10 — dev

Trong chương 15 — Data Science, dùng hàm NumPy nào để chuyển một list hoặc tuple Python thành ndarray?

**Đáp án:** np.array().

**Nguồn:** trang PDF 344, trang in 334. **Filter:** `{"chapter": 15}`.

**Bằng chứng:**

> Creating an ndarray by converting a Python list or tuple using the np.array() function.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 368.

## q11 — dev

Hai hàm NumPy nào được dùng để tạo mảng toàn số 0 và mảng toàn số 1, tương ứng?

**Đáp án:** np.zeros() tạo mảng toàn 0; np.ones() tạo mảng toàn 1.

**Nguồn:** trang PDF 344, trang in 334. **Filter:** `{}`.

**Bằng chứng:**

> Using built-in functions like np.zeros() and np.ones() for creating an array of all 0's or all 1's,
>          respectively.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 368.

## q12 — dev

Series và DataFrame khác nhau thế nào về số chiều, và các cột của DataFrame có bắt buộc cùng kiểu dữ liệu không?

**Đáp án:** Series là mảng có nhãn một chiều; DataFrame là cấu trúc có nhãn hai chiều, các cột có thể khác kiểu dữ liệu.

**Nguồn:** trang PDF 346, trang in 336. **Filter:** `{}`.

**Bằng chứng:**

> Series: A Series is a one-dimensional labeled array.
>          ◦ DataFrame: A DataFrame is a two-dimensional labeled data structure that consists of columns and
>            rows. A DataFrame can be thought of as a spreadsheet-like data structure where each column
>            represents a Series. DataFrame is a heterogeneous data structure where each column can have a
>            different data type.

Access for free at openstax.org.

## q13 — dev

Khi truy cập dữ liệu trong DataFrame, loc[] và iloc[] chọn vị trí bằng cách nào?

**Đáp án:** loc[] dùng nhãn dòng/cột; iloc[] dùng chỉ số nguyên.

**Nguồn:** trang PDF 355, trang in 345. **Filter:** `{}`.

**Bằng chứng:**

> Label-based indexing using loc[]: loc[] allows you to access data in a DataFrame using row/column
>     labels. Ex: df.loc[row_label, column_label] returns specific data at the intersection of row_label
>     and column_label.
>  • Integer-based indexing using iloc[]: iloc[] allows you to access data in a DataFrame using integer-based
>     indexes. Integer indexes can be passed to retrieve specific data. Ex: df.iloc[row_index,
>     column_index] returns specific data at the index row_index and column_index.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 369.

## q14 — dev

Biểu thức df[condition] giữ lại những hàng nào trong DataFrame?

**Đáp án:** Chỉ các hàng thỏa mãn điều kiện.

**Nguồn:** trang PDF 356, trang in 346. **Filter:** `{}`.

**Bằng chứng:**

> Slicing based on a condition: df[condition] selects only the rows that meet the given condition.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 369.

## q15 — dev

Mục tiêu chính của phân tích khám phá dữ liệu (EDA) được sách mô tả là gì?

**Đáp án:** Làm quen với dữ liệu và đánh giá chất lượng dữ liệu.

**Nguồn:** trang PDF 354, trang in 344. **Filter:** `{}`.

**Bằng chứng:**

> The
>       main goal of EDA is to become familiar with the data and assess the quality of the data.

Access for free at openstax.org.

## q16 — test

Nếu một ngoại lệ được phát sinh nhưng không được xử lý bằng try và except, chương trình sẽ làm gì?

**Đáp án:** Hiển thị thông báo lỗi và kết thúc.

**Nguồn:** trang PDF 336, trang in 326. **Filter:** `{}`.

**Bằng chứng:**

> If the exception is not handled using try and except, the program displays an error message
>       and terminates.

Access for free at openstax.org.

## q17 — test

Việc phát sinh ngoại lệ trong constructor giúp ngăn điều gì xảy ra?

**Đáp án:** Ngăn tạo một đối tượng không hợp lệ.

**Nguồn:** trang PDF 337, trang in 327. **Filter:** `{}`.

**Bằng chứng:**

> Raising an exception in a constructor prevents an invalid object from being constructed.

Access for free at openstax.org.

## q18 — test

isnull() trả về cấu trúc gì, kích thước thế nào so với DataFrame gốc và True có ý nghĩa gì?

**Đáp án:** Một Boolean DataFrame cùng kích thước với DataFrame gốc; True tại các vị trí có giá trị bị thiếu.

**Nguồn:** trang PDF 357, trang in 347. **Filter:** `{}`.

**Bằng chứng:**

> isnull(): The isnull() function can be used to identify Null entries in a DataFrame. The return value of
>     the function is a Boolean DataFrame, with the same dimensions as the original DataFrame with True
>    values where missing values exist.

Access for free at openstax.org.

## q19 — test

Trong chương 15 — Data Science, hàm nào thay giá trị Null bằng một giá trị thay thế được cung cấp?

**Đáp án:** fillna().

**Nguồn:** trang PDF 357, trang in 347. **Filter:** `{"chapter": 15}`.

**Bằng chứng:**

> fillna(): The fillna() function can be used to replace Null values with a provided substitute value.

Access for free at openstax.org.

## q20 — test

Phần Data visualization tools nêu ba framework Python phổ biến nào để trực quan hóa dữ liệu?

**Đáp án:** Matplotlib, Plotly và Seaborn.

**Nguồn:** trang PDF 361, trang in 351. **Filter:** `{}`.

**Bằng chứng:**

> Some of the most commonly used frameworks are Matplotlib, Plotly, and Seaborn.

Access for free at openstax.org.

Bằng chứng thay thế được lưu trong JSONL, tại trang PDF 368.

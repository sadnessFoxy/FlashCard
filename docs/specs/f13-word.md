# Đặc tả tính năng: F13. Hỗ trợ tài liệu Word (.docx)

- **Trạng thái:** Xong (2026-11-14). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U5 (tải tài liệu lên)

## 1. Mục tiêu
Người học tải được file Word (.docx) như PDF: cùng giới hạn (20 MB, 200 trang, 10 tài liệu), cùng xử lý nền, và mọi tính năng dùng nội dung tài liệu (hỏi đáp, xem trang, tạo thẻ, trắc nghiệm, tóm tắt) chạy giống hệt.

## 2. Luồng
1. Nút tải lên cho chọn file PDF hoặc Word.
2. Backend nhận diện định dạng **theo nội dung file** (không theo tên): PDF, hoặc zip chứa `word/document.xml`.
3. File khác (kể cả `.doc` đời cũ): `FILE_TYPE_NOT_SUPPORTED` với thông báo "Chỉ hỗ trợ file PDF hoặc Word (.docx)".
4. Phần còn lại như F5.

## 4. API
- `POST /v1/documents`: nhận PDF hoặc .docx.
- `Document` thêm `file_kind` (`pdf`, `docx`).

## 5. Dữ liệu (migration mới)
`documents.file_kind` (mặc định `pdf`, các tài liệu cũ là PDF).

## 6. Quy tắc
- **Trang của file Word:** theo các dấu ngắt trang Word lưu trong file (ngắt trang thủ công và vị trí ngắt trang Word ghi lại khi lưu). File không có dấu ngắt nào: cứ khoảng 3.000 ký tự là một trang (`DOCX_CHARS_PER_PAGE`), không cắt giữa đoạn văn.
- **Đọc file:** chỉ dùng thư viện chuẩn của Python (zip và XML), không thêm phụ thuộc.
- **An toàn với file không đáng tin:** từ chối XML có khai báo DTD hoặc ENTITY (chống mở rộng thực thể); giới hạn kích thước phần nội dung sau giải nén 50 MB (`DOCX_MAX_BODY_BYTES`, chống zip bomb).
- Mọi chỗ đọc nội dung tài liệu đi qua một lớp chung `documents/formats.py` (tải lên, xử lý nền, xem trang, tóm tắt), nên thêm định dạng sau này chỉ sửa ở một chỗ.
- File được lưu với đúng loại nội dung (content type) của Word.

## 9. Tiêu chí nghiệm thu
1. Tải .docx: 202, `file_kind = docx`, số trang đúng.
2. Xử lý nền: `READY`, các đoạn mang đúng số trang.
3. Nhận diện theo nội dung; file giả zip hoặc văn bản thường bị từ chối.
4. XML có ENTITY bị từ chối; phần nội dung quá lớn bị từ chối.
5. Trang theo dấu ngắt; không có dấu ngắt thì theo độ dài.
6. Xem một trang của file Word (màn hình trích dẫn) trả đúng văn bản.
7. Giao diện: chọn được file Word; thông báo lỗi nhắc cả PDF và Word.
8. Thử thật: file Word tiếng Việt lên `READY`, tìm đúng chương, tóm tắt bằng Gemini đúng trang.

## 12. Lựa chọn đã tự chốt
- **Đổi quyết định cũ** "đếm trang Word sau khi chuyển sang PDF": việc đó cần LibreOffice (thư viện lớn, chưa cài, phải đưa vào image worker). Thay bằng dấu ngắt trang Word lưu sẵn, hoặc 3.000 ký tự mỗi trang. Số trang có thể lệch đôi chút so với khi in. Nếu cần khớp tuyệt đối thì thêm LibreOffice sau.
- Chưa hỗ trợ `.doc` đời cũ, chữ trong hình, hộp văn bản, chú thích cuối trang.

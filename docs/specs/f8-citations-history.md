# Đặc tả tính năng: F8. Xem trích dẫn và lịch sử hội thoại

- **Trạng thái:** Xong (2026-11-13). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U7; màn hình 10 (Xem trích dẫn), 11 (Lịch sử hội thoại)

## 1. Mục tiêu
Từ một trích dẫn trong câu trả lời, người học mở đúng trang tài liệu và thấy đoạn liên quan được đánh dấu. Người học xem lại danh sách hội thoại của một Không gian, mở lại hoặc xóa hội thoại.

## 2. Luồng
1. Trong câu trả lời, bấm chip trích dẫn: hộp thoại hiện đoạn trích, kèm nút **Xem trang**.
2. Bấm **Xem trang**: mở màn hình trang tài liệu (tên tài liệu, "Trang n/N"), nội dung trang chia theo đoạn văn; đoạn trùng với đoạn trích được tô nổi bật. Có nút trang trước, trang sau.
3. Tài liệu đã xóa: chip vẫn mở được đoạn trích, ghi "tài liệu đã xóa", không có nút **Xem trang**.
4. Tab Hỏi đáp có nút **Lịch sử**: mở danh sách hội thoại của Không gian (mới nhất trước, tiêu đề là câu hỏi đầu, thời điểm cập nhật).
5. Bấm một hội thoại: quay lại tab Hỏi đáp với hội thoại đó.
6. Xóa hội thoại: hỏi xác nhận, xóa luôn các tin nhắn bên trong.

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/documents/{id}/pages/{page}` | GET | `{document_id, filename, page, page_count, paragraphs[]}`. 404 nếu không phải tài liệu của mình hoặc trang ngoài phạm vi; 409 `DOCUMENT_NOT_READY` nếu tài liệu chưa `READY` |
| `/v1/conversations?space_id=&limit=` | GET | Thêm `limit` (1 đến 50, mặc định 20) |
| `/v1/conversations/{id}` | DELETE | 204; hội thoại của người khác trả 404 |

## 6. Quy tắc
- Nội dung trang đọc lại từ file PDF đã lưu, nên đúng với trang thật. Văn bản đã trích được giữ trong Redis 1 giờ (`DOCUMENT_PAGE_CACHE_SECONDS`), khóa gồm người dùng và tài liệu (R4). Redis lỗi thì đọc thẳng từ file.
- Đánh dấu đoạn: phía app so khớp sau khi chuẩn hóa khoảng trắng; một đoạn văn được tô nếu nó nằm trong đoạn trích, hoặc đoạn trích bắt đầu bên trong nó.
- Tài liệu là dữ liệu không đáng tin (R7): chỉ hiển thị dạng chữ thường, không diễn giải định dạng.

## 7. Quyền và bảo mật
Mọi truy vấn lọc theo chủ sở hữu; khóa cache có ID người dùng. Xóa hội thoại chỉ xóa của chính mình.

## 9. Tiêu chí nghiệm thu
1. Mở trang được trích: trả đúng văn bản của trang đó, chia đoạn.
2. Mở lại cùng trang: không tải lại file PDF (cache).
3. Trang ngoài phạm vi, tài liệu của người khác: 404; tài liệu chưa `READY`: 409.
4. Danh sách hội thoại mới nhất trước, `limit` hoạt động; xóa thì không mở lại được.
5. Không xóa được hội thoại của người khác.
6. Giao diện: nút Xem trang, đánh dấu đoạn, chuyển trang, danh sách lịch sử, mở lại, xóa có xác nhận, trạng thái rỗng, song ngữ.

## 12. Lựa chọn đã tự chốt
- Xem trang dạng văn bản (không nhúng trình xem PDF): chạy được trên Expo Go và web mà không thêm thư viện gốc. Nhúng trình xem PDF thật để sau nếu cần.
- Không đổi tên hội thoại ở bản này (tiêu đề tự lấy từ câu hỏi đầu).

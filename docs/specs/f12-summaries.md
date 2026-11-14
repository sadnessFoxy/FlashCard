# Đặc tả tính năng: F12. Tóm tắt theo chương

- **Trạng thái:** Xong (2026-11-14). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U15; màn hình 8 (Tóm tắt theo chương)

## 1. Mục tiêu
Người học mở một tài liệu `READY`, xem danh sách chương và yêu cầu tóm tắt từng chương. Mỗi ý tóm tắt kèm trang nguồn; tóm tắt được lưu để xem lại không tốn lượt AI.

## 2. Luồng
1. Trang chi tiết tài liệu `READY` có các lối tắt: **Tóm tắt theo chương**, **Tạo thẻ bằng AI**, **Tạo trắc nghiệm**.
2. Màn hình Tóm tắt: tên tài liệu, số lượt tóm tắt còn lại hôm nay, danh sách chương (tiêu đề và khoảng trang).
3. Chương đã có tóm tắt: hiện các ý, mỗi ý có liên kết "trang n" mở trang tài liệu (F8).
4. Chương chưa có: nút **Tạo tóm tắt**; hết lượt hoặc AI tạm nghỉ thì báo rõ, tóm tắt đã có vẫn xem được.

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/documents/{id}/sections` | GET | `{document_id, filename, items: [{id, position, title, page_start, page_end, summary}]}` |
| `/v1/documents/{id}/sections/{section_id}/summary` | POST | 201 khi vừa tạo (trừ lượt); 200 khi đã có (không trừ lượt) |
| `/v1/usage/me` | GET | Thêm bộ đếm `summaries` |

Lỗi: `DOCUMENT_NOT_READY` (409), `SOURCE_EMPTY` (422), `USER_QUOTA_EXCEEDED` (429), `AI_TEMPORARILY_UNAVAILABLE` (503).

## 5. Dữ liệu (migration mới)
| Bảng | Cột chính |
|---|---|
| `document_sections` | `document_id` (xóa tài liệu thì xóa theo), `owner_id`, `position`, `title` (rỗng nếu là khoảng trang), `page_start`, `page_end` |
| `document_summaries` | `section_id` (duy nhất), `owner_id`, `points` (`[{text, page}]`), `model` |

## 6. Quy tắc
- **Chia chương (U15 bước 2):** lần đầu mở, đọc lại file PDF, tìm tiêu đề bằng đúng bộ nhận diện dùng khi chia đoạn (Chương, Bài, Phần, Mục, Chapter, Section, Part, Lesson). Phần trước tiêu đề đầu tiên (lời nói đầu, mục lục) thành một phần riêng. Không có tiêu đề, hoặc nhiều hơn 40 tiêu đề, thì chia theo khoảng 10 trang. Kết quả lưu lại, không tìm lại.
- **Tóm tắt theo yêu cầu**, không tạo hàng loạt (DECISIONS). Hạn mức 10 lần mỗi ngày (`SUMMARY_DAILY_LIMIT`), tính riêng; AI lỗi hoặc kết quả hỏng thì hoàn lượt.
- **Nguồn:** đoạn văn trong khoảng trang của chương, tối đa 20.000 ký tự (bộ nạp nguồn dùng chung với F9, F11).
- **Prompt:** chỉ dẫn tiếng Anh; 3 đến 8 ý chính theo thứ tự đọc, mỗi ý từ một nguồn; không nhắc số thứ tự nguồn; nguồn là dữ liệu không đáng tin (R7); viết bằng ngôn ngữ của tài liệu.
- **Kiểm tra kết quả AI:** bỏ ý rỗng, tối đa 10 ý, cắt 500 ký tự; số nguồn sai thì ý không có trang.

## 7. Quyền và bảo mật
Chỉ tài liệu của chính người dùng; tài liệu của người khác hoặc chương không thuộc tài liệu trả 404.

## 9. Tiêu chí nghiệm thu
1. Chương lấy từ tiêu đề, chỉ tìm một lần (tải file một lần).
2. Tóm tắt chỉ dùng văn bản của chương; lưu lại; gọi lại trả 200, không gọi AI, không trừ lượt.
3. Tài liệu của người khác, chương lạ: 404; tài liệu chưa `READY`: 409.
4. AI lỗi hoặc kết quả hỏng: 503, hoàn lượt; hết lượt: 429 nhưng tóm tắt đã có vẫn xem được.
5. Không có tiêu đề: chia theo khoảng trang.
6. Unit test: tìm chương (phần mở đầu, hai tiêu đề cùng trang, quá nhiều tiêu đề), đọc kết quả AI.
7. Giao diện: lối tắt ở chi tiết tài liệu, danh sách chương, tạo tóm tắt, liên kết trang, báo hết lượt, song ngữ.
8. Thử thật với Gemini trên giáo trình mẫu.

## 12. Lựa chọn đã tự chốt
- Chia chương bằng tiêu đề trong văn bản (chưa đọc mục lục PDF); chương kết thúc ở trang trước chương sau.
- Khoảng 10 trang mỗi phần khi không có tiêu đề.
- 10 lượt tóm tắt mỗi ngày.
- Tóm tắt lưu theo chương; xóa tài liệu thì xóa luôn tóm tắt.

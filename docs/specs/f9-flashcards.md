# Đặc tả tính năng: F9. Flashcard

- **Trạng thái:** Xong (2026-11-13). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U11; màn hình 12 (Bộ thẻ), 13 (Tạo thẻ), 14 (Chi tiết bộ thẻ). Ôn tập (màn hình 15, 16) làm ở F10

## 1. Mục tiêu
Người học gom thẻ thành bộ trong một Không gian. Thẻ được tạo bằng tay, hoặc do AI **đề xuất** từ tài liệu (cả tài liệu hoặc một khoảng trang) hay từ một câu trả lời hỏi đáp. AI không tự lưu thẻ: người học xem, sửa, bỏ chọn rồi mới lưu. Mỗi thẻ ghi nguồn (tài liệu, trang) để quay lại đọc.

## 2. Luồng
1. Tab **Thẻ** của Không gian: danh sách bộ thẻ, số thẻ và số thẻ cần ôn; nút **Bộ thẻ mới**.
2. Chi tiết bộ thẻ: danh sách thẻ (mặt trước, mặt sau, nguồn), thêm thẻ bằng tay, sửa, xóa có xác nhận, đổi tên, xóa bộ; bấm nguồn để mở trang được trích (F8).
3. **Tạo thẻ bằng AI**: chọn tài liệu `READY`, khoảng trang (không bắt buộc), số thẻ tối đa (5, 10, 20) rồi bấm **Đề xuất thẻ**. Danh sách đề xuất hiện ra; mỗi thẻ sửa được và có nút Giữ hoặc Bỏ qua; bấm **Lưu x thẻ**.
4. Từ câu trả lời hỏi đáp: nút **Tạo thẻ** dưới câu trả lời hoàn chỉnh; nguồn là câu trả lời và các đoạn nó trích; người học chọn bộ thẻ có sẵn hoặc đặt tên bộ mới khi lưu.
5. Hết lượt tạo thẻ hoặc AI tạm nghỉ: báo rõ, vẫn thêm thẻ bằng tay được.

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/decks?space_id=` | GET | Bộ thẻ kèm `card_count`, `due_count` |
| `/v1/decks` | POST `{space_id, name}` | 201 |
| `/v1/decks/{id}` | GET, PATCH `{name}`, DELETE | Chi tiết kèm thẻ; xóa bộ xóa luôn thẻ |
| `/v1/flashcards` | POST `{deck_id, cards[]}` | Lưu 1 đến 50 thẻ; `origin` là `ai` hoặc `manual`; `source {document_id, page}` |
| `/v1/flashcards/{id}` | PATCH `{front?, back?}`, DELETE | |
| `/v1/flashcards/suggestions` | POST `{space_id, source, count}` | `source` là `{type: "document", document_id, page_start?, page_end?}` hoặc `{type: "message", message_id}`; trả danh sách đề xuất, **không lưu** |
| `/v1/usage/me` | GET | Thêm `card_suggestions` (hạn mức tạo thẻ riêng) |

Lỗi: `DECK_FULL` (409, `max_cards`), `SOURCE_EMPTY` (422), `DOCUMENT_NOT_READY` (409), `USER_QUOTA_EXCEEDED` (429), `AI_TEMPORARILY_UNAVAILABLE` (503).

## 5. Dữ liệu (migration mới)
| Bảng | Cột chính |
|---|---|
| `flashcard_decks` | `owner_id`, `space_id` (xóa Không gian thì xóa bộ), `name` |
| `flashcards` | `deck_id`, `owner_id`, `position` (thứ tự trong bộ), `front`, `back`, `origin`, nguồn dạng bản ghi nhanh (`source_document_id` đặt rỗng khi tài liệu bị xóa, `source_document_name`, `source_page`), cột lịch SM-2 cho F10 (`ease_factor` 2,5, `interval_days`, `repetitions`, `due_at`) |

## 6. Quy tắc
- **Hạn mức:** 10 lần đề xuất mỗi ngày (`CARD_SUGGESTION_DAILY_LIMIT`), tính riêng với hỏi đáp, theo giờ Việt Nam. Lỗi AI hoặc kết quả không dùng được thì hoàn lại lượt.
- **Nguồn đưa cho AI:** đoạn của tài liệu theo thứ tự đọc, tối đa 12.000 ký tự (`CARD_SUGGESTION_SOURCE_CHARS`); hoặc các đoạn được trích trong câu trả lời, kèm chính câu trả lời làm trọng tâm.
- **Prompt:** chỉ dẫn tiếng Anh; nguồn bọc trong `<source>` và là dữ liệu không đáng tin (R7); AI trả JSON `{"cards": [{"front", "back", "source"}]}`; viết bằng ngôn ngữ của tài liệu (backend nhận diện tiếng Việt hay tiếng Anh). Không đưa thông tin người dùng vào prompt (R10).
- **Kiểm tra kết quả AI:** bỏ thẻ thiếu mặt, trùng mặt trước, cắt độ dài (mặt trước 200, mặt sau 600 ký tự); số nguồn sai thì thẻ không có nguồn.
- **Khi lưu:** nguồn phải là tài liệu của chính người dùng, không thì bỏ nguồn (không báo lỗi, không lộ tài liệu người khác); trang vượt số trang thì bỏ trang. Tối đa 1.000 thẻ mỗi bộ.

## 7. Quyền và bảo mật
Mọi truy vấn lọc theo chủ sở hữu; bộ thẻ, thẻ, tin nhắn của người khác trả 404. Câu trả lời dùng làm nguồn phải thuộc hội thoại trong đúng Không gian.

## 9. Tiêu chí nghiệm thu
1. Tạo, đổi tên, xóa bộ thẻ; đếm thẻ và thẻ cần ôn đúng.
2. Thêm, sửa, xóa thẻ; nguồn là bản ghi nhanh, tài liệu bị xóa thì `document_id = null`.
3. Bộ thẻ, thẻ của người khác: 404.
4. `DECK_FULL`, dữ liệu sai: 422.
5. Đề xuất theo khoảng trang: chỉ văn bản các trang đó vào prompt; không lưu gì; trừ 1 lượt tạo thẻ, không trừ lượt hỏi đáp.
6. Đề xuất từ câu trả lời dùng các đoạn được trích.
7. AI lỗi hoặc trả kết quả hỏng: 503 và hoàn lượt.
8. Hết lượt: 429, không gọi AI.
9. Tài liệu chưa `READY`, ngoài Không gian, khoảng trang rỗng: 409, 404, `SOURCE_EMPTY`.
10. Giao diện: tab Thẻ, chi tiết bộ, màn hình tạo thẻ (sửa, bỏ chọn, chọn bộ), nút Tạo thẻ trong hỏi đáp, thông báo hết lượt, song ngữ.
11. Thử thật với Gemini trên giáo trình mẫu: thẻ đúng nội dung và đúng trang.

## 12. Lựa chọn đã tự chốt
- Mã nguồn đặt trong module `study` (theo docs/ARCHITECTURE.md), chia gói con `study/flashcards/`; F10, F11 thêm `study/reviews/`, `study/quizzes/`.
- Hạn mức đề xuất thẻ: 10 lần mỗi ngày, mỗi lần tối đa 20 thẻ.
- Chương được chọn bằng khoảng trang (chưa có danh sách chương tự động).
- Thẻ mới đến hạn ôn ngay; lịch SM-2 làm ở F10.

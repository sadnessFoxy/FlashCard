# Mô hình dữ liệu và trạng thái tài liệu

> **Khi nào đọc:** khi viết migration, model, repository, worker xử lý tài liệu, hoặc bất kỳ chỗ nào đổi trạng thái tài liệu.

## Thiết kế dữ liệu (PostgreSQL + pgvector)

File gốc (PDF, ảnh) lưu ở object storage tương thích S3; PostgreSQL lưu metadata, trạng thái, nội dung đoạn và vector.

| Bảng | Dữ liệu chính | Mục đích |
|---|---|---|
| `users` | ID, email, password hash, thời điểm tạo | Danh tính người dùng |
| `documents` | Owner, tên file, storage key, trạng thái | Quản lý tài liệu |
| `document_chunks` | Document ID, nội dung, số trang, embedding | Tìm đoạn liên quan và trích dẫn |
| `document_jobs` | Loại job, trạng thái, số lần thử, lỗi | Theo dõi và phục hồi tác vụ nền |
| `conversations` | Owner, tiêu đề, thời điểm tạo | Gom nhóm hội thoại |
| `messages` | Conversation ID, role, nội dung, citations | Lịch sử hỏi đáp |
| `flashcards` | Mặt trước, mặt sau, nguồn tạo | Quản lý thẻ học |
| `review_logs` | Thời điểm ôn, kết quả, đánh giá | Theo dõi tiến độ ôn tập |
| `ai_usage` | Model, token, thời gian, chi phí ước tính | Kiểm soát ngân sách AI |

Quan hệ chính:
- `users` có nhiều `documents`; mỗi `documents` có nhiều `document_chunks` và `document_jobs`
- `users` có nhiều `conversations`; mỗi `conversations` có nhiều `messages`
- `users` có nhiều `flashcards`; mỗi `flashcards` có nhiều `review_logs`
- `users` có nhiều bản ghi `ai_usage`

Quy tắc thiết kế:
- **Khóa ngoại:** `documents.owner_id` → `users.id`; `document_chunks.document_id` → `documents.id`; `messages.conversation_id` → `conversations.id`; `review_logs.flashcard_id` → `flashcards.id`.
- **Index nên có:** unique cho email đã chuẩn hóa; `documents(owner_id, created_at)`; `document_chunks(document_id)`; `messages(conversation_id, created_at)`; vector index phù hợp cách truy xuất đã chọn. Không thêm index máy móc cho mọi cột, kiểm tra theo truy vấn thực tế.
- **Embedding:** số chiều cố định theo mô hình. Lưu tên và số chiều mô hình cùng dữ liệu; đổi mô hình nghĩa là tạo lại toàn bộ vector, cần có kế hoạch chuyển đổi.
- **Migration:** dùng Alembic, không sửa schema production thủ công; thay đổi ưu tiên tương thích ngược, thử trên staging trước.
- **Xóa dữ liệu:** khi người dùng xóa tài liệu, phải xử lý file gốc, chunk, vector và job đang chờ. Nếu xóa bất đồng bộ thì dùng trạng thái `DELETING` để tài liệu đó không còn xuất hiện trong tìm kiếm.

## Máy trạng thái của tài liệu

| Trạng thái | Ý nghĩa | Chuyển được sang |
|---|---|---|
| `UPLOADED` | File đã lưu, chưa vào hàng đợi | `QUEUED` |
| `QUEUED` | Đang chờ worker | `PROCESSING`, `DELETING` |
| `PROCESSING` | Đang trích văn bản, chia đoạn, tạo embedding | `READY`, `FAILED`, `PAUSED_QUOTA`, `QUEUED` (lỗi tạm thời, chờ lần thử sau; thêm ở F5), `DELETING` |
| `READY` | Sẵn sàng hỏi đáp | `DELETING` |
| `FAILED` | Lỗi sau số lần thử cho phép | `QUEUED` (thử lại), `DELETING` |
| `PAUSED_QUOTA` | Tạm dừng vì AI hết hạn mức, chờ phục hồi | `QUEUED` (tự động khi hạn mức phục hồi), `DELETING` |
| `DELETING` | Đang dọn dữ liệu | Xóa hẳn |

Quy tắc:
- API upload trả về `document_id` và trạng thái ban đầu ngay, không chờ xử lý xong.
- Chỉ cho phép các chuyển trạng thái ở bảng trên; cập nhật có điều kiện theo trạng thái hiện tại để **job cũ không ghi đè trạng thái mới**.
- Chỉ tài liệu `READY` mới được đưa vào tìm kiếm; worker kiểm tra lại trạng thái trước các thao tác nhạy cảm, đặc biệt khi tài liệu đã bị xóa.
- Lỗi và số lần thử ghi vào `document_jobs`; thử lại có giới hạn và không tạo dữ liệu trùng.
- `PAUSED_QUOTA` không tính vào số lần thử và không chuyển sang `FAILED`; job tự chạy lại khi hạn mức phục hồi (xem docs/QUOTA_AND_RESILIENCE.md).

## Bảng và cột bổ sung cho xác thực, quản trị và đồng ý (đề xuất)

Cần cho các luồng U1 đến U4, U5 và nhóm A trong docs/BUSINESS_FLOWS.md. Đây là đề xuất thiết kế, agent có thể điều chỉnh khi viết đặc tả nhưng phải nêu lý do.

| Bảng | Dữ liệu chính | Mục đích |
|---|---|---|
| `auth_identities` | User ID, nhà cung cấp (email, google), mã định danh từ nhà cung cấp, email do nhà cung cấp trả về, đã xác minh hay chưa | Một người dùng có nhiều cách đăng nhập |
| `refresh_tokens` | User ID, mã băm token, hạn dùng, thời điểm thu hồi, thông tin thiết bị | Xoay vòng và thu hồi phiên |
| `email_tokens` | User ID, loại (xác minh, đặt lại mật khẩu), mã băm, hạn, đã dùng chưa | Token một lần |
| `user_consents` | User ID, loại đồng ý (gửi dữ liệu cho nhà cung cấp AI), phiên bản văn bản, thời điểm | Chứng minh đã thông báo và được đồng ý |
| `user_quota_overrides` | User ID, hạn mức riêng, thời hạn, người đặt | Ngoại lệ do quản trị viên đặt |
| `app_settings` | Khóa, giá trị, người sửa, thời điểm | Cấu hình đổi được không cần triển khai (hạn mức, giới hạn tải lên, công tắc AI) |
| `flashcard_decks` | Owner, tên, tài liệu nguồn (nếu có) | Gom thẻ thành bộ |
| `document_summaries` | Tài liệu, chương hoặc khoảng trang, nội dung tóm tắt, trang nguồn, mô hình, thời điểm | Lưu tóm tắt để không tính lại |
| `quizzes` | Owner, tài liệu nguồn, số câu, thời điểm | Bộ câu hỏi trắc nghiệm |
| `quiz_questions` | Quiz ID, nội dung câu hỏi, các đáp án, đáp án đúng, trích dẫn nguồn | Câu hỏi và đáp án đúng lưu cùng lúc khi sinh |
| `quiz_attempts` | Quiz ID, User ID, câu trả lời, điểm, thời điểm | Kết quả làm bài, điểm do code chấm |
| `audit_logs` | Người thực hiện, hành động, đối tượng, giá trị cũ và mới, thời điểm | Nhật ký kiểm toán, chỉ thêm |

Cột bổ sung cho `flashcards` (lập lịch SM-2): `deck_id`, `ease_factor`, `interval_days`, `repetitions`, `due_at`.

Cột bổ sung cho `users`: `role` (user, admin), `status` (active, blocked), `locale` (vi, en), `email_verified_at`, `deleted_at`.

Quy tắc:
- Token (refresh, xác minh email, đặt lại mật khẩu) **chỉ lưu dạng băm**, không lưu thô.
- `document_chunks.embedding` là vector 768 chiều; lưu tên mô hình embedding cùng dữ liệu.
- **Trích dẫn khi xóa tài liệu:** mỗi trích dẫn trong `messages` lưu bản ghi nhanh (tên tài liệu, số trang) và `document_id` cho phép rỗng. Khi tài liệu bị xóa, lịch sử hội thoại vẫn còn và giao diện hiện "tài liệu đã xóa".
- `audit_logs` không có thao tác sửa hay xóa qua ứng dụng.
- Xóa tài khoản: xóa dữ liệu theo docs/BUSINESS_FLOWS.md (U9); bản sao lưu giữ tối đa 30 ngày.

## Không gian (spaces)

| Bảng | Dữ liệu chính | Mục đích |
|---|---|---|
| `spaces` | ID, owner_id, tên, thời điểm tạo, thời điểm cập nhật | Gom tài liệu và học liệu theo môn hoặc chủ đề |

Thêm cột `space_id` (bắt buộc, khóa ngoại tới `spaces.id`) vào `documents`, `conversations`, `flashcard_decks`, `quizzes`, `document_summaries`.

Quy tắc:
- Mỗi tài liệu thuộc đúng một không gian; chuyển không gian là đổi `space_id` của tài liệu (chunk đi theo tài liệu).
- Truy xuất vector lọc theo `space_id` và `owner_id`; chỉ tài liệu `READY`.
- Xóa không gian: dọn tài liệu theo quy trình xóa tài liệu (trạng thái `DELETING`), rồi hội thoại, bộ thẻ, trắc nghiệm.
- Index nên có: `spaces(owner_id)`, `documents(space_id)`.

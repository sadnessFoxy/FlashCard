# Đặc tả tính năng: F16. Giao diện quản trị web

- **Trạng thái:** Xong (2026-11-16). Tự chốt theo quyền người dùng cấp; phần hoãn ghi ở mục 12
- **Luồng:** A1 đến A7; màn hình 20 đến 25

## 1. Mục tiêu
Quản trị viên theo dõi hệ thống, xử lý người dùng và tài liệu lỗi, chỉnh hạn mức và tắt khẩn cấp AI mà không cần triển khai lại; mọi thao tác được ghi nhật ký. Quản trị viên **không xem được nội dung tài liệu và hội thoại** (R13).

## 2. Luồng
1. **Cấp quyền (A1):** không có đăng ký quản trị công khai. Người vận hành chạy `make create-admin email=...` cho một tài khoản đã đăng ký.
2. Quản trị viên đăng nhập như thường, vào Hồ sơ → **Trang quản trị** (chỉ hiện trên web), hoặc mở thẳng `/admin`. Trên điện thoại báo "chỉ dùng trên web"; tài khoản thường thấy "không có quyền".
3. **Tổng quan (A2, màn hình 20):** người dùng, người hoạt động hôm nay, câu hỏi, lượt gọi AI, lượt lỗi, token hôm nay, phần trăm ngân sách token (nếu đặt), AI bật hay tắt, trạng thái cầu dao, số job đang chờ, tài liệu theo trạng thái. Ô có vấn đề tô đỏ.
4. **Người dùng (A3, màn hình 21, 22):** tìm theo email; xem cách đăng nhập, trạng thái, xác minh email, số tài liệu, câu hỏi hôm nay. Khóa (bắt buộc lý do, thu hồi phiên ngay), mở khóa, buộc đăng xuất, hạn mức hỏi đáp riêng (có thể có thời hạn), xóa tài khoản theo yêu cầu (bắt buộc lý do, chạy quy trình U9).
5. **Tài liệu và job (A4, màn hình 23):** lọc theo trạng thái, xem mã lỗi và số lần thử, thử lại tài liệu `FAILED` hoặc `PAUSED_QUOTA`.
6. **Cấu hình (A5, màn hình 24):** câu hỏi mỗi người mỗi ngày, dung lượng tối đa, số trang tối đa, số tài liệu mỗi người, ngân sách token mỗi ngày, công tắc khẩn cấp tắt AI; hiện giá trị cũ → mới trước khi lưu.
7. **Nhật ký (A7, màn hình 25):** mọi thao tác ghi: ai, làm gì, trên đối tượng nào, lúc nào, giá trị cũ và mới, lý do; lọc theo hành động; chỉ xem.

## 4. API (tiền tố `/v1/admin`, mọi endpoint kiểm tra vai trò ở backend)
| Endpoint | Mô tả |
|---|---|
| `GET /overview` | Tổng quan |
| `GET /users?q=&limit=&offset=`, `GET /users/{id}` | Danh sách, chi tiết |
| `POST /users/{id}/block {reason}`, `/unblock`, `/sign-out` | Khóa, mở khóa, buộc đăng xuất |
| `PUT /users/{id}/quota {daily_limit, expires_at}` | Hạn mức riêng (`daily_limit: null` để gỡ) |
| `POST /users/{id}/deletion {reason}` | Xóa tài khoản theo yêu cầu |
| `GET /documents?status=`, `POST /documents/{id}/retry` | Tài liệu và job |
| `GET /settings`, `PATCH /settings {values}` | Cấu hình chạy |
| `GET /audit?action=&actor_id=` | Nhật ký |

Lỗi: `FORBIDDEN` (403, không phải quản trị viên), `CANNOT_TARGET_SELF` (409: không tự khóa, tự đăng xuất, tự xóa), `DOCUMENT_NOT_RETRYABLE` (409), `VALIDATION_ERROR` (422, cấu hình sai).

## 5. Dữ liệu (migration mới)
`admin_audit_logs` (chỉ thêm), `app_settings` (khóa, giá trị), `user_quota_overrides` (người dùng, hạn mức, hết hạn).

## 6. Quy tắc
- **Cấu hình chạy:** lưu trong database; khóa chưa đổi dùng giá trị trong `.env`. Mỗi tiến trình (API, worker) đọc lại sau tối đa 15 giây. Giá trị được kiểm tra kiểu và khoảng.
- **Công tắc tắt AI:** đặt trong cổng gọi AI (R5); khi tắt, mọi lời gọi AI báo lỗi ngay như cầu dao mở, nên các tính năng tự suy giảm: hỏi đáp chỉ tìm đoạn, tài liệu mới chờ `PAUSED_QUOTA`, tạo thẻ, trắc nghiệm, tóm tắt báo AI tạm nghỉ.
- **Hạn mức hỏi đáp:** hạn mức riêng còn hiệu lực > mặc định chạy > `.env`.
- **Nhật ký:** ghi trong cùng giao dịch với thay đổi, nên không có thay đổi nào thiếu nhật ký; giữ lại cả khi tài khoản quản trị bị xóa (lưu email người làm).
- **Quyền riêng tư (R13):** API chỉ trả siêu dữ liệu (email, tên file, trạng thái, số đếm); không có endpoint đọc nội dung tài liệu hay hội thoại.

## 9. Tiêu chí nghiệm thu
1. Tài khoản thường: 403 `FORBIDDEN` ở mọi endpoint quản trị; chưa đăng nhập: 401.
2. Tổng quan đếm đúng người dùng, người hoạt động, tài liệu theo trạng thái, câu hỏi, lượt gọi, lượt lỗi, token.
3. Danh sách, tìm kiếm người dùng; không có trường nội dung.
4. Khóa: người dùng bị thu hồi phiên, `/me` trả `ACCOUNT_BLOCKED`; nhật ký có lý do, giá trị cũ, giá trị mới; không tự khóa được.
5. Hạn mức riêng áp dụng ngay, hết hạn thì về mặc định, gỡ được.
6. Buộc đăng xuất; xóa theo yêu cầu: dữ liệu và file bị dọn, nhật ký còn.
7. Lọc tài liệu theo trạng thái, thử lại tài liệu lỗi, tài liệu `READY` không thử lại được.
8. Cấu hình: giá trị sai bị từ chối; tắt AI làm hỏi đáp chuyển chỉ tìm đoạn; đổi hạn mức và số trang tối đa áp dụng ngay; nhật ký có giá trị cũ và mới.
9. Giao diện: chặn điện thoại và tài khoản thường, tổng quan tô đỏ chỗ có vấn đề, khóa cần lý do, báo lỗi tự thao tác lên mình, cấu hình hiện cũ → mới, thử lại, nhật ký, song ngữ.
10. Thử thật qua HTTP: đủ các bước trên với tài khoản thử, rồi dọn sạch.

## 12. Lựa chọn đã tự chốt và phần hoãn
- Giao diện quản trị ở đường dẫn `/admin` trong cùng app (chỉ web).
- Quản trị viên không xem nội dung người dùng (R13, áp dụng như đề xuất).
- **Hoãn xác thực hai bước** cho quản trị viên (DECISIONS cho phép hoãn khi chỉ chạy thử). Cần làm trước khi đưa lên mạng.
- **Hoãn cảnh báo tự động (A6)** qua email khi ngân sách chạm 50/80/100%, cầu dao mở, hàng đợi nghẽn; hiện tại tổng quan tô đỏ các chỉ số này.
- **Chưa có chỉ số thời gian phản hồi (p95)**: cần hạ tầng đo (Prometheus) ở giai đoạn 5.
- Trạng thái cầu dao trên tổng quan là của tiến trình API đang trả lời (mỗi tiến trình có cầu dao riêng).

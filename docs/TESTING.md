# Chiến lược kiểm thử

> **Khi nào đọc:** trước khi viết hoặc sửa test, và khi quyết định một việc đã "xong" hay chưa.

## Chiến lược kiểm thử

| Loại | Mục tiêu | Công cụ |
|---|---|---|
| Unit | Hàm hoặc thành phần riêng lẻ | pytest, Jest, React Native Testing Library |
| Integration | API, database, storage, worker khi kết hợp | pytest, HTTPX, Postgres thử nghiệm, Docker |
| E2E | Luồng người dùng từ đầu đến cuối | Maestro hoặc Detox |
| AI evaluation | Chất lượng truy xuất, độ đúng nguồn, chất lượng câu trả lời | Bộ dữ liệu trong `evals/`, pytest |

Bảng kịch bản bắt buộc:

| Tình huống | Kết quả mong đợi |
|---|---|
| Đăng nhập sai mật khẩu | Từ chối, không tiết lộ thông tin nhạy cảm |
| Người A truy cập `document_id` của người B | Bị từ chối, không trả về nội dung |
| Tải lên file sai định dạng | Bị từ chối trước khi xử lý |
| Worker lỗi giữa chừng | Có trạng thái lỗi, thử lại theo chính sách, không tạo dữ liệu trùng |
| Tài liệu không chứa câu trả lời | AI nói không tìm thấy căn cứ phù hợp |
| Streaming bị ngắt | App thể hiện lỗi hoặc trạng thái chưa hoàn tất |
| Người dùng xóa tài liệu | File, dữ liệu tìm kiếm và quyền truy cập được xử lý theo chính sách |
| Chạy migration database | Chạy được trên môi trường test, không mất dữ liệu ngoài dự kiến |
| Nhà cung cấp AI trả lỗi hết hạn mức | Circuit breaker mở; job chuyển `PAUSED_QUOTA` (không `FAILED`); hỏi đáp chuyển chế độ chỉ tìm đoạn; app nhận `AI_TEMPORARILY_UNAVAILABLE` |
| Nhà cung cấp AI trả lỗi giới hạn tốc độ tạm thời | Thử lại có giới hạn với thời gian chờ tăng dần, không tạo dữ liệu trùng |
| Người dùng vượt hạn mức ngày | Từ chối ngay với `USER_QUOTA_EXCEEDED` kèm thời điểm đặt lại, không gọi AI |
| Hạn mức hệ thống phục hồi | Circuit breaker đóng lại; job `PAUSED_QUOTA` tự chạy tiếp từ đoạn dang dở |
| Câu hỏi hoặc hội thoại quá dài | Rút gọn ngữ cảnh hoặc trả `CONTEXT_TOO_LONG`, không lỗi 500 |

Dùng nhà cung cấp AI giả (fake provider) trong test để mô phỏng các lỗi hạn mức ở trên.

Không đặt mục tiêu độ phủ (coverage) cao một cách máy móc; ưu tiên luồng nghiệp vụ quan trọng, quyền truy cập, xử lý lỗi và thao tác dữ liệu.

## Kịch bản bổ sung (xác thực, quản trị, nhiều tài liệu)

| Tình huống | Kết quả mong đợi |
|---|---|
| Đăng ký bằng email rồi đăng nhập bằng Google cùng email | Theo quy tắc liên kết đã chốt; không để tài khoản bị chiếm bằng email chưa xác minh |
| ID token Google giả, hết hạn hoặc sai đối tượng nhận | Bị từ chối |
| Dùng lại token đặt lại mật khẩu hoặc token xác minh đã dùng | Bị từ chối |
| Quên mật khẩu với email không tồn tại | Thông báo giống hệt trường hợp email tồn tại |
| Đổi mật khẩu | Mọi refresh token cũ bị thu hồi |
| Người dùng thường gọi API `/v1/admin/*` | Bị từ chối |
| Quản trị viên khóa người dùng | Phiên của người đó bị thu hồi, đăng nhập bị từ chối kèm thông báo rõ |
| Quản trị viên đổi cấu hình hoặc khóa người dùng | Có bản ghi trong nhật ký kiểm toán; không sửa được bản ghi |
| Hỏi đáp trên nhiều tài liệu, trong đó có tài liệu của người khác | Chỉ dùng tài liệu của chủ sở hữu; không lộ nội dung người khác |
| Hỏi đáp khi một tài liệu đã bị xóa | Lịch sử cũ còn, trích dẫn hiện "tài liệu đã xóa" |
| Người dùng hỏi quá 30 câu trong ngày | `USER_QUOTA_EXCEEDED` kèm số lượt còn lại và thời điểm đặt lại |
| Đổi ngôn ngữ giao diện sang tiếng Anh | Mọi chuỗi đã dịch, không còn khóa i18n trần |

## Kịch bản bổ sung (học tập)

| Tình huống | Kết quả mong đợi |
|---|---|
| AI đề xuất thẻ | Thẻ chỉ được lưu sau khi người học xác nhận; không tự lưu |
| Hết hạn mức AI khi tạo thẻ | Tạo thẻ bằng tay vẫn dùng được; báo rõ lý do cho phần AI |
| Chấm một thẻ ôn tập theo SM-2 | Ngày ôn kế tiếp, hệ số và khoảng cách tính đúng theo quy tắc đã chốt |
| Ôn tập khi AI ngừng hoặc mất mạng | Vẫn ôn được; kết quả được lưu tạm và đồng bộ sau, không mất, không ghi trùng |
| Chấm trắc nghiệm | Điểm do code so khớp đáp án đã lưu, không gọi AI |
| Yêu cầu tóm tắt chương đã có | Trả bản đã lưu, không gọi AI lại |
| Tải file Word hợp lệ | Xử lý đến `READY`, trích dẫn có số trang quy đổi |
| Tài liệu scan khi hết hạn mức AI | Dùng OCR dự phòng, ghi nhận phương pháp đã dùng, không để job nằm chờ vô hạn |

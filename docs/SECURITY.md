# Bảo mật

> **Khi nào đọc:** khi làm xác thực, phân quyền, truy vấn dữ liệu người dùng, cache, xóa dữ liệu, hoặc quản lý khóa và secret.

Các việc bảo mật còn lại cần làm nằm ở giai đoạn 4 trong docs/PLAN.md. Quy tắc khóa API và dữ liệu khi dùng gói AI miễn phí nằm trong docs/AI_PIPELINE.md.

## Bảo mật giữa người dùng

Đây là rủi ro lớn nhất của ứng dụng RAG. Giả sử người A tải `giao_trinh.pdf`, người B tải `tai_lieu.pdf`; khi B hỏi AI:

- Truy vấn chỉ lấy chunk thuộc tài liệu mà B được phép truy cập, lọc **trước khi** nội dung vào ngữ cảnh AI.
- Không dùng kết quả cache của A cho B: khóa cache phải gồm người dùng và tập tài liệu.
- Không thể vượt kiểm tra quyền bằng cách đổi ID trên URL hoặc trong nội dung request.
- Lịch sử hội thoại, trích dẫn, flashcard và file tải về đều kiểm tra quyền.
- Worker kiểm tra trạng thái trước thao tác nhạy cảm (tài liệu đã xóa thì dừng).
- Row-Level Security của PostgreSQL là lớp phòng thủ bổ sung, **không thay thế** kiểm tra quyền trong ứng dụng.
- Tách riêng development, staging, production (database, storage, API URL, thông tin xác thực, khóa mã hóa); không dùng database production để chạy test.

## Xác thực và quản trị

**Đăng nhập (email và mật khẩu, Google)**
- Mật khẩu băm bằng argon2 hoặc bcrypt; không lưu thô, không ghi log.
- ID token của Google xác thực ở backend (chữ ký, đối tượng nhận, hạn dùng). Không tin email hay ID do app tự gửi lên.
- Liên kết tài khoản khi trùng email: chỉ tự liên kết khi email đã được nhà cung cấp xác minh (đề xuất, chờ xác nhận); tránh để người khác chiếm tài khoản bằng một email chưa xác minh.
- Access token ngắn hạn (khoảng 15 phút), refresh token xoay vòng và thu hồi được; đổi mật khẩu thì thu hồi toàn bộ phiên.
- Giới hạn tốc độ riêng cho đăng nhập, quên mật khẩu, gửi lại email xác minh; thông báo lỗi không tiết lộ email có tồn tại.
- Token xác minh email và đặt lại mật khẩu: dùng một lần, hạn ngắn, lưu dạng băm.

**Quản trị**
- Vai trò admin kiểm tra ở backend cho mọi API `/v1/admin/*`; ẩn nút ở giao diện không thay thế kiểm tra này.
- Không có đăng ký quản trị công khai; quản trị viên đầu tiên tạo bằng script hoặc cấu hình.
- Quản trị viên không xem nội dung tài liệu và hội thoại của người dùng (đề xuất, chờ xác nhận); chỉ thấy siêu dữ liệu và thống kê.
- Mọi thao tác quản trị ghi vào `audit_logs`; nhật ký không sửa, không xóa qua ứng dụng.
- Cân nhắc bắt buộc xác thực hai bước cho tài khoản quản trị (chưa chốt).

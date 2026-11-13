# Đặc tả tính năng: F4. Xác minh email và quên mật khẩu

- **Trạng thái:** Xong (2026-11-13). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U2, U3; màn hình 2 (Quên và đặt lại mật khẩu), 3 (Xác minh email)

## 1. Mục tiêu
Tài khoản email và mật khẩu xác minh được email bằng mã gửi qua email; người quên mật khẩu đặt lại được mà không ai dò được email nào có tài khoản.

## 2. Luồng
**Xác minh email (U2)**
1. Đăng ký xong, hệ thống gửi email chứa mã 6 chữ số; người dùng vẫn vào app ngay.
2. Chưa xác minh: màn hình Không gian có dải nhắc; tải tài liệu bị từ chối với `EMAIL_NOT_VERIFIED` và thông báo hướng dẫn.
3. Màn hình Xác minh email: nhập mã; nút Gửi lại mã (tối đa 1 lần mỗi phút, 5 lần mỗi giờ).

**Quên mật khẩu (U3)**
1. Màn hình đăng nhập có liên kết **Quên mật khẩu?**.
2. Nhập email: luôn hiện cùng một thông báo "nếu email có tài khoản, mã đã được gửi".
3. Nhập mã, mật khẩu mới (theo quy tắc mật khẩu F2) và nhập lại.
4. Xong: mọi phiên đăng nhập cũ bị đăng xuất, email được coi là đã xác minh, hệ thống gửi email báo mật khẩu đã đổi.
5. Tài khoản chỉ đăng nhập bằng Google: email gửi đi hướng dẫn dùng Google (không đặt mật khẩu).

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/auth/email-verification` | POST (cần đăng nhập) | Gửi mã mới; 204; 429 `TOO_MANY_ATTEMPTS` khi gửi quá dày |
| `/v1/auth/email-verification/confirm` | POST `{code}` | 200 `User`; 400 `INVALID_CODE` |
| `/v1/auth/password-reset` | POST `{email}` | Luôn 202, không có nội dung |
| `/v1/auth/password-reset/confirm` | POST `{email, code, new_password}` | 204; 400 `INVALID_CODE`; 422 `WEAK_PASSWORD` |

## 5. Dữ liệu (migration mới)
`auth_codes`: `user_id`, `purpose` (`verify_email`, `reset_password`), `code_hash`, `expires_at`, `used_at`, `attempts`.

## 6. Quy tắc
- Mã 6 chữ số, sinh ngẫu nhiên an toàn, hiệu lực 15 phút, dùng một lần; gửi mã mới làm mã cũ hết hiệu lực.
- Lưu dạng HMAC-SHA256 với `SECRET_KEY` (R15): lộ database cũng không dò được mã.
- Nhập sai 5 lần thì mã hết hiệu lực; mỗi lần sai đều được ghi lại kể cả khi yêu cầu thất bại.
- Mã chỉ dùng cho đúng mục đích (mã xác minh không đặt lại mật khẩu được và ngược lại).
- Giới hạn yêu cầu đặt lại: 3 lần mỗi giờ mỗi email, 20 lần mỗi giờ mỗi IP; quá giới hạn thì im lặng (vẫn trả 202).
- Email dạng văn bản thuần, theo ngôn ngữ của người dùng; không ghi nội dung email hay mã vào log (R10).
- Gửi email bằng SMTP (Mailpit khi chạy local); gửi lỗi thì ghi log mục đích, không làm hỏng yêu cầu.
- Bật `REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD` (mặc định bật).

## 9. Tiêu chí nghiệm thu
1. Đăng ký gửi mã; nhập đúng thì `email_verified = true`.
2. Sai mã: `INVALID_CODE`; sai 5 lần thì mã đúng cũng hết dùng được.
3. Gửi lại thay mã cũ và bị giới hạn tần suất.
4. Chưa xác minh không tải tài liệu được; xác minh xong tải được.
5. Quên mật khẩu trả giống nhau cho email có và không có tài khoản.
6. Đặt lại: đổi mật khẩu, thu hồi mọi refresh token, mật khẩu cũ hết dùng, email được xác minh, có email báo.
7. Mã gắn với mục đích. 8. Mã hết hạn bị từ chối. 9. Mã không lưu dạng chữ thường.
10. Tài khoản chỉ có Google nhận hướng dẫn dùng Google; vượt giới hạn yêu cầu thì im lặng.
11. Giao diện: quên mật khẩu hai bước, xác minh email, gửi lại, dải nhắc, song ngữ.
12. Thử thật với Mailpit: nhận đủ email và đi hết hai luồng.

## 12. Lựa chọn đã tự chốt
- Dùng mã 6 chữ số thay vì liên kết: dùng được trên cả app và web, không cần cấu hình mở liên kết vào app.
- Tài khoản chỉ có Google không được thêm mật khẩu qua luồng quên mật khẩu.
- Gửi email bằng `smtplib` của Python (chạy trong thread), không thêm thư viện.
- Thứ tự lát: F4 làm trước F3 vì F3 cần OAuth client Google của người dùng.

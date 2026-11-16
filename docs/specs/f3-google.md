# Đặc tả tính năng: F3. Đăng nhập bằng Google

- **Trạng thái:** Code xong (2026-11-16); chờ người dùng tạo OAuth client (docs/SETUP_GOOGLE.md) để thử thật
- **Luồng:** U1 (phần Google); màn hình 1

## 1. Mục tiêu
Người học đăng nhập hoặc đăng ký bằng tài khoản Google trên web (và bản dev build trên điện thoại), không cần mật khẩu.

## 2. Luồng
1. Màn hình đăng nhập có nút **Tiếp tục với Google**, chỉ hiện khi nền tảng đang chạy có client ID.
2. App mở Google (thư viện `expo-auth-session`), nhận **ID token**, gửi `POST /v1/auth/google {id_token, locale}`.
3. Backend **xác thực ID token** (R15): chữ ký RS256 với khóa công khai của Google (tải và lưu tạm), đối tượng nhận là một trong `GOOGLE_CLIENT_IDS`, nơi phát hành là Google, còn hạn. Chỉ tin dữ liệu trong token.
4. Tìm danh tính `google` theo `sub`:
   - Có: đăng nhập vào tài khoản đó.
   - Chưa có, email chưa có tài khoản: tạo tài khoản không mật khẩu (email đã xác minh nếu Google xác minh), ngôn ngữ theo `locale`.
   - Chưa có, email đã có tài khoản: **chỉ liên kết khi Google xác minh email**; nếu không trả `GOOGLE_LINK_REQUIRED` (409) để tránh chiếm tài khoản.
5. Cấp phiên như đăng nhập thường: mobile nhận token, web nhận cookie `httpOnly` (R12). Tài khoản bị khóa: `ACCOUNT_BLOCKED`.

## 4. API
`POST /v1/auth/google`. Lỗi: `INVALID_GOOGLE_TOKEN` (401), `ACCOUNT_BLOCKED` (403), `GOOGLE_LINK_REQUIRED` (409), `GOOGLE_NOT_CONFIGURED` (503, khi `GOOGLE_CLIENT_IDS` trống).

## 5. Dữ liệu
Không có migration mới: dùng bảng `auth_identities` sẵn có (`provider = google`, `provider_subject = sub`).

## 6. Liên quan
- Quên mật khẩu với tài khoản chỉ có Google: email hướng dẫn dùng Google (F4).
- Xóa tài khoản chỉ có Google: xác nhận bằng cách nhập lại email (F15).
- Đổi mật khẩu với tài khoản chỉ có Google: `NO_PASSWORD` (F15).

## 9. Tiêu chí nghiệm thu
1. Kiểm tra token: token hợp lệ được nhận; sai chữ ký, sai đối tượng nhận, sai nơi phát hành, hết hạn, thiếu email, chuỗi rác đều bị từ chối (test đơn vị với khóa RSA tự sinh).
2. Lần đầu tạo tài khoản đã xác minh, không mật khẩu, đúng ngôn ngữ; lần sau vào đúng tài khoản đó.
3. Email Google đã xác minh trùng tài khoản email: liên kết, tài khoản có cả hai cách đăng nhập.
4. Email Google chưa xác minh trùng tài khoản: 409, không liên kết.
5. Token giả: 401; tài khoản bị khóa: 403; chưa cấu hình: 503.
6. Web nhận cookie `httpOnly`, không có token trong body.
7. Frontend: chọn đúng client ID theo nền tảng, ẩn nút khi không có; gửi ID token lên backend; thông báo lỗi song ngữ.
8. Backend tải được khóa công khai thật của Google (đã thử: 2 khóa).
9. **Chờ người dùng:** thử thật với OAuth client (docs/SETUP_GOOGLE.md).

## 12. Lựa chọn đã tự chốt
- Dùng `PyJWT` và `cryptography` sẵn có (không thêm thư viện Google); frontend thêm `expo-auth-session`, `expo-web-browser`, `expo-crypto` (bộ chuẩn của Expo cho OAuth).
- Expo Go không hỗ trợ đăng nhập Google; trên điện thoại cần bản dev build, nếu không thì dùng email và mật khẩu.

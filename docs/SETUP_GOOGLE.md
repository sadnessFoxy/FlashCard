# Bật đăng nhập bằng Google (việc bạn tự làm, khoảng 15 phút)

Code đã xong và có test. Chỉ còn thiếu **OAuth client ID** do bạn tạo bằng tài khoản Google của bạn; agent không tạo hộ được. Chưa làm bước này thì app vẫn chạy bình thường, chỉ không hiện nút "Tiếp tục với Google".

Client ID **không phải bí mật** (nằm công khai trong app), nhưng vẫn để trong `.env`, không cần commit.

## 1. Tạo dự án và màn hình đồng ý
1. Mở https://console.cloud.google.com, đăng nhập, tạo dự án mới (ví dụ `flashcard-dev`).
2. Vào **APIs & Services → OAuth consent screen** (hoặc **Google Auth Platform → Branding**):
   - Loại người dùng: **External**.
   - Tên ứng dụng: `FlashCard`, email hỗ trợ: email của bạn.
   - Phạm vi (scopes): chỉ cần `openid`, `email`, `profile` (mặc định).
   - **Test users:** thêm các email Google bạn sẽ dùng để thử. Ở chế độ "Testing" chỉ những email này đăng nhập được, đủ cho bản thử nghiệm.

## 2. Tạo client cho web (bắt buộc, dùng cho cả thử trên trình duyệt)
**APIs & Services → Credentials → Create credentials → OAuth client ID**
- Application type: **Web application**, tên `FlashCard web`.
- **Authorized JavaScript origins:** `http://localhost:8081` và `http://localhost:19006`.
- **Authorized redirect URIs:** `http://localhost:8081` và `http://localhost:19006`.
- Bấm Create, chép **Client ID** (dạng `1234-abc.apps.googleusercontent.com`).

## 3. (Tùy chọn) Client cho điện thoại
Chỉ cần khi chạy **bản dev build** trên điện thoại (Expo Go không hỗ trợ đăng nhập Google; trên Expo Go hãy dùng email và mật khẩu).
- **Android:** Application type **Android**, package `com.example.flashcard.dev`, SHA-1 lấy bằng `cd frontend/android && ./gradlew signingReport` sau khi có bản dev build.
- **iOS:** Application type **iOS**, bundle ID `com.example.flashcard.dev`.

## 4. Điền vào cấu hình
Trong `backend/.env` (backend dùng để kiểm tra token, liệt kê **mọi** client ID, cách nhau dấu phẩy):
```
GOOGLE_CLIENT_IDS=1234-web.apps.googleusercontent.com,1234-android.apps.googleusercontent.com
```
Khi chạy frontend, đặt biến môi trường (PowerShell):
```
$env:GOOGLE_WEB_CLIENT_ID="1234-web.apps.googleusercontent.com"
$env:GOOGLE_ANDROID_CLIENT_ID="..."   # nếu có
$env:GOOGLE_IOS_CLIENT_ID="..."       # nếu có
make dev-frontend
```
Khởi động lại backend sau khi sửa `.env`.

## 5. Thử
1. Mở http://localhost:8081, màn hình đăng nhập có nút **Tiếp tục với Google**.
2. Đăng nhập bằng một email trong danh sách Test users: lần đầu tự tạo tài khoản (email đã xác minh, không có mật khẩu).
3. Nếu email đó đã có tài khoản email và mật khẩu: Google xác minh email nên hai cách đăng nhập được gộp vào một tài khoản.

## Lỗi thường gặp
| Hiện tượng | Cách xử lý |
|---|---|
| Không thấy nút Google | Chưa đặt `GOOGLE_WEB_CLIENT_ID` khi chạy frontend |
| "Đăng nhập Google chưa được thiết lập trên máy chủ" | `GOOGLE_CLIENT_IDS` trong `backend/.env` trống; điền rồi khởi động lại backend |
| "Không xác thực được đăng nhập Google" | Client ID của frontend không có trong `GOOGLE_CLIENT_IDS` của backend |
| Google báo `redirect_uri_mismatch` hoặc `access_blocked` | Thêm đúng địa chỉ ở bước 2, hoặc thêm email vào Test users |

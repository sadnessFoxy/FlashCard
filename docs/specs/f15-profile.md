# Đặc tả tính năng: F15. Hồ sơ và cài đặt

- **Trạng thái:** Xong (2026-11-14). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U4, U9, U10; màn hình 4 (Hồ sơ và cài đặt)

## 1. Mục tiêu
Người dùng xem tài khoản, đổi ngôn ngữ giao diện (lưu theo tài khoản), xem lượt dùng AI còn lại hôm nay, đổi mật khẩu, đăng xuất và xóa tài khoản kèm toàn bộ dữ liệu.

## 2. Luồng
1. Tab **Hồ sơ**: email, trạng thái xác minh (chưa xác minh thì có liên kết nhập mã).
2. **Ngôn ngữ giao diện**: Tiếng Việt hoặc English; đổi là áp dụng ngay và lưu vào tài khoản; đăng nhập trên máy khác cũng dùng ngôn ngữ này.
3. **Lượt dùng AI hôm nay**: số câu hỏi còn lại và số lượt tạo thẻ bằng AI còn lại; đặt lại lúc 0 giờ giờ Việt Nam.
4. **Đổi mật khẩu**: nhập mật khẩu hiện tại, mật khẩu mới, nhập lại. Xong thì các thiết bị khác bị đăng xuất, thiết bị đang dùng vẫn đăng nhập, có email báo.
5. **Xóa tài khoản**: cảnh báo không khôi phục được; xác nhận bằng mật khẩu. Tài khoản chỉ dùng Google thì nhập lại email. Xóa xong về màn hình đăng nhập.

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/me` | PATCH `{locale}` | 200 `User` |
| `/v1/auth/password/change` | POST `{current_password, new_password}` | 200 phiên mới (`AuthSession`); 403 `INVALID_PASSWORD`; 409 `NO_PASSWORD`; 422 `WEAK_PASSWORD`; 429 `TOO_MANY_ATTEMPTS` |
| `/v1/me/deletion` | POST `{password?, confirm_email?}` | 204 (web: xóa cookie phiên); 403 `INVALID_PASSWORD`; 422 `CONFIRMATION_MISMATCH`; 429 |
| `/v1/usage/me` | GET | Đã có (F7, F9) |

## 6. Quy tắc
- Nhập lại mật khẩu cho thao tác nhạy cảm bị giới hạn như đăng nhập (5 lần sai trong 15 phút thì khóa tạm), để phiên bị đánh cắp không dò được mật khẩu.
- Đổi mật khẩu: kiểm tra quy tắc mật khẩu F2, thu hồi mọi refresh token, cấp phiên mới cho thiết bị đang dùng.
- Xóa tài khoản (U9): xóa người dùng; khóa ngoại xóa theo mọi dữ liệu (Không gian, tài liệu, đoạn, hội thoại, bộ thẻ, thẻ, nhật ký ôn, token, đồng ý); file tài liệu được xóa bằng job dọn nền (ARQ thử lại đến khi kho file xác nhận); dòng `ai_usage` chỉ giữ số liệu ẩn danh (`user_id` thành rỗng). Bản sao lưu xóa theo chu kỳ, tối đa 30 ngày (ghi trong cảnh báo).
- Ngôn ngữ: app đổi theo `locale` của tài khoản mỗi khi đăng nhập hoặc nhận thông tin người dùng mới.

## 9. Tiêu chí nghiệm thu
1. Đổi ngôn ngữ lưu vào tài khoản; giá trị lạ bị từ chối.
2. Đổi mật khẩu: phiên khác bị thu hồi, thiết bị hiện tại vẫn dùng được, đăng nhập bằng mật khẩu mới được, có email báo.
3. Sai mật khẩu hiện tại: `INVALID_PASSWORD`; mật khẩu yếu: `WEAK_PASSWORD`; sai quá số lần: 429 kể cả khi nhập đúng.
4. Tài khoản chỉ có Google: `NO_PASSWORD`.
5. Xóa tài khoản: không còn dữ liệu, file được đưa vào hàng đợi dọn, `ai_usage` ẩn danh, phiên cũ hết dùng, tài khoản khác không bị ảnh hưởng.
6. Tài khoản chỉ có Google xác nhận bằng email (không phân biệt hoa thường, khoảng trắng).
7. Web: xóa cookie phiên.
8. Giao diện: hiển thị lượt dùng, đổi ngôn ngữ áp dụng ngay, đổi mật khẩu, xóa tài khoản (cả kiểu Google), song ngữ.
9. Thử thật qua HTTP: đủ các bước trên.

## 12. Lựa chọn đã tự chốt
- Đổi mật khẩu đăng xuất mọi thiết bị khác nhưng giữ thiết bị đang dùng (cấp phiên mới).
- Tài khoản chỉ có Google xác nhận xóa bằng cách nhập lại email; khi có F3 sẽ thêm xác nhận bằng đăng nhập Google.
- Dùng `POST /v1/me/deletion` thay cho `DELETE /v1/me` có nội dung, để tránh proxy bỏ nội dung của lệnh DELETE.

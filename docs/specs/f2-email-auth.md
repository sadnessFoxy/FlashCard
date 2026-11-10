# Đặc tả tính năng: F2. Đăng ký, đăng nhập bằng email và mật khẩu, duy trì và kết thúc phiên

- **Trạng thái:** Xong 2026-11-10 (người dùng duyệt ngày 2026-11-09: Q1 = A, đồng ý Q2, Q3, Q4). Khác biệt khi làm: xem mục 13
- **Thuộc bản:** 1
- **Giai đoạn liên quan:** F2 (giai đoạn F); một phần giai đoạn 4 (access token ngắn, refresh xoay vòng, băm mật khẩu, giới hạn đăng nhập sai)
- **Luồng:** U1 (phần email), U4 trong docs/BUSINESS_FLOWS.md; màn hình 1 trong docs/SCREENS.md

## 1. Mục tiêu
Người dùng tạo tài khoản bằng email và mật khẩu, đăng nhập, mở lại app vẫn còn đăng nhập, và đăng xuất được, trên cả web và mobile. Các lát sau dùng chung cơ chế phiên này để biết "ai đang gọi API".

## 2. Luồng người dùng

**Đăng ký**
1. Mở app chưa đăng nhập: vào màn hình 1, tab "Đăng ký".
2. Nhập email, mật khẩu, nhập lại mật khẩu. App kiểm tra ngay ở máy: email đúng định dạng, mật khẩu đủ dài, hai lần nhập khớp.
3. Gửi lên backend. Backend chuẩn hóa email, kiểm tra mật khẩu theo quy tắc ở mục 6, băm mật khẩu, tạo tài khoản và cấp phiên.
4. Vào thẳng màn hình chính (đã đăng nhập). Tài khoản ở trạng thái **chưa xác minh email**; việc gửi email xác minh làm ở lát F4.
5. Lỗi: email đã được dùng (xem câu hỏi mở Q1), mật khẩu yếu (nêu rõ lý do), đăng ký quá nhiều lần, mất mạng.

**Đăng nhập**
1. Tab "Đăng nhập": nhập email, mật khẩu.
2. Đúng: vào màn hình chính.
3. Sai email hoặc sai mật khẩu: **một thông báo chung duy nhất** "Email hoặc mật khẩu không đúng", không cho biết email có tồn tại hay không.
4. Sai quá số lần cho phép: tạm khóa đăng nhập, hiện thời gian phải chờ.
5. Tài khoản bị quản trị viên khóa: chỉ báo "tài khoản đã bị khóa" khi mật khẩu **đúng**; mật khẩu sai vẫn nhận thông báo chung.

**Duy trì phiên (U4)**
1. Mở lại app: app hỏi backend "tôi là ai". Phiên còn hạn thì vào màn hình chính, không thì về màn hình đăng nhập.
2. Access token hết hạn (15 phút): API client tự gọi refresh **một lần** rồi gửi lại yêu cầu, người dùng không nhận ra. Nhiều yêu cầu cùng lúc thì chỉ refresh một lần.
3. Refresh thất bại (hết hạn, bị thu hồi): xóa phiên ở app, về màn hình đăng nhập.

**Đăng xuất**
1. Ở tab Hồ sơ bấm "Đăng xuất": backend thu hồi refresh token của phiên này, app xóa phiên và về màn hình đăng nhập.
2. Mất mạng khi đăng xuất: app vẫn xóa phiên ở máy (token còn lại sẽ tự hết hạn).

## 3. Màn hình và hành vi giao diện

| Màn hình | Nội dung | Trạng thái |
|---|---|---|
| 1. Đăng nhập và đăng ký (`app/(auth)/login.tsx`) | Hai tab Đăng nhập / Đăng ký; ô email, mật khẩu (có nút hiện/ẩn), nhập lại mật khẩu (tab Đăng ký); nút gửi | Đang gửi (khóa nút), lỗi từng ô, lỗi chung, bị giới hạn số lần thử (hiện thời gian chờ), tài khoản bị khóa, mất mạng |
| Màn hình chính tạm (`app/(tabs)/`) | Điều hướng theo docs/SCREENS.md: **Không gian** (chỗ trống, làm ở F4b), **Hồ sơ** (email đang đăng nhập, nút đăng xuất). Tab **Thẻ học** thêm ở F9 | Đang tải phiên lần đầu (màn hình chờ) |
| Trạng thái hệ thống (lát F1) | Chuyển sang đường dẫn `/system`, vẫn mở được khi chưa đăng nhập | Như F1 |

- Nút "Đăng nhập bằng Google" (F3) và liên kết "Quên mật khẩu" (F4) **chưa hiện** ở lát này.
- Mọi chuỗi qua i18n (R14); lỗi hiển thị dựa trên `code` từ API, không hiện `message` kỹ thuật.
- Web và mobile dùng chung giao diện; chỉ khác cách giữ token (mục 7).

## 4. API

Tất cả nằm trong tag `auth`, viết vào `contract/openapi.yaml` trước khi code.

| Endpoint | Phương thức | Yêu cầu | Phản hồi | Mã lỗi |
|---|---|---|---|---|
| `/v1/auth/register` | POST | `{email, password, locale?}` + header `X-Client-Platform` | 201 `AuthSession` | 422 `VALIDATION_ERROR`, 422 `WEAK_PASSWORD` (kèm `reason`), 409 `EMAIL_UNAVAILABLE`, 429 `TOO_MANY_ATTEMPTS` |
| `/v1/auth/login` | POST | `{email, password}` + `X-Client-Platform` | 200 `AuthSession` | 401 `INVALID_CREDENTIALS`, 403 `ACCOUNT_BLOCKED`, 429 `TOO_MANY_ATTEMPTS` |
| `/v1/auth/refresh` | POST | Mobile: `{refresh_token}`; web: cookie | 200 `AuthSession` (token mới, token cũ hết hiệu lực) | 401 `INVALID_REFRESH_TOKEN`, 403 `ACCOUNT_BLOCKED` |
| `/v1/auth/logout` | POST | Mobile: `{refresh_token}`; web: cookie | 204 | Luôn 204 (token sai cũng vậy) |
| `/v1/me` | GET | Access token | 200 `User` | 401 `UNAUTHORIZED` |

- `AuthSession` = `{user: User, access_token?, refresh_token?, access_token_expires_in}`. Mobile (`X-Client-Platform: native`) nhận token trong body; web (`X-Client-Platform: web`) **không** nhận token trong body mà nhận cookie `httpOnly` (R12).
- `User` = `{id, email, email_verified, locale, role, created_at}`. Không có `password_hash`, `status` nội bộ.
- 429 kèm header `Retry-After` và trường `retry_after_seconds`.
- Bổ sung các mã lỗi trên vào `ErrorResponse` và `frontend/src/api/errors.ts`.

## 5. Dữ liệu

Migration Alembic đầu tiên của dự án (R9), tạo 3 bảng theo đề xuất trong docs/DATA_MODEL.md:

| Bảng | Cột | Ràng buộc, index |
|---|---|---|
| `users` | `id` UUID, `email` (đã chuẩn hóa), `password_hash` (cho phép rỗng: tài khoản chỉ có Google ở F3), `role` (`user`, `admin`), `status` (`active`, `blocked`), `locale` (`vi`, `en`), `email_verified_at`, `deleted_at`, `created_at`, `updated_at` | `email` unique; CHECK cho `role`, `status`, `locale` |
| `auth_identities` | `id`, `user_id`, `provider` (`email`, `google`), `provider_subject`, `email`, `email_verified`, `created_at` | unique (`provider`, `provider_subject`); index `user_id`; xóa theo user |
| `refresh_tokens` | `id`, `user_id`, `family_id`, `token_hash` (SHA-256), `expires_at`, `revoked_at`, `replaced_by_id`, `session_started_at`, `user_agent` (cắt 200 ký tự), `created_at` | `token_hash` unique; index (`user_id`), (`family_id`) |

Điều chỉnh so với đề xuất trong docs/DATA_MODEL.md, kèm lý do:
- `password_hash` để ở `users` (như bảng gốc), không để ở `auth_identities`: mỗi người có tối đa một mật khẩu.
- Thêm `family_id` và `replaced_by_id` vào `refresh_tokens`: dùng để phát hiện token bị đánh cắp (mục 7).
- Không lưu IP của thiết bị (dữ liệu cá nhân, chưa cần).
- `email_tokens` để sang F4.

## 6. Quy tắc nghiệp vụ

- **Chuẩn hóa email:** bỏ khoảng trắng hai đầu, chuẩn Unicode NFKC, chuyển chữ thường toàn bộ; kiểm tra định dạng bằng `email-validator`. Không bỏ dấu chấm hay phần `+` của Gmail.
- **Mật khẩu** (theo hướng dẫn NIST, xem Q2): 8 đến 128 ký tự; không bắt buộc chữ hoa hay ký tự đặc biệt; bị từ chối nếu trùng email, hoặc nằm trong danh sách mật khẩu phổ biến (`backend/app/modules/auth/data/common_passwords.txt`, gồm cả mật khẩu tiếng Việt hay gặp); khoảng trắng được giữ nguyên.
- **Giới hạn số lần thử** (xem Q3), đếm bằng Redis:
  - Đăng nhập sai: 5 lần trong 15 phút cho mỗi email; 20 lần trong 15 phút cho mỗi IP. Đăng nhập đúng xóa bộ đếm của email đó.
  - Đăng ký: 5 lần mỗi giờ cho mỗi IP.
  - Redis không hoạt động: vẫn cho đăng nhập (ghi cảnh báo), vì khóa toàn bộ người dùng nguy hại hơn.
- **Thời hạn phiên** (xem Q4): access token 15 phút; refresh token 30 ngày, mỗi lần refresh cấp token mới 30 ngày; chuỗi phiên tối đa 90 ngày kể từ lần đăng nhập, sau đó phải đăng nhập lại. Mọi giá trị nằm trong cấu hình.
- Người dùng có thể đăng nhập trên nhiều thiết bị cùng lúc; mỗi thiết bị là một chuỗi refresh token riêng.
- Ngôn ngữ (`locale`) lấy theo ngôn ngữ đang chọn trên app lúc đăng ký.

## 7. Quyền và bảo mật

- **Băm mật khẩu** bằng argon2id (có sẵn trong `core/security.py`); không ghi mật khẩu, token, email vào log (R10). Log chỉ ghi `user_id` và kết quả.
- **Chống dò email:** đăng nhập sai luôn trả cùng mã lỗi và **cùng thời gian xử lý**. Khi email không tồn tại, backend vẫn chạy một phép kiểm tra mật khẩu giả để thời gian phản hồi không lộ thông tin.
- **Access token:** JWT HS256, ký bằng `SECRET_KEY`, gồm `sub` (user id), `type=access`, `exp`. Backend kiểm tra mỗi yêu cầu và kiểm tra tài khoản còn `active`, nên tài khoản bị khóa mất quyền ngay.
- **Refresh token:** chuỗi ngẫu nhiên (không phải JWT), chỉ lưu bản băm (R15).
  - Mỗi lần refresh: token cũ bị thu hồi, cấp token mới cùng `family_id`.
  - **Dùng lại token đã thu hồi** (dấu hiệu bị đánh cắp): thu hồi toàn bộ chuỗi của thiết bị đó, bắt đăng nhập lại.
- **Mobile:** token lưu bằng `expo-secure-store` (đã có `storage/session.native.ts`).
- **Web:** backend đặt 2 cookie `httpOnly`, `SameSite=Lax`, có `Secure` khi không phải development:
  - `access_token`: dùng cho mọi API.
  - `refresh_token`: chỉ gửi tới `/v1/auth/`.
  - JavaScript không đọc được token (R12).
- **Chống CSRF cho web:** yêu cầu thay đổi dữ liệu (POST/PUT/PATCH/DELETE) dùng cookie phải có header `Origin` nằm trong `CORS_ORIGINS`, nếu không thì bị từ chối với 403 `CSRF_REJECTED`.
- `/v1/me` và mọi endpoint sau này lấy người dùng từ token qua một dependency chung (`get_current_user`), làm nền cho kiểm tra theo chủ sở hữu (R4).

## 8. AI và hạn mức
Không gọi AI.

## 9. Tiêu chí nghiệm thu

1. Cho email chưa dùng, Khi đăng ký với mật khẩu hợp lệ, Thì nhận 201, tài khoản được tạo với `email_verified=false`, mật khẩu lưu dạng băm argon2, và người dùng vào màn hình chính.
2. Cho email `  An@Example.COM `, Khi đăng ký, Thì email lưu là `an@example.com`; đăng nhập bằng `an@example.com` thành công.
3. Cho mật khẩu 7 ký tự, hoặc trùng email, hoặc là `password123`, Khi đăng ký, Thì nhận 422 `WEAK_PASSWORD` kèm lý do, và không tạo tài khoản.
4. Cho email đã có tài khoản, Khi đăng ký, Thì nhận phản hồi theo lựa chọn ở Q1, và không tạo tài khoản thứ hai.
5. Cho mật khẩu sai, và cho email không tồn tại, Khi đăng nhập, Thì cả hai nhận 401 `INVALID_CREDENTIALS` với nội dung giống hệt nhau.
6. Cho 5 lần đăng nhập sai liên tiếp với cùng email, Khi thử lần 6 (kể cả đúng mật khẩu), Thì nhận 429 `TOO_MANY_ATTEMPTS` kèm `Retry-After`.
7. Cho tài khoản bị khóa, Khi đăng nhập đúng mật khẩu, Thì nhận 403 `ACCOUNT_BLOCKED`; Khi sai mật khẩu, Thì nhận 401 như bình thường.
8. Cho access token hết hạn, Khi app gọi API, Thì app tự refresh một lần và yêu cầu thành công; nhiều yêu cầu đồng thời chỉ tạo đúng một lần refresh.
9. Cho refresh token đã dùng để refresh, Khi dùng lại token đó, Thì nhận 401 và mọi token trong chuỗi phiên của thiết bị đó bị thu hồi.
10. Cho người dùng đăng xuất, Khi dùng lại refresh token cũ, Thì nhận 401.
11. Cho đăng nhập trên web, Thì body phản hồi không chứa token, cookie có `HttpOnly`, và `/v1/me` trả đúng người dùng.
12. Cho yêu cầu POST dùng cookie từ `Origin` lạ, Thì nhận 403 `CSRF_REJECTED`.
13. Cho người dùng A đăng nhập, Khi gọi `/v1/me`, Thì chỉ nhận thông tin của A, không có `password_hash`.
14. Cho đổi ngôn ngữ sang tiếng Anh, Thì mọi chữ trên màn hình 1 và mọi thông báo lỗi đều là tiếng Anh.
15. Log của backend không chứa mật khẩu, token hay email trong mọi test trên.

## 10. Test cần có

- **Unit (backend):** chuẩn hóa email; quy tắc mật khẩu; tạo và kiểm tra access token (hết hạn, sai chữ ký, sai `type`); băm refresh token; tính thời hạn chuỗi phiên.
- **API và integration (backend, database test thật):** tiêu chí 1 đến 13; contract test như F1 cho mọi endpoint mới; migration chạy lên và chạy lùi được trên database test.
- **Security (backend, `tests/security/`):** kịch bản "đăng nhập sai mật khẩu" trong docs/TESTING.md; dò email qua đăng nhập; dùng lại refresh token; CSRF; không lộ dữ liệu nhạy cảm trong log.
- **Frontend:** màn hình đăng nhập và đăng ký (kiểm tra từng ô, lỗi theo mã, giới hạn số lần thử, chuyển màn hình khi thành công); API client refresh một lần khi có nhiều yêu cầu 401 cùng lúc, và khi refresh thất bại thì về đăng nhập; khóa i18n vi/en đầy đủ.
- **Chạy thử thủ công:** đăng ký, đăng nhập, tải lại trang vẫn còn đăng nhập, đăng xuất, trên web.
- E2E (Maestro hoặc Detox) chưa làm vì chưa chọn công cụ.

## 11. Ngoài phạm vi
- Đăng nhập Google và liên kết tài khoản (F3).
- Gửi email xác minh, quên và đặt lại mật khẩu (F4). Ở F2, tài khoản luôn chưa xác minh và chưa bị giới hạn gì; giới hạn "chưa xác minh thì chưa tải tài liệu" áp dụng từ F4/F5.
- Đổi mật khẩu, xóa tài khoản, đổi ngôn ngữ trong hồ sơ (F15).
- Khóa và mở khóa tài khoản từ giao diện quản trị (F16). Ở F2 chỉ có cột `status` và kiểm tra khi đăng nhập.
- Row-Level Security của PostgreSQL, xác thực hai bước (giai đoạn 4, F16).

## 12. Câu hỏi mở (đã trả lời)

**Q1. Đăng ký bằng email đã có tài khoản thì trả lời thế nào?**
- **A (khuyến nghị):** báo chung "Không thể đăng ký bằng email này. Nếu đây là email của bạn, hãy đăng nhập hoặc đặt lại mật khẩu" (409 `EMAIL_UNAVAILABLE`). Cách này để lộ một phần rằng email đã được dùng, nhưng được giảm thiểu bằng giới hạn 5 lần đăng ký mỗi giờ. Người dùng vẫn đăng nhập ngay sau khi đăng ký.
- **B:** luôn trả "hãy kiểm tra email" dù email có tồn tại hay không, nên không lộ gì. Nhưng người dùng phải bấm liên kết xác minh trong email mới đăng nhập được, tức F2 phải chờ làm cùng F4.

**Q2. Quy tắc mật khẩu ở mục 6 có được không?** Gồm: tối thiểu 8 ký tự, không bắt buộc ký tự đặc biệt, chặn mật khẩu phổ biến và mật khẩu trùng email.

**Q3. Giới hạn số lần thử ở mục 6 có được không?** Gồm: 5 lần sai mỗi 15 phút theo email, 20 lần theo IP, 5 lần đăng ký mỗi giờ.

**Q4. Thời hạn phiên ở mục 6 có được không?** Gồm: tự đăng xuất nếu 30 ngày không mở app; dù dùng liên tục thì cũng phải đăng nhập lại sau 90 ngày.

Giả định đã đặt, không cần trả lời nếu đồng ý:
- Điều hướng chính đổi theo docs/SCREENS.md: Không gian, Thẻ học, Hồ sơ. Bộ 4 tab hiện tại (Thư viện, Hỏi đáp, Ôn tập, Hồ sơ) do bản khung tạo ra không khớp với tài liệu.
- Màn hình trạng thái hệ thống của F1 chuyển sang `/system`.
- Thêm 2 thư viện backend nhỏ: `email-validator` (kiểm tra định dạng email) và `argon2-cffi` (đã có sẵn).

## 13. Khác biệt so với đặc tả khi triển khai

- `refresh_tokens` có thêm cột `session_started_at` để tính giới hạn 90 ngày mà không phải dò lại cả chuỗi.
- Có **khoảng ân hạn 30 giây** (`REFRESH_REUSE_GRACE_SECONDS`): nếu một refresh token vừa xoay vòng bị gửi lại trong 30 giây (ví dụ hai tab trình duyệt cùng gia hạn), backend chỉ từ chối chứ không thu hồi cả phiên. Sau 30 giây mới coi là bị đánh cắp.
- Danh sách mật khẩu phổ biến tự soạn (khoảng 200 mục từ 8 ký tự trở lên, có mật khẩu tiếng Việt) thay vì 1.000 mục, vì không tải được danh sách công khai và mật khẩu dưới 8 ký tự đã bị chặn sẵn.
- Màn hình chờ khi mở app có thêm trạng thái "không kết nối được máy chủ" kèm nút thử lại, để không nhầm mất mạng với chưa đăng nhập.
- Thư viện: `PyJWT` và `argon2-cffi` thay cho `python-jose` và `passlib` (cả hai đã ngừng bảo trì); thêm `email-validator`.

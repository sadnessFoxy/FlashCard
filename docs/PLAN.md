# Kế hoạch và tiến độ

> **Dành cho agent:** đây là nguồn sự thật về tiến độ. Làm việc theo thứ tự giai đoạn, chọn việc chưa tick (`[ ]`) tiếp theo. Khi xong một việc: đổi thành `[x]`, sửa cột Xong/Tổng trong bảng tiến độ, thêm một dòng vào nhật ký thay đổi. Không tick khi chưa chạy test và chưa đạt định nghĩa "xong" trong AGENTS.md.

## Cách dùng

1. Đi lần lượt từng giai đoạn; mỗi giai đoạn có **mục tiêu**, **việc cần làm** và **tiêu chí hoàn thành**.
2. Chỉ chuyển sang giai đoạn sau khi đạt tiêu chí hoàn thành của giai đoạn trước (riêng Bảo mật nên bắt đầu sớm và chạy song song).
3. Sau mỗi lần cập nhật, sửa lại cột **Xong/Tổng** và **Trạng thái** ở bảng tiến độ.

Trạng thái: `Chưa bắt đầu` · `Đang làm` · `Xong` · `Tạm hoãn`

## Bảng tiến độ tổng quan

| # | Giai đoạn | Xong/Tổng | Trạng thái | Dự kiến | Thực tế |
|---|---|---|---|---|---|
| 0 | Chuẩn bị & chốt quyết định | 12/16 | Đang làm | | |
| 1 | Khởi tạo dự án | 15/19 | Đang làm | Tuần 1 | 2026-11-07 |
| 2 | CI/CD | 0/9 | Tạm hoãn | Người dùng hoãn 2026-11-10 | |
| 3 | Kết nối & đồng bộ dữ liệu | 3/16 | Đang làm | Tuần 2 đến 4 | |
| 4 | Bảo mật | 7/28 | Đang làm | Tuần 2 đến 4, rà soát lại trước beta | |
| 5 | Sức tải, hiệu năng & chi phí AI | 3/19 | Đang làm | Trước production | |
| 6 | Beta & chuẩn bị production | 0/10 | Chưa bắt đầu | | |
| 7 | Ra mắt & vận hành | 0/6 | Chưa bắt đầu | | |
| F | Lát chức năng bản 1 | 11/17 | Đang làm | Song song với giai đoạn 1 đến 6 | 2026-11-08 |
| | **Tổng** | **51/140** | | | |

---

## Giai đoạn 0. Chuẩn bị & chốt quyết định

**Mục tiêu:** biết rõ làm app gì, cho ai, và chốt các lựa chọn công nghệ lớn trước khi viết code.

**Việc cần làm**
- [x] Xác định loại app và mục tiêu sản phẩm: trợ lý học tập từ tài liệu
- [x] Liệt kê tính năng bản 1 đầy đủ chức năng (xem docs/PRODUCT.md và docs/SCREENS.md)
- [x] Xác định quy mô team và vai trò: làm một mình, phần lớn code do agent viết
- [x] Chọn backend tự dựng hay dùng BaaS (Firebase/Supabase): tự dựng, Python (FastAPI)
- [x] Chọn kiến trúc backend: modular monolith (xem docs/ARCHITECTURE.md)
- [x] Chọn monorepo hay nhiều repo: monorepo gồm `frontend/`, `backend/`, `contract/` (OpenAPI), FE và BE không import code của nhau
- [x] Chọn nhà cung cấp hạ tầng: Railway
- [ ] Chốt ngân sách hosting hằng tháng trên Railway (không có gói miễn phí vĩnh viễn, xem docs/OPERATIONS.md)
- [x] Chọn dịch vụ xác thực: tự xây, hỗ trợ email và mật khẩu, Google (không có Apple ở bản 1)
- [x] Chọn cổng thanh toán nếu có: không có tính năng thu phí ở bản 1
- [x] Định nghĩa chỉ số tải mục tiêu: 100 người dùng, 10 đồng thời, API p95 dưới 500 ms, chữ đầu tiên trong khoảng 3 giây
- [x] Quyết định ngân sách AI và hạn mức người dùng: ngân sách AI 0 đồng (gói miễn phí), mặc định khoảng 30 câu mỗi người mỗi ngày (xem docs/QUOTA_AND_RESILIENCE.md)
- [x] Chọn nhà cung cấp AI: Gemini API, dùng gói miễn phí; thiết kế để chuyển sang gói trả phí bất kỳ lúc nào (xem docs/AI_PIPELINE.md)
- [ ] Chốt các dòng còn `Chưa chốt` trong docs/DECISIONS.md (ngân sách hosting, kho lưu file, dịch vụ email, liên kết tài khoản, giao diện quản trị...)
- [ ] Chuẩn bị bên ngoài (người dùng tự làm): khóa Gemini API (Google AI Studio) và OAuth client của Google Cloud khi tới lát đăng nhập Google; Railway chỉ cần khi muốn đưa lên mạng
- [ ] Ghi mỗi quyết định kèm lý do vào tài liệu quyết định (ADR)

**Tiêu chí hoàn thành:** bảng quyết định trong docs/DECISIONS.md không còn dòng `Chưa chốt` cho các mục thuộc giai đoạn này.


---

## Giai đoạn 1. Khởi tạo dự án

**Mục tiêu:** có khung app và backend chạy được ở máy local, với công cụ chất lượng code bật sẵn từ đầu.

**Đầu vào:** các quyết định của giai đoạn 0.

**Việc cần làm**
- [x] Chọn và ghi lại phiên bản ổn định (stable hoặc LTS, không cần mới nhất) của Python, Node, Expo SDK, PostgreSQL, pgvector vào file khóa phiên bản (`versions.txt`)
- [x] Tạo app bằng `create-expo-app` với TypeScript (tạo thủ công `package.json`, `app.config.ts`, `tsconfig.json`)
- [x] Cài `expo-dev-client`, `expo-secure-store`, `expo-router` (khai báo trong `frontend/package.json`)
- [x] Bật TypeScript `strict` (`frontend/tsconfig.json` với tất cả strict flags)
- [x] Cài ESLint và Prettier (`frontend/.eslintrc.js`)
- [x] Cài Husky và lint-staged (khai báo trong `frontend/package.json`)
- [x] Cài Jest và React Native Testing Library (khai báo trong `frontend/package.json`)
- [ ] Chọn công cụ test end-to-end: Maestro hoặc Detox (cần người dùng quyết định)
- [x] Tách 3 môi trường dev / staging / production, mỗi môi trường có API URL và bundle ID riêng (`frontend/app.config.ts`)
- [ ] Thiết lập repo và quy tắc nhánh: `main` (production), `develop`, `feature/*` qua Pull Request (cần setup GitHub branch protection)
- [x] Tạo backend FastAPI, chia module `auth`, `users`, `documents`, `chat`, `study`, `ai`, `usage`, `admin` (mỗi module có router, schemas, models, service, repository), thêm thư mục `integrations/` (object storage, email, llm_gateway) và `workers/`
- [x] Viết `contract/openapi.yaml` skeleton (contract-first); CI kiểm tra breaking change (xem `.github/workflows/ci.yml`)
- [x] Dựng Docker Compose chạy Postgres (pgvector/pgvector:pg16, kèm database test `flashcard_test`), Redis, Mailpit, SeaweedFS làm kho file S3 (`infra/docker/docker-compose.yml`)
- [x] Thiết lập Alembic và migration đầu tiên cho các bảng chính (xem docs/DATA_MODEL.md): `users`, `auth_identities`, `refresh_tokens` ở lát F2; các bảng khác thêm theo từng lát
- [ ] Tạo cột vector 768 chiều (đã chốt) và index tương ứng; xác nhận trên tài liệu thật (xem docs/AI_PIPELINE.md) - thuộc lát F5
- [x] Cài i18n cho frontend (tiếng Việt và tiếng Anh) - `frontend/src/i18n/` với vi.json và en.json
- [x] Viết `providers/gemini.py` theo interface chung cho LLM và embedding; tên mô hình, số chiều, giới hạn tốc độ, khóa API đọc từ cấu hình/biến môi trường, không viết cứng
- [x] Cài pytest và HTTPX cho backend; tạo `tests/` gồm `unit`, `integration`, `api`, `security`, `fixtures` (khai báo trong `pyproject.toml`, `tests/conftest.py`)
- [x] Tổ chức thư mục frontend theo docs/ARCHITECTURE.md (`app`, `features`, `components`, `api`, `hooks`, `store`, `storage`, `theme`...)

**Tiêu chí hoàn thành:** clone repo về, chạy một lệnh là app và backend lên được; commit sai lint bị chặn.

---

## Giai đoạn 2. CI/CD

> **Tạm hoãn (2026-11-10):** người dùng yêu cầu bỏ qua CI/CD. Workflow `.github/workflows/ci.yml` vẫn giữ nhưng chỉ chạy tay; kiểm tra chất lượng chạy ở máy local (lint, typecheck, test) trước mỗi commit. Agent không làm các việc dưới đây cho tới khi người dùng mở lại.

**Mục tiêu:** mỗi lần đẩy code, hệ thống tự kiểm tra, build và phát hành mà không cần làm tay.

**Luồng đích**

| Sự kiện | Hệ thống tự làm |
|---|---|
| Mở Pull Request | Lint, kiểm tra kiểu, chạy test |
| Merge vào `develop` | Chạy kiểm tra và đóng gói bản thử nghiệm (không đẩy lên store) |
| Gắn tag phiên bản (ví dụ v0.1.0) | Đóng gói bản thử nghiệm |
| Backend merge | Build Docker image, deploy staging, duyệt, deploy production |

**Việc cần làm**
- [ ] Workflow CI cho PR trên GitHub Actions (lint, typecheck, test)
- [ ] CI chạy unit và integration test của backend trên Postgres thử nghiệm (không dùng database production)
- [ ] Branch protection: PR phải qua CI mới được merge
- [ ] Pipeline backend: build Docker, deploy lên Railway (staging rồi production), duyệt trước khi lên production
- [ ] Dựng môi trường Railway cho từng môi trường: dịch vụ API, worker ARQ, PostgreSQL có pgvector, Redis, kho file; biến môi trường theo môi trường (xem docs/OPERATIONS.md)
- [ ] Chạy migration database tự động trong pipeline, luôn thử trên staging trước
- [ ] Tích hợp Sentry cho cả app và backend
- [ ] Quản lý secret bằng GitHub Secrets, không commit key vào repo
- [ ] Soạn quy trình rollback khi bản phát hành lỗi

**Tiêu chí hoàn thành:** một thay đổi nhỏ đi từ PR đến staging hoàn toàn tự động.

---

## Giai đoạn 3. Kết nối & đồng bộ dữ liệu

**Mục tiêu:** app chạy ổn định trên mạng di động chập chờn, không mất hoặc nhân đôi dữ liệu.

**Việc cần làm**

*Lớp gọi API và cache*
- [ ] Một API client duy nhất: gắn token, timeout, retry khi lỗi mạng, tự refresh token khi nhận 401
- [ ] TanStack Query cho cache, refetch khi mở lại app, retry, trạng thái loading/error
- [ ] Zustand chỉ cho state phía client (trạng thái giao diện tạm, cài đặt); dữ liệu từ server do TanStack Query quản lý

*Offline*
- [ ] Phát hiện trạng thái mạng bằng NetInfo
- [ ] Cache xuống máy bằng MMKV
- [ ] Hàng đợi thao tác ghi khi mất mạng, gửi lại khi có mạng
- [ ] Optimistic update, rollback khi lỗi

*Toàn vẹn dữ liệu*
- [x] Idempotency-Key (UUID mỗi thao tác) cho tải tài liệu và các thao tác tạo dữ liệu quan trọng, backend trả kết quả cũ nếu key trùng (tải tài liệu, F5; các thao tác khác thêm theo lát)
- [ ] Chọn chiến lược xung đột: last-write-wins hoặc optimistic locking bằng `version`/`updatedAt`

*Thời gian thực và thông báo*
- [ ] Realtime nếu cần (WebSocket/Socket.IO hoặc SSE)
- [ ] Push notification qua Expo Notifications (FCM/APNs)
- [x] Hiển thị trạng thái xử lý tài liệu cho người dùng (polling hoặc thông báo) theo máy trạng thái ở docs/DATA_MODEL.md (polling 3 giây khi còn tài liệu đang xử lý, F5)
- [ ] Khai báo mã lỗi hạn mức AI trong hợp đồng OpenAPI (`AI_TEMPORARILY_UNAVAILABLE`, `AI_RATE_LIMITED`, `USER_QUOTA_EXCEEDED`, `CONTEXT_TOO_LONG`), kể cả lỗi giữa luồng streaming (docs/QUOTA_AND_RESILIENCE.md)
- [x] App xử lý các mã lỗi hạn mức: thông báo thân thiện, hiện số lượt còn lại và thời điểm đặt lại, giữ lại câu hỏi đã gõ để gửi lại

*Tương thích phiên bản*
- [ ] Đánh phiên bản API (`/v1`, `/v2`) và giữ tương thích ngược
- [ ] Cơ chế force update: backend trả phiên bản tối thiểu, app cũ hơn hiện màn hình yêu cầu cập nhật

**Tiêu chí hoàn thành:** tắt mạng giữa chừng khi tải tài liệu rồi bật lại, không tạo tài liệu trùng và không mất tài liệu; app hiện đúng thông báo khi AI hết hạn mức.

---

## Giai đoạn 4. Bảo mật

**Mục tiêu:** đóng các lỗ hổng phổ biến trước khi có người dùng thật. Bắt đầu cùng giai đoạn 3 và rà soát lại trước beta.

**Việc cần làm**

*Phía app*
- [x] Lưu token bằng `expo-secure-store` (Keychain/Keystore), không dùng AsyncStorage; web dùng cookie httpOnly (F2)
- [ ] Không nhúng secret hoặc API key vào app
- [ ] Bắt buộc HTTPS; cân nhắc certificate pinning cho app tài chính
- [ ] Phát hiện root/jailbreak nếu app nhạy cảm
- [ ] Khóa sinh trắc học cho thao tác quan trọng
- [ ] Che nội dung nhạy cảm ở màn hình đa nhiệm

*Xác thực và phân quyền*
- [x] Access token ngắn (khoảng 15 phút) cộng refresh token có xoay vòng (rotation) và thu hồi được; phát hiện dùng lại token (F2)
- [x] Băm mật khẩu bằng argon2 hoặc bcrypt (argon2id, F2)
- [ ] Đăng nhập email và mật khẩu, Google: backend xác thực ID token, quy tắc liên kết tài khoản (xem docs/SECURITY.md)
- [x] Xác minh email và quên mật khẩu: token một lần, hạn ngắn, không lộ email có tồn tại hay không, thu hồi phiên sau khi đổi mật khẩu (F4)
- [x] Tích hợp dịch vụ gửi email (xác minh, đặt lại mật khẩu, cảnh báo) (F4: SMTP, Mailpit khi chạy local)
- [ ] Tự xây xác thực bằng thư viện chuẩn (không tự phát minh thuật toán mã hóa) và kiểm thử kỹ các luồng U1 đến U4 trong docs/BUSINESS_FLOWS.md
- [ ] Phân quyền theo từng bản ghi ở backend (chống IDOR, tức xem tài liệu của người khác bằng cách đổi ID)
- [ ] Phân quyền quản trị: vai trò admin kiểm tra ở backend, API `/v1/admin/*`, quản trị viên không xem nội dung người dùng, mọi thao tác ghi nhật ký kiểm toán (xem docs/SECURITY.md)
- [ ] Bật PostgreSQL Row-Level Security như lớp phòng thủ bổ sung (không thay thế kiểm tra quyền trong ứng dụng)
- [ ] Khóa cache theo người dùng, không dùng chung kết quả cache giữa các người dùng (docs/SECURITY.md)
- [x] Triển khai chính sách xóa tài liệu: file gốc, chunk, vector và job đang chờ; tài liệu đang xóa không còn xuất hiện trong tìm kiếm (F6: `DELETING` rồi job dọn nền, tác vụ định kỳ dọn lại)

*Backend và hạ tầng*
- [ ] Validate mọi input; dùng ORM hoặc query tham số hóa chống SQL injection
- [ ] Cấu hình CORS, Helmet, và rate limit riêng cho đăng nhập (chống brute-force)
- [ ] Lưu secret trong Secrets Manager/Vault
- [ ] Quản lý khóa API AI: mỗi môi trường một khóa riêng, chỉ nằm ở backend, không commit lên Git, có quy trình thu hồi và tạo khóa mới khi nghi bị lộ
- [x] Quy tắc dữ liệu khi dùng gói AI miễn phí: thông báo rõ và xin đồng ý của người dùng trước khi tải tài liệu (nội dung được gửi cho Google xử lý và có thể được dùng để cải thiện sản phẩm), khuyến cáo không tải tài liệu nhạy cảm, không đưa thông tin định danh không cần thiết vào prompt (docs/AI_PIPELINE.md) (đồng ý theo phiên bản `user_consents`, F5)
- [ ] Mã hóa dữ liệu nhạy cảm khi lưu và khi truyền
- [ ] Quét lỗ hổng phụ thuộc trong CI (npm audit, pip-audit, Dependabot, Snyk)
- [ ] Ghi log truy cập, tuyệt đối không ghi mật khẩu hoặc token
- [ ] Backup database tự động và thử khôi phục định kỳ
- [ ] Tuân thủ quy định dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP, GDPR nếu có người dùng châu Âu) và có chức năng xóa tài khoản; bản sao lưu giữ tối đa 30 ngày sau khi xóa
- [ ] Đối chiếu OWASP Mobile Top 10 và OWASP API Security Top 10

**Tiêu chí hoàn thành:** checklist OWASP đã đối chiếu xong, không còn lỗ hổng mức cao.

---

## Giai đoạn 5. Sức tải, hiệu năng & chi phí AI

**Mục tiêu:** hệ thống đạt chỉ số tải đã đặt ở giai đoạn 0 và chi phí AI nằm trong ngân sách, kể cả khi nhà cung cấp hết hạn mức. Nguyên tắc: **đo trước, tối ưu sau**.

**Việc cần làm**

*Backend (làm theo thứ tự)*
- [ ] Đo: test tải bằng k6 hoặc Artillery; theo dõi bằng Prometheus + Grafana (hoặc Datadog)
- [ ] Tối ưu database: index đúng chỗ, tránh N+1, phân trang cursor-based, connection pool (PgBouncer)
- [ ] Cache Redis cho dữ liệu đọc nhiều, ít đổi; đặt TTL và quy tắc xóa cache
- [ ] Mở rộng ngang: nhiều bản sao API sau load balancer (API phải stateless)
- [ ] Đưa tác vụ nặng vào hàng đợi (Celery hoặc ARQ): email, xử lý ảnh, báo cáo
- [ ] Rate limiting chống quá tải và lạm dụng
- [ ] CDN cho ảnh và file tĩnh, resize ảnh nhiều kích thước
- [ ] Read replica (làm muộn, chỉ khi lượng đọc rất lớn)

*App React Native*
- [ ] Dùng `FlatList`/`FlashList` cho danh sách dài
- [ ] Bật Hermes, dùng `React.memo` và `useCallback` đúng chỗ
- [ ] Dùng `expo-image` (cache, placeholder)
- [ ] Giảm kích thước bundle, lazy load màn hình ít dùng
- [ ] Đo bằng React DevTools Profiler và Perfetto

*Chi phí AI và hạn mức (chi tiết ở docs/QUOTA_AND_RESILIENCE.md)*
- [ ] Hạn mức ba tầng (hệ thống, người dùng, mỗi yêu cầu/tài liệu): đếm bằng Redis, ước lượng trước khi gọi và ghi số token thực tế vào `ai_usage`
- [x] Phân loại lỗi và circuit breaker ở `llm_gateway`: lỗi tạm thời thì thử lại có giới hạn, lỗi hết hạn mức thì không thử lại và mở cầu dao (F5: phân biệt giới hạn tốc độ, hết hạn mức ngày hoặc billing, lỗi tạm thời)
- [x] Trạng thái `PAUSED_QUOTA` cho job tài liệu, lưu tiến độ theo từng đoạn, tự chạy lại khi hạn mức phục hồi (F5: tác vụ định kỳ 10 phút)
- [x] Chế độ suy giảm khi AI ngừng: hỏi đáp chuyển sang chỉ tìm đoạn liên quan, các tính năng không cần AI vẫn chạy (F7: không tạo được embedding thì tìm theo từ khóa)
- [ ] Biện pháp giảm token: giới hạn số đoạn đưa vào ngữ cảnh, tóm tắt hội thoại cũ, mô hình nhỏ cho việc đơn giản, giới hạn độ dài đầu ra
- [ ] Cố ý chạm giới hạn tốc độ của gói miễn phí để kiểm tra retry, circuit breaker, `PAUSED_QUOTA` và thông báo trên app

**Tiêu chí hoàn thành:** test tải đạt chỉ số mục tiêu (100 người dùng, 10 đồng thời, API p95 dưới 500 ms, chữ đầu tiên trong khoảng 3 giây); mọi nút thắt tìm ra đều có số liệu chứng minh. Khi mô phỏng nhà cung cấp AI hết hạn mức, hệ thống chuyển chế độ suy giảm, không lỗi 500 và không mất dữ liệu.

---

## Giai đoạn 6. Beta & chuẩn bị production

**Mục tiêu:** mang app đến tay nhóm thử nghiệm và chạy ổn định để thử nghiệm (không phát hành lên store).

**Việc cần làm**
- [ ] Chạy thử trên điện thoại thật qua Expo Go hoặc development build, và trên trình duyệt web
- [ ] Chạy test end-to-end cho các luồng chính (đăng nhập, tải tài liệu, hỏi đáp, ôn tập)
- [ ] Chạy đủ bảng kịch bản kiểm thử ở docs/TESTING.md, gồm kiểm tra truy cập chéo giữa người dùng
- [ ] Test tải lần cuối theo chỉ số mục tiêu
- [ ] Rà soát bảo mật lần cuối
- [ ] Thử đường chuyển gói AI trên staging: đổi sang khóa gói trả phí chỉ bằng cấu hình, app và backend chạy bình thường không sửa code; thông báo quyền riêng tư nêu rõ dữ liệu được gửi cho nhà cung cấp AI (docs/AI_PIPELINE.md)
- [ ] Dựng dashboard và cảnh báo (Sentry, Prometheus + Grafana) cho các chỉ số ở docs/OPERATIONS.md
- [ ] Viết runbook: khôi phục database, xử lý job tài liệu lỗi, rollback production, xử lý hết hạn mức AI
- [ ] Thiết lập cảnh báo ngân sách AI (50%, 80%, 100%), đặt trần chi tiêu tại tài khoản nhà cung cấp, cảnh báo khi một người dùng dùng bất thường (docs/QUOTA_AND_RESILIENCE.md)
- [ ] Thử khôi phục từ backup thành công

**Tiêu chí hoàn thành:** beta chạy ổn định ít nhất một chu kỳ thử nghiệm, không có lỗi nghiêm trọng còn mở.

---

## Giai đoạn 7. Ra mắt & vận hành

**Mục tiêu:** phát hành, theo dõi, và cải tiến dựa trên số liệu thật.

**Việc cần làm**
- [ ] Phát hành production bằng cách gắn tag phiên bản
- [ ] Theo dõi crash và hiệu năng (Sentry, dashboard)
- [ ] Thu thập phản hồi người dùng
- [ ] Đo thực tế rồi ưu tiên danh sách cần tối ưu
- [ ] Đánh giá có cần tách microservices không (chỉ khi một module cần scale riêng hoặc team đã đủ lớn)
- [ ] Cập nhật tài liệu và nhật ký quyết định

**Tiêu chí hoàn thành:** có quy trình vận hành lặp lại được: phát hiện lỗi, sửa, phát hành, theo dõi.

---

## Giai đoạn F. Lát chức năng bản 1 (làm song song với giai đoạn 1 đến 6)

**Mục tiêu:** hoàn thành đầy đủ chức năng bản 1 theo từng lát dọc (contract, backend, frontend, test cho cùng một chức năng), mỗi lát kiểm chứng được trước khi sang lát sau.

**Cách làm:** mỗi lát gồm đặc tả từ `docs/specs/_TEMPLATE.md` được người dùng duyệt, cập nhật `contract/openapi.yaml`, backend, frontend (màn hình trong docs/SCREENS.md), test (docs/TESTING.md). Các lát đầu (F1 đến F8) đi cùng giai đoạn 1 đến 3; bảo mật, hạn mức và chi phí AI ở giai đoạn 4 và 5 áp dụng cho mọi lát.

**Việc cần làm**
- [x] F1. Khung chạy được xuyên suốt: một endpoint thật đi từ frontend qua backend tới database, có kiểm tra sức khỏe và test (`/health`, `/v1/system/status`; màn hình trạng thái ở `frontend/app/index.tsx`)
- [x] F2. Đăng ký, đăng nhập bằng email và mật khẩu, duy trì và kết thúc phiên (U1, U4; màn hình 1; docs/specs/f2-email-auth.md)
- [ ] F3. Đăng nhập bằng Google (U1; màn hình 1)
- [x] F4. Xác minh email và quên, đặt lại mật khẩu (U2, U3; màn hình 2, 3) (docs/specs/f4-email-codes.md)
- [x] F4b. Không gian học tập: tạo, đổi tên, xóa, không gian mặc định (U16; màn hình 5; docs/specs/f4b-spaces.md). Hàm tạo không gian mặc định đã có, được gọi từ luồng tải lên ở F5
- [x] F5. Tải tài liệu PDF và xử lý nền đến `READY`: trích văn bản, chia đoạn, embedding, trạng thái (U5; màn hình 5, 6) (docs/specs/f5-document-upload.md)
- [x] F6. Quản lý tài liệu: danh sách, chi tiết, thử lại, xóa (U6; màn hình 5, 7) (docs/specs/f6-document-management.md)
- [x] F7. Hỏi đáp trên nhiều tài liệu, có trích dẫn, trả lời dần (U7; màn hình 9) (docs/specs/f7-qa.md)
- [x] F8. Xem trích dẫn và lịch sử hội thoại (U7; màn hình 10, 11) (docs/specs/f8-citations-history.md)
- [x] F9. Flashcard: bộ thẻ, AI đề xuất và người học duyệt, tạo tay, sửa, xóa (U11; màn hình 12, 13, 14) (docs/specs/f9-flashcards.md)
- [x] F10. Ôn tập lặp lại ngắt quãng theo SM-2 và kết quả ôn tập (U12; màn hình 15, 16) (docs/specs/f10-reviews.md)
- [ ] F11. Câu hỏi trắc nghiệm: tạo, làm bài, chấm bằng code, xem lại câu sai kèm nguồn (U13; màn hình 17, 18, 19)
- [ ] F12. Tóm tắt theo chương (U15; màn hình 8)
- [ ] F13. Hỗ trợ tài liệu Word (.docx) (U5)
- [ ] F14. Tài liệu scan: Gemini đọc trực tiếp, Tesseract dự phòng, sau khi thử trên tài liệu tiếng Việt thật (U14)
- [x] F15. Hồ sơ và cài đặt: ngôn ngữ, lượt hỏi còn lại, đổi mật khẩu, xóa tài khoản (U4, U9, U10; màn hình 4) (docs/specs/f15-profile.md)
- [ ] F16. Giao diện quản trị web: tổng quan, người dùng, theo dõi job, cấu hình, nhật ký kiểm toán (A1 đến A7; màn hình 20 đến 25)

**Tiêu chí hoàn thành:** mọi chức năng trong docs/BUSINESS_FLOWS.md phần bản 1 và phần quản trị chạy được, test qua, và kịch bản trong docs/TESTING.md đều đạt.

---

## Việc có thể bổ sung sau (backlog)

- [ ] Chiến lược kiểm thử chi tiết (tỉ lệ unit/integration/E2E)
- [ ] Analytics, A/B test, feature flag
- [ ] Đa ngôn ngữ (i18n) và khả năng tiếp cận
- [ ] Ước tính chi phí hạ tầng theo từng mốc người dùng
- [ ] Design system (component, màu sắc, typography)
- [ ] Quy ước team: commit, review code, onboarding

---

## Nhật ký thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-10-05 | Tạo file từ các ý tưởng ban đầu |
| 2026-10-05 | Viết lại thành quy trình theo giai đoạn, thêm bảng tiến độ, bỏ code minh họa |
| 2026-10-22 | Chốt dự án trợ lý học tập; backend chuyển sang Python (FastAPI); FE/BE tách qua OpenAPI; thêm docs/PRODUCT.md; cập nhật giai đoạn 0 |
| 2026-10-23 | Áp dụng các điểm từ tài liệu thiết kế: module `chat`/`usage`, lớp `repository`, `integrations/`; 9 bảng gồm `document_jobs`; máy trạng thái tài liệu; bảo mật giữa người dùng (RLS, cache, xóa dữ liệu); chiến lược kiểm thử; vận hành (runbook, Prometheus/Grafana). Cập nhật giai đoạn 1 đến 6, tổng 103 việc |
| 2026-10-23 | Thêm docs/QUOTA_AND_RESILIENCE.md về hành vi khi hết hạn mức AI (mã lỗi, circuit breaker, hạn mức ba tầng, `PAUSED_QUOTA`, chế độ suy giảm, cảnh báo ngân sách); cập nhật giai đoạn 0, 3, 5, 6, máy trạng thái docs/DATA_MODEL.md, kịch bản test docs/TESTING.md, vận hành docs/OPERATIONS.md. Tổng 112 việc |
| 2026-10-28 | Thêm docs/AI_PIPELINE.md về dùng Gemini API bản miễn phí (quy tắc dữ liệu, giới hạn tốc độ, quản lý khóa, embedding và chiều vector, chuyển gói trả phí); cập nhật giai đoạn 0, 1, 4, 5, 6 và bảng rủi ro. Tổng 119 việc |
| 2026-10-28 | Điều chỉnh docs/AI_PIPELINE.md: dùng gói Gemini miễn phí, không bắt buộc chuyển gói trả phí; thiết kế để chuyển bất kỳ lúc nào chỉ bằng đổi khóa và cấu hình; thay quy tắc "không nhận dữ liệu thật" bằng thông báo, xin đồng ý và giảm thiểu dữ liệu gửi đi; sửa giai đoạn 0, 1, 4, 6 và bảng rủi ro |
| 2026-10-28 | Tách thành bộ tài liệu cho agent (AGENTS.md và docs/); thêm docs/BUSINESS_FLOWS.md; sửa chỗ còn sót từ ví dụ cũ; thêm việc chốt quy tắc nghiệp vụ ở giai đoạn 0. Tổng 120 việc |
| 2026-10-29 | Chốt các quyết định (ARQ, 768 chiều, đăng nhập email/Google/Apple, song ngữ, giới hạn tải lên, hỏi đáp nhiều tài liệu, 30 câu/ngày, Railway, không thu phí, chỉ số tải, SM-2, giao diện quản trị, hướng xử lý tài liệu scan); thêm luồng quản trị, xác minh email, quên mật khẩu; cập nhật giai đoạn 0, 1, 2, 4, 5; bỏ việc thanh toán |
| 2026-10-29 | Chốt ORM là SQLAlchemy; bỏ đăng nhập Apple ở bản 1 (chỉ email và mật khẩu, Google); thêm rủi ro App Store 4.8 và việc quyết định trước khi gửi bản iOS ở giai đoạn 6 |
| 2026-10-30 | Mở rộng bản 1 thành đầy đủ chức năng (gồm flashcard, ôn tập, trắc nghiệm, tóm tắt theo chương, Word, tài liệu scan); bản 2 chỉ còn chia sẻ, học nhóm, giọng nói...; thêm docs/SCREENS.md (25 màn hình) và giai đoạn F gồm 16 lát chức năng |

| 2026-11-07 | Chốt: tên ứng dụng FlashCard, chỉ bản thử nghiệm (không phát hành lên store, bỏ rủi ro App Store 4.8, bỏ EAS Submit và hồ sơ store), có cấu trúc Không gian (U16), dùng mặc định cho các mục còn lại; thêm START_HERE.md và AGENT_PROMPTS.md |
| 2026-11-07 | Bước 0 / Giai đoạn 1: Khởi tạo monorepo `flashcard/`. Tạo cấu trúc thư mục đầy đủ; frontend (Expo SDK 52, TypeScript strict, i18n vi/en, API client, session storage); backend (FastAPI, SQLAlchemy async, Pydantic settings, Gemini provider, LLM gateway, circuit breaker); Docker Compose (Postgres+pgvector, Redis, Mailpit, MinIO); GitHub Actions CI; Makefile; versions.txt. 14/19 việc giai đoạn 1 xong; còn E2E tool, branch protection, Alembic migration đầu tiên, và vector index (thuộc lát F5). |
| 2026-11-08 | Sửa môi trường chạy được thật (npm/pip cài lỗi, MinIO thay bằng SeaweedFS, `make setup` không còn ghi đè `backend/.env`, embedding gửi đúng 768 chiều); chốt mô hình `gemini-3.5-flash-lite` và `gemini-embedding-2` |
| 2026-11-08 | Lát F1 xong: contract có `GET /health` và `GET /v1/system/status` (database có pgvector, Redis); backend kèm test khớp contract (route, operationId, schema response), unit, integration trên database test riêng (20 test); frontend sinh kiểu từ contract bằng `openapi-typescript`, màn hình trạng thái song ngữ (6 test), build web được; CI viết lại (test backend trên Postgres có pgvector, kiểm tra file sinh lệch contract, chặn thay đổi phá vỡ contract ở PR). CI **chưa chạy** vì repo chưa có remote GitHub nên chưa tick giai đoạn 2. Sửa thêm: khóa Gemini chuyển sang header để không lọt vào log (R10), tên tab viết cứng chuyển sang i18n (R14), thiếu gói web và gói phụ thuộc của expo-router |
| 2026-11-10 | Lát F2 xong (docs/specs/f2-email-auth.md): đăng ký, đăng nhập, refresh xoay vòng có phát hiện dùng lại, đăng xuất, `/v1/me`; mobile giữ token trong secure store, web dùng cookie httpOnly kèm chống CSRF theo Origin; giới hạn số lần thử bằng Redis; migration Alembic đầu tiên (3 bảng). Test: backend 88 (API, bảo mật, unit, migration lên/xuống), frontend 22. Thay `python-jose`/`passlib` (ngừng bảo trì) bằng `PyJWT`/`argon2-cffi`, thêm `email-validator`. Sửa thêm: SQL echo ghi email và bản băm vào log ở môi trường dev (giờ là `SQL_ECHO`, mặc định tắt), lỗi validation trả lại dữ liệu đã nhập, `SECRET_KEY` bắt buộc từ 32 ký tự. Điều hướng chính đổi theo docs/SCREENS.md (Không gian, Hồ sơ); màn hình trạng thái F1 chuyển sang `/system`. Comment trong code chuyển sang tiếng Anh theo yêu cầu người dùng |
| 2026-11-10 | Hoãn giai đoạn 2 (CI/CD) theo yêu cầu người dùng: workflow chỉ chạy tay; chuyển toàn bộ comment trong code sang tiếng Anh |
| 2026-11-10 | Lát F4b xong (docs/specs/f4b-spaces.md): module `spaces` (CRUD, tên chuẩn hóa NFC, không trùng tên trong tài khoản theo index `lower(name)`, Không gian của người khác trả 404), migration thứ hai, màn hình danh sách và chi tiết có hộp xác nhận xóa chạy được trên web. Test: backend 125, frontend 34; thử qua HTTP thật đủ luồng. Sửa thêm: lỗi của framework (JSON hỏng, đường dẫn không tồn tại, sai phương thức) trước đây trả `{detail}` thay vì `ErrorResponse` của contract |
| 2026-11-12 | Lát F5 xong (docs/specs/f5-document-upload.md): tải PDF (kiểm tra nội dung thật, 20 MB, 200 trang, 10 tài liệu, PDF có mật khẩu), Idempotency-Key, đồng ý dữ liệu theo phiên bản, Không gian mặc định, kho file S3 (boto3), worker ARQ trích văn bản theo trang, chia đoạn theo cấu trúc (chương, trang), embedding Gemini 768 chiều lưu pgvector có index HNSW, `PAUSED_QUOTA` và tự chạy lại, ghi `ai_usage`. Gateway phân biệt giới hạn tốc độ (chờ rồi thử lại) với hết hạn mức (không thử lại). Thử thật với Gemini trên giáo trình tiếng Việt mẫu: READY sau 2 giây, 3 câu hỏi đều trỏ đúng trang. Test: backend 197, frontend 44. Sửa: SeaweedFS cấu hình quá ít volume nên không ghi được file; worker thiếu model khi chạy riêng (thêm `app/db/all_models.py` và test chạy worker ở tiến trình riêng) |
| 2026-11-13 | Lát F6 xong (docs/specs/f6-document-management.md): chi tiết tài liệu, thử lại (`FAILED`, `PAUSED_QUOTA`), xóa theo máy trạng thái với job dọn nền mang sẵn khóa lưu trữ, chuyển Không gian; xóa Không gian giờ dọn cả file tài liệu bên trong; tác vụ định kỳ dọn lại các xóa bị kẹt. Thử thật qua worker và SeaweedFS: không còn file, không còn bản ghi. Test: backend 206, frontend 50 |
| 2026-11-13 | Lát F7 xong (docs/specs/f7-qa.md): hội thoại theo Không gian, câu trả lời trả dần qua SSE (start, citations, delta, done, error), truy xuất lọc theo chủ sở hữu, Không gian, tài liệu `READY` và tập đã chọn trước khi xếp hạng; trích dẫn lưu dạng bản ghi nhanh nên vẫn hiện khi tài liệu bị xóa; hạn mức 30 câu/ngày theo giờ Việt Nam bằng Redis (không tìm thấy và chế độ chỉ tìm đoạn không trừ lượt); AI ngừng thì chuyển sang chỉ tìm đoạn, kể cả khi không tạo được embedding (tìm theo từ khóa). Tab Hỏi đáp: chip chọn tài liệu, trả lời hiện dần (mobile dùng `expo/fetch`), chip trích dẫn, đếm lượt, giữ câu hỏi khi lỗi. Thử thật với Gemini: chữ đầu tiên sau khoảng 1,5 giây, trích dẫn đúng trang, câu ngoài tài liệu trả "không tìm thấy". Test: backend 226, frontend 63. Sửa lỗi có từ trước: phiên database commit **sau** khi phản hồi đã gửi, nên yêu cầu kế tiếp có thể chưa thấy dữ liệu (401 ngay sau đăng ký, 404 ngay sau tạo); giờ commit trước khi gửi phản hồi, có test chặn tái diễn |
| 2026-11-13 | Lát F8 xong (docs/specs/f8-citations-history.md): xem trang được trích dạng văn bản đọc lại từ PDF gốc, đoạn trích được tô nổi bật, chuyển trang, cache Redis theo người dùng; lịch sử hội thoại theo Không gian, mở lại, xóa có xác nhận. Theo yêu cầu người dùng về code dễ đọc, dễ bảo trì: tách module chat backend (nguồn trích, trích dẫn, luồng trả lời, trình bày) và tab Hỏi đáp frontend (hook gửi câu hỏi, bong bóng tin nhắn, hộp trích dẫn, chip tài liệu, ô nhập); gom helper test dùng chung. Sửa nhờ thử thật với Gemini: câu hỏi tiếng Anh trên giáo trình tiếng Việt bị trả lời bằng tiếng Việt (giờ ghi rõ ngôn ngữ cần trả lời cạnh câu hỏi, đúng 3/3 lần thử), câu trả lời có ký hiệu LaTeX, câu hỏi không có câu trả lời trong lịch sử làm lệch câu kế tiếp. Test: backend 233, frontend 74 |
| 2026-11-13 | Lát F9 xong (docs/specs/f9-flashcards.md): bộ thẻ trong Không gian, thẻ tạo bằng tay hoặc AI đề xuất từ tài liệu (khoảng trang) hay từ câu trả lời hỏi đáp; người học sửa, bỏ chọn rồi mới lưu; nguồn thẻ là bản ghi nhanh (tài liệu, trang); hạn mức tạo thẻ 10 lần mỗi ngày tính riêng với hỏi đáp; bảng thẻ có sẵn cột lịch SM-2 cho F10. Code: module `study/flashcards/`; hạn mức theo ngày tổng quát hóa (`DailyQuota`) dùng chung cho hỏi đáp và tạo thẻ; khối nguồn `<source>` và nhận diện ngôn ngữ tách ra dùng chung (`modules/ai/`); hộp xác nhận, nhóm chip dùng chung ở frontend; cấu hình test frontend có sẵn địa chỉ API nên màn hình mới không làm vỡ test cũ. Thử thật với Gemini: 6 thẻ tiếng Việt đúng nội dung, đúng trang, sau 2,3 giây. Test: backend 246, frontend 83 |
| 2026-11-13 | Lát F10 xong (docs/specs/f10-reviews.md): ôn tập SM-2 bốn mức (Quên, Khó, Được, Dễ), thẻ Quên quay lại trong phiên, màn hình kết quả (thẻ khó, lần ôn kế tiếp); không cần AI. Chạy khi mất mạng: mỗi lượt chấm có mã do app tạo, lưu hàng đợi trên máy (AsyncStorage) rồi gửi theo lô; server bỏ qua lượt gửi lại, lượt cũ đến muộn chỉ ghi nhật ký. Test: backend 261 (gồm unit test công thức SM-2), frontend 91; thử qua HTTP thật: lịch đúng, gửi lại không ghi trùng |
| 2026-11-13 | Lát F4 xong trước F3 (F3 cần OAuth client Google của người dùng) (docs/specs/f4-email-codes.md): xác minh email và quên mật khẩu bằng mã 6 chữ số qua email, mã lưu dạng HMAC, dùng một lần, 15 phút, sai 5 lần thì hủy; quên mật khẩu không lộ email nào có tài khoản; đặt lại thì thu hồi mọi phiên và gửi email báo; tài khoản chưa xác minh không tải tài liệu được (bật `REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD`). Gửi email qua SMTP bằng thư viện chuẩn (không thêm phụ thuộc); test dùng hộp thư giả. Thử thật với Mailpit: đi hết hai luồng. Test: backend 271, frontend 96 |
| 2026-11-14 | Lát F15 xong (docs/specs/f15-profile.md): màn hình Hồ sơ gồm trạng thái xác minh email, ngôn ngữ giao diện lưu theo tài khoản (app đổi theo khi đăng nhập), lượt hỏi và lượt tạo thẻ còn lại, đổi mật khẩu (đăng xuất thiết bị khác, giữ thiết bị đang dùng, có email báo), xóa tài khoản (xác nhận bằng mật khẩu hoặc nhập lại email với tài khoản Google; xóa toàn bộ dữ liệu, dọn file bằng job nền, số liệu AI chỉ giữ ẩn danh). Nhập lại mật khẩu bị giới hạn số lần như đăng nhập. Thử thật qua HTTP: đủ các bước. Test: backend 278, frontend 102 |

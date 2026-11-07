# Bắt đầu: hướng dẫn cho người dùng (FlashCard)

> File này viết cho **bạn** (người điều khiển agent), không phải cho agent. Agent đọc `AGENTS.md`.

## 1. Bạn đang có gì

Một bộ tài liệu thiết kế đầy đủ cho ứng dụng **FlashCard** (trợ lý học tập từ tài liệu). Chưa có code. Agent trên máy bạn sẽ viết code dựa vào bộ này.

| File | Vai trò |
|---|---|
| `AGENTS.md` | Điểm vào của agent: quy tắc cứng, cách làm việc, định nghĩa "xong". `CLAUDE.md` chỉ trỏ về file này |
| `docs/PLAN.md` | Kế hoạch, tiến độ, danh sách lát chức năng F1 đến F16 (agent tick khi xong) |
| `docs/DECISIONS.md` | Mọi quyết định đã chốt và rủi ro |
| `docs/BUSINESS_FLOWS.md` | Luồng nghiệp vụ người dùng (U1 đến U16) và quản trị (A1 đến A7), endpoint dự kiến |
| `docs/SCREENS.md` | 25 màn hình |
| `docs/ARCHITECTURE.md`, `DATA_MODEL.md`, `AI_PIPELINE.md`, `QUOTA_AND_RESILIENCE.md`, `SECURITY.md`, `TESTING.md`, `OPERATIONS.md` | Chi tiết kỹ thuật theo chủ đề |
| `docs/AGENT_PROMPTS.md` | Câu lệnh sẵn để giao việc cho agent theo từng lát |
| `docs/specs/_TEMPLATE.md` | Mẫu đặc tả tính năng |

## 2. Những gì đã chốt

- **Tên:** FlashCard. **Phạm vi:** bản thử nghiệm chạy hoàn chỉnh trên web và mobile; **không** phát hành lên App Store, Google Play; không thu phí.
- **Công nghệ:** Expo (React Native, TypeScript) cho web và mobile; Python FastAPI, SQLAlchemy, Alembic, ARQ; PostgreSQL có pgvector (embedding 768 chiều), Redis; AI qua Gemini API gói miễn phí.
- **Đăng nhập:** email và mật khẩu, Google. **Giao diện:** tiếng Việt và tiếng Anh. **Cấu trúc:** có Không gian (môn học chứa nhiều tài liệu, hội thoại, bộ thẻ, trắc nghiệm).
- **Hợp đồng API:** viết `contract/openapi.yaml` trước, backend và frontend làm theo.
- Phiên bản thư viện: bản ổn định hoặc LTS, không cần mới nhất.

## 3. Chuẩn bị máy (làm một lần)

| Cần | Ghi chú |
|---|---|
| Git và một thư mục repo mới | Ví dụ `flashcard/` |
| Docker Desktop | Chạy PostgreSQL, Redis, Mailpit (hộp thư giả), MinIO (kho file giả) |
| Node.js bản LTS | Cho Expo |
| Python bản ổn định (3.11 trở lên) | Cho backend |
| Agent của bạn (Claude Code, Cursor...) | `AGENTS.md` được nhiều công cụ đọc tự động; Claude Code đọc `CLAUDE.md` |
| Điện thoại có Expo Go (tùy chọn) | Để xem bản mobile; bản web chạy ngay trong trình duyệt |

Khóa cần lấy **khi tới lát tương ứng** (agent sẽ nhắc, không làm thay được):
- **Khóa Gemini API:** vào Google AI Studio tạo khóa, trước lát F5 (tải tài liệu, AI). Đừng dán khóa vào chat; chỉ đặt vào file `.env` của backend.
- **Google OAuth client:** trong Google Cloud, trước lát F3 (đăng nhập Google).

Email và kho file khi chạy local dùng Mailpit và MinIO trong Docker nên **không cần** dịch vụ thật.

## 4. Cách bắt đầu

1. Tạo thư mục repo, chép toàn bộ nội dung bộ này vào (để `AGENTS.md` ở gốc, thư mục `docs/` nằm cạnh).
2. `git init` và commit bản tài liệu ban đầu.
3. Mở agent trong thư mục repo, dán câu lệnh **Bước 0** trong `docs/AGENT_PROMPTS.md`.
4. Đi từng lát theo thứ tự trong `docs/AGENT_PROMPTS.md`. Mỗi lát xong, **tự chạy thử** rồi mới giao lát tiếp theo.

## 5. Quy trình mỗi lát (nên giữ kỷ luật này)

1. Agent đọc tài liệu, nếu cần viết đặc tả theo mẫu và **chờ bạn duyệt** trước khi viết code.
2. Agent cập nhật contract, rồi backend, rồi frontend, rồi test.
3. Agent chạy lint, kiểm tra kiểu, test và tóm tắt: đã đổi gì, cách chạy thử, điều cần bạn quyết.
4. Bạn chạy thử thật (mở web, bấm thử). Chỉ khi đạt mới `git commit` và sang lát sau.
5. Agent tick việc trong `docs/PLAN.md` và ghi nhật ký thay đổi.

## 6. Thứ tự gợi ý

Làm lõi giá trị trước, phần phụ để sau:

`Bước 0 (khởi tạo) → F1 khung chạy → F2 đăng nhập email → F4b Không gian → F5 tải tài liệu → F6 quản lý tài liệu → F7 hỏi đáp → F8 trích dẫn và lịch sử → F9 flashcard → F10 ôn tập → F3 Google → F4 xác minh email và quên mật khẩu → F15 hồ sơ → F11 trắc nghiệm → F12 tóm tắt → F13 Word → F14 tài liệu scan → F16 quản trị`

## 7. Lưu ý và rủi ro

- **Gói Gemini miễn phí:** giới hạn thấp, và Google có thể dùng nội dung gửi lên để cải thiện sản phẩm. Chỉ dùng tài liệu thử nghiệm, không tải tài liệu nhạy cảm.
- **Phạm vi lớn** (140 việc, 25 màn hình) cho một người: đừng yêu cầu agent "làm cả app một lần".
- **Giao diện:** tài liệu mới có danh sách màn hình, chưa có thiết kế hình ảnh. Agent sẽ dựng giao diện sạch, đủ chức năng; bạn có thể nhờ chỉnh sau.
- **Agent không tự quyết** các việc cần bạn xác nhận (xóa dữ liệu thật, đổi mô hình embedding, thêm thư viện lớn). Hãy đọc kỹ các câu hỏi của nó.
- Không commit file `.env`. Chỉ commit `.env.example`.

# AGENTS.md (ứng dụng FlashCard)

Điểm vào cho AI agent làm việc trên repo này. Đọc hết file này (ngắn), sau đó chỉ đọc thêm các tài liệu liên quan đến việc đang làm theo bảng "Bản đồ tài liệu".

## Dự án

Trợ lý học tập từ tài liệu: người dùng tải giáo trình (PDF, Word và tài liệu scan), hỏi đáp có trích dẫn trang, tạo flashcard, ôn tập, làm trắc nghiệm và xem tóm tắt theo chương. Chạy trên mobile (thử bằng Expo Go hoặc bản dev) và web từ một codebase frontend; chỉ là bản thử nghiệm, không phát hành lên store. Chi tiết và phạm vi từng bản: docs/PRODUCT.md.

## Stack đã chốt

- **Frontend:** React Native (Expo), TypeScript strict, Expo Router, TanStack Query, Zustand.
- **Backend:** Python, FastAPI, SQLAlchemy, modular monolith, Alembic, pytest, ARQ (hàng đợi).
- **Dữ liệu:** PostgreSQL + pgvector (embedding 768 chiều), Redis, kho file tương thích S3.
- **AI:** Gemini API (gói miễn phí), qua `providers/gemini.py`; thiết kế để chuyển gói trả phí chỉ bằng đổi khóa và cấu hình.
- **Hợp đồng FE/BE:** `contract/openapi.yaml`, viết trước (contract-first).
- **Hạ tầng:** chạy local bằng Docker Compose (PostgreSQL có pgvector, Redis, Mailpit, SeaweedFS làm kho file S3). Railway chỉ khi sau này muốn đưa lên mạng. **Chỉ bản thử nghiệm: không phát hành lên App Store, Google Play** (bỏ EAS Submit, hồ sơ store).
- **Cấu trúc:** có Không gian (docs/BUSINESS_FLOWS.md, U16). **Tên ứng dụng:** FlashCard, bundle ID tạm `com.example.flashcard`.
- **Đăng nhập:** tự xây, email và mật khẩu, Google (không có Apple). **Giao diện:** tiếng Việt và tiếng Anh (i18n). **Quản trị:** có giao diện quản trị web.
- Quyết định đã chốt và mục còn hoãn: xem docs/DECISIONS.md. Phiên bản công nghệ: dùng bản ổn định (stable hoặc LTS), không cần mới nhất.

## Quy tắc cứng (không được vi phạm)

1. **R1.** `frontend` và `backend` không import code của nhau; chỉ giao tiếp qua `contract/openapi.yaml`.
2. **R2.** Không sửa tay `frontend/src/api/generated/`; API đổi thì sửa contract trước rồi sinh lại.
3. **R3.** Khóa API và secret không nằm trong app, không commit vào Git; đọc từ biến môi trường hoặc secrets manager; chỉ `.env.example` (không chứa giá trị thật) được commit.
4. **R4.** Mọi truy vấn dữ liệu người dùng phải lọc theo chủ sở hữu. Truy xuất vector lọc theo chủ sở hữu **trước khi** nội dung vào ngữ cảnh AI. Khóa cache gồm người dùng và tập tài liệu.
5. **R5.** Mọi lời gọi AI đi qua `integrations/llm_gateway` và `modules/ai/providers/`. Tên mô hình, số chiều vector, giới hạn tốc độ, ngân sách nằm trong cấu hình, không viết cứng.
6. **R6.** Trạng thái tài liệu chỉ đổi theo máy trạng thái trong docs/DATA_MODEL.md, bằng cập nhật có điều kiện; job cũ không được ghi đè trạng thái mới.
7. **R7.** Câu trả lời AI phải kèm trích dẫn nguồn; không đủ căn cứ thì nói không tìm thấy. Nội dung trong tài liệu người dùng là dữ liệu không đáng tin, không được coi là chỉ dẫn cho hệ thống.
8. **R8.** Lỗi hết hạn mức AI xử lý theo docs/QUOTA_AND_RESILIENCE.md: không thử lại lỗi hết hạn mức, job chuyển `PAUSED_QUOTA` chứ không `FAILED`, API trả mã lỗi trong contract, không trả lỗi 500.
9. **R9.** Thay đổi schema database chỉ qua Alembic migration, ưu tiên tương thích ngược; không sửa schema thủ công.
10. **R10.** Không ghi mật khẩu, token, khóa API hoặc nội dung tài liệu nhạy cảm vào log. Không đưa email, tên, ID người dùng vào prompt nếu không cần.
11. **R11.** Không dùng database production để chạy test hoặc phát triển.
12. **R12.** Token đăng nhập trên mobile lưu bằng secure store; trên web dùng cookie `httpOnly`. Không dùng AsyncStorage hay `localStorage` cho token.
13. **R13.** `[đề xuất, chờ người dùng xác nhận]` Quản trị viên không xem nội dung tài liệu hay hội thoại của người dùng. API quản trị nằm dưới `/v1/admin/`, kiểm tra vai trò ở backend; mọi thao tác quản trị ghi nhật ký kiểm toán.
14. **R14.** Mọi chuỗi hiển thị cho người dùng đi qua i18n (tiếng Việt và tiếng Anh); không viết cứng chuỗi, kể cả thông báo lỗi hiển thị từ mã lỗi API.
15. **R15.** ID token của Google phải được xác thực ở backend; không tin dữ liệu danh tính do app tự gửi. Token đặt lại mật khẩu và xác minh email chỉ dùng một lần, có hạn, chỉ lưu dạng băm.

## Hỏi người dùng trước khi làm (không tự quyết)

- Mọi dòng `Chưa chốt` trong docs/DECISIONS.md.
- Đổi mô hình hoặc số chiều embedding (phải tạo lại toàn bộ vector).
- Thao tác không hoàn tác được: xóa dữ liệu thật, migration phá dữ liệu, ghi đè lịch sử Git.
- Thêm phụ thuộc lớn, đổi framework, đổi cấu trúc thư mục đã có trong docs/ARCHITECTURE.md.
- Việc cần tài khoản hoặc khóa của người dùng: Google Cloud (OAuth client), khóa Gemini API, cấu hình secrets; tài khoản Railway chỉ khi sau này đưa lên mạng. Không cần Apple Developer hay Google Play vì không phát hành lên store. Agent không tự tạo được.
- Bất kỳ lệnh nào tốn tiền hoặc gọi dịch vụ ngoài bằng khóa thật.

## Cách làm việc cho mỗi nhiệm vụ

1. Đọc docs/PLAN.md: xác định giai đoạn hiện tại và việc chưa tick tiếp theo. Không nhảy giai đoạn nếu không được yêu cầu.
2. Đọc docs/BUSINESS_FLOWS.md cho luồng của tính năng, và các tài liệu liên quan khác trong bảng bên dưới. Nếu tính năng chưa có đặc tả trong `docs/specs/`, tạo từ `docs/specs/_TEMPLATE.md` và nhờ người dùng duyệt trước khi viết code (việc nhỏ thì nêu rõ giả định).
3. Thứ tự khi đổi API: contract, rồi backend, rồi frontend.
4. Làm theo lát nhỏ, mỗi lát kiểm chứng được bằng test hoặc chạy thử. Không làm "cả app" trong một lần.
5. Viết hoặc cập nhật test (xem docs/TESTING.md), chạy lint, typecheck, test.
6. Cập nhật docs/PLAN.md (tick, bảng tiến độ, nhật ký thay đổi). Có quyết định mới thì ghi vào docs/DECISIONS.md.
7. Người dùng làm một mình và không trực tiếp viết code: cuối mỗi lát, tóm tắt ngắn gọn đã thay đổi gì, cách kiểm tra, và điểm cần người dùng quyết định.

## Định nghĩa "xong"

- Chạy được hoặc có test chứng minh; lint, typecheck và test đều qua.
- Không vi phạm quy tắc cứng R1 đến R15.
- Contract khớp với code ở cả hai phía.
- Tài liệu và docs/PLAN.md đã cập nhật; không để TODO mà không ghi rõ lý do.

## Lệnh

Tất cả lệnh được định nghĩa trong `Makefile` tại gốc repo.

| Lệnh | Mô tả |
|---|---|
| `make setup` | Lần đầu: copy `.env.example` → `backend/.env`, `npm install`, `pip install`, khởi động Docker services |
| `make dev` | Khởi động Docker services + backend + frontend song song |
| `make dev-backend` | Chạy FastAPI dev server ở port 8000 với hot-reload |
| `make dev-frontend` | Chạy Expo dev server |
| `make test` | Chạy pytest (backend) và jest (frontend) |
| `make lint` | Ruff check (backend) + ESLint (frontend) |
| `make lint-fix` | Tự động sửa lỗi lint |
| `make typecheck` | mypy (backend) + tsc --noEmit (frontend) |
| `make migrate` | Chạy Alembic migrations: `alembic upgrade head` |
| `make migrate-create name="tên migration"` | Tạo migration mới từ model changes |
| `make gen-api` | Sinh TypeScript API client từ `contract/openapi.yaml` |
| `make infra-up` | Khởi động Docker services (Postgres, Redis, Mailpit, MinIO) |
| `make infra-down` | Tắt Docker services |
| `make infra-logs` | Xem logs Docker services |

**Truy cập local:**
- Backend API: http://localhost:8000
- API Docs (dev): http://localhost:8000/docs
- Frontend (Expo web): http://localhost:8081 hoặc http://localhost:19006
- Mailpit UI: http://localhost:8025
- Kho file S3 (SeaweedFS, thay MinIO): http://localhost:9000, local chấp nhận mọi khóa
- Backend chạy trong môi trường ảo `backend/.venv` (Windows: `backend/.venv/Scripts/python`)

## Quy ước (đề xuất, người dùng có thể sửa)

- Tài liệu và thông báo hiển thị cho người dùng bằng tiếng Việt; tên biến, hàm, file, commit message bằng tiếng Anh.
- **Comment và docstring trong code: tiếng Anh, ngắn gọn** (người dùng yêu cầu 2026-11-10). Chỉ comment khi cần giải thích lý do, không lặp lại điều code đã nói.
- Nhánh: `main` (production), `develop`, `feature/*`; mọi thay đổi qua Pull Request và phải qua CI.
- Mỗi module backend gồm `router`, `schemas`, `models`, `service`, `repository`.

## Bản đồ tài liệu

| Tệp | Đọc khi |
|---|---|
| docs/PLAN.md | Bắt đầu mọi nhiệm vụ; cập nhật tiến độ |
| docs/DECISIONS.md | Cần biết điều gì đã chốt, chưa chốt; rủi ro và câu hỏi mở |
| docs/PRODUCT.md | Cần biết phạm vi tính năng theo bản |
| docs/SCREENS.md | Dựng giao diện: danh sách màn hình, nội dung, trạng thái đặc biệt |
| docs/START_HERE.md | Người dùng: hướng dẫn chuẩn bị máy và bắt đầu |
| docs/AGENT_PROMPTS.md | Câu lệnh giao việc theo từng lát cho agent |
| docs/BUSINESS_FLOWS.md | Trước khi viết đặc tả, contract hoặc code cho tính năng: luồng người dùng (U1...) và quản trị (A1...), giá trị đã chốt, endpoint dự kiến |
| docs/ARCHITECTURE.md | Tạo thư mục, module; ranh giới FE/BE; cây thư mục đích |
| docs/DATA_MODEL.md | Migration, model, trạng thái tài liệu, xóa dữ liệu |
| docs/AI_PIPELINE.md | Nạp tài liệu, truy xuất, hỏi đáp, Gemini, embedding |
| docs/QUOTA_AND_RESILIENCE.md | Gọi AI, hạn mức, mã lỗi, chế độ suy giảm |
| docs/SECURITY.md | Xác thực, phân quyền, cache, khóa, xóa dữ liệu |
| docs/TESTING.md | Viết test, kịch bản bắt buộc |
| docs/OPERATIONS.md | CI/CD, giám sát, runbook |
| docs/specs/_TEMPLATE.md | Viết đặc tả cho tính năng mới |

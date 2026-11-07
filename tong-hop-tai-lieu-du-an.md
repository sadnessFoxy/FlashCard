# FlashCard: toàn bộ tài liệu dự án

Bản tổng hợp một file để đọc liền mạch. Khi giao cho agent, dùng bộ file riêng (`agent-kit.zip`).

## Mục lục

1. Bắt đầu (hướng dẫn cho người dùng) (`docs/START_HERE.md`)
2. Quy tắc làm việc cho agent (AGENTS.md) (`AGENTS.md`)
3. Câu lệnh giao việc cho agent (`docs/AGENT_PROMPTS.md`)
4. Sản phẩm và phạm vi (`docs/PRODUCT.md`)
5. Quy trình nghiệp vụ (`docs/BUSINESS_FLOWS.md`)
6. Danh sách màn hình (`docs/SCREENS.md`)
7. Kiến trúc (`docs/ARCHITECTURE.md`)
8. Mô hình dữ liệu (`docs/DATA_MODEL.md`)
9. Pipeline AI, RAG và Gemini (`docs/AI_PIPELINE.md`)
10. Hạn mức AI (`docs/QUOTA_AND_RESILIENCE.md`)
11. Bảo mật (`docs/SECURITY.md`)
12. Kiểm thử (`docs/TESTING.md`)
13. Vận hành (`docs/OPERATIONS.md`)
14. Quyết định (`docs/DECISIONS.md`)
15. Kế hoạch và tiến độ (`docs/PLAN.md`)
16. Mẫu đặc tả (`docs/specs/_TEMPLATE.md`)

---

<!-- Nguồn: docs/START_HERE.md -->

## Bắt đầu: hướng dẫn cho người dùng (FlashCard)

> File này viết cho **bạn** (người điều khiển agent), không phải cho agent. Agent đọc `AGENTS.md`.

### 1. Bạn đang có gì

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

### 2. Những gì đã chốt

- **Tên:** FlashCard. **Phạm vi:** bản thử nghiệm chạy hoàn chỉnh trên web và mobile; **không** phát hành lên App Store, Google Play; không thu phí.
- **Công nghệ:** Expo (React Native, TypeScript) cho web và mobile; Python FastAPI, SQLAlchemy, Alembic, ARQ; PostgreSQL có pgvector (embedding 768 chiều), Redis; AI qua Gemini API gói miễn phí.
- **Đăng nhập:** email và mật khẩu, Google. **Giao diện:** tiếng Việt và tiếng Anh. **Cấu trúc:** có Không gian (môn học chứa nhiều tài liệu, hội thoại, bộ thẻ, trắc nghiệm).
- **Hợp đồng API:** viết `contract/openapi.yaml` trước, backend và frontend làm theo.
- Phiên bản thư viện: bản ổn định hoặc LTS, không cần mới nhất.

### 3. Chuẩn bị máy (làm một lần)

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

### 4. Cách bắt đầu

1. Tạo thư mục repo, chép toàn bộ nội dung bộ này vào (để `AGENTS.md` ở gốc, thư mục `docs/` nằm cạnh).
2. `git init` và commit bản tài liệu ban đầu.
3. Mở agent trong thư mục repo, dán câu lệnh **Bước 0** trong `docs/AGENT_PROMPTS.md`.
4. Đi từng lát theo thứ tự trong `docs/AGENT_PROMPTS.md`. Mỗi lát xong, **tự chạy thử** rồi mới giao lát tiếp theo.

### 5. Quy trình mỗi lát (nên giữ kỷ luật này)

1. Agent đọc tài liệu, nếu cần viết đặc tả theo mẫu và **chờ bạn duyệt** trước khi viết code.
2. Agent cập nhật contract, rồi backend, rồi frontend, rồi test.
3. Agent chạy lint, kiểm tra kiểu, test và tóm tắt: đã đổi gì, cách chạy thử, điều cần bạn quyết.
4. Bạn chạy thử thật (mở web, bấm thử). Chỉ khi đạt mới `git commit` và sang lát sau.
5. Agent tick việc trong `docs/PLAN.md` và ghi nhật ký thay đổi.

### 6. Thứ tự gợi ý

Làm lõi giá trị trước, phần phụ để sau:

`Bước 0 (khởi tạo) → F1 khung chạy → F2 đăng nhập email → F4b Không gian → F5 tải tài liệu → F6 quản lý tài liệu → F7 hỏi đáp → F8 trích dẫn và lịch sử → F9 flashcard → F10 ôn tập → F3 Google → F4 xác minh email và quên mật khẩu → F15 hồ sơ → F11 trắc nghiệm → F12 tóm tắt → F13 Word → F14 tài liệu scan → F16 quản trị`

### 7. Lưu ý và rủi ro

- **Gói Gemini miễn phí:** giới hạn thấp, và Google có thể dùng nội dung gửi lên để cải thiện sản phẩm. Chỉ dùng tài liệu thử nghiệm, không tải tài liệu nhạy cảm.
- **Phạm vi lớn** (140 việc, 25 màn hình) cho một người: đừng yêu cầu agent "làm cả app một lần".
- **Giao diện:** tài liệu mới có danh sách màn hình, chưa có thiết kế hình ảnh. Agent sẽ dựng giao diện sạch, đủ chức năng; bạn có thể nhờ chỉnh sau.
- **Agent không tự quyết** các việc cần bạn xác nhận (xóa dữ liệu thật, đổi mô hình embedding, thêm thư viện lớn). Hãy đọc kỹ các câu hỏi của nó.
- Không commit file `.env`. Chỉ commit `.env.example`.

---

<!-- Nguồn: AGENTS.md -->

## AGENTS.md (ứng dụng FlashCard)

Điểm vào cho AI agent làm việc trên repo này. Đọc hết file này (ngắn), sau đó chỉ đọc thêm các tài liệu liên quan đến việc đang làm theo bảng "Bản đồ tài liệu".

### Dự án

Trợ lý học tập từ tài liệu: người dùng tải giáo trình (PDF, Word và tài liệu scan), hỏi đáp có trích dẫn trang, tạo flashcard, ôn tập, làm trắc nghiệm và xem tóm tắt theo chương. Chạy trên mobile (thử bằng Expo Go hoặc bản dev) và web từ một codebase frontend; chỉ là bản thử nghiệm, không phát hành lên store. Chi tiết và phạm vi từng bản: docs/PRODUCT.md.

### Stack đã chốt

- **Frontend:** React Native (Expo), TypeScript strict, Expo Router, TanStack Query, Zustand.
- **Backend:** Python, FastAPI, SQLAlchemy, modular monolith, Alembic, pytest, ARQ (hàng đợi).
- **Dữ liệu:** PostgreSQL + pgvector (embedding 768 chiều), Redis, kho file tương thích S3.
- **AI:** Gemini API (gói miễn phí), qua `providers/gemini.py`; thiết kế để chuyển gói trả phí chỉ bằng đổi khóa và cấu hình.
- **Hợp đồng FE/BE:** `contract/openapi.yaml`, viết trước (contract-first).
- **Hạ tầng:** chạy local bằng Docker Compose (PostgreSQL có pgvector, Redis, Mailpit, MinIO). Railway chỉ khi sau này muốn đưa lên mạng. **Chỉ bản thử nghiệm: không phát hành lên App Store, Google Play** (bỏ EAS Submit, hồ sơ store).
- **Cấu trúc:** có Không gian (docs/BUSINESS_FLOWS.md, U16). **Tên ứng dụng:** FlashCard, bundle ID tạm `com.example.flashcard`.
- **Đăng nhập:** tự xây, email và mật khẩu, Google (không có Apple). **Giao diện:** tiếng Việt và tiếng Anh (i18n). **Quản trị:** có giao diện quản trị web.
- Quyết định đã chốt và mục còn hoãn: xem docs/DECISIONS.md. Phiên bản công nghệ: dùng bản ổn định (stable hoặc LTS), không cần mới nhất.

### Quy tắc cứng (không được vi phạm)

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

### Hỏi người dùng trước khi làm (không tự quyết)

- Mọi dòng `Chưa chốt` trong docs/DECISIONS.md.
- Đổi mô hình hoặc số chiều embedding (phải tạo lại toàn bộ vector).
- Thao tác không hoàn tác được: xóa dữ liệu thật, migration phá dữ liệu, ghi đè lịch sử Git.
- Thêm phụ thuộc lớn, đổi framework, đổi cấu trúc thư mục đã có trong docs/ARCHITECTURE.md.
- Việc cần tài khoản hoặc khóa của người dùng: Google Cloud (OAuth client), khóa Gemini API, cấu hình secrets; tài khoản Railway chỉ khi sau này đưa lên mạng. Không cần Apple Developer hay Google Play vì không phát hành lên store. Agent không tự tạo được.
- Bất kỳ lệnh nào tốn tiền hoặc gọi dịch vụ ngoài bằng khóa thật.

### Cách làm việc cho mỗi nhiệm vụ

1. Đọc docs/PLAN.md: xác định giai đoạn hiện tại và việc chưa tick tiếp theo. Không nhảy giai đoạn nếu không được yêu cầu.
2. Đọc docs/BUSINESS_FLOWS.md cho luồng của tính năng, và các tài liệu liên quan khác trong bảng bên dưới. Nếu tính năng chưa có đặc tả trong `docs/specs/`, tạo từ `docs/specs/_TEMPLATE.md` và nhờ người dùng duyệt trước khi viết code (việc nhỏ thì nêu rõ giả định).
3. Thứ tự khi đổi API: contract, rồi backend, rồi frontend.
4. Làm theo lát nhỏ, mỗi lát kiểm chứng được bằng test hoặc chạy thử. Không làm "cả app" trong một lần.
5. Viết hoặc cập nhật test (xem docs/TESTING.md), chạy lint, typecheck, test.
6. Cập nhật docs/PLAN.md (tick, bảng tiến độ, nhật ký thay đổi). Có quyết định mới thì ghi vào docs/DECISIONS.md.
7. Người dùng làm một mình và không trực tiếp viết code: cuối mỗi lát, tóm tắt ngắn gọn đã thay đổi gì, cách kiểm tra, và điểm cần người dùng quyết định.

### Định nghĩa "xong"

- Chạy được hoặc có test chứng minh; lint, typecheck và test đều qua.
- Không vi phạm quy tắc cứng R1 đến R15.
- Contract khớp với code ở cả hai phía.
- Tài liệu và docs/PLAN.md đã cập nhật; không để TODO mà không ghi rõ lý do.

### Lệnh

Chưa có (repo chưa được khởi tạo; tạo ở "Bước 0" trong docs/AGENT_PROMPTS.md, tương ứng giai đoạn 1 trong docs/PLAN.md). Dự kiến dùng `Makefile` với các mục tiêu sau; khi tạo xong, **cập nhật lại mục này bằng lệnh thật** và không tự bịa lệnh chưa tồn tại:

`make setup` · `make dev` · `make test` · `make lint` · `make typecheck` · `make migrate` · `make gen-api`

### Quy ước (đề xuất, người dùng có thể sửa)

- Tài liệu và thông báo hiển thị cho người dùng bằng tiếng Việt; tên biến, hàm, file, commit message bằng tiếng Anh.
- Nhánh: `main` (production), `develop`, `feature/*`; mọi thay đổi qua Pull Request và phải qua CI.
- Mỗi module backend gồm `router`, `schemas`, `models`, `service`, `repository`.

### Bản đồ tài liệu

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

---

<!-- Nguồn: docs/AGENT_PROMPTS.md -->

## Câu lệnh giao việc cho agent

> Dán từng câu lệnh vào agent theo thứ tự. Mỗi câu lệnh giả định agent đã có `AGENTS.md` và thư mục `docs/` trong repo. Thay chỗ `<...>` nếu có.
> Sau mỗi lát: bạn tự chạy thử và `git commit` trước khi giao lát tiếp theo.

### Mẫu chung cho mọi lát

```
Đọc AGENTS.md, docs/PLAN.md, docs/DECISIONS.md và các tài liệu liên quan trong bản đồ tài liệu.
Thực hiện lát <TÊN LÁT> trong docs/PLAN.md (giai đoạn F).
Trước khi viết code: nếu chưa có đặc tả thì tạo docs/specs/<ten-lat>.md từ docs/specs/_TEMPLATE.md và dừng lại để tôi duyệt.
Sau khi tôi duyệt: cập nhật contract/openapi.yaml trước, rồi backend, rồi frontend, rồi test.
Chạy lint, kiểm tra kiểu và test. Không tick việc trong PLAN.md nếu chưa đạt định nghĩa "xong".
Khi xong, tóm tắt: đã thay đổi gì, cách chạy thử để tôi kiểm tra, điểm cần tôi quyết định.
Không tự quyết các việc trong mục "Hỏi người dùng trước khi làm" của AGENTS.md.
```

### Bước 0. Khởi tạo dự án (giai đoạn 1)

```
Đọc AGENTS.md, docs/PLAN.md (giai đoạn 1), docs/ARCHITECTURE.md và docs/DECISIONS.md.
Khởi tạo monorepo FlashCard theo cây thư mục đích trong docs/ARCHITECTURE.md:
- frontend/: Expo (TypeScript strict, Expo Router, TanStack Query, Zustand, i18n tiếng Việt và tiếng Anh), chạy được trên web và mobile.
- backend/: Python FastAPI, SQLAlchemy, Alembic, pytest, ruff; cấu trúc module theo docs/ARCHITECTURE.md.
- contract/openapi.yaml: để trống khung, sẽ viết ở lát F1.
- infra/docker/docker-compose.yml: PostgreSQL có pgvector, Redis, Mailpit, MinIO.
- Makefile với các mục tiêu trong AGENTS.md (setup, dev, test, lint, typecheck, migrate, gen-api), .env.example, .gitignore.
Dùng phiên bản ổn định (stable hoặc LTS), ghi phiên bản đã chọn vào file khóa phiên bản.
Bundle ID tạm: com.example.flashcard. Chỉ làm giai đoạn 1, chưa làm tính năng.
Khi xong: cập nhật mục "Lệnh" trong AGENTS.md bằng các lệnh thật đã có, tick PLAN.md, và hướng dẫn tôi cách chạy.
```

### F1. Khung chạy xuyên suốt

```
Làm lát F1 trong docs/PLAN.md: một endpoint thật đi từ frontend qua backend tới database.
Viết contract/openapi.yaml (contract-first) cho /health và một endpoint kiểm tra kết nối database,
sinh API client cho frontend từ contract, thêm test bảo đảm backend khớp contract.
Frontend có một màn hình hiển thị trạng thái kết nối tới backend (chạy được trên web).
Thêm CI cơ bản (lint, kiểm tra kiểu, test) cho GitHub Actions.
```

### F2. Đăng ký và đăng nhập bằng email

```
Làm lát F2: đăng ký, đăng nhập bằng email và mật khẩu, duy trì và kết thúc phiên (docs/BUSINESS_FLOWS.md U1, U4; docs/SECURITY.md).
Tuân thủ quy tắc R3, R12, R15: mật khẩu băm argon2 hoặc bcrypt, access token ngắn hạn, refresh token xoay vòng và chỉ lưu dạng băm,
giới hạn số lần đăng nhập sai, thông báo lỗi không lộ email có tồn tại hay không.
Token: mobile lưu bằng secure store, web dùng cookie httpOnly (storage/session.native.ts và session.web.ts).
Màn hình 1 (đăng nhập, đăng ký) song ngữ qua i18n. Viết các test trong docs/TESTING.md liên quan xác thực.
Viết đặc tả trước và chờ tôi duyệt.
```

### F4b. Không gian học tập

```
Làm lát F4b: Không gian (docs/BUSINESS_FLOWS.md U16, docs/DATA_MODEL.md mục Không gian, màn hình 5 trong docs/SCREENS.md).
Tạo, đổi tên, xóa không gian (có xác nhận), không gian mặc định khi tải tài liệu đầu tiên. Kiểm tra quyền theo chủ sở hữu ở mọi truy vấn (R4).
```

### F5. Tải tài liệu và xử lý nền (PDF)

```
Làm lát F5: tải tài liệu PDF vào một không gian và xử lý nền đến READY (U5, docs/DATA_MODEL.md máy trạng thái, docs/AI_PIPELINE.md).
Giới hạn: 20 MB, 200 trang, 10 tài liệu mỗi người. Idempotency-Key khi tải. Worker ARQ: trích văn bản, chia đoạn theo cấu trúc, tạo embedding 768 chiều, lưu kèm số trang.
Mọi lời gọi AI qua integrations/llm_gateway và providers/gemini.py (R5), đọc tên mô hình và khóa từ cấu hình.
Hiện thông báo dữ liệu gửi cho Google ở lần tải đầu và lưu sự đồng ý (user_consents).
Khóa Gemini API: tôi sẽ đặt vào backend/.env, hãy nhắc tôi và không bao giờ in giá trị khóa ra.
Dùng nhà cung cấp AI giả (fake provider) cho test.
```

### F6. Quản lý tài liệu

```
Làm lát F6: danh sách, chi tiết, thử lại khi FAILED, xóa tài liệu, chuyển tài liệu sang không gian khác (U6).
Xóa theo máy trạng thái: DELETING ngay, dọn nền file gốc, chunk, vector, job. Lịch sử hội thoại giữ lại, trích dẫn hiện "tài liệu đã xóa".
```

### F7. Hỏi đáp trên nhiều tài liệu

```
Làm lát F7: hỏi đáp có trích dẫn, trả lời dần (streaming) trong một không gian (U7, U8; docs/AI_PIPELINE.md; docs/QUOTA_AND_RESILIENCE.md).
Truy xuất chỉ trong tài liệu READY của chủ sở hữu và thuộc không gian, lọc trước khi vào ngữ cảnh. Trích dẫn kèm tên tài liệu và số trang.
Không đủ căn cứ thì nói không tìm thấy. Hạn mức khoảng 30 câu mỗi ngày, mã lỗi hạn mức trong contract, chế độ chỉ tìm đoạn khi AI ngừng.
Thêm test mô phỏng nhà cung cấp AI trả lỗi hết hạn mức (docs/TESTING.md).
```

### F8. Xem trích dẫn và lịch sử hội thoại

```
Làm lát F8: màn hình xem trang được trích dẫn và danh sách, mở lại, xóa hội thoại (U7; màn hình 10, 11).
```

### F9. Flashcard

```
Làm lát F9: bộ thẻ, AI đề xuất thẻ rồi người học xem, sửa, bỏ chọn mới lưu (AI không tự lưu), tạo thẻ bằng tay, sửa, xóa (U11; màn hình 12, 13, 14).
Tạo thẻ tính hạn mức AI riêng với hỏi đáp. Hết hạn mức thì vẫn tạo bằng tay được.
```

### F10. Ôn tập SM-2

```
Làm lát F10: ôn tập lặp lại ngắt quãng theo SM-2 và màn hình kết quả (U12; màn hình 15, 16).
Không gọi AI. Hoạt động khi mất mạng: lưu tạm kết quả và đồng bộ sau, không ghi trùng. Viết test tính lịch SM-2.
```

### F3. Đăng nhập Google

```
Làm lát F3: đăng nhập bằng Google (U1). Backend xác thực ID token (R15). Quy tắc liên kết tài khoản: tự liên kết nếu email Google đã xác minh.
Khi cần Google OAuth client, hãy nhắc tôi tạo và hướng dẫn từng bước; không tự bịa giá trị.
```

### F4. Xác minh email và quên mật khẩu

```
Làm lát F4: xác minh email, quên và đặt lại mật khẩu (U2, U3; màn hình 2, 3). Token dùng một lần, hạn ngắn, chỉ lưu dạng băm.
Khi chạy local gửi email qua Mailpit (http://localhost:8025). Tài khoản chưa xác minh chưa được tải tài liệu.
```

### F15. Hồ sơ và cài đặt

```
Làm lát F15: ngôn ngữ giao diện, lượt hỏi còn lại, đổi mật khẩu, đăng xuất, xóa tài khoản (U4, U9, U10; màn hình 4).
```

### F11, F12, F13, F14

```
Làm lát F11 (trắc nghiệm, U13, điểm do code chấm), F12 (tóm tắt theo chương, theo yêu cầu, U15), F13 (tài liệu Word), F14 (tài liệu scan: Gemini đọc trực tiếp, Tesseract dự phòng; hãy thử trên tài liệu scan tiếng Việt thật và báo kết quả trước khi chốt).
Làm từng lát một theo mẫu chung, mỗi lát một lần giao.
```

### F16. Quản trị

```
Làm lát F16: giao diện quản trị web (A1 đến A7, màn hình 20 đến 25). API /v1/admin/*, kiểm tra vai trò ở backend, quản trị viên không xem nội dung tài liệu và hội thoại, mọi thao tác ghi audit_logs (R13).
Quản trị viên đầu tiên tạo bằng script, không có đăng ký quản trị công khai.
```

### Khi agent làm sai hoặc bị kẹt

```
Dừng lại. Đọc lại AGENTS.md, nhất là các quy tắc cứng R1 đến R15 và mục "Hỏi người dùng trước khi làm".
Cho tôi biết: bạn đang làm lát nào, đã thay đổi những file nào, điều gì đang lỗi (kèm thông báo lỗi), và đề xuất cách sửa. Chưa sửa gì cho đến khi tôi đồng ý.
```

---

<!-- Nguồn: docs/PRODUCT.md -->

## Sản phẩm và phạm vi (ứng dụng FlashCard)

> **Khi nào đọc:** trước khi làm bất kỳ tính năng nào, để biết tính năng thuộc bản nào và có nằm trong phạm vi không.

### Mô tả sản phẩm

Trợ lý học tập từ tài liệu: người dùng tải giáo trình, ghi chú, đề cương (PDF, Word, tài liệu scan); app cho phép hỏi đáp dựa trên nội dung các tài liệu đó kèm trích dẫn trang, tạo flashcard, ôn tập, làm trắc nghiệm và xem tóm tắt theo chương. Chạy trên iOS, Android và web từ một codebase frontend. Giao diện tiếng Việt và tiếng Anh; hỗ trợ tài liệu tiếng Việt và tiếng Anh.

Ngoài phạm vi: thanh toán và mọi tính năng thu phí; phát hành lên App Store, Google Play (dự án chỉ là bản thử nghiệm chạy được hoàn chỉnh trên web và mobile). Tài liệu được tổ chức theo **Không gian** (môn học hoặc chủ đề), xem U16 trong docs/BUSINESS_FLOWS.md.

### Phạm vi theo bản

**Nguyên tắc:** ưu tiên đầy đủ chức năng; số màn hình không bị giới hạn trên (tối thiểu khoảng 10 đến 15). Danh sách màn hình: docs/SCREENS.md.

| Bản | Nội dung |
|---|---|
| 1 (đầy đủ chức năng) | **Tài khoản:** đăng ký, đăng nhập bằng email và mật khẩu, Google · xác minh email, quên mật khẩu · xóa tài khoản · giao diện song ngữ Việt, Anh. **Tài liệu:** tải lên PDF và Word (khoảng 20 MB, 200 trang, 10 tài liệu mỗi người) · tài liệu scan (Gemini đọc trực tiếp, Tesseract dự phòng) · xử lý nền · quản lý (xem, thử lại, xóa) · tóm tắt theo chương. **Hỏi đáp:** trên nhiều tài liệu, có trích dẫn, trả lời dần, khoảng 30 câu mỗi ngày · xem trích dẫn · lịch sử hội thoại. **Học tập:** flashcard (AI đề xuất, người học duyệt, hoặc tạo tay) · ôn tập lặp lại ngắt quãng (SM-2) · câu hỏi trắc nghiệm. **Quản trị (web):** tổng quan sử dụng và ngân sách AI, quản lý người dùng, theo dõi job, cấu hình hạn mức, nhật ký kiểm toán |
| 2 | Chia sẻ bộ tài liệu, học nhóm · thống kê tiến độ nâng cao · nhập bằng giọng nói · tối ưu bố cục web cho máy tính · tải sẵn bộ thẻ để dùng offline hoàn chỉnh |

Luồng nghiệp vụ chi tiết của từng tính năng (người dùng và quản trị): docs/BUSINESS_FLOWS.md. Chức năng ở mức màn hình: docs/SCREENS.md.

---

<!-- Nguồn: docs/BUSINESS_FLOWS.md -->

## Quy trình nghiệp vụ

> **Khi nào đọc:** trước khi viết đặc tả (`docs/specs/`), contract hoặc code cho bất kỳ tính năng nào. File này mô tả mỗi luồng từ góc nhìn người dùng, quản trị viên và hệ thống.
>
> **Dành cho agent:** giá trị đánh dấu `[cần chốt]` chưa được quyết định, `[đề xuất]` là gợi ý chưa được người dùng xác nhận. Không tự điền; hỏi người dùng rồi ghi vào docs/DECISIONS.md. Danh sách endpoint ở cuối là **dự kiến**; `contract/openapi.yaml` mới là nguồn sự thật.

### Giá trị đã chốt (dùng cho mọi luồng)

| Mục | Giá trị |
|---|---|
| Đăng nhập | Email và mật khẩu, Google (không có Apple; dự án không phát hành lên store) |
| Xác minh email, quên mật khẩu | Có cả hai (chỉ áp dụng cho tài khoản email và mật khẩu) |
| Ngôn ngữ | Giao diện tiếng Việt và tiếng Anh; hỗ trợ tài liệu tiếng Việt và tiếng Anh |
| Giới hạn tải lên | Khoảng 20 MB mỗi file, 200 trang mỗi tài liệu, 10 tài liệu mỗi người |
| Phạm vi bản 1 | Đầy đủ chức năng: gồm flashcard, ôn tập, trắc nghiệm, tóm tắt theo chương, Word và tài liệu scan |
| Hỏi đáp | Trên nhiều tài liệu; mặc định khoảng 30 câu mỗi người mỗi ngày, tùy hạn mức AI còn lại |
| Xóa tài liệu | Giữ lịch sử hội thoại; trích dẫn hiện "tài liệu đã xóa" |
| Xóa tài khoản | Giữ bản sao lưu 30 ngày |
| Thanh toán | Không có tính năng thu phí |
| Giao diện quản trị | Có; tách riêng luồng người dùng và luồng quản trị |
| Lập lịch ôn tập | SM-2 |
| Chỉ số tải | 100 người dùng, 10 đồng thời; API p95 dưới 500 ms; chữ đầu tiên của câu trả lời trong khoảng 3 giây |

**Cấu trúc Không gian và phạm vi phát hành:** có Không gian (xem U16); chỉ bản thử nghiệm, không phát hành lên App Store, Google Play.

### Tác nhân

| Tác nhân | Vai trò |
|---|---|
| Người học | Người dùng cuối: tải tài liệu, hỏi đáp, ôn tập |
| Quản trị viên | Theo dõi sử dụng và ngân sách AI, quản lý người dùng, theo dõi job, cấu hình hạn mức |
| Hệ thống | API, worker nền (ARQ), `llm_gateway` |
| Nhà cung cấp AI | Gemini API (bên ngoài) |
| Nhà cung cấp đăng nhập | Google (bên ngoài) |
| Dịch vụ gửi email | Dùng cho xác minh email và đặt lại mật khẩu `[cần chốt: nhà cung cấp]` |

---

## Phần 1. Luồng người dùng

### Chức năng bản 1 (đầy đủ chức năng)

#### U1. Đăng ký và đăng nhập

**Email và mật khẩu**

| Bước | Ai | Hệ thống làm gì |
|---|---|---|
| 1 | Nhập email và mật khẩu | Kiểm tra định dạng, chuẩn hóa email, kiểm tra độ mạnh mật khẩu |
| 2 | | Nếu email đã tồn tại: không tiết lộ chi tiết, hướng người dùng đăng nhập hoặc đặt lại mật khẩu |
| 3 | | Băm mật khẩu (argon2 hoặc bcrypt), tạo tài khoản và danh tính đăng nhập kiểu email |
| 4 | | Gửi email xác minh (xem U2); cấp access token ngắn hạn và refresh token |

**Google**

| Bước | Ai | Hệ thống làm gì |
|---|---|---|
| 1 | Chọn đăng nhập bằng Google | App lấy ID token từ Google (mobile dùng luồng gốc; web dùng luồng OAuth chuyển hướng) |
| 2 | | Backend **xác thực ID token** (chữ ký, đối tượng nhận, hạn dùng), không tin dữ liệu do app tự gửi |
| 3 | | Tìm danh tính đã có; nếu chưa có thì tạo tài khoản mới |
| 4 | | Cấp access token và refresh token |

Quy tắc:
- **Liên kết tài khoản** khi cùng một email xuất hiện ở nhiều cách đăng nhập `[đề xuất: tự liên kết nếu email từ Google đã được xác minh; nếu không thì yêu cầu đăng nhập bằng cách cũ rồi mới liên kết; cần chốt]`.
- Giới hạn số lần đăng nhập sai (chống brute-force); thông báo lỗi không cho biết email có tồn tại hay không.

#### U2. Xác minh email (chỉ tài khoản email và mật khẩu)

1. Hệ thống gửi email chứa liên kết hoặc mã, dùng một lần, có hạn ngắn.
2. Người dùng xác nhận; tài khoản chuyển sang trạng thái đã xác minh.
3. Cho phép gửi lại, có giới hạn tần suất.
4. Tài khoản chưa xác minh bị giới hạn những gì `[cần chốt: ví dụ không cho tải tài liệu]`.

#### U3. Quên mật khẩu

1. Người dùng nhập email.
2. Hệ thống **luôn trả cùng một thông báo** (không tiết lộ email có tồn tại), nếu có thì gửi liên kết hoặc mã đặt lại: dùng một lần, hạn ngắn.
3. Người dùng đặt mật khẩu mới; mọi refresh token cũ bị thu hồi; gửi email thông báo mật khẩu đã đổi.
4. Tài khoản chỉ có Google: hướng dẫn đăng nhập bằng cách đó `[cần chốt: có cho thêm mật khẩu không]`.

#### U4. Duy trì và kết thúc phiên

- Access token hết hạn (khoảng 15 phút): app gọi refresh **một lần** rồi gửi lại yêu cầu. Refresh có xoay vòng token.
- Refresh thất bại: xóa phiên, về màn hình đăng nhập, giữ lại dữ liệu người dùng đang soạn nếu có.
- Đăng xuất: thu hồi refresh token ở backend, xóa phiên ở app.
- Tài khoản bị quản trị viên khóa: phiên bị thu hồi, đăng nhập bị từ chối kèm thông báo rõ ràng.

#### U5. Tải tài liệu lên

| Bước | Ai | Hệ thống làm gì |
|---|---|---|
| 0 | Lần đầu tải | Hiện thông báo: nội dung được gửi cho Google xử lý và có thể được dùng để cải thiện sản phẩm của họ (gói miễn phí); khuyến cáo không tải tài liệu nhạy cảm; lưu việc người dùng đã đồng ý |
| 1 | Chọn file (PDF hoặc Word .docx) | App kiểm tra sơ bộ định dạng và kích thước (tối đa khoảng 20 MB) |
| 2 | Gửi lên | Kèm `Idempotency-Key`. Backend kiểm tra quyền, định dạng thật của file (không tin đuôi file), kích thước, số trang (tối đa khoảng 200), số tài liệu đã có (tối đa 10) |
| 3 | | Lưu file gốc vào kho lưu trữ; tạo tài liệu ở `UPLOADED` và job; đưa vào hàng đợi (`QUEUED`); trả `document_id` và trạng thái ngay |
| 4 | Xem danh sách | App hiển thị trạng thái, cập nhật bằng polling hoặc thông báo |
| 5 | | Worker (`PROCESSING`): trích văn bản, chia đoạn, tạo embedding (768 chiều), lưu đoạn kèm số trang |
| 6 | | Thành công: `READY`. Lỗi: thử lại có giới hạn rồi `FAILED`. Hết hạn mức AI: `PAUSED_QUOTA`, tự chạy tiếp khi phục hồi |

Trường hợp đặc biệt:
- Sai định dạng hoặc vượt giới hạn: từ chối ngay với mã lỗi rõ ràng, nói rõ giới hạn là bao nhiêu.
- Tài liệu scan (PDF ảnh, không có lớp văn bản): xử lý theo U14.
- Word (.docx): số trang được quy đổi sau khi chuyển đổi để áp dụng giới hạn 200 trang `[cần chốt: cách tính]`.
- Mất mạng giữa chừng rồi gửi lại: `Idempotency-Key` bảo đảm không tạo tài liệu trùng.
- Tài liệu `FAILED`: người dùng được bấm thử lại (chuyển về `QUEUED`).

#### U6. Quản lý tài liệu

| Hành động | Hành vi |
|---|---|
| Xem danh sách | Chỉ thấy tài liệu của mình; hiện tên, trạng thái, thời điểm tải |
| Xem chi tiết | Trạng thái, lỗi (nếu có), số trang |
| Xóa | Chuyển `DELETING` ngay (biến mất khỏi danh sách và tìm kiếm); dọn nền file gốc, đoạn văn bản, vector, job đang chờ; xong thì xóa hẳn |
| Hội thoại cũ có trích dẫn tài liệu đã xóa | **Giữ lịch sử**; trích dẫn hiện "tài liệu đã xóa" (dùng bản ghi nhanh tên tài liệu và số trang đã lưu cùng tin nhắn) |

#### U7. Hỏi đáp trên nhiều tài liệu

| Bước | Ai | Hệ thống làm gì |
|---|---|---|
| 1 | Chọn tập tài liệu để hỏi `[cần chốt: mặc định chọn tất cả tài liệu sẵn sàng hay chọn tay]` và gõ câu hỏi | |
| 2 | | Kiểm tra hạn mức người dùng (mặc định khoảng 30 câu mỗi ngày); vượt thì trả `USER_QUOTA_EXCEEDED` kèm số lượt còn lại và thời điểm đặt lại, **không gọi AI** |
| 3 | | Kiểm tra circuit breaker; AI đang ngừng thì chuyển chế độ chỉ tìm đoạn (xem U8) |
| 4 | | Tạo embedding cho câu hỏi; tìm đoạn gần nghĩa **chỉ trong các tài liệu `READY` của chủ sở hữu và thuộc tập đã chọn**; lọc trước khi vào ngữ cảnh. Giới hạn số đoạn lấy từ mỗi tài liệu để một tài liệu không lấn át `[đề xuất]` |
| 5 | | Ghép ngữ cảnh (giới hạn số đoạn), gọi LLM, trả lời dần (streaming); chữ đầu tiên hiện trong khoảng 3 giây |
| 6 | | Câu trả lời kèm trích dẫn (tên tài liệu, số trang). Không đủ căn cứ thì nói không tìm thấy trong các tài liệu đã chọn |
| 7 | | Lưu tin nhắn kèm nguồn (có bản ghi nhanh tên tài liệu, số trang); ghi lượng dùng AI |

Lỗi: streaming bị ngắt thì gửi sự kiện lỗi kèm mã; câu hỏi quá dài thì `CONTEXT_TOO_LONG`; app giữ lại câu hỏi đã gõ để gửi lại. Ngôn ngữ trả lời theo ngôn ngữ của câu hỏi `[đề xuất]`.

#### U8. Khi AI hết hạn mức hoặc tạm ngừng

Người dùng thấy:
- Hỏi đáp: chỉ hiện các đoạn liên quan kèm tên tài liệu và số trang, không có lời giải thích do AI sinh, kèm thông báo "AI tạm nghỉ".
- Xem tài liệu, lịch sử hội thoại, flashcard có sẵn: dùng bình thường.
- Tải tài liệu mới: vẫn nhận file; tài liệu chờ xử lý (`PAUSED_QUOTA`) và tự tiếp tục khi AI hoạt động lại.
- Hết lượt cá nhân: thấy số lượt và thời điểm được dùng tiếp.
- Hạn mức mỗi người có thể được hạ xuống khi hạn mức AI toàn hệ thống còn ít `[cần chốt: cách hạ]`.

Chi tiết kỹ thuật: docs/QUOTA_AND_RESILIENCE.md.

#### U9. Xóa tài khoản

| Bước | Hệ thống làm gì |
|---|---|
| 1 | Người dùng yêu cầu xóa; yêu cầu xác nhận lại (mật khẩu, hoặc đăng nhập lại bằng Google) |
| 2 | Thu hồi mọi token; khóa tài khoản ngay |
| 3 | Xóa tài liệu theo U6, hội thoại, flashcard, nhật ký ôn tập, dữ liệu sử dụng gắn với tài khoản |
| 4 | Dữ liệu còn trong bản sao lưu được xóa theo chu kỳ, **tối đa 30 ngày**; ghi rõ trong chính sách quyền riêng tư |
| 5 | Xác nhận cho người dùng |

Nên có dù chỉ chạy thử, vì liên quan đến quyền riêng tư của người dùng.

#### U10. Ngôn ngữ giao diện

Giao diện hỗ trợ tiếng Việt và tiếng Anh. Mặc định theo ngôn ngữ thiết bị, đổi được trong cài đặt và lưu theo tài khoản. Mọi chuỗi hiển thị qua i18n, kể cả thông báo lỗi từ mã lỗi API.

#### U11. Tạo flashcard

1. Người học chọn tài liệu, chương hoặc một câu trả lời, yêu cầu tạo thẻ.
2. Kiểm tra hạn mức (tính riêng với hỏi đáp); AI đề xuất danh sách thẻ.
3. Người học **xem, sửa, bỏ chọn** rồi mới lưu. AI không tự lưu thẻ.
4. Mỗi thẻ ghi nguồn (tài liệu, trang) để quay lại đọc.

#### U12. Ôn tập lặp lại ngắt quãng (SM-2)

1. App hiện các thẻ đến hạn hôm nay.
2. Người học xem mặt trước, tự lật, tự chấm mức nhớ.
3. Hệ thống ghi nhật ký ôn tập và tính ngày ôn kế tiếp theo SM-2 hoặc biến thể gần giống; tham số chi tiết do đặc tả quyết định.
4. Luồng này **không cần AI**, nên vẫn chạy khi AI ngừng; nên hoạt động được offline và đồng bộ sau.

#### U13. Câu hỏi trắc nghiệm

AI sinh câu hỏi và đáp án đúng cùng lúc, kèm nguồn trích dẫn. Việc chấm điểm do code so khớp đáp án đã lưu, không nhờ AI chấm lại. Người học xem lại câu sai kèm nguồn.

#### U14. Tài liệu scan (không có lớp văn bản)

1. Worker phát hiện tài liệu không có lớp văn bản.
2. **Mặc định:** gửi trang cho Gemini đọc trực tiếp (miễn phí trong hạn mức, tính vào hạn mức AI); giới hạn số trang scan mỗi tài liệu vì tốn token `[cần chốt: giới hạn]`.
3. **Dự phòng:** khi hết hạn mức hoặc AI ngừng, dùng OCR chạy cục bộ (Tesseract, gói ngôn ngữ tiếng Việt và tiếng Anh) thay vì để job nằm chờ; chất lượng thấp hơn nên ghi nhận phương pháp OCR đã dùng cho từng tài liệu.
4. Hướng này cần được **thử nghiệm trên 3 đến 5 tài liệu scan tiếng Việt thật** trước khi coi là chốt hẳn (xem docs/AI_PIPELINE.md).

#### U15. Tóm tắt theo chương

1. Người học mở tài liệu `READY` và chọn xem tóm tắt theo chương.
2. Hệ thống xác định chương hoặc mục từ mục lục hoặc tiêu đề trong văn bản; nếu không có thì chia theo khoảng trang.
3. Người học yêu cầu tóm tắt từng chương `[đề xuất: tạo theo yêu cầu, không tự tạo hàng loạt; cần chốt]`. Kiểm tra hạn mức AI (tính riêng).
4. AI tóm tắt, mỗi ý kèm trang nguồn; kết quả được lưu để không tính lại.
5. Hết hạn mức AI: các tóm tắt đã lưu vẫn xem được, chưa có thì báo rõ lý do.

#### U16. Không gian học tập

**Khái niệm:** một Không gian (ví dụ "Giải tích 1") gom nhiều tài liệu và mọi thứ phát sinh từ chúng: hội thoại, bộ thẻ, trắc nghiệm, tóm tắt.

| Hành động | Hành vi |
|---|---|
| Danh sách không gian | Hiện tên, số tài liệu, số thẻ đến hạn; tạo, đổi tên, xóa |
| Tạo không gian mặc định | Khi người dùng tải tài liệu đầu tiên mà chưa có không gian: tự tạo, tên lấy theo tên tài liệu, đổi tên được |
| Tải tài liệu (U5) | Luôn thuộc đúng một không gian; tài liệu có thể chuyển sang không gian khác |
| Hỏi đáp (U7) | Thuộc một không gian; mặc định hỏi trên mọi tài liệu `READY` của không gian đó, cho chọn bớt |
| Flashcard, trắc nghiệm, tóm tắt (U11 đến U15) | Gắn với không gian; thẻ và trắc nghiệm có thể gắn thêm tài liệu nguồn |
| Xóa không gian | Có xác nhận; xóa luôn tài liệu (theo U6), hội thoại, bộ thẻ, trắc nghiệm bên trong |
| Giới hạn | Không giới hạn số không gian; vẫn giữ 10 tài liệu mỗi người tính trên toàn tài khoản |

Quy tắc: mọi truy vấn kiểm tra quyền ở cấp không gian (chủ sở hữu), truy xuất vector lọc theo không gian và chủ sở hữu trước khi vào ngữ cảnh AI.

### Bản 2 (chỉ nêu tên, chưa mô tả luồng)

Chia sẻ bộ tài liệu và học nhóm · thống kê tiến độ nâng cao · nhập bằng giọng nói · tối ưu bố cục web cho máy tính · tải sẵn bộ thẻ để dùng offline hoàn chỉnh.

---

## Phần 2. Luồng quản trị (bản 1)

> Giao diện quản trị chỉ dùng trên web `[đề xuất: nhóm route riêng trong cùng codebase frontend; cần chốt]`. API quản trị tách tiền tố `/v1/admin/`, kiểm tra vai trò ở backend; không dựa vào việc ẩn nút ở giao diện.

#### A1. Đăng nhập và phân quyền quản trị

- Có hai vai trò: người dùng và quản trị viên. Quản trị viên đầu tiên được tạo bằng script hoặc cấu hình, **không có đăng ký quản trị công khai**.
- Tài khoản quản trị dùng cùng cơ chế đăng nhập, `[cần chốt: có bắt buộc xác thực hai bước không]`.
- Mọi API quản trị kiểm tra vai trò ở backend và ghi nhật ký kiểm toán (A7).

#### A2. Tổng quan sử dụng và ngân sách AI

Màn hình tổng quan hiển thị:
- Số người dùng, số người hoạt động mỗi ngày
- Số tài liệu theo trạng thái, số job lỗi hoặc đang tạm dừng
- Số câu hỏi mỗi ngày, lượng token đã dùng, phần trăm hạn mức hoặc ngân sách AI đã dùng
- Trạng thái circuit breaker, độ dài hàng đợi
- Các chỉ số thời gian phản hồi (p95 API, thời gian tới chữ đầu tiên)

#### A3. Quản lý người dùng

| Hành động | Hành vi |
|---|---|
| Xem danh sách, tìm kiếm | Email, ngày tạo, cách đăng nhập, trạng thái, số tài liệu, mức dùng |
| Khóa, mở khóa | Khóa thì thu hồi phiên ngay; ghi lý do |
| Đặt hạn mức riêng | Tăng hoặc giảm hạn mức hỏi đáp cho một người, có thời hạn |
| Buộc đăng xuất | Thu hồi toàn bộ refresh token |
| Hỗ trợ xóa tài khoản theo yêu cầu | Thực hiện quy trình U9 |

**Quyền riêng tư `[đề xuất, cần xác nhận]`:** quản trị viên **không xem được nội dung tài liệu hay hội thoại** của người dùng, chỉ thấy siêu dữ liệu và thống kê. Nếu cần xem để hỗ trợ, phải có cơ chế riêng có sự đồng ý của người dùng và được ghi nhật ký.

#### A4. Theo dõi tài liệu và job

- Danh sách job theo trạng thái (`QUEUED`, `PROCESSING`, `FAILED`, `PAUSED_QUOTA`), kèm nguyên nhân lỗi (không kèm nội dung tài liệu).
- Thử lại job `FAILED`; kích hoạt lại job `PAUSED_QUOTA` thủ công khi hạn mức đã phục hồi (dù hệ thống cũng tự chạy lại).
- Xem độ dài hàng đợi và thời gian xử lý trung bình.

#### A5. Cấu hình hạn mức và giới hạn

Các giá trị đổi được mà không cần triển khai lại:
- Hạn mức hỏi đáp mặc định mỗi người mỗi ngày
- Giới hạn tải lên (kích thước, số trang, số tài liệu)
- Ngưỡng cảnh báo ngân sách
- Công tắc khẩn cấp để tạm tắt tính năng AI

Mọi thay đổi cấu hình ghi nhật ký kiểm toán (ai, đổi gì, giá trị cũ và mới).

#### A6. Cảnh báo

Quản trị viên nhận cảnh báo khi: ngân sách hoặc hạn mức AI chạm 50%, 80%, 100%; circuit breaker mở; hàng đợi nghẽn hoặc tỷ lệ job lỗi cao; một người dùng dùng bất thường nhiều so với trung bình. Kênh nhận `[cần chốt: email, Telegram hoặc kênh khác]`.

#### A7. Nhật ký kiểm toán

- Mọi thao tác quản trị (khóa người dùng, đổi hạn mức, đổi cấu hình, thử lại job) ghi: ai, làm gì, trên đối tượng nào, lúc nào, giá trị cũ và mới.
- Nhật ký chỉ thêm, không sửa hay xóa qua ứng dụng.
- Quản trị viên xem và lọc được nhật ký.

---

## Bảng luồng và endpoint dự kiến

Dùng làm điểm xuất phát khi viết `contract/openapi.yaml`; tên cụ thể do contract quyết định.

| Luồng | Endpoint dự kiến |
|---|---|
| U1 | `POST /v1/auth/register`, `/login`, `/google` |
| U2 | `POST /v1/auth/verify-email`, `/resend-verification` |
| U3 | `POST /v1/auth/forgot-password`, `/reset-password` |
| U4 | `POST /v1/auth/refresh`, `/logout` |
| U5 | `POST /v1/documents` (kèm `Idempotency-Key`) |
| U5, U6 | `GET /v1/documents`, `GET /v1/documents/{id}`, `POST /v1/documents/{id}/retry`, `DELETE /v1/documents/{id}` |
| U7 | `POST /v1/conversations`, `POST /v1/conversations/{id}/messages` (streaming, kèm danh sách `document_ids`), `GET /v1/conversations/{id}` |
| U8 | Mã lỗi `AI_TEMPORARILY_UNAVAILABLE`, `AI_RATE_LIMITED`, `USER_QUOTA_EXCEEDED`, `CONTEXT_TOO_LONG` ở mọi endpoint gọi AI; `GET /v1/usage/me` cho số lượt còn lại |
| U9 | `DELETE /v1/account` |
| U10 | `PATCH /v1/me` (ngôn ngữ ưa thích) |
| U11 | `POST /v1/flashcards/suggestions`, `POST /v1/flashcards` |
| U12 | `GET /v1/reviews/due`, `POST /v1/reviews` |
| U13 | `POST /v1/quizzes`, `POST /v1/quizzes/{id}/answers` |
| U15 | `POST /v1/documents/{id}/summaries`, `GET /v1/documents/{id}/summaries` |
| A2 | `GET /v1/admin/overview` |
| A3 | `GET /v1/admin/users`, `POST /v1/admin/users/{id}/block`, `/unblock`, `/revoke-sessions`, `PUT /v1/admin/users/{id}/quota` |
| A4 | `GET /v1/admin/jobs`, `POST /v1/admin/jobs/{id}/retry` |
| A5 | `GET /v1/admin/settings`, `PUT /v1/admin/settings` |
| A7 | `GET /v1/admin/audit-logs` |
| U16 | `GET/POST /v1/spaces`, `GET/PATCH/DELETE /v1/spaces/{id}`, `POST /v1/documents/{id}/move`; các endpoint tài liệu, hội thoại, bộ thẻ, trắc nghiệm nhận `space_id` |

---

<!-- Nguồn: docs/SCREENS.md -->

## Danh sách màn hình

> **Khi nào đọc:** trước khi dựng giao diện hoặc viết đặc tả có màn hình. Mỗi màn hình liên kết với luồng trong docs/BUSINESS_FLOWS.md.
>
> **Dành cho agent:** đây là danh sách chức năng ở mức màn hình, **chưa có thiết kế hình ảnh**. Số lượng màn hình không phải mục tiêu cần tối thiểu hóa; điều quan trọng là đủ chức năng. Mọi chuỗi hiển thị đi qua i18n (tiếng Việt và tiếng Anh).

### Quy tắc chung cho mọi màn hình

- Mỗi màn hình có đủ các trạng thái: đang tải, rỗng (có hướng dẫn việc cần làm tiếp), lỗi (có nút thử lại), thành công.
- Lỗi hạn mức AI (`USER_QUOTA_EXCEEDED`, `AI_TEMPORARILY_UNAVAILABLE`, `AI_RATE_LIMITED`, `CONTEXT_TOO_LONG`) hiển thị thông báo thân thiện, không hiển thị mã kỹ thuật; hiện số lượt còn lại và thời điểm đặt lại khi có.
- Màn hình dùng chung cho mobile và web, bố cục thích ứng: mobile dùng tab dưới, web dùng thanh bên.
- Điều hướng chính của người dùng: **Không gian**, **Thẻ học**, **Hồ sơ**. Tài liệu, Hỏi đáp, Thẻ, Trắc nghiệm nằm trong từng không gian (các tab).
- Màn hình quản trị chỉ có trên web, chỉ vai trò admin vào được.
- Không hiển thị nội dung của người dùng khác ở bất kỳ màn hình nào.

### Người dùng (mobile và web)

#### Tài khoản

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 1 | Đăng nhập và đăng ký | U1 | Hai tab; nhập email và mật khẩu; nút đăng nhập Google; liên kết sang quên mật khẩu | Sai thông tin (thông báo chung), bị giới hạn số lần thử, tài khoản bị khóa |
| 2 | Quên và đặt lại mật khẩu | U3 | Nhập email, nhập mã hoặc mở liên kết, đặt mật khẩu mới | Thông báo luôn giống nhau dù email có tồn tại hay không; token hết hạn hoặc đã dùng |
| 3 | Xác minh email | U2 | Hướng dẫn kiểm tra email, nút gửi lại (có giới hạn tần suất) | Chưa xác minh bị giới hạn chức năng (chưa chốt) |
| 4 | Hồ sơ và cài đặt | U4, U9, U10 | Ngôn ngữ giao diện, lượt hỏi còn lại hôm nay, đổi mật khẩu, đăng xuất, xóa tài khoản (xác nhận lại) | Xóa tài khoản cần xác nhận lại bằng mật khẩu hoặc Google |

#### Tài liệu

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 5 | Danh sách không gian và Chi tiết không gian | U6, U16 | Danh sách không gian (tên, số tài liệu, thẻ đến hạn; tạo, đổi tên, xóa); trong một không gian là các tab Tài liệu, Hỏi đáp, Thẻ, Trắc nghiệm. Tab Tài liệu: danh sách tài liệu, trạng thái xử lý, nút tải lên, mở chi tiết | Rỗng; đạt giới hạn 10 tài liệu; tài liệu `FAILED` và `PAUSED_QUOTA` có nhãn riêng |
| 6 | Tải tài liệu | U5 | Chọn file PDF hoặc Word; ở lần đầu hiện thông báo dữ liệu gửi cho Google và xin đồng ý; hiện giới hạn (khoảng 20 MB, 200 trang) | Sai định dạng, quá lớn, quá nhiều trang, mất mạng giữa chừng, file scan |
| 7 | Chi tiết tài liệu | U6, U15 | Tên, trạng thái, số trang, lỗi; thử lại, xóa; các lối tắt: hỏi đáp, tạo thẻ, tạo trắc nghiệm, xem tóm tắt | `DELETING` hiển thị đang xóa; tài liệu chưa `READY` khóa các lối tắt |
| 8 | Tóm tắt theo chương | U15 | Danh sách chương, nút tạo tóm tắt, nội dung tóm tắt kèm trang nguồn | Tóm tắt tốn hạn mức; chưa tạo thì hiện nút tạo |

#### Hỏi đáp

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 9 | Hỏi đáp | U7, U8 | Chọn tập tài liệu, khung chat, câu trả lời hiện dần, trích dẫn bấm được, số lượt còn lại | Hết lượt; AI tạm nghỉ thì chỉ hiện các đoạn liên quan; không tìm thấy trong tài liệu; luồng bị ngắt |
| 10 | Xem trích dẫn | U7 | Mở đúng trang tài liệu được trích, đánh dấu đoạn liên quan | Tài liệu đã xóa thì hiện "tài liệu đã xóa" |
| 11 | Lịch sử hội thoại | U7 | Danh sách hội thoại, mở lại, xóa hội thoại | Rỗng |

#### Học tập

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 12 | Bộ thẻ | U11, U12 | Danh sách bộ thẻ, số thẻ đến hạn hôm nay, nút bắt đầu ôn, nút tạo bộ mới | Rỗng; không có thẻ đến hạn |
| 13 | Tạo thẻ | U11 | Chọn nguồn (tài liệu, chương hoặc một câu trả lời), AI đề xuất danh sách thẻ, **người học xem, sửa, bỏ chọn rồi mới lưu**; có chế độ tạo thẻ bằng tay | Hết hạn mức AI thì chỉ cho tạo bằng tay; thẻ ghi nguồn (tài liệu, trang) |
| 14 | Chi tiết bộ thẻ | U11 | Danh sách thẻ, sửa, xóa, thêm thẻ, xem nguồn | Rỗng |
| 15 | Ôn tập | U12 | Hiện mặt trước, lật thẻ, tự chấm mức nhớ theo SM-2, tiến độ phiên | Không cần AI nên vẫn dùng khi AI ngừng; mất mạng thì lưu tạm kết quả và gửi sau |
| 16 | Kết quả ôn tập | U12 | Tổng kết phiên, thẻ khó, ngày ôn kế tiếp | |
| 17 | Tạo trắc nghiệm | U13 | Chọn tài liệu hoặc chương, số câu | Tốn hạn mức AI; hết hạn mức thì báo rõ |
| 18 | Làm trắc nghiệm | U13 | Từng câu hỏi, chọn đáp án, tiến độ | Thoát giữa chừng thì hỏi có lưu không |
| 19 | Kết quả trắc nghiệm | U13 | Điểm, xem lại câu sai kèm nguồn trích dẫn; điểm do code chấm, không nhờ AI chấm lại | |

### Quản trị (chỉ web)

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 20 | Tổng quan | A2 | Số người dùng, tài liệu theo trạng thái, số câu hỏi mỗi ngày, % hạn mức hoặc ngân sách AI, trạng thái circuit breaker, độ dài hàng đợi, p95 | Cảnh báo hiện nổi bật khi vượt ngưỡng |
| 21 | Danh sách người dùng | A3 | Tìm kiếm, lọc; cột email, cách đăng nhập, trạng thái, số tài liệu, mức dùng | |
| 22 | Chi tiết người dùng | A3 | Khóa, mở khóa, đặt hạn mức riêng, buộc đăng xuất; **không hiển thị nội dung tài liệu và hội thoại** (chờ xác nhận) | Mọi thao tác ghi nhật ký kiểm toán |
| 23 | Theo dõi job | A4 | Job theo trạng thái, nguyên nhân lỗi (không kèm nội dung), thử lại, kích hoạt lại job `PAUSED_QUOTA` | |
| 24 | Cấu hình | A5 | Hạn mức mặc định, giới hạn tải lên, ngưỡng cảnh báo, công tắc khẩn cấp tắt AI | Hiện giá trị cũ và mới trước khi lưu |
| 25 | Nhật ký kiểm toán | A7 | Danh sách thao tác quản trị, lọc theo người, hành động, thời gian | Chỉ xem, không sửa |

**Tổng cộng 25 màn hình:** 19 màn hình người dùng và 6 màn hình quản trị. Màn hình ở nhóm Tài khoản và Hỏi đáp là nền tảng; nhóm Học tập là phần tạo giá trị chính của một trợ lý học tập.

**Ghi chú về Không gian:** màn hình 5 gộp danh sách không gian và chi tiết không gian; các màn hình 7 đến 19 mở từ trong một không gian. Có thể tách thành màn hình riêng khi dựng nếu cần. Bản phác giao diện tham khảo: 4 màn hình (danh sách không gian, chi tiết không gian, hỏi đáp, ôn tập) đã được duyệt hướng ban đầu.

---

<!-- Nguồn: docs/ARCHITECTURE.md -->

## Kiến trúc

> **Khi nào đọc:** trước khi tạo thư mục, module hoặc thay đổi cách các phần giao tiếp với nhau.

### Tổng quan

```
Client (Expo: iOS, Android, Web)
        │  HTTPS (REST theo contract/openapi.yaml, streaming cho hỏi đáp)
        ▼
API (FastAPI, modular monolith)  ──►  Gemini API (qua llm_gateway / providers)
   │            │
   ▼            ▼
PostgreSQL     Redis ◄── Worker nền (xử lý tài liệu)
(+ pgvector)   (cache, hàng đợi)
   │
Object storage (file gốc)
```

Nguyên tắc: bắt đầu bằng modular monolith, chỉ tách microservices khi **đo được** một module cần scale riêng hoặc team đã đủ lớn.

### Ranh giới Frontend và Backend

| Từ | Được dùng | Không được dùng |
|---|---|---|
| `frontend` | Gọi API theo `contract/openapi.yaml`; client sinh tự động | Import code từ `backend` |
| `backend` | Thư viện của chính nó | Import code từ `frontend` |
| `contract` | Chỉ mô tả API | Chứa logic |

Quy tắc hợp đồng:
- `contract/openapi.yaml` là nguồn sự thật duy nhất về endpoint, dữ liệu vào/ra, mã lỗi.
- Thứ tự khi API đổi: sửa contract, rồi backend, rồi sinh lại client cho frontend.
- `frontend/src/api/generated/` do công cụ sinh ra, không sửa tay.
- CI kiểm tra thay đổi phá vỡ (breaking change) giữa phiên bản contract mới và cũ.
- Quy ước chung (đặt tên, mã lỗi, phân trang, phiên bản `/v1`, mô tả streaming) ghi trong `contract/README.md`.

### Phân lớp trong backend

Mỗi module gồm `router` (nhận request) → `service` (logic nghiệp vụ) → `repository` (truy cập dữ liệu) → `models`; `schemas` là dữ liệu vào/ra khớp với contract.
- Router không chứa logic nghiệp vụ; service không viết truy vấn trực tiếp.
- Module này không đọc thẳng bảng của module khác; gọi qua service của module đó.
- Dịch vụ bên ngoài (object storage, email, LLM) chỉ được gọi qua `integrations/`.

### Phân lớp trong frontend

- `app/`: định tuyến, chỉ ghép màn hình.
- `features/`: mỗi nghiệp vụ một thư mục (giao diện, hook, gọi API của nghiệp vụ đó).
- `components/`: UI dùng chung, không biết gì về nghiệp vụ.
- `api/`: lớp duy nhất được phép gọi mạng. Màn hình không gọi mạng trực tiếp.
- `storage/`: lưu phiên đăng nhập, tách cài đặt theo nền tảng (`.native.ts` dùng secure store, `.web.ts` dùng cookie `httpOnly` do backend đặt). Không lưu token vào AsyncStorage hay `localStorage`.

### Cây thư mục tổng thể (đích, tạo dần theo giai đoạn)

```
study-assistant/
├── contract/
│   └── openapi.yaml                   # hợp đồng API, nguồn sự thật duy nhất
├── frontend/                          # Expo: iOS, Android, Web
│   ├── app/                           # (auth), (tabs): thư viện, hỏi đáp, ôn tập, hồ sơ; (admin): chỉ web
│   ├── src/
│   │   ├── features/                  # auth, documents, chat, flashcards, quizzes, profile
│   │   ├── components/                # ui, forms, feedback, layout
│   │   ├── api/                       # generated/, client.ts, errors.ts, streaming.ts
│   │   ├── hooks/  store/  storage/  theme/  config/  types/  utils/
│   ├── tests/                         # unit, components, integration
│   ├── e2e/                           # Maestro hoặc Detox (chỉ một nơi)
│   └── app.config.ts
├── backend/                           # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                       # router gốc, chuẩn hóa lỗi, middleware
│   │   ├── core/                      # config, security, logging, metrics, rate_limit, exceptions
│   │   ├── db/                        # session, base, migrations/
│   │   ├── modules/
│   │   │   ├── auth/  users/  documents/  chat/  study/  usage/  admin/
│   │   │   │   (mỗi module: router, schemas, models, service, repository, dependencies)
│   │   │   └── ai/
│   │   │       ├── providers/  ingestion/  retrieval/   # providers/gemini.py là nhà cung cấp mặc định
│   │   │       ├── prompts/  guardrails/  services/
│   │   │       └── usage.py           # ghi nhận mỗi lần gọi AI
│   │   ├── integrations/              # object_storage, email, llm_gateway (retry, circuit breaker)
│   │   └── workers/                   # queue, tasks, document_tasks
│   ├── tests/                         # unit, integration, api, security, fixtures
│   ├── evals/                         # datasets/, test_retrieval.py, test_answers.py
│   ├── scripts/                       # healthcheck, cleanup_jobs
│   ├── pyproject.toml  alembic.ini  Dockerfile
├── infra/
│   ├── docker/                        # docker-compose (và bản test), postgres, redis
│   ├── nginx/
│   └── monitoring/                    # prometheus, grafana
├── docs/
│   ├── architecture/  adr/  api/  security/  runbooks/
├── .github/workflows/
├── .env.example  Makefile  README.md
```

Lưu ý: `modules/usage/` quản lý hạn mức ba tầng, thống kê và cảnh báo ngân sách; `modules/ai/usage.py` chỉ ghi nhận từng lần gọi AI.

### Giao diện quản trị và triển khai

- Giao diện quản trị chỉ dùng trên web, đặt trong nhóm route `(admin)` của cùng codebase frontend (đề xuất, chờ xác nhận); chỉ vai trò admin vào được.
- API quản trị nằm dưới `/v1/admin/`, có nhóm (tag) riêng trong `contract/openapi.yaml`, kiểm tra vai trò ở backend.
- Triển khai trên Railway: API, worker ARQ, PostgreSQL có pgvector, Redis, kho file (docs/OPERATIONS.md).
- Frontend hỗ trợ tiếng Việt và tiếng Anh qua i18n; mọi chuỗi hiển thị đi qua i18n.

### Tham chiếu: các kiến trúc đã cân nhắc

#### Kiến trúc hệ thống (chia và triển khai thế nào)

| Kiến trúc | Mô tả ngắn | Phù hợp khi |
|---|---|---|
| Monolith | Một codebase, một lần deploy | Team nhỏ, sản phẩm mới |
| Modular monolith | Monolith chia module rõ ràng, module giao tiếp qua cổng riêng | Muốn dễ tách service sau này |
| Microservices | Nhiều service nhỏ, DB riêng, deploy độc lập | Nhiều team, hệ thống lớn |
| Event-driven | Giao tiếp bất đồng bộ qua sự kiện (Kafka, RabbitMQ) | Nhiều bước xử lý nền, tải lớn |
| Serverless | Viết hàm, nhà cung cấp lo hạ tầng | Tải thất thường, tác vụ ngắn |
| Cloud-native | Docker, Kubernetes, CI/CD, hạ tầng dưới dạng code | Vận hành ổn định ở quy mô lớn |

#### Mẫu tổ chức code (bên trong một service hoặc app)

| Mẫu | Ý chính | Hay gặp ở |
|---|---|---|
| MVC | Controller điều phối Model và View | Web backend (Rails, Django, Laravel, Spring) |
| MVP | View chỉ hiển thị, Presenter điều khiển hai chiều | Android cũ, desktop |
| MVVM | ViewModel giữ state, View tự cập nhật | Mobile hiện đại, Vue, Angular |
| Flux/Redux | Một store, luồng dữ liệu một chiều | Frontend phức tạp |
| Clean/Hexagonal | Lõi nghiệp vụ không phụ thuộc framework | Service cần dễ test, dễ đổi công nghệ |

#### Ghép cho dự án này

| Tầng | Lựa chọn |
|---|---|
| App di động | React Native: component + custom hook (gần MVVM) + TanStack Query |
| Cổng vào | API Gateway hoặc BFF (gom dữ liệu cho mobile) |
| Backend | FastAPI modular monolith, mỗi module gồm router, schemas, models, service, repository, trả JSON |
| Dữ liệu | PostgreSQL (pgvector), Redis, hàng đợi Celery/ARQ, kho lưu file (S3 hoặc R2) |
| Hướng phát triển | Tách microservices khi đo được nhu cầu thật |

Quy tắc nếu sau này tách microservices: mỗi service có database riêng, không truy vấn thẳng bảng của service khác, giao tiếp qua REST/gRPC hoặc event.

---

<!-- Nguồn: docs/DATA_MODEL.md -->

## Mô hình dữ liệu và trạng thái tài liệu

> **Khi nào đọc:** khi viết migration, model, repository, worker xử lý tài liệu, hoặc bất kỳ chỗ nào đổi trạng thái tài liệu.

### Thiết kế dữ liệu (PostgreSQL + pgvector)

File gốc (PDF, ảnh) lưu ở object storage tương thích S3; PostgreSQL lưu metadata, trạng thái, nội dung đoạn và vector.

| Bảng | Dữ liệu chính | Mục đích |
|---|---|---|
| `users` | ID, email, password hash, thời điểm tạo | Danh tính người dùng |
| `documents` | Owner, tên file, storage key, trạng thái | Quản lý tài liệu |
| `document_chunks` | Document ID, nội dung, số trang, embedding | Tìm đoạn liên quan và trích dẫn |
| `document_jobs` | Loại job, trạng thái, số lần thử, lỗi | Theo dõi và phục hồi tác vụ nền |
| `conversations` | Owner, tiêu đề, thời điểm tạo | Gom nhóm hội thoại |
| `messages` | Conversation ID, role, nội dung, citations | Lịch sử hỏi đáp |
| `flashcards` | Mặt trước, mặt sau, nguồn tạo | Quản lý thẻ học |
| `review_logs` | Thời điểm ôn, kết quả, đánh giá | Theo dõi tiến độ ôn tập |
| `ai_usage` | Model, token, thời gian, chi phí ước tính | Kiểm soát ngân sách AI |

Quan hệ chính:
- `users` có nhiều `documents`; mỗi `documents` có nhiều `document_chunks` và `document_jobs`
- `users` có nhiều `conversations`; mỗi `conversations` có nhiều `messages`
- `users` có nhiều `flashcards`; mỗi `flashcards` có nhiều `review_logs`
- `users` có nhiều bản ghi `ai_usage`

Quy tắc thiết kế:
- **Khóa ngoại:** `documents.owner_id` → `users.id`; `document_chunks.document_id` → `documents.id`; `messages.conversation_id` → `conversations.id`; `review_logs.flashcard_id` → `flashcards.id`.
- **Index nên có:** unique cho email đã chuẩn hóa; `documents(owner_id, created_at)`; `document_chunks(document_id)`; `messages(conversation_id, created_at)`; vector index phù hợp cách truy xuất đã chọn. Không thêm index máy móc cho mọi cột, kiểm tra theo truy vấn thực tế.
- **Embedding:** số chiều cố định theo mô hình. Lưu tên và số chiều mô hình cùng dữ liệu; đổi mô hình nghĩa là tạo lại toàn bộ vector, cần có kế hoạch chuyển đổi.
- **Migration:** dùng Alembic, không sửa schema production thủ công; thay đổi ưu tiên tương thích ngược, thử trên staging trước.
- **Xóa dữ liệu:** khi người dùng xóa tài liệu, phải xử lý file gốc, chunk, vector và job đang chờ. Nếu xóa bất đồng bộ thì dùng trạng thái `DELETING` để tài liệu đó không còn xuất hiện trong tìm kiếm.

### Máy trạng thái của tài liệu

| Trạng thái | Ý nghĩa | Chuyển được sang |
|---|---|---|
| `UPLOADED` | File đã lưu, chưa vào hàng đợi | `QUEUED` |
| `QUEUED` | Đang chờ worker | `PROCESSING`, `DELETING` |
| `PROCESSING` | Đang trích văn bản, chia đoạn, tạo embedding | `READY`, `FAILED`, `PAUSED_QUOTA`, `DELETING` |
| `READY` | Sẵn sàng hỏi đáp | `DELETING` |
| `FAILED` | Lỗi sau số lần thử cho phép | `QUEUED` (thử lại), `DELETING` |
| `PAUSED_QUOTA` | Tạm dừng vì AI hết hạn mức, chờ phục hồi | `QUEUED` (tự động khi hạn mức phục hồi), `DELETING` |
| `DELETING` | Đang dọn dữ liệu | Xóa hẳn |

Quy tắc:
- API upload trả về `document_id` và trạng thái ban đầu ngay, không chờ xử lý xong.
- Chỉ cho phép các chuyển trạng thái ở bảng trên; cập nhật có điều kiện theo trạng thái hiện tại để **job cũ không ghi đè trạng thái mới**.
- Chỉ tài liệu `READY` mới được đưa vào tìm kiếm; worker kiểm tra lại trạng thái trước các thao tác nhạy cảm, đặc biệt khi tài liệu đã bị xóa.
- Lỗi và số lần thử ghi vào `document_jobs`; thử lại có giới hạn và không tạo dữ liệu trùng.
- `PAUSED_QUOTA` không tính vào số lần thử và không chuyển sang `FAILED`; job tự chạy lại khi hạn mức phục hồi (xem docs/QUOTA_AND_RESILIENCE.md).

### Bảng và cột bổ sung cho xác thực, quản trị và đồng ý (đề xuất)

Cần cho các luồng U1 đến U4, U5 và nhóm A trong docs/BUSINESS_FLOWS.md. Đây là đề xuất thiết kế, agent có thể điều chỉnh khi viết đặc tả nhưng phải nêu lý do.

| Bảng | Dữ liệu chính | Mục đích |
|---|---|---|
| `auth_identities` | User ID, nhà cung cấp (email, google), mã định danh từ nhà cung cấp, email do nhà cung cấp trả về, đã xác minh hay chưa | Một người dùng có nhiều cách đăng nhập |
| `refresh_tokens` | User ID, mã băm token, hạn dùng, thời điểm thu hồi, thông tin thiết bị | Xoay vòng và thu hồi phiên |
| `email_tokens` | User ID, loại (xác minh, đặt lại mật khẩu), mã băm, hạn, đã dùng chưa | Token một lần |
| `user_consents` | User ID, loại đồng ý (gửi dữ liệu cho nhà cung cấp AI), phiên bản văn bản, thời điểm | Chứng minh đã thông báo và được đồng ý |
| `user_quota_overrides` | User ID, hạn mức riêng, thời hạn, người đặt | Ngoại lệ do quản trị viên đặt |
| `app_settings` | Khóa, giá trị, người sửa, thời điểm | Cấu hình đổi được không cần triển khai (hạn mức, giới hạn tải lên, công tắc AI) |
| `flashcard_decks` | Owner, tên, tài liệu nguồn (nếu có) | Gom thẻ thành bộ |
| `document_summaries` | Tài liệu, chương hoặc khoảng trang, nội dung tóm tắt, trang nguồn, mô hình, thời điểm | Lưu tóm tắt để không tính lại |
| `quizzes` | Owner, tài liệu nguồn, số câu, thời điểm | Bộ câu hỏi trắc nghiệm |
| `quiz_questions` | Quiz ID, nội dung câu hỏi, các đáp án, đáp án đúng, trích dẫn nguồn | Câu hỏi và đáp án đúng lưu cùng lúc khi sinh |
| `quiz_attempts` | Quiz ID, User ID, câu trả lời, điểm, thời điểm | Kết quả làm bài, điểm do code chấm |
| `audit_logs` | Người thực hiện, hành động, đối tượng, giá trị cũ và mới, thời điểm | Nhật ký kiểm toán, chỉ thêm |

Cột bổ sung cho `flashcards` (lập lịch SM-2): `deck_id`, `ease_factor`, `interval_days`, `repetitions`, `due_at`.

Cột bổ sung cho `users`: `role` (user, admin), `status` (active, blocked), `locale` (vi, en), `email_verified_at`, `deleted_at`.

Quy tắc:
- Token (refresh, xác minh email, đặt lại mật khẩu) **chỉ lưu dạng băm**, không lưu thô.
- `document_chunks.embedding` là vector 768 chiều; lưu tên mô hình embedding cùng dữ liệu.
- **Trích dẫn khi xóa tài liệu:** mỗi trích dẫn trong `messages` lưu bản ghi nhanh (tên tài liệu, số trang) và `document_id` cho phép rỗng. Khi tài liệu bị xóa, lịch sử hội thoại vẫn còn và giao diện hiện "tài liệu đã xóa".
- `audit_logs` không có thao tác sửa hay xóa qua ứng dụng.
- Xóa tài khoản: xóa dữ liệu theo docs/BUSINESS_FLOWS.md (U9); bản sao lưu giữ tối đa 30 ngày.

### Không gian (spaces)

| Bảng | Dữ liệu chính | Mục đích |
|---|---|---|
| `spaces` | ID, owner_id, tên, thời điểm tạo, thời điểm cập nhật | Gom tài liệu và học liệu theo môn hoặc chủ đề |

Thêm cột `space_id` (bắt buộc, khóa ngoại tới `spaces.id`) vào `documents`, `conversations`, `flashcard_decks`, `quizzes`, `document_summaries`.

Quy tắc:
- Mỗi tài liệu thuộc đúng một không gian; chuyển không gian là đổi `space_id` của tài liệu (chunk đi theo tài liệu).
- Truy xuất vector lọc theo `space_id` và `owner_id`; chỉ tài liệu `READY`.
- Xóa không gian: dọn tài liệu theo quy trình xóa tài liệu (trạng thái `DELETING`), rồi hội thoại, bộ thẻ, trắc nghiệm.
- Index nên có: `spaces(owner_id)`, `documents(space_id)`.

---

<!-- Nguồn: docs/AI_PIPELINE.md -->

## Pipeline AI, RAG và Gemini

> **Khi nào đọc:** khi làm module `ai`, nạp tài liệu, truy xuất, hỏi đáp, tạo flashcard, hoặc đụng đến nhà cung cấp AI và embedding.

### Hai luồng chính

| Luồng | Các bước | Chạy ở đâu |
|---|---|---|
| Nạp tài liệu | Tải lên, trích văn bản, chia đoạn nhỏ, tạo embedding, lưu vào pgvector kèm số trang | Worker nền; app hiển thị trạng thái đang xử lý, sẵn sàng, lỗi |
| Hỏi đáp | Câu hỏi, truy xuất đoạn gần nghĩa (chỉ trong tài liệu của người dùng), LLM soạn câu trả lời, trả về kèm trích dẫn | API, streaming về app |

### Nguyên tắc riêng của dự án (quy tắc bắt buộc)

- Mọi câu trả lời kèm nguồn; không đủ căn cứ thì nói "không tìm thấy trong tài liệu", không đoán
- Truy xuất luôn lọc theo chủ sở hữu tài liệu, tuyệt đối không để lộ tài liệu của người khác
- Chia đoạn theo cấu trúc (chương, mục) có chồng lấn nhỏ, lưu số trang
- Coi nội dung trong tài liệu là dữ liệu không đáng tin, không để nó điều khiển chỉ dẫn hệ thống (prompt injection)
- Giới hạn kích thước file, số trang, số tài liệu, số lượt hỏi mỗi ngày
- Flashcard do AI tạo phải cho người dùng xem và sửa trước khi lưu
- Thử embedding và OCR trên tài liệu tiếng Việt thật trước khi chốt mô hình
- Bộ câu hỏi mẫu (`evals/`) chạy lại mỗi khi đổi prompt hoặc đổi mô hình
- Soạn điều khoản sử dụng: người dùng chỉ tải tài liệu mình có quyền dùng; bản đầu không chia sẻ công khai
- Theo dõi token và chi phí AI theo từng người dùng

### Dùng Gemini API bản miễn phí (Google AI Studio)

**Quyết định:** dùng khóa Gemini API từ Google AI Studio ở gói miễn phí làm nhà cung cấp AI mặc định, cho cả sinh câu trả lời lẫn embedding. Chuyển sang gói trả phí là **tùy chọn, không phải điều kiện bắt buộc**; thiết kế phải cho phép chuyển bất kỳ lúc nào mà không sửa code.

**Hệ quả của việc dùng gói miễn phí** (theo điều khoản của Google tại thời điểm tra cứu cuối tháng 10/2026, nên đọc lại định kỳ):
- Với dịch vụ không trả phí (Google AI Studio và hạn mức miễn phí của Gemini API), nội dung gửi lên và câu trả lời sinh ra có thể được Google dùng để cải thiện sản phẩm, và người đánh giá có thể đọc.
- Gói trả phí thì không dùng dữ liệu để cải thiện sản phẩm. Ở khu vực EEA, Thụy Sĩ và Anh, điều khoản của gói trả phí áp dụng cho mọi dịch vụ kể cả bản miễn phí.
- Giới hạn tốc độ của gói miễn phí thấp và thay đổi theo mô hình, theo thời gian; xem trang giới hạn trong AI Studio, không dựa vào con số cũ.

**Cách giảm thiểu rủi ro dữ liệu khi vẫn dùng gói miễn phí**
- Thông báo rõ trước khi người dùng tải tài liệu và xin đồng ý: nội dung được gửi cho Google xử lý và có thể được dùng để cải thiện sản phẩm của họ.
- Khuyến cáo không tải tài liệu nhạy cảm (thông tin cá nhân, y tế, tài chính, tài liệu mật).
- Không đưa thông tin định danh không cần thiết (email, tên, ID người dùng) vào prompt; chỉ gửi nội dung tối thiểu cần để trả lời.
- Ghi log không chứa khóa API hoặc nội dung nhạy cảm.
- Ghi điều khoản sử dụng: người dùng chỉ tải tài liệu mình có quyền dùng.

**Tận dụng giới hạn tốc độ để kiểm thử:** cố ý chạm giới hạn rồi quan sát retry, circuit breaker, `PAUSED_QUOTA` và thông báo trên app (docs/QUOTA_AND_RESILIENCE.md). Đặt hạn mức người dùng nội bộ thấp hơn giới hạn của nhà cung cấp để hệ thống tự chặn trước khi nhà cung cấp chặn.

**Thiết kế để chuyển gói bất kỳ lúc nào**
- Mọi khác biệt giữa hai gói chỉ nằm ở khóa API và cấu hình (tên mô hình, giới hạn tốc độ, ngân sách hệ thống); không viết cứng trong code.
- Mọi lời gọi AI đi qua `providers/gemini.py` và `llm_gateway`; hạn mức ba tầng ở docs/QUOTA_AND_RESILIENCE.md đọc giới hạn từ cấu hình.
- Nếu giữ nguyên mô hình embedding và số chiều thì vector đã lưu vẫn dùng được sau khi đổi gói, không phải tạo lại.
- Khi cần chuyển: tạo khóa gói trả phí và liên kết thanh toán, đặt cảnh báo ngân sách tại Google Cloud (kiểm tra xem có đặt được trần cứng không), thay khóa trong secrets manager, nâng giới hạn trong cấu hình, cập nhật thông báo quyền riêng tư, rồi chạy lại các kịch bản hạn mức ở docs/TESTING.md.
- Tín hiệu nên cân nhắc chuyển: hay chạm giới hạn tốc độ, lượng người dùng tăng, người dùng hoặc đối tác yêu cầu cam kết về dữ liệu, hoặc cần phục vụ thị trường có quy định chặt về dữ liệu.

**Quản lý khóa API**
- Khóa chỉ nằm ở backend (biến môi trường hoặc secrets manager), không bao giờ nhúng vào app.
- Mỗi môi trường (dev, staging, production) dùng khóa riêng.
- Không commit khóa lên Git, không dán vào chat hay tài liệu; nghi ngờ bị lộ thì thu hồi và tạo khóa mới ngay.

**Embedding (`gemini-embedding-001`)**
- Hỗ trợ hơn 100 ngôn ngữ và nhận tối đa khoảng 2048 token đầu vào, nên mỗi đoạn (chunk) phải nằm trong giới hạn này. Vẫn thử trên tài liệu tiếng Việt thật như đã nêu ở docs/AI_PIPELINE.md.
- Số chiều: 3072 (mặc định), có thể giảm xuống 1536 hoặc 768. **Phải chốt trước khi nạp dữ liệu**, vì đổi chiều nghĩa là tạo lại toàn bộ vector.
- Index của pgvector cho kiểu `vector` có giới hạn số chiều (khoảng 2000 theo hiểu biết hiện tại), nên 3072 khó đánh index trực tiếp. Ưu tiên 768 hoặc 1536, hoặc dùng kiểu `halfvec`; kiểm tra theo phiên bản pgvector bạn dùng.
- Kiểm tra tài liệu Google về việc có cần chuẩn hóa vector khi giảm chiều không, và khai báo đúng loại tác vụ (tài liệu hay câu hỏi) khi tạo embedding.
- Sau hạn mức miễn phí, giá embedding tính theo triệu token đầu vào (khoảng 0,15 USD theo công bố của Google tại thời điểm tra cứu); đưa vào dự toán nếu sau này chuyển gói.

**Không đặt cứng tên mô hình:** mô hình của nhà cung cấp đổi và ngừng hỗ trợ khá nhanh (ví dụ một mô hình embedding cũ của Google có lịch ngừng vào tháng 1/2026). Tên mô hình, số chiều và nhà cung cấp nằm trong cấu hình và được lưu cùng vector trong database.

**Tài liệu dạng ảnh:** Gemini có thể đọc trực tiếp PDF và ảnh, là phương án thay cho bước OCR riêng với tài liệu scan. Cái giá là tốn token hơn, nên chỉ áp dụng cho tài liệu thật sự là ảnh; PDF có sẵn văn bản vẫn trích văn bản như thiết kế ở docs/AI_PIPELINE.md.

### Quyết định bổ sung (tháng 10/2026)

**Embedding:** chiều vector 768 (đã chốt). Vẫn thử lại trên tài liệu tiếng Việt và tiếng Anh thật trước khi nạp nhiều; đổi chiều sau này nghĩa là tạo lại toàn bộ vector.

**Hỏi đáp trên nhiều tài liệu**
- Truy xuất chỉ trong các tài liệu `READY` của chủ sở hữu và thuộc tập tài liệu người dùng đã chọn; lọc trước khi nội dung vào ngữ cảnh AI.
- Giới hạn số đoạn lấy từ mỗi tài liệu để một tài liệu không lấn át các tài liệu còn lại (đề xuất).
- Mỗi trích dẫn gồm tên tài liệu và số trang, kèm bản ghi nhanh để hiển thị khi tài liệu đã bị xóa.

**Ngôn ngữ:** tài liệu và câu hỏi có thể là tiếng Việt hoặc tiếng Anh; dùng mô hình embedding đa ngôn ngữ; trả lời theo ngôn ngữ của câu hỏi (đề xuất).

**Mục tiêu độ trễ:** chữ đầu tiên của câu trả lời hiện trong khoảng 3 giây; API thường dưới 500 ms ở p95 (không tính phần sinh câu trả lời dài).

**Tài liệu scan**
- Hướng chọn: Gemini đọc trực tiếp làm mặc định (miễn phí trong hạn mức, tính vào hạn mức AI); Tesseract với gói ngôn ngữ tiếng Việt và tiếng Anh làm dự phòng khi hết hạn mức hoặc AI ngừng.
- Lý do: theo các so sánh của bên thứ ba (không riêng cho tiếng Việt), các mô hình như Gemini xử lý tốt hơn với bố cục phức tạp, ảnh chất lượng thấp và tài liệu đa ngôn ngữ; Tesseract miễn phí, chạy cục bộ nhưng không hiểu bố cục và yếu với bản scan kém. Tesseract chạy trên máy chủ thì tốn CPU và RAM của dịch vụ Railway.
- Việc phải làm trước khi coi là chốt hẳn: thử trên 3 đến 5 tài liệu scan tiếng Việt thật và đo chất lượng; đặt giới hạn số trang scan vì mỗi trang tốn token; ghi nhận phương pháp OCR đã dùng cho từng tài liệu.

---

<!-- Nguồn: docs/QUOTA_AND_RESILIENCE.md -->

## Hạn mức AI và chế độ suy giảm

> **Khi nào đọc:** khi làm `llm_gateway`, module `usage`, worker, mã lỗi API, hoặc bất kỳ chỗ nào gọi AI và phải xử lý lỗi hạn mức.

### Hành vi khi hết hạn mức AI

"Hết hạn mức" gồm nhiều tình huống khác nhau, mỗi loại cần cách xử lý riêng:

| Tình huống | Bản chất | Cách xử lý |
|---|---|---|
| Chạm giới hạn tốc độ (lỗi 429) | Tạm thời, tự hết sau vài giây đến vài phút | Thử lại với thời gian chờ tăng dần, tôn trọng thời gian chờ nhà cung cấp báo, có giới hạn số lần |
| Hết credit hoặc chạm trần chi tiêu của tài khoản | Toàn hệ thống, kéo dài đến khi nạp thêm | Không thử lại; mở circuit breaker; chuyển chế độ suy giảm; job sang `PAUSED_QUOTA`; báo quản trị viên |
| Người dùng vượt hạn mức do mình đặt | Cục bộ, có chủ ý | Từ chối ngay, không gọi AI, báo thời điểm đặt lại |
| Ngữ cảnh quá dài | Theo từng yêu cầu | Rút gọn (giảm số đoạn, tóm tắt lịch sử) hoặc từ chối với mã lỗi riêng |

**Mã lỗi trong hợp đồng OpenAPI**

| Mã lỗi | HTTP gợi ý | Ý nghĩa | App hiển thị |
|---|---|---|---|
| `AI_TEMPORARILY_UNAVAILABLE` | 503 | AI tạm ngừng (hết hạn mức hệ thống hoặc nhà cung cấp lỗi) | Thông báo AI tạm nghỉ, các tính năng khác vẫn dùng được |
| `AI_RATE_LIMITED` | 429 | Quá nhiều yêu cầu, kèm thời gian chờ | Hiện "thử lại sau ít giây", tự thử lại có giới hạn |
| `USER_QUOTA_EXCEEDED` | 429 | Hết lượt của người dùng, kèm số lượt còn lại và thời điểm đặt lại | Hiện số lượt và khi nào được dùng tiếp |
| `CONTEXT_TOO_LONG` | 422 | Câu hỏi hoặc hội thoại vượt giới hạn | Gợi ý rút gọn hoặc bắt đầu cuộc trò chuyện mới |

Lỗi xảy ra giữa luồng streaming phải được báo bằng một sự kiện lỗi kèm mã, không để luồng đứt âm thầm. OpenAPI mô tả streaming không tốt nên phần này ghi chú riêng trong `contract/README.md`.

**Circuit breaker ở `llm_gateway`**
- Đóng: gọi bình thường.
- Mở: sau một số lần lỗi hết hạn mức liên tiếp, trả lỗi ngay mà không gọi nhà cung cấp.
- Nửa mở: sau một khoảng chờ, thử một lượng nhỏ yêu cầu; thành công thì đóng lại, thất bại thì mở tiếp.
- Phải phân loại lỗi trước: lỗi tạm thời chỉ thử lại, không làm mở cầu dao ngay; lỗi hết hạn mức hoặc billing mới làm mở cầu dao.

**Hạn mức ba tầng**

| Tầng | Phạm vi | Ví dụ giới hạn |
|---|---|---|
| 1. Hệ thống | Toàn bộ ứng dụng | Ngân sách AI theo ngày và tháng; chạm ngưỡng cao thì tắt trước các tác vụ hàng loạt, không khẩn |
| 2. Người dùng | Mỗi tài khoản | Số câu hỏi và token mỗi ngày; tạo flashcard hoặc tóm tắt tính riêng |
| 3. Mỗi yêu cầu hoặc tài liệu | Từng thao tác | Số trang, kích thước file, số tài liệu, độ dài đầu vào, giới hạn token đầu ra |

Cách đếm: dùng Redis với thao tác nguyên tử; ước lượng token trước khi gọi (giữ chỗ), sau đó điều chỉnh theo số token thực tế nhà cung cấp trả về và ghi vào `ai_usage`. Các con số cụ thể cần chỉnh theo ngân sách đã quyết ở giai đoạn 0.

**Job nền khi hết hạn mức**
- Chuyển sang `PAUSED_QUOTA`, không phải `FAILED`, và không tính vào số lần thử lại, tránh làm nghẽn hàng đợi và đốt thêm tiền.
- Lưu tiến độ theo từng đoạn: đoạn nào đã có embedding thì không làm lại.
- Tự chạy tiếp khi circuit breaker đóng lại hoặc hạn mức phục hồi.

**Chế độ suy giảm khi AI ngừng**

| Tính năng | Hành vi |
|---|---|
| Xem tài liệu, lịch sử hội thoại | Bình thường |
| Flashcard có sẵn và lịch ôn tập | Bình thường |
| Hỏi đáp | Chỉ tìm đoạn liên quan, hiện đoạn trích kèm số trang, không sinh câu trả lời (cần embedding còn chạy được; nếu không thì thông báo tạm ngừng) |
| Tạo flashcard, tóm tắt mới | Tạm khóa, báo rõ lý do |
| Tải tài liệu mới | Vẫn nhận file; job chờ ở `PAUSED_QUOTA` |

**Cảnh báo ngân sách**
- Báo quản trị viên khi ngân sách chạm 50%, 80% và 100%.
- Đặt thêm trần chi tiêu ngay tại tài khoản nhà cung cấp như lớp bảo vệ cuối.
- Cảnh báo khi một người dùng dùng nhiều gấp bội mức trung bình (dấu hiệu lạm dụng hoặc lỗi lặp vòng).
- Dashboard chi phí theo từng người dùng và theo từng tính năng.

**Giảm lượng token tiêu thụ**
- Chỉ đưa vài đoạn liên quan nhất vào ngữ cảnh, không đưa cả tài liệu.
- Hội thoại dài thì tóm tắt phần cũ thay vì gửi lại toàn bộ lịch sử.
- Mô hình nhỏ cho việc đơn giản (phân loại, tóm tắt ngắn), mô hình mạnh cho trả lời phức tạp.
- Đặt giới hạn độ dài đầu ra cho từng loại yêu cầu.
- Embedding làm một lần rồi lưu; tạo flashcard khi người dùng yêu cầu, không tự động cho mọi tài liệu.
- Cache câu trả lời lặp lại, khóa cache phải gồm người dùng và tập tài liệu (xem docs/SECURITY.md).
- Tận dụng lưu đệm prompt của nhà cung cấp nếu có hỗ trợ.

**Dự phòng nhà cung cấp**
- Lớp `providers/` cho phép chuyển phần sinh câu trả lời sang nhà cung cấp hoặc mô hình dự phòng.
- Embedding khó đổi hơn: vector của hai mô hình khác nhau không so sánh được, nên đổi embedding nghĩa là tạo lại toàn bộ vector. Vì vậy chọn mô hình embedding kỹ từ đầu.

**Trải nghiệm người dùng:** hiện số lượt còn lại, nói rõ khi hết và khi nào được dùng tiếp, giữ lại câu hỏi đã gõ để gửi lại, không hiển thị lỗi kỹ thuật.

### Giá trị khởi điểm đã chốt

| Mục | Giá trị |
|---|---|
| Ngân sách AI | 0 đồng (gói miễn phí); hạn mức hệ thống bằng giới hạn miễn phí của nhà cung cấp |
| Hạn mức hỏi đáp mỗi người | Khoảng 30 câu mỗi ngày, cấu hình được, có thể hạ khi hạn mức AI toàn hệ thống còn ít (cách hạ chưa chốt) |
| Giới hạn tải lên | Khoảng 20 MB, 200 trang, 10 tài liệu mỗi người |
| Cảnh báo ngân sách | 50%, 80%, 100% |
| Kênh nhận cảnh báo | Chưa chốt |

Quản trị viên xem mức dùng, đặt hạn mức riêng cho từng người và bật công tắc khẩn cấp tắt AI trong giao diện quản trị (docs/BUSINESS_FLOWS.md, nhóm A).

---

<!-- Nguồn: docs/SECURITY.md -->

## Bảo mật

> **Khi nào đọc:** khi làm xác thực, phân quyền, truy vấn dữ liệu người dùng, cache, xóa dữ liệu, hoặc quản lý khóa và secret.

Các việc bảo mật còn lại cần làm nằm ở giai đoạn 4 trong docs/PLAN.md. Quy tắc khóa API và dữ liệu khi dùng gói AI miễn phí nằm trong docs/AI_PIPELINE.md.

### Bảo mật giữa người dùng

Đây là rủi ro lớn nhất của ứng dụng RAG. Giả sử người A tải `giao_trinh.pdf`, người B tải `tai_lieu.pdf`; khi B hỏi AI:

- Truy vấn chỉ lấy chunk thuộc tài liệu mà B được phép truy cập, lọc **trước khi** nội dung vào ngữ cảnh AI.
- Không dùng kết quả cache của A cho B: khóa cache phải gồm người dùng và tập tài liệu.
- Không thể vượt kiểm tra quyền bằng cách đổi ID trên URL hoặc trong nội dung request.
- Lịch sử hội thoại, trích dẫn, flashcard và file tải về đều kiểm tra quyền.
- Worker kiểm tra trạng thái trước thao tác nhạy cảm (tài liệu đã xóa thì dừng).
- Row-Level Security của PostgreSQL là lớp phòng thủ bổ sung, **không thay thế** kiểm tra quyền trong ứng dụng.
- Tách riêng development, staging, production (database, storage, API URL, thông tin xác thực, khóa mã hóa); không dùng database production để chạy test.

### Xác thực và quản trị

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

---

<!-- Nguồn: docs/TESTING.md -->

## Chiến lược kiểm thử

> **Khi nào đọc:** trước khi viết hoặc sửa test, và khi quyết định một việc đã "xong" hay chưa.

### Chiến lược kiểm thử

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

### Kịch bản bổ sung (xác thực, quản trị, nhiều tài liệu)

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

### Kịch bản bổ sung (học tập)

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

---

<!-- Nguồn: docs/OPERATIONS.md -->

## Vận hành và CI/CD

> **Khi nào đọc:** khi làm pipeline, giám sát, cảnh báo, runbook, hoặc triển khai.

### Luồng CI/CD đích

| Sự kiện | Hệ thống tự làm |
|---|---|
| Mở Pull Request | Lint, kiểm tra kiểu, chạy test |
| Merge vào `develop` | Chạy kiểm tra và đóng gói bản thử nghiệm (không đẩy lên store) |
| Gắn tag phiên bản (ví dụ v0.1.0) | Đóng gói bản thử nghiệm (không đẩy lên store) |
| Backend merge | Build Docker image, deploy staging, duyệt, deploy production |


### Vận hành

Chỉ số nên theo dõi:
- **API:** tỷ lệ lỗi, thời gian phản hồi p95, số request
- **Database:** số kết nối, thời gian truy vấn, dung lượng
- **Worker:** độ dài hàng đợi, thời gian xử lý tài liệu, tỷ lệ job thất bại
- **AI:** token vào/ra, chi phí ước tính, thời gian phản hồi, chất lượng trích dẫn
- **Hạn mức AI:** % ngân sách đã dùng, trạng thái circuit breaker, số job `PAUSED_QUOTA`, số lần người dùng chạm hạn mức
- **Mobile:** crash, lỗi mạng, thời gian tải màn hình

Công cụ: Sentry cho lỗi ứng dụng, Prometheus + Grafana cho metrics, log tập trung khi quy mô cần. Không cần dựng đủ ngay từ đầu.

Runbook (đặt ở `docs/runbooks/`): `database-recovery.md`, `failed-document-jobs.md`, `production-rollback.md`, `ai-quota-exhausted.md`. Script hỗ trợ ở `backend/scripts/`: `healthcheck.py`, `cleanup_jobs.py`.

### Triển khai trên Railway

Dịch vụ cần dựng cho mỗi môi trường: API, worker ARQ, PostgreSQL có pgvector, Redis, kho file tương thích S3. Railway có template PostgreSQL kèm pgvector (do cộng đồng và Railway cung cấp) và Bucket lưu trữ S3; cần xác nhận phiên bản và điều kiện hiện hành trước khi dựng.

**Chi phí (theo tài liệu Railway tại thời điểm tra cứu cuối tháng 10/2026, cần kiểm tra lại):**
- Không có gói miễn phí vĩnh viễn: tài khoản mới có khoảng 5 USD credit dùng thử một lần trong 30 ngày, sau đó là gói Free với khoảng 1 USD credit mỗi tháng và tài nguyên hạn chế.
- Gói Hobby: 5 USD mỗi tháng, đã gồm 5 USD tài nguyên sử dụng.
- Đơn giá tài nguyên: RAM khoảng 10 USD mỗi GB mỗi tháng, CPU khoảng 20 USD mỗi vCPU mỗi tháng, lưu trữ volume khoảng 0,15 USD mỗi GB mỗi tháng, lưu lượng ra khoảng 0,05 USD mỗi GB.
- API, worker, PostgreSQL và Redis chạy cùng lúc có thể vượt mức 5 USD; cần chốt ngân sách hosting và đặt cảnh báo chi phí.
- Volume của tài khoản dùng thử bị xóa 30 ngày sau khi hết credit: không dùng gói dùng thử cho dữ liệu cần giữ.

**Sao lưu:**
- Sao lưu PostgreSQL định kỳ ra nơi khác và thử khôi phục; sao lưu database không bao gồm file gốc đã tải lên, nên cần sao lưu kho file riêng.
- Bản sao lưu giữ tối đa 30 ngày sau khi người dùng xóa tài khoản (docs/BUSINESS_FLOWS.md, U9).

**Chỉ số tải mục tiêu dùng khi định cỡ tài nguyên:** 100 người dùng, 10 đồng thời, API p95 dưới 500 ms, chữ đầu tiên của câu trả lời trong khoảng 3 giây.

> **Phạm vi hiện tại:** dự án chỉ chạy thử trên máy cá nhân (web và mobile qua Expo). Phần Railway ở trên chỉ áp dụng khi sau này muốn đưa lên mạng.

---

<!-- Nguồn: docs/DECISIONS.md -->

## Quyết định và câu hỏi mở

> **Dành cho agent:** dòng có trạng thái `Chưa chốt` nghĩa là chưa có quyết định. **Không tự quyết**, hãy hỏi người dùng, rồi ghi kết quả vào đây (lựa chọn, lý do, ngày chốt).

### Bảng quyết định

| Quyết định | Lựa chọn | Lý do và ghi chú | Ngày chốt | Trạng thái |
|---|---|---|---|---|
| Loại app | Trợ lý học tập từ tài liệu | Hợp RAG, hợp Python và AI | 2026-10-29 | Đã chốt |
| Phạm vi bản 1 | Đầy đủ chức năng: gồm flashcard, ôn tập SM-2, trắc nghiệm, tóm tắt theo chương, Word và tài liệu scan; số màn hình tối thiểu khoảng 10 đến 15, không giới hạn trên | Người dùng ưu tiên đầy đủ chức năng; xem docs/SCREENS.md | 2026-10-30 | Đã chốt |
| Tên ứng dụng | FlashCard | Người dùng chọn | 2026-11-07 | Đã chốt |
| Mã định danh ứng dụng (bundle ID, package name) | `com.example.flashcard` (tạm) | Dùng khi chạy thử; đổi một lần nếu sau này cần | 2026-11-07 | Đã chốt (tạm) |
| Phạm vi phát hành | Chỉ bản thử nghiệm: chạy được hoàn chỉnh trên web và mobile (qua Expo Go hoặc development build); **không** phát hành lên App Store, Google Play | Người dùng yêu cầu. Bỏ các việc EAS Submit, hồ sơ store, TestFlight, Play Console | 2026-11-07 | Đã chốt |
| Cách làm việc | Agent của người dùng chạy trên máy người dùng, đọc AGENTS.md và docs/ | Người dùng tự chạy agent trên máy mình | 2026-11-07 | Đã chốt |
| Cấu trúc Không gian | Có. Một không gian chứa nhiều tài liệu, hội thoại, bộ thẻ, trắc nghiệm, tóm tắt. Mỗi tài liệu thuộc đúng một không gian (chuyển được sang không gian khác). Tự tạo không gian mặc định khi tải tài liệu đầu tiên. Không giới hạn số không gian, vẫn giữ giới hạn 10 tài liệu mỗi người | Khớp cách học theo môn; xem docs/BUSINESS_FLOWS.md mục U16 | 2026-11-07 | Đã chốt |
| Cách làm việc | Làm một mình, phần lớn code do agent viết | Agent cần tự kiểm thử, tóm tắt thay đổi và nêu cách kiểm tra cho người dùng duyệt | 2026-10-29 | Đã chốt |
| Backend | Python (FastAPI) | Hệ sinh thái AI, tự sinh OpenAPI | 2026-10-22 | Đã chốt |
| Kiến trúc | Modular monolith | Team nhỏ, ra nhanh, dễ tách sau | 2026-10-22 | Đã chốt |
| Repo | Monorepo; FE và BE tách, giao tiếp qua OpenAPI | Tách rõ nhưng tiện quản lý | 2026-10-22 | Đã chốt |
| Cách viết hợp đồng API | Contract-first: viết `contract/openapi.yaml` trước, backend và frontend làm theo | Người dùng làm một mình nhưng muốn hợp đồng rõ ràng cho agent | 2026-10-29 | Đã chốt |
| Phiên bản công nghệ chính (Python, Node, Expo SDK, PostgreSQL, pgvector) | Chọn bản ổn định (stable hoặc LTS), không cần bản mới nhất | Giảm rủi ro; số phiên bản cụ thể chốt khi khởi tạo và ghi vào file khóa phiên bản | 2026-10-29 | Đã chốt |
| Thư viện hàng đợi | ARQ | Nhẹ, hợp FastAPI bất đồng bộ | 2026-10-29 | Đã chốt |
| ORM | SQLAlchemy | Người dùng đồng ý đề xuất | 2026-10-29 | Đã chốt |
| Nơi triển khai | Railway (API, worker, PostgreSQL có pgvector, Redis, kho file) | Dễ dùng cho dự án nhỏ; có template PostgreSQL kèm pgvector | 2026-10-29 | Đã chốt |
| Ngân sách hosting hằng tháng | Chưa cần | Chỉ chạy trên máy cá nhân; chỉ cần quyết khi muốn đưa lên mạng (Railway không có gói miễn phí vĩnh viễn) | 2026-11-07 | Hoãn |
| Kho lưu file gốc | MinIO (giao diện S3) khi chạy local | Chỉ chạy local, không deploy | 2026-11-07 | Đã chốt (mặc định) |
| Dịch vụ gửi email (xác minh email, quên mật khẩu, cảnh báo) | Mailpit khi chạy local | Không cần dịch vụ thật khi chạy thử | 2026-11-07 | Đã chốt (mặc định) |
| Xác thực | Tự xây: email và mật khẩu, Google (không có Apple) | Không phát hành lên App Store/Google Play nên không bị ràng buộc Sign in with Apple | 2026-11-07 | Đã chốt |
| Rủi ro App Store 4.8 | Không áp dụng | Dự án chỉ là bản thử nghiệm, không phát hành lên store (xem dòng Phạm vi phát hành) | 2026-11-07 | Đã chốt |
| Xác minh email và quên mật khẩu | Có cả hai (chỉ cho tài khoản email và mật khẩu) |  | 2026-10-29 | Đã chốt |
| Quy tắc liên kết tài khoản khi cùng email ở nhiều cách đăng nhập | Tự liên kết nếu email từ Google đã được xác minh; nếu không thì phải đăng nhập bằng cách cũ trước | Mặc định đề xuất, người dùng đồng ý dùng mặc định | 2026-11-07 | Đã chốt (mặc định) |
| Tài khoản chưa xác minh email bị giới hạn gì | Chưa cho tải tài liệu | Mặc định đề xuất | 2026-11-07 | Đã chốt (mặc định) |
| Thanh toán | Không có; không có tính năng thu phí | Bản 1 không thu phí | 2026-10-29 | Đã chốt |
| Ngôn ngữ | Giao diện tiếng Việt và tiếng Anh; hỗ trợ tài liệu tiếng Việt và tiếng Anh | Dùng i18n; thử embedding trên cả hai ngôn ngữ | 2026-10-29 | Đã chốt |
| Giới hạn tải lên | Khoảng 20 MB mỗi file, 200 trang, 10 tài liệu mỗi người | Điều chỉnh theo thực tế và giới hạn của gói AI miễn phí | 2026-10-29 | Đã chốt |
| Phạm vi một lần hỏi đáp | Nhiều tài liệu | Người dùng chọn; kéo theo quy tắc cân bằng đoạn giữa các tài liệu | 2026-10-29 | Đã chốt |
| Mặc định chọn tập tài liệu khi hỏi | Mặc định hỏi trên mọi tài liệu sẵn sàng của không gian đang mở, cho phép chọn bớt | Gắn với cấu trúc Không gian | 2026-11-07 | Đã chốt (mặc định) |
| Hạn mức hỏi đáp mỗi người mỗi ngày | Khoảng 30 câu, cấu hình được, tùy hạn mức AI còn lại | Cách hạ hạn mức khi AI còn ít chưa chốt | 2026-10-29 | Đã chốt |
| Lịch sử hội thoại khi tài liệu bị xóa | Giữ lịch sử; trích dẫn hiện "tài liệu đã xóa" |  | 2026-10-29 | Đã chốt |
| Thời gian giữ bản sao lưu sau khi xóa tài khoản | 30 ngày | Ghi rõ trong chính sách quyền riêng tư | 2026-10-29 | Đã chốt |
| Chỉ số tải mục tiêu | 100 người dùng, 10 đồng thời; API p95 dưới 500 ms; chữ đầu tiên của câu trả lời trong khoảng 3 giây |  | 2026-10-29 | Đã chốt |
| Nhà cung cấp AI | Gemini API, dùng gói miễn phí; thiết kế để chuyển gói trả phí bất kỳ lúc nào chỉ bằng đổi khóa và cấu hình | Không tốn chi phí AI; chấp nhận rủi ro dữ liệu của gói miễn phí và giảm thiểu bằng thông báo, xin đồng ý | 2026-10-29 | Đã chốt |
| Ngân sách AI | 0 đồng (gói miễn phí) | Hạn mức hệ thống bằng giới hạn miễn phí; cảnh báo ở 50%, 80%, 100% | 2026-10-29 | Đã chốt |
| Chiều vector embedding | 768 | Tiết kiệm lưu trữ, nằm trong giới hạn index của pgvector; thử lại trên tài liệu thật trước khi nạp nhiều | 2026-10-29 | Đã chốt |
| Giao diện quản trị | Có; tách luồng người dùng và luồng quản trị | Xem docs/BUSINESS_FLOWS.md phần 2 | 2026-10-29 | Đã chốt |
| Hình thức giao diện quản trị | Chỉ web, nhóm route riêng trong cùng codebase, API `/v1/admin/` | Mặc định đề xuất | 2026-11-07 | Đã chốt (mặc định) |
| Quyền của quản trị viên với nội dung người dùng | Không xem nội dung tài liệu và hội thoại, chỉ siêu dữ liệu và thống kê; ghi nhật ký kiểm toán | Mặc định đề xuất | 2026-11-07 | Đã chốt (mặc định) |
| Xác thực hai bước cho tài khoản quản trị | Có (làm ở lát quản trị, có thể hoãn nếu chỉ chạy thử) | Mặc định đề xuất | 2026-11-07 | Đã chốt (mặc định) |
| Kênh nhận cảnh báo của quản trị viên | Email (Mailpit khi chạy local) | Mặc định đề xuất | 2026-11-07 | Đã chốt (mặc định) |
| Thuật toán lập lịch ôn tập | SM-2 | | 2026-10-29 | Đã chốt |
| Tóm tắt theo chương: tạo tự động hay theo yêu cầu | Tạo theo yêu cầu | Tiết kiệm hạn mức AI | 2026-11-07 | Đã chốt (mặc định) |
| Cách tính số trang cho file Word (giới hạn 200 trang) | Quy đổi sau khi chuyển đổi sang PDF | Mặc định | 2026-11-07 | Đã chốt (mặc định) |
| Xử lý tài liệu scan | Gemini đọc trực tiếp làm mặc định; Tesseract (tiếng Việt và tiếng Anh) làm dự phòng khi hết hạn mức | Cả hai đều miễn phí trong điều kiện nhất định; chọn theo khuyến nghị, cần thử nghiệm trên tài liệu scan tiếng Việt thật. Xem docs/AI_PIPELINE.md | 2026-10-29 | Đã chốt, chờ thử nghiệm |

### Rủi ro & câu hỏi mở

| Mục | Mô tả | Người phụ trách | Trạng thái |
|---|---|---|---|
| Chất lượng embedding và OCR với tiếng Việt | Thử trên 3 đến 5 tài liệu thật trước khi chốt mô hình | | Chưa làm |
| Bản quyền tài liệu người dùng tải lên | Soạn điều khoản, không chia sẻ công khai ở bản đầu | | Chưa làm |
| Chi phí AI mỗi người dùng | Đặt hạn mức, đo trong giai đoạn beta | | Chưa làm |
| Đổi mô hình embedding phải tạo lại toàn bộ vector | Chọn mô hình cẩn thận từ đầu; lưu tên và số chiều mô hình cùng dữ liệu | | Chưa làm |
| Hết hạn mức AI làm gián đoạn tính năng | Circuit breaker, chế độ suy giảm, job `PAUSED_QUOTA` (docs/QUOTA_AND_RESILIENCE.md) | | Chưa làm |
| Chi phí AI tăng đột biến do lạm dụng hoặc lỗi lặp vòng | Hạn mức ba tầng, cảnh báo bất thường, trần chi tiêu tại nhà cung cấp | | Chưa làm |
| Dữ liệu qua gói AI miễn phí có thể bị nhà cung cấp dùng cải thiện sản phẩm | Thông báo rõ và xin đồng ý của người dùng, khuyến cáo không tải tài liệu nhạy cảm, thiết kế để chuyển gói trả phí bất kỳ lúc nào (docs/AI_PIPELINE.md) | | Chưa làm |
| Giới hạn chiều index của pgvector không khớp chiều embedding mặc định | Chọn 768 hoặc 1536 chiều hoặc kiểu `halfvec`, kiểm tra trước khi nạp dữ liệu (docs/AI_PIPELINE.md) | | Chưa làm |
| Railway không có gói miễn phí vĩnh viễn nên chi phí hosting phát sinh | Chốt ngân sách hosting, theo dõi mức dùng tài nguyên, đặt cảnh báo chi phí | | Chưa làm |
| PostgreSQL trên Railway là dịch vụ tự vận hành bằng template, dữ liệu mất nếu volume mất | Sao lưu định kỳ ra nơi khác và thử khôi phục; sao lưu file gốc riêng với sao lưu database | | Chưa làm |
| Gộp tài khoản sai giữa Google và email (nguy cơ chiếm tài khoản) | Chỉ tự liên kết khi email đã xác minh; kiểm thử kỹ các tình huống liên kết | | Chưa làm |
| Chất lượng OCR tiếng Việt chưa có số liệu riêng | Thử trên 3 đến 5 tài liệu scan thật trước khi chốt | | Chưa làm |

| Dữ liệu qua gói Gemini miễn phí có thể được Google dùng cải thiện sản phẩm | Chỉ dùng dữ liệu thử nghiệm; hiện thông báo và xin đồng ý như đã thiết kế | | Chưa làm |

---

<!-- Nguồn: docs/PLAN.md -->

## Kế hoạch và tiến độ

> **Dành cho agent:** đây là nguồn sự thật về tiến độ. Làm việc theo thứ tự giai đoạn, chọn việc chưa tick (`[ ]`) tiếp theo. Khi xong một việc: đổi thành `[x]`, sửa cột Xong/Tổng trong bảng tiến độ, thêm một dòng vào nhật ký thay đổi. Không tick khi chưa chạy test và chưa đạt định nghĩa "xong" trong AGENTS.md.

### Cách dùng

1. Đi lần lượt từng giai đoạn; mỗi giai đoạn có **mục tiêu**, **việc cần làm** và **tiêu chí hoàn thành**.
2. Chỉ chuyển sang giai đoạn sau khi đạt tiêu chí hoàn thành của giai đoạn trước (riêng Bảo mật nên bắt đầu sớm và chạy song song).
3. Sau mỗi lần cập nhật, sửa lại cột **Xong/Tổng** và **Trạng thái** ở bảng tiến độ.

Trạng thái: `Chưa bắt đầu` · `Đang làm` · `Xong` · `Tạm hoãn`

### Bảng tiến độ tổng quan

| # | Giai đoạn | Xong/Tổng | Trạng thái | Dự kiến | Thực tế |
|---|---|---|---|---|---|
| 0 | Chuẩn bị & chốt quyết định | 12/16 | Đang làm | | |
| 1 | Khởi tạo dự án | 0/19 | Chưa bắt đầu | Tuần 1 | |
| 2 | CI/CD | 0/9 | Chưa bắt đầu | Tuần 1 đến 2 | |
| 3 | Kết nối & đồng bộ dữ liệu | 0/16 | Chưa bắt đầu | Tuần 2 đến 4 | |
| 4 | Bảo mật | 0/28 | Chưa bắt đầu | Tuần 2 đến 4, rà soát lại trước beta | |
| 5 | Sức tải, hiệu năng & chi phí AI | 0/19 | Chưa bắt đầu | Trước production | |
| 6 | Beta & chuẩn bị production | 0/10 | Chưa bắt đầu | | |
| 7 | Ra mắt & vận hành | 0/6 | Chưa bắt đầu | | |
| F | Lát chức năng bản 1 | 0/17 | Chưa bắt đầu | Song song với giai đoạn 1 đến 6 | |
| | **Tổng** | **12/140** | | | |

---

### Giai đoạn 0. Chuẩn bị & chốt quyết định

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

### Giai đoạn 1. Khởi tạo dự án

**Mục tiêu:** có khung app và backend chạy được ở máy local, với công cụ chất lượng code bật sẵn từ đầu.

**Đầu vào:** các quyết định của giai đoạn 0.

**Việc cần làm**
- [ ] Chọn và ghi lại phiên bản ổn định (stable hoặc LTS, không cần mới nhất) của Python, Node, Expo SDK, PostgreSQL, pgvector vào file khóa phiên bản
- [ ] Tạo app bằng `create-expo-app` với TypeScript
- [ ] Cài `expo-dev-client`, `expo-secure-store`, `expo-router`
- [ ] Bật TypeScript `strict`
- [ ] Cài ESLint và Prettier
- [ ] Cài Husky và lint-staged (tự lint/format trước mỗi commit)
- [ ] Cài Jest và React Native Testing Library
- [ ] Chọn công cụ test end-to-end: Maestro hoặc Detox
- [ ] Tách 3 môi trường dev / staging / production, mỗi môi trường có API URL và bundle ID riêng
- [ ] Thiết lập repo và quy tắc nhánh: `main` (production), `develop`, `feature/*` qua Pull Request
- [ ] Tạo backend FastAPI, chia module `auth`, `users`, `documents`, `chat`, `study`, `ai`, `usage`, `admin` (mỗi module có router, schemas, models, service, repository), thêm thư mục `integrations/` (object storage, email, llm_gateway) và `workers/`
- [ ] Viết `contract/openapi.yaml` trước (contract-first) cho các luồng bản 1, sinh API client cho frontend và kiểm tra thay đổi phá vỡ trong CI
- [ ] Dựng Docker Compose chạy Postgres (bật pgvector) và Redis ở local
- [ ] Thiết lập Alembic và migration đầu tiên cho các bảng chính (xem docs/DATA_MODEL.md)
- [ ] Tạo cột vector 768 chiều (đã chốt) và index tương ứng; xác nhận trên tài liệu thật (xem docs/AI_PIPELINE.md)
- [ ] Cài i18n cho frontend (tiếng Việt và tiếng Anh), không viết cứng chuỗi hiển thị
- [ ] Viết `providers/gemini.py` theo interface chung cho LLM và embedding; tên mô hình, số chiều, giới hạn tốc độ, khóa API đọc từ cấu hình/biến môi trường, không viết cứng, để chuyển gói chỉ cần đổi khóa và cấu hình
- [ ] Cài pytest và HTTPX cho backend; tạo `tests/` gồm `unit`, `integration`, `api`, `security`, `fixtures` (xem docs/TESTING.md)
- [ ] Tổ chức thư mục frontend theo docs/ARCHITECTURE.md (`app`, `features`, `components`, `api`, `hooks`, `store`, `storage`, `theme`...)

**Tiêu chí hoàn thành:** clone repo về, chạy một lệnh là app và backend lên được; commit sai lint bị chặn.

---

### Giai đoạn 2. CI/CD

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

### Giai đoạn 3. Kết nối & đồng bộ dữ liệu

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
- [ ] Idempotency-Key (UUID mỗi thao tác) cho tải tài liệu và các thao tác tạo dữ liệu quan trọng, backend trả kết quả cũ nếu key trùng
- [ ] Chọn chiến lược xung đột: last-write-wins hoặc optimistic locking bằng `version`/`updatedAt`

*Thời gian thực và thông báo*
- [ ] Realtime nếu cần (WebSocket/Socket.IO hoặc SSE)
- [ ] Push notification qua Expo Notifications (FCM/APNs)
- [ ] Hiển thị trạng thái xử lý tài liệu cho người dùng (polling hoặc thông báo) theo máy trạng thái ở docs/DATA_MODEL.md
- [ ] Khai báo mã lỗi hạn mức AI trong hợp đồng OpenAPI (`AI_TEMPORARILY_UNAVAILABLE`, `AI_RATE_LIMITED`, `USER_QUOTA_EXCEEDED`, `CONTEXT_TOO_LONG`), kể cả lỗi giữa luồng streaming (docs/QUOTA_AND_RESILIENCE.md)
- [ ] App xử lý các mã lỗi hạn mức: thông báo thân thiện, hiện số lượt còn lại và thời điểm đặt lại, giữ lại câu hỏi đã gõ để gửi lại

*Tương thích phiên bản*
- [ ] Đánh phiên bản API (`/v1`, `/v2`) và giữ tương thích ngược
- [ ] Cơ chế force update: backend trả phiên bản tối thiểu, app cũ hơn hiện màn hình yêu cầu cập nhật

**Tiêu chí hoàn thành:** tắt mạng giữa chừng khi tải tài liệu rồi bật lại, không tạo tài liệu trùng và không mất tài liệu; app hiện đúng thông báo khi AI hết hạn mức.

---

### Giai đoạn 4. Bảo mật

**Mục tiêu:** đóng các lỗ hổng phổ biến trước khi có người dùng thật. Bắt đầu cùng giai đoạn 3 và rà soát lại trước beta.

**Việc cần làm**

*Phía app*
- [ ] Lưu token bằng `expo-secure-store` (Keychain/Keystore), không dùng AsyncStorage
- [ ] Không nhúng secret hoặc API key vào app
- [ ] Bắt buộc HTTPS; cân nhắc certificate pinning cho app tài chính
- [ ] Phát hiện root/jailbreak nếu app nhạy cảm
- [ ] Khóa sinh trắc học cho thao tác quan trọng
- [ ] Che nội dung nhạy cảm ở màn hình đa nhiệm

*Xác thực và phân quyền*
- [ ] Access token ngắn (khoảng 15 phút) cộng refresh token có xoay vòng (rotation) và thu hồi được
- [ ] Băm mật khẩu bằng argon2 hoặc bcrypt
- [ ] Đăng nhập email và mật khẩu, Google: backend xác thực ID token, quy tắc liên kết tài khoản (xem docs/SECURITY.md)
- [ ] Xác minh email và quên mật khẩu: token một lần, hạn ngắn, không lộ email có tồn tại hay không, thu hồi phiên sau khi đổi mật khẩu
- [ ] Tích hợp dịch vụ gửi email (xác minh, đặt lại mật khẩu, cảnh báo)
- [ ] Tự xây xác thực bằng thư viện chuẩn (không tự phát minh thuật toán mã hóa) và kiểm thử kỹ các luồng U1 đến U4 trong docs/BUSINESS_FLOWS.md
- [ ] Phân quyền theo từng bản ghi ở backend (chống IDOR, tức xem tài liệu của người khác bằng cách đổi ID)
- [ ] Phân quyền quản trị: vai trò admin kiểm tra ở backend, API `/v1/admin/*`, quản trị viên không xem nội dung người dùng, mọi thao tác ghi nhật ký kiểm toán (xem docs/SECURITY.md)
- [ ] Bật PostgreSQL Row-Level Security như lớp phòng thủ bổ sung (không thay thế kiểm tra quyền trong ứng dụng)
- [ ] Khóa cache theo người dùng, không dùng chung kết quả cache giữa các người dùng (docs/SECURITY.md)
- [ ] Triển khai chính sách xóa tài liệu: file gốc, chunk, vector và job đang chờ; tài liệu đang xóa không còn xuất hiện trong tìm kiếm

*Backend và hạ tầng*
- [ ] Validate mọi input; dùng ORM hoặc query tham số hóa chống SQL injection
- [ ] Cấu hình CORS, Helmet, và rate limit riêng cho đăng nhập (chống brute-force)
- [ ] Lưu secret trong Secrets Manager/Vault
- [ ] Quản lý khóa API AI: mỗi môi trường một khóa riêng, chỉ nằm ở backend, không commit lên Git, có quy trình thu hồi và tạo khóa mới khi nghi bị lộ
- [ ] Quy tắc dữ liệu khi dùng gói AI miễn phí: thông báo rõ và xin đồng ý của người dùng trước khi tải tài liệu (nội dung được gửi cho Google xử lý và có thể được dùng để cải thiện sản phẩm), khuyến cáo không tải tài liệu nhạy cảm, không đưa thông tin định danh không cần thiết vào prompt (docs/AI_PIPELINE.md)
- [ ] Mã hóa dữ liệu nhạy cảm khi lưu và khi truyền
- [ ] Quét lỗ hổng phụ thuộc trong CI (npm audit, pip-audit, Dependabot, Snyk)
- [ ] Ghi log truy cập, tuyệt đối không ghi mật khẩu hoặc token
- [ ] Backup database tự động và thử khôi phục định kỳ
- [ ] Tuân thủ quy định dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP, GDPR nếu có người dùng châu Âu) và có chức năng xóa tài khoản; bản sao lưu giữ tối đa 30 ngày sau khi xóa
- [ ] Đối chiếu OWASP Mobile Top 10 và OWASP API Security Top 10

**Tiêu chí hoàn thành:** checklist OWASP đã đối chiếu xong, không còn lỗ hổng mức cao.

---

### Giai đoạn 5. Sức tải, hiệu năng & chi phí AI

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
- [ ] Phân loại lỗi và circuit breaker ở `llm_gateway`: lỗi tạm thời thì thử lại có giới hạn, lỗi hết hạn mức thì không thử lại và mở cầu dao
- [ ] Trạng thái `PAUSED_QUOTA` cho job tài liệu, lưu tiến độ theo từng đoạn, tự chạy lại khi hạn mức phục hồi
- [ ] Chế độ suy giảm khi AI ngừng: hỏi đáp chuyển sang chỉ tìm đoạn liên quan, các tính năng không cần AI vẫn chạy
- [ ] Biện pháp giảm token: giới hạn số đoạn đưa vào ngữ cảnh, tóm tắt hội thoại cũ, mô hình nhỏ cho việc đơn giản, giới hạn độ dài đầu ra
- [ ] Cố ý chạm giới hạn tốc độ của gói miễn phí để kiểm tra retry, circuit breaker, `PAUSED_QUOTA` và thông báo trên app

**Tiêu chí hoàn thành:** test tải đạt chỉ số mục tiêu (100 người dùng, 10 đồng thời, API p95 dưới 500 ms, chữ đầu tiên trong khoảng 3 giây); mọi nút thắt tìm ra đều có số liệu chứng minh. Khi mô phỏng nhà cung cấp AI hết hạn mức, hệ thống chuyển chế độ suy giảm, không lỗi 500 và không mất dữ liệu.

---

### Giai đoạn 6. Beta & chuẩn bị production

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

### Giai đoạn 7. Ra mắt & vận hành

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

### Giai đoạn F. Lát chức năng bản 1 (làm song song với giai đoạn 1 đến 6)

**Mục tiêu:** hoàn thành đầy đủ chức năng bản 1 theo từng lát dọc (contract, backend, frontend, test cho cùng một chức năng), mỗi lát kiểm chứng được trước khi sang lát sau.

**Cách làm:** mỗi lát gồm đặc tả từ `docs/specs/_TEMPLATE.md` được người dùng duyệt, cập nhật `contract/openapi.yaml`, backend, frontend (màn hình trong docs/SCREENS.md), test (docs/TESTING.md). Các lát đầu (F1 đến F8) đi cùng giai đoạn 1 đến 3; bảo mật, hạn mức và chi phí AI ở giai đoạn 4 và 5 áp dụng cho mọi lát.

**Việc cần làm**
- [ ] F1. Khung chạy được xuyên suốt: một endpoint thật đi từ frontend qua backend tới database, có kiểm tra sức khỏe và test
- [ ] F2. Đăng ký, đăng nhập bằng email và mật khẩu, duy trì và kết thúc phiên (U1, U4; màn hình 1)
- [ ] F3. Đăng nhập bằng Google (U1; màn hình 1)
- [ ] F4. Xác minh email và quên, đặt lại mật khẩu (U2, U3; màn hình 2, 3)
- [ ] F4b. Không gian học tập: tạo, đổi tên, xóa, không gian mặc định (U16; màn hình 5)
- [ ] F5. Tải tài liệu PDF và xử lý nền đến `READY`: trích văn bản, chia đoạn, embedding, trạng thái (U5; màn hình 5, 6)
- [ ] F6. Quản lý tài liệu: danh sách, chi tiết, thử lại, xóa (U6; màn hình 5, 7)
- [ ] F7. Hỏi đáp trên nhiều tài liệu, có trích dẫn, trả lời dần (U7; màn hình 9)
- [ ] F8. Xem trích dẫn và lịch sử hội thoại (U7; màn hình 10, 11)
- [ ] F9. Flashcard: bộ thẻ, AI đề xuất và người học duyệt, tạo tay, sửa, xóa (U11; màn hình 12, 13, 14)
- [ ] F10. Ôn tập lặp lại ngắt quãng theo SM-2 và kết quả ôn tập (U12; màn hình 15, 16)
- [ ] F11. Câu hỏi trắc nghiệm: tạo, làm bài, chấm bằng code, xem lại câu sai kèm nguồn (U13; màn hình 17, 18, 19)
- [ ] F12. Tóm tắt theo chương (U15; màn hình 8)
- [ ] F13. Hỗ trợ tài liệu Word (.docx) (U5)
- [ ] F14. Tài liệu scan: Gemini đọc trực tiếp, Tesseract dự phòng, sau khi thử trên tài liệu tiếng Việt thật (U14)
- [ ] F15. Hồ sơ và cài đặt: ngôn ngữ, lượt hỏi còn lại, đổi mật khẩu, xóa tài khoản (U4, U9, U10; màn hình 4)
- [ ] F16. Giao diện quản trị web: tổng quan, người dùng, theo dõi job, cấu hình, nhật ký kiểm toán (A1 đến A7; màn hình 20 đến 25)

**Tiêu chí hoàn thành:** mọi chức năng trong docs/BUSINESS_FLOWS.md phần bản 1 và phần quản trị chạy được, test qua, và kịch bản trong docs/TESTING.md đều đạt.

---

### Việc có thể bổ sung sau (backlog)

- [ ] Chiến lược kiểm thử chi tiết (tỉ lệ unit/integration/E2E)
- [ ] Analytics, A/B test, feature flag
- [ ] Đa ngôn ngữ (i18n) và khả năng tiếp cận
- [ ] Ước tính chi phí hạ tầng theo từng mốc người dùng
- [ ] Design system (component, màu sắc, typography)
- [ ] Quy ước team: commit, review code, onboarding

---

### Nhật ký thay đổi

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

---

<!-- Nguồn: docs/specs/_TEMPLATE.md -->

## Đặc tả tính năng: <tên tính năng>

> Sao chép file này thành `docs/specs/<ten-tinh-nang>.md`, điền đầy đủ và để người dùng duyệt **trước khi viết code**. Mục nào chưa biết thì ghi vào "Câu hỏi mở", không tự đoán.

- **Trạng thái:** Nháp / Đã duyệt / Đang làm / Xong
- **Thuộc bản:** 1 / 2 / 3 (xem docs/PRODUCT.md)
- **Giai đoạn liên quan:** (xem docs/PLAN.md)

### 1. Mục tiêu
Một đến hai câu: người dùng làm được gì sau khi tính năng này xong.

### 2. Luồng người dùng
Các bước theo thứ tự, gồm cả luồng lỗi chính.

### 3. Màn hình và hành vi giao diện
Danh sách màn hình, trạng thái (đang tải, rỗng, lỗi, thành công), khác biệt giữa mobile và web nếu có.

### 4. API
| Endpoint | Phương thức | Yêu cầu | Phản hồi | Mã lỗi |
|---|---|---|---|---|
| | | | | |

Cập nhật `contract/openapi.yaml` trước khi viết code.

### 5. Dữ liệu
Bảng, cột, ràng buộc, index cần thêm hoặc đổi; migration cần tạo (xem docs/DATA_MODEL.md).

### 6. Quy tắc nghiệp vụ
Các quy tắc và giới hạn (kích thước, số lượng, định dạng, trạng thái hợp lệ).

### 7. Quyền và bảo mật
Ai được làm gì; các kiểm tra quyền theo chủ sở hữu (xem docs/SECURITY.md).

### 8. AI và hạn mức (nếu có gọi AI)
Gọi AI ở bước nào, dữ liệu gửi đi là gì, hạn mức áp dụng, hành vi khi hết hạn mức (xem docs/QUOTA_AND_RESILIENCE.md).

### 9. Tiêu chí nghiệm thu
Viết dạng "Cho (điều kiện), Khi (hành động), Thì (kết quả)". Mỗi tiêu chí phải kiểm chứng được bằng test.

### 10. Test cần có
Unit, integration, E2E, kịch bản liên quan trong docs/TESTING.md.

### 11. Ngoài phạm vi
Những gì cố ý không làm ở lần này.

### 12. Câu hỏi mở
Những điều cần người dùng quyết định.

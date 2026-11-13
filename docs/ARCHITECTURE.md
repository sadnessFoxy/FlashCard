# Kiến trúc

> **Khi nào đọc:** trước khi tạo thư mục, module hoặc thay đổi cách các phần giao tiếp với nhau.

## Tổng quan

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

## Ranh giới Frontend và Backend

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

## Phân lớp trong backend

Mỗi module gồm `router` (nhận request) → `service` (logic nghiệp vụ) → `repository` (truy cập dữ liệu) → `models`; `schemas` là dữ liệu vào/ra khớp với contract.
- Router không chứa logic nghiệp vụ; service không viết truy vấn trực tiếp.
- Module này không đọc thẳng bảng của module khác; gọi qua service của module đó.
- Dịch vụ bên ngoài (object storage, email, LLM) chỉ được gọi qua `integrations/`.

## Phân lớp trong frontend

- `app/`: định tuyến, chỉ ghép màn hình.
- `features/`: mỗi nghiệp vụ một thư mục (giao diện, hook, gọi API của nghiệp vụ đó).
- `components/`: UI dùng chung, không biết gì về nghiệp vụ.
- `api/`: lớp duy nhất được phép gọi mạng. Màn hình không gọi mạng trực tiếp.
- `storage/`: lưu phiên đăng nhập, tách cài đặt theo nền tảng (`.native.ts` dùng secure store, `.web.ts` dùng cookie `httpOnly` do backend đặt). Không lưu token vào AsyncStorage hay `localStorage`.

## Cây thư mục tổng thể (đích, tạo dần theo giai đoạn)

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
│   │   │   ├── auth/  users/  spaces/  documents/  chat/  study/  usage/  admin/
│   │   │   │   (study/ chia gói con: flashcards/, reviews/, quizzes/)
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

## Giao diện quản trị và triển khai

- Giao diện quản trị chỉ dùng trên web, đặt trong nhóm route `(admin)` của cùng codebase frontend (đề xuất, chờ xác nhận); chỉ vai trò admin vào được.
- API quản trị nằm dưới `/v1/admin/`, có nhóm (tag) riêng trong `contract/openapi.yaml`, kiểm tra vai trò ở backend.
- Triển khai trên Railway: API, worker ARQ, PostgreSQL có pgvector, Redis, kho file (docs/OPERATIONS.md).
- Frontend hỗ trợ tiếng Việt và tiếng Anh qua i18n; mọi chuỗi hiển thị đi qua i18n.

## Tham chiếu: các kiến trúc đã cân nhắc

### Kiến trúc hệ thống (chia và triển khai thế nào)

| Kiến trúc | Mô tả ngắn | Phù hợp khi |
|---|---|---|
| Monolith | Một codebase, một lần deploy | Team nhỏ, sản phẩm mới |
| Modular monolith | Monolith chia module rõ ràng, module giao tiếp qua cổng riêng | Muốn dễ tách service sau này |
| Microservices | Nhiều service nhỏ, DB riêng, deploy độc lập | Nhiều team, hệ thống lớn |
| Event-driven | Giao tiếp bất đồng bộ qua sự kiện (Kafka, RabbitMQ) | Nhiều bước xử lý nền, tải lớn |
| Serverless | Viết hàm, nhà cung cấp lo hạ tầng | Tải thất thường, tác vụ ngắn |
| Cloud-native | Docker, Kubernetes, CI/CD, hạ tầng dưới dạng code | Vận hành ổn định ở quy mô lớn |

### Mẫu tổ chức code (bên trong một service hoặc app)

| Mẫu | Ý chính | Hay gặp ở |
|---|---|---|
| MVC | Controller điều phối Model và View | Web backend (Rails, Django, Laravel, Spring) |
| MVP | View chỉ hiển thị, Presenter điều khiển hai chiều | Android cũ, desktop |
| MVVM | ViewModel giữ state, View tự cập nhật | Mobile hiện đại, Vue, Angular |
| Flux/Redux | Một store, luồng dữ liệu một chiều | Frontend phức tạp |
| Clean/Hexagonal | Lõi nghiệp vụ không phụ thuộc framework | Service cần dễ test, dễ đổi công nghệ |

### Ghép cho dự án này

| Tầng | Lựa chọn |
|---|---|
| App di động | React Native: component + custom hook (gần MVVM) + TanStack Query |
| Cổng vào | API Gateway hoặc BFF (gom dữ liệu cho mobile) |
| Backend | FastAPI modular monolith, mỗi module gồm router, schemas, models, service, repository, trả JSON |
| Dữ liệu | PostgreSQL (pgvector), Redis, hàng đợi Celery/ARQ, kho lưu file (S3 hoặc R2) |
| Hướng phát triển | Tách microservices khi đo được nhu cầu thật |

Quy tắc nếu sau này tách microservices: mỗi service có database riêng, không truy vấn thẳng bảng của service khác, giao tiếp qua REST/gRPC hoặc event.

## Bổ sung module (2026-11-10)

- `modules/spaces/` (lát F4b): Không gian là cấp cha của tài liệu, hội thoại, bộ thẻ và trắc nghiệm, nên tách thành module riêng thay vì đặt trong `documents`. Các module khác gọi `SpaceService` để kiểm tra Không gian thuộc về người dùng, không đọc thẳng bảng `spaces`.

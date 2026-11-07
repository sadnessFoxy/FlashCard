# Contract

`openapi.yaml` là nguồn sự thật duy nhất về API giữa frontend và backend.

## Quy tắc

- Thứ tự khi API đổi: sửa contract trước, rồi backend, rồi sinh lại client cho frontend.
- `frontend/src/api/generated/` do công cụ sinh ra, **không sửa tay**.
- CI kiểm tra breaking change giữa phiên bản contract mới và cũ.

## Quy ước chung

- Đặt tên: snake_case cho field JSON, camelCase cho TypeScript generated.
- Mã lỗi: trả về object `{ "code": "ERROR_CODE", "message": "..." }`.
- Phân trang: cursor-based, field `next_cursor` và `limit`.
- Phiên bản API: prefix `/v1`.
- Streaming (hỏi đáp): dùng Server-Sent Events (SSE), mỗi event là một JSON chunk.
- Mã lỗi AI: `AI_TEMPORARILY_UNAVAILABLE`, `AI_RATE_LIMITED`, `USER_QUOTA_EXCEEDED`, `CONTEXT_TOO_LONG`.

## Sinh API client

```bash
make gen-api
```

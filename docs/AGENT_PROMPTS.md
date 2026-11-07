# Câu lệnh giao việc cho agent

> Dán từng câu lệnh vào agent theo thứ tự. Mỗi câu lệnh giả định agent đã có `AGENTS.md` và thư mục `docs/` trong repo. Thay chỗ `<...>` nếu có.
> Sau mỗi lát: bạn tự chạy thử và `git commit` trước khi giao lát tiếp theo.

## Mẫu chung cho mọi lát

```
Đọc AGENTS.md, docs/PLAN.md, docs/DECISIONS.md và các tài liệu liên quan trong bản đồ tài liệu.
Thực hiện lát <TÊN LÁT> trong docs/PLAN.md (giai đoạn F).
Trước khi viết code: nếu chưa có đặc tả thì tạo docs/specs/<ten-lat>.md từ docs/specs/_TEMPLATE.md và dừng lại để tôi duyệt.
Sau khi tôi duyệt: cập nhật contract/openapi.yaml trước, rồi backend, rồi frontend, rồi test.
Chạy lint, kiểm tra kiểu và test. Không tick việc trong PLAN.md nếu chưa đạt định nghĩa "xong".
Khi xong, tóm tắt: đã thay đổi gì, cách chạy thử để tôi kiểm tra, điểm cần tôi quyết định.
Không tự quyết các việc trong mục "Hỏi người dùng trước khi làm" của AGENTS.md.
```

## Bước 0. Khởi tạo dự án (giai đoạn 1)

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

## F1. Khung chạy xuyên suốt

```
Làm lát F1 trong docs/PLAN.md: một endpoint thật đi từ frontend qua backend tới database.
Viết contract/openapi.yaml (contract-first) cho /health và một endpoint kiểm tra kết nối database,
sinh API client cho frontend từ contract, thêm test bảo đảm backend khớp contract.
Frontend có một màn hình hiển thị trạng thái kết nối tới backend (chạy được trên web).
Thêm CI cơ bản (lint, kiểm tra kiểu, test) cho GitHub Actions.
```

## F2. Đăng ký và đăng nhập bằng email

```
Làm lát F2: đăng ký, đăng nhập bằng email và mật khẩu, duy trì và kết thúc phiên (docs/BUSINESS_FLOWS.md U1, U4; docs/SECURITY.md).
Tuân thủ quy tắc R3, R12, R15: mật khẩu băm argon2 hoặc bcrypt, access token ngắn hạn, refresh token xoay vòng và chỉ lưu dạng băm,
giới hạn số lần đăng nhập sai, thông báo lỗi không lộ email có tồn tại hay không.
Token: mobile lưu bằng secure store, web dùng cookie httpOnly (storage/session.native.ts và session.web.ts).
Màn hình 1 (đăng nhập, đăng ký) song ngữ qua i18n. Viết các test trong docs/TESTING.md liên quan xác thực.
Viết đặc tả trước và chờ tôi duyệt.
```

## F4b. Không gian học tập

```
Làm lát F4b: Không gian (docs/BUSINESS_FLOWS.md U16, docs/DATA_MODEL.md mục Không gian, màn hình 5 trong docs/SCREENS.md).
Tạo, đổi tên, xóa không gian (có xác nhận), không gian mặc định khi tải tài liệu đầu tiên. Kiểm tra quyền theo chủ sở hữu ở mọi truy vấn (R4).
```

## F5. Tải tài liệu và xử lý nền (PDF)

```
Làm lát F5: tải tài liệu PDF vào một không gian và xử lý nền đến READY (U5, docs/DATA_MODEL.md máy trạng thái, docs/AI_PIPELINE.md).
Giới hạn: 20 MB, 200 trang, 10 tài liệu mỗi người. Idempotency-Key khi tải. Worker ARQ: trích văn bản, chia đoạn theo cấu trúc, tạo embedding 768 chiều, lưu kèm số trang.
Mọi lời gọi AI qua integrations/llm_gateway và providers/gemini.py (R5), đọc tên mô hình và khóa từ cấu hình.
Hiện thông báo dữ liệu gửi cho Google ở lần tải đầu và lưu sự đồng ý (user_consents).
Khóa Gemini API: tôi sẽ đặt vào backend/.env, hãy nhắc tôi và không bao giờ in giá trị khóa ra.
Dùng nhà cung cấp AI giả (fake provider) cho test.
```

## F6. Quản lý tài liệu

```
Làm lát F6: danh sách, chi tiết, thử lại khi FAILED, xóa tài liệu, chuyển tài liệu sang không gian khác (U6).
Xóa theo máy trạng thái: DELETING ngay, dọn nền file gốc, chunk, vector, job. Lịch sử hội thoại giữ lại, trích dẫn hiện "tài liệu đã xóa".
```

## F7. Hỏi đáp trên nhiều tài liệu

```
Làm lát F7: hỏi đáp có trích dẫn, trả lời dần (streaming) trong một không gian (U7, U8; docs/AI_PIPELINE.md; docs/QUOTA_AND_RESILIENCE.md).
Truy xuất chỉ trong tài liệu READY của chủ sở hữu và thuộc không gian, lọc trước khi vào ngữ cảnh. Trích dẫn kèm tên tài liệu và số trang.
Không đủ căn cứ thì nói không tìm thấy. Hạn mức khoảng 30 câu mỗi ngày, mã lỗi hạn mức trong contract, chế độ chỉ tìm đoạn khi AI ngừng.
Thêm test mô phỏng nhà cung cấp AI trả lỗi hết hạn mức (docs/TESTING.md).
```

## F8. Xem trích dẫn và lịch sử hội thoại

```
Làm lát F8: màn hình xem trang được trích dẫn và danh sách, mở lại, xóa hội thoại (U7; màn hình 10, 11).
```

## F9. Flashcard

```
Làm lát F9: bộ thẻ, AI đề xuất thẻ rồi người học xem, sửa, bỏ chọn mới lưu (AI không tự lưu), tạo thẻ bằng tay, sửa, xóa (U11; màn hình 12, 13, 14).
Tạo thẻ tính hạn mức AI riêng với hỏi đáp. Hết hạn mức thì vẫn tạo bằng tay được.
```

## F10. Ôn tập SM-2

```
Làm lát F10: ôn tập lặp lại ngắt quãng theo SM-2 và màn hình kết quả (U12; màn hình 15, 16).
Không gọi AI. Hoạt động khi mất mạng: lưu tạm kết quả và đồng bộ sau, không ghi trùng. Viết test tính lịch SM-2.
```

## F3. Đăng nhập Google

```
Làm lát F3: đăng nhập bằng Google (U1). Backend xác thực ID token (R15). Quy tắc liên kết tài khoản: tự liên kết nếu email Google đã xác minh.
Khi cần Google OAuth client, hãy nhắc tôi tạo và hướng dẫn từng bước; không tự bịa giá trị.
```

## F4. Xác minh email và quên mật khẩu

```
Làm lát F4: xác minh email, quên và đặt lại mật khẩu (U2, U3; màn hình 2, 3). Token dùng một lần, hạn ngắn, chỉ lưu dạng băm.
Khi chạy local gửi email qua Mailpit (http://localhost:8025). Tài khoản chưa xác minh chưa được tải tài liệu.
```

## F15. Hồ sơ và cài đặt

```
Làm lát F15: ngôn ngữ giao diện, lượt hỏi còn lại, đổi mật khẩu, đăng xuất, xóa tài khoản (U4, U9, U10; màn hình 4).
```

## F11, F12, F13, F14

```
Làm lát F11 (trắc nghiệm, U13, điểm do code chấm), F12 (tóm tắt theo chương, theo yêu cầu, U15), F13 (tài liệu Word), F14 (tài liệu scan: Gemini đọc trực tiếp, Tesseract dự phòng; hãy thử trên tài liệu scan tiếng Việt thật và báo kết quả trước khi chốt).
Làm từng lát một theo mẫu chung, mỗi lát một lần giao.
```

## F16. Quản trị

```
Làm lát F16: giao diện quản trị web (A1 đến A7, màn hình 20 đến 25). API /v1/admin/*, kiểm tra vai trò ở backend, quản trị viên không xem nội dung tài liệu và hội thoại, mọi thao tác ghi audit_logs (R13).
Quản trị viên đầu tiên tạo bằng script, không có đăng ký quản trị công khai.
```

## Khi agent làm sai hoặc bị kẹt

```
Dừng lại. Đọc lại AGENTS.md, nhất là các quy tắc cứng R1 đến R15 và mục "Hỏi người dùng trước khi làm".
Cho tôi biết: bạn đang làm lát nào, đã thay đổi những file nào, điều gì đang lỗi (kèm thông báo lỗi), và đề xuất cách sửa. Chưa sửa gì cho đến khi tôi đồng ý.
```

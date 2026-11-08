# Quyết định và câu hỏi mở

> **Dành cho agent:** dòng có trạng thái `Chưa chốt` nghĩa là chưa có quyết định. **Không tự quyết**, hãy hỏi người dùng, rồi ghi kết quả vào đây (lựa chọn, lý do, ngày chốt).

## Bảng quyết định

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
| Kho lưu file gốc | SeaweedFS (giao diện S3) khi chạy local, cổng 9000 | Thay MinIO vì image `minio/minio` không còn tải được từ Docker Hub và quay.io; cùng giao diện S3 nên code không đổi | 2026-11-08 | Đã chốt |
| Mô hình chat Gemini | `gemini-3.5-flash-lite` | Bản ổn định, miễn phí, rẻ (0,30/2,50 USD mỗi 1M token vào/ra nếu trả phí); là mô hình Google chọn thay cho `gemini-2.5-flash`. Nếu chất lượng không đủ cho hỏi đáp thì nâng lên `gemini-3.6-flash` chỉ bằng đổi cấu hình | 2026-11-08 | Đã chốt (người dùng nhờ chọn) |
| Mô hình embedding Gemini | `gemini-embedding-2`, 768 chiều (`outputDimensionality`) | Bản ổn định, miễn phí, nhận tới 8192 token, mới hơn nên ít rủi ro bị ngừng (đổi mô hình phải tạo lại toàn bộ vector). Phương án dự phòng: `gemini-embedding-001` (rẻ hơn, chỉ văn bản, 2048 token). Thử trên tài liệu tiếng Việt thật ở lát F5 | 2026-11-08 | Đã chốt (người dùng nhờ chọn), chờ thử nghiệm |
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

## Rủi ro & câu hỏi mở

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

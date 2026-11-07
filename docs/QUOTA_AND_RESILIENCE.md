# Hạn mức AI và chế độ suy giảm

> **Khi nào đọc:** khi làm `llm_gateway`, module `usage`, worker, mã lỗi API, hoặc bất kỳ chỗ nào gọi AI và phải xử lý lỗi hạn mức.

## Hành vi khi hết hạn mức AI

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

## Giá trị khởi điểm đã chốt

| Mục | Giá trị |
|---|---|
| Ngân sách AI | 0 đồng (gói miễn phí); hạn mức hệ thống bằng giới hạn miễn phí của nhà cung cấp |
| Hạn mức hỏi đáp mỗi người | Khoảng 30 câu mỗi ngày, cấu hình được, có thể hạ khi hạn mức AI toàn hệ thống còn ít (cách hạ chưa chốt) |
| Giới hạn tải lên | Khoảng 20 MB, 200 trang, 10 tài liệu mỗi người |
| Cảnh báo ngân sách | 50%, 80%, 100% |
| Kênh nhận cảnh báo | Chưa chốt |

Quản trị viên xem mức dùng, đặt hạn mức riêng cho từng người và bật công tắc khẩn cấp tắt AI trong giao diện quản trị (docs/BUSINESS_FLOWS.md, nhóm A).

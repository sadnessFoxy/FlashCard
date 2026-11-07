# Quy trình nghiệp vụ

> **Khi nào đọc:** trước khi viết đặc tả (`docs/specs/`), contract hoặc code cho bất kỳ tính năng nào. File này mô tả mỗi luồng từ góc nhìn người dùng, quản trị viên và hệ thống.
>
> **Dành cho agent:** giá trị đánh dấu `[cần chốt]` chưa được quyết định, `[đề xuất]` là gợi ý chưa được người dùng xác nhận. Không tự điền; hỏi người dùng rồi ghi vào docs/DECISIONS.md. Danh sách endpoint ở cuối là **dự kiến**; `contract/openapi.yaml` mới là nguồn sự thật.

## Giá trị đã chốt (dùng cho mọi luồng)

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

## Tác nhân

| Tác nhân | Vai trò |
|---|---|
| Người học | Người dùng cuối: tải tài liệu, hỏi đáp, ôn tập |
| Quản trị viên | Theo dõi sử dụng và ngân sách AI, quản lý người dùng, theo dõi job, cấu hình hạn mức |
| Hệ thống | API, worker nền (ARQ), `llm_gateway` |
| Nhà cung cấp AI | Gemini API (bên ngoài) |
| Nhà cung cấp đăng nhập | Google (bên ngoài) |
| Dịch vụ gửi email | Dùng cho xác minh email và đặt lại mật khẩu `[cần chốt: nhà cung cấp]` |

---

# Phần 1. Luồng người dùng

## Chức năng bản 1 (đầy đủ chức năng)

### U1. Đăng ký và đăng nhập

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

### U2. Xác minh email (chỉ tài khoản email và mật khẩu)

1. Hệ thống gửi email chứa liên kết hoặc mã, dùng một lần, có hạn ngắn.
2. Người dùng xác nhận; tài khoản chuyển sang trạng thái đã xác minh.
3. Cho phép gửi lại, có giới hạn tần suất.
4. Tài khoản chưa xác minh bị giới hạn những gì `[cần chốt: ví dụ không cho tải tài liệu]`.

### U3. Quên mật khẩu

1. Người dùng nhập email.
2. Hệ thống **luôn trả cùng một thông báo** (không tiết lộ email có tồn tại), nếu có thì gửi liên kết hoặc mã đặt lại: dùng một lần, hạn ngắn.
3. Người dùng đặt mật khẩu mới; mọi refresh token cũ bị thu hồi; gửi email thông báo mật khẩu đã đổi.
4. Tài khoản chỉ có Google: hướng dẫn đăng nhập bằng cách đó `[cần chốt: có cho thêm mật khẩu không]`.

### U4. Duy trì và kết thúc phiên

- Access token hết hạn (khoảng 15 phút): app gọi refresh **một lần** rồi gửi lại yêu cầu. Refresh có xoay vòng token.
- Refresh thất bại: xóa phiên, về màn hình đăng nhập, giữ lại dữ liệu người dùng đang soạn nếu có.
- Đăng xuất: thu hồi refresh token ở backend, xóa phiên ở app.
- Tài khoản bị quản trị viên khóa: phiên bị thu hồi, đăng nhập bị từ chối kèm thông báo rõ ràng.

### U5. Tải tài liệu lên

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

### U6. Quản lý tài liệu

| Hành động | Hành vi |
|---|---|
| Xem danh sách | Chỉ thấy tài liệu của mình; hiện tên, trạng thái, thời điểm tải |
| Xem chi tiết | Trạng thái, lỗi (nếu có), số trang |
| Xóa | Chuyển `DELETING` ngay (biến mất khỏi danh sách và tìm kiếm); dọn nền file gốc, đoạn văn bản, vector, job đang chờ; xong thì xóa hẳn |
| Hội thoại cũ có trích dẫn tài liệu đã xóa | **Giữ lịch sử**; trích dẫn hiện "tài liệu đã xóa" (dùng bản ghi nhanh tên tài liệu và số trang đã lưu cùng tin nhắn) |

### U7. Hỏi đáp trên nhiều tài liệu

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

### U8. Khi AI hết hạn mức hoặc tạm ngừng

Người dùng thấy:
- Hỏi đáp: chỉ hiện các đoạn liên quan kèm tên tài liệu và số trang, không có lời giải thích do AI sinh, kèm thông báo "AI tạm nghỉ".
- Xem tài liệu, lịch sử hội thoại, flashcard có sẵn: dùng bình thường.
- Tải tài liệu mới: vẫn nhận file; tài liệu chờ xử lý (`PAUSED_QUOTA`) và tự tiếp tục khi AI hoạt động lại.
- Hết lượt cá nhân: thấy số lượt và thời điểm được dùng tiếp.
- Hạn mức mỗi người có thể được hạ xuống khi hạn mức AI toàn hệ thống còn ít `[cần chốt: cách hạ]`.

Chi tiết kỹ thuật: docs/QUOTA_AND_RESILIENCE.md.

### U9. Xóa tài khoản

| Bước | Hệ thống làm gì |
|---|---|
| 1 | Người dùng yêu cầu xóa; yêu cầu xác nhận lại (mật khẩu, hoặc đăng nhập lại bằng Google) |
| 2 | Thu hồi mọi token; khóa tài khoản ngay |
| 3 | Xóa tài liệu theo U6, hội thoại, flashcard, nhật ký ôn tập, dữ liệu sử dụng gắn với tài khoản |
| 4 | Dữ liệu còn trong bản sao lưu được xóa theo chu kỳ, **tối đa 30 ngày**; ghi rõ trong chính sách quyền riêng tư |
| 5 | Xác nhận cho người dùng |

Nên có dù chỉ chạy thử, vì liên quan đến quyền riêng tư của người dùng.

### U10. Ngôn ngữ giao diện

Giao diện hỗ trợ tiếng Việt và tiếng Anh. Mặc định theo ngôn ngữ thiết bị, đổi được trong cài đặt và lưu theo tài khoản. Mọi chuỗi hiển thị qua i18n, kể cả thông báo lỗi từ mã lỗi API.

### U11. Tạo flashcard

1. Người học chọn tài liệu, chương hoặc một câu trả lời, yêu cầu tạo thẻ.
2. Kiểm tra hạn mức (tính riêng với hỏi đáp); AI đề xuất danh sách thẻ.
3. Người học **xem, sửa, bỏ chọn** rồi mới lưu. AI không tự lưu thẻ.
4. Mỗi thẻ ghi nguồn (tài liệu, trang) để quay lại đọc.

### U12. Ôn tập lặp lại ngắt quãng (SM-2)

1. App hiện các thẻ đến hạn hôm nay.
2. Người học xem mặt trước, tự lật, tự chấm mức nhớ.
3. Hệ thống ghi nhật ký ôn tập và tính ngày ôn kế tiếp theo SM-2 hoặc biến thể gần giống; tham số chi tiết do đặc tả quyết định.
4. Luồng này **không cần AI**, nên vẫn chạy khi AI ngừng; nên hoạt động được offline và đồng bộ sau.

### U13. Câu hỏi trắc nghiệm

AI sinh câu hỏi và đáp án đúng cùng lúc, kèm nguồn trích dẫn. Việc chấm điểm do code so khớp đáp án đã lưu, không nhờ AI chấm lại. Người học xem lại câu sai kèm nguồn.

### U14. Tài liệu scan (không có lớp văn bản)

1. Worker phát hiện tài liệu không có lớp văn bản.
2. **Mặc định:** gửi trang cho Gemini đọc trực tiếp (miễn phí trong hạn mức, tính vào hạn mức AI); giới hạn số trang scan mỗi tài liệu vì tốn token `[cần chốt: giới hạn]`.
3. **Dự phòng:** khi hết hạn mức hoặc AI ngừng, dùng OCR chạy cục bộ (Tesseract, gói ngôn ngữ tiếng Việt và tiếng Anh) thay vì để job nằm chờ; chất lượng thấp hơn nên ghi nhận phương pháp OCR đã dùng cho từng tài liệu.
4. Hướng này cần được **thử nghiệm trên 3 đến 5 tài liệu scan tiếng Việt thật** trước khi coi là chốt hẳn (xem docs/AI_PIPELINE.md).

### U15. Tóm tắt theo chương

1. Người học mở tài liệu `READY` và chọn xem tóm tắt theo chương.
2. Hệ thống xác định chương hoặc mục từ mục lục hoặc tiêu đề trong văn bản; nếu không có thì chia theo khoảng trang.
3. Người học yêu cầu tóm tắt từng chương `[đề xuất: tạo theo yêu cầu, không tự tạo hàng loạt; cần chốt]`. Kiểm tra hạn mức AI (tính riêng).
4. AI tóm tắt, mỗi ý kèm trang nguồn; kết quả được lưu để không tính lại.
5. Hết hạn mức AI: các tóm tắt đã lưu vẫn xem được, chưa có thì báo rõ lý do.

### U16. Không gian học tập

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

## Bản 2 (chỉ nêu tên, chưa mô tả luồng)

Chia sẻ bộ tài liệu và học nhóm · thống kê tiến độ nâng cao · nhập bằng giọng nói · tối ưu bố cục web cho máy tính · tải sẵn bộ thẻ để dùng offline hoàn chỉnh.

---

# Phần 2. Luồng quản trị (bản 1)

> Giao diện quản trị chỉ dùng trên web `[đề xuất: nhóm route riêng trong cùng codebase frontend; cần chốt]`. API quản trị tách tiền tố `/v1/admin/`, kiểm tra vai trò ở backend; không dựa vào việc ẩn nút ở giao diện.

### A1. Đăng nhập và phân quyền quản trị

- Có hai vai trò: người dùng và quản trị viên. Quản trị viên đầu tiên được tạo bằng script hoặc cấu hình, **không có đăng ký quản trị công khai**.
- Tài khoản quản trị dùng cùng cơ chế đăng nhập, `[cần chốt: có bắt buộc xác thực hai bước không]`.
- Mọi API quản trị kiểm tra vai trò ở backend và ghi nhật ký kiểm toán (A7).

### A2. Tổng quan sử dụng và ngân sách AI

Màn hình tổng quan hiển thị:
- Số người dùng, số người hoạt động mỗi ngày
- Số tài liệu theo trạng thái, số job lỗi hoặc đang tạm dừng
- Số câu hỏi mỗi ngày, lượng token đã dùng, phần trăm hạn mức hoặc ngân sách AI đã dùng
- Trạng thái circuit breaker, độ dài hàng đợi
- Các chỉ số thời gian phản hồi (p95 API, thời gian tới chữ đầu tiên)

### A3. Quản lý người dùng

| Hành động | Hành vi |
|---|---|
| Xem danh sách, tìm kiếm | Email, ngày tạo, cách đăng nhập, trạng thái, số tài liệu, mức dùng |
| Khóa, mở khóa | Khóa thì thu hồi phiên ngay; ghi lý do |
| Đặt hạn mức riêng | Tăng hoặc giảm hạn mức hỏi đáp cho một người, có thời hạn |
| Buộc đăng xuất | Thu hồi toàn bộ refresh token |
| Hỗ trợ xóa tài khoản theo yêu cầu | Thực hiện quy trình U9 |

**Quyền riêng tư `[đề xuất, cần xác nhận]`:** quản trị viên **không xem được nội dung tài liệu hay hội thoại** của người dùng, chỉ thấy siêu dữ liệu và thống kê. Nếu cần xem để hỗ trợ, phải có cơ chế riêng có sự đồng ý của người dùng và được ghi nhật ký.

### A4. Theo dõi tài liệu và job

- Danh sách job theo trạng thái (`QUEUED`, `PROCESSING`, `FAILED`, `PAUSED_QUOTA`), kèm nguyên nhân lỗi (không kèm nội dung tài liệu).
- Thử lại job `FAILED`; kích hoạt lại job `PAUSED_QUOTA` thủ công khi hạn mức đã phục hồi (dù hệ thống cũng tự chạy lại).
- Xem độ dài hàng đợi và thời gian xử lý trung bình.

### A5. Cấu hình hạn mức và giới hạn

Các giá trị đổi được mà không cần triển khai lại:
- Hạn mức hỏi đáp mặc định mỗi người mỗi ngày
- Giới hạn tải lên (kích thước, số trang, số tài liệu)
- Ngưỡng cảnh báo ngân sách
- Công tắc khẩn cấp để tạm tắt tính năng AI

Mọi thay đổi cấu hình ghi nhật ký kiểm toán (ai, đổi gì, giá trị cũ và mới).

### A6. Cảnh báo

Quản trị viên nhận cảnh báo khi: ngân sách hoặc hạn mức AI chạm 50%, 80%, 100%; circuit breaker mở; hàng đợi nghẽn hoặc tỷ lệ job lỗi cao; một người dùng dùng bất thường nhiều so với trung bình. Kênh nhận `[cần chốt: email, Telegram hoặc kênh khác]`.

### A7. Nhật ký kiểm toán

- Mọi thao tác quản trị (khóa người dùng, đổi hạn mức, đổi cấu hình, thử lại job) ghi: ai, làm gì, trên đối tượng nào, lúc nào, giá trị cũ và mới.
- Nhật ký chỉ thêm, không sửa hay xóa qua ứng dụng.
- Quản trị viên xem và lọc được nhật ký.

---

# Bảng luồng và endpoint dự kiến

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

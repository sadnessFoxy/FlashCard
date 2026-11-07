# Danh sách màn hình

> **Khi nào đọc:** trước khi dựng giao diện hoặc viết đặc tả có màn hình. Mỗi màn hình liên kết với luồng trong docs/BUSINESS_FLOWS.md.
>
> **Dành cho agent:** đây là danh sách chức năng ở mức màn hình, **chưa có thiết kế hình ảnh**. Số lượng màn hình không phải mục tiêu cần tối thiểu hóa; điều quan trọng là đủ chức năng. Mọi chuỗi hiển thị đi qua i18n (tiếng Việt và tiếng Anh).

## Quy tắc chung cho mọi màn hình

- Mỗi màn hình có đủ các trạng thái: đang tải, rỗng (có hướng dẫn việc cần làm tiếp), lỗi (có nút thử lại), thành công.
- Lỗi hạn mức AI (`USER_QUOTA_EXCEEDED`, `AI_TEMPORARILY_UNAVAILABLE`, `AI_RATE_LIMITED`, `CONTEXT_TOO_LONG`) hiển thị thông báo thân thiện, không hiển thị mã kỹ thuật; hiện số lượt còn lại và thời điểm đặt lại khi có.
- Màn hình dùng chung cho mobile và web, bố cục thích ứng: mobile dùng tab dưới, web dùng thanh bên.
- Điều hướng chính của người dùng: **Không gian**, **Thẻ học**, **Hồ sơ**. Tài liệu, Hỏi đáp, Thẻ, Trắc nghiệm nằm trong từng không gian (các tab).
- Màn hình quản trị chỉ có trên web, chỉ vai trò admin vào được.
- Không hiển thị nội dung của người dùng khác ở bất kỳ màn hình nào.

## Người dùng (mobile và web)

### Tài khoản

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 1 | Đăng nhập và đăng ký | U1 | Hai tab; nhập email và mật khẩu; nút đăng nhập Google; liên kết sang quên mật khẩu | Sai thông tin (thông báo chung), bị giới hạn số lần thử, tài khoản bị khóa |
| 2 | Quên và đặt lại mật khẩu | U3 | Nhập email, nhập mã hoặc mở liên kết, đặt mật khẩu mới | Thông báo luôn giống nhau dù email có tồn tại hay không; token hết hạn hoặc đã dùng |
| 3 | Xác minh email | U2 | Hướng dẫn kiểm tra email, nút gửi lại (có giới hạn tần suất) | Chưa xác minh bị giới hạn chức năng (chưa chốt) |
| 4 | Hồ sơ và cài đặt | U4, U9, U10 | Ngôn ngữ giao diện, lượt hỏi còn lại hôm nay, đổi mật khẩu, đăng xuất, xóa tài khoản (xác nhận lại) | Xóa tài khoản cần xác nhận lại bằng mật khẩu hoặc Google |

### Tài liệu

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 5 | Danh sách không gian và Chi tiết không gian | U6, U16 | Danh sách không gian (tên, số tài liệu, thẻ đến hạn; tạo, đổi tên, xóa); trong một không gian là các tab Tài liệu, Hỏi đáp, Thẻ, Trắc nghiệm. Tab Tài liệu: danh sách tài liệu, trạng thái xử lý, nút tải lên, mở chi tiết | Rỗng; đạt giới hạn 10 tài liệu; tài liệu `FAILED` và `PAUSED_QUOTA` có nhãn riêng |
| 6 | Tải tài liệu | U5 | Chọn file PDF hoặc Word; ở lần đầu hiện thông báo dữ liệu gửi cho Google và xin đồng ý; hiện giới hạn (khoảng 20 MB, 200 trang) | Sai định dạng, quá lớn, quá nhiều trang, mất mạng giữa chừng, file scan |
| 7 | Chi tiết tài liệu | U6, U15 | Tên, trạng thái, số trang, lỗi; thử lại, xóa; các lối tắt: hỏi đáp, tạo thẻ, tạo trắc nghiệm, xem tóm tắt | `DELETING` hiển thị đang xóa; tài liệu chưa `READY` khóa các lối tắt |
| 8 | Tóm tắt theo chương | U15 | Danh sách chương, nút tạo tóm tắt, nội dung tóm tắt kèm trang nguồn | Tóm tắt tốn hạn mức; chưa tạo thì hiện nút tạo |

### Hỏi đáp

| # | Màn hình | Luồng | Nội dung và hành động chính | Trạng thái đặc biệt |
|---|---|---|---|---|
| 9 | Hỏi đáp | U7, U8 | Chọn tập tài liệu, khung chat, câu trả lời hiện dần, trích dẫn bấm được, số lượt còn lại | Hết lượt; AI tạm nghỉ thì chỉ hiện các đoạn liên quan; không tìm thấy trong tài liệu; luồng bị ngắt |
| 10 | Xem trích dẫn | U7 | Mở đúng trang tài liệu được trích, đánh dấu đoạn liên quan | Tài liệu đã xóa thì hiện "tài liệu đã xóa" |
| 11 | Lịch sử hội thoại | U7 | Danh sách hội thoại, mở lại, xóa hội thoại | Rỗng |

### Học tập

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

## Quản trị (chỉ web)

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

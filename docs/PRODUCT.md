# Sản phẩm và phạm vi (ứng dụng FlashCard)

> **Khi nào đọc:** trước khi làm bất kỳ tính năng nào, để biết tính năng thuộc bản nào và có nằm trong phạm vi không.

## Mô tả sản phẩm

Trợ lý học tập từ tài liệu: người dùng tải giáo trình, ghi chú, đề cương (PDF, Word, tài liệu scan); app cho phép hỏi đáp dựa trên nội dung các tài liệu đó kèm trích dẫn trang, tạo flashcard, ôn tập, làm trắc nghiệm và xem tóm tắt theo chương. Chạy trên iOS, Android và web từ một codebase frontend. Giao diện tiếng Việt và tiếng Anh; hỗ trợ tài liệu tiếng Việt và tiếng Anh.

Ngoài phạm vi: thanh toán và mọi tính năng thu phí; phát hành lên App Store, Google Play (dự án chỉ là bản thử nghiệm chạy được hoàn chỉnh trên web và mobile). Tài liệu được tổ chức theo **Không gian** (môn học hoặc chủ đề), xem U16 trong docs/BUSINESS_FLOWS.md.

## Phạm vi theo bản

**Nguyên tắc:** ưu tiên đầy đủ chức năng; số màn hình không bị giới hạn trên (tối thiểu khoảng 10 đến 15). Danh sách màn hình: docs/SCREENS.md.

| Bản | Nội dung |
|---|---|
| 1 (đầy đủ chức năng) | **Tài khoản:** đăng ký, đăng nhập bằng email và mật khẩu, Google · xác minh email, quên mật khẩu · xóa tài khoản · giao diện song ngữ Việt, Anh. **Tài liệu:** tải lên PDF và Word (khoảng 20 MB, 200 trang, 10 tài liệu mỗi người) · tài liệu scan (Gemini đọc trực tiếp, Tesseract dự phòng) · xử lý nền · quản lý (xem, thử lại, xóa) · tóm tắt theo chương. **Hỏi đáp:** trên nhiều tài liệu, có trích dẫn, trả lời dần, khoảng 30 câu mỗi ngày · xem trích dẫn · lịch sử hội thoại. **Học tập:** flashcard (AI đề xuất, người học duyệt, hoặc tạo tay) · ôn tập lặp lại ngắt quãng (SM-2) · câu hỏi trắc nghiệm. **Quản trị (web):** tổng quan sử dụng và ngân sách AI, quản lý người dùng, theo dõi job, cấu hình hạn mức, nhật ký kiểm toán |
| 2 | Chia sẻ bộ tài liệu, học nhóm · thống kê tiến độ nâng cao · nhập bằng giọng nói · tối ưu bố cục web cho máy tính · tải sẵn bộ thẻ để dùng offline hoàn chỉnh |

Luồng nghiệp vụ chi tiết của từng tính năng (người dùng và quản trị): docs/BUSINESS_FLOWS.md. Chức năng ở mức màn hình: docs/SCREENS.md.

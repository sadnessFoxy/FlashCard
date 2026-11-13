# Đặc tả tính năng: F6. Quản lý tài liệu

- **Trạng thái:** Xong 2026-11-13. Tự chốt theo quyền người dùng cấp (2026-11-13); lựa chọn ghi ở mục 12
- **Thuộc bản:** 1
- **Luồng:** U6, U16 (chuyển tài liệu, xóa Không gian); màn hình 5 (danh sách) và 7 (chi tiết tài liệu)

## 1. Mục tiêu
Người dùng xem chi tiết một tài liệu, thử lại tài liệu lỗi, xóa tài liệu và chuyển tài liệu sang Không gian khác. Xóa tài liệu hoặc xóa cả Không gian phải dọn sạch file gốc, các đoạn văn và vector, và job đang chờ (docs/DATA_MODEL.md).

## 2. Luồng người dùng
- **Xem chi tiết:** bấm vào một tài liệu trong tab Tài liệu để mở màn hình chi tiết: tên, trạng thái, số trang, dung lượng, ngày tải, lý do lỗi (nếu có).
- **Thử lại:** tài liệu ở trạng thái `FAILED` hoặc `PAUSED_QUOTA` có nút Thử lại. Bấm thì chuyển sang `QUEUED` và được xử lý lại; các đoạn đã có vector được giữ lại.
- **Xóa:** cần xác nhận. Tài liệu chuyển sang `DELETING` và biến mất ngay khỏi danh sách và khỏi tìm kiếm. Worker xóa file gốc rồi xóa hẳn bản ghi; đoạn văn, vector và job bị xóa theo nhờ khóa ngoại.
- **Chuyển Không gian:** chọn Không gian đích trong danh sách Không gian của mình. Tài liệu đang `DELETING` thì không chuyển được.
- **Xóa Không gian:** mọi tài liệu bên trong chuyển sang `DELETING` và được dọn file như khi xóa từng tài liệu.

## 3. Màn hình
| Màn hình | Nội dung | Trạng thái |
|---|---|---|
| 7. Chi tiết tài liệu (`/spaces/documents/[id]`) | Tên, nhãn trạng thái, số trang, dung lượng, ngày tải; lý do lỗi; nút Thử lại, Chuyển Không gian, Xóa; các lối tắt Hỏi đáp, Tạo thẻ (khóa tới khi tài liệu `READY` và tới khi có F7, F9) | Đang tải, không tìm thấy, đang xử lý (tự làm mới) |
| Hộp chọn Không gian đích | Danh sách Không gian khác của người dùng | Không có Không gian nào khác: hướng dẫn tạo |

## 4. API
| Endpoint | Phương thức | Phản hồi | Mã lỗi |
|---|---|---|---|
| `/v1/documents/{id}/retry` | POST | 200 `Document` (`QUEUED`) | 404; 409 `DOCUMENT_NOT_RETRYABLE` (chỉ thử lại được từ `FAILED` hoặc `PAUSED_QUOTA`) |
| `/v1/documents/{id}` | DELETE | 204 | 404 (kể cả khi đã ở `DELETING`) |
| `/v1/documents/{id}/move` | POST `{space_id}` | 200 `Document` | 404 tài liệu hoặc Không gian đích |

## 5. Dữ liệu
Không có bảng mới. Bước dọn dẹp là một job ARQ mới, `purge_document(document_id, storage_key)`: job tự mang theo khóa lưu trữ, nên vẫn xóa được file kể cả khi bản ghi đã mất do xóa Không gian.

## 6. Quy tắc
- Mọi chuyển trạng thái là cập nhật có điều kiện (R6). Xóa thắng mọi trạng thái khác: worker đang xử lý thấy `DELETING` thì dừng (đã có từ F5).
- Tác vụ định kỳ (cứ 10 phút) đưa lại vào hàng đợi các tài liệu nằm ở `DELETING` quá 10 phút. Như vậy nếu worker tắt giữa chừng, file vẫn được dọn.
- Dọn dẹp lặp lại nhiều lần cũng an toàn: file đã mất thì bỏ qua.
- Thử lại tạo job mới với `attempts = 0`.

## 7. Quyền
Mọi thao tác lọc theo chủ sở hữu (R4). Không gian đích khi chuyển cũng phải thuộc về người dùng. Tài liệu hay Không gian của người khác trả 404.

## 9. Tiêu chí nghiệm thu
1. Xóa tài liệu `READY`: nhận 204; danh sách và chi tiết không còn nó; sau khi worker chạy thì file gốc, các đoạn và job đều không còn.
2. Xóa trong lúc đang xử lý: worker dừng, không ghi đè thành `READY`; cuối cùng bản ghi bị xóa.
3. Thử lại tài liệu `FAILED`: chuyển sang `QUEUED`, có job mới, được đưa vào hàng đợi; thử lại tài liệu `READY` thì nhận 409.
4. Chuyển sang Không gian khác: tài liệu hiện trong danh sách của Không gian đích và không còn ở Không gian cũ; Không gian đích của người khác thì nhận 404.
5. Xóa Không gian có 2 tài liệu: cả 2 file gốc bị xóa khỏi kho.
6. Người khác gọi thử lại, xóa hay chuyển tài liệu: đều nhận 404, dữ liệu không đổi.
7. Giao diện: chi tiết, xác nhận xóa, thử lại, chuyển Không gian, song ngữ.

## 12. Lựa chọn đã tự chốt
- Cho phép thử lại thủ công cả tài liệu `PAUSED_QUOTA` (không phải chờ lượt tự động).
- Xóa trả 204 ngay; phần dọn dẹp chạy nền.
- Lối tắt Hỏi đáp và Tạo thẻ hiện nhưng bị khóa, kèm ghi chú, cho tới các lát F7 và F9.

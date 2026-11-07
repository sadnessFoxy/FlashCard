# Đặc tả tính năng: <tên tính năng>

> Sao chép file này thành `docs/specs/<ten-tinh-nang>.md`, điền đầy đủ và để người dùng duyệt **trước khi viết code**. Mục nào chưa biết thì ghi vào "Câu hỏi mở", không tự đoán.

- **Trạng thái:** Nháp / Đã duyệt / Đang làm / Xong
- **Thuộc bản:** 1 / 2 / 3 (xem docs/PRODUCT.md)
- **Giai đoạn liên quan:** (xem docs/PLAN.md)

## 1. Mục tiêu
Một đến hai câu: người dùng làm được gì sau khi tính năng này xong.

## 2. Luồng người dùng
Các bước theo thứ tự, gồm cả luồng lỗi chính.

## 3. Màn hình và hành vi giao diện
Danh sách màn hình, trạng thái (đang tải, rỗng, lỗi, thành công), khác biệt giữa mobile và web nếu có.

## 4. API
| Endpoint | Phương thức | Yêu cầu | Phản hồi | Mã lỗi |
|---|---|---|---|---|
| | | | | |

Cập nhật `contract/openapi.yaml` trước khi viết code.

## 5. Dữ liệu
Bảng, cột, ràng buộc, index cần thêm hoặc đổi; migration cần tạo (xem docs/DATA_MODEL.md).

## 6. Quy tắc nghiệp vụ
Các quy tắc và giới hạn (kích thước, số lượng, định dạng, trạng thái hợp lệ).

## 7. Quyền và bảo mật
Ai được làm gì; các kiểm tra quyền theo chủ sở hữu (xem docs/SECURITY.md).

## 8. AI và hạn mức (nếu có gọi AI)
Gọi AI ở bước nào, dữ liệu gửi đi là gì, hạn mức áp dụng, hành vi khi hết hạn mức (xem docs/QUOTA_AND_RESILIENCE.md).

## 9. Tiêu chí nghiệm thu
Viết dạng "Cho (điều kiện), Khi (hành động), Thì (kết quả)". Mỗi tiêu chí phải kiểm chứng được bằng test.

## 10. Test cần có
Unit, integration, E2E, kịch bản liên quan trong docs/TESTING.md.

## 11. Ngoài phạm vi
Những gì cố ý không làm ở lần này.

## 12. Câu hỏi mở
Những điều cần người dùng quyết định.

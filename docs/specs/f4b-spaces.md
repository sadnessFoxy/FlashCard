# Đặc tả tính năng: F4b. Không gian học tập

- **Trạng thái:** Đang làm (người dùng duyệt ngày 2026-11-10: Q1 = A, Q2 = A). Xong 2026-11-10
- **Thuộc bản:** 1
- **Giai đoạn liên quan:** F4b (giai đoạn F)
- **Luồng:** U16 trong docs/BUSINESS_FLOWS.md; màn hình 5 trong docs/SCREENS.md; mục "Không gian" trong docs/DATA_MODEL.md

## 1. Mục tiêu
Người dùng tạo các Không gian theo môn học (ví dụ "Giải tích 1"), đổi tên và xóa chúng. Các lát sau gắn tài liệu (F5), hội thoại (F7), bộ thẻ (F9), trắc nghiệm (F11) và tóm tắt (F12) vào một Không gian.

## 2. Luồng người dùng

**Xem danh sách**
1. Sau khi đăng nhập, tab **Không gian** hiện danh sách Không gian của chính người dùng, mới cập nhật nằm trên cùng.
2. Chưa có Không gian nào: hiện hướng dẫn và nút "Tạo không gian đầu tiên".

**Tạo**
1. Bấm "Tạo không gian", nhập tên, bấm Lưu.
2. Tên rỗng, quá dài hoặc trùng (xem Q1): báo lỗi ngay ở ô nhập.
3. Thành công: Không gian mới hiện đầu danh sách.

**Đổi tên**
1. Mở menu của một Không gian (hoặc mở Không gian rồi bấm Đổi tên), sửa tên, Lưu.
2. Lỗi như khi tạo.

**Xóa**
1. Chọn Xóa, hộp xác nhận nêu rõ những gì bị xóa cùng (xem Q2).
2. Xác nhận: Không gian biến mất khỏi danh sách. Hủy: không có gì thay đổi.

**Mở một Không gian**
1. Bấm vào Không gian: màn hình chi tiết có tên ở đầu và các tab Tài liệu, Hỏi đáp, Thẻ, Trắc nghiệm.
2. Ở lát này các tab chỉ hiện "sắp có"; tab Tài liệu được làm ở F5 và F6.

**Không gian mặc định** (quy tắc U16): khi người dùng tải tài liệu đầu tiên mà chưa có Không gian, hệ thống tự tạo một Không gian đặt tên theo tài liệu. F4b viết sẵn hàm nghiệp vụ và test cho quy tắc này; việc gọi hàm nằm ở F5 (luồng tải lên).

## 3. Màn hình và hành vi giao diện

| Màn hình | Nội dung | Trạng thái |
|---|---|---|
| 5a. Danh sách Không gian (tab Không gian) | Thẻ cho mỗi Không gian: tên, ngày cập nhật; nút tạo; menu Đổi tên, Xóa | Đang tải, rỗng (có hướng dẫn), lỗi (có nút thử lại), mất mạng |
| Hộp tạo / đổi tên | Một ô tên, nút Lưu và Hủy | Đang lưu, lỗi ở ô nhập |
| Hộp xác nhận xóa | Tên Không gian, mô tả hậu quả, nút Xóa (màu cảnh báo) và Hủy | Đang xóa |
| 5b. Chi tiết Không gian | Tên, Đổi tên, Xóa; 4 tab Tài liệu, Hỏi đáp, Thẻ, Trắc nghiệm với nội dung "sắp có" | Không gian không tồn tại hoặc đã bị xóa: báo và quay về danh sách |

- Hộp xác nhận tự làm bằng component chung: `Alert.alert` của React Native **không hoạt động trên web**.
- Số tài liệu và số thẻ đến hạn trên mỗi thẻ Không gian (theo U16) sẽ thêm ở F5 và F9, khi đã có dữ liệu để đếm. Đây là thay đổi bổ sung, không phá contract.
- Mọi chuỗi qua i18n (R14).

## 4. API

Tag `spaces` trong `contract/openapi.yaml`; mọi endpoint cần đăng nhập.

| Endpoint | Phương thức | Yêu cầu | Phản hồi | Mã lỗi |
|---|---|---|---|---|
| `/v1/spaces` | GET | | 200 `{items: Space[]}`, mới cập nhật trước | 401 |
| `/v1/spaces` | POST | `{name}` | 201 `Space` | 422 `VALIDATION_ERROR`, 409 `SPACE_NAME_TAKEN` |
| `/v1/spaces/{space_id}` | GET | | 200 `Space` | 404 `NOT_FOUND` |
| `/v1/spaces/{space_id}` | PATCH | `{name}` | 200 `Space` | 404, 409, 422 |
| `/v1/spaces/{space_id}` | DELETE | | 204 | 404 |

- `Space` = `{id, name, created_at, updated_at}`.
- Không gian của người khác trả **404** (không phải 403), để không lộ là ID đó có tồn tại.
- Danh sách không phân trang: mỗi người thường chỉ có vài chục Không gian. Nếu sau này cần thì thêm `next_cursor` theo quy ước trong `contract/README.md`, không phá tương thích.

## 5. Dữ liệu

Migration mới tạo bảng `spaces`:

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | UUID | khóa chính |
| `owner_id` | UUID | khóa ngoại `users.id`, xóa theo người dùng |
| `name` | varchar(100) | không rỗng |
| `created_at`, `updated_at` | timestamptz | |

- Index `spaces(owner_id, updated_at)` cho danh sách.
- Nếu chọn Q1 = A: thêm unique index `(owner_id, lower(name))`.
- Cột `space_id` trên `documents`, `conversations`... do các lát tạo ra các bảng đó thêm vào, như docs/DATA_MODEL.md đã mô tả.

## 6. Quy tắc nghiệp vụ

- **Tên:** bỏ khoảng trắng hai đầu, gộp nhiều khoảng trắng liên tiếp thành một; dài 1 đến 100 ký tự; được dùng tiếng Việt có dấu và emoji.
- **Trùng tên:** theo Q1.
- **Số lượng:** không giới hạn số Không gian (đã chốt); giới hạn 10 tài liệu tính trên cả tài khoản, kiểm tra ở F5.
- **Không gian mặc định:** tên lấy từ tên file tài liệu (bỏ đuôi `.pdf`, `.docx`), cắt còn 100 ký tự; nếu tên đã có thì thêm hậu tố " (2)", " (3)"...
- **Xóa:** ở lát này một Không gian chưa có gì bên trong, nên xóa là xóa hẳn dòng dữ liệu. Từ F5, xóa Không gian phải đi qua quy trình xóa tài liệu (trạng thái `DELETING`, dọn file và vector), như docs/DATA_MODEL.md đã quy định; lát F6 sẽ cập nhật lại hành vi này.

## 7. Quyền và bảo mật

- Mọi truy vấn lọc theo `owner_id` của người đang đăng nhập (R4). Đọc, sửa hay xóa Không gian của người khác đều trả 404.
- `owner_id` lấy từ token, không bao giờ nhận từ request body.
- Không ghi tên Không gian vào log (có thể là dữ liệu cá nhân); log chỉ có `space_id` và `user_id`.

## 8. AI và hạn mức
Không gọi AI.

## 9. Tiêu chí nghiệm thu

1. Cho người dùng đã đăng nhập, Khi tạo Không gian tên "  Giải   tích 1 ", Thì nhận 201 và tên lưu là "Giải tích 1".
2. Cho tên rỗng, toàn khoảng trắng hoặc dài 101 ký tự, Khi tạo hoặc đổi tên, Thì nhận 422 và không có gì thay đổi.
3. Cho đã có "Giải tích 1", Khi tạo "giải TÍCH 1", Thì kết quả theo Q1.
4. Cho người dùng có 3 Không gian, Khi lấy danh sách, Thì nhận đúng 3 cái của mình, cái mới cập nhật nhất đứng đầu; không thấy Không gian của người khác.
5. Cho Không gian của người A, Khi người B GET, PATCH hoặc DELETE nó, Thì người B nhận 404 và dữ liệu của A không đổi.
6. Cho một Không gian, Khi đổi tên, Thì `updated_at` tăng và nó lên đầu danh sách.
7. Cho một Không gian, Khi xóa, Thì nhận 204, GET trả 404, và danh sách không còn nó.
8. Cho người dùng chưa có Không gian, Khi hàm tạo Không gian mặc định chạy với tài liệu "Giáo trình Giải tích.pdf", Thì tạo Không gian "Giáo trình Giải tích"; chạy lần nữa với cùng tên thì ra "Giáo trình Giải tích (2)" (nếu Q1 = A).
9. Cho không có token, Khi gọi bất kỳ endpoint nào, Thì nhận 401.
10. Cho giao diện, Khi tạo, đổi tên, xóa (có xác nhận) trên web, Thì danh sách cập nhật ngay, không cần tải lại trang; hộp xác nhận chạy được trên web.
11. Cho đổi ngôn ngữ sang tiếng Anh, Thì mọi chữ trên các màn hình Không gian đều là tiếng Anh.

## 10. Test cần có

- **Backend, API và integration (database test):** tiêu chí 1 đến 9, kiểm tra response theo contract như F1 và F2; migration lên và xuống.
- **Backend, security:** truy cập chéo giữa người dùng (tiêu chí 5), đúng kịch bản "Người A truy cập ID của người B" trong docs/TESTING.md.
- **Backend, unit:** chuẩn hóa tên, đặt tên Không gian mặc định.
- **Frontend:** danh sách (đang tải, rỗng, lỗi, có dữ liệu), tạo và lỗi tên trùng, đổi tên, xóa có xác nhận và hủy, tiếng Anh.

## 11. Ngoài phạm vi
- Tài liệu, hỏi đáp, thẻ, trắc nghiệm bên trong Không gian (F5, F7, F9, F11). Các tab chỉ hiện "sắp có".
- Số tài liệu và số thẻ đến hạn trên danh sách (F5, F9).
- Chuyển tài liệu sang Không gian khác (F6).
- Sắp xếp tùy chỉnh, ghim, màu hay biểu tượng cho Không gian.

## 12. Câu hỏi mở (đã trả lời)

**Q1. Có cho hai Không gian trùng tên trong cùng một tài khoản không?**
- **A (khuyến nghị):** không cho. So khớp không phân biệt hoa thường, nên "Giải tích 1" và "giải tích 1" bị coi là trùng. Trả 409 `SPACE_NAME_TAKEN`. Lợi ích: không nhầm lẫn khi chọn Không gian để tải tài liệu hay hỏi đáp.
- **B:** cho trùng tên, phân biệt bằng ngày tạo.

**Q2. Xác nhận khi xóa Không gian thế nào?**
- **A (khuyến nghị):** hộp xác nhận nêu rõ "Mọi tài liệu, hội thoại, bộ thẻ và trắc nghiệm trong không gian này sẽ bị xóa vĩnh viễn", có nút Xóa và Hủy.
- **B:** chặt hơn, bắt gõ lại tên Không gian mới bật được nút Xóa (giống GitHub khi xóa repo). An toàn hơn khi đã có nhiều tài liệu, nhưng phiền hơn.

Giả định đã đặt, không cần trả lời nếu đồng ý:
- Danh sách xếp theo lần cập nhật gần nhất (mới nhất trên cùng).
- Không gian của người khác trả 404 thay vì 403.
- Số tài liệu và số thẻ đến hạn hiển thị từ F5 và F9.

## 13. Ghi chú khi triển khai

- Tên được chuẩn hóa NFC trước khi so trùng, nên "Hóa học" gõ bằng hai kiểu bộ gõ tiếng Việt khác nhau vẫn bị coi là trùng.
- Đổi tên chỉ khác hoa thường của chính Không gian đó ("giải tích" thành "Giải Tích") được phép.
- Màn hình chi tiết nằm trong tab Không gian (`/spaces/[id]`) để thanh tab vẫn hiện.

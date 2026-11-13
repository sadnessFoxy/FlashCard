# Đặc tả tính năng: F10. Ôn tập lặp lại ngắt quãng (SM-2)

- **Trạng thái:** Xong (2026-11-13). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U12; màn hình 15 (Ôn tập), 16 (Kết quả ôn tập)

## 1. Mục tiêu
Người học ôn các thẻ đến hạn: xem mặt trước, tự lật, tự chấm mức nhớ. Hệ thống tính ngày ôn kế tiếp theo SM-2. Luồng này **không cần AI** nên vẫn chạy khi AI ngừng, và chạy được khi mất mạng: kết quả lưu trên máy, đồng bộ sau, không ghi trùng.

## 2. Luồng
1. Tab Thẻ của Không gian có nút **Ôn tập ngay (n thẻ)**; chi tiết bộ thẻ có **Bắt đầu ôn** (chỉ bộ đó).
2. Màn hình ôn: "Thẻ x/y", mặt trước, nút **Lật thẻ**, rồi 4 mức: **Quên, Khó, Được, Dễ**.
3. Thẻ chấm **Quên** quay lại cuối phiên cho đến khi nhớ.
4. Hết thẻ: màn hình kết quả gồm số lượt ôn, số lượt theo từng mức, danh sách thẻ khó (Quên hoặc Khó), thời điểm ôn kế tiếp sớm nhất; nếu còn kết quả chưa gửi được thì báo "đang lưu trên máy, sẽ đồng bộ khi có mạng".
5. Không có thẻ đến hạn: báo rõ.

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/reviews/due?space_id=&deck_id=&limit=` | GET | Thẻ đến hạn (quá hạn lâu nhất trước) và `total_due` |
| `/v1/reviews` | POST `{reviews: [{id, card_id, grade, reviewed_at}]}` | 1 đến 100 lượt; mỗi lượt trả `status` là `applied`, `duplicate`, `stale` hoặc `not_found`, kèm `due_at`, `interval_days` |

## 5. Dữ liệu (migration mới)
`review_logs`: `id` (do app tạo), `owner_id`, `flashcard_id`, `grade`, `reviewed_at`, lịch sau lượt ôn (`ease_after`, `interval_days_after`, `due_at_after`). Thêm `flashcards.last_reviewed_at`.

## 6. Quy tắc SM-2
- Mức quy về chất lượng SM-2: Quên = 1, Khó = 3, Được = 4, Dễ = 5.
- Hệ số dễ: `EF' = EF + (0,1 - (5 - q) × (0,08 + (5 - q) × 0,02))`, không dưới 1,3; thẻ mới EF = 2,5.
- q < 3 (Quên): số lần nhớ liên tiếp về 0, thẻ đến hạn lại sau 10 phút.
- q ≥ 3: lần 1 cách 1 ngày, lần 2 cách 6 ngày, sau đó khoảng cách cũ × EF (làm tròn); mức Dễ nhân thêm 1,3.
- Thẻ mới đến hạn ngay.

## 6b. Đồng bộ khi mất mạng
- App tạo `id` cho mỗi lượt chấm, lưu vào hàng đợi trên máy (AsyncStorage), rồi gửi theo lô tối đa 100.
- Gửi lại cùng `id` thì server trả `duplicate`, không đổi gì.
- Server áp dụng các lượt trong lô theo thời gian cũ trước. Lượt cũ hơn lần ôn mới nhất của thẻ (đến muộn từ máy khác) được ghi nhật ký với `stale`, không đổi lịch.
- `reviewed_at` ở tương lai (đồng hồ máy chạy nhanh) bị kéo về giờ server.
- Mất mạng thì giữ hàng đợi; gửi lại khi mở màn hình ôn hoặc sau lượt chấm kế tiếp.

## 7. Quyền và bảo mật
Chỉ thẻ của chính người dùng; thẻ của người khác trả `not_found`, Không gian của người khác trả 404. Kết quả ôn không phải bí mật nên được lưu bằng AsyncStorage (R12 chỉ cấm dùng nó cho token).

## 9. Tiêu chí nghiệm thu
1. Chấm thẻ đổi lịch đúng SM-2; thẻ rời danh sách đến hạn.
2. Gửi lại cùng `id`: không đổi gì.
3. Lô gửi sai thứ tự vẫn áp dụng theo thời gian; lượt cũ đến muộn là `stale`.
4. Không chạm thẻ của người khác; danh sách đến hạn đúng Không gian và bộ thẻ.
5. Đồng hồ máy chạy nhanh không đẩy lịch đi xa.
6. Vẫn chạy khi AI ngừng.
7. Unit test công thức SM-2 (docs/TESTING.md).
8. Giao diện: lật, chấm 4 mức, thẻ Quên quay lại, kết quả phiên, báo lưu tạm khi mất mạng, song ngữ.

## 12. Lựa chọn đã tự chốt
- Bốn mức chấm thay cho thang 0 đến 5 của SM-2 gốc (dễ dùng trên điện thoại).
- Thẻ Quên quay lại sau 10 phút (thay vì 1 ngày như SM-2 gốc) để ôn lại ngay trong phiên.
- Thêm thư viện `@react-native-async-storage/async-storage` cho hàng đợi offline (chạy được trên Expo Go; MMKV cần bản dev build).

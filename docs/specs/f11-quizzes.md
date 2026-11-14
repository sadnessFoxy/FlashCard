# Đặc tả tính năng: F11. Câu hỏi trắc nghiệm

- **Trạng thái:** Xong (2026-11-14). Tự chốt theo quyền người dùng cấp; lựa chọn ghi ở mục 12
- **Luồng:** U13; màn hình 17 (Tạo trắc nghiệm), 18 (Làm trắc nghiệm), 19 (Kết quả)

## 1. Mục tiêu
Người học chọn tài liệu hoặc một chương (khoảng trang), AI soạn câu hỏi trắc nghiệm 4 lựa chọn. Người học làm bài, **code chấm điểm** (không nhờ AI chấm), rồi xem lại câu sai kèm giải thích và nguồn để mở trang tài liệu.

## 2. Luồng
1. Tab **Trắc nghiệm** của Không gian: danh sách bài (tên tài liệu, khoảng trang, số câu, điểm lần gần nhất), nút **Tạo trắc nghiệm**.
2. Tạo: chọn tài liệu `READY`, từ trang, đến trang (không bắt buộc), số câu (5, 10, 15, 20); mỗi lần tạo dùng 1 lượt tạo trắc nghiệm trong ngày.
3. Làm bài: từng câu một, "Câu x/y", chọn A đến D, câu trước, câu tiếp, **Nộp bài** ở câu cuối (báo số câu bỏ trống; bỏ trống tính là sai).
4. Thoát giữa chừng: hỏi **Lưu và thoát** (bài làm dở lưu trên máy, mở lại thì làm tiếp) hoặc **Bỏ bài làm**.
5. Kết quả: số câu đúng; xem lại câu sai gồm lựa chọn của người học, đáp án đúng, giải thích, nguồn (bấm mở trang tài liệu, F8); **Làm lại** hoặc **Xong**.
6. Hết lượt hoặc AI tạm nghỉ: báo rõ; bài đã có vẫn làm được.

## 4. API
| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `/v1/quizzes?space_id=` | GET | Danh sách kèm `question_count`, `attempt_count`, `last_score` |
| `/v1/quizzes` | POST `{space_id, document_id, page_start?, page_end?, question_count}` | 201 bài kèm câu hỏi (không có đáp án) |
| `/v1/quizzes/{id}` | GET, DELETE | Câu hỏi không có đáp án; xóa bài xóa luôn các lần làm |
| `/v1/quizzes/{id}/attempts` | POST `{answers: [{question_id, choice}]}` | 201: điểm, từng câu kèm `correct_index`, `explanation`, `source` |
| `/v1/usage/me` | GET | Thêm bộ đếm `quizzes` |

Lỗi: `USER_QUOTA_EXCEEDED` (429), `AI_TEMPORARILY_UNAVAILABLE` (503), `DOCUMENT_NOT_READY` (409), `SOURCE_EMPTY` (422).

## 5. Dữ liệu (migration mới)
| Bảng | Cột chính |
|---|---|
| `quizzes` | `owner_id`, `space_id`, `title`, nguồn dạng bản ghi nhanh (`source_document_id` đặt rỗng khi tài liệu bị xóa, `source_document_name`), `page_start`, `page_end` |
| `quiz_questions` | `quiz_id`, `position`, `prompt`, `options` (4), `correct_index`, `explanation`, `source_page` |
| `quiz_attempts` | `quiz_id`, `owner_id`, `answers`, `score`, `total` |

## 6. Quy tắc
- **Hạn mức:** 5 lần tạo mỗi ngày (`QUIZ_DAILY_LIMIT`), tính riêng với hỏi đáp và tạo thẻ; AI lỗi hoặc kết quả hỏng thì hoàn lượt.
- **Nguồn:** đoạn của tài liệu theo thứ tự đọc trong khoảng trang, tối đa 15.000 ký tự (dùng chung bộ nạp nguồn với F9).
- **Prompt:** chỉ dẫn tiếng Anh, nguồn bọc `<source>` và là dữ liệu không đáng tin (R7); mỗi câu đúng 4 lựa chọn, một đáp án; không "tất cả đều đúng"; giải thích dựa trên nguồn và không nhắc số thứ tự nguồn; viết bằng ngôn ngữ của tài liệu.
- **Kiểm tra kết quả AI:** bỏ câu thiếu nội dung, không đủ 4 lựa chọn khác nhau, đáp án ngoài phạm vi, câu trùng; cắt độ dài.
- **Xáo lựa chọn bằng code** để đáp án đúng không luôn ở cùng một vị trí.
- **Chấm bằng code:** so lựa chọn với `correct_index`; câu bỏ trống, mã câu lạ, lựa chọn ngoài phạm vi đều tính sai. Đáp án đúng chỉ trả về sau khi nộp.

## 7. Quyền và bảo mật
Mọi truy vấn lọc theo chủ sở hữu; bài của người khác, tài liệu của người khác hay ngoài Không gian trả 404.

## 9. Tiêu chí nghiệm thu
1. Tạo bài từ khoảng trang: chỉ văn bản các trang đó vào prompt; câu hỏi không lộ đáp án; trừ 1 lượt trắc nghiệm, không đụng lượt khác.
2. Chấm bằng code: điểm, từng câu đúng sai, giải thích, nguồn; chấm không gọi AI; danh sách hiện điểm gần nhất.
3. Lựa chọn ngoài phạm vi, mã câu lạ: tính sai.
4. Bài của người khác: 404; xóa bài được.
5. AI lỗi hoặc kết quả hỏng: 503, hoàn lượt; hết lượt: 429, không gọi AI.
6. Tài liệu chưa `READY`: 409; khoảng trang rỗng: `SOURCE_EMPTY`; tài liệu bị xóa thì nguồn có `document_id = null`.
7. Unit test: xáo lựa chọn giữ đúng đáp án, bỏ câu hỏng.
8. Giao diện: danh sách, tạo, làm từng câu, lưu bài làm dở, kết quả và xem lại câu sai, song ngữ.
9. Thử thật với Gemini trên giáo trình mẫu: câu hỏi đúng nội dung, đáp án đúng phân bố ở nhiều vị trí.

## 12. Lựa chọn đã tự chốt
- 5 lần tạo trắc nghiệm mỗi ngày, mỗi bài tối đa 20 câu.
- Câu hỏi 4 lựa chọn, một đáp án; chưa có loại câu đúng sai hay điền từ.
- Bài làm dở lưu trên máy (AsyncStorage), không lưu lên server.
- Chương được chọn bằng khoảng trang (như F9).

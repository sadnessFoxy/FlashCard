# Đặc tả tính năng: F5. Tải tài liệu PDF và xử lý nền đến READY

- **Trạng thái:** Xong 2026-11-12. Người dùng cho phép tự chốt trong phiên (2026-11-10); các lựa chọn tự chốt ghi ở mục 12 và docs/DECISIONS.md
- **Thuộc bản:** 1
- **Giai đoạn liên quan:** F5; một phần giai đoạn 3 (Idempotency-Key, hiện trạng thái xử lý) và giai đoạn 5 (hạn mức AI, `PAUSED_QUOTA`)
- **Luồng:** U5, U16 (Không gian mặc định), U8 (khi AI hết hạn mức); màn hình 5 (tab Tài liệu) và 6 (Tải tài liệu)

## 1. Mục tiêu
Người dùng tải một file PDF vào một Không gian. Hệ thống xử lý nền: trích văn bản theo trang, chia đoạn, tạo embedding 768 chiều, lưu vào pgvector, rồi đánh dấu tài liệu sẵn sàng (`READY`) để F7 dùng cho hỏi đáp. Người dùng thấy trạng thái xử lý cập nhật trên màn hình.

## 2. Luồng người dùng
1. Trong tab **Tài liệu** của một Không gian, bấm **Tải tài liệu**.
2. **Lần đầu tải:** hiện thông báo dữ liệu (nội dung được gửi cho Google xử lý ở gói miễn phí và có thể được dùng để cải thiện sản phẩm của họ; không nên tải tài liệu nhạy cảm; chỉ tải tài liệu mình có quyền dùng). Người dùng bấm **Đồng ý** thì mới chọn được file; sự đồng ý được lưu kèm phiên bản văn bản.
3. Chọn file PDF. App kiểm tra sơ bộ đuôi và kích thước (tối đa 20 MB) trước khi gửi.
4. Gửi lên kèm `Idempotency-Key`. Backend kiểm tra: quyền với Không gian, định dạng thật (byte đầu `%PDF-`, không tin đuôi file), kích thước, số trang (tối đa 200), PDF có mật khẩu không, số tài liệu đã có (tối đa 10 trên cả tài khoản).
5. Hợp lệ: lưu file gốc vào kho S3, tạo tài liệu ở trạng thái `QUEUED`, đưa job vào hàng đợi, trả về ngay.
6. Danh sách tài liệu hiện nhãn trạng thái và tự làm mới vài giây một lần khi còn tài liệu đang xử lý.
7. Worker: `PROCESSING` → trích văn bản → chia đoạn → embedding → `READY`.
8. Lỗi:
   - Sai định dạng hoặc vượt giới hạn: báo ngay, nói rõ giới hạn.
   - Mất mạng giữa chừng rồi gửi lại cùng `Idempotency-Key`: không tạo tài liệu trùng.
   - PDF không có lớp văn bản (bản scan): `FAILED` với lý do "tài liệu scan chưa hỗ trợ". F14 sẽ xử lý loại này.
   - AI chạm giới hạn tốc độ: worker chờ rồi thử lại.
   - AI hết hạn mức ngày: `PAUSED_QUOTA`; tự chạy tiếp khi hạn mức phục hồi.
   - Lỗi khác sau 3 lần thử: `FAILED`. Nút thử lại làm ở F6.

**Không gian mặc định:** gọi API tải lên mà không có `space_id` chỉ hợp lệ khi người dùng chưa có Không gian nào. Khi đó hệ thống tự tạo một Không gian đặt tên theo file (hàm đã có từ F4b). Nếu người dùng đã có Không gian thì bắt buộc gửi `space_id`. Giao diện luôn tải từ trong một Không gian nên luôn có `space_id`.

## 3. Màn hình và hành vi giao diện

| Màn hình | Nội dung | Trạng thái |
|---|---|---|
| Tab Tài liệu (trong chi tiết Không gian) | Danh sách tài liệu: tên, số trang, ngày tải, nhãn trạng thái; nút Tải tài liệu; dòng "x/10 tài liệu" | Đang tải, rỗng (có hướng dẫn), lỗi; nhãn riêng cho Đang chờ, Đang xử lý, Sẵn sàng, Lỗi (kèm lý do), Tạm dừng vì AI hết hạn mức; đạt 10 tài liệu thì nút tải bị khóa kèm giải thích |
| Hộp đồng ý dữ liệu (lần đầu) | Văn bản thông báo, nút Đồng ý và Hủy | |
| Đang tải lên | Tên file, vòng xoay | Lỗi theo mã: quá lớn, sai định dạng, quá nhiều trang, có mật khẩu, đủ 10 tài liệu, mất mạng |

Mobile dùng `expo-document-picker` để chọn file; web dùng hộp chọn file của trình duyệt qua cùng thư viện đó.

## 4. API

| Endpoint | Phương thức | Yêu cầu | Phản hồi | Mã lỗi |
|---|---|---|---|---|
| `/v1/documents` | POST | multipart: `file`, `space_id` (tùy chọn, xem mục 2); header `Idempotency-Key` (UUID) | 202 `Document` (lặp lại cùng key: trả lại đúng tài liệu cũ, 200) | 403 `CONSENT_REQUIRED`, 404 Không gian, 409 `DOCUMENT_LIMIT_REACHED`, 409 `IDEMPOTENCY_KEY_REUSED`, 413 `FILE_TOO_LARGE`, 415 `FILE_TYPE_NOT_SUPPORTED`, 422 `TOO_MANY_PAGES`, 422 `PDF_ENCRYPTED`, 422 `SPACE_REQUIRED`, 422 `VALIDATION_ERROR` |
| `/v1/documents` | GET | query `space_id` (bắt buộc) | 200 `{items: Document[], total_documents, max_documents}` | 404 Không gian |
| `/v1/documents/{document_id}` | GET | | 200 `Document` | 404 |
| `/v1/me/consents` | GET | | 200 `{items: Consent[]}` | |
| `/v1/me/consents` | POST | `{kind: "ai_processing", version}` | 201 `Consent` (đã có thì 200) | 422 phiên bản không khớp bản hiện hành |

`Document` = `{id, space_id, filename, size_bytes, page_count, status, error_code, created_at, updated_at}`. `status` gồm `UPLOADED`, `QUEUED`, `PROCESSING`, `READY`, `FAILED`, `PAUSED_QUOTA`, `DELETING`. `error_code` gồm `NO_TEXT_LAYER`, `EXTRACTION_FAILED`, `PROCESSING_FAILED`.

Danh sách và chi tiết dùng cho việc theo dõi trạng thái. Xóa, thử lại và chuyển Không gian làm ở F6.

## 5. Dữ liệu (migration thứ ba)

| Bảng | Cột chính | Ràng buộc, index |
|---|---|---|
| `documents` | `owner_id`, `space_id`, `filename`, `storage_key`, `size_bytes`, `page_count`, `sha256`, `status`, `error_code`, `idempotency_key`, `embedding_model`, `embedding_dims` | CHECK cho `status`; unique (`owner_id`, `idempotency_key`); index (`owner_id`, `created_at`), (`space_id`) |
| `document_chunks` | `document_id`, `owner_id`, `chunk_index`, `page_start`, `page_end`, `content`, `token_estimate`, `embedding vector(768)` (rỗng cho tới khi embed xong) | unique (`document_id`, `chunk_index`); index HNSW cosine trên `embedding`; index (`owner_id`) |
| `document_jobs` | `document_id`, `kind`, `status`, `attempts`, `last_error_code`, `started_at`, `finished_at` | index (`document_id`) |
| `user_consents` | `user_id`, `kind`, `version`, `created_at` | unique (`user_id`, `kind`, `version`) |
| `ai_usage` | `user_id` (rỗng được), `provider`, `model`, `operation`, `input_tokens`, `output_tokens`, `latency_ms`, `success`, `error_code`, `created_at` | index (`user_id`, `created_at`) |

- `document_chunks.owner_id` được lưu lặp lại để truy xuất vector ở F7 lọc theo chủ sở hữu ngay trên bảng chunk (R4).
- Tên và số chiều mô hình embedding được lưu cùng tài liệu (docs/DATA_MODEL.md).

## 6. Quy tắc nghiệp vụ

- **Giới hạn** (cấu hình được): 20 MB mỗi file, 200 trang, 10 tài liệu mỗi người. Tài liệu `DELETING` không tính vào giới hạn.
- **Định dạng:** chỉ PDF ở F5 (Word là F13). Kiểm tra bằng byte đầu file, không tin đuôi và `Content-Type`.
- **Tên file:** chỉ giữ phần tên cuối (bỏ đường dẫn), chuẩn NFC, bỏ ký tự điều khiển, cắt còn 255 ký tự. Dùng để hiển thị, không dùng làm đường dẫn lưu trữ.
- **Khóa lưu trữ:** `documents/{owner_id}/{document_id}.pdf`, không chứa tên file người dùng.
- **Idempotency:** cùng người dùng gửi lại cùng `Idempotency-Key` thì nhận lại tài liệu cũ. Cùng key nhưng nội dung file khác (khác `sha256`) thì báo 409.
- **Máy trạng thái:** chỉ các chuyển trạng thái trong docs/DATA_MODEL.md, bằng câu lệnh cập nhật có điều kiện theo trạng thái hiện tại (R6). Worker kiểm tra lại trạng thái trước mỗi bước nặng; tài liệu đã chuyển sang `DELETING` thì dừng ngay.
- **Trích văn bản:** theo từng trang bằng `pypdf`. Nếu trung bình dưới 20 ký tự mỗi trang thì coi là tài liệu scan: `FAILED` với `NO_TEXT_LAYER`.
- **Chia đoạn:** theo đoạn văn trong từng trang, gom tới khoảng 1.200 ký tự (khoảng 300 đến 400 token tiếng Việt), chồng lấn khoảng 150 ký tự với đoạn trước. Không bao giờ vượt 6.000 ký tự, dưới giới hạn đầu vào 8.192 token của mô hình. Mỗi đoạn lưu trang bắt đầu và trang kết thúc. Tiêu đề chương hay mục được giữ ở đầu đoạn kế tiếp nhờ phần chồng lấn. Việc nhận diện mục lục để chia theo chương làm ở F12.
- **Embedding:** theo lô 32 đoạn, `taskType = RETRIEVAL_DOCUMENT`. Đoạn nào đã có vector thì không làm lại, nên tiếp tục được sau khi tạm dừng.
- **Thử lại:** chạm giới hạn tốc độ thì chờ theo thời gian nhà cung cấp báo (tối đa 60 giây), không tính vào số lần thử. Lỗi tạm thời khác thì thử tối đa 3 lần, rồi `FAILED`.
- **Hết hạn mức ngày hoặc lỗi billing:** `PAUSED_QUOTA`, không tính lần thử. Cứ 10 phút một tác vụ định kỳ đưa các tài liệu `PAUSED_QUOTA` về `QUEUED` để thử tiếp.

## 7. Quyền và bảo mật
- Mọi truy vấn lọc theo chủ sở hữu (R4). Tài liệu hay Không gian của người khác đều trả 404.
- File gốc chỉ đọc được qua backend, không có URL công khai.
- Không ghi tên file hay nội dung tài liệu vào log (R10); log chỉ có `document_id`, số trang, số đoạn.
- Không gửi email, tên hay ID người dùng tới Gemini; chỉ gửi nội dung các đoạn văn (docs/AI_PIPELINE.md).
- Nội dung tài liệu là dữ liệu không đáng tin (R7). F5 chỉ tạo embedding, không đưa nội dung vào prompt.
- Chặn tải lên khi tài khoản chưa xác minh email (DECISIONS) cần có F4. Đã viết sẵn cờ cấu hình `REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD`, đang tắt; F4 sẽ bật.

## 8. AI và hạn mức
- Gọi AI: chỉ embedding, ở worker, qua `llm_gateway` (R5).
- Gateway phân biệt lỗi: giới hạn tốc độ (thử lại sau `retry_after`), hết hạn mức ngày hoặc billing (không thử lại, mở circuit breaker), lỗi tạm thời (thử lại có giới hạn).
- Mỗi lần gọi ghi vào `ai_usage`: số token ước lượng, độ trễ, thành công hay thất bại; không ghi nội dung.
- Hạn mức hỏi đáp theo người dùng không áp dụng ở F5. Giới hạn số trang và số tài liệu đóng vai trò hạn mức tầng 3.

## 9. Tiêu chí nghiệm thu
1. Cho PDF 3 trang có chữ, Khi tải lên, Thì nhận 202 trạng thái `QUEUED`; sau khi worker chạy thì `READY`; có ít nhất 1 đoạn, mỗi đoạn có trang hợp lệ và vector 768 chiều.
2. Cho file đổi đuôi thành `.pdf` nhưng không phải PDF, Thì nhận 415; không có gì được lưu.
3. Cho file trên 20 MB, Thì 413. Cho PDF trên 200 trang, Thì 422 `TOO_MANY_PAGES`. Cho PDF có mật khẩu, Thì 422 `PDF_ENCRYPTED`.
4. Cho người dùng đã có 10 tài liệu, Khi tải thêm, Thì 409 `DOCUMENT_LIMIT_REACHED`.
5. Cho cùng `Idempotency-Key` gửi hai lần, Thì chỉ có một tài liệu và lần hai trả đúng tài liệu đó; khác nội dung thì 409.
6. Cho người dùng chưa đồng ý, Khi tải, Thì 403 `CONSENT_REQUIRED`; đồng ý xong thì tải được.
7. Cho người dùng chưa có Không gian, Khi tải không kèm `space_id`, Thì có Không gian mới tên theo file. Đã có Không gian mà không gửi `space_id` thì 422 `SPACE_REQUIRED`.
8. Cho Không gian hoặc tài liệu của người khác, Thì 404; danh sách không lộ tài liệu của người khác.
9. Cho PDF toàn ảnh (không có chữ), Thì `FAILED` với `NO_TEXT_LAYER`.
10. Cho nhà cung cấp AI báo hết hạn mức ngày giữa chừng, Thì `PAUSED_QUOTA`; các đoạn đã embed giữ nguyên; chạy lại thì chỉ embed các đoạn còn thiếu rồi `READY`.
11. Cho nhà cung cấp báo chạm giới hạn tốc độ một lần, Thì worker chờ rồi xong `READY`, không bị `FAILED`.
12. Cho tài liệu chuyển sang `DELETING` trong lúc xử lý, Thì worker dừng, không ghi đè thành `READY` (R6).
13. Log không chứa tên file hay nội dung tài liệu.
14. Giao diện: lần đầu tải hiện hộp đồng ý; danh sách hiện nhãn trạng thái và tự cập nhật tới khi `READY`; lỗi hiện theo mã, song ngữ.

## 10. Test cần có
- **Unit:** chia đoạn (trang, chồng lấn, giới hạn kích thước), phát hiện scan, làm sạch tên file, máy trạng thái (chuyển hợp lệ và không hợp lệ), phân loại lỗi Gemini (giới hạn tốc độ, hết hạn mức ngày, billing).
- **API và integration:** tiêu chí 1 đến 9 với PDF tạo sẵn trong test (dùng `FakeProvider`, không gọi Gemini thật); kho file thật (SeaweedFS) cho tiêu chí 1.
- **Worker:** tiêu chí 10 đến 12 bằng provider giả có thể báo lỗi theo kịch bản.
- **Security:** truy cập chéo (tiêu chí 8), log (tiêu chí 13).
- **Frontend:** hộp đồng ý, danh sách theo trạng thái, lỗi tải lên theo mã, tự làm mới.
- **Chạy thử thủ công:** một giáo trình PDF tiếng Việt thật, qua worker thật và Gemini thật.

## 11. Ngoài phạm vi
- Xóa, thử lại, chuyển Không gian, màn hình chi tiết tài liệu (F6).
- Word `.docx` (F13), tài liệu scan và OCR (F14), tóm tắt và nhận diện chương (F12).
- Hạn mức hệ thống theo token mỗi ngày (giai đoạn 5); ở F5 dựa vào giới hạn của nhà cung cấp và circuit breaker.
- Thông báo đẩy khi xử lý xong; giao diện chỉ tự làm mới định kỳ.

## 12. Lựa chọn đã tự chốt (người dùng cho phép, có thể đổi)
- Đồng ý dữ liệu lưu theo phiên bản văn bản (`ai-processing-2026-11`); đổi văn bản thì phải đồng ý lại.
- Kích thước đoạn khoảng 1.200 ký tự, chồng lấn 150 ký tự, lô embedding 32 đoạn. Đổi những giá trị này không phải tạo lại vector cho tài liệu cũ.
- Ngưỡng nhận diện tài liệu scan: trung bình dưới 20 ký tự mỗi trang.
- Kho file: thư viện `boto3`, chạy trong thread, dùng được cho cả SeaweedFS lẫn S3 thật. Tự tạo bucket ở môi trường development.
- Thư viện đọc PDF: `pypdf` (thuần Python, giấy phép BSD).
- Chọn file ở frontend: `expo-document-picker` (thư viện chính thức của Expo).
- Chưa chặn tài khoản chưa xác minh email tải tài liệu cho tới khi có F4 (xem mục 7).

## 13. Khác biệt và kết quả khi triển khai

- **Chia đoạn theo cấu trúc** thay vì chỉ theo kích thước: chạy thử thật cho thấy đoạn gộp hai chương làm trích dẫn sai trang. Giờ tiêu đề chương, mục và sang trang luôn bắt đầu đoạn mới, và không chồng lấn qua các ranh giới đó.
- **Thêm chuyển `PROCESSING → QUEUED`** cho lỗi tạm thời chờ lần thử sau (docs/DATA_MODEL.md đã cập nhật).
- **Circuit breaker mở** (lỗi liên tiếp từ nhà cung cấp) cũng dẫn tới `PAUSED_QUOTA` thay vì tiêu hết số lần thử.
- **Thử thật:** giáo trình Giải tích tiếng Việt 3 trang (văn bản tự soạn) qua worker thật và Gemini thật: READY sau khoảng 2 giây; câu hỏi về đạo hàm, định lý cơ bản và tính liên tục trỏ đúng trang 2, 3 và 1.
- **Chạy worker:** `make worker` (hoặc `backend\.venv\Scripts\python -m arq app.workers.queue.WorkerSettings`).

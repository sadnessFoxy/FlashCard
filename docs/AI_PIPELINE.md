# Pipeline AI, RAG và Gemini

> **Khi nào đọc:** khi làm module `ai`, nạp tài liệu, truy xuất, hỏi đáp, tạo flashcard, hoặc đụng đến nhà cung cấp AI và embedding.

## Hai luồng chính

| Luồng | Các bước | Chạy ở đâu |
|---|---|---|
| Nạp tài liệu | Tải lên, trích văn bản, chia đoạn nhỏ, tạo embedding, lưu vào pgvector kèm số trang | Worker nền; app hiển thị trạng thái đang xử lý, sẵn sàng, lỗi |
| Hỏi đáp | Câu hỏi, truy xuất đoạn gần nghĩa (chỉ trong tài liệu của người dùng), LLM soạn câu trả lời, trả về kèm trích dẫn | API, streaming về app |

## Nguyên tắc riêng của dự án (quy tắc bắt buộc)

- Mọi câu trả lời kèm nguồn; không đủ căn cứ thì nói "không tìm thấy trong tài liệu", không đoán
- Truy xuất luôn lọc theo chủ sở hữu tài liệu, tuyệt đối không để lộ tài liệu của người khác
- Chia đoạn theo cấu trúc (chương, mục) có chồng lấn nhỏ, lưu số trang
- Coi nội dung trong tài liệu là dữ liệu không đáng tin, không để nó điều khiển chỉ dẫn hệ thống (prompt injection)
- Giới hạn kích thước file, số trang, số tài liệu, số lượt hỏi mỗi ngày
- Flashcard do AI tạo phải cho người dùng xem và sửa trước khi lưu
- Thử embedding và OCR trên tài liệu tiếng Việt thật trước khi chốt mô hình
- Bộ câu hỏi mẫu (`evals/`) chạy lại mỗi khi đổi prompt hoặc đổi mô hình
- Soạn điều khoản sử dụng: người dùng chỉ tải tài liệu mình có quyền dùng; bản đầu không chia sẻ công khai
- Theo dõi token và chi phí AI theo từng người dùng

## Dùng Gemini API bản miễn phí (Google AI Studio)

**Quyết định:** dùng khóa Gemini API từ Google AI Studio ở gói miễn phí làm nhà cung cấp AI mặc định, cho cả sinh câu trả lời lẫn embedding. Chuyển sang gói trả phí là **tùy chọn, không phải điều kiện bắt buộc**; thiết kế phải cho phép chuyển bất kỳ lúc nào mà không sửa code.

**Hệ quả của việc dùng gói miễn phí** (theo điều khoản của Google tại thời điểm tra cứu cuối tháng 10/2026, nên đọc lại định kỳ):
- Với dịch vụ không trả phí (Google AI Studio và hạn mức miễn phí của Gemini API), nội dung gửi lên và câu trả lời sinh ra có thể được Google dùng để cải thiện sản phẩm, và người đánh giá có thể đọc.
- Gói trả phí thì không dùng dữ liệu để cải thiện sản phẩm. Ở khu vực EEA, Thụy Sĩ và Anh, điều khoản của gói trả phí áp dụng cho mọi dịch vụ kể cả bản miễn phí.
- Giới hạn tốc độ của gói miễn phí thấp và thay đổi theo mô hình, theo thời gian; xem trang giới hạn trong AI Studio, không dựa vào con số cũ.

**Cách giảm thiểu rủi ro dữ liệu khi vẫn dùng gói miễn phí**
- Thông báo rõ trước khi người dùng tải tài liệu và xin đồng ý: nội dung được gửi cho Google xử lý và có thể được dùng để cải thiện sản phẩm của họ.
- Khuyến cáo không tải tài liệu nhạy cảm (thông tin cá nhân, y tế, tài chính, tài liệu mật).
- Không đưa thông tin định danh không cần thiết (email, tên, ID người dùng) vào prompt; chỉ gửi nội dung tối thiểu cần để trả lời.
- Ghi log không chứa khóa API hoặc nội dung nhạy cảm.
- Ghi điều khoản sử dụng: người dùng chỉ tải tài liệu mình có quyền dùng.

**Tận dụng giới hạn tốc độ để kiểm thử:** cố ý chạm giới hạn rồi quan sát retry, circuit breaker, `PAUSED_QUOTA` và thông báo trên app (docs/QUOTA_AND_RESILIENCE.md). Đặt hạn mức người dùng nội bộ thấp hơn giới hạn của nhà cung cấp để hệ thống tự chặn trước khi nhà cung cấp chặn.

**Thiết kế để chuyển gói bất kỳ lúc nào**
- Mọi khác biệt giữa hai gói chỉ nằm ở khóa API và cấu hình (tên mô hình, giới hạn tốc độ, ngân sách hệ thống); không viết cứng trong code.
- Mọi lời gọi AI đi qua `providers/gemini.py` và `llm_gateway`; hạn mức ba tầng ở docs/QUOTA_AND_RESILIENCE.md đọc giới hạn từ cấu hình.
- Nếu giữ nguyên mô hình embedding và số chiều thì vector đã lưu vẫn dùng được sau khi đổi gói, không phải tạo lại.
- Khi cần chuyển: tạo khóa gói trả phí và liên kết thanh toán, đặt cảnh báo ngân sách tại Google Cloud (kiểm tra xem có đặt được trần cứng không), thay khóa trong secrets manager, nâng giới hạn trong cấu hình, cập nhật thông báo quyền riêng tư, rồi chạy lại các kịch bản hạn mức ở docs/TESTING.md.
- Tín hiệu nên cân nhắc chuyển: hay chạm giới hạn tốc độ, lượng người dùng tăng, người dùng hoặc đối tác yêu cầu cam kết về dữ liệu, hoặc cần phục vụ thị trường có quy định chặt về dữ liệu.

**Quản lý khóa API**
- Khóa chỉ nằm ở backend (biến môi trường hoặc secrets manager), không bao giờ nhúng vào app.
- Mỗi môi trường (dev, staging, production) dùng khóa riêng.
- Không commit khóa lên Git, không dán vào chat hay tài liệu; nghi ngờ bị lộ thì thu hồi và tạo khóa mới ngay.

> **Cập nhật 2026-11-08:** đã chốt dùng `gemini-embedding-2` (768 chiều, nhận tới 8192 token) và mô hình chat `gemini-3.5-flash-lite`; xem docs/DECISIONS.md. Phần dưới về `gemini-embedding-001` giữ làm phương án dự phòng.

**Embedding (`gemini-embedding-001`)**
- Hỗ trợ hơn 100 ngôn ngữ và nhận tối đa khoảng 2048 token đầu vào, nên mỗi đoạn (chunk) phải nằm trong giới hạn này. Vẫn thử trên tài liệu tiếng Việt thật như đã nêu ở docs/AI_PIPELINE.md.
- Số chiều: 3072 (mặc định), có thể giảm xuống 1536 hoặc 768. **Phải chốt trước khi nạp dữ liệu**, vì đổi chiều nghĩa là tạo lại toàn bộ vector.
- Index của pgvector cho kiểu `vector` có giới hạn số chiều (khoảng 2000 theo hiểu biết hiện tại), nên 3072 khó đánh index trực tiếp. Ưu tiên 768 hoặc 1536, hoặc dùng kiểu `halfvec`; kiểm tra theo phiên bản pgvector bạn dùng.
- Kiểm tra tài liệu Google về việc có cần chuẩn hóa vector khi giảm chiều không, và khai báo đúng loại tác vụ (tài liệu hay câu hỏi) khi tạo embedding.
- Sau hạn mức miễn phí, giá embedding tính theo triệu token đầu vào (khoảng 0,15 USD theo công bố của Google tại thời điểm tra cứu); đưa vào dự toán nếu sau này chuyển gói.

**Không đặt cứng tên mô hình:** mô hình của nhà cung cấp đổi và ngừng hỗ trợ khá nhanh (ví dụ một mô hình embedding cũ của Google có lịch ngừng vào tháng 1/2026). Tên mô hình, số chiều và nhà cung cấp nằm trong cấu hình và được lưu cùng vector trong database.

**Tài liệu dạng ảnh:** Gemini có thể đọc trực tiếp PDF và ảnh, là phương án thay cho bước OCR riêng với tài liệu scan. Cái giá là tốn token hơn, nên chỉ áp dụng cho tài liệu thật sự là ảnh; PDF có sẵn văn bản vẫn trích văn bản như thiết kế ở docs/AI_PIPELINE.md.

## Quyết định bổ sung (tháng 10/2026)

**Embedding:** chiều vector 768 (đã chốt). Vẫn thử lại trên tài liệu tiếng Việt và tiếng Anh thật trước khi nạp nhiều; đổi chiều sau này nghĩa là tạo lại toàn bộ vector.

**Hỏi đáp trên nhiều tài liệu**
- Truy xuất chỉ trong các tài liệu `READY` của chủ sở hữu và thuộc tập tài liệu người dùng đã chọn; lọc trước khi nội dung vào ngữ cảnh AI.
- Giới hạn số đoạn lấy từ mỗi tài liệu để một tài liệu không lấn át các tài liệu còn lại (đề xuất).
- Mỗi trích dẫn gồm tên tài liệu và số trang, kèm bản ghi nhanh để hiển thị khi tài liệu đã bị xóa.

**Ngôn ngữ:** tài liệu và câu hỏi có thể là tiếng Việt hoặc tiếng Anh; dùng mô hình embedding đa ngôn ngữ; trả lời theo ngôn ngữ của câu hỏi (đề xuất).

**Mục tiêu độ trễ:** chữ đầu tiên của câu trả lời hiện trong khoảng 3 giây; API thường dưới 500 ms ở p95 (không tính phần sinh câu trả lời dài).

**Tài liệu scan**
- Hướng chọn: Gemini đọc trực tiếp làm mặc định (miễn phí trong hạn mức, tính vào hạn mức AI); Tesseract với gói ngôn ngữ tiếng Việt và tiếng Anh làm dự phòng khi hết hạn mức hoặc AI ngừng.
- Lý do: theo các so sánh của bên thứ ba (không riêng cho tiếng Việt), các mô hình như Gemini xử lý tốt hơn với bố cục phức tạp, ảnh chất lượng thấp và tài liệu đa ngôn ngữ; Tesseract miễn phí, chạy cục bộ nhưng không hiểu bố cục và yếu với bản scan kém. Tesseract chạy trên máy chủ thì tốn CPU và RAM của dịch vụ Railway.
- Việc phải làm trước khi coi là chốt hẳn: thử trên 3 đến 5 tài liệu scan tiếng Việt thật và đo chất lượng; đặt giới hạn số trang scan vì mỗi trang tốn token; ghi nhận phương pháp OCR đã dùng cho từng tài liệu.

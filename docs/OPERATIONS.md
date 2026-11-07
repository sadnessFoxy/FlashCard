# Vận hành và CI/CD

> **Khi nào đọc:** khi làm pipeline, giám sát, cảnh báo, runbook, hoặc triển khai.

## Luồng CI/CD đích

| Sự kiện | Hệ thống tự làm |
|---|---|
| Mở Pull Request | Lint, kiểm tra kiểu, chạy test |
| Merge vào `develop` | Chạy kiểm tra và đóng gói bản thử nghiệm (không đẩy lên store) |
| Gắn tag phiên bản (ví dụ v0.1.0) | Đóng gói bản thử nghiệm (không đẩy lên store) |
| Backend merge | Build Docker image, deploy staging, duyệt, deploy production |


## Vận hành

Chỉ số nên theo dõi:
- **API:** tỷ lệ lỗi, thời gian phản hồi p95, số request
- **Database:** số kết nối, thời gian truy vấn, dung lượng
- **Worker:** độ dài hàng đợi, thời gian xử lý tài liệu, tỷ lệ job thất bại
- **AI:** token vào/ra, chi phí ước tính, thời gian phản hồi, chất lượng trích dẫn
- **Hạn mức AI:** % ngân sách đã dùng, trạng thái circuit breaker, số job `PAUSED_QUOTA`, số lần người dùng chạm hạn mức
- **Mobile:** crash, lỗi mạng, thời gian tải màn hình

Công cụ: Sentry cho lỗi ứng dụng, Prometheus + Grafana cho metrics, log tập trung khi quy mô cần. Không cần dựng đủ ngay từ đầu.

Runbook (đặt ở `docs/runbooks/`): `database-recovery.md`, `failed-document-jobs.md`, `production-rollback.md`, `ai-quota-exhausted.md`. Script hỗ trợ ở `backend/scripts/`: `healthcheck.py`, `cleanup_jobs.py`.

## Triển khai trên Railway

Dịch vụ cần dựng cho mỗi môi trường: API, worker ARQ, PostgreSQL có pgvector, Redis, kho file tương thích S3. Railway có template PostgreSQL kèm pgvector (do cộng đồng và Railway cung cấp) và Bucket lưu trữ S3; cần xác nhận phiên bản và điều kiện hiện hành trước khi dựng.

**Chi phí (theo tài liệu Railway tại thời điểm tra cứu cuối tháng 10/2026, cần kiểm tra lại):**
- Không có gói miễn phí vĩnh viễn: tài khoản mới có khoảng 5 USD credit dùng thử một lần trong 30 ngày, sau đó là gói Free với khoảng 1 USD credit mỗi tháng và tài nguyên hạn chế.
- Gói Hobby: 5 USD mỗi tháng, đã gồm 5 USD tài nguyên sử dụng.
- Đơn giá tài nguyên: RAM khoảng 10 USD mỗi GB mỗi tháng, CPU khoảng 20 USD mỗi vCPU mỗi tháng, lưu trữ volume khoảng 0,15 USD mỗi GB mỗi tháng, lưu lượng ra khoảng 0,05 USD mỗi GB.
- API, worker, PostgreSQL và Redis chạy cùng lúc có thể vượt mức 5 USD; cần chốt ngân sách hosting và đặt cảnh báo chi phí.
- Volume của tài khoản dùng thử bị xóa 30 ngày sau khi hết credit: không dùng gói dùng thử cho dữ liệu cần giữ.

**Sao lưu:**
- Sao lưu PostgreSQL định kỳ ra nơi khác và thử khôi phục; sao lưu database không bao gồm file gốc đã tải lên, nên cần sao lưu kho file riêng.
- Bản sao lưu giữ tối đa 30 ngày sau khi người dùng xóa tài khoản (docs/BUSINESS_FLOWS.md, U9).

**Chỉ số tải mục tiêu dùng khi định cỡ tài nguyên:** 100 người dùng, 10 đồng thời, API p95 dưới 500 ms, chữ đầu tiên của câu trả lời trong khoảng 3 giây.

> **Phạm vi hiện tại:** dự án chỉ chạy thử trên máy cá nhân (web và mobile qua Expo). Phần Railway ở trên chỉ áp dụng khi sau này muốn đưa lên mạng.

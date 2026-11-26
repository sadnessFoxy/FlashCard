# Đưa app lên mạng miễn phí bằng máy ảo Oracle

Kết quả: app chạy 24/7 tại một địa chỉ dạng `https://152-67-1-23.sslip.io`, có HTTPS, máy bạn tắt cũng không ảnh hưởng. Chi phí 0 đồng nếu chỉ dùng tài nguyên "Always Free".

Code và cấu hình đã có sẵn trong repo (`infra/deploy/`) và đã được thử chạy đủ trên Docker. Phần dưới đây là việc chỉ bạn làm được, vì cần tài khoản của bạn. Tổng thời gian khoảng 45 phút.

**Cần chuẩn bị:** thẻ ngân hàng (Visa hoặc Mastercard) để Oracle xác minh (không trừ tiền), khóa Gemini (đang có trong `backend/.env`), một email của bạn.

---

## Bước 1. Tạo tài khoản Oracle Cloud (10 phút)
1. Vào https://www.oracle.com/cloud/free/ → **Start for free**.
2. Điền thông tin và xác minh thẻ. Oracle có thể tạm giữ khoảng 1 USD rồi hoàn lại.
3. **Home Region:** chọn **Singapore** (gần Việt Nam nhất, nhanh nhất, nhưng hay hết máy miễn phí). Muốn ít bị hết máy hơn thì chọn **Japan Central (Osaka)** hoặc **South Korea North (Chuncheon)**, chậm hơn một chút. Vùng này không đổi được về sau và máy ảo miễn phí chỉ tạo được trong vùng này.
4. Giữ tài khoản ở gói **Free Tier**, chưa nâng cấp (xem "Câu hỏi thường gặp" ở cuối để quyết định có nâng lên Pay As You Go không).

> Đôi khi Oracle từ chối đăng ký mà không nói lý do. Nếu bị, thử lại bằng trình duyệt khác, tắt VPN, hoặc dùng thẻ khác.

## Bước 2. Tạo máy ảo (10 phút)
Trong trang quản lý Oracle: menu ☰ → **Compute** → **Instances** → **Create instance**.

| Mục | Chọn |
|---|---|
| Name | `flashcard` |
| Image | **Ubuntu 24.04** (bấm *Change image* → Ubuntu → Canonical Ubuntu 24.04) |
| Shape | *Change shape* → **Ampere** → **VM.Standard.A1.Flex**, **2 OCPU, 12 GB** |
| Networking | *Create new virtual cloud network*, *public subnet*, **Assign a public IPv4 address: Yes** |
| SSH keys | **Generate a key pair for me** → bấm **Save private key** (lưu file, bước 5 cần) |
| Boot volume | Để mặc định (50 GB) |

> **Không chọn quá 2 OCPU / 12 GB.** Từ tháng 8/2026, máy vượt mức miễn phí sẽ bị Oracle xóa.
>
> Nếu báo **Out of capacity**: vùng đang hết máy miễn phí. Đợi vài giờ rồi thử lại (sáng sớm hoặc đêm khuya hay còn máy hơn). Vùng có nhiều *Availability domain* thì thử đổi AD; Singapore và Tokyo chỉ có một.

Bấm **Create**. Khi trạng thái thành **Running**, chép **Public IP address** (ví dụ `152.67.1.23`).

## Bước 3. Mở cổng web trong Oracle (3 phút)
Mặc định Oracle chỉ cho kết nối SSH. Mở thêm cổng web:
1. Trong trang máy ảo, bấm vào tên **Subnet** → **Security Lists** → **Default Security List**.
2. **Add Ingress Rules**, thêm 3 dòng (Source CIDR đều là `0.0.0.0/0`):
   - IP Protocol **TCP**, Destination Port **80**
   - IP Protocol **TCP**, Destination Port **443**
   - IP Protocol **UDP**, Destination Port **443**

## Bước 4. Lấy khóa gửi email Resend (3 phút)
1. Vào https://resend.com → đăng ký **bằng chính email bạn sẽ dùng để đăng nhập app**.
2. **API Keys** → **Create API Key**, quyền *Sending access* → chép khóa (dạng `re_...`).

> Chưa có tên miền, Resend chỉ gửi được thư tới email của bạn. Vì vậy app tạm **không bắt xác minh email trước khi tải tài liệu**; người khác vẫn dùng được, chỉ chưa nhận được thư (mã xác minh, quên mật khẩu). Xem mục "Khi có tên miền".

## Bước 5. Cài app lên máy ảo (5 phút làm, 15 phút chờ)
Trên máy bạn, mở **PowerShell**:
```powershell
# Chuyển file khóa đã tải ở bước 2 vào thư mục .ssh và khóa quyền (sửa tên file nếu khác)
mkdir $HOME\.ssh -Force
Move-Item $HOME\Downloads\ssh-key-*.key $HOME\.ssh\flashcard-oracle.key
icacls $HOME\.ssh\flashcard-oracle.key /inheritance:r /grant:r "$($env:USERNAME):R"

# Kết nối vào máy ảo (thay IP của bạn); lần đầu gõ yes
ssh -i $HOME\.ssh\flashcard-oracle.key ubuntu@152.67.1.23
```
Bây giờ bạn đang gõ lệnh trên máy ảo. Dán lần lượt:
```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/sadnessFoxy/FlashCard.git flashcard
cd flashcard
sudo bash infra/deploy/setup.sh
```
Script hỏi 4 câu:

| Câu hỏi | Trả lời |
|---|---|
| Web address | Nhấn **Enter** (dùng địa chỉ sslip.io tự tạo từ IP) |
| Your email | Email của bạn (trùng email Resend) |
| Gemini API key | Dán khóa Gemini (chữ không hiện ra là bình thường) |
| Resend API key | Dán khóa `re_...` |

Script tự cài Docker, mở tường lửa, tạo mật khẩu ngẫu nhiên cho database và kho file, dựng app và đặt lịch sao lưu hằng ngày. Lần đầu mất 10 đến 20 phút. Cuối cùng nó in ra địa chỉ web.

## Bước 6. Dùng thử và nhận quyền quản trị
1. Mở địa chỉ vừa in (ví dụ `https://152-67-1-23.sslip.io`). Lần đầu có thể chờ 1 phút để lấy chứng chỉ HTTPS.
2. Đăng ký tài khoản của bạn trong app.
3. Trong cửa sổ SSH:
   ```bash
   sudo bash infra/deploy/admin.sh email-cua-ban@gmail.com
   ```
   Rồi mở `https://.../admin`.

**Trên điện thoại:** mở chính địa chỉ đó bằng trình duyệt (Chrome, Safari), không cần cài gì.

---

## Việc thường làm (gõ trong cửa sổ SSH, thư mục `~/flashcard`)
| Việc | Lệnh |
|---|---|
| Cập nhật lên code mới nhất trên GitHub | `sudo bash infra/deploy/update.sh` (tự sao lưu trước) |
| Xem các phần có đang chạy | `cd infra/deploy && sudo docker compose ps` |
| Xem log khi có lỗi | `cd infra/deploy && sudo docker compose logs --tail 100 api` (hoặc `worker`, `web`) |
| Sửa cấu hình, khóa | `nano infra/deploy/.env`, rồi `cd infra/deploy && sudo docker compose up -d` |
| Sao lưu ngay | `sudo bash infra/deploy/backup.sh` |

**Sao lưu:** mỗi ngày 3 giờ sáng (giờ máy chủ), giữ 7 ngày ở `/opt/flashcard-backups` (database `db-*.dump`, file tài liệu `files-*.tar.gz`). Thỉnh thoảng nên tải một bản về máy bạn (PowerShell):
```powershell
scp -i $HOME\.ssh\flashcard-oracle.key "ubuntu@152.67.1.23:/opt/flashcard-backups/*" .
```
Khôi phục database từ một bản sao lưu (ví dụ khi chuyển máy):
```bash
cd ~/flashcard/infra/deploy
sudo docker compose exec -T postgres pg_restore -U flashcard -d flashcard --clean --if-exists < /opt/flashcard-backups/db-YYYYMMDD-HHMM.dump
```

## Khi có tên miền (tùy chọn, khoảng 1 đến 3 USD/năm)
1. Trỏ tên miền (ví dụ `app.ten-mien.xyz`) về IP máy ảo (bản ghi **A**).
2. Trong `infra/deploy/.env`: đổi `SITE_ADDRESS=app.ten-mien.xyz`.
3. Trong Resend: **Domains** → thêm tên miền, làm theo hướng dẫn DNS; rồi đổi `SMTP_FROM_EMAIL=noreply@ten-mien.xyz` và `REQUIRE_VERIFIED_EMAIL_FOR_UPLOAD=true`.
4. `sudo bash infra/deploy/update.sh`.

## Bật đăng nhập Google trên bản mạng
Làm theo docs/SETUP_GOOGLE.md, thêm địa chỉ `https://...sslip.io` vào *Authorized JavaScript origins* và *redirect URIs*. Sau đó điền `GOOGLE_CLIENT_IDS` và `GOOGLE_WEB_CLIENT_ID` trong `infra/deploy/.env` rồi chạy `update.sh`. Phải dựng lại vì client ID được gắn vào bản web lúc dựng.

---

## Câu hỏi thường gặp
**Máy ảo bị Oracle tắt?** Nếu máy ảo miễn phí gần như không làm gì suốt 7 ngày (CPU dưới 20%), Oracle có thể tắt nó và gửi email báo trước. Dữ liệu không mất: vào trang Oracle bấm **Start** là chạy lại (app tự khởi động). Muốn tránh hẳn, có thể nâng tài khoản lên **Pay As You Go**. Vẫn 0 đồng nếu chỉ dùng tài nguyên Always Free, nhưng sẽ tính tiền nếu lỡ tạo thứ vượt mức. Nếu nâng, nên đặt **Budget** cảnh báo ở mức 1 USD.

**Chứng chỉ HTTPS không lấy được (trình duyệt báo không an toàn)?** Kiểm tra lại bước 3 (cổng 80, 443). Xem `sudo docker compose logs web`. Nếu dịch vụ cấp chứng chỉ từ chối địa chỉ sslip.io, app tự thử nhà cấp thứ hai; vẫn không được thì dùng tên miền (mục trên).

**Có tốn tiền Gemini không?** Không, vẫn dùng khóa miễn phí. Lưu ý: ở gói miễn phí, Google có thể dùng nội dung gửi lên để cải thiện sản phẩm. App đã xin đồng ý trước khi tải tài liệu; nên nhắc người dùng không tải tài liệu nhạy cảm. Có thể giới hạn lượt dùng AI ở trang quản trị → Cấu hình.

**Bảo mật:** database, Redis, kho file và API không mở ra Internet, chỉ có cổng web 80/443. Mật khẩu nội bộ được tạo ngẫu nhiên trong `infra/deploy/.env` trên máy chủ (không nằm trên GitHub). Quản trị viên chưa có xác thực hai bước: dùng mật khẩu dài, riêng cho tài khoản quản trị.

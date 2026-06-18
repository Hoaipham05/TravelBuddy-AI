# Deploy demo bằng Cloudflare Tunnel

Hướng dẫn tự dựng **link công khai (HTTPS)** cho TravelBuddy AI để người khác truy cập, **miễn phí, không cần thẻ, không cần thuê server**.

> ⚠️ Đây là cách **demo tạm**: link sống chừng nào **máy bạn còn bật + Docker còn chạy + tiến trình `cloudflared` còn mở**. Tắt 1 trong 3 → link chết. Dùng để trình bày/nộp báo cáo, không phải chạy production 24/7.

---

# PHẦN A — Hướng dẫn từng bước chi tiết (cho người mới)

> Làm lần lượt từ trên xuống. Mọi lệnh đều gõ trong **PowerShell**. "Gõ lệnh" = dán vào khung PowerShell rồi nhấn **Enter**.

## 🖥️ Bước 0 — Mở chỗ để gõ lệnh (PowerShell)

Chọn **1 trong 2 cách**:

**Cách A — Terminal trong VS Code (khuyên dùng):**
1. Trong VS Code, nhấn phím **`Ctrl + ` `** (phím dấu huyền `~`, nằm ngay dưới phím `Esc`).
2. Khung terminal hiện ra ở dưới. Nhìn góc phải khung đó — nếu không phải **PowerShell**, bấm mũi tên `⌄` cạnh dấu `+` → chọn **PowerShell**.
3. Vào đúng thư mục dự án:
   ```powershell
   cd d:\ThucTapNN\TravelBuddy_AI
   ```

**Cách B — PowerShell riêng:**
1. Bấm phím **Windows**, gõ `powershell`, nhấn Enter.
2. Gõ: `cd d:\ThucTapNN\TravelBuddy_AI`

---

## Bước 1 — Bật Docker Desktop

1. Bấm phím **Windows**, gõ `Docker Desktop`, nhấn Enter để mở.
2. Chờ icon cá voi 🐳 ở khay hệ thống (góc dưới phải màn hình) **đứng yên** (không còn chạy động) → Docker đã sẵn sàng.
3. Kiểm tra bằng lệnh:
   ```powershell
   docker version
   ```
   → Thấy cả **Client** và **Server** = OK. Nếu báo `cannot connect` = Docker chưa bật xong, chờ thêm rồi gõ lại.

---

## Bước 2 — Khởi động website (các container)

```powershell
docker compose up -d --build
```
- Lần đầu chạy lâu (vài phút) vì phải build. Chờ tới khi con trỏ quay lại dòng nhập lệnh.

Kiểm tra trạng thái:
```powershell
docker compose ps
```
→ Tất cả dòng phải có chữ **`healthy`** (riêng 2 dòng `worker` ghi `Up` là đúng). Trạng thái đúng trông như:

```
api        Up (healthy)
frontend   Up (healthy)
postgres   Up (healthy)
redis      Up (healthy)
searxng    Up (healthy)
worker     Up            (×2, không có healthcheck — bình thường)
```

> Nếu thấy `unhealthy` → xem [PHẦN C](#phẦn-c--lỗi--nâng-cao).
> Lần đầu chạy cần khởi tạo DB + seed: xem các lệnh `psql` trong `README.md` mục "Database Và Seed".

---

## Bước 3 — Cài cloudflared (CHỈ làm 1 lần duy nhất đời máy)

> Nếu đã cài rồi (có file `C:\Users\<tên-bạn>\cloudflared\cloudflared.exe`) thì **bỏ qua**, nhảy tới Bước 4.

`cloudflared` là **1 file .exe duy nhất**, **không cần quyền admin**. Copy cả 4 dòng dưới, dán **1 lần** vào PowerShell, nhấn Enter:
```powershell
$dir = "$env:USERPROFILE\cloudflared"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "$dir\cloudflared.exe"
& "$dir\cloudflared.exe" --version
```
→ Dòng cuối in `cloudflared version ...` = cài xong.

---

## Bước 4 — Mở tunnel để lấy link 🔗

```powershell
& "$env:USERPROFILE\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:3000 --no-autoupdate
```

> ⚠️ Phải là `127.0.0.1`, **ĐỪNG** sửa thành `localhost` (sẽ lỗi 403 — xem PHẦN C).

Chờ ~5 giây, màn hình hiện khung chứa link:
```
+----------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at:        |
|  https://abcd-xyz-1234.trycloudflare.com                 |  ← ĐÂY là link của bạn
+----------------------------------------------------------+
```

👉 **Copy dòng `https://....trycloudflare.com`** → gửi cho người khác.

> 🔴 **Cực kỳ quan trọng:** ĐỪNG đóng cửa sổ PowerShell này, ĐỪNG nhấn Ctrl+C. Cứ để nó chạy (log chạy liên tục là bình thường). Đóng = link chết ngay. Muốn dùng máy tiếp thì mở **một cửa sổ PowerShell KHÁC** (làm lại Bước 0).

---

## Bước 5 — Thử link

- **Tự bạn:** mở trình duyệt, dán link → thấy website hiện ra.
- **Chứng minh người khác vào được:** mở link trên **điện thoại, TẮT WiFi, dùng 4G/5G**. Vào được qua mạng di động = chắc chắn ai cũng vào được.

(Muốn test nhanh bằng lệnh thì xem [PHẦN C](#kiểm-tra-link-bằng-lệnh).)

---

## Bước 6 — Khi demo xong, tắt tunnel

Quay lại cửa sổ PowerShell đang chạy cloudflared, nhấn **`Ctrl + C`** (hoặc đóng cửa sổ). Link sẽ chết.

---

## ⏱️ Tóm tắt siêu gọn cho lần sau (khi đã cài cloudflared rồi)

Mở PowerShell trong VS Code (`Ctrl + ` `), gõ lần lượt:
```powershell
cd d:\ThucTapNN\TravelBuddy_AI
docker compose up -d
& "$env:USERPROFILE\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:3000 --no-autoupdate
```
→ Copy link, gửi đi, để cửa sổ chạy. Xong demo thì `Ctrl + C`.

---

# PHẦN B — Hiểu cơ chế (đọc thêm nếu muốn)

```
Người dùng bất kỳ
   → DNS công khai
   → Cloudflare edge (máy chủ toàn cầu của Cloudflare)
   → tunnel (qua tiến trình cloudflared trên máy bạn)
   → nginx container (cổng 3000)
   → nginx tự proxy /api → api:8000 trong mạng Docker nội bộ
```

Điểm mấu chốt: **chỉ cần expose 1 cổng** — cổng `3000` của container `frontend` (nginx). Postgres, redis, api, worker, searxng đều chạy ngầm trong mạng Docker, không lộ ra ngoài. Vì nginx đã proxy `/api/` nội bộ (xem `frontend/nginx.conf`), người dùng chỉ gọi 1 domain duy nhất.

**Vì sao phải `127.0.0.1` chứ không `localhost`?** Nếu bạn đang chạy `npm run dev` (Vite), Vite chiếm `localhost:3000` qua IPv6 (`::1`) và **chặn host lạ** (báo 403 "host is not allowed"). Còn nginx container — bản production cần expose — chạy trên IPv4 `0.0.0.0:3000`. Dùng `127.0.0.1` để ép request vào đúng **nginx**, không trúng Vite.

---

# PHẦN C — Lỗi & nâng cao

## Lỗi thường gặp

### a) Link trả `403 — This host ... is not allowed ... vite.config.js`
- **Nguyên nhân:** tunnel trỏ trúng **Vite dev server** (`npm run dev`) thay vì nginx.
- **Cách sửa:** trỏ vào `http://127.0.0.1:3000` (IPv4), **không** dùng `localhost` (xem Bước 4 ở PHẦN A).

### b) `frontend` báo `unhealthy` dù web vẫn mở được
- **Nguyên nhân:** healthcheck dùng `localhost` → trong container resolve ra IPv6 `::1`, mà nginx chỉ listen IPv4 → "connection refused".
- **Cách sửa:** trong `docker-compose.yml`, healthcheck của `frontend` dùng `127.0.0.1`:
  ```yaml
  test: ["CMD-SHELL", "wget -qO- http://127.0.0.1/nginx-health || exit 1"]
  ```
  Rồi: `docker compose up -d frontend`
  *(Sửa này đã được áp dụng sẵn trong repo.)*

### c) `worker` báo `unhealthy`
- **Nguyên nhân:** worker build chung Dockerfile với api nên thừa hưởng HEALTHCHECK `curl localhost:8000/health`, nhưng worker **không mở HTTP server** → luôn fail.
- **Cách sửa:** trong `docker-compose.yml`, service `worker` thêm:
  ```yaml
  healthcheck:
    disable: true
  ```
  Rồi: `docker compose up -d worker`
  *(Sửa này đã được áp dụng sẵn trong repo.)*

### d) Link đổi mỗi lần khởi động lại
- Quick tunnel cấp URL **ngẫu nhiên mới** mỗi lần chạy `cloudflared`. Mở lại = link mới = phải gửi lại. Muốn link cố định → xem [Nâng cấp](#nâng-cấp-link-cố-định) bên dưới.

### e) Link chết giữa chừng
- Kiểm tra: máy có ngủ/tắt không? Docker còn chạy? Cửa sổ `cloudflared` còn mở? Cả 3 phải sống.

---

## Kiểm tra link bằng lệnh

```powershell
$u = "https://<chuoi-ngau-nhien>.trycloudflare.com"   # thay bằng link thật
$h = @{ "User-Agent" = "Mozilla/5.0 Chrome/149" }

# Trang chủ → mong đợi HTTP 200
(Invoke-WebRequest -Uri "$u/" -Headers $h -UseBasicParsing).StatusCode

# API qua link → mong đợi HTTP 200 + dữ liệu JSON
(Invoke-WebRequest -Uri "$u/api/travel/community/featured-destinations?limit=3" -Headers $h -UseBasicParsing).Content
```

---

## Chạy tunnel ở chế độ nền (không chiếm cửa sổ)

```powershell
$exe = "$env:USERPROFILE\cloudflared\cloudflared.exe"
$log = "$env:USERPROFILE\cloudflared\tunnel.log"
Start-Process -FilePath $exe `
  -ArgumentList "tunnel","--url","http://127.0.0.1:3000","--no-autoupdate" `
  -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden

Start-Sleep -Seconds 6
Select-String -Path "$log","$log.err" -Pattern "https://.*\.trycloudflare\.com" | Select-Object -First 1
```

Dừng tunnel nền:
```powershell
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## Nâng cấp: link cố định

Quick tunnel là link tạm, đổi liên tục. Muốn **link cố định + domain riêng** (vẫn miễn phí, nhưng cần tài khoản Cloudflare + 1 domain):

1. Tạo tài khoản Cloudflare, add domain của bạn.
2. `cloudflared tunnel login`
3. `cloudflared tunnel create travelbuddy`
4. `cloudflared tunnel route dns travelbuddy travelbuddy.<domain>.com`
5. Tạo file `config.yml` trỏ `travelbuddy.<domain>.com` → `http://127.0.0.1:3000`
6. `cloudflared tunnel run travelbuddy`

Khi đó link là `https://travelbuddy.<domain>.com`, không đổi.

> Nếu cần chạy thật 24/7 (không phụ thuộc máy cá nhân), nên chuyển sang VPS thay vì tunnel.

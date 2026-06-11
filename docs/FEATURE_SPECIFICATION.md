# TRAVELBUDDY — ĐẶC TẢ CHỨC NĂNG CHI TIẾT

> **Tài liệu:** Software Requirements Specification (SRS)
> **Phiên bản:** 2.0
> **Phân loại:** Tài liệu kỹ thuật & Báo cáo đồ án

---

## MỤC LỤC

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Chức năng 1 — Lập kế hoạch du lịch](#2-chức-năng-1--lập-kế-hoạch-du-lịch)
3. [Chức năng 2 — Giá vé máy bay thông minh](#3-chức-năng-2--giá-vé-máy-bay-thông-minh)
4. [Chức năng 3 — Tìm kiếm khách sạn](#4-chức-năng-3--tìm-kiếm-khách-sạn)
5. [Chức năng 4 — Cộng đồng & Chia sẻ](#5-chức-năng-4--cộng-đồng--chia-sẻ)
6. [Chức năng 5 — TravelBuddy AI](#6-chức-năng-5--travelbuddy-ai)
7. [Các tính năng ngang (Cross-cutting Features)](#7-các-tính-năng-ngang)

---

## 1. TỔNG QUAN HỆ THỐNG

### 1.1 Giới thiệu

**TravelBuddy** là nền tảng du lịch thông minh tích hợp, kết hợp giữa công cụ lập kế hoạch trực quan, thông tin giá vé và khách sạn theo thời gian thực, cộng đồng chia sẻ kinh nghiệm, và trợ lý AI cá nhân hoá. Hệ thống được thiết kế theo triết lý **"người dùng tự thao tác — AI hỗ trợ khi cần"**, đặt người dùng làm trung tâm của mọi quyết định du lịch.

### 1.2 Đối tượng người dùng

| Nhóm | Đặc điểm | Nhu cầu chính |
|------|---------|---------------|
| **Traveler cá nhân** | 18–35 tuổi, du lịch tự túc | Lập kế hoạch nhanh, tìm giá rẻ |
| **Gia đình** | Có con nhỏ, lên kế hoạch cẩn thận | Quản lý ngân sách, hành trang |
| **Nhóm bạn** | 3–8 người, cần phối hợp lịch | Chia sẻ & cộng tác lịch trình |
| **Người lười** | Muốn AI làm thay | Nhập yêu cầu → nhận kết quả |

### 1.3 Kiến trúc chức năng tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRAVELBUDDY                              │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  Lập kế      │  Giá vé      │  Khách       │  Cộng đồng         │
│  hoạch       │  máy bay     │  sạn         │  & Review          │
│  du lịch     │  thông minh  │              │                    │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│              TravelBuddy AI — Trợ lý tích hợp                   │
│         (Hỗ trợ tất cả 4 chức năng phía trên)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. CHỨC NĂNG 1 — LẬP KẾ HOẠCH DU LỊCH

### 2.1 Mô tả tổng quan

Chức năng Lập kế hoạch du lịch là **tính năng cốt lõi** của TravelBuddy. Đây là công cụ giúp người dùng tự tay xây dựng lịch trình du lịch chi tiết theo từng ngày, theo phong cách **kéo-thả trực quan** kết hợp giao diện **ghi chú kỹ thuật số (Smart Note)** — tương tự cảm giác viết tay trên giấy nhưng thông minh hơn nhiều.

Điểm khác biệt so với các ứng dụng lên lịch thông thường: hệ thống **chủ động gợi ý** địa điểm phù hợp dựa trên điểm đến và thời gian, thay vì người dùng phải tự tìm kiếm từ đầu.

---

### 2.2 Luồng hoạt động chi tiết

#### **Bước 1 — Nhập thông tin chuyến đi**

Người dùng điền vào form khởi tạo:

| Trường | Bắt buộc | Mô tả |
|--------|----------|-------|
| Điểm đến | ✅ | Tên tỉnh/thành phố hoặc quốc gia — có autocomplete gợi ý |
| Điểm xuất phát | ✅ | Để tính khoảng cách di chuyển và phương tiện |
| Số ngày | ✅ | 1 đến 30 ngày |
| Ngày bắt đầu | ✅ | Ảnh hưởng đến thời tiết và lễ hội gợi ý |
| Sở thích | Tùy chọn | Thiên nhiên / Ẩm thực / Lịch sử / Mua sắm / Giải trí |
| Số người đi | Tùy chọn | Ảnh hưởng đến gợi ý chỗ ở và phương tiện |
| Ngân sách ước tính | Tùy chọn | Lọc địa điểm có phí vào cửa phù hợp |

> 💡 **Cải tiến đề xuất:** Hệ thống tự động hiển thị **"Thời điểm lý tưởng"** cho điểm đến đó (VD: *"Đà Nẵng tháng 6–8 đẹp nhất, ít mưa"*) ngay sau khi người dùng chọn điểm đến.

---

#### **Bước 2 — Khám phá địa điểm & xây dựng lịch trình (Giao diện chính)**

Giao diện được chia làm **2 cột song song**:

```
┌─────────────────────────────┐  ┌─────────────────────────────┐
│   CỘT TRÁI                  │  │   CỘT PHẢI                  │
│   Danh sách địa điểm gợi ý  │  │   Smart Note — Ngày 1       │
│                             │  │                             │
│  🗺️ [Bản đồ mini]           │  │  📅 Thứ 2, 14/07/2026       │
│                             │  │  ─────────────────────────  │
│  Filter:                    │  │  ⏰ 08:00  Cáp treo Bà Nà   │
│  [Tất cả][Thiên nhiên]      │  │  ⏰ 12:00  [Trống]          │
│  [Ẩm thực][Lịch sử]        │  │  ⏰ 14:00  Phố cổ Hội An    │
│  [Vui chơi][Mua sắm]        │  │  ⏰ 19:00  [Trống]          │
│                             │  │                             │
│  📍 Cáp treo Bà Nà Hills    │  │  [+ Thêm địa điểm thủ công] │
│     ⭐ 4.8 | 💰 750k/người  │  │  [+ Thêm ghi chú tự do]    │
│     ⏱ ~3 giờ | ✅ Đã thêm  │  │                             │
│                             │  │  💰 Chi phí ngày 1:         │
│  📍 Bãi biển Mỹ Khê         │  │     Ước tính: 1.200.000đ   │
│     ⭐ 4.6 | 💰 Miễn phí    │  │                             │
│     ⏱ ~2 giờ | [+ Thêm]    │  │  [← Ngày trước] [Ngày sau→]│
│                             │  │  [✅ Hoàn thành ngày này]   │
│  📍 Núi Thần Tài            │  │                             │
│     ⭐ 4.3 | 💰 350k/người  │  │                             │
│     ⏱ ~4 giờ | [+ Thêm]    │  │                             │
└─────────────────────────────┘  └─────────────────────────────┘
```

**Chi tiết cột trái — Danh sách địa điểm:**

- Hiển thị **tất cả địa điểm nổi bật** tại điểm đến đã chọn, có phân loại theo tab
- Mỗi địa điểm hiển thị: tên, ảnh thumbnail, sao đánh giá, giá vé vào (nếu có), thời gian tham quan ước tính, khoảng cách từ trung tâm
- Tính năng **bộ lọc thông minh**: lọc theo loại hình, giá vé, đánh giá, khoảng cách
- Tính năng **sắp xếp theo lộ trình tối ưu**: hệ thống gợi ý thứ tự địa điểm tránh đi lại nhiều (cluster theo khu vực)
- Khi người dùng đã thêm 1 địa điểm, card đó sẽ hiển thị badge **"✅ Đã thêm vào ngày X"** thay vì nút `+ Thêm`

**Chi tiết cột phải — Smart Note:**

- Mỗi ngày là 1 **"trang note kỹ thuật số"** với giao diện trực quan giống sổ tay
- Timeline theo giờ (06:00 → 22:00), mỗi slot 30 phút
- Khi ấn `+ Thêm` ở cột trái → địa điểm tự động điền vào slot trống gần nhất, người dùng kéo chỉnh giờ nếu muốn
- Người dùng có thể **tự gõ tên địa điểm** bất kỳ nếu không có trong danh sách (VD: nhà hàng quen, chỗ hẹn riêng)
- Có ô **"Ghi chú tự do"** ở cuối mỗi ngày (VD: *"Nhớ đặt bàn nhà hàng trước 2 tiếng"*)
- Hiển thị **tổng chi phí ước tính** theo ngày và cả chuyến

> 💡 **Cải tiến đề xuất:**
> - **Cảnh báo xung đột lịch**: Nếu người dùng thêm 2 địa điểm vào cùng giờ → hệ thống hiển thị cảnh báo màu đỏ
> - **Gợi ý thời gian thực tế**: Dựa trên đánh giá từ cộng đồng, hệ thống tự động đề xuất *"Nên đến Bà Nà lúc 8h sáng để tránh đông"*
> - **Gợi ý ăn uống tự động**: Sau khi điền địa điểm tham quan, hệ thống tự gợi ý nhà hàng/quán ăn gần đó phù hợp bữa trưa/tối

---

#### **Bước 3 — Hoàn thành từng ngày**

- Sau khi điền đủ lịch ngày 1 → ấn **"✅ Hoàn thành ngày này"**
- Hệ thống hiển thị **tổng kết ngày 1**: số địa điểm, tổng giờ di chuyển, chi phí ước tính
- Tự động chuyển sang **Smart Note ngày 2**, danh sách địa điểm cột trái tự động lọc bỏ những địa điểm đã thêm ở ngày 1
- Ở những ngày tiếp theo, hệ thống có thêm **"Gợi ý tiếp nối"**: *"Hôm qua bạn ở khu Sơn Trà, hôm nay gợi ý các địa điểm khu Ngũ Hành Sơn gần đó"*
- Người dùng có thể **quay lại chỉnh sửa** ngày trước bất kỳ lúc nào

---

#### **Bước 4 — Chọn hành trang (Tùy chọn)**

Sau khi hoàn thành ngày cuối → hệ thống hỏi: *"Bạn có muốn lập danh sách hành trang không?"*

Người dùng có thể **bỏ qua** hoặc tiếp tục:

**Giao diện chọn hành trang:**

```
📦 DANH SÁCH HÀNH TRANG — Chuyến đi Đà Nẵng 3 ngày

Hệ thống gợi ý tự động dựa trên:
  • Thời tiết Đà Nẵng tháng 7: Nắng nóng, có mưa buổi chiều
  • Địa điểm đã chọn: Biển, leo núi, phố cổ

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   👗 QUẦN ÁO    │  │  🎒 PHỤ KIỆN    │  │  🧴 VỆ SINH     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ ☑ Quần short   │  │ ☑ Kính mát      │  │ ☑ Kem chống nắng│
│ ☑ Áo phông (3) │  │ ☑ Kem chống nắng│  │ ☑ Bàn chải đánh│
│ ☐ Áo khoác nhẹ │  │ ☑ Dép biển      │  │ ☑ Sữa tắm       │
│ ☑ Đồ bơi       │  │ ☐ Máy ảnh       │  │ ☐ Thuốc say xe  │
│ ☐ Sandal       │  │ ☑ Sạc dự phòng  │  │ ☑ Thuốc đau đầu │
│ [+ Thêm...]    │  │ [+ Thêm...]     │  │ [+ Thêm...]     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

> 💡 **Cải tiến đề xuất:**
> - Hệ thống **tự động tích sẵn** những đồ dùng phù hợp dựa trên thời tiết và địa điểm (người dùng chỉ cần bỏ tích những gì không cần)
> - Thêm danh mục **"Giấy tờ & Thẻ"**: CMND, thẻ ATM, vé in sẵn...
> - Thêm nút **"Lưu template hành trang"** để lần sau dùng lại

---

#### **Bước 5 — Xuất kết quả**

Sau khi hoàn thành, hệ thống tổng hợp và hiển thị **bản xem trước**:

```
┌────────────────────────────────────────────────────┐
│           LỊCH TRÌNH CHUYẾN ĐI ĐÀ NẴNG            │
│              14/07 – 16/07/2026 (3 ngày)           │
├────────────────────────────────────────────────────┤
│  NGÀY 1 – Thứ 2, 14/07          Ước tính: 1.200k  │
│  08:00  Cáp treo Bà Nà Hills    750k/người         │
│  12:30  Cơm nhà hàng Madame Lan 150k/người         │
│  14:00  Phố cổ Hội An           Miễn phí           │
│  19:30  Thả đèn hoa đăng        50k/người          │
├────────────────────────────────────────────────────┤
│  NGÀY 2 – Thứ 3, 15/07          Ước tính: 800k    │
│  ...                                               │
├────────────────────────────────────────────────────┤
│  💰 TỔNG CHI PHÍ DỰ KIẾN: ~4.500.000đ/người       │
├────────────────────────────────────────────────────┤
│  📦 HÀNH TRANG: 18 món                             │
│  Quần áo (6) | Phụ kiện (7) | Vệ sinh (5)         │
└────────────────────────────────────────────────────┘

  [📥 Xuất PDF]   [🖼️ Xuất ảnh (PNG)]   [📤 Chia sẻ lên cộng đồng]
  [📋 Sao chép link]   [✏️ Chỉnh sửa lại]
```

**Định dạng xuất:**
- **PDF**: 1 file nhiều trang — trang 1 là lịch trình, trang cuối là hành trang (bố cục tự động điều chỉnh theo số ngày)
- **PNG**: 1 ảnh dạng infographic đẹp, tối ưu chia sẻ lên mạng xã hội
- **Chia sẻ lên cộng đồng**: Đăng thẳng lên mục Cộng đồng của TravelBuddy (có thể chọn public hoặc riêng tư)

> 💡 **Cải tiến đề xuất:** Thêm nút **"Thêm vào Google Calendar"** để export file `.ics`, người dùng có thể import thẳng vào lịch điện thoại.

---

### 2.3 Tóm tắt yêu cầu chức năng

| Mã | Yêu cầu | Ưu tiên |
|----|---------|---------|
| PL-01 | Nhập điểm đến với autocomplete và gợi ý thời điểm lý tưởng | Cao |
| PL-02 | Hiển thị danh sách địa điểm phân loại theo tab, có filter | Cao |
| PL-03 | Thêm địa điểm vào Smart Note bằng click hoặc kéo-thả | Cao |
| PL-04 | Tự nhập địa điểm tùy chỉnh nếu không có trong danh sách | Cao |
| PL-05 | Cảnh báo xung đột lịch khi 2 hoạt động trùng giờ | Trung bình |
| PL-06 | Gợi ý nhà hàng/ăn uống tự động theo địa điểm và buổi trong ngày | Trung bình |
| PL-07 | Hiển thị tổng chi phí ước tính theo ngày và cả chuyến | Cao |
| PL-08 | Hành trang gợi ý tự động dựa trên thời tiết + địa điểm | Cao |
| PL-09 | Xuất PDF và PNG với bố cục chuyên nghiệp | Cao |
| PL-10 | Export file `.ics` để thêm vào Google/Apple Calendar | Thấp |
| PL-11 | Lưu và chỉnh sửa lịch trình bất kỳ lúc nào | Cao |
| PL-12 | Gợi ý sắp xếp địa điểm theo cluster địa lý tối ưu | Trung bình |

---

## 3. CHỨC NĂNG 2 — GIÁ VÉ MÁY BAY THÔNG MINH

### 3.1 Mô tả tổng quan

Chức năng Giá vé máy bay thông minh không chỉ đơn thuần hiển thị giá — đây là **công cụ hỗ trợ quyết định** (Decision Support Tool) giúp người dùng chọn ngày bay tối ưu bằng cách **kết hợp 3 chiều thông tin**: giá vé, thời tiết điểm đến và cảnh báo ngày lễ/sự kiện đặc biệt.

> **Lưu ý:** Chức năng này hoàn toàn mang tính **tham khảo**. TravelBuddy không thực hiện đặt vé — chỉ cung cấp thông tin và liên kết tới trang đặt vé chính thức của từng hãng.

---

### 3.2 Luồng hoạt động chi tiết

#### **Bước 1 — Nhập thông tin tìm kiếm**

| Trường | Bắt buộc | Mô tả |
|--------|----------|-------|
| Điểm khởi hành | ✅ | Chọn từ danh sách sân bay (IATA code + tên tiếng Việt) |
| Điểm đến | ✅ | Tương tự |
| Tháng muốn xem | ✅ | Picker chọn tháng/năm (xem tổng quan cả tháng) |
| Số người lớn | Tùy chọn | Mặc định: 1 người |
| Hạng ghế | Tùy chọn | Economy / Business (mặc định: Economy) |

> 💡 **Cải tiến đề xuất:** Thêm tùy chọn **"Tôi linh hoạt ngày đi"** → hệ thống tự tìm và highlight 3–5 ngày rẻ nhất trong tháng.

---

#### **Bước 2 — Xem lịch giá theo tháng (Price Calendar)**

Giao diện chính là **lịch tháng dạng grid**, mỗi ô là 1 ngày:

```
◀ Tháng 6/2026                HÀ NỘI (HAN) → ĐÀ NẴNG (DAD)           Tháng 7 ▶

Thứ 2    Thứ 3    Thứ 4    Thứ 5    Thứ 6    Thứ 7    CN
                                     1        2        3
                                   ☀️980k   🌤️1.2tr   ☀️750k ⭐
  4        5        6        7        8        9        10
🌧️1.4tr  ☀️890k  ☀️760k ⭐ ☀️820k   🌤️1.1tr  ☀️690k ⭐ ☀️720k
  ...
```

**Giải thích từng ô ngày:**
- **Dòng 1**: Icon thời tiết (☀️ Nắng / ⛅ Mây / 🌧️ Mưa / 🌩️ Giông)
- **Dòng 2**: Giá vé rẻ nhất tìm thấy hôm đó (format `XXXk` hoặc `X.Xtr`)
- **Badge ⭐**: Đánh dấu ngày có giá rẻ nhất + thời tiết đẹp (khuyến nghị của hệ thống)
- **Màu nền ô**:
  - 🟢 Xanh nhạt: Giá rẻ (dưới mức trung bình 20%)
  - ⚪ Trắng: Giá trung bình
  - 🔴 Hồng nhạt: Giá cao (trên mức trung bình 20%)
  - ⚫ Xám: Ngày đã qua hoặc không có chuyến bay

**Thanh thông tin bên phải lịch:**
```
📊 THỐNG KÊ THÁNG 6
  Giá rẻ nhất: 690.000đ (ngày 9)
  Giá trung bình: 980.000đ
  Giá cao nhất: 1.850.000đ

🌤️ THỜI TIẾT THÁNG 6
  Tại Đà Nẵng: Nắng 70% | Mưa 30%
  Nhiệt độ TB: 29–33°C

⚠️ LƯU Ý THÁNG NÀY
  • 1/6: Ngày Quốc tế Thiếu nhi — đông, giá cao
  • Mùa hè cao điểm — nên đặt sớm
```

---

#### **Bước 3 — Xem chi tiết ngày (Popup/Modal)**

Khi người dùng click vào 1 ngày bất kỳ, hiển thị popup chi tiết:

```
┌──────────────────────────────────────────────────────────────┐
│  🗓️ Thứ 6, ngày 09 tháng 6 năm 2026                         │
│  HÀ NỘI (HAN) → ĐÀ NẴNG (DAD) • 1 người lớn • Economy      │
├──────────────────────────────────────────────────────────────┤
│  ✈️ CHUYẾN BAY                                               │
│                                                              │
│  🥇 VietJet Air              05:45 → 07:10  1h25m           │
│     Thẳng • Economy          690.000đ/người                  │
│     ⭐ Rẻ nhất hôm nay       [🔗 Đặt vé tại VietJet.com]    │
│  ─────────────────────────────────────────────────────────   │
│  🥈 Bamboo Airways           07:30 → 08:55  1h25m           │
│     Thẳng • Economy          850.000đ/người                  │
│                              [🔗 Đặt vé tại BambooAir.com]   │
│  ─────────────────────────────────────────────────────────   │
│  🥉 Vietnam Airlines         10:00 → 11:25  1h25m           │
│     Thẳng • Economy          1.250.000đ/người                │
│     ✅ Bay đúng giờ cao       [🔗 Đặt vé tại VietnamAir.com] │
│  ─────────────────────────────────────────────────────────   │
│  + Xem thêm 5 chuyến khác    [🔽 Mở rộng]                   │
├──────────────────────────────────────────────────────────────┤
│  🌤️ THỜI TIẾT ĐÀ NẴNG — 09/06/2026                         │
│                                                              │
│  ☀️ Buổi sáng    31°C   Nắng đẹp, ít mây                    │
│  ⛅ Buổi chiều   33°C   Mây rải rác, có thể có mưa rào nhẹ  │
│  🌧️ Buổi tối    28°C   Mưa vừa, khoảng 70% khả năng        │
│                                                              │
│  💧 Độ ẩm: 78%    💨 Gió: 15 km/h hướng Đông               │
│  🌊 Sóng biển: Nhỏ (0.5–1m) — Tắm biển bình thường         │
│                                                              │
│  🕶️ Chỉ số UV: 8 (Rất cao) — Cần kem chống nắng SPF 50+    │
├──────────────────────────────────────────────────────────────┤
│  💡 GỢI Ý CỦA TRAVELBUDDY                                   │
│  Ngày này có giá vé rẻ nhất tháng, thời tiết buổi sáng đẹp. │
│  Lý tưởng cho chuyến bay sớm + tắm biển buổi sáng!          │
│                              [+ Thêm vào lịch trình của tôi] │
└──────────────────────────────────────────────────────────────┘
```

> 💡 **Cải tiến đề xuất:**
> - Thêm **"So sánh 2 ngày"**: người dùng chọn 2 ngày → xem song song giá + thời tiết
> - Thêm **"Đặt cảnh báo giá"**: nhập email → nhận thông báo khi giá xuống dưới ngưỡng đặt

---

### 3.3 Tóm tắt yêu cầu chức năng

| Mã | Yêu cầu | Ưu tiên |
|----|---------|---------|
| FL-01 | Hiển thị lịch tháng với giá vé rẻ nhất + icon thời tiết từng ngày | Cao |
| FL-02 | Phân biệt màu sắc ô ngày theo mức giá (rẻ/trung bình/đắt) | Cao |
| FL-03 | Tự động đề xuất ngày tốt nhất (giá thấp + thời tiết đẹp) | Cao |
| FL-04 | Popup chi tiết: ≥3 hãng bay từ rẻ đến đắt, kèm link đặt vé | Cao |
| FL-05 | Thời tiết chi tiết 3 buổi: sáng/chiều/tối + độ ẩm, gió, UV, sóng biển | Cao |
| FL-06 | Cảnh báo ngày lễ / sự kiện lớn có thể ảnh hưởng giá và đám đông | Trung bình |
| FL-07 | So sánh 2 ngày cùng lúc | Trung bình |
| FL-08 | Thêm ngày bay vào lịch trình đang lập | Trung bình |
| FL-09 | Đặt cảnh báo khi giá xuống dưới ngưỡng (Price Alert) | Thấp |

---

## 4. CHỨC NĂNG 3 — TÌM KIẾM KHÁCH SẠN

### 4.1 Mô tả tổng quan

Công cụ tìm kiếm và so sánh khách sạn của TravelBuddy giúp người dùng **lọc nhanh** lựa chọn phù hợp từ hàng chục tùy chọn, với thông tin rõ ràng về vị trí, tiện ích và mức giá thực tế. Tương tự giá vé máy bay, đây là công cụ **tham khảo** — mọi đặt phòng được thực hiện trên trang của đối tác.

---

### 4.2 Luồng hoạt động chi tiết

#### **Bước 1 — Nhập thông tin tìm kiếm**

| Trường | Bắt buộc | Mô tả |
|--------|----------|-------|
| Điểm đến | ✅ | Tên thành phố / tỉnh |
| Ngày nhận phòng | ✅ | Check-in date |
| Ngày trả phòng | ✅ | Check-out date (tự tính số đêm) |
| Số người | ✅ | Người lớn + trẻ em |
| Số phòng | Tùy chọn | Mặc định: 1 phòng |
| Ngân sách tối đa / đêm | Tùy chọn | Slider range |

---

#### **Bước 2 — Xem danh sách khách sạn**

Giao diện 2 chế độ xem: **Danh sách (List)** và **Bản đồ (Map)**

**Chế độ List — Mỗi card khách sạn hiển thị:**

```
┌─────────────────────────────────────────────────────────────┐
│  [ẢNH 1][ẢNH 2][ẢNH 3]  ←→                 ❤️ Yêu thích   │
│                                                             │
│  ★★★★☆  Mường Thanh Luxury Đà Nẵng Hotel                  │
│  📍 Đường Võ Nguyên Giáp, Bãi biển Mỹ Khê — 0.2km biển   │
│  ⭐ 4.7/5 (2.847 đánh giá) | 🏆 Top lựa chọn tháng này    │
│                                                             │
│  ✅ Hồ bơi vô cực    ✅ Bữa sáng miễn phí                  │
│  ✅ WiFi tốc độ cao  ✅ Đưa đón sân bay                    │
│  ✅ Phòng gym        ✅ Spa                                 │
│                                                             │
│  [Xem trên bản đồ]  [Xem ảnh (47)]  [Đọc đánh giá (2.8k)] │
│                                                             │
│  💰 Từ  1.800.000đ / đêm                                   │
│     (cho 2 người, bao gồm thuế)                            │
│     3 đêm × 1.800.000đ = 5.400.000đ                       │
│                          [🔗 Xem & đặt phòng tại Agoda.com]│
└─────────────────────────────────────────────────────────────┘
```

**Bộ lọc sidebar:**

```
🔽 LỌC KẾT QUẢ

💰 Giá / đêm
   0đ ────●─────────── 3.000.000đ

⭐ Xếp hạng sao
   [1★][2★][3★][4★][5★]

🏆 Điểm đánh giá
   Tuyệt vời 9+  Rất tốt 8+  Tốt 7+

🏊 Tiện ích
   [☐] Hồ bơi       [☐] Bãi biển riêng
   [☐] Bữa sáng     [☐] Đỗ xe miễn phí
   [☐] Gym/Spa      [☐] Thân thiện trẻ em
   [☐] Đưa đón bay  [☐] Phòng không hút thuốc

📍 Khu vực
   [☐] Trung tâm thành phố
   [☐] Gần biển (< 500m)
   [☐] Gần sân bay (< 5km)
   [☐] Khu phố cổ

🛏️ Loại phòng
   [Phòng đơn][Phòng đôi][Suite][Căn hộ]

🏠 Loại chỗ ở
   [Khách sạn][Resort][Homestay][Hostel][Villa]
```

**Sắp xếp kết quả:**
```
[Phổ biến nhất ▼] [Giá thấp → cao] [Giá cao → thấp] [Điểm cao nhất] [Gần nhất]
```

---

#### **Bước 3 — Xem chi tiết khách sạn**

Khi click vào card → mở trang chi tiết đầy đủ:

- **Gallery ảnh** tất cả phòng + tiện ích
- **Mô tả chi tiết** bằng tiếng Việt
- **Danh sách phòng** với giá từng loại (Standard, Deluxe, Suite...)
- **Bản đồ vị trí** với các địa điểm nổi bật xung quanh
- **Đánh giá thực tế** từ TravelBuddy cộng đồng + Booking.com/Agoda
- **Link đặt phòng** đến ≥3 OTA (Booking.com, Agoda, Traveloka) để so sánh giá

> 💡 **Cải tiến đề xuất:**
> - Tính năng **"So sánh 3 khách sạn"**: chọn 3 khách sạn → so sánh song song theo bảng tiêu chí
> - Hiển thị **"Giá theo ngày trong tuần"**: chỉ ra thứ mấy trong tuần khách sạn này rẻ nhất
> - Badge **"Gần địa điểm trong lịch trình của bạn"**: nếu người dùng đã có lịch trình, hệ thống gợi ý khách sạn gần nhất với các điểm đã chọn

---

### 4.3 Tóm tắt yêu cầu chức năng

| Mã | Yêu cầu | Ưu tiên |
|----|---------|---------|
| HT-01 | Tìm kiếm khách sạn theo thành phố, ngày, số người | Cao |
| HT-02 | Bộ lọc đa tiêu chí: giá, sao, tiện ích, khu vực, loại phòng | Cao |
| HT-03 | Sắp xếp kết quả theo 5 tiêu chí khác nhau | Cao |
| HT-04 | Hiển thị giá tổng theo số đêm ngay trên card | Cao |
| HT-05 | Liên kết đặt phòng đến ≥3 OTA để so sánh | Cao |
| HT-06 | Xem vị trí trên bản đồ tích hợp | Cao |
| HT-07 | So sánh 3 khách sạn side-by-side | Trung bình |
| HT-08 | Gợi ý khách sạn gần địa điểm trong lịch trình hiện tại | Trung bình |
| HT-09 | Lưu yêu thích để xem lại sau | Thấp |

---

## 5. CHỨC NĂNG 4 — CỘNG ĐỒNG & CHIA SẺ

### 5.1 Mô tả tổng quan

Cộng đồng TravelBuddy là **mạng xã hội du lịch thu nhỏ** — nơi người dùng chia sẻ kinh nghiệm thực tế, lịch trình đã trải nghiệm, và truyền cảm hứng cho nhau. Không giống các mạng xã hội thông thường, nội dung tại đây được **tổ chức có cấu trúc** theo điểm đến — giúp người đang lên kế hoạch tìm kiếm thông tin cực kỳ nhanh.

---

### 5.2 Luồng hoạt động chi tiết

#### **5.2.1 Đăng bài chia sẻ**

Người dùng có thể đăng bài theo 2 cách:

**Cách 1 — Chia sẻ từ lịch trình vừa tạo:**
- Sau khi xuất PDF/PNG từ Chức năng 1, có nút **"📤 Chia sẻ lên cộng đồng"**
- Hệ thống tự điền: ảnh lịch trình, điểm đến, số ngày, chi phí ước tính
- Người dùng thêm: mô tả cá nhân, đánh giá sao tổng thể, ảnh thực tế chuyến đi

**Cách 2 — Đăng bài mới từ trang Cộng đồng:**
```
┌─────────────────────────────────────────────────────────────┐
│  📝 CHIA SẺ TRẢI NGHIỆM DU LỊCH                            │
├─────────────────────────────────────────────────────────────┤
│  Tiêu đề bài viết:                                          │
│  [Ví dụ: 3 ngày Đà Nẵng với 3 triệu — trải nghiệm thật!]  │
│                                                             │
│  Điểm đến: [Đà Nẵng ▼]    Thời gian đi: [Tháng 6/2026]   │
│                                                             │
│  Loại bài: [Lịch trình][Review][Mẹo hay][Cảnh báo]        │
│                                                             │
│  Nội dung: (hỗ trợ định dạng văn bản cơ bản)              │
│  [                                                    ]     │
│  [                                                    ]     │
│                                                             │
│  📎 Đính kèm:                                              │
│  [📄 Upload PDF lịch trình]  [🖼️ Upload ảnh (tối đa 10)]  │
│  [📋 Gắn lịch trình từ TravelBuddy của tôi ▼]             │
│                                                             │
│  Tags: #DaNang #3ngay2dem #budget3trieu                    │
│                                                             │
│  Hiển thị: [🌍 Công khai][🔒 Riêng tư][👥 Bạn bè]        │
│                           [📤 Đăng bài]                    │
└─────────────────────────────────────────────────────────────┘
```

---

#### **5.2.2 Trang khám phá cộng đồng (Feed)**

```
🗺️ CỘNG ĐỒNG TRAVELBUDDY

┌─── BỘ LỌC ────────────────────────────────────────────────┐
│ Điểm đến: [Tất cả ▼]  Loại bài: [Tất cả ▼]               │
│ Thời gian: [Tháng 6][Tháng 7][Mùa hè][Lễ Tết]           │
│ Ngân sách: [Tiết kiệm][Trung bình][Sang trọng]            │
│ Sắp xếp: [Mới nhất ▼][Nhiều lượt thích][Nhiều bình luận] │
└────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  👤 Nguyễn Minh Anh  •  ⭐⭐⭐⭐⭐  •  Đà Nẵng  •  3 ngày   │
│  "3 ngày ở Đà Nẵng với 3 triệu — hoàn toàn có thể!"       │
│                                                             │
│  [Ảnh 1][Ảnh 2][Ảnh 3] +7 ảnh khác                       │
│                                                             │
│  "Mình vừa về từ Đà Nẵng và thực sự bất ngờ khi chi phí   │
│   chỉ hết 2.8 triệu/người cho 3 ngày 2 đêm. Vé máy bay    │
│   mình book sớm 1 tháng được 690k/chiều..."                │
│                                                             │
│  📄 [Xem lịch trình chi tiết (PDF)]                       │
│  💰 Chi phí thực tế: 2.800.000đ/người                     │
│  📅 Tháng 6/2026                                          │
│                                                             │
│  ❤️ 347  💬 52  🔖 189  📤 Chia sẻ                        │
│  [+ Sao chép lịch trình về Trip của tôi]                   │
└─────────────────────────────────────────────────────────────┘
```

---

#### **5.2.3 Trang điểm đến (Destination Hub)**

Mỗi điểm đến có **trang riêng** tổng hợp tất cả bài viết liên quan:

```
🏖️ CỘNG ĐỒNG ĐÀ NẴNG — 4.827 bài viết

[Lịch trình][Review khách sạn][Review nhà hàng][Mẹo hay][Hỏi & Đáp]

📊 TỔNG QUAN TỪ CỘNG ĐỒNG (dựa trên 4.827 bài)
  ⭐ Điểm đánh giá TB: 4.6/5
  💰 Chi phí TB: 2.5 – 4 triệu/người/3 ngày
  📅 Thời điểm được review nhiều nhất: Tháng 6–8
  🌤️ Đánh giá thời tiết: "Nắng đẹp, nóng, nên đi biển sáng sớm"
  🍜 Top 3 quán ăn được nhắc nhiều nhất: ...
  🏨 Top 3 khách sạn được recommend nhiều nhất: ...
```

> 💡 **Cải tiến đề xuất:**
> - Tính năng **"Clone lịch trình"**: Xem bài người khác và chỉ cần 1 click để copy lịch trình đó vào Trip Builder của mình, rồi chỉnh sửa theo ý
> - Tính năng **"Hỏi & Đáp theo điểm đến"**: Forum Q&A nhỏ gắn với từng điểm đến, người đã đi có thể giải đáp cho người chưa đi

---

### 5.3 Tóm tắt yêu cầu chức năng

| Mã | Yêu cầu | Ưu tiên |
|----|---------|---------|
| CM-01 | Đăng bài kèm ảnh, PDF lịch trình | Cao |
| CM-02 | Tự động chia sẻ từ kết quả Chức năng 1 | Cao |
| CM-03 | Bộ lọc: điểm đến, loại bài, thời gian, ngân sách | Cao |
| CM-04 | Sắp xếp: mới nhất, nhiều like, nhiều comment | Cao |
| CM-05 | Trang hub theo điểm đến với thống kê tổng hợp | Trung bình |
| CM-06 | Clone lịch trình về Trip Builder của mình | Trung bình |
| CM-07 | Forum Hỏi & Đáp theo điểm đến | Thấp |
| CM-08 | Đánh dấu bài viết yêu thích (bookmark) | Thấp |

---

## 6. CHỨC NĂNG 5 — TRAVELBUDDY AI

### 6.1 Mô tả tổng quan

TravelBuddy AI là **trợ lý du lịch cá nhân ảo** — hoạt động như một người bạn đồng hành thông minh, sẵn sàng làm hầu hết mọi việc thay người dùng: từ lên lịch trình, tìm vé máy bay, gợi ý khách sạn, đến trả lời các câu hỏi về điểm đến. AI không phải trung tâm của hệ thống, mà là **lớp hỗ trợ linh hoạt** — đặc biệt hữu ích cho người dùng bận rộn hoặc lần đầu đi đến nơi xa lạ.

---

### 6.2 Luồng hoạt động chi tiết

#### **6.2.1 Giao diện AI Chat**

AI xuất hiện dưới dạng **floating button** ở góc phải dưới màn hình trên mọi trang. Khi click → mở panel chat.

Người dùng gõ yêu cầu bằng ngôn ngữ tự nhiên tiếng Việt:

```
Ví dụ input của người dùng:
"Tôi muốn đi Phú Quốc 4 ngày 3 đêm, 2 người, ngân sách
khoảng 10 triệu/người, thích tắm biển và ăn hải sản,
không thích quá đông đúc. Xuất phát từ Hà Nội."
```

---

#### **6.2.2 Kết quả AI trả về — 5 phần**

AI tổng hợp và trả về kết quả có cấu trúc gồm **5 phần rõ ràng**:

---

**Phần 1 — Giới thiệu điểm đến**

```
🏝️ PHÚ QUỐC — ĐẢO NGỌC VIỆT NAM

[ẢNH PANORAMA PHÚ QUỐC]

Phú Quốc là hòn đảo lớn nhất Việt Nam, thuộc tỉnh Kiên Giang,
nổi tiếng với những bãi biển cát trắng mịn, nước biển trong
xanh và hải sản tươi ngon. Tháng 6–8 là mùa mưa (giá rẻ hơn),
tháng 11–4 là mùa khô (lý tưởng nhất). Dựa trên ngân sách của
bạn, đây là lựa chọn hoàn toàn phù hợp!

🌤️ Thời tiết hiện tại: 30°C, nắng nhẹ
⭐ Điểm đánh giá cộng đồng: 4.7/5
💰 Ngân sách của bạn: Thoải mái cho 4 ngày
```

---

**Phần 2 — Gợi ý lịch trình**

```
📅 LỘ TRÌNH GỢI Ý — 4 NGÀY 3 ĐÊM PHÚ QUỐC

NGÀY 1: Khám phá phía Nam
  🌅 08:00  Bãi Sao — bãi biển đẹp nhất đảo
  🐠 11:00  Lặn ngắm san hô tại Hòn Thơm
  🦞 13:00  Ăn trưa hải sản tại chợ Dương Đông
  🌴 15:30  Vườn tiêu & Trại nuôi cá sấu
  🌇 18:00  Ngắm hoàng hôn tại Dinh Cậu

NGÀY 2: Cáp treo & Vinpearl
  🚡 09:00  Cáp treo 3 dây vượt biển dài nhất thế giới
  🎡 10:00  Vinpearl Safari — sở thú bán hoang dã
  ...

[📋 Thêm lịch trình này vào Trip Builder]
```

---

**Phần 3 — Chuyến bay**

```
✈️ VÉ MÁY BAY GỢI Ý — HÀ NỘI → PHÚ QUỐC

🥇 VietJet Air         HAN → PQC
   Thứ 6, 14/06/2026   06:30 → 09:00  (2h30m)
   💰 1.350.000đ/người  [🔗 Đặt vé tại VietJet.com]
   ⭐ Giá tốt nhất tuần này

🥈 Bamboo Airways      HAN → PQC
   Thứ 6, 14/06/2026   08:45 → 11:20  (2h35m)
   💰 1.580.000đ/người  [🔗 Đặt vé tại BambooAir.com]

🥉 Vietnam Airlines    HAN → PQC
   Thứ 6, 14/06/2026   10:30 → 13:05  (2h35m)
   💰 2.100.000đ/người  [🔗 Đặt vé tại VietnamAir.com]
   ✅ Uy tín, ít delay

[🔍 Xem lịch giá cả tháng 6]
```

---

**Phần 4 — Khách sạn**

```
🏨 KHÁCH SẠN GỢI Ý — PHÚ QUỐC

Dựa trên: 2 người, 3 đêm, thích yên tĩnh, gần biển

🥇 Lahana Resort & Spa ★★★★
   📍 Bãi Dài — 50m ra biển, vắng, yên tĩnh
   ⭐ 4.6/5 (1.247 đánh giá)
   ✅ Hồ bơi | Bữa sáng | Đưa đón sân bay
   💰 950.000đ/đêm → 3 đêm = 2.850.000đ
   [🔗 Đặt phòng tại Agoda] [🔗 Booking.com]

🥈 Coco Palm Resort ★★★
   📍 Bãi Trường — Sôi động hơn, nhiều nhà hàng
   ⭐ 4.4/5 (892 đánh giá)
   💰 720.000đ/đêm → 3 đêm = 2.160.000đ
   [🔗 Đặt phòng tại Agoda]

🥉 La Veranda Resort ★★★★★
   📍 Dương Đông — Boutique, phong cách Pháp thuộc địa
   ⭐ 4.9/5 (632 đánh giá)
   💰 2.800.000đ/đêm → 3 đêm = 8.400.000đ
   [🔗 Đặt phòng tại Booking.com]
```

---

**Phần 5 — Tổng kết ngân sách**

```
💰 DỰ TOÁN CHI PHÍ TỔNG

  ✈️  Vé máy bay (2 chiều × 2 người)    5.400.000đ
  🏨  Khách sạn (3 đêm, Lahana Resort)  2.850.000đ
  🍜  Ăn uống (TB 400k/người/ngày)      3.200.000đ
  🚕  Di chuyển nội đảo                   800.000đ
  🎡  Vui chơi (Vinpearl, lặn biển)     1.500.000đ
  🛍️  Mua sắm, phát sinh                  500.000đ
  ─────────────────────────────────────────────────
  TỔNG DỰ KIẾN              ≈ 14.250.000đ
                           (≈ 7.125.000đ/người)

✅ Trong ngân sách của bạn (10tr/người)
💡 Tiết kiệm thêm: Chọn khách sạn Coco Palm → giết khoảng 700k

[📋 Lưu kế hoạch này]  [✏️ Điều chỉnh]  [📤 Chia sẻ]
```

---

#### **6.2.3 Khả năng hỏi đáp tự do**

Ngoài luồng trên, AI còn trả lời các câu hỏi tự do:

```
Người dùng hỏi gì?             AI làm gì?
─────────────────────────────────────────────────────
"Mưa tháng 7 ở Hội An không?"  → Trả lời thời tiết + gợi ý
"Cần xin visa đi Nhật không?"  → Hướng dẫn thủ tục visa đầy đủ
"Từ Đà Lạt đi Mũi Né mấy tiếng?" → Thông tin di chuyển
"Gợi ý quán ăn bình dân ở Hội An" → List 5 quán kèm địa chỉ
"Đà Nẵng hay Nha Trang đẹp hơn?" → So sánh 2 điểm đến khách quan
"Tôi có 5 ngày, nên đi đâu tháng 8?" → Gợi ý 3 điểm đến phù hợp
```

> 💡 **Cải tiến đề xuất:**
> - Tính năng **"Nhận diện địa điểm từ ảnh"**: người dùng upload ảnh → AI nhận dạng đây là nơi nào
> - Tính năng **"Tái tạo từ cộng đồng"**: Nếu câu hỏi của người dùng giống với bài viết nào trên cộng đồng, AI tự động trích dẫn và liên kết

---

### 6.3 Tóm tắt yêu cầu chức năng

| Mã | Yêu cầu | Ưu tiên |
|----|---------|---------|
| AI-01 | Hiểu yêu cầu tiếng Việt tự nhiên, đa dạng cách diễn đạt | Cao |
| AI-02 | Trả về kết quả 5 phần: Giới thiệu, Lịch trình, Vé bay, Khách sạn, Ngân sách | Cao |
| AI-03 | Ảnh điểm đến đẹp kèm mô tả ngắn | Cao |
| AI-04 | Tất cả giá vé và khách sạn có link đặt trực tiếp | Cao |
| AI-05 | Tính toán và hiển thị bảng ngân sách dự kiến | Cao |
| AI-06 | Nút "Thêm vào Trip Builder" cho lịch trình AI gợi ý | Cao |
| AI-07 | Hỏi đáp tự do về thời tiết, visa, ẩm thực, văn hoá | Trung bình |
| AI-08 | Nhận diện địa điểm từ ảnh upload | Thấp |
| AI-09 | Trích dẫn bài viết cộng đồng liên quan khi trả lời | Thấp |
| AI-10 | Lưu lịch sử cuộc hội thoại, tiếp tục ở lần sau | Trung bình |

---

## 7. CÁC TÍNH NĂNG NGANG

### 7.1 Tài khoản người dùng

| Chức năng | Mô tả |
|-----------|-------|
| Đăng ký / Đăng nhập | Email & mật khẩu; Google OAuth |
| Hồ sơ cá nhân | Ảnh đại diện, tên, sở thích du lịch |
| Lịch sử & Wishlist | Lưu các chuyến đi đã lập, địa điểm yêu thích |
| Thông báo | Cảnh báo giá vé, reply bình luận, bài mới ở điểm đến theo dõi |

### 7.2 Tìm kiếm toàn hệ thống

- Thanh tìm kiếm trên Navbar có thể tìm đồng thời: điểm đến, bài viết cộng đồng, câu hỏi AI thường gặp
- Hỗ trợ tìm kiếm **không dấu** tiếng Việt (Hà Nội = ha noi = hanoi = HN)

### 7.3 Responsive & Đa nền tảng

- Giao diện **Mobile-first**: tối ưu hoàn toàn trên điện thoại
- **Dark mode / Light mode**: tự động theo cài đặt hệ thống, có thể chỉnh tay
- Hỗ trợ **PWA** (Progressive Web App): người dùng có thể "cài" TravelBuddy lên màn hình điện thoại như app native

### 7.4 Bảo mật & Quyền riêng tư

- Mật khẩu mã hoá bằng bcrypt
- Rate limiting: chống spam và tấn công
- AI Guardrails: 4 lớp bảo vệ an toàn nội dung AI
- Người dùng kiểm soát: lịch trình public / riêng tư / chỉ bạn bè

---

## PHỤ LỤC — BẢNG TÓM TẮT TOÀN BỘ YÊU CẦU

| Mã | Tên chức năng | Số yêu cầu | Ưu tiên Cao | Ưu tiên TB | Ưu tiên Thấp |
|----|--------------|-----------|------------|------------|-------------|
| PL | Lập kế hoạch | 12 | 8 | 3 | 1 |
| FL | Giá máy bay | 9 | 5 | 3 | 1 |
| HT | Khách sạn | 9 | 6 | 2 | 1 |
| CM | Cộng đồng | 8 | 4 | 2 | 2 |
| AI | AI Trợ lý | 10 | 6 | 2 | 2 |
| **Tổng** | | **48** | **29** | **12** | **7** |

---

*Tài liệu này tuân theo chuẩn IEEE 830 — Software Requirements Specification.*
*Mọi yêu cầu đều có thể đo lường, kiểm tra và xác nhận trong quá trình kiểm thử.*

*Phiên bản 2.0 — Cập nhật: 2026*

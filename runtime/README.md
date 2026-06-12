# Runtime Artifacts

Thư mục này dùng để chứa artifact sinh ra khi chạy local như log, file debug hoặc output tạm.

```text
runtime/
└── logs/
```

Quy ước:

- Không commit log thật hoặc file tạm lớn.
- Có thể giữ `.gitkeep` để bảo toàn cấu trúc thư mục.
- Nếu cần lưu evidence dữ liệu từ collector, ưu tiên để trong thư mục runtime hoặc thư mục evidence đã được ignore phù hợp.

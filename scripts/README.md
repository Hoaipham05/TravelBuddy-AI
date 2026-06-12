# Scripts

Thư mục này chứa các script tiện ích chạy từ root project.

## Data Pipeline

```bash
python scripts/run_data_pipeline.py --summary
python scripts/run_data_pipeline.py --only weather
python scripts/run_data_pipeline.py --only flights
python scripts/run_data_pipeline.py --only hotels
```

Trong Docker, vẫn ưu tiên chạy pipeline bên trong container API:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --summary"
```

Quy ước:

- Script ở đây chỉ là wrapper/dev utility.
- Logic chính vẫn nằm trong package backend để Docker và production dùng chung.
- Khi chạy từ root, log pipeline được ghi vào `runtime/logs/pipeline.log`.

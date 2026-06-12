# Frontend

Frontend là React/Vite app. Ở giai đoạn hiện tại dự án đang tập trung hoàn thiện data/backend, nhưng cấu trúc frontend được giữ sẵn để xây UI TravelBuddy sau.

## Cấu Trúc

```text
frontend/
├── src/
│   ├── assets/
│   ├── components/
│   ├── hooks/
│   ├── layouts/
│   ├── pages/
│   ├── services/
│   └── utils/
├── Dockerfile
├── package.json
└── vite.config.js
```

## Chạy Local

```bash
cd frontend
npm install
npm run dev
```

## Ghi Chú

- Khi xây FE, ưu tiên đọc các endpoint `/travel/*` từ backend.
- Không hard-code data du lịch trong FE; dữ liệu đã nằm ở PostgreSQL và FastAPI.
- Nội dung hiển thị cho người dùng dùng tiếng Việt có dấu.

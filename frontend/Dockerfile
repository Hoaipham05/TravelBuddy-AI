# ── Stage 1: Build React app ──────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --prefer-offline
COPY . .
# Production build — API calls sẽ đi qua nginx /api/ prefix
# Vite proxy chỉ dùng cho dev; production dùng nginx
ENV VITE_API_BASE=/api
RUN npm run build
# ── Stage 2: Serve với nginx ──────────────────────────────────────────────────
FROM nginx:alpine
# Copy build output vào nginx html root
COPY --from=builder /app/dist /usr/share/nginx/html
# Nginx config được mount từ docker-compose (nginx.conf)
# Không cần copy ở đây vì sẽ bind mount
EXPOSE 80


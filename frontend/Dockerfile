# syntax=docker/dockerfile:1.7

# ── Stage 1: Build React (Vite) ───────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .
RUN npm run build

# ── Stage 2: Serve with nginx ──────────────────────────────────────────────────
FROM nginx:alpine

# Copy React build output
COPY --from=builder /app/dist /usr/share/nginx/html

# Replace default nginx config with our SPA + API proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]

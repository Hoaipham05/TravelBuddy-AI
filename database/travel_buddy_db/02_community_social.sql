-- ============================================================
-- TravelBuddy AI — Migration 02: Community Social v2
--
-- Bổ sung (idempotent, KHÔNG xoá dữ liệu cũ):
--   • users.google_sub        → đăng nhập bằng Google
--   • community_comments.images → bình luận có thể đính kèm ảnh
--   • saved_items             → "lưu hữu ích" (bài / bình luận / ảnh) vào Wishlist
--   • notifications           → thông báo tương tác (hữu ích / bình luận / lưu)
--
-- Áp dụng cho DB đang chạy:
--   docker compose exec -T postgres \
--     psql -U postgres -d travel_buddy < database/travel_buddy_db/02_community_social.sql
--
-- Fresh install (volume rỗng) tự chạy sau 01_schema.sql theo thứ tự tên file.
-- ============================================================

-- ── Đăng nhập Google ──────────────────────────────────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_google_sub
    ON users(google_sub) WHERE google_sub IS NOT NULL;

-- ── Ảnh đính kèm trong bình luận ────────────────────────────────────────────
ALTER TABLE community_comments ADD COLUMN IF NOT EXISTS images JSONB NOT NULL DEFAULT '[]';

-- ── Mục đã lưu từ cộng đồng (đổ vào Wishlist) ────────────────────────────────
--   kind = 'post'    → lưu cả bài chia sẻ (kèm lịch trình)
--          'comment' → lưu một bình luận hữu ích
--          'photo'   → lưu một tấm ảnh du lịch cụ thể
--   snapshot: dữ liệu hiển thị đã denormalize (tác giả, điểm đến, trích nội dung,
--             ảnh, snapshot lịch trình) để Wishlist render độc lập, không vỡ khi
--             bài/bình luận gốc bị xoá.
CREATE TABLE IF NOT EXISTS saved_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind        VARCHAR(16) NOT NULL CHECK (kind IN ('post', 'comment', 'photo')),
    review_id   UUID REFERENCES reviews(id) ON DELETE CASCADE,
    comment_id  UUID REFERENCES community_comments(id) ON DELETE CASCADE,
    image_url   TEXT,
    note        TEXT,
    snapshot    JSONB NOT NULL DEFAULT '{}',
    dedup_key   TEXT NOT NULL,           -- khoá chống lưu trùng (app sinh)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, dedup_key)
);
CREATE INDEX IF NOT EXISTS idx_saved_items_user ON saved_items(user_id, created_at DESC);

-- ── Thông báo ────────────────────────────────────────────────────────────────
--   kind = 'helpful' | 'comment' | 'reply' | 'save' | 'system'
CREATE TABLE IF NOT EXISTS notifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- người nhận
    actor_id    UUID REFERENCES users(id) ON DELETE SET NULL,           -- người gây ra
    kind        VARCHAR(20) NOT NULL,
    review_id   UUID REFERENCES reviews(id) ON DELETE CASCADE,
    comment_id  UUID REFERENCES community_comments(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    data        JSONB NOT NULL DEFAULT '{}',
    is_read     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notifications_user
    ON notifications(user_id, is_read, created_at DESC);

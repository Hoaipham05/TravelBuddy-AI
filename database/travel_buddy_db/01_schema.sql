-- ============================================================
-- Travel Buddy — Database Schema
-- PostgreSQL 14+
-- Chạy: psql -U postgres -d travel_buddy -f 01_schema.sql
-- ============================================================

-- Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";  -- tìm kiếm không dấu

-- ── 1. USERS ─────────────────────────────────────────────────
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name           VARCHAR(120) NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255),
    avatar_url          TEXT,
    -- Sở thích du lịch (JSON): {"budget_range": [5,15], "hotel_stars": 3, "food": ["seafood"]}
    travel_preferences  JSONB DEFAULT '{}',
    total_points        INT DEFAULT 0,
    level               VARCHAR(30) DEFAULT 'Explorer',   -- Explorer / Adventurer / Nomad
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. DESTINATIONS ──────────────────────────────────────────
CREATE TABLE destinations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(120) NOT NULL,           -- "Đà Nẵng"
    slug            VARCHAR(120) UNIQUE NOT NULL,    -- "da-nang"
    city            VARCHAR(100),
    country         VARCHAR(80) DEFAULT 'Vietnam',
    description     TEXT,
    lat             NUMERIC(9,6),
    lng             NUMERIC(9,6),
    images          JSONB DEFAULT '[]',              -- mảng URL ảnh
    tags            JSONB DEFAULT '[]',              -- ["biển","phố cổ","ẩm thực"]
    best_months     JSONB DEFAULT '[]',              -- [6,7,8]
    avg_rating      NUMERIC(3,2) DEFAULT 0,
    review_count    INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 3. HOTELS ────────────────────────────────────────────────
CREATE TABLE hotels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id  UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    stars           SMALLINT CHECK (stars BETWEEN 1 AND 5),
    price_per_night INT NOT NULL,                    -- VND
    address         TEXT,
    lat             NUMERIC(9,6),
    lng             NUMERIC(9,6),
    amenities       JSONB DEFAULT '[]',              -- ["wifi","pool","breakfast"]
    images          JSONB DEFAULT '[]',
    booking_url     TEXT,                            -- deep link Booking.com / Agoda
    avg_rating      NUMERIC(3,2) DEFAULT 0,
    review_count    INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 4. FLIGHTS ───────────────────────────────────────────────
CREATE TABLE flights (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id  UUID REFERENCES destinations(id),  -- điểm đến
    airline         VARCHAR(80) NOT NULL,            -- "VietJet Air"
    flight_no       VARCHAR(12) NOT NULL,            -- "VJ521"
    origin          CHAR(3) NOT NULL,                -- IATA: "HAN"
    destination     CHAR(3) NOT NULL,                -- "DAD"
    price           INT NOT NULL,                    -- VND
    cabin_class     VARCHAR(20) DEFAULT 'economy',
    depart_at       TIMESTAMPTZ,
    arrive_at       TIMESTAMPTZ,
    -- Giá theo tháng cho tính năng Price Intelligence
    monthly_prices  JSONB DEFAULT '{}',              -- {"2026-06": 980000, "2026-07": 1250000}
    source          VARCHAR(30) DEFAULT 'manual',    -- 'manual' | 'amadeus' | 'crawl'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 5. TRIPS ─────────────────────────────────────────────────
CREATE TABLE trips (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    start_date  DATE,
    end_date    DATE,
    budget      INT,                                -- VND
    status      VARCHAR(20) DEFAULT 'planning',    -- planning / confirmed / completed
    is_public   BOOLEAN DEFAULT FALSE,             -- chia sẻ cộng đồng
    clone_count INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── 6. TRIP_DAYS ─────────────────────────────────────────────
CREATE TABLE trip_days (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id     UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    day_number  SMALLINT NOT NULL,
    date        DATE,
    note        TEXT,
    UNIQUE (trip_id, day_number)
);

-- ── 7. ITINERARY_ITEMS ───────────────────────────────────────
CREATE TABLE itinerary_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    day_id          UUID NOT NULL REFERENCES trip_days(id) ON DELETE CASCADE,
    destination_id  UUID REFERENCES destinations(id),
    hotel_id        UUID REFERENCES hotels(id),
    flight_id       UUID REFERENCES flights(id),
    item_type       VARCHAR(30) NOT NULL,           -- flight/hotel/attraction/restaurant/transport
    title           VARCHAR(200),                  -- tên tùy chỉnh
    note            TEXT,
    start_time      TIME,
    duration_min    INT DEFAULT 60,
    cost            INT DEFAULT 0,                 -- VND
    sort_order      SMALLINT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 8. REVIEWS ───────────────────────────────────────────────
CREATE TABLE reviews (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    destination_id  UUID REFERENCES destinations(id),
    hotel_id        UUID REFERENCES hotels(id),
    rating          NUMERIC(2,1) CHECK (rating BETWEEN 1 AND 5),
    content         TEXT NOT NULL,
    images          JSONB DEFAULT '[]',
    helpful_count   INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_review_target CHECK (
        (destination_id IS NOT NULL) != (hotel_id IS NOT NULL)  -- review 1 trong 2
    )
);

-- ── 9. PRICE_ALERTS ──────────────────────────────────────────
CREATE TABLE price_alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    flight_id       UUID REFERENCES flights(id),
    route           VARCHAR(10),                   -- "HAN-DAD"
    target_price    INT NOT NULL,                  -- VND
    notify_via      VARCHAR(20) DEFAULT 'email',   -- email / zalo / both
    is_active       BOOLEAN DEFAULT TRUE,
    triggered_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 10. TRIP_MEMBERS ─────────────────────────────────────────
CREATE TABLE trip_members (
    trip_id     UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        VARCHAR(20) DEFAULT 'viewer',      -- owner / editor / viewer
    joined_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (trip_id, user_id)
);

-- ── 11. TRIP_EXPENSES ────────────────────────────────────────
CREATE TABLE trip_expenses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id         UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    paid_by         UUID NOT NULL REFERENCES users(id),
    description     VARCHAR(200) NOT NULL,
    amount          INT NOT NULL,                  -- VND
    -- split_with: [{"user_id": "...", "amount": 200000}, ...]
    split_with      JSONB DEFAULT '[]',
    expense_date    DATE DEFAULT CURRENT_DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── INDEXES ──────────────────────────────────────────────────
CREATE INDEX idx_hotels_dest      ON hotels(destination_id);
CREATE INDEX idx_flights_route    ON flights(origin, destination);
CREATE INDEX idx_flights_price    ON flights(price);
CREATE INDEX idx_trips_owner      ON trips(owner_id);
CREATE INDEX idx_trips_public     ON trips(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_reviews_dest     ON reviews(destination_id);
CREATE INDEX idx_reviews_hotel    ON reviews(hotel_id);
CREATE INDEX idx_itinerary_day    ON itinerary_items(day_id, sort_order);
CREATE INDEX idx_price_alerts_usr ON price_alerts(user_id) WHERE is_active = TRUE;

-- Full-text search destinations (tiếng Việt)
CREATE INDEX idx_dest_fts ON destinations
    USING GIN(to_tsvector('simple', unaccent(name || ' ' || COALESCE(city,'') || ' ' || COALESCE(description,''))));

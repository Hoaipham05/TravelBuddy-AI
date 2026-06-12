-- ============================================================
-- TravelBuddy AI - Canonical Data Schema
-- PostgreSQL 14+
--
-- Chay:
--   psql -U postgres -d travel_buddy -f 01_schema.sql
--
-- Kien truc du lieu:
--   - Gia ve/gia phong la snapshot co TTL, khong gan cung vao metadata.
--   - Weather/exchange/hotel/flight realtime deu co cache_key + expires_at.
--   - POI tach rieng khoi destinations de Trip Builder cluster theo toa do.
--   - Hanh trang la rule/template deterministic, khong AI generate runtime.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop theo thu tu phu thuoc de file co the chay lai sach trong dev.
DROP VIEW IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS data_refresh_jobs CASCADE;
DROP TABLE IF EXISTS api_call_logs CASCADE;
DROP TABLE IF EXISTS trip_expenses CASCADE;
DROP TABLE IF EXISTS price_alerts CASCADE;
DROP TABLE IF EXISTS user_packing_items CASCADE;
DROP TABLE IF EXISTS user_packing_lists CASCADE;
DROP TABLE IF EXISTS itinerary_items CASCADE;
DROP TABLE IF EXISTS trip_members CASCADE;
DROP TABLE IF EXISTS trip_days CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS packing_template_items CASCADE;
DROP TABLE IF EXISTS packing_templates CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS country_visa_rules CASCADE;
DROP TABLE IF EXISTS countries CASCADE;
DROP TABLE IF EXISTS exchange_rate_history CASCADE;
DROP TABLE IF EXISTS exchange_rate_cache CASCADE;
DROP TABLE IF EXISTS poi_images CASCADE;
DROP TABLE IF EXISTS pois CASCADE;
DROP TABLE IF EXISTS weather_daily_forecasts CASCADE;
DROP TABLE IF EXISTS weather_cache CASCADE;
DROP TABLE IF EXISTS hotel_offer_cache CASCADE;
DROP TABLE IF EXISTS hotel_rate_snapshots CASCADE;
DROP TABLE IF EXISTS hotel_images CASCADE;
DROP TABLE IF EXISTS hotels CASCADE;
DROP TABLE IF EXISTS flight_offer_cache CASCADE;
DROP TABLE IF EXISTS flight_price_snapshots CASCADE;
DROP TABLE IF EXISTS flight_routes CASCADE;
DROP TABLE IF EXISTS airlines CASCADE;
DROP TABLE IF EXISTS airports CASCADE;
DROP TABLE IF EXISTS destination_images CASCADE;
DROP TABLE IF EXISTS destinations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- 1. USERS
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    avatar_url TEXT,
    travel_preferences JSONB NOT NULL DEFAULT '{}',
    total_points INT NOT NULL DEFAULT 0,
    level VARCHAR(30) NOT NULL DEFAULT 'Explorer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. DESTINATIONS + IMAGES
-- ============================================================

CREATE TABLE destinations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(160) NOT NULL,
    slug VARCHAR(160) UNIQUE NOT NULL,
    city VARCHAR(120),
    province VARCHAR(120),
    country_code CHAR(2) NOT NULL DEFAULT 'VN',
    country_name VARCHAR(120) NOT NULL DEFAULT 'Vietnam',
    iata_city_code CHAR(3),
    description TEXT,
    lat NUMERIC(9,6),
    lng NUMERIC(9,6),
    timezone VARCHAR(80) NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',
    tags JSONB NOT NULL DEFAULT '[]',
    best_months JSONB NOT NULL DEFAULT '[]',
    avg_rating NUMERIC(3,2) NOT NULL DEFAULT 0,
    review_count INT NOT NULL DEFAULT 0,
    is_seeded BOOLEAN NOT NULL DEFAULT FALSE,
    popularity_rank INT,
    source VARCHAR(40) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE destination_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    provider VARCHAR(40) NOT NULL,             -- wikimedia, unsplash, manual
    provider_ref TEXT,
    author_name VARCHAR(160),
    author_url TEXT,
    license VARCHAR(120),
    attribution TEXT,
    width INT,
    height INT,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. AIRPORTS, AIRLINES, FLIGHT ROUTES, PRICE SNAPSHOTS
-- ============================================================

CREATE TABLE airports (
    iata_code CHAR(3) PRIMARY KEY,
    name VARCHAR(180) NOT NULL,
    city VARCHAR(120),
    country_code CHAR(2) NOT NULL,
    lat NUMERIC(9,6),
    lng NUMERIC(9,6),
    timezone VARCHAR(80),
    is_domestic_vn BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE airlines (
    iata_code CHAR(2) PRIMARY KEY,
    name VARCHAR(140) NOT NULL,
    country_code CHAR(2),
    booking_base_url TEXT,
    logo_url TEXT,
    is_seed_target BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE flight_routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_iata CHAR(3) NOT NULL REFERENCES airports(iata_code),
    destination_iata CHAR(3) NOT NULL REFERENCES airports(iata_code),
    route_key VARCHAR(7) UNIQUE NOT NULL,
    destination_id UUID REFERENCES destinations(id),
    is_domestic BOOLEAN NOT NULL DEFAULT TRUE,
    is_popular_seed BOOLEAN NOT NULL DEFAULT FALSE,
    popularity_rank INT,
    search_volume_30d INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (origin_iata, destination_iata)
);

CREATE TABLE flight_price_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID NOT NULL REFERENCES flight_routes(id) ON DELETE CASCADE,
    airline_iata CHAR(2) REFERENCES airlines(iata_code),
    airline_name VARCHAR(140) NOT NULL,
    flight_number VARCHAR(20),
    cabin_class VARCHAR(30) NOT NULL DEFAULT 'economy',
    departure_date DATE NOT NULL,
    depart_at TIMESTAMPTZ,
    arrive_at TIMESTAMPTZ,
    duration_minutes INT,
    stops SMALLINT NOT NULL DEFAULT 0,
    price_amount NUMERIC(14,2) NOT NULL CHECK (price_amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'VND',
    seats_left INT,
    booking_url TEXT,
    source VARCHAR(40) NOT NULL,
    source_ref TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    raw JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE flight_offer_cache (
    cache_key VARCHAR(220) PRIMARY KEY,
    route_id UUID REFERENCES flight_routes(id) ON DELETE SET NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'amadeus',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Compatibility view cho mot so code/doc cu chi doc bang flights.
CREATE VIEW flights AS
SELECT
    fps.id,
    fr.destination_id,
    fps.airline_name AS airline,
    fps.flight_number AS flight_no,
    fr.origin_iata AS origin,
    fr.destination_iata AS destination,
    fps.price_amount::INT AS price,
    fps.cabin_class,
    fps.depart_at,
    fps.arrive_at,
    '{}'::JSONB AS monthly_prices,
    fps.source,
    fps.fetched_at AS created_at
FROM flight_price_snapshots fps
JOIN flight_routes fr ON fr.id = fps.route_id;

-- ============================================================
-- 4. HOTELS, HOTEL IMAGES, RATE SNAPSHOTS
-- ============================================================

CREATE TABLE hotels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id UUID NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    name VARCHAR(220) NOT NULL,
    slug VARCHAR(240) NOT NULL,
    stars NUMERIC(2,1) CHECK (stars IS NULL OR (stars >= 0 AND stars <= 5)),
    property_type VARCHAR(60) NOT NULL DEFAULT 'hotel',
    description TEXT,
    address TEXT,
    area VARCHAR(120),
    lat NUMERIC(9,6),
    lng NUMERIC(9,6),
    amenities JSONB NOT NULL DEFAULT '[]',
    checkin_time TIME,
    checkout_time TIME,
    avg_rating NUMERIC(3,2) NOT NULL DEFAULT 0,
    review_count INT NOT NULL DEFAULT 0,
    provider VARCHAR(40),                       -- agoda, booking, manual
    provider_property_id TEXT,
    deep_link_url TEXT,
    is_seeded BOOLEAN NOT NULL DEFAULT FALSE,
    source VARCHAR(40) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (destination_id, slug)
);

CREATE UNIQUE INDEX idx_hotels_provider_property
    ON hotels(provider, provider_property_id)
    WHERE provider IS NOT NULL AND provider_property_id IS NOT NULL;

CREATE TABLE hotel_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    provider VARCHAR(40) NOT NULL,
    provider_ref TEXT,
    license VARCHAR(120),
    attribution TEXT,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE hotel_rate_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    adults SMALLINT NOT NULL DEFAULT 2,
    rooms SMALLINT NOT NULL DEFAULT 1,
    room_name VARCHAR(180),
    refundable BOOLEAN,
    breakfast_included BOOLEAN,
    price_amount NUMERIC(14,2) NOT NULL CHECK (price_amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'VND',
    taxes_and_fees NUMERIC(14,2),
    provider VARCHAR(40) NOT NULL,
    provider_rate_id TEXT,
    deep_link_url TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    raw JSONB NOT NULL DEFAULT '{}',
    CHECK (checkout_date > checkin_date)
);

CREATE TABLE hotel_offer_cache (
    cache_key VARCHAR(260) PRIMARY KEY,
    destination_id UUID REFERENCES destinations(id) ON DELETE SET NULL,
    request JSONB NOT NULL,
    response JSONB NOT NULL,
    provider VARCHAR(40) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- ============================================================
-- 5. WEATHER CACHE
-- ============================================================

CREATE TABLE weather_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id UUID REFERENCES destinations(id) ON DELETE CASCADE,
    cache_key VARCHAR(220) UNIQUE NOT NULL,
    lat NUMERIC(9,6) NOT NULL,
    lng NUMERIC(9,6) NOT NULL,
    timezone VARCHAR(80) NOT NULL,
    forecast_days SMALLINT NOT NULL DEFAULT 16,
    source VARCHAR(40) NOT NULL DEFAULT 'open-meteo',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    raw JSONB NOT NULL
);

CREATE TABLE weather_daily_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    weather_cache_id UUID NOT NULL REFERENCES weather_cache(id) ON DELETE CASCADE,
    destination_id UUID REFERENCES destinations(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    weather_code INT,
    temp_max_c NUMERIC(5,2),
    temp_min_c NUMERIC(5,2),
    precipitation_sum_mm NUMERIC(6,2),
    precipitation_probability_max INT,
    wind_speed_max_kmh NUMERIC(6,2),
    travel_score SMALLINT CHECK (travel_score IS NULL OR (travel_score BETWEEN 0 AND 100)),
    UNIQUE (weather_cache_id, forecast_date)
);

-- ============================================================
-- 6. POI + POI IMAGES
-- ============================================================

CREATE TABLE pois (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    destination_id UUID REFERENCES destinations(id) ON DELETE SET NULL,
    name VARCHAR(220) NOT NULL,
    slug VARCHAR(260) NOT NULL,
    category VARCHAR(80),
    kinds JSONB NOT NULL DEFAULT '[]',
    description TEXT,
    lat NUMERIC(9,6),
    lng NUMERIC(9,6),
    address TEXT,
    estimated_duration_min INT,
    entrance_fee_amount NUMERIC(14,2),
    currency CHAR(3) DEFAULT 'VND',
    avg_rating NUMERIC(3,2) NOT NULL DEFAULT 0,
    source VARCHAR(40) NOT NULL DEFAULT 'opentripmap',
    source_ref TEXT,
    wikidata_id TEXT,
    wikipedia_url TEXT,
    is_seeded BOOLEAN NOT NULL DEFAULT FALSE,
    fetched_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw JSONB NOT NULL DEFAULT '{}',
    UNIQUE (destination_id, slug)
);

CREATE UNIQUE INDEX idx_pois_source_ref
    ON pois(source, source_ref)
    WHERE source_ref IS NOT NULL;

CREATE TABLE poi_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    poi_id UUID NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    provider VARCHAR(40) NOT NULL,
    provider_ref TEXT,
    license VARCHAR(120),
    attribution TEXT,
    sort_order SMALLINT NOT NULL DEFAULT 0
);

-- ============================================================
-- 7. EXCHANGE RATES + COUNTRIES/VISA
-- ============================================================

CREATE TABLE exchange_rate_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    base_currency CHAR(3) NOT NULL,
    target_currency CHAR(3) NOT NULL,
    rate NUMERIC(18,6) NOT NULL CHECK (rate > 0),
    rate_date DATE NOT NULL,
    source VARCHAR(40) NOT NULL DEFAULT 'frankfurter',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    raw JSONB NOT NULL DEFAULT '{}',
    UNIQUE (base_currency, target_currency, rate_date)
);

CREATE TABLE exchange_rate_history (
    rate_date DATE NOT NULL,
    base_currency CHAR(3) NOT NULL,
    target_currency CHAR(3) NOT NULL,
    rate NUMERIC(18,6) NOT NULL CHECK (rate > 0),
    source VARCHAR(40) NOT NULL DEFAULT 'frankfurter',
    PRIMARY KEY (rate_date, base_currency, target_currency)
);

CREATE TABLE countries (
    code CHAR(2) PRIMARY KEY,
    alpha3 CHAR(3),
    name_en VARCHAR(120) NOT NULL,
    name_vn VARCHAR(120),
    capital VARCHAR(120),
    region VARCHAR(80),
    subregion VARCHAR(120),
    population BIGINT,
    area_km2 NUMERIC(14,2),
    currencies JSONB NOT NULL DEFAULT '[]',
    languages JSONB NOT NULL DEFAULT '[]',
    timezones JSONB NOT NULL DEFAULT '[]',
    flag_url TEXT,
    flag_svg TEXT,
    calling_code VARCHAR(12),
    source VARCHAR(40) NOT NULL DEFAULT 'restcountries',
    fetched_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE country_visa_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passport_country_code CHAR(2) NOT NULL DEFAULT 'VN',
    destination_country_code CHAR(2) NOT NULL REFERENCES countries(code),
    visa_required BOOLEAN NOT NULL,
    visa_type VARCHAR(80),
    max_stay_days INT,
    note TEXT,
    source_url TEXT,
    verified_at DATE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (passport_country_code, destination_country_code)
);

-- ============================================================
-- 8. PACKING TEMPLATES + USER PACKING LISTS
-- ============================================================

CREATE TABLE packing_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(160) NOT NULL,
    trip_type VARCHAR(60) NOT NULL,
    season VARCHAR(40) NOT NULL,
    day_min SMALLINT NOT NULL,
    day_max SMALLINT,
    activities JSONB NOT NULL DEFAULT '[]',
    traveler_tags JSONB NOT NULL DEFAULT '[]',
    priority SMALLINT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE packing_template_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES packing_templates(id) ON DELETE CASCADE,
    category VARCHAR(60) NOT NULL CHECK (category IN ('clothing', 'accessories', 'health', 'documents', 'electronics')),
    item_name VARCHAR(160) NOT NULL,
    quantity_rule VARCHAR(120),
    note TEXT,
    is_default_checked BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order SMALLINT NOT NULL DEFAULT 0
);

-- ============================================================
-- 9. TRIPS, ITINERARY, COMMUNITY, EXPENSES
-- ============================================================

CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_id UUID REFERENCES destinations(id),
    title VARCHAR(220) NOT NULL,
    start_date DATE,
    end_date DATE,
    budget_amount NUMERIC(14,2),
    currency CHAR(3) NOT NULL DEFAULT 'VND',
    status VARCHAR(30) NOT NULL DEFAULT 'planning',
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    clone_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE trip_days (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    day_number SMALLINT NOT NULL,
    date DATE,
    note TEXT,
    UNIQUE (trip_id, day_number)
);

CREATE TABLE itinerary_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    day_id UUID NOT NULL REFERENCES trip_days(id) ON DELETE CASCADE,
    item_type VARCHAR(40) NOT NULL,
    title VARCHAR(220) NOT NULL,
    destination_id UUID REFERENCES destinations(id),
    poi_id UUID REFERENCES pois(id),
    hotel_id UUID REFERENCES hotels(id),
    flight_snapshot_id UUID REFERENCES flight_price_snapshots(id),
    start_time TIME,
    duration_min INT NOT NULL DEFAULT 60,
    cost_amount NUMERIC(14,2) DEFAULT 0,
    currency CHAR(3) DEFAULT 'VND',
    lat NUMERIC(9,6),
    lng NUMERIC(9,6),
    note TEXT,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE trip_members (
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('owner', 'editor', 'viewer')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (trip_id, user_id)
);

CREATE TABLE user_packing_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES packing_templates(id),
    title VARCHAR(180) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_packing_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    packing_list_id UUID NOT NULL REFERENCES user_packing_lists(id) ON DELETE CASCADE,
    category VARCHAR(60) NOT NULL CHECK (category IN ('clothing', 'accessories', 'health', 'documents', 'electronics')),
    item_name VARCHAR(160) NOT NULL,
    quantity VARCHAR(80),
    is_checked BOOLEAN NOT NULL DEFAULT FALSE,
    is_custom BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_id UUID REFERENCES destinations(id) ON DELETE CASCADE,
    hotel_id UUID REFERENCES hotels(id) ON DELETE CASCADE,
    poi_id UUID REFERENCES pois(id) ON DELETE CASCADE,
    rating NUMERIC(2,1) CHECK (rating BETWEEN 1 AND 5),
    content TEXT NOT NULL,
    images JSONB NOT NULL DEFAULT '[]',
    helpful_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_review_single_target CHECK (
        ((destination_id IS NOT NULL)::INT + (hotel_id IS NOT NULL)::INT + (poi_id IS NOT NULL)::INT) = 1
    )
);

CREATE TABLE price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(30) NOT NULL CHECK (alert_type IN ('flight', 'hotel')),
    route_id UUID REFERENCES flight_routes(id) ON DELETE CASCADE,
    hotel_id UUID REFERENCES hotels(id) ON DELETE CASCADE,
    target_price_amount NUMERIC(14,2) NOT NULL CHECK (target_price_amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'VND',
    travel_date DATE,
    notify_via VARCHAR(30) NOT NULL DEFAULT 'email',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_alert_single_target CHECK (
        (alert_type = 'flight' AND route_id IS NOT NULL AND hotel_id IS NULL)
        OR
        (alert_type = 'hotel' AND hotel_id IS NOT NULL AND route_id IS NULL)
    )
);

CREATE TABLE trip_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    paid_by UUID NOT NULL REFERENCES users(id),
    description VARCHAR(220) NOT NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'VND',
    split_with JSONB NOT NULL DEFAULT '[]',
    expense_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 10. OPS LOGS
-- ============================================================

CREATE TABLE api_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(40) NOT NULL,
    endpoint TEXT NOT NULL,
    request_hash VARCHAR(80),
    status_code INT,
    latency_ms INT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE data_refresh_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(120) NOT NULL,
    provider VARCHAR(40),
    entity_type VARCHAR(60) NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN ('running', 'success', 'failed', 'skipped')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    records_fetched INT NOT NULL DEFAULT 0,
    records_upserted INT NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_destinations_country ON destinations(country_code);
CREATE INDEX idx_destinations_popular ON destinations(popularity_rank) WHERE popularity_rank IS NOT NULL;
CREATE INDEX idx_destination_images_dest ON destination_images(destination_id, sort_order);

CREATE INDEX idx_flight_routes_pair ON flight_routes(origin_iata, destination_iata);
CREATE INDEX idx_flight_routes_seed ON flight_routes(is_popular_seed, popularity_rank);
CREATE INDEX idx_flight_price_lookup ON flight_price_snapshots(route_id, departure_date, cabin_class, expires_at);
CREATE INDEX idx_flight_price_cheapest ON flight_price_snapshots(route_id, departure_date, price_amount);
CREATE INDEX idx_flight_offer_expiry ON flight_offer_cache(expires_at);

CREATE INDEX idx_hotels_destination ON hotels(destination_id);
CREATE INDEX idx_hotels_rating ON hotels(destination_id, avg_rating DESC);
CREATE INDEX idx_hotel_rates_lookup ON hotel_rate_snapshots(hotel_id, checkin_date, checkout_date, adults, expires_at);
CREATE INDEX idx_hotel_offer_expiry ON hotel_offer_cache(expires_at);

CREATE INDEX idx_weather_expiry ON weather_cache(expires_at);
CREATE INDEX idx_weather_daily_dest_date ON weather_daily_forecasts(destination_id, forecast_date);

CREATE INDEX idx_pois_destination ON pois(destination_id);
CREATE INDEX idx_pois_category ON pois(destination_id, category);
CREATE INDEX idx_pois_geo ON pois(destination_id, lat, lng);

CREATE INDEX idx_exchange_expiry ON exchange_rate_cache(expires_at);
CREATE INDEX idx_countries_region ON countries(region);

CREATE INDEX idx_packing_template_match ON packing_templates(trip_type, season, day_min, day_max, is_active);

CREATE INDEX idx_trips_owner ON trips(owner_id);
CREATE INDEX idx_trips_public ON trips(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_trip_days_trip ON trip_days(trip_id, day_number);
CREATE INDEX idx_itinerary_day ON itinerary_items(day_id, sort_order);
CREATE INDEX idx_reviews_destination ON reviews(destination_id);
CREATE INDEX idx_reviews_hotel ON reviews(hotel_id);
CREATE INDEX idx_price_alerts_active ON price_alerts(user_id) WHERE is_active = TRUE;

CREATE INDEX idx_destinations_fts ON destinations
    USING GIN(to_tsvector('simple', name || ' ' || COALESCE(city,'') || ' ' || COALESCE(description,'')));

CREATE INDEX idx_hotels_name_trgm ON hotels USING GIN(name gin_trgm_ops);
CREATE INDEX idx_pois_name_trgm ON pois USING GIN(name gin_trgm_ops);

-- ============================================================
-- DONE
-- ============================================================

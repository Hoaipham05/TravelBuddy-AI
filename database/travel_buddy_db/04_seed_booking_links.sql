-- ============================================================
-- TravelBuddy AI - Booking Links Seed/Backfill
-- Run after 01_schema.sql and 02_seed_data.sql.
--
-- Mục tiêu:
--   - Chuẩn hóa link đặt vé chính thức của hãng bay.
--   - Backfill `booking_url` cho flight snapshots nếu provider không trả
--     deep link cụ thể.
--   - Giữ nguyên hotel deep link do provider trả về.
--
-- Lưu ý:
--   - Link flight fallback là trang đặt vé/trang chính thức của hãng,
--     không phải deep link đã prefill tuyến/ngày.
--   - Nếu sau này provider trả deep link cụ thể hơn thì collector sẽ lưu
--     link đó và không cần dùng fallback.
-- ============================================================

UPDATE airlines
SET booking_base_url = CASE iata_code
    WHEN 'VN' THEN 'https://www.vietnamairlines.com/vn/vi/home'
    WHEN 'VJ' THEN 'https://www.vietjetair.com/vi'
    WHEN 'QH' THEN 'https://www.bambooairways.com/vn/vi'
    ELSE booking_base_url
END
WHERE iata_code IN ('VN', 'VJ', 'QH');

UPDATE flight_price_snapshots fps
SET booking_url = a.booking_base_url
FROM airlines a
WHERE fps.airline_iata = a.iata_code
  AND (fps.booking_url IS NULL OR fps.booking_url = '')
  AND a.booking_base_url IS NOT NULL
  AND a.booking_base_url <> '';

-- Backfill an toàn cho hotel metadata nếu sau này có row nào thiếu link.
-- Với hotel từ SerpApi, deep link cụ thể đã nằm ở `hotel_rate_snapshots`.
UPDATE hotels h
SET deep_link_url = CASE
    WHEN h.deep_link_url IS NOT NULL AND h.deep_link_url <> '' THEN h.deep_link_url
    WHEN h.provider = 'serpapi_google_hotels' THEN 'https://www.google.com/travel/hotels'
    ELSE 'https://www.agoda.com'
END
WHERE h.deep_link_url IS NULL OR h.deep_link_url = '';

SELECT
    'airlines_with_booking_base_url' AS metric,
    COUNT(*) AS value
FROM airlines
WHERE booking_base_url IS NOT NULL AND booking_base_url <> ''
UNION ALL
SELECT
    'flight_snapshots_with_booking_url',
    COUNT(*)
FROM flight_price_snapshots
WHERE booking_url IS NOT NULL AND booking_url <> ''
UNION ALL
SELECT
    'hotels_with_deep_link',
    COUNT(*)
FROM hotels
WHERE deep_link_url IS NOT NULL AND deep_link_url <> ''
UNION ALL
SELECT
    'hotel_rates_with_deep_link',
    COUNT(*)
FROM hotel_rate_snapshots
WHERE deep_link_url IS NOT NULL AND deep_link_url <> '';

-- ============================================================
-- Travel Buddy — Seed Data (Data thực tế)
-- Chạy SAU 01_schema.sql
-- psql -U postgres -d travel_buddy -f 02_seed_data.sql
-- ============================================================

-- ── DESTINATIONS (10 điểm đến thực tế Việt Nam + quốc tế) ──

INSERT INTO destinations (name, slug, city, country, description, lat, lng, tags, best_months, avg_rating) VALUES

('Đà Nẵng',    'da-nang',   'Đà Nẵng', 'Vietnam',
 'Thành phố biển sầm uất miền Trung, nổi tiếng với bãi biển Mỹ Khê, Bà Nà Hills và cầu Rồng phun lửa.',
 16.0544, 108.2022, '["biển","thành phố","ẩm thực","resort"]', '[5,6,7,8,9]', 4.6),

('Hội An',     'hoi-an',    'Hội An',  'Vietnam',
 'Phố cổ di sản UNESCO với đèn lồng rực rỡ, ẩm thực độc đáo và kiến trúc giao thoa văn hóa.',
 15.8801, 108.3380, '["phố cổ","di sản","ẩm thực","lịch sử"]', '[1,2,3,10,11,12]', 4.8),

('Hạ Long',    'ha-long',   'Quảng Ninh','Vietnam',
 'Vịnh Hạ Long – Di sản thiên nhiên thế giới với hơn 1.600 hòn đảo đá vôi hùng vĩ.',
 20.9101, 107.1839, '["biển","thuyền","thiên nhiên","di sản"]', '[3,4,5,10,11]', 4.7),

('Đà Lạt',     'da-lat',    'Lâm Đồng','Vietnam',
 'Thành phố mộng mơ với khí hậu mát mẻ quanh năm, đồi thông, vườn hoa và thác nước.',
 11.9404, 108.4583, '["núi","hoa","cà phê","nghỉ dưỡng","lãng mạn"]', '[1,2,3,11,12]', 4.5),

('Phú Quốc',   'phu-quoc',  'Kiên Giang','Vietnam',
 'Đảo Ngọc với bãi biển nước trong vắt, san hô đẹp và resort đẳng cấp quốc tế.',
 10.2897, 103.9840, '["đảo","biển","lặn biển","resort","hoàng hôn"]', '[11,12,1,2,3,4]', 4.7),

('Sapa',       'sapa',      'Lào Cai',  'Vietnam',
 'Thị trấn vùng cao với ruộng bậc thang kỳ vĩ, bản làng người H''Mông và đỉnh Fansipan.',
 22.3364, 103.8438, '["núi","trekking","văn hóa dân tộc","ruộng bậc thang"]', '[3,4,5,9,10]', 4.6),

('Nha Trang',  'nha-trang', 'Khánh Hòa','Vietnam',
 'Thành phố biển xanh với đảo Hòn Mun lặn ngắm san hô, Vinpearl Land và hải sản tươi ngon.',
 12.2388, 109.1967, '["biển","đảo","hải sản","resort","lặn biển"]', '[1,2,3,7,8]', 4.4),

('Bangkok',    'bangkok',   'Bangkok',  'Thailand',
 'Thủ đô năng động với chùa Phật Ngọc, đường phố ẩm thực sôi động và trung tâm mua sắm hiện đại.',
 13.7563, 100.5018, '["thành phố","chùa","ẩm thực","mua sắm","đêm"]', '[11,12,1,2]', 4.5),

('Tokyo',      'tokyo',     'Tokyo',    'Japan',
 'Siêu đô thị kết hợp hoàn hảo giữa truyền thống và hiện đại – đền Senso-ji, Shibuya, ẩm thực Michelin.',
 35.6762, 139.6503, '["thành phố","công nghệ","ẩm thực","anime","mùa hoa anh đào"]', '[3,4,10,11]', 4.9),

('Singapore',  'singapore', 'Singapore','Singapore',
 'Quốc đảo sạch đẹp với Gardens by the Bay, Marina Bay Sands và thiên đường ẩm thực đường phố.',
 1.3521, 103.8198, '["thành phố","ẩm thực","hiện đại","mua sắm","gia đình"]', '[2,3,7,8]', 4.7);


-- ── HOTELS (3 khách sạn / điểm đến, dữ liệu thực) ───────────

-- Đà Nẵng
WITH d AS (SELECT id FROM destinations WHERE slug='da-nang')
INSERT INTO hotels (destination_id, name, stars, price_per_night, address, lat, lng, amenities, avg_rating) VALUES
((SELECT id FROM d), 'Furama Resort Danang',         5, 3500000, '68 Hồ Xuân Hương, Bắc Mỹ An, Đà Nẵng',
 16.0333, 108.2464, '["pool","spa","beach","restaurant","gym","wifi","kids_club"]', 4.7),
((SELECT id FROM d), 'Haian Beach Hotel & Spa',      4, 900000,  '28 Võ Nguyên Giáp, Sơn Trà, Đà Nẵng',
 16.0613, 108.2494, '["pool","beach","breakfast","wifi","restaurant"]', 4.3),
((SELECT id FROM d), 'Brilliant Hotel Danang',       3, 500000,  '162 Bach Dang, Hai Chau, Đà Nẵng',
 16.0624, 108.2234, '["wifi","breakfast","city_view","restaurant"]', 4.1);

-- Hội An
WITH d AS (SELECT id FROM destinations WHERE slug='hoi-an')
INSERT INTO hotels (destination_id, name, stars, price_per_night, address, lat, lng, amenities, avg_rating) VALUES
((SELECT id FROM d), 'Anantara Hoi An Resort',       5, 4200000, '1 Pham Hong Thai, Hoi An',
 15.8817, 108.3342, '["pool","spa","river_view","restaurant","wifi","bicycle"]', 4.9),
((SELECT id FROM d), 'Hoi An Silk Village Resort',   4, 1200000, 'Thanh Ha Village, Hoi An',
 15.8833, 108.3069, '["pool","spa","traditional","breakfast","wifi"]', 4.5),
((SELECT id FROM d), 'Hoi An Backpackers Hostel',    2, 180000,  '19 Phan Dinh Phung, Hoi An',
 15.8792, 108.3349, '["wifi","bar","breakfast","social_area"]', 4.0);

-- Đà Lạt
WITH d AS (SELECT id FROM destinations WHERE slug='da-lat')
INSERT INTO hotels (destination_id, name, stars, price_per_night, address, lat, lng, amenities, avg_rating) VALUES
((SELECT id FROM d), 'Dalat Palace Heritage Hotel',  5, 3800000, '2 Tran Phu, Da Lat',
 11.9388, 108.4380, '["heritage","lake_view","restaurant","spa","wifi","garden"]', 4.8),
((SELECT id FROM d), 'TTC Hotel Premium Ngoc Lan',   4, 1100000, '42 Nguyen Chi Thanh, Da Lat',
 11.9400, 108.4419, '["mountain_view","breakfast","wifi","restaurant","fireplace"]', 4.2),
((SELECT id FROM d), 'Terracotta Hotel & Resort',    4, 1800000, '2/2 Phu Dong Thien Vuong, Da Lat',
 11.9444, 108.4333, '["pool","resort","garden","wifi","breakfast","coffee"]', 4.4);

-- Bangkok
WITH d AS (SELECT id FROM destinations WHERE slug='bangkok')
INSERT INTO hotels (destination_id, name, stars, price_per_night, address, lat, lng, amenities, avg_rating) VALUES
((SELECT id FROM d), 'Mandarin Oriental Bangkok',    5, 12000000,'48 Oriental Ave, Bangkok',
 13.7243, 100.5126, '["riverside","spa","pool","heritage","restaurant","butler"]', 4.9),
((SELECT id FROM d), 'Chatrium Hotel Riverside',     4, 2800000, '28 Charoenkrung 70, Bangkok',
 13.7101, 100.5185, '["riverside","pool","gym","restaurant","wifi"]', 4.4),
((SELECT id FROM d), 'Lub d Bangkok Silom',          2, 450000,  '4 Decho Road, Silom, Bangkok',
 13.7249, 100.5220, '["wifi","social","rooftop_bar","hostel","central"]', 4.1);


-- ── FLIGHTS (data tham khảo thực tế tháng 6/2026) ───────────

WITH da_nang  AS (SELECT id FROM destinations WHERE slug='da-nang'),
     hoi_an   AS (SELECT id FROM destinations WHERE slug='hoi-an'),
     ha_long  AS (SELECT id FROM destinations WHERE slug='ha-long'),
     phu_quoc AS (SELECT id FROM destinations WHERE slug='phu-quoc'),
     bangkok  AS (SELECT id FROM destinations WHERE slug='bangkok'),
     tokyo    AS (SELECT id FROM destinations WHERE slug='tokyo')

INSERT INTO flights (destination_id, airline, flight_no, origin, destination, price, cabin_class, depart_at, arrive_at, monthly_prices, source) VALUES

-- HAN → DAD (Đà Nẵng)
((SELECT id FROM da_nang), 'VietJet Air','VJ521','HAN','DAD', 980000, 'economy',
 '2026-06-17 06:30', '2026-06-17 07:50',
 '{"2026-06": 980000, "2026-07": 1250000, "2026-08": 1380000}', 'crawl'),

((SELECT id FROM da_nang), 'Vietnam Airlines','VN161','HAN','DAD', 1450000, 'economy',
 '2026-06-17 07:00', '2026-06-17 08:20',
 '{"2026-06": 1450000, "2026-07": 1650000, "2026-08": 1720000}', 'crawl'),

((SELECT id FROM da_nang), 'Bamboo Airways','QH901','HAN','DAD', 1100000, 'economy',
 '2026-06-17 11:00', '2026-06-17 12:25',
 '{"2026-06": 1100000, "2026-07": 1300000}', 'crawl'),

-- HAN → SGN (TP.HCM – transit hub cho Phú Quốc)
((SELECT id FROM phu_quoc), 'VietJet Air','VJ130','HAN','SGN', 1200000, 'economy',
 '2026-06-14 06:00', '2026-06-14 07:55',
 '{"2026-06": 1200000, "2026-07": 1450000}', 'crawl'),

-- SGN → PQC (Phú Quốc)
((SELECT id FROM phu_quoc), 'VietJet Air','VJ836','SGN','PQC', 650000, 'economy',
 '2026-06-14 10:00', '2026-06-14 11:05',
 '{"2026-06": 650000, "2026-07": 890000}', 'crawl'),

-- HAN → BKK (Bangkok)
((SELECT id FROM bangkok), 'VietJet Air','VJ890','HAN','BKK', 1850000, 'economy',
 '2026-06-20 08:00', '2026-06-20 10:30',
 '{"2026-06": 1850000, "2026-07": 2100000, "2026-08": 2350000}', 'crawl'),

((SELECT id FROM bangkok), 'Bangkok Airways','PG961','HAN','BKK', 2800000, 'economy',
 '2026-06-20 10:30', '2026-06-20 13:00',
 '{"2026-06": 2800000, "2026-07": 3100000}', 'crawl'),

-- HAN → NRT (Tokyo Narita)
((SELECT id FROM tokyo), 'Vietnam Airlines','VN392','HAN','NRT', 7200000, 'economy',
 '2026-06-15 00:30', '2026-06-15 08:30',
 '{"2026-06": 7200000, "2026-07": 8500000}', 'crawl');


-- ── SAMPLE USERS ─────────────────────────────────────────────

INSERT INTO users (full_name, email, travel_preferences, total_points, level) VALUES
('Nguyễn Lan', 'nguyen.lan@gmail.com',
 '{"budget_range": [8, 15], "hotel_stars": 3, "food": ["seafood","street_food"], "trip_type": ["couple","family"]}',
 2450, 'Explorer'),
('Trần Huy',   'tran.huy@gmail.com',
 '{"budget_range": [5, 10], "hotel_stars": 2, "food": ["street_food"], "trip_type": ["backpacker","solo"]}',
 980, 'Explorer'),
('Minh Khoa',  'minhkhoa.bk@gmail.com',
 '{"budget_range": [15, 30], "hotel_stars": 4, "food": ["fine_dining","local"], "trip_type": ["couple"]}',
 5600, 'Adventurer');


-- ── SAMPLE TRIP (Đà Nẵng – Hội An 5N4Đ) ─────────────────────

WITH u AS (SELECT id FROM users WHERE email='nguyen.lan@gmail.com'),
     trip_ins AS (
       INSERT INTO trips (owner_id, title, start_date, end_date, budget, status, is_public)
       VALUES ((SELECT id FROM u), 'Đà Nẵng – Hội An 5N4Đ tháng 6',
               '2026-06-14', '2026-06-18', 10000000, 'confirmed', TRUE)
       RETURNING id
     ),
     day1 AS (INSERT INTO trip_days (trip_id, day_number, date) VALUES ((SELECT id FROM trip_ins), 1, '2026-06-14') RETURNING id),
     day2 AS (INSERT INTO trip_days (trip_id, day_number, date) VALUES ((SELECT id FROM trip_ins), 2, '2026-06-15') RETURNING id),
     day3 AS (INSERT INTO trip_days (trip_id, day_number, date) VALUES ((SELECT id FROM trip_ins), 3, '2026-06-16') RETURNING id)

INSERT INTO itinerary_items (day_id, destination_id, item_type, title, start_time, cost, sort_order)
SELECT day1.id, d.id, 'attraction', 'Bãi biển Mỹ Khê – buổi sáng', '06:00', 0, 1
FROM day1, destinations d WHERE d.slug='da-nang'
UNION ALL
SELECT day1.id, d.id, 'attraction', 'Bà Nà Hills – Cầu Vàng', '14:00', 750000, 2
FROM day1, destinations d WHERE d.slug='da-nang'
UNION ALL
SELECT day2.id, d.id, 'attraction', 'Ngũ Hành Sơn', '09:00', 40000, 1
FROM day2, destinations d WHERE d.slug='da-nang'
UNION ALL
SELECT day3.id, d.id, 'attraction', 'Phố cổ Hội An – đèn lồng', '19:00', 120000, 1
FROM day3, destinations d WHERE d.slug='hoi-an';


-- ── SAMPLE REVIEWS ───────────────────────────────────────────

WITH u1 AS (SELECT id FROM users WHERE email='nguyen.lan@gmail.com'),
     u2 AS (SELECT id FROM users WHERE email='tran.huy@gmail.com')

INSERT INTO reviews (user_id, destination_id, rating, content, helpful_count) VALUES
((SELECT id FROM u1), (SELECT id FROM destinations WHERE slug='da-nang'),
 4.5, 'Đà Nẵng mùa hè đẹp lắm! Biển Mỹ Khê sóng nhỏ, nước trong. Bà Nà Hills nên đặt vé online để tránh xếp hàng. Ăn hải sản bờ biển ngon mà giá bình dân hơn trong phố nhiều.', 47),
((SELECT id FROM u2), (SELECT id FROM destinations WHERE slug='hoi-an'),
 5.0, 'Hội An đẹp không tưởng vào buổi tối. Ra phố cổ lúc 7-8h tối, đèn lồng lung linh, thả đèn hoa đăng xuống sông Thu Bồn. Cao lầu ở đây ngon hơn bất kỳ nơi nào khác vì dùng nước giếng Bá Lễ.', 103);


-- Xác nhận
SELECT 'destinations' AS tbl, COUNT(*) FROM destinations
UNION ALL SELECT 'hotels', COUNT(*) FROM hotels
UNION ALL SELECT 'flights', COUNT(*) FROM flights
UNION ALL SELECT 'users',   COUNT(*) FROM users
UNION ALL SELECT 'trips',   COUNT(*) FROM trips
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews;

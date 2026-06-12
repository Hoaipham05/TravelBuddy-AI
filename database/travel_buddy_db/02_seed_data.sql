-- ============================================================
-- TravelBuddy AI - Seed Data
-- Chay SAU 01_schema.sql
--
-- Seed nay KHONG tao gia ve/gia phong mock.
-- Gia ve/gia phong se duoc lay boi collectors/API va luu vao
-- flight_price_snapshots / hotel_rate_snapshots voi TTL.
-- ============================================================

-- ============================================================
-- 1. TOP 10 DOMESTIC DESTINATIONS
-- ============================================================

INSERT INTO destinations
    (name, slug, city, province, country_code, country_name, iata_city_code,
     description, lat, lng, timezone, tags, best_months, avg_rating,
     review_count, is_seeded, popularity_rank, source)
VALUES
('Đà Nẵng', 'da-nang', 'Đà Nẵng', 'Đà Nẵng', 'VN', 'Vietnam', 'DAD',
 'Thành phố biển miền Trung, nổi bật với biển Mỹ Khê, bán đảo Sơn Trà, Ngũ Hành Sơn và kết nối thuận tiện tới Hội An.',
 16.054407, 108.202167, 'Asia/Ho_Chi_Minh', '["biển","thành phố","ẩm thực","resort"]', '[3,4,5,6,7,8]', 4.6, 0, TRUE, 1, 'manual_seed'),
('Hà Nội', 'ha-noi', 'Hà Nội', 'Hà Nội', 'VN', 'Vietnam', 'HAN',
 'Thủ đô Việt Nam với phố cổ, hồ Hoàn Kiếm, di sản văn hóa và ẩm thực đường phố đặc sắc.',
 21.027764, 105.834160, 'Asia/Ho_Chi_Minh', '["thành phố","lịch sử","ẩm thực","văn hóa"]', '[10,11,12,1,2,3,4]', 4.6, 0, TRUE, 2, 'manual_seed'),
('TP.HCM', 'ho-chi-minh', 'TP.HCM', 'TP.HCM', 'VN', 'Vietnam', 'SGN',
 'Đô thị năng động phía Nam, phù hợp city break, ẩm thực, mua sắm và kết nối các tuyến du lịch miền Tây, Phú Quốc.',
 10.823099, 106.629664, 'Asia/Ho_Chi_Minh', '["thành phố","ẩm thực","mua sắm","đêm"]', '[12,1,2,3,4]', 4.5, 0, TRUE, 3, 'manual_seed'),
('Hội An', 'hoi-an', 'Hội An', 'Quảng Nam', 'VN', 'Vietnam', 'DAD',
 'Phố cổ di sản UNESCO với đèn lồng, kiến trúc giao thoa và ẩm thực đặc trưng miền Trung.',
 15.880058, 108.338047, 'Asia/Ho_Chi_Minh', '["phố cổ","di sản","ẩm thực","văn hóa"]', '[2,3,4,5,8,9]', 4.8, 0, TRUE, 4, 'manual_seed'),
('Phú Quốc', 'phu-quoc', 'Phú Quốc', 'Kiên Giang', 'VN', 'Vietnam', 'PQC',
 'Đảo du lịch nổi tiếng với biển, resort, lặn ngắm san hô, hoàng hôn và hải sản.',
 10.289879, 103.984020, 'Asia/Ho_Chi_Minh', '["đảo","biển","resort","lặn biển"]', '[11,12,1,2,3,4]', 4.7, 0, TRUE, 5, 'manual_seed'),
('Nha Trang', 'nha-trang', 'Nha Trang', 'Khánh Hòa', 'VN', 'Vietnam', 'CXR',
 'Thành phố biển Nam Trung Bộ với vịnh biển, đảo Hòn Mun, suối khoáng và nhiều resort ven biển.',
 12.238791, 109.196749, 'Asia/Ho_Chi_Minh', '["biển","đảo","hải sản","resort"]', '[1,2,3,4,7,8]', 4.4, 0, TRUE, 6, 'manual_seed'),
('Đà Lạt', 'da-lat', 'Đà Lạt', 'Lâm Đồng', 'VN', 'Vietnam', 'DLI',
 'Thành phố cao nguyên khí hậu mát mẻ, nổi bật với hồ, thác, rừng thông, cà phê và nông trại.',
 11.940419, 108.458313, 'Asia/Ho_Chi_Minh', '["núi","cà phê","nghỉ dưỡng","thiên nhiên"]', '[11,12,1,2,3]', 4.5, 0, TRUE, 7, 'manual_seed'),
('Huế', 'hue', 'Huế', 'Thừa Thiên Huế', 'VN', 'Vietnam', 'HUI',
 'Cố đô Việt Nam với Đại Nội, lăng tẩm triều Nguyễn, sông Hương và ẩm thực cung đình.',
 16.463713, 107.590866, 'Asia/Ho_Chi_Minh', '["lịch sử","di sản","ẩm thực","văn hóa"]', '[1,2,3,4,8,9]', 4.5, 0, TRUE, 8, 'manual_seed'),
('Hạ Long', 'ha-long', 'Hạ Long', 'Quảng Ninh', 'VN', 'Vietnam', 'VDO',
 'Điểm đến vịnh biển, du thuyền và hang động đá vôi nổi tiếng tại Quảng Ninh.',
 20.971198, 107.044807, 'Asia/Ho_Chi_Minh', '["vịnh","du thuyền","thiên nhiên","di sản"]', '[3,4,5,10,11]', 4.7, 0, TRUE, 9, 'manual_seed'),
('Sapa', 'sapa', 'Sapa', 'Lào Cai', 'VN', 'Vietnam', NULL,
 'Thị trấn vùng cao với ruộng bậc thang, bản làng dân tộc, trekking và đỉnh Fansipan.',
 22.336360, 103.843785, 'Asia/Ho_Chi_Minh', '["núi","trekking","văn hóa","ruộng bậc thang"]', '[3,4,5,9,10]', 4.6, 0, TRUE, 10, 'manual_seed');

-- ============================================================
-- 2. AIRPORTS, AIRLINES, TOP 20 ROUTES
-- ============================================================

INSERT INTO airports (iata_code, name, city, country_code, lat, lng, timezone, is_domestic_vn) VALUES
('HAN', 'Noi Bai International Airport', 'Hà Nội', 'VN', 21.218714, 105.804170, 'Asia/Ho_Chi_Minh', TRUE),
('SGN', 'Tan Son Nhat International Airport', 'TP.HCM', 'VN', 10.818797, 106.651856, 'Asia/Ho_Chi_Minh', TRUE),
('DAD', 'Da Nang International Airport', 'Đà Nẵng', 'VN', 16.043917, 108.199370, 'Asia/Ho_Chi_Minh', TRUE),
('PQC', 'Phu Quoc International Airport', 'Phú Quốc', 'VN', 10.169800, 103.993100, 'Asia/Ho_Chi_Minh', TRUE),
('CXR', 'Cam Ranh International Airport', 'Nha Trang', 'VN', 11.998200, 109.219400, 'Asia/Ho_Chi_Minh', TRUE),
('DLI', 'Lien Khuong Airport', 'Đà Lạt', 'VN', 11.750000, 108.367000, 'Asia/Ho_Chi_Minh', TRUE),
('HUI', 'Phu Bai International Airport', 'Huế', 'VN', 16.401500, 107.703000, 'Asia/Ho_Chi_Minh', TRUE),
('VDO', 'Van Don International Airport', 'Hạ Long', 'VN', 21.117800, 107.414200, 'Asia/Ho_Chi_Minh', TRUE),
('HPH', 'Cat Bi International Airport', 'Hải Phòng', 'VN', 20.819400, 106.724900, 'Asia/Ho_Chi_Minh', TRUE);

INSERT INTO airlines (iata_code, name, country_code, booking_base_url, is_seed_target) VALUES
('VN', 'Vietnam Airlines', 'VN', 'https://www.vietnamairlines.com/vn/vi/home', TRUE),
('VJ', 'VietJet Air', 'VN', 'https://www.vietjetair.com/vi', TRUE),
('QH', 'Bamboo Airways', 'VN', 'https://www.bambooairways.com/vn/vi', TRUE);

INSERT INTO flight_routes
    (origin_iata, destination_iata, route_key, destination_id, is_domestic, is_popular_seed, popularity_rank)
VALUES
('HAN','SGN','HAN-SGN',(SELECT id FROM destinations WHERE slug='ho-chi-minh'),TRUE,TRUE,1),
('SGN','HAN','SGN-HAN',(SELECT id FROM destinations WHERE slug='ha-noi'),TRUE,TRUE,2),
('HAN','DAD','HAN-DAD',(SELECT id FROM destinations WHERE slug='da-nang'),TRUE,TRUE,3),
('DAD','HAN','DAD-HAN',(SELECT id FROM destinations WHERE slug='ha-noi'),TRUE,TRUE,4),
('SGN','DAD','SGN-DAD',(SELECT id FROM destinations WHERE slug='da-nang'),TRUE,TRUE,5),
('DAD','SGN','DAD-SGN',(SELECT id FROM destinations WHERE slug='ho-chi-minh'),TRUE,TRUE,6),
('HAN','PQC','HAN-PQC',(SELECT id FROM destinations WHERE slug='phu-quoc'),TRUE,TRUE,7),
('PQC','HAN','PQC-HAN',(SELECT id FROM destinations WHERE slug='ha-noi'),TRUE,TRUE,8),
('SGN','PQC','SGN-PQC',(SELECT id FROM destinations WHERE slug='phu-quoc'),TRUE,TRUE,9),
('PQC','SGN','PQC-SGN',(SELECT id FROM destinations WHERE slug='ho-chi-minh'),TRUE,TRUE,10),
('HAN','CXR','HAN-CXR',(SELECT id FROM destinations WHERE slug='nha-trang'),TRUE,TRUE,11),
('CXR','HAN','CXR-HAN',(SELECT id FROM destinations WHERE slug='ha-noi'),TRUE,TRUE,12),
('SGN','CXR','SGN-CXR',(SELECT id FROM destinations WHERE slug='nha-trang'),TRUE,TRUE,13),
('CXR','SGN','CXR-SGN',(SELECT id FROM destinations WHERE slug='ho-chi-minh'),TRUE,TRUE,14),
('HAN','DLI','HAN-DLI',(SELECT id FROM destinations WHERE slug='da-lat'),TRUE,TRUE,15),
('DLI','HAN','DLI-HAN',(SELECT id FROM destinations WHERE slug='ha-noi'),TRUE,TRUE,16),
('SGN','DLI','SGN-DLI',(SELECT id FROM destinations WHERE slug='da-lat'),TRUE,TRUE,17),
('DLI','SGN','DLI-SGN',(SELECT id FROM destinations WHERE slug='ho-chi-minh'),TRUE,TRUE,18),
('HAN','HUI','HAN-HUI',(SELECT id FROM destinations WHERE slug='hue'),TRUE,TRUE,19),
('SGN','HUI','SGN-HUI',(SELECT id FROM destinations WHERE slug='hue'),TRUE,TRUE,20);

-- ============================================================
-- 3. HOTEL METADATA SEED - NO PRICES
-- ============================================================

WITH hotel_seed(destination_slug, name, slug, stars, property_type, area, address, lat, lng, amenities, provider, deep_link_url, source) AS (
    VALUES
    ('da-nang','Furama Resort Danang','furama-resort-danang',5,'resort','Bắc Mỹ An','68 Hồ Xuân Hương, Đà Nẵng',16.033300,108.246400,'["beach","pool","spa","restaurant","gym","wifi"]','manual','https://www.agoda.com/search?city=16440','manual_seed'),
    ('da-nang','Haian Beach Hotel & Spa','haian-beach-hotel-spa',4,'hotel','Mỹ Khê','278 Võ Nguyên Giáp, Đà Nẵng',16.061300,108.249400,'["beach","pool","breakfast","wifi","restaurant"]','manual','https://www.agoda.com/search?city=16440','manual_seed'),
    ('da-nang','Brilliant Hotel Danang','brilliant-hotel-danang',4,'hotel','Hải Châu','162 Bạch Đằng, Đà Nẵng',16.066100,108.224000,'["river_view","breakfast","wifi","restaurant"]','manual','https://www.agoda.com/search?city=16440','manual_seed'),

    ('ha-noi','Sofitel Legend Metropole Hanoi','sofitel-legend-metropole-hanoi',5,'hotel','Hoàn Kiếm','15 Ngô Quyền, Hà Nội',21.025500,105.856300,'["heritage","pool","spa","restaurant","gym","wifi"]','manual','https://www.agoda.com/search?city=2758','manual_seed'),
    ('ha-noi','Hanoi La Siesta Hotel & Spa','hanoi-la-siesta-hotel-spa',4,'hotel','Hoàn Kiếm','94 Mã Mây, Hà Nội',21.035200,105.852000,'["spa","breakfast","wifi","restaurant"]','manual','https://www.agoda.com/search?city=2758','manual_seed'),
    ('ha-noi','The Light Hotel Hanoi','the-light-hotel-hanoi',4,'hotel','Hoàn Kiếm','128-130 Hàng Bông, Hà Nội',21.029300,105.847700,'["pool","breakfast","wifi","gym"]','manual','https://www.agoda.com/search?city=2758','manual_seed'),

    ('ho-chi-minh','Rex Hotel Saigon','rex-hotel-saigon',5,'hotel','Quận 1','141 Nguyễn Huệ, TP.HCM',10.775600,106.701900,'["pool","spa","restaurant","gym","wifi"]','manual','https://www.agoda.com/search?city=13170','manual_seed'),
    ('ho-chi-minh','Liberty Central Saigon Citypoint','liberty-central-saigon-citypoint',4,'hotel','Quận 1','59 Pasteur, TP.HCM',10.775900,106.700500,'["pool","breakfast","wifi","gym"]','manual','https://www.agoda.com/search?city=13170','manual_seed'),
    ('ho-chi-minh','Silverland Jolie Hotel','silverland-jolie-hotel',4,'hotel','Quận 1','4D Thi Sách, TP.HCM',10.777800,106.705000,'["pool","breakfast","wifi","spa"]','manual','https://www.agoda.com/search?city=13170','manual_seed'),

    ('hoi-an','Anantara Hoi An Resort','anantara-hoi-an-resort',5,'resort','Ven sông','1 Phạm Hồng Thái, Hội An',15.881700,108.334200,'["river_view","pool","spa","restaurant","bicycle"]','manual','https://www.agoda.com/search?city=16552','manual_seed'),
    ('hoi-an','Hoi An Silk Village Resort','hoi-an-silk-village-resort',4,'resort','Tân An','28 Nguyễn Tất Thành, Hội An',15.890600,108.323100,'["pool","spa","breakfast","wifi"]','manual','https://www.agoda.com/search?city=16552','manual_seed'),
    ('hoi-an','Little Riverside Hoi An','little-riverside-hoi-an',5,'hotel','Cẩm Châu','09 Phan Bội Châu, Hội An',15.878900,108.337500,'["river_view","pool","breakfast","wifi"]','manual','https://www.agoda.com/search?city=16552','manual_seed'),

    ('phu-quoc','La Veranda Resort Phu Quoc','la-veranda-resort-phu-quoc',5,'resort','Dương Đông','Trần Hưng Đạo, Phú Quốc',10.199400,103.964700,'["beach","pool","spa","restaurant","wifi"]','manual','https://www.agoda.com/search?city=17188','manual_seed'),
    ('phu-quoc','Lahana Resort Phu Quoc','lahana-resort-phu-quoc',4,'resort','Dương Đông','91/3 Trần Hưng Đạo, Phú Quốc',10.212700,103.960600,'["pool","breakfast","wifi","garden"]','manual','https://www.agoda.com/search?city=17188','manual_seed'),
    ('phu-quoc','Premier Village Phu Quoc Resort','premier-village-phu-quoc-resort',5,'resort','Mũi Ông Đội','Mũi Ông Đội, Phú Quốc',10.009900,104.023400,'["beach","pool","villa","spa","restaurant"]','manual','https://www.agoda.com/search?city=17188','manual_seed'),

    ('nha-trang','InterContinental Nha Trang','intercontinental-nha-trang',5,'hotel','Trần Phú','32-34 Trần Phú, Nha Trang',12.246100,109.196400,'["beach","pool","spa","restaurant","gym"]','manual','https://www.agoda.com/search?city=2679','manual_seed'),
    ('nha-trang','Mia Resort Nha Trang','mia-resort-nha-trang',5,'resort','Bãi Dông','Bãi Dông, Cam Lâm, Khánh Hòa',12.065000,109.196000,'["beach","villa","pool","spa","restaurant"]','manual','https://www.agoda.com/search?city=2679','manual_seed'),
    ('nha-trang','Liberty Central Nha Trang','liberty-central-nha-trang',4,'hotel','Trần Phú','9 Biệt Thự, Nha Trang',12.238400,109.195600,'["pool","breakfast","wifi","gym"]','manual','https://www.agoda.com/search?city=2679','manual_seed'),

    ('da-lat','Dalat Palace Heritage Hotel','dalat-palace-heritage-hotel',5,'hotel','Hồ Xuân Hương','2 Trần Phú, Đà Lạt',11.938800,108.438000,'["heritage","lake_view","restaurant","spa","garden"]','manual','https://www.agoda.com/search?city=15932','manual_seed'),
    ('da-lat','Ana Mandara Villas Dalat','ana-mandara-villas-dalat',5,'resort','Lê Lai','Lê Lai, Đà Lạt',11.950800,108.430600,'["villa","garden","spa","restaurant","pool"]','manual','https://www.agoda.com/search?city=15932','manual_seed'),
    ('da-lat','TTC Hotel Premium Ngoc Lan','ttc-hotel-premium-ngoc-lan',4,'hotel','Trung tâm','42 Nguyễn Chí Thanh, Đà Lạt',11.940000,108.441900,'["lake_view","breakfast","wifi","restaurant"]','manual','https://www.agoda.com/search?city=15932','manual_seed'),

    ('hue','Azerai La Residence Hue','azerai-la-residence-hue',5,'hotel','Sông Hương','5 Lê Lợi, Huế',16.458800,107.578600,'["heritage","river_view","pool","spa","restaurant"]','manual','https://www.agoda.com/search?city=2846','manual_seed'),
    ('hue','Pilgrimage Village Boutique Resort','pilgrimage-village-boutique-resort',5,'resort','Thủy Xuân','130 Minh Mạng, Huế',16.425700,107.568800,'["pool","spa","garden","restaurant"]','manual','https://www.agoda.com/search?city=2846','manual_seed'),
    ('hue','Eldora Hotel Hue','eldora-hotel-hue',4,'hotel','Trung tâm','60 Bến Nghé, Huế',16.461000,107.594300,'["pool","breakfast","wifi","restaurant"]','manual','https://www.agoda.com/search?city=2846','manual_seed'),

    ('ha-long','Vinpearl Resort & Spa Ha Long','vinpearl-resort-spa-ha-long',5,'resort','Đảo Rều','Đảo Rều, Hạ Long',20.948900,107.049000,'["bay_view","pool","spa","beach","restaurant"]','manual','https://www.agoda.com/search?city=17182','manual_seed'),
    ('ha-long','Wyndham Legend Halong','wyndham-legend-halong',5,'hotel','Bãi Cháy','12 Hạ Long, Bãi Cháy',20.953000,107.055900,'["bay_view","pool","breakfast","gym"]','manual','https://www.agoda.com/search?city=17182','manual_seed'),
    ('ha-long','Paradise Suites Hotel','paradise-suites-hotel',4,'hotel','Tuần Châu','Tuần Châu, Hạ Long',20.923000,106.991200,'["pool","breakfast","wifi","marina"]','manual','https://www.agoda.com/search?city=17182','manual_seed'),

    ('sapa','Hotel de la Coupole Sapa','hotel-de-la-coupole-sapa',5,'hotel','Trung tâm','1 Hoàng Liên, Sapa',22.335500,103.840900,'["mountain_view","pool","spa","restaurant"]','manual','https://www.agoda.com/search?city=17198','manual_seed'),
    ('sapa','Topas Ecolodge','topas-ecolodge',5,'lodge','Thanh Kim','Thanh Kim, Sapa',22.262900,103.934600,'["mountain_view","pool","eco","restaurant"]','manual','https://www.agoda.com/search?city=17198','manual_seed'),
    ('sapa','Pao''s Sapa Leisure Hotel','paos-sapa-leisure-hotel',5,'hotel','Mường Hoa','Mường Hoa, Sapa',22.328500,103.839900,'["mountain_view","pool","breakfast","wifi"]','manual','https://www.agoda.com/search?city=17198','manual_seed')
)
INSERT INTO hotels
    (destination_id, name, slug, stars, property_type, area, address, lat, lng,
     amenities, provider, deep_link_url, is_seeded, source)
SELECT d.id, h.name, h.slug, h.stars, h.property_type, h.area, h.address, h.lat, h.lng,
       h.amenities::jsonb, h.provider, h.deep_link_url, TRUE, h.source
FROM hotel_seed h
JOIN destinations d ON d.slug = h.destination_slug;

-- ============================================================
-- 4. SEED POI - TOP POI SAMPLE FOR EACH DESTINATION
-- ============================================================

WITH poi_seed(destination_slug, name, slug, category, kinds, description, lat, lng, estimated_duration_min, source_ref) AS (
    VALUES
    ('da-nang','Bãi biển Mỹ Khê','bai-bien-my-khe','beach','["beaches","natural"]','Bãi biển nổi tiếng của Đà Nẵng, phù hợp tắm biển, dạo sáng sớm và ngắm bình minh.',16.061700,108.246800,120,'seed-da-nang-my-khe'),
    ('da-nang','Ngũ Hành Sơn','ngu-hanh-son','nature','["natural","historic","religion"]','Cụm núi đá vôi, hang động và chùa cổ phía Nam Đà Nẵng.',16.003900,108.264400,180,'seed-da-nang-marble'),
    ('da-nang','Bán đảo Sơn Trà','ban-dao-son-tra','nature','["natural","view_points"]','Khu bán đảo có rừng, chùa Linh Ứng, đường ven biển và điểm ngắm cảnh.',16.118600,108.273900,240,'seed-da-nang-son-tra'),

    ('ha-noi','Hồ Hoàn Kiếm','ho-hoan-kiem','landmark','["cultural","historic"]','Không gian trung tâm Hà Nội, phù hợp đi bộ, tham quan đền Ngọc Sơn và phố cổ.',21.028700,105.852100,90,'seed-ha-noi-hoan-kiem'),
    ('ha-noi','Văn Miếu - Quốc Tử Giám','van-mieu-quoc-tu-giam','historic','["historic","cultural"]','Quần thể di tích Nho học tiêu biểu, gắn với lịch sử giáo dục Việt Nam.',21.028100,105.835600,120,'seed-ha-noi-van-mieu'),
    ('ha-noi','Phố cổ Hà Nội','pho-co-ha-noi','culture','["cultural","foods"]','Khu phố cổ với ẩm thực, kiến trúc và đời sống đô thị đặc trưng.',21.035000,105.850000,180,'seed-ha-noi-old-quarter'),

    ('ho-chi-minh','Dinh Độc Lập','dinh-doc-lap','historic','["historic","cultural"]','Công trình lịch sử trung tâm TP.HCM, thường kết hợp tham quan Nhà thờ Đức Bà và Bưu điện.',10.777000,106.695300,90,'seed-hcm-independence'),
    ('ho-chi-minh','Chợ Bến Thành','cho-ben-thanh','market','["foods","cultural"]','Chợ biểu tượng của thành phố, phù hợp mua sắm và khám phá ẩm thực.',10.772500,106.698000,90,'seed-hcm-ben-thanh'),
    ('ho-chi-minh','Phố đi bộ Nguyễn Huệ','pho-di-bo-nguyen-hue','city_walk','["urban","cultural"]','Không gian đi bộ trung tâm, nhiều quán cà phê, nhà hàng và hoạt động buổi tối.',10.775700,106.703900,90,'seed-hcm-nguyen-hue'),

    ('hoi-an','Phố cổ Hội An','pho-co-hoi-an','heritage','["historic","cultural"]','Khu phố cổ di sản với nhà cổ, hội quán, đèn lồng và ẩm thực địa phương.',15.880100,108.338000,180,'seed-hoi-an-old-town'),
    ('hoi-an','Chùa Cầu','chua-cau-hoi-an','historic','["historic","architecture"]','Biểu tượng kiến trúc của Hội An, nằm trong khu phố cổ.',15.877900,108.326900,45,'seed-hoi-an-japanese-bridge'),
    ('hoi-an','Rừng dừa Bảy Mẫu','rung-dua-bay-mau','nature','["natural","amusements"]','Khu sinh thái sông nước với trải nghiệm thuyền thúng.',15.848000,108.377000,120,'seed-hoi-an-coconut'),

    ('phu-quoc','Bãi Sao','bai-sao-phu-quoc','beach','["beaches","natural"]','Bãi biển cát trắng nổi tiếng ở phía Nam Phú Quốc.',10.058800,104.035600,180,'seed-pq-bai-sao'),
    ('phu-quoc','Dinh Cậu','dinh-cau-phu-quoc','culture','["religion","view_points"]','Điểm ngắm hoàng hôn và địa danh văn hóa tại Dương Đông.',10.219600,103.958100,60,'seed-pq-dinh-cau'),
    ('phu-quoc','Hòn Thơm','hon-thom-phu-quoc','island','["beaches","amusements"]','Đảo phía Nam Phú Quốc, nổi bật với cáp treo biển và hoạt động vui chơi.',9.957200,104.017900,240,'seed-pq-hon-thom'),

    ('nha-trang','Tháp Bà Ponagar','thap-ba-ponagar','historic','["historic","cultural","religion"]','Di tích Chăm Pa nổi bật bên sông Cái.',12.265400,109.195300,90,'seed-nt-ponagar'),
    ('nha-trang','Hòn Mun','hon-mun','island','["natural","beaches"]','Khu vực đảo nổi tiếng với lặn ngắm san hô.',12.165200,109.303200,240,'seed-nt-hon-mun'),
    ('nha-trang','Bãi biển Trần Phú','bai-bien-tran-phu','beach','["beaches","urban"]','Bãi biển trung tâm thành phố, thuận tiện đi bộ và ăn uống.',12.238800,109.196700,120,'seed-nt-tran-phu'),

    ('da-lat','Hồ Xuân Hương','ho-xuan-huong','landmark','["natural","urban"]','Hồ trung tâm Đà Lạt, phù hợp đi dạo, đạp vịt và cà phê ven hồ.',11.941900,108.448300,90,'seed-dl-xuan-huong'),
    ('da-lat','Thung lũng Tình Yêu','thung-lung-tinh-yeu','nature','["natural","gardens"]','Khu du lịch cảnh quan với hồ, đồi thông và vườn hoa.',11.978300,108.449300,180,'seed-dl-love-valley'),
    ('da-lat','Đồi chè Cầu Đất','doi-che-cau-dat','nature','["natural","view_points"]','Vùng đồi chè và săn mây ngoại ô Đà Lạt.',11.812200,108.667500,180,'seed-dl-cau-dat'),

    ('hue','Đại Nội Huế','dai-noi-hue','historic','["historic","cultural"]','Quần thể Hoàng thành và Tử Cấm Thành triều Nguyễn.',16.469500,107.577500,180,'seed-hue-citadel'),
    ('hue','Lăng Khải Định','lang-khai-dinh','historic','["historic","architecture"]','Lăng vua Nguyễn nổi bật với kiến trúc giao thoa Đông Tây.',16.398200,107.590800,90,'seed-hue-khai-dinh'),
    ('hue','Chùa Thiên Mụ','chua-thien-mu','religion','["religion","historic"]','Ngôi chùa cổ bên sông Hương, biểu tượng của Huế.',16.453900,107.545500,90,'seed-hue-thien-mu'),

    ('ha-long','Vịnh Hạ Long','vinh-ha-long','bay','["natural","unesco"]','Vịnh biển với đảo đá vôi, hang động và trải nghiệm du thuyền.',20.910100,107.183900,300,'seed-hl-bay'),
    ('ha-long','Hang Sửng Sốt','hang-sung-sot','cave','["natural","caves"]','Hang động nổi bật trên tuyến tham quan vịnh Hạ Long.',20.846900,107.091600,90,'seed-hl-sung-sot'),
    ('ha-long','Đảo Ti Tốp','dao-ti-top','island','["beaches","view_points"]','Đảo có bãi tắm nhỏ và điểm leo ngắm toàn cảnh vịnh.',20.855600,107.081900,120,'seed-hl-titop'),

    ('sapa','Fansipan','fansipan','mountain','["natural","view_points"]','Đỉnh núi cao nhất Việt Nam, có thể đi cáp treo hoặc trekking theo tour.',22.303300,103.775800,240,'seed-sapa-fansipan'),
    ('sapa','Bản Cát Cát','ban-cat-cat','culture','["cultural","natural"]','Bản du lịch gần trung tâm Sapa, có thác nước và văn hóa H''Mông.',22.329600,103.821300,150,'seed-sapa-cat-cat'),
    ('sapa','Đèo Ô Quy Hồ','deo-o-quy-ho','viewpoint','["natural","view_points"]','Cung đèo ngắm núi nổi tiếng giữa Lào Cai và Lai Châu.',22.348700,103.775100,120,'seed-sapa-o-quy-ho')
)
INSERT INTO pois
    (destination_id, name, slug, category, kinds, description, lat, lng,
     estimated_duration_min, source, source_ref, is_seeded, fetched_at)
SELECT d.id, p.name, p.slug, p.category, p.kinds::jsonb, p.description, p.lat, p.lng,
       p.estimated_duration_min, 'manual_seed', p.source_ref, TRUE, NOW()
FROM poi_seed p
JOIN destinations d ON d.slug = p.destination_slug;

-- ============================================================
-- 5. COUNTRIES + VISA RULE FALLBACK
-- ============================================================

INSERT INTO countries
    (code, alpha3, name_en, name_vn, capital, region, subregion, currencies,
     languages, timezones, calling_code, source, fetched_at, raw)
VALUES
('VN','VNM','Vietnam','Việt Nam','Hà Nội','Asia','South-Eastern Asia','[{"code":"VND","name":"Vietnamese đồng","symbol":"₫"}]','["Vietnamese"]','["UTC+07:00"]','+84','manual_seed',NOW(),'{}'),
('TH','THA','Thailand','Thái Lan','Bangkok','Asia','South-Eastern Asia','[{"code":"THB","name":"Thai baht","symbol":"฿"}]','["Thai"]','["UTC+07:00"]','+66','manual_seed',NOW(),'{}'),
('JP','JPN','Japan','Nhật Bản','Tokyo','Asia','Eastern Asia','[{"code":"JPY","name":"Japanese yen","symbol":"¥"}]','["Japanese"]','["UTC+09:00"]','+81','manual_seed',NOW(),'{}'),
('SG','SGP','Singapore','Singapore','Singapore','Asia','South-Eastern Asia','[{"code":"SGD","name":"Singapore dollar","symbol":"$"}]','["English","Malay","Tamil","Chinese"]','["UTC+08:00"]','+65','manual_seed',NOW(),'{}'),
('KR','KOR','South Korea','Hàn Quốc','Seoul','Asia','Eastern Asia','[{"code":"KRW","name":"South Korean won","symbol":"₩"}]','["Korean"]','["UTC+09:00"]','+82','manual_seed',NOW(),'{}'),
('CN','CHN','China','Trung Quốc','Beijing','Asia','Eastern Asia','[{"code":"CNY","name":"Chinese yuan","symbol":"¥"}]','["Chinese"]','["UTC+08:00"]','+86','manual_seed',NOW(),'{}'),
('FR','FRA','France','Pháp','Paris','Europe','Western Europe','[{"code":"EUR","name":"Euro","symbol":"€"}]','["French"]','["UTC-10:00","UTC+01:00","UTC+03:00"]','+33','manual_seed',NOW(),'{}'),
('US','USA','United States','Mỹ','Washington, D.C.','Americas','North America','[{"code":"USD","name":"United States dollar","symbol":"$"}]','["English"]','["UTC-12:00","UTC-05:00","UTC-04:00"]','+1','manual_seed',NOW(),'{}'),
('AU','AUS','Australia','Úc','Canberra','Oceania','Australia and New Zealand','[{"code":"AUD","name":"Australian dollar","symbol":"$"}]','["English"]','["UTC+08:00","UTC+10:00"]','+61','manual_seed',NOW(),'{}'),
('GB','GBR','United Kingdom','Vương quốc Anh','London','Europe','Northern Europe','[{"code":"GBP","name":"British pound","symbol":"£"}]','["English"]','["UTC+00:00"]','+44','manual_seed',NOW(),'{}');

INSERT INTO country_visa_rules
    (passport_country_code, destination_country_code, visa_required, visa_type, max_stay_days, note, source_url, verified_at)
VALUES
('VN','VN',FALSE,'domestic',NULL,'Du lịch nội địa Việt Nam không cần visa.',NULL,CURRENT_DATE),
('VN','TH',FALSE,'visa_free',30,'Công dân Việt Nam thường được miễn thị thực ngắn ngày khi du lịch Thái Lan; kiểm tra lại quy định trước khi bay.',NULL,CURRENT_DATE),
('VN','SG',FALSE,'visa_free',30,'Công dân Việt Nam thường được miễn thị thực ngắn ngày khi du lịch Singapore; cần hộ chiếu còn hạn.',NULL,CURRENT_DATE),
('VN','JP',TRUE,'sticker_or_evisa',NULL,'Nhật Bản thường yêu cầu visa với hộ chiếu Việt Nam; cần kiểm tra nguồn lãnh sự chính thức.',NULL,CURRENT_DATE),
('VN','KR',TRUE,'sticker_or_evisa',NULL,'Hàn Quốc thường yêu cầu visa với hộ chiếu Việt Nam; cần kiểm tra nguồn lãnh sự chính thức.',NULL,CURRENT_DATE),
('VN','CN',TRUE,'sticker',NULL,'Trung Quốc thường yêu cầu visa với hộ chiếu Việt Nam; cần kiểm tra nguồn lãnh sự chính thức.',NULL,CURRENT_DATE),
('VN','FR',TRUE,'schengen',NULL,'Pháp thuộc khối Schengen, thường yêu cầu visa Schengen với hộ chiếu Việt Nam.',NULL,CURRENT_DATE),
('VN','US',TRUE,'sticker',NULL,'Mỹ yêu cầu visa với hộ chiếu Việt Nam.',NULL,CURRENT_DATE),
('VN','AU',TRUE,'evisa_or_visitor',NULL,'Úc yêu cầu visa visitor/eVisitor phù hợp với hộ chiếu và mục đích chuyến đi.',NULL,CURRENT_DATE),
('VN','GB',TRUE,'visitor_visa',NULL,'Vương quốc Anh thường yêu cầu visa visitor với hộ chiếu Việt Nam.',NULL,CURRENT_DATE);

-- ============================================================
-- 6. PACKING TEMPLATES
-- ============================================================

WITH beach AS (
    INSERT INTO packing_templates
        (name, trip_type, season, day_min, day_max, activities, traveler_tags, priority)
    VALUES
        ('Biển mùa hè 3-5 ngày', 'beach', 'summer', 3, 5, '["swim","snorkel","walk"]', '[]', 10)
    RETURNING id
), mountain AS (
    INSERT INTO packing_templates
        (name, trip_type, season, day_min, day_max, activities, traveler_tags, priority)
    VALUES
        ('Núi/trekking mùa mát 3-5 ngày', 'mountain', 'cool', 3, 5, '["trekking","photo","walk"]', '[]', 20)
    RETURNING id
), city AS (
    INSERT INTO packing_templates
        (name, trip_type, season, day_min, day_max, activities, traveler_tags, priority)
    VALUES
        ('City break 2-4 ngày', 'city', 'dry', 2, 4, '["food","shopping","walk"]', '[]', 30)
    RETURNING id
), rainy AS (
    INSERT INTO packing_templates
        (name, trip_type, season, day_min, day_max, activities, traveler_tags, priority)
    VALUES
        ('Du lịch mùa mưa 3-5 ngày', 'general', 'rainy', 3, 5, '["walk","photo"]', '[]', 40)
    RETURNING id
)
INSERT INTO packing_template_items
    (template_id, category, item_name, quantity_rule, note, is_default_checked, sort_order)
SELECT id, category, item_name, quantity_rule, note, is_default_checked, sort_order
FROM beach, (VALUES
    ('clothing','Đồ bơi','fixed:2','Mang thêm túi chống nước cho đồ ướt.',TRUE,1),
    ('clothing','Áo phông thoáng mát','days','Ưu tiên chất liệu nhanh khô.',TRUE,2),
    ('accessories','Kính mát','fixed:1',NULL,TRUE,3),
    ('accessories','Dép biển','fixed:1',NULL,TRUE,4),
    ('health','Kem chống nắng SPF50+','fixed:1','Bôi lại sau khi tắm biển.',TRUE,5),
    ('health','Thuốc say sóng/say xe','fixed:1','Cần nếu đi đảo hoặc tàu cao tốc.',TRUE,6),
    ('documents','CCCD/Hộ chiếu','fixed:1',NULL,TRUE,7),
    ('electronics','Sạc dự phòng','fixed:1',NULL,TRUE,8)
) AS v(category, item_name, quantity_rule, note, is_default_checked, sort_order)
UNION ALL
SELECT id, category, item_name, quantity_rule, note, is_default_checked, sort_order
FROM mountain, (VALUES
    ('clothing','Áo khoác gió','fixed:1','Nhiệt độ vùng núi xuống nhanh buổi tối.',TRUE,1),
    ('clothing','Quần dài trekking','fixed:2',NULL,TRUE,2),
    ('accessories','Giày trekking','fixed:1','Không dùng giày mới chưa đi thử.',TRUE,3),
    ('accessories','Balo nhỏ đi trong ngày','fixed:1',NULL,TRUE,4),
    ('health','Thuốc đau bụng/đau đầu','fixed:1',NULL,TRUE,5),
    ('health','Miếng dán cá nhân','fixed:1','Hữu ích khi đi bộ nhiều.',TRUE,6),
    ('documents','CCCD/Hộ chiếu','fixed:1',NULL,TRUE,7),
    ('electronics','Đèn pin nhỏ','fixed:1',NULL,TRUE,8)
) AS v(category, item_name, quantity_rule, note, is_default_checked, sort_order)
UNION ALL
SELECT id, category, item_name, quantity_rule, note, is_default_checked, sort_order
FROM city, (VALUES
    ('clothing','Trang phục đi bộ thoải mái','days',NULL,TRUE,1),
    ('clothing','Một bộ lịch sự','fixed:1','Dùng khi đi nhà hàng hoặc check-in nơi yêu cầu dress code.',FALSE,2),
    ('accessories','Túi đeo chéo chống trộm','fixed:1',NULL,TRUE,3),
    ('health','Khẩu trang/gel rửa tay','fixed:1',NULL,TRUE,4),
    ('documents','Thẻ ATM/thẻ tín dụng','fixed:1',NULL,TRUE,5),
    ('documents','CCCD/Hộ chiếu','fixed:1',NULL,TRUE,6),
    ('electronics','Cáp sạc điện thoại','fixed:1',NULL,TRUE,7),
    ('electronics','Tai nghe','fixed:1',NULL,FALSE,8)
) AS v(category, item_name, quantity_rule, note, is_default_checked, sort_order)
UNION ALL
SELECT id, category, item_name, quantity_rule, note, is_default_checked, sort_order
FROM rainy, (VALUES
    ('clothing','Áo khoác chống nước nhẹ','fixed:1',NULL,TRUE,1),
    ('accessories','Ô gấp hoặc áo mưa mỏng','fixed:1',NULL,TRUE,2),
    ('accessories','Túi chống nước','fixed:1','Bảo vệ giấy tờ và điện thoại.',TRUE,3),
    ('health','Thuốc cảm/sốt','fixed:1',NULL,TRUE,4),
    ('health','Dầu gió hoặc thuốc côn trùng','fixed:1',NULL,FALSE,5),
    ('documents','CCCD/Hộ chiếu','fixed:1',NULL,TRUE,6),
    ('electronics','Sạc dự phòng','fixed:1',NULL,TRUE,7),
    ('electronics','Túi zip cho thiết bị','fixed:1',NULL,TRUE,8)
) AS v(category, item_name, quantity_rule, note, is_default_checked, sort_order);

-- ============================================================
-- 7. SAMPLE USER/TRIP WITHOUT FAKE PRICE SNAPSHOTS
-- ============================================================

INSERT INTO users (full_name, email, travel_preferences, total_points, level)
VALUES
('Nguyễn Lan', 'nguyen.lan@gmail.com',
 '{"budget_range": [8000000, 15000000], "hotel_stars": 3, "food": ["seafood","street_food"], "trip_type": ["couple","family"]}',
 2450, 'Explorer'),
('Trần Huy', 'tran.huy@gmail.com',
 '{"budget_range": [5000000, 10000000], "hotel_stars": 2, "food": ["street_food"], "trip_type": ["backpacker","solo"]}',
 980, 'Explorer');

WITH u AS (
    SELECT id FROM users WHERE email='nguyen.lan@gmail.com'
), t AS (
    INSERT INTO trips (owner_id, destination_id, title, start_date, end_date, budget_amount, status, is_public)
    VALUES (
        (SELECT id FROM u),
        (SELECT id FROM destinations WHERE slug='da-nang'),
        'Đà Nẵng - Hội An 5N4Đ',
        '2026-07-14',
        '2026-07-18',
        10000000,
        'planning',
        TRUE
    )
    RETURNING id
), d1 AS (
    INSERT INTO trip_days (trip_id, day_number, date)
    VALUES ((SELECT id FROM t), 1, '2026-07-14')
    RETURNING id
), d2 AS (
    INSERT INTO trip_days (trip_id, day_number, date)
    VALUES ((SELECT id FROM t), 2, '2026-07-15')
    RETURNING id
)
INSERT INTO itinerary_items
    (day_id, item_type, title, destination_id, poi_id, start_time, duration_min, cost_amount, sort_order)
SELECT d1.id, 'poi', 'Bãi biển Mỹ Khê buổi sáng',
       (SELECT id FROM destinations WHERE slug='da-nang'),
       (SELECT id FROM pois WHERE slug='bai-bien-my-khe'),
       '06:00'::TIME, 120, 0, 1
FROM d1
UNION ALL
SELECT d1.id, 'poi', 'Ngũ Hành Sơn',
       (SELECT id FROM destinations WHERE slug='da-nang'),
       (SELECT id FROM pois WHERE slug='ngu-hanh-son'),
       '14:00'::TIME, 180, 0, 2
FROM d1
UNION ALL
SELECT d2.id, 'poi', 'Phố cổ Hội An buổi tối',
       (SELECT id FROM destinations WHERE slug='hoi-an'),
       (SELECT id FROM pois WHERE slug='pho-co-hoi-an'),
       '19:00'::TIME, 180, 0, 1
FROM d2;

INSERT INTO reviews (user_id, destination_id, rating, content, helpful_count)
VALUES
((SELECT id FROM users WHERE email='nguyen.lan@gmail.com'),
 (SELECT id FROM destinations WHERE slug='da-nang'),
 4.5,
 'Đà Nẵng phù hợp cho lịch trình tự túc: biển gần trung tâm, dễ ghép Hội An, nhiều lựa chọn ăn uống.',
 47);

-- ============================================================
-- 8. SUMMARY
-- ============================================================

SELECT 'destinations' AS tbl, COUNT(*) FROM destinations
UNION ALL SELECT 'airports', COUNT(*) FROM airports
UNION ALL SELECT 'airlines', COUNT(*) FROM airlines
UNION ALL SELECT 'flight_routes', COUNT(*) FROM flight_routes
UNION ALL SELECT 'flight_price_snapshots', COUNT(*) FROM flight_price_snapshots
UNION ALL SELECT 'hotels', COUNT(*) FROM hotels
UNION ALL SELECT 'hotel_rate_snapshots', COUNT(*) FROM hotel_rate_snapshots
UNION ALL SELECT 'pois', COUNT(*) FROM pois
UNION ALL SELECT 'countries', COUNT(*) FROM countries
UNION ALL SELECT 'packing_templates', COUNT(*) FROM packing_templates
UNION ALL SELECT 'packing_template_items', COUNT(*) FROM packing_template_items
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'trips', COUNT(*) FROM trips
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews;

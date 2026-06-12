-- ============================================================
-- TravelBuddy AI - Curated POI Seed
-- Run after 01_schema.sql and 02_seed_data.sql.
--
-- Idempotent: safe to run multiple times. This expands the MVP
-- attraction dataset for the "pick places for trip notes" flow.
-- ============================================================

WITH poi_seed(
    destination_slug, name, slug, category, kinds, description,
    lat, lng, estimated_duration_min, source_ref
) AS (
    VALUES
    -- Da Nang
    ('da-nang','Bãi biển Mỹ Khê','bai-bien-my-khe','beach','["beaches","natural"]','Bãi biển trung tâm nổi tiếng của Đà Nẵng, phù hợp tắm biển, đi dạo và ngắm bình minh.',16.061700,108.246800,120,'curated-da-nang-my-khe'),
    ('da-nang','Ngũ Hành Sơn','ngu-hanh-son','nature','["natural","historic","religion"]','Cụm núi đá vôi, hang động và chùa cổ phía Nam Đà Nẵng.',16.003900,108.264400,180,'curated-da-nang-marble'),
    ('da-nang','Bán đảo Sơn Trà','ban-dao-son-tra','nature','["natural","view_points"]','Khu bán đảo có rừng, đường ven biển, điểm ngắm cảnh và nhiều cung chạy xe đẹp.',16.118600,108.273900,240,'curated-da-nang-son-tra'),
    ('da-nang','Cầu Rồng','cau-rong','landmark','["architecture","urban","nightlife"]','Biểu tượng đô thị bắc qua sông Hàn, nổi bật nhất khi lên đèn buổi tối.',16.061900,108.227000,60,'curated-da-nang-dragon-bridge'),
    ('da-nang','Bà Nà Hills','ba-na-hills','theme_park','["amusements","view_points","architecture"]','Khu du lịch trên núi với cáp treo, Cầu Vàng và nhiều điểm vui chơi.',15.995000,107.996000,360,'curated-da-nang-ba-na-hills'),
    ('da-nang','Chùa Linh Ứng Sơn Trà','chua-linh-ung-son-tra','religion','["religion","view_points","architecture"]','Ngôi chùa lớn trên bán đảo Sơn Trà, có tượng Quan Âm và tầm nhìn ra biển.',16.100800,108.277800,90,'curated-da-nang-linh-ung'),
    ('da-nang','Chợ Hàn','cho-han-da-nang','market','["foods","shopping","cultural"]','Chợ trung tâm phù hợp mua đặc sản, quà mang về và thử đồ ăn địa phương.',16.068500,108.224000,75,'curated-da-nang-han-market'),
    ('da-nang','Cầu Tình Yêu','cau-tinh-yeu-da-nang','landmark','["urban","view_points","nightlife"]','Điểm đi dạo ven sông Hàn, gần tượng cá chép hóa rồng và Cầu Rồng.',16.063700,108.229800,45,'curated-da-nang-love-bridge'),
    ('da-nang','Bảo tàng Điêu khắc Chăm','bao-tang-dieu-khac-cham','museum','["museums","historic","cultural"]','Bảo tàng trưng bày hiện vật Chăm Pa quan trọng tại miền Trung.',16.060500,108.223000,90,'curated-da-nang-cham-museum'),
    ('da-nang','Asia Park Đà Nẵng','asia-park-da-nang','theme_park','["amusements","nightlife"]','Công viên giải trí trong thành phố, phù hợp gia đình và buổi tối.',16.039300,108.226000,180,'curated-da-nang-asia-park'),
    ('da-nang','Đèo Hải Vân','deo-hai-van','viewpoint','["natural","view_points","road_trip"]','Cung đèo ven biển nổi tiếng giữa Đà Nẵng và Huế, hợp lịch trình road trip.',16.198000,108.132000,150,'curated-da-nang-hai-van'),
    ('da-nang','Đỉnh Bàn Cờ','dinh-ban-co','viewpoint','["natural","view_points"]','Điểm ngắm toàn cảnh Đà Nẵng trên bán đảo Sơn Trà.',16.121300,108.288000,120,'curated-da-nang-ban-co'),
    ('da-nang','Bãi biển Non Nước','bai-bien-non-nuoc','beach','["beaches","natural"]','Bãi biển phía Nam Đà Nẵng gần Ngũ Hành Sơn, yên tĩnh hơn khu Mỹ Khê.',16.000700,108.270300,120,'curated-da-nang-non-nuoc'),
    ('da-nang','Công viên APEC','cong-vien-apec-da-nang','park','["urban","architecture","view_points"]','Không gian công cộng ven sông Hàn với kiến trúc mái vòm nổi bật.',16.058500,108.223900,45,'curated-da-nang-apec-park'),
    ('da-nang','Chợ đêm Helio','cho-dem-helio','market','["foods","nightlife","shopping"]','Khu chợ đêm gần trung tâm, phù hợp ăn uống và đi chơi tối.',16.036400,108.226800,90,'curated-da-nang-helio'),

    -- Ha Noi
    ('ha-noi','Hồ Hoàn Kiếm','ho-hoan-kiem','landmark','["cultural","historic","urban"]','Không gian trung tâm Hà Nội, phù hợp đi bộ, tham quan đền Ngọc Sơn và phố cổ.',21.028700,105.852100,90,'curated-ha-noi-hoan-kiem'),
    ('ha-noi','Phố cổ Hà Nội','pho-co-ha-noi','culture','["cultural","foods","urban"]','Khu phố cổ với ẩm thực, kiến trúc và đời sống đô thị đặc trưng.',21.035000,105.850000,180,'curated-ha-noi-old-quarter'),
    ('ha-noi','Văn Miếu - Quốc Tử Giám','van-mieu-quoc-tu-giam','historic','["historic","cultural","architecture"]','Quần thể di tích Nho học tiêu biểu, gắn với lịch sử giáo dục Việt Nam.',21.028100,105.835600,120,'curated-ha-noi-van-mieu'),
    ('ha-noi','Lăng Chủ tịch Hồ Chí Minh','lang-chu-tich-ho-chi-minh','historic','["historic","cultural"]','Cụm tham quan lịch sử ở quảng trường Ba Đình.',21.036700,105.834600,120,'curated-ha-noi-mausoleum'),
    ('ha-noi','Chùa Một Cột','chua-mot-cot','religion','["religion","historic","architecture"]','Ngôi chùa biểu tượng gần khu Ba Đình, thường ghép cùng lăng và bảo tàng.',21.035900,105.833600,45,'curated-ha-noi-one-pillar'),
    ('ha-noi','Hoàng thành Thăng Long','hoang-thanh-thang-long','heritage','["historic","unesco","cultural"]','Di sản văn hóa thế giới, phù hợp tìm hiểu lịch sử Thăng Long.',21.035600,105.840300,120,'curated-ha-noi-citadel'),
    ('ha-noi','Hồ Tây','ho-tay','landmark','["urban","view_points","foods"]','Khu hồ lớn của Hà Nội, hợp đi dạo, cà phê và ngắm hoàng hôn.',21.058300,105.823100,120,'curated-ha-noi-west-lake'),
    ('ha-noi','Chùa Trấn Quốc','chua-tran-quoc','religion','["religion","historic","architecture"]','Ngôi chùa cổ bên Hồ Tây, nổi bật với tháp và không gian ven hồ.',21.047900,105.836100,60,'curated-ha-noi-tran-quoc'),
    ('ha-noi','Nhà tù Hỏa Lò','nha-tu-hoa-lo','museum','["museums","historic"]','Di tích lịch sử trong trung tâm Hà Nội, phù hợp lịch trình văn hóa.',21.025300,105.846500,75,'curated-ha-noi-hoa-lo'),
    ('ha-noi','Nhà thờ Lớn Hà Nội','nha-tho-lon-ha-noi','landmark','["architecture","religion","urban"]','Công trình kiến trúc nổi bật gần Hồ Hoàn Kiếm và khu cà phê phố cổ.',21.028700,105.848900,45,'curated-ha-noi-cathedral'),
    ('ha-noi','Chợ Đồng Xuân','cho-dong-xuan','market','["shopping","foods","cultural"]','Chợ lớn trong phố cổ, hợp mua sắm và khám phá ẩm thực quanh chợ.',21.038300,105.849700,75,'curated-ha-noi-dong-xuan'),
    ('ha-noi','Cầu Long Biên','cau-long-bien','landmark','["architecture","historic","view_points"]','Cây cầu lịch sử qua sông Hồng, phù hợp chụp ảnh và ngắm phố ven sông.',21.043100,105.855200,60,'curated-ha-noi-long-bien'),
    ('ha-noi','Bảo tàng Dân tộc học Việt Nam','bao-tang-dan-toc-hoc-viet-nam','museum','["museums","cultural"]','Bảo tàng phù hợp gia đình, có không gian trưng bày ngoài trời.',21.040400,105.798000,120,'curated-ha-noi-ethnology'),
    ('ha-noi','Nhà hát Múa rối nước Thăng Long','nha-hat-mua-roi-nuoc-thang-long','culture','["cultural","theatres"]','Điểm xem biểu diễn truyền thống ngay gần Hồ Hoàn Kiếm.',21.031400,105.853900,75,'curated-ha-noi-water-puppet'),
    ('ha-noi','Làng gốm Bát Tràng','lang-gom-bat-trang','craft_village','["cultural","shopping","workshops"]','Làng nghề gốm ven sông Hồng, phù hợp nửa ngày trải nghiệm thủ công.',20.975000,105.912000,180,'curated-ha-noi-bat-trang'),

    -- Ho Chi Minh City
    ('ho-chi-minh','Dinh Độc Lập','dinh-doc-lap','historic','["historic","cultural","architecture"]','Công trình lịch sử trung tâm TP.HCM, thường ghép với nhà thờ và bưu điện.',10.777000,106.695300,90,'curated-hcm-independence'),
    ('ho-chi-minh','Chợ Bến Thành','cho-ben-thanh','market','["foods","shopping","cultural"]','Chợ biểu tượng của thành phố, phù hợp mua sắm và khám phá ẩm thực.',10.772500,106.698000,90,'curated-hcm-ben-thanh'),
    ('ho-chi-minh','Phố đi bộ Nguyễn Huệ','pho-di-bo-nguyen-hue','city_walk','["urban","cultural","nightlife"]','Không gian đi bộ trung tâm với nhiều quán cà phê, nhà hàng và hoạt động buổi tối.',10.775700,106.703900,90,'curated-hcm-nguyen-hue'),
    ('ho-chi-minh','Nhà thờ Đức Bà Sài Gòn','nha-tho-duc-ba-sai-gon','landmark','["architecture","religion","historic"]','Công trình kiến trúc nổi bật ở trung tâm Quận 1.',10.779800,106.699000,45,'curated-hcm-notre-dame'),
    ('ho-chi-minh','Bưu điện Trung tâm Sài Gòn','buu-dien-trung-tam-sai-gon','landmark','["architecture","historic"]','Công trình cổ gần Nhà thờ Đức Bà, phù hợp tham quan nhanh trong city walk.',10.779900,106.699900,45,'curated-hcm-post-office'),
    ('ho-chi-minh','Bảo tàng Chứng tích Chiến tranh','bao-tang-chung-tich-chien-tranh','museum','["museums","historic"]','Bảo tàng lịch sử quan trọng tại Quận 3.',10.779500,106.692000,120,'curated-hcm-war-remnants'),
    ('ho-chi-minh','Địa đạo Củ Chi','dia-dao-cu-chi','historic','["historic","museums"]','Khu di tích ngoại thành, phù hợp lịch trình nửa ngày hoặc một ngày.',11.141900,106.462500,240,'curated-hcm-cu-chi'),
    ('ho-chi-minh','Landmark 81','landmark-81','viewpoint','["architecture","view_points","shopping"]','Tòa nhà cao nổi bật tại Bình Thạnh, có khu thương mại và điểm ngắm thành phố.',10.794900,106.721800,120,'curated-hcm-landmark-81'),
    ('ho-chi-minh','Phố Tây Bùi Viện','pho-tay-bui-vien','nightlife','["nightlife","foods","urban"]','Khu phố đêm sôi động ở Quận 1.',10.767900,106.693100,90,'curated-hcm-bui-vien'),
    ('ho-chi-minh','Chùa Ngọc Hoàng','chua-ngoc-hoang','religion','["religion","architecture"]','Ngôi chùa nổi tiếng tại Quận 1, phù hợp tham quan văn hóa.',10.791600,106.698100,60,'curated-hcm-jade-emperor'),
    ('ho-chi-minh','Bitexco Financial Tower Skydeck','bitexco-skydeck','viewpoint','["architecture","view_points"]','Điểm ngắm skyline trung tâm TP.HCM từ trên cao.',10.771600,106.704500,75,'curated-hcm-bitexco'),
    ('ho-chi-minh','Nhà hát Thành phố','nha-hat-thanh-pho-hcm','culture','["architecture","theatres","cultural"]','Công trình kiến trúc Pháp cổ tại trung tâm Quận 1.',10.776600,106.703100,45,'curated-hcm-opera-house'),
    ('ho-chi-minh','Chợ hoa Hồ Thị Kỷ','cho-hoa-ho-thi-ky','market','["foods","shopping","nightlife"]','Khu chợ hoa và ẩm thực đường phố đông vui ở Quận 10.',10.774300,106.672400,90,'curated-hcm-ho-thi-ky'),
    ('ho-chi-minh','Chợ Bình Tây','cho-binh-tay','market','["shopping","cultural","architecture"]','Chợ lớn ở khu Chợ Lớn, phù hợp khám phá văn hóa người Hoa.',10.749600,106.651800,90,'curated-hcm-binh-tay'),
    ('ho-chi-minh','Bảo tàng TP.HCM','bao-tang-tp-hcm','museum','["museums","historic","architecture"]','Bảo tàng trong tòa nhà cổ gần phố đi bộ Nguyễn Huệ.',10.776900,106.699900,75,'curated-hcm-city-museum'),

    -- Hoi An
    ('hoi-an','Phố cổ Hội An','pho-co-hoi-an','heritage','["historic","cultural","unesco"]','Khu phố cổ di sản với nhà cổ, hội quán, đèn lồng và ẩm thực địa phương.',15.880100,108.338000,180,'curated-hoi-an-old-town'),
    ('hoi-an','Chùa Cầu Hội An','chua-cau-hoi-an','historic','["historic","architecture"]','Biểu tượng kiến trúc của Hội An, nằm trong khu phố cổ.',15.877900,108.326900,45,'curated-hoi-an-japanese-bridge'),
    ('hoi-an','Rừng dừa Bảy Mẫu','rung-dua-bay-mau','nature','["natural","amusements"]','Khu sinh thái sông nước với trải nghiệm thuyền thúng.',15.848000,108.377000,120,'curated-hoi-an-coconut'),
    ('hoi-an','Bãi biển An Bàng','bai-bien-an-bang','beach','["beaches","foods"]','Bãi biển gần phố cổ, nhiều quán ăn và beach bar.',15.914000,108.337000,150,'curated-hoi-an-an-bang'),
    ('hoi-an','Làng rau Trà Quế','lang-rau-tra-que','craft_village','["cultural","foods","workshops"]','Làng rau giữa Hội An và An Bàng, phù hợp trải nghiệm nấu ăn và đạp xe.',15.902500,108.335500,120,'curated-hoi-an-tra-que'),
    ('hoi-an','Nhà cổ Tấn Ký','nha-co-tan-ky','historic','["historic","architecture","cultural"]','Nhà cổ tiêu biểu trong khu phố cổ Hội An.',15.877500,108.326600,45,'curated-hoi-an-tan-ky'),
    ('hoi-an','Hội quán Phúc Kiến','hoi-quan-phuc-kien','historic','["historic","religion","architecture"]','Hội quán người Hoa nổi bật trên tuyến tham quan phố cổ.',15.878800,108.330900,45,'curated-hoi-an-fujian'),
    ('hoi-an','Chợ đêm Hội An','cho-dem-hoi-an','market','["nightlife","shopping","foods"]','Khu chợ đêm bán đèn lồng, đồ lưu niệm và đồ ăn đường phố.',15.876800,108.325600,90,'curated-hoi-an-night-market'),
    ('hoi-an','Làng gốm Thanh Hà','lang-gom-thanh-ha','craft_village','["cultural","workshops"]','Làng nghề gốm gần phố cổ, phù hợp ghé nửa ngày.',15.885600,108.312100,120,'curated-hoi-an-thanh-ha'),
    ('hoi-an','Làng mộc Kim Bồng','lang-moc-kim-bong','craft_village','["cultural","workshops"]','Làng nghề mộc bên kia sông Thu Bồn, hợp đi xe đạp hoặc thuyền.',15.870500,108.323500,120,'curated-hoi-an-kim-bong'),
    ('hoi-an','Bãi biển Cửa Đại','bai-bien-cua-dai','beach','["beaches","foods"]','Bãi biển phía Đông Hội An, phù hợp nghỉ ngơi và ăn hải sản.',15.879400,108.367100,120,'curated-hoi-an-cua-dai'),
    ('hoi-an','Thánh địa Mỹ Sơn','thanh-dia-my-son','heritage','["historic","unesco","cultural"]','Quần thể đền tháp Chăm Pa tại Quảng Nam, thường đi trong ngày từ Hội An.',15.765000,108.122000,240,'curated-hoi-an-my-son'),
    ('hoi-an','Cù Lao Chàm','cu-lao-cham','island','["beaches","natural","islands"]','Cụm đảo ngoài khơi Hội An, phù hợp đi tour biển trong ngày.',15.958000,108.510000,300,'curated-hoi-an-cham-island'),
    ('hoi-an','Công viên Ấn tượng Hội An','cong-vien-an-tuong-hoi-an','theme_park','["cultural","theatres","nightlife"]','Khu biểu diễn và trải nghiệm văn hóa Hội An về đêm.',15.875100,108.338400,180,'curated-hoi-an-memories'),
    ('hoi-an','Bảo tàng Văn hóa Sa Huỳnh','bao-tang-van-hoa-sa-huynh','museum','["museums","historic","cultural"]','Bảo tàng nhỏ trong phố cổ, phù hợp ghép tuyến tham quan di sản.',15.877600,108.326500,45,'curated-hoi-an-sa-huynh'),

    -- Phu Quoc
    ('phu-quoc','Bãi Sao','bai-sao-phu-quoc','beach','["beaches","natural"]','Bãi biển cát trắng nổi tiếng ở phía Nam Phú Quốc.',10.058800,104.035600,180,'curated-phu-quoc-bai-sao'),
    ('phu-quoc','Dinh Cậu','dinh-cau-phu-quoc','culture','["religion","view_points"]','Điểm ngắm hoàng hôn và địa danh văn hóa tại Dương Đông.',10.219600,103.958100,60,'curated-phu-quoc-dinh-cau'),
    ('phu-quoc','Hòn Thơm','hon-thom-phu-quoc','island','["beaches","amusements","islands"]','Đảo phía Nam Phú Quốc, nổi bật với cáp treo biển và hoạt động vui chơi.',9.957200,104.017900,240,'curated-phu-quoc-hon-thom'),
    ('phu-quoc','VinWonders Phú Quốc','vinwonders-phu-quoc','theme_park','["amusements","family"]','Công viên chủ đề lớn ở Bắc đảo, phù hợp gia đình.',10.338500,103.854500,360,'curated-phu-quoc-vinwonders'),
    ('phu-quoc','Vinpearl Safari Phú Quốc','vinpearl-safari-phu-quoc','nature','["zoos","family","natural"]','Công viên chăm sóc và bảo tồn động vật bán hoang dã ở Bắc đảo.',10.337700,103.889200,240,'curated-phu-quoc-safari'),
    ('phu-quoc','Thị trấn Hoàng Hôn','thi-tran-hoang-hon','landmark','["architecture","view_points","nightlife"]','Khu vui chơi, mua sắm và ngắm hoàng hôn ở Nam đảo.',10.019400,104.015700,180,'curated-phu-quoc-sunset-town'),
    ('phu-quoc','Cầu Hôn','cau-hon-phu-quoc','landmark','["architecture","view_points"]','Công trình biểu tượng tại khu Hoàng Hôn, hợp chụp ảnh lúc chiều tối.',10.018500,104.014500,60,'curated-phu-quoc-kiss-bridge'),
    ('phu-quoc','Nhà tù Phú Quốc','nha-tu-phu-quoc','historic','["historic","museums"]','Di tích lịch sử ở An Thới.',10.054400,104.037400,90,'curated-phu-quoc-prison'),
    ('phu-quoc','Làng chài Hàm Ninh','lang-chai-ham-ninh','culture','["foods","cultural","view_points"]','Làng chài ven biển phía Đông, nổi tiếng với hải sản và bình minh.',10.187000,104.049700,120,'curated-phu-quoc-ham-ninh'),
    ('phu-quoc','Bãi Rạch Vẹm','bai-rach-vem','beach','["beaches","natural","foods"]','Khu biển Bắc đảo thường được biết đến với sao biển và làng bè.',10.373000,103.956000,180,'curated-phu-quoc-rach-vem'),
    ('phu-quoc','Suối Tranh','suoi-tranh','nature','["natural","waterfalls"]','Điểm đi bộ nhẹ và tắm suối trong mùa có nước.',10.176600,104.012300,120,'curated-phu-quoc-suoi-tranh'),
    ('phu-quoc','Mũi Gành Dầu','mui-ganh-dau','viewpoint','["beaches","view_points","natural"]','Mũi đất ở Bắc đảo với góc nhìn ra biển và hải giới.',10.381500,103.840600,120,'curated-phu-quoc-ganh-dau'),
    ('phu-quoc','Bãi Ông Lang','bai-ong-lang','beach','["beaches","foods"]','Bãi biển yên tĩnh phía Tây đảo, hợp nghỉ ngơi và ngắm hoàng hôn.',10.247600,103.939800,150,'curated-phu-quoc-ong-lang'),
    ('phu-quoc','Chợ đêm Phú Quốc','cho-dem-phu-quoc','market','["foods","nightlife","shopping"]','Khu ăn uống và mua đặc sản trung tâm Dương Đông.',10.216700,103.960200,90,'curated-phu-quoc-night-market'),
    ('phu-quoc','Vườn tiêu Phú Quốc','vuon-tieu-phu-quoc','farm','["foods","cultural","shopping"]','Điểm tham quan nông sản địa phương, phù hợp mua quà và chụp ảnh.',10.248000,103.993000,60,'curated-phu-quoc-pepper-farm'),

    -- Nha Trang
    ('nha-trang','Tháp Bà Ponagar','thap-ba-ponagar','historic','["historic","cultural","religion"]','Di tích Chăm Pa nổi bật bên sông Cái.',12.265400,109.195300,90,'curated-nha-trang-ponagar'),
    ('nha-trang','Hòn Mun','hon-mun','island','["natural","beaches","islands"]','Khu vực đảo nổi tiếng với lặn ngắm san hô.',12.165200,109.303200,240,'curated-nha-trang-hon-mun'),
    ('nha-trang','Bãi biển Trần Phú','bai-bien-tran-phu','beach','["beaches","urban"]','Bãi biển trung tâm thành phố, thuận tiện đi bộ và ăn uống.',12.238800,109.196700,120,'curated-nha-trang-tran-phu'),
    ('nha-trang','VinWonders Nha Trang','vinwonders-nha-trang','theme_park','["amusements","family","islands"]','Khu vui chơi trên đảo Hòn Tre, phù hợp lịch trình cả ngày.',12.217700,109.242800,360,'curated-nha-trang-vinwonders'),
    ('nha-trang','Hòn Tằm','hon-tam','island','["beaches","islands","wellness"]','Đảo nghỉ dưỡng gần Nha Trang với biển, bùn khoáng và thể thao nước.',12.183600,109.234700,240,'curated-nha-trang-hon-tam'),
    ('nha-trang','Chùa Long Sơn','chua-long-son','religion','["religion","view_points","historic"]','Ngôi chùa nổi tiếng với tượng Phật trắng trên đồi.',12.250200,109.180800,75,'curated-nha-trang-long-son'),
    ('nha-trang','Nhà thờ Núi Nha Trang','nha-tho-nui-nha-trang','landmark','["architecture","religion"]','Công trình kiến trúc đá nằm trên đồi nhỏ trong trung tâm.',12.248500,109.187500,45,'curated-nha-trang-cathedral'),
    ('nha-trang','Chợ Đầm','cho-dam-nha-trang','market','["shopping","foods","cultural"]','Chợ lớn của Nha Trang, phù hợp mua đặc sản và đồ khô.',12.255000,109.191000,75,'curated-nha-trang-dam-market'),
    ('nha-trang','Viện Hải dương học','vien-hai-duong-hoc','museum','["museums","family","natural"]','Điểm tham quan giáo dục về sinh vật biển, phù hợp gia đình.',12.207500,109.214600,90,'curated-nha-trang-oceanography'),
    ('nha-trang','Thác Ba Hồ','thac-ba-ho','nature','["natural","waterfalls","adventure"]','Điểm trekking nhẹ và tắm suối phía Bắc Nha Trang.',12.386000,109.134000,180,'curated-nha-trang-ba-ho'),
    ('nha-trang','Hòn Chồng','hon-chong','landmark','["natural","view_points"]','Cụm đá ven biển với góc nhìn ra vịnh Nha Trang.',12.272200,109.206400,60,'curated-nha-trang-hon-chong'),
    ('nha-trang','Suối khoáng nóng I-Resort','i-resort-nha-trang','wellness','["wellness","family"]','Khu tắm bùn khoáng và nghỉ ngơi gần trung tâm.',12.279100,109.181100,180,'curated-nha-trang-i-resort'),
    ('nha-trang','Bãi Dài Cam Ranh','bai-dai-cam-ranh','beach','["beaches","foods"]','Bãi biển dài phía Nam Nha Trang, gần khu resort Cam Ranh.',12.021500,109.215000,180,'curated-nha-trang-bai-dai'),
    ('nha-trang','Đảo Điệp Sơn','dao-diep-son','island','["islands","beaches","natural"]','Điểm đảo nổi tiếng với con đường cát giữa biển, thường đi tour trong ngày.',12.655000,109.390000,300,'curated-nha-trang-diep-son'),
    ('nha-trang','Vịnh Nha Phu','vinh-nha-phu','bay','["natural","islands","family"]','Khu vịnh phía Bắc Nha Trang, thường kết hợp Hòn Lao hoặc Suối Hoa Lan.',12.383000,109.214000,240,'curated-nha-trang-nha-phu'),

    -- Da Lat
    ('da-lat','Hồ Xuân Hương','ho-xuan-huong','landmark','["natural","urban"]','Hồ trung tâm Đà Lạt, phù hợp đi dạo, đạp vịt và cà phê ven hồ.',11.941900,108.448300,90,'curated-da-lat-xuan-huong'),
    ('da-lat','Thung lũng Tình Yêu','thung-lung-tinh-yeu','nature','["natural","gardens"]','Khu du lịch cảnh quan với hồ, đồi thông và vườn hoa.',11.978300,108.449300,180,'curated-da-lat-love-valley'),
    ('da-lat','Đồi chè Cầu Đất','doi-che-cau-dat','nature','["natural","view_points","farm"]','Vùng đồi chè và săn mây ngoại ô Đà Lạt.',11.812200,108.667500,180,'curated-da-lat-cau-dat'),
    ('da-lat','Núi Langbiang','nui-langbiang','mountain','["natural","view_points","adventure"]','Điểm ngắm cao nguyên và trekking nhẹ gần trung tâm Đà Lạt.',12.050000,108.441000,240,'curated-da-lat-langbiang'),
    ('da-lat','Thác Datanla','thac-datanla','waterfall','["natural","waterfalls","adventure"]','Khu thác gần đèo Prenn, có máng trượt và hoạt động ngoài trời.',11.903700,108.449800,180,'curated-da-lat-datanla'),
    ('da-lat','Chùa Linh Phước','chua-linh-phuoc','religion','["religion","architecture","cultural"]','Ngôi chùa khảm sành nổi bật tại Trại Mát.',11.944900,108.498900,90,'curated-da-lat-linh-phuoc'),
    ('da-lat','Crazy House','crazy-house-da-lat','landmark','["architecture","museums"]','Công trình kiến trúc độc đáo trong trung tâm Đà Lạt.',11.936700,108.434800,75,'curated-da-lat-crazy-house'),
    ('da-lat','Vườn hoa Thành phố Đà Lạt','vuon-hoa-thanh-pho-da-lat','garden','["gardens","urban"]','Vườn hoa lớn gần Hồ Xuân Hương, phù hợp chụp ảnh.',11.948600,108.458900,90,'curated-da-lat-flower-garden'),
    ('da-lat','Hồ Tuyền Lâm','ho-tuyen-lam','lake','["natural","view_points"]','Khu hồ rộng phía Nam thành phố, gần Thiền viện Trúc Lâm.',11.886800,108.436700,150,'curated-da-lat-tuyen-lam'),
    ('da-lat','Thiền viện Trúc Lâm','thien-vien-truc-lam-da-lat','religion','["religion","view_points","architecture"]','Thiền viện trên đồi nhìn xuống Hồ Tuyền Lâm.',11.888600,108.435500,90,'curated-da-lat-truc-lam'),
    ('da-lat','Chợ đêm Đà Lạt','cho-dem-da-lat','market','["foods","nightlife","shopping"]','Khu ăn uống và mua sắm buổi tối ở trung tâm.',11.940100,108.437900,90,'curated-da-lat-night-market'),
    ('da-lat','Nhà thờ Domaine de Marie','nha-tho-domaine-de-marie','landmark','["architecture","religion"]','Nhà thờ màu hồng nổi bật, phù hợp ghé nhanh trong city tour.',11.951000,108.435100,45,'curated-da-lat-domaine'),
    ('da-lat','Thác Pongour','thac-pongour','waterfall','["natural","waterfalls"]','Thác lớn tại Đức Trọng, phù hợp lịch trình ngoại ô trong ngày.',11.735400,108.268300,180,'curated-da-lat-pongour'),
    ('da-lat','Mê Linh Coffee Garden','me-linh-coffee-garden','cafe','["foods","view_points","farm"]','Quán cà phê ngoại ô có view đồi và nông trại cà phê.',11.930700,108.330900,90,'curated-da-lat-me-linh'),
    ('da-lat','Quảng trường Lâm Viên','quang-truong-lam-vien','landmark','["urban","architecture"]','Không gian quảng trường bên Hồ Xuân Hương với biểu tượng nụ hoa atiso.',11.939200,108.448300,45,'curated-da-lat-lam-vien'),

    -- Hue
    ('hue','Đại Nội Huế','dai-noi-hue','historic','["historic","cultural","unesco"]','Quần thể Hoàng thành và Tử Cấm Thành triều Nguyễn.',16.469500,107.577500,180,'curated-hue-citadel'),
    ('hue','Lăng Khải Định','lang-khai-dinh','historic','["historic","architecture"]','Lăng vua Nguyễn nổi bật với kiến trúc giao thoa Đông Tây.',16.398200,107.590800,90,'curated-hue-khai-dinh'),
    ('hue','Chùa Thiên Mụ','chua-thien-mu','religion','["religion","historic","view_points"]','Ngôi chùa cổ bên sông Hương, biểu tượng của Huế.',16.453900,107.545500,90,'curated-hue-thien-mu'),
    ('hue','Lăng Minh Mạng','lang-minh-mang','historic','["historic","architecture","gardens"]','Lăng vua Nguyễn với không gian hồ nước, cây xanh và kiến trúc cân đối.',16.373800,107.568700,90,'curated-hue-minh-mang'),
    ('hue','Lăng Tự Đức','lang-tu-duc','historic','["historic","architecture","gardens"]','Quần thể lăng có hồ, nhà bia và không gian yên tĩnh.',16.433600,107.565900,90,'curated-hue-tu-duc'),
    ('hue','Chợ Đông Ba','cho-dong-ba','market','["foods","shopping","cultural"]','Chợ lớn của Huế, phù hợp ăn đặc sản và mua quà.',16.470300,107.588600,90,'curated-hue-dong-ba'),
    ('hue','Sông Hương','song-huong','landmark','["view_points","natural","cultural"]','Dòng sông biểu tượng của Huế, hợp đi thuyền hoặc dạo chiều.',16.463700,107.590900,120,'curated-hue-perfume-river'),
    ('hue','Cầu Trường Tiền','cau-truong-tien','landmark','["architecture","historic","view_points"]','Cây cầu biểu tượng bắc qua sông Hương.',16.467400,107.590300,45,'curated-hue-truong-tien'),
    ('hue','Làng hương Thủy Xuân','lang-huong-thuy-xuan','craft_village','["cultural","shopping","workshops"]','Làng nghề hương nhiều màu sắc trên tuyến đi các lăng.',16.431300,107.562500,75,'curated-hue-thuy-xuan'),
    ('hue','Vườn quốc gia Bạch Mã','vuon-quoc-gia-bach-ma','nature','["natural","waterfalls","adventure"]','Khu rừng núi và thác nước giữa Huế và Đà Nẵng, phù hợp lịch trình trong ngày.',16.199000,107.850000,360,'curated-hue-bach-ma'),
    ('hue','Cung An Định','cung-an-dinh','historic','["historic","architecture"]','Cung điện triều Nguyễn với kiến trúc nổi bật gần trung tâm Huế.',16.457700,107.594300,75,'curated-hue-an-dinh'),
    ('hue','Bảo tàng Cổ vật Cung đình Huế','bao-tang-co-vat-cung-dinh-hue','museum','["museums","historic","cultural"]','Bảo tàng trưng bày cổ vật cung đình trong khu vực Đại Nội.',16.467700,107.579800,75,'curated-hue-royal-antiquities'),
    ('hue','Điện Hòn Chén','dien-hon-chen','religion','["religion","historic","view_points"]','Điểm tâm linh bên sông Hương, thường đi kết hợp thuyền.',16.401200,107.549500,90,'curated-hue-hon-chen'),
    ('hue','Phá Tam Giang','pha-tam-giang','nature','["natural","view_points","foods"]','Đầm phá rộng gần Huế, phù hợp ngắm hoàng hôn và ăn hải sản.',16.585000,107.507000,180,'curated-hue-tam-giang'),
    ('hue','Đầm Lập An','dam-lap-an','nature','["natural","view_points","foods"]','Đầm nước lợ gần Lăng Cô, hợp ghé trên cung Huế - Đà Nẵng.',16.223000,108.064000,120,'curated-hue-lap-an'),

    -- Ha Long
    ('ha-long','Vịnh Hạ Long','vinh-ha-long','bay','["natural","unesco","islands"]','Vịnh biển với đảo đá vôi, hang động và trải nghiệm du thuyền.',20.910100,107.183900,300,'curated-ha-long-bay'),
    ('ha-long','Hang Sửng Sốt','hang-sung-sot','cave','["natural","caves"]','Hang động nổi bật trên tuyến tham quan vịnh Hạ Long.',20.846900,107.091600,90,'curated-ha-long-sung-sot'),
    ('ha-long','Đảo Ti Tốp','dao-ti-top','island','["beaches","view_points","islands"]','Đảo có bãi tắm nhỏ và điểm leo ngắm toàn cảnh vịnh.',20.855600,107.081900,120,'curated-ha-long-titop'),
    ('ha-long','Động Thiên Cung','dong-thien-cung','cave','["natural","caves"]','Hang động gần bến Tuần Châu, thường nằm trong tour vịnh ngắn.',20.907400,107.040800,75,'curated-ha-long-thien-cung'),
    ('ha-long','Hang Đầu Gỗ','hang-dau-go','cave','["natural","caves","historic"]','Hang lớn trên đảo Đầu Gỗ, gần động Thiên Cung.',20.903900,107.034800,75,'curated-ha-long-dau-go'),
    ('ha-long','Bãi biển Bãi Cháy','bai-bien-bai-chay','beach','["beaches","urban"]','Bãi biển nhân tạo gần khu du lịch Bãi Cháy.',20.951400,107.047900,120,'curated-ha-long-bai-chay'),
    ('ha-long','Sun World Hạ Long','sun-world-ha-long','theme_park','["amusements","family","view_points"]','Khu vui chơi với cáp treo, vòng quay và công viên giải trí.',20.959100,107.049100,240,'curated-ha-long-sun-world'),
    ('ha-long','Đảo Tuần Châu','dao-tuan-chau','island','["islands","marina","beaches"]','Khu đảo du lịch và bến tàu tham quan vịnh.',20.921900,106.986500,120,'curated-ha-long-tuan-chau'),
    ('ha-long','Làng chài Cửa Vạn','lang-chai-cua-van','culture','["cultural","natural","islands"]','Làng chài nổi trên vịnh, thường xuất hiện trong tour du thuyền.',20.842000,107.089000,90,'curated-ha-long-cua-van'),
    ('ha-long','Vịnh Bái Tử Long','vinh-bai-tu-long','bay','["natural","islands"]','Khu vịnh phía Đông Bắc, yên tĩnh hơn tuyến Hạ Long phổ biến.',20.980000,107.300000,300,'curated-ha-long-bai-tu-long'),
    ('ha-long','Bảo tàng Quảng Ninh','bao-tang-quang-ninh','museum','["museums","architecture","cultural"]','Bảo tàng kiến trúc kính đen nổi bật tại Hòn Gai.',20.951800,107.097500,90,'curated-ha-long-quang-ninh-museum'),
    ('ha-long','Chợ Hạ Long','cho-ha-long','market','["foods","shopping","cultural"]','Chợ địa phương phù hợp mua hải sản khô và đặc sản.',20.950600,107.082200,75,'curated-ha-long-market'),
    ('ha-long','Núi Bài Thơ','nui-bai-tho','viewpoint','["natural","view_points"]','Điểm núi biểu tượng nhìn ra thành phố và vịnh, cần kiểm tra điều kiện tiếp cận thực tế.',20.950000,107.083000,120,'curated-ha-long-bai-tho'),
    ('ha-long','Làng chài Vung Viêng','lang-chai-vung-vieng','culture','["cultural","natural","islands"]','Làng chài trên khu vực vịnh, thường ghép trong tuyến du thuyền.',20.872000,107.252000,90,'curated-ha-long-vung-vieng'),
    ('ha-long','Công viên Hoa Hạ Long','cong-vien-hoa-ha-long','park','["urban","gardens","family"]','Không gian công viên ven biển gần trung tâm Hạ Long.',20.952000,107.085000,60,'curated-ha-long-flower-park'),

    -- Sapa
    ('sapa','Fansipan','fansipan','mountain','["natural","view_points","mountains"]','Đỉnh núi cao nhất Việt Nam, có thể đi cáp treo hoặc trekking theo tour.',22.303300,103.775800,240,'curated-sapa-fansipan'),
    ('sapa','Bản Cát Cát','ban-cat-cat','culture','["cultural","natural"]','Bản du lịch gần trung tâm Sapa, có thác nước và văn hóa H''Mông.',22.329600,103.821300,150,'curated-sapa-cat-cat'),
    ('sapa','Đèo Ô Quy Hồ','deo-o-quy-ho','viewpoint','["natural","view_points","road_trip"]','Cung đèo ngắm núi nổi tiếng giữa Lào Cai và Lai Châu.',22.348700,103.775100,120,'curated-sapa-o-quy-ho'),
    ('sapa','Thung lũng Mường Hoa','thung-lung-muong-hoa','nature','["natural","view_points","cultural"]','Thung lũng ruộng bậc thang và bản làng phía dưới thị trấn Sapa.',22.300000,103.880000,240,'curated-sapa-muong-hoa'),
    ('sapa','Bản Tả Van','ban-ta-van','culture','["cultural","natural","homestay"]','Bản làng trong thung lũng Mường Hoa, phù hợp trekking và homestay.',22.303400,103.891800,180,'curated-sapa-ta-van'),
    ('sapa','Bản Lao Chải','ban-lao-chai','culture','["cultural","natural","homestay"]','Bản làng nổi tiếng với ruộng bậc thang và tuyến trekking từ Sapa.',22.313900,103.868500,180,'curated-sapa-lao-chai'),
    ('sapa','Núi Hàm Rồng','nui-ham-rong','viewpoint','["natural","gardens","view_points"]','Điểm ngắm thị trấn Sapa và dãy Hoàng Liên ngay gần trung tâm.',22.334900,103.842600,120,'curated-sapa-ham-rong'),
    ('sapa','Thác Bạc','thac-bac-sapa','waterfall','["natural","waterfalls"]','Thác nước trên tuyến đi đèo Ô Quy Hồ.',22.357200,103.779900,60,'curated-sapa-silver-waterfall'),
    ('sapa','Thác Tình Yêu','thac-tinh-yeu-sapa','waterfall','["natural","waterfalls","hiking"]','Điểm đi bộ trong khu vực Vườn quốc gia Hoàng Liên.',22.342500,103.772800,120,'curated-sapa-love-waterfall'),
    ('sapa','Nhà thờ Đá Sapa','nha-tho-da-sapa','landmark','["architecture","religion","urban"]','Công trình trung tâm thị trấn, gần quảng trường và chợ đêm.',22.336500,103.842300,45,'curated-sapa-stone-church'),
    ('sapa','Chợ Sapa','cho-sapa','market','["foods","shopping","cultural"]','Khu chợ trung tâm phù hợp mua đồ địa phương và ăn uống.',22.338300,103.844200,75,'curated-sapa-market'),
    ('sapa','Bản Tả Phìn','ban-ta-phin','culture','["cultural","natural","homestay"]','Bản làng người Dao đỏ nổi tiếng với tắm lá thuốc và thủ công.',22.386700,103.833500,180,'curated-sapa-ta-phin'),
    ('sapa','Bản Ý Linh Hồ','ban-y-linh-ho','culture','["cultural","natural","hiking"]','Bản làng trên tuyến trekking xuống thung lũng Mường Hoa.',22.318000,103.857000,150,'curated-sapa-y-linh-ho'),
    ('sapa','Cổng Trời Sapa','cong-troi-sapa','viewpoint','["natural","view_points","road_trip"]','Điểm ngắm mây và núi gần đèo Ô Quy Hồ.',22.351000,103.775000,60,'curated-sapa-heaven-gate'),
    ('sapa','Bản Sín Chải','ban-sin-chai','culture','["cultural","natural","hiking"]','Bản làng gần Cát Cát, phù hợp lịch trình đi bộ nhẹ.',22.325000,103.809000,120,'curated-sapa-sin-chai')
)
INSERT INTO pois
    (destination_id, name, slug, category, kinds, description, lat, lng,
     estimated_duration_min, source, source_ref, is_seeded, fetched_at, raw)
SELECT
    d.id,
    p.name,
    p.slug,
    p.category,
    p.kinds::jsonb,
    p.description,
    p.lat,
    p.lng,
    p.estimated_duration_min,
    'manual_curated',
    p.source_ref,
    TRUE,
    NOW(),
    jsonb_build_object('seed_batch', 'curated_mvp_2026_06', 'destination_slug', p.destination_slug)
FROM poi_seed p
JOIN destinations d ON d.slug = p.destination_slug
ON CONFLICT (destination_id, slug) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    kinds = EXCLUDED.kinds,
    description = EXCLUDED.description,
    lat = EXCLUDED.lat,
    lng = EXCLUDED.lng,
    estimated_duration_min = EXCLUDED.estimated_duration_min,
    source = EXCLUDED.source,
    source_ref = EXCLUDED.source_ref,
    is_seeded = TRUE,
    fetched_at = COALESCE(pois.fetched_at, NOW()),
    updated_at = NOW(),
    raw = pois.raw || EXCLUDED.raw;

SELECT d.slug, d.name, COUNT(p.id) AS poi_count
FROM destinations d
LEFT JOIN pois p ON p.destination_id = d.id
GROUP BY d.slug, d.name, d.popularity_rank
ORDER BY d.popularity_rank;

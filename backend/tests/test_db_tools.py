"""
Kiểm thử các tool đọc dữ liệu BE (grounding) trên PostgreSQL thật.

Tự bỏ qua (skip) nếu không kết nối được DB — để chạy được ở cả môi trường
không có database. Trong Docker: `docker compose exec api python -m unittest tests.test_db_tools -v`
"""
from __future__ import annotations

import os
import unittest


def _db_available() -> bool:
    try:
        import psycopg2
    except Exception:
        return False
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            dbname=os.getenv("DB_NAME", "travel_buddy"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", ""),
            connect_timeout=3,
        )
        conn.close()
        return True
    except Exception:
        return False


DB_UP = _db_available()


@unittest.skipUnless(DB_UP, "PostgreSQL không khả dụng — bỏ qua test tool DB")
class DestinationToolTests(unittest.TestCase):
    def test_get_destination_info_known_city(self):
        from src.tools.travel_db import get_destination_info
        out = get_destination_info.invoke({"destination": "Đà Nẵng"})
        self.assertIsInstance(out, str)
        # Phải gắn nhãn nguồn DB (grounding), không phải bịa.
        self.assertIn("📦 DB", out)
        self.assertIn("Đà Nẵng", out)

    def test_alias_resolution(self):
        # 'hcm' phải map về Hồ Chí Minh qua normalize_city.
        from src.tools.travel_db import get_destination_info
        out = get_destination_info.invoke({"destination": "hcm"})
        self.assertIsInstance(out, str)
        self.assertTrue(len(out) > 20)

    def test_unknown_destination_graceful(self):
        from src.tools.travel_db import get_destination_info
        out = get_destination_info.invoke({"destination": "Zzxqwlandia"})
        # Không có dữ liệu → trả thông báo fallback, KHÔNG raise.
        self.assertIn("⚠️", out)


@unittest.skipUnless(DB_UP, "PostgreSQL không khả dụng")
class AttractionsToolTests(unittest.TestCase):
    def test_list_attractions_returns_pois(self):
        from src.tools.travel_db import list_attractions
        out = list_attractions.invoke({"destination": "Đà Nẵng"})
        self.assertIsInstance(out, str)
        # Hoặc có địa điểm [DB-N], hoặc thông báo chưa có dữ liệu.
        self.assertTrue("DB-1" in out or "⚠️" in out)


@unittest.skipUnless(DB_UP, "PostgreSQL không khả dụng")
class VisaToolTests(unittest.TestCase):
    def test_visa_japan(self):
        from src.tools.travel_db import get_visa_info
        out = get_visa_info.invoke({"country": "Nhật Bản"})
        self.assertIn("Visa", out)
        # Có kết luận rõ ràng: cần / miễn / chưa có dữ liệu.
        self.assertTrue(any(k in out for k in ("CẦN VISA", "MIỄN VISA", "chưa có", "⚠️")))

    def test_visa_by_code(self):
        from src.tools.travel_db import get_visa_info
        out = get_visa_info.invoke({"country": "TH"})
        self.assertIsInstance(out, str)
        self.assertTrue(len(out) > 10)


@unittest.skipUnless(DB_UP, "PostgreSQL không khả dụng")
class MiscToolsTests(unittest.TestCase):
    def test_weather_forecast_no_exception(self):
        from src.tools.travel_db import get_weather_forecast
        out = get_weather_forecast.invoke({"destination": "Đà Nẵng", "days": 5})
        self.assertIsInstance(out, str)
        self.assertTrue(len(out) > 10)

    def test_exchange_rate_no_exception(self):
        from src.tools.travel_db import get_exchange_rate
        out = get_exchange_rate.invoke({"target_currency": "USD"})
        self.assertIsInstance(out, str)
        self.assertTrue("Tỷ giá" in out or "⚠️" in out)

    def test_suggest_packing_no_exception(self):
        from src.tools.travel_db import suggest_packing
        out = suggest_packing.invoke({"trip_type": "beach", "season": "summer", "days": 3})
        self.assertIsInstance(out, str)

    def test_community_posts_no_exception(self):
        from src.tools.travel_db import search_community_posts
        out = search_community_posts.invoke({"destination": "Đà Nẵng"})
        self.assertIsInstance(out, str)


if __name__ == "__main__":
    unittest.main()

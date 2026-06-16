"""
Kiểm thử tầng dữ liệu của router /travel (gọi trực tiếp hàm endpoint, không qua HTTP)
→ xác nhận FE và AI dùng chung nguồn dữ liệu PostgreSQL.

Tự bỏ qua nếu DB không khả dụng.
Chạy: `docker compose exec api python -m unittest tests.test_travel_data_api -v`
"""
from __future__ import annotations

import datetime as dt
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


@unittest.skipUnless(DB_UP, "PostgreSQL không khả dụng — bỏ qua test API dữ liệu")
class TravelDataEndpointTests(unittest.TestCase):
    def test_list_destinations(self):
        from src.api.travel_data import list_destinations
        res = list_destinations(q=None, country=None, limit=5)
        self.assertIn("items", res)
        self.assertIsInstance(res["items"], list)
        if res["items"]:
            self.assertIn("slug", res["items"][0])
            self.assertIn("name", res["items"][0])

    def test_list_airports_domestic(self):
        from src.api.travel_data import list_airports
        res = list_airports(domestic_only=True)
        self.assertIn("items", res)
        self.assertIsInstance(res["items"], list)
        if res["items"]:
            self.assertIn("iata_code", res["items"][0])

    def test_list_airlines(self):
        from src.api.travel_data import list_airlines
        res = list_airlines()
        self.assertIn("items", res)

    def test_list_hotels_for_known_destination(self):
        from src.api.travel_data import list_destinations, list_hotels
        dests = list_destinations(q=None, country=None, limit=1)["items"]
        if not dests:
            self.skipTest("DB chưa có destination để test khách sạn")
        slug = dests[0]["slug"]
        res = list_hotels(destination=slug, checkin=None, checkout=None,
                          adults=2, min_stars=None, limit=5)
        self.assertIn("items", res)
        self.assertIsInstance(res["items"], list)

    def test_list_pois_for_known_destination(self):
        from src.api.travel_data import list_destinations, list_pois
        dests = list_destinations(q=None, country=None, limit=1)["items"]
        if not dests:
            self.skipTest("DB chưa có destination để test POI")
        slug = dests[0]["slug"]
        res = list_pois(destination=slug, category=None, limit=5)
        self.assertIn("items", res)

    def test_community_posts_listing(self):
        from src.api.travel_data import community_posts
        res = community_posts(destination=None, sort="recent", limit=10)
        self.assertIn("items", res)
        self.assertIsInstance(res["items"], list)

    def test_data_consistency_ai_tool_vs_api(self):
        """Cùng một điểm đến, tool AI và API phải tham chiếu cùng slug/tên."""
        from src.api.travel_data import list_destinations
        from src.tools.travel_db import _resolve_destination
        dests = list_destinations(q=None, country=None, limit=1)["items"]
        if not dests:
            self.skipTest("DB rỗng")
        name = dests[0]["name"]
        resolved = _resolve_destination(name)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["slug"], dests[0]["slug"])


if __name__ == "__main__":
    unittest.main()

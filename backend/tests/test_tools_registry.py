"""
Kiểm thử đăng ký tool của agent — đảm bảo đủ tool và metadata hợp lệ.

Chạy:
    cd backend && python -m unittest tests.test_tools_registry -v
"""
from __future__ import annotations

import unittest

from src.tools.travel import ALL_TOOLS
from src.tools.travel_db import DB_TOOLS


EXPECTED_TOOL_NAMES = {
    # Tool nghiệp vụ gốc
    "plan_journey", "search_flights", "search_ground_transport",
    "search_hotels", "calculate_budget", "get_travel_tips",
    # Tool dữ liệu BE (grounding)
    "get_destination_info", "list_attractions", "get_weather_forecast",
    "suggest_packing", "get_visa_info", "get_exchange_rate",
    "search_community_posts",
    # Tiện ích
    "search_images", "web_search",
}


class ToolsRegistryTests(unittest.TestCase):
    def test_all_expected_tools_registered(self):
        names = {t.name for t in ALL_TOOLS}
        missing = EXPECTED_TOOL_NAMES - names
        self.assertFalse(missing, f"Thiếu tool: {missing}")

    def test_db_tools_count(self):
        self.assertEqual(len(DB_TOOLS), 7)

    def test_db_tools_included_in_all_tools(self):
        names = {t.name for t in ALL_TOOLS}
        for t in DB_TOOLS:
            self.assertIn(t.name, names)

    def test_every_tool_has_name_and_description(self):
        for t in ALL_TOOLS:
            self.assertTrue(t.name, "Tool thiếu name")
            self.assertTrue(
                t.description and len(t.description.strip()) >= 10,
                f"Tool '{t.name}' thiếu mô tả đủ ý (LLM cần để chọn tool)",
            )

    def test_no_duplicate_tool_names(self):
        names = [t.name for t in ALL_TOOLS]
        self.assertEqual(len(names), len(set(names)), "Có tool trùng tên")


if __name__ == "__main__":
    unittest.main()

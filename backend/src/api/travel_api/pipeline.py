"""
pipeline.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline chính: chạy tất cả 5 collectors theo thứ tự
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cách dùng:
  # Chạy toàn bộ
  python pipeline.py

  # Chỉ chạy 1 collector
  python pipeline.py --only weather
  python pipeline.py --only exchange_rate
  python pipeline.py --only countries
  python pipeline.py --only opentripmap    # cần OPENTRIPMAP_KEY
  python pipeline.py --only amadeus        # cần AMADEUS_API_KEY

  # Xem tóm tắt DB
  python pipeline.py --summary
"""

import sys, logging, argparse
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


def run_pipeline(only: str = None):
    from db.connection import get_conn, summary

    log.info("=" * 55)
    log.info("🚀 Travel Buddy — Data Pipeline")
    log.info("=" * 55)

    conn = get_conn()

    # ── Bước 0: Collectors không cần API key ────────────────────
    # Chạy trước để có data cơ bản ngay lập tức

    if not only or only == "exchange_rate":
        log.info("\n[1/5] 💱 Exchange Rate (Frankfurter) — không cần key")
        try:
            from collectors.exchange_rate import ExchangeRateCollector
            ExchangeRateCollector().run(conn)
        except Exception as e:
            log.error(f"ExchangeRate lỗi: {e}")

    if not only or only == "countries":
        log.info("\n[2/5] 🌍 Countries (RestCountries) — không cần key")
        try:
            from collectors.countries import CountriesCollector
            CountriesCollector().run(conn)
        except Exception as e:
            log.error(f"Countries lỗi: {e}")

    if not only or only == "weather":
        log.info("\n[3/5] 🌤 Weather (Open-Meteo) — không cần key")
        try:
            from collectors.weather import WeatherCollector
            WeatherCollector().run(conn)
        except Exception as e:
            log.error(f"Weather lỗi: {e}")

    # ── Bước 1: OpenTripMap — cần API key ───────────────────────
    if not only or only == "opentripmap":
        log.info("\n[4/5] 🗺  Điểm tham quan (OpenTripMap) — cần OPENTRIPMAP_KEY")
        try:
            from collectors.opentripmap import OpenTripMapCollector
            OpenTripMapCollector().run(conn)
        except ValueError as e:
            log.warning(f"  ⚠ Bỏ qua: {e}")
        except Exception as e:
            log.error(f"OpenTripMap lỗi: {e}")

    # ── Bước 2: Amadeus — cần API key ───────────────────────────
    if not only or only == "amadeus":
        log.info("\n[5/5] ✈  Vé máy bay (Amadeus) — cần AMADEUS_API_KEY")
        try:
            from collectors.amadeus import AmadeusCollector
            AmadeusCollector().run(conn)
        except ValueError as e:
            log.warning(f"  ⚠ Bỏ qua: {e}")
        except Exception as e:
            log.error(f"Amadeus lỗi: {e}")

    # ── Tóm tắt ─────────────────────────────────────────────────
    summary(conn)
    conn.close()

    log.info("\n✅ Pipeline hoàn thành!")
    log.info("📁 Raw JSON minh chứng: thư mục evidence/")
    log.info("📋 Log chi tiết: pipeline.log")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Travel Buddy Data Pipeline")
    parser.add_argument("--only",    help="Chỉ chạy 1 collector cụ thể")
    parser.add_argument("--summary", action="store_true", help="Chỉ xem tóm tắt DB")
    args = parser.parse_args()

    if args.summary:
        from db.connection import get_conn, summary
        conn = get_conn()
        summary(conn)
        conn.close()
    else:
        run_pipeline(only=args.only)

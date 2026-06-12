"""
Chạy TravelBuddy data pipeline từ root project.

Ví dụ:
  python scripts/run_data_pipeline.py --summary
  python scripts/run_data_pipeline.py --only weather
  python scripts/run_data_pipeline.py --only flights
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_LOG = ROOT / "runtime" / "logs" / "pipeline.log"
PIPELINE_LOG.parent.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("TRAVELBUDDY_PIPELINE_LOG", str(PIPELINE_LOG))

TRAVEL_API = ROOT / "backend" / "src" / "api" / "travel_api"
sys.path.insert(0, str(TRAVEL_API))

from db.connection import get_conn, summary  # noqa: E402
from pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy TravelBuddy data pipeline")
    parser.add_argument("--only", help="Chỉ chạy một collector")
    parser.add_argument("--summary", action="store_true", help="In thống kê database")
    args = parser.parse_args()

    if args.summary:
        conn = get_conn()
        try:
            summary(conn)
        finally:
            conn.close()
        return

    run_pipeline(only=args.only)


if __name__ == "__main__":
    main()

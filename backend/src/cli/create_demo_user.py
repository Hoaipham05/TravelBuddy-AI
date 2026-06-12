"""Create or update a demo login account in PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2

from src.security.auth import hash_password


def _connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "travel_buddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create/update a TravelBuddy demo user.")
    parser.add_argument("--email", default=os.getenv("DEMO_USER_EMAIL", "demo@travelbuddy.local"))
    parser.add_argument("--full-name", default=os.getenv("DEMO_USER_FULL_NAME", "TravelBuddy Demo"))
    parser.add_argument("--password", default=os.getenv("DEMO_USER_PASSWORD"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    email = args.email.strip().lower()
    if not args.password:
        print("Missing password. Pass --password or set DEMO_USER_PASSWORD.", file=sys.stderr)
        return 2

    password_hash = hash_password(args.password)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (full_name, email, password_hash, travel_preferences)
                VALUES (%s, %s, %s, %s::jsonb)
                ON CONFLICT (email)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    password_hash = EXCLUDED.password_hash,
                    updated_at = NOW()
                RETURNING id, email, full_name
                """,
                (args.full_name, email, password_hash, "{}"),
            )
            user_id, user_email, full_name = cur.fetchone()

    print(f"demo_user_id={user_id}")
    print(f"email={user_email}")
    print(f"full_name={full_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

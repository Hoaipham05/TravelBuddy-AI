"""
db/connection.py
Quản lý kết nối PostgreSQL và các hàm helper INSERT/UPSERT.
"""

import os, logging
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)


def get_conn():
    """Trả về psycopg2 connection từ biến môi trường."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "travel_buddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
    )


def upsert_destination(conn, row: dict) -> str:
    """
    Upsert 1 destination, trả về UUID.
    row cần có: name, slug, city, country, lat, lng
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO destinations
            (name, slug, city, country, description, lat, lng,
             images, tags, best_months, avg_rating, review_count)
        VALUES
            (%(name)s, %(slug)s, %(city)s, %(country)s,
             %(description)s, %(lat)s, %(lng)s,
             %(images)s::jsonb, %(tags)s::jsonb,
             %(best_months)s::jsonb, %(avg_rating)s, %(review_count)s)
        ON CONFLICT (slug) DO UPDATE SET
            description  = EXCLUDED.description,
            lat          = EXCLUDED.lat,
            lng          = EXCLUDED.lng,
            tags         = EXCLUDED.tags,
            avg_rating   = EXCLUDED.avg_rating,
            review_count = EXCLUDED.review_count
        RETURNING id
    """, {
        "name":         row.get("name", ""),
        "slug":         row.get("slug", ""),
        "city":         row.get("city", ""),
        "country":      row.get("country", "Vietnam"),
        "description":  row.get("description", ""),
        "lat":          row.get("lat"),
        "lng":          row.get("lng"),
        "images":       row.get("images", "[]"),
        "tags":         row.get("tags", "[]"),
        "best_months":  row.get("best_months", "[]"),
        "avg_rating":   row.get("avg_rating", 0),
        "review_count": row.get("review_count", 0),
    })
    dest_id = cur.fetchone()[0]
    conn.commit()
    return str(dest_id)


def upsert_hotel(conn, row: dict) -> str:
    """Upsert 1 hotel theo (destination_id, name)."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO hotels
            (destination_id, name, stars, price_per_night,
             address, lat, lng, amenities, images, avg_rating)
        VALUES
            (%(destination_id)s, %(name)s, %(stars)s, %(price_per_night)s,
             %(address)s, %(lat)s, %(lng)s,
             %(amenities)s::jsonb, %(images)s::jsonb, %(avg_rating)s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, {
        "destination_id":  row["destination_id"],
        "name":            row.get("name", ""),
        "stars":           row.get("stars", 3),
        "price_per_night": row.get("price_per_night", 0),
        "address":         row.get("address", ""),
        "lat":             row.get("lat"),
        "lng":             row.get("lng"),
        "amenities":       row.get("amenities", "[]"),
        "images":          row.get("images", "[]"),
        "avg_rating":      row.get("avg_rating", 0),
    })
    result = cur.fetchone()
    conn.commit()
    return str(result[0]) if result else ""


def upsert_flight(conn, row: dict) -> str:
    """Upsert 1 flight theo (flight_no, depart_at)."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO flights
            (destination_id, airline, flight_no, origin, destination,
             price, cabin_class, depart_at, arrive_at, monthly_prices, source)
        VALUES
            (%(destination_id)s, %(airline)s, %(flight_no)s,
             %(origin)s, %(destination)s, %(price)s, %(cabin_class)s,
             %(depart_at)s, %(arrive_at)s,
             %(monthly_prices)s::jsonb, %(source)s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, {
        "destination_id": row.get("destination_id"),
        "airline":        row.get("airline", ""),
        "flight_no":      row.get("flight_no", ""),
        "origin":         row.get("origin", ""),
        "destination":    row.get("destination", ""),
        "price":          row.get("price", 0),
        "cabin_class":    row.get("cabin_class", "economy"),
        "depart_at":      row.get("depart_at"),
        "arrive_at":      row.get("arrive_at"),
        "monthly_prices": row.get("monthly_prices", "{}"),
        "source":         row.get("source", "api"),
    })
    result = cur.fetchone()
    conn.commit()
    return str(result[0]) if result else ""


def get_dest_id(conn, slug: str) -> str | None:
    """Lấy destination UUID theo slug."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM destinations WHERE slug = %s", (slug,))
    row = cur.fetchone()
    return str(row[0]) if row else None


def summary(conn):
    """In số bản ghi mỗi bảng."""
    cur = conn.cursor()
    print("\n📊 Tổng bản ghi trong DB:")
    print("-" * 35)
    for tbl in ["destinations", "hotels", "flights", "users", "trips", "reviews"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"  {tbl:<20} {cur.fetchone()[0]:>6} rows")
    print("-" * 35)

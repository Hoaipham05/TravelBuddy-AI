"""
src/tools/travel_db.py — Tool đọc dữ liệu có cấu trúc từ PostgreSQL.

Mục tiêu: grounding TravelBuddy AI vào ĐÚNG dữ liệu mà frontend đang hiển thị
(/api/travel/*), thay vì để model bịa. Mỗi tool ưu tiên trả số liệu thật từ DB;
khi DB chưa có dữ liệu, trả thông báo rõ ràng để agent fallback sang web_search.

Các tool ở đây bổ sung cho src/tools/travel.py (vé/khách sạn/ngân sách):
  • get_destination_info   → giới thiệu điểm đến + ảnh (Phần 1 trong câu trả lời 5 phần)
  • list_attractions       → POIs cho gợi ý lịch trình (Phần 2)
  • get_weather_forecast   → dự báo thời tiết theo ngày
  • suggest_packing        → gợi ý hành trang theo mùa/loại chuyến/số ngày
  • get_visa_info          → quy định visa cho hộ chiếu VN
  • get_exchange_rate      → tỷ giá ngoại tệ
  • search_community_posts → bài chia sẻ thực tế từ cộng đồng

Toàn bộ tool đọc cùng database với router /travel (cùng schema, cùng cache TTL),
nên dữ liệu AI trả về luôn khớp với trang Lập kế hoạch / Vé / Khách sạn / Cộng đồng.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from langchain_core.tools import tool

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover
    psycopg2 = None
    RealDictCursor = None

from src.database import normalize_city


# ─────────────────────────────────────────────────────────────────────────────
#  DB helpers (self-contained — trả [] khi lỗi thay vì raise, để agent fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _db_enabled() -> bool:
    return os.getenv("TRAVELBUDDY_DATA_MODE", "auto").strip().lower() in {"auto", "postgres", "db"}


def _conn():
    if not psycopg2 or not _db_enabled():
        return None
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            dbname=os.getenv("DB_NAME", "travel_buddy"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", ""),
            cursor_factory=RealDictCursor,
            connect_timeout=3,
            options="-c timezone=Asia/Ho_Chi_Minh",
        )
    except Exception:
        return None


def _fetch_all(sql: str, params: dict | None = None) -> list[dict]:
    conn = _conn()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or {})
                return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _fetch_one(sql: str, params: dict | None = None) -> dict | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _fmt_vnd(amount) -> str:
    try:
        return f"{int(amount):,.0f}đ".replace(",", ".")
    except Exception:
        return str(amount)


# ─────────────────────────────────────────────────────────────────────────────
#  Resolver: tên/biệt danh thành phố → bản ghi destination (slug)
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_destination(query: str) -> dict | None:
    """Tìm destination khớp nhất với chuỗi người dùng nhập (có dấu/không dấu)."""
    q = (query or "").strip()
    if not q:
        return None
    city_std = normalize_city(q)  # 'hcm' → 'Hồ Chí Minh', 'da nang' → 'Đà Nẵng'

    return _fetch_one(
        """
        SELECT d.id, d.slug, d.name, d.city, d.province, d.country_code, d.country_name,
               d.description, d.tags, d.best_months, d.avg_rating, d.review_count,
               d.iata_city_code,
               img.url AS image_url, img.thumbnail_url AS image_thumb,
               img.attribution AS image_attr
        FROM destinations d
        LEFT JOIN LATERAL (
            SELECT url, thumbnail_url, attribution
            FROM destination_images
            WHERE destination_id = d.id
            ORDER BY is_primary DESC, sort_order ASC
            LIMIT 1
        ) img ON TRUE
        WHERE d.slug = %(slug)s
           OR unaccent(lower(d.name)) = unaccent(lower(%(std)s))
           OR unaccent(lower(d.city)) = unaccent(lower(%(std)s))
           OR unaccent(lower(d.name)) LIKE unaccent(lower(%(like)s))
           OR unaccent(lower(d.city)) LIKE unaccent(lower(%(like)s))
        ORDER BY
            (d.slug = %(slug)s) DESC,
            (unaccent(lower(d.name)) = unaccent(lower(%(std)s))) DESC,
            COALESCE(d.popularity_rank, 999) ASC,
            d.avg_rating DESC
        LIMIT 1
        """,
        {
            "slug": q.lower().replace(" ", "-"),
            "std": city_std,
            "like": f"%{city_std}%",
        },
    )


def _images_json_block(dest: dict, extra: list[dict] | None = None) -> str:
    """Phát khối IMAGES_JSON để UI render gallery (cùng format search_images)."""
    images: list[dict] = []
    if dest.get("image_url"):
        images.append({
            "url": dest["image_url"],
            "thumb": dest.get("image_thumb") or dest["image_url"],
            "title": dest.get("name") or "",
            "source": dest.get("image_attr") or "",
        })
    for it in (extra or []):
        if it.get("url"):
            images.append(it)
    if not images:
        return ""
    return "🖼️ Ảnh điểm đến (DB):\nIMAGES_JSON:" + json.dumps(images, ensure_ascii=False)


def _no_data(name: str, kind: str) -> str:
    return (
        f"⚠️ DB nội bộ chưa có dữ liệu {kind} cho '{name}'. "
        f"Hãy dùng web_search/get_travel_tips và kèm trích dẫn [N]."
    )


# WMO weather code → mô tả tiếng Việt + emoji
_WMO = {
    0: ("☀️", "Trời quang"), 1: ("🌤️", "Ít mây"), 2: ("⛅", "Mây rải rác"),
    3: ("☁️", "Nhiều mây"), 45: ("🌫️", "Sương mù"), 48: ("🌫️", "Sương mù đóng băng"),
    51: ("🌦️", "Mưa phùn nhẹ"), 53: ("🌦️", "Mưa phùn"), 55: ("🌧️", "Mưa phùn dày"),
    61: ("🌧️", "Mưa nhẹ"), 63: ("🌧️", "Mưa vừa"), 65: ("🌧️", "Mưa to"),
    71: ("🌨️", "Tuyết nhẹ"), 73: ("🌨️", "Tuyết vừa"), 75: ("❄️", "Tuyết dày"),
    80: ("🌦️", "Mưa rào nhẹ"), 81: ("🌧️", "Mưa rào"), 82: ("⛈️", "Mưa rào lớn"),
    95: ("⛈️", "Giông"), 96: ("⛈️", "Giông kèm mưa đá"), 99: ("⛈️", "Giông mạnh"),
}


# ═════════════════════════════════════════════════════════════════════════════
#  TOOLS
# ═════════════════════════════════════════════════════════════════════════════

@tool
def get_destination_info(destination: str) -> str:
    """
    Lấy thông tin giới thiệu điểm đến từ DB nội bộ TravelBuddy: mô tả, thẻ chủ đề,
    thời điểm lý tưởng (best_months), điểm đánh giá cộng đồng và ảnh đại diện.

    Dùng khi user hỏi "giới thiệu về <điểm đến>", "<điểm đến> có gì", "khi nào nên đi",
    hoặc làm PHẦN 1 (giới thiệu) khi tư vấn chuyến đi đầy đủ.

    Args:
        destination: Tên điểm đến (VD: 'Đà Nẵng', 'Phú Quốc', 'da lat', 'hcm')
    """
    dest = _resolve_destination(destination)
    if not dest:
        return _no_data(destination, "điểm đến")

    tags = dest.get("tags") or []
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    best = dest.get("best_months") or []
    if isinstance(best, str):
        try:
            best = json.loads(best)
        except Exception:
            best = []

    lines = [
        f"📍 {dest['name']} ({dest.get('province') or dest.get('country_name') or ''})  [📦 DB]",
        "─" * 56,
    ]
    if dest.get("description"):
        lines.append(dest["description"].strip())
    meta = []
    if dest.get("avg_rating"):
        meta.append(f"⭐ {float(dest['avg_rating']):.1f}/5 ({dest.get('review_count', 0)} đánh giá)")
    if best:
        meta.append("🗓️ Thời điểm lý tưởng: tháng " + ", ".join(str(m) for m in best))
    if tags:
        meta.append("🏷️ " + " · ".join(str(t) for t in tags[:8]))
    if dest.get("iata_city_code"):
        meta.append(f"✈️ Mã sân bay: {dest['iata_city_code']}")
    if meta:
        lines.append("")
        lines.extend(meta)
    lines.append("\n📦 NGUỒN: DB NỘI BỘ TRAVELBUDDY — dùng đúng thông tin trên, không bịa thêm.")

    img = _images_json_block(dest)
    out = "\n".join(lines)
    return out + ("\n\n" + img if img else "")


@tool
def list_attractions(destination: str, category: Optional[str] = None, limit: int = 12) -> str:
    """
    Liệt kê địa điểm tham quan (POI) tại một điểm đến từ DB nội bộ: tên, loại hình,
    thời gian tham quan ước tính, phí vào cửa, đánh giá. Dùng để gợi ý LỊCH TRÌNH
    (PHẦN 2) hoặc khi user hỏi "có gì chơi ở <điểm đến>", "địa điểm nổi tiếng".

    Args:
        destination: Tên điểm đến (VD: 'Hội An', 'Đà Nẵng')
        category   : Lọc theo loại (vd: 'beach', 'historic', 'nature', 'museum') — tùy chọn
        limit      : Số địa điểm tối đa (mặc định 12)
    """
    dest = _resolve_destination(destination)
    if not dest:
        return _no_data(destination, "địa điểm tham quan")

    params: dict[str, Any] = {"slug": dest["slug"], "limit": max(1, min(limit, 30))}
    cat_clause = ""
    if category:
        cat_clause = "AND (p.category ILIKE %(cat)s OR p.kinds::text ILIKE %(cat)s)"
        params["cat"] = f"%{category}%"

    rows = _fetch_all(
        f"""
        SELECT p.name, p.category, p.description, p.estimated_duration_min,
               p.entrance_fee_amount, p.currency, p.avg_rating, p.address
        FROM pois p
        JOIN destinations d ON d.id = p.destination_id
        WHERE d.slug = %(slug)s {cat_clause}
        ORDER BY p.avg_rating DESC NULLS LAST, p.name
        LIMIT %(limit)s
        """,
        params,
    )
    if not rows:
        return _no_data(dest["name"], "địa điểm tham quan")

    lines = [
        f"🎯 Địa điểm nổi bật tại {dest['name']}  [📦 DB] ({len(rows)} điểm)",
        "─" * 56,
    ]
    for i, p in enumerate(rows, 1):
        bits = []
        if p.get("avg_rating"):
            bits.append(f"⭐{float(p['avg_rating']):.1f}")
        if p.get("estimated_duration_min"):
            h = p["estimated_duration_min"] / 60
            bits.append(f"⏱~{h:.1f}h" if h % 1 else f"⏱~{int(h)}h")
        fee = p.get("entrance_fee_amount")
        if fee is not None:
            bits.append("💰 Miễn phí" if float(fee) == 0 else f"💰 {_fmt_vnd(fee)}")
        cat = f" · {p['category']}" if p.get("category") else ""
        lines.append(f"  [DB-{i}] {p['name']}{cat}")
        if bits:
            lines.append("          " + "  |  ".join(bits))
        if p.get("address"):
            lines.append(f"          📍 {p['address']}")
    lines.append("\n📦 NGUỒN: DB NỘI BỘ — chỉ dùng đúng các địa điểm [DB-N] trên.")
    return "\n".join(lines)


@tool
def get_weather_forecast(destination: str, days: int = 7) -> str:
    """
    Dự báo thời tiết theo ngày tại điểm đến từ DB nội bộ (cache Open-Meteo):
    nhiệt độ cao/thấp, tình trạng trời, xác suất mưa, điểm thuận lợi du lịch.

    Dùng khi user hỏi "thời tiết <điểm đến>", "tháng này mưa không", "có nên đi
    biển không", hoặc bổ trợ khi tư vấn chọn ngày đi.

    Args:
        destination: Tên điểm đến (VD: 'Đà Nẵng', 'Sa Pa')
        days       : Số ngày dự báo (1–16, mặc định 7)
    """
    dest = _resolve_destination(destination)
    if not dest:
        return _no_data(destination, "thời tiết")

    rows = _fetch_all(
        """
        SELECT wdf.forecast_date, wdf.weather_code, wdf.temp_max_c, wdf.temp_min_c,
               wdf.precipitation_probability_max, wdf.travel_score
        FROM destinations d
        JOIN weather_daily_forecasts wdf ON wdf.destination_id = d.id
        JOIN weather_cache wc ON wc.id = wdf.weather_cache_id
        WHERE d.slug = %(slug)s AND wc.expires_at > NOW()
        ORDER BY wdf.forecast_date
        LIMIT %(days)s
        """,
        {"slug": dest["slug"], "days": max(1, min(days, 16))},
    )
    if not rows:
        return (
            f"⚠️ DB chưa có cache thời tiết còn hạn cho {dest['name']}. "
            "Có thể gọi web_search hoặc gợi ý user xem mục Vé máy bay (có thời tiết theo ngày)."
        )

    lines = [f"🌤️ Dự báo thời tiết {dest['name']}  [📦 DB]", "─" * 56]
    for r in rows:
        emoji, desc = _WMO.get(r.get("weather_code"), ("🌡️", "—"))
        tmax = f"{float(r['temp_max_c']):.0f}°" if r.get("temp_max_c") is not None else "?"
        tmin = f"{float(r['temp_min_c']):.0f}°" if r.get("temp_min_c") is not None else "?"
        rain = r.get("precipitation_probability_max")
        rain_s = f" · 🌧️ {rain}%" if rain is not None else ""
        score = r.get("travel_score")
        score_s = f" · 👍 {score}/100" if score is not None else ""
        lines.append(f"  {r['forecast_date']}  {emoji} {desc}  {tmin}–{tmax}C{rain_s}{score_s}")
    lines.append("\n📦 NGUỒN: DB NỘI BỘ (cache Open-Meteo).")
    return "\n".join(lines)


@tool
def suggest_packing(trip_type: str, season: str, days: int) -> str:
    """
    Gợi ý danh sách hành trang theo loại chuyến đi, mùa và số ngày, lấy từ template
    chuẩn trong DB nội bộ (giống mục Hành trang ở trang Lập kế hoạch).

    Args:
        trip_type: Loại chuyến — 'beach' | 'mountain' | 'city' | 'general' ...
        season   : Mùa — 'summer' | 'winter' | 'spring' | 'autumn' | 'rainy' | 'dry'
        days     : Số ngày đi (1–60)
    """
    rows = _fetch_all(
        """
        SELECT pt.name,
               json_agg(jsonb_build_object(
                   'category', pti.category, 'item_name', pti.item_name,
                   'quantity_rule', pti.quantity_rule,
                   'is_default_checked', pti.is_default_checked
               ) ORDER BY pti.category, pti.sort_order)
               FILTER (WHERE pti.id IS NOT NULL) AS items
        FROM packing_templates pt
        LEFT JOIN packing_template_items pti ON pti.template_id = pt.id
        WHERE pt.is_active = TRUE
          AND pt.trip_type IN (%(tt)s, 'general')
          AND pt.season = %(season)s
          AND pt.day_min <= %(days)s
          AND (pt.day_max IS NULL OR pt.day_max >= %(days)s)
        GROUP BY pt.id
        ORDER BY pt.priority ASC
        """,
        {"tt": trip_type, "season": season, "days": max(1, min(days, 60))},
    )
    if not rows:
        return _no_data(f"{trip_type}/{season}/{days} ngày", "hành trang")

    cat_label = {
        "clothing": "👗 Quần áo", "accessories": "🎒 Phụ kiện", "health": "🧴 Sức khoẻ/Vệ sinh",
        "documents": "📄 Giấy tờ", "electronics": "🔌 Điện tử",
    }
    buckets: dict[str, list[str]] = {}
    for tpl in rows:
        for it in (tpl.get("items") or []):
            label = cat_label.get(it["category"], it["category"])
            qty = f" ({it['quantity_rule']})" if it.get("quantity_rule") else ""
            check = "☑" if it.get("is_default_checked") else "☐"
            buckets.setdefault(label, []).append(f"{check} {it['item_name']}{qty}")

    lines = [f"📦 Gợi ý hành trang — {trip_type}, {season}, {days} ngày  [📦 DB]", "─" * 56]
    for label, items in buckets.items():
        lines.append(f"\n{label}")
        lines.extend("  " + x for x in items)
    lines.append("\n📦 NGUỒN: DB NỘI BỘ (packing template).")
    return "\n".join(lines)


@tool
def get_visa_info(country: str) -> str:
    """
    Tra cứu quy định visa cho hộ chiếu Việt Nam đến một quốc gia, từ DB nội bộ.

    Dùng khi user hỏi "đi <nước> có cần visa không", "ở được bao nhiêu ngày".

    Args:
        country: Tên nước hoặc mã quốc gia 2 ký tự (VD: 'Nhật Bản', 'Thái Lan', 'JP', 'TH')
    """
    c = (country or "").strip()
    row = _fetch_one(
        """
        SELECT c.code, c.name_vn, c.name_en, c.capital, c.calling_code, c.currencies,
               vr.visa_required, vr.visa_type, vr.max_stay_days, vr.note,
               vr.source_url, vr.verified_at
        FROM countries c
        LEFT JOIN country_visa_rules vr
            ON vr.destination_country_code = c.code AND vr.passport_country_code = 'VN'
        WHERE upper(c.code) = upper(%(c)s)
           OR unaccent(lower(c.name_vn)) LIKE unaccent(lower(%(like)s))
           OR lower(c.name_en) LIKE lower(%(like)s)
        ORDER BY (upper(c.code) = upper(%(c)s)) DESC
        LIMIT 1
        """,
        {"c": c, "like": f"%{c}%"},
    )
    if not row:
        return _no_data(country, "visa")

    name = row.get("name_vn") or row.get("name_en")
    lines = [f"🛂 Visa cho hộ chiếu 🇻🇳 → {name} ({row['code']})  [📦 DB]", "─" * 56]
    vr = row.get("visa_required")
    if vr is None:
        lines.append("ℹ️ DB chưa có quy định visa cụ thể — hãy xác minh qua web_search và kèm [N].")
    elif vr is False:
        days = f" tối đa {row['max_stay_days']} ngày" if row.get("max_stay_days") else ""
        lines.append(f"✅ MIỄN VISA{days}." + (f" ({row['visa_type']})" if row.get("visa_type") else ""))
    else:
        days = f", lưu trú tối đa {row['max_stay_days']} ngày" if row.get("max_stay_days") else ""
        lines.append(f"⚠️ CẦN VISA{days}." + (f" Loại: {row['visa_type']}." if row.get("visa_type") else ""))
    if row.get("note"):
        lines.append(f"📝 {row['note']}")
    if row.get("verified_at"):
        lines.append(f"🕓 Cập nhật: {row['verified_at']}")
    lines.append("\n⚠️ Quy định visa có thể thay đổi — luôn khuyên user kiểm tra với ĐSQ/LSQ trước khi đi.")
    return "\n".join(lines)


@tool
def get_exchange_rate(target_currency: str, base_currency: str = "VND") -> str:
    """
    Tra cứu tỷ giá ngoại tệ từ DB nội bộ (cache). Dùng khi user hỏi quy đổi tiền tệ,
    "1 USD bằng bao nhiêu", "đổi tiền đi Thái".

    Args:
        target_currency: Mã tiền cần quy đổi (VD: 'USD', 'THB', 'JPY')
        base_currency  : Mã tiền gốc (mặc định 'VND')
    """
    row = _fetch_one(
        """
        SELECT base_currency, target_currency, rate, rate_date, source
        FROM exchange_rate_cache
        WHERE base_currency = %(base)s AND target_currency = %(tgt)s AND expires_at > NOW()
        ORDER BY fetched_at DESC LIMIT 1
        """,
        {"base": base_currency.upper(), "tgt": target_currency.upper()},
    )
    if not row:
        # thử chiều ngược lại
        rev = _fetch_one(
            """
            SELECT base_currency, target_currency, rate, rate_date, source
            FROM exchange_rate_cache
            WHERE base_currency = %(tgt)s AND target_currency = %(base)s AND expires_at > NOW()
            ORDER BY fetched_at DESC LIMIT 1
            """,
            {"base": base_currency.upper(), "tgt": target_currency.upper()},
        )
        if rev and rev.get("rate"):
            inv = 1 / float(rev["rate"])
            return (
                f"💱 Tỷ giá (DB): 1 {base_currency.upper()} ≈ {inv:.6f} {target_currency.upper()} "
                f"(suy ra từ chiều ngược lại, ngày {rev.get('rate_date')})  [📦 DB]"
            )
        return _no_data(f"{base_currency}/{target_currency}", "tỷ giá")

    return (
        f"💱 Tỷ giá (DB): 1 {row['base_currency']} = {float(row['rate']):,.4f} {row['target_currency']} "
        f"(ngày {row.get('rate_date')}, nguồn {row.get('source')})  [📦 DB]"
    )


@tool
def search_community_posts(destination: str, limit: int = 5) -> str:
    """
    Lấy bài chia sẻ thực tế của cộng đồng TravelBuddy về một điểm đến: trải nghiệm,
    đánh giá, chi phí thật. Dùng để trích dẫn kinh nghiệm người đi trước.

    Args:
        destination: Tên điểm đến
        limit      : Số bài tối đa (mặc định 5)
    """
    dest = _resolve_destination(destination)
    if not dest:
        return _no_data(destination, "bài cộng đồng")

    rows = _fetch_all(
        """
        SELECT r.rating, r.content, r.helpful_count, r.created_at,
               u.full_name AS author_name
        FROM reviews r
        JOIN users u ON u.id = r.user_id
        WHERE r.destination_id = %(did)s
        ORDER BY r.helpful_count DESC, r.created_at DESC
        LIMIT %(limit)s
        """,
        {"did": dest["id"], "limit": max(1, min(limit, 10))},
    )
    if not rows:
        return f"ℹ️ Cộng đồng chưa có bài chia sẻ nào về {dest['name']}."

    lines = [f"👥 Cộng đồng chia sẻ về {dest['name']}  [📦 DB] ({len(rows)} bài)", "─" * 56]
    for r in rows:
        stars = "⭐" * int(round(float(r.get("rating") or 0)))
        content = (r.get("content") or "").strip().replace("\n", " ")
        if len(content) > 220:
            content = content[:220] + "…"
        lines.append(f"\n  {stars} — {r.get('author_name', 'Ẩn danh')} (👍 {r.get('helpful_count', 0)})")
        lines.append(f"  “{content}”")
    lines.append("\n📦 NGUỒN: cộng đồng TravelBuddy (DB nội bộ).")
    return "\n".join(lines)


# ── Export ───────────────────────────────────────────────────────────────────
DB_TOOLS = [
    get_destination_info,
    list_attractions,
    get_weather_forecast,
    suggest_packing,
    get_visa_info,
    get_exchange_rate,
    search_community_posts,
]

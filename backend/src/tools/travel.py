"""
src/tools/travel.py – Travel tools với hỗ trợ hành trình đa chặng.

Cải tiến so với bản cũ:
  ✅ Detect thành phố không có sân bay → tự động tính chặng nối
  ✅ Tool search_ground_transport (bus / tàu hoả / phà)
  ✅ Tool plan_journey — lập kế hoạch toàn trình thông minh
  ✅ Web fetch URLs được hiển thị rõ trong output
  ✅ Chain-of-thought routing: HY → HN (xe) → fly HN → PQC
"""
from __future__ import annotations

import re
from typing import Optional

from langchain_core.tools import tool

from src.config import SEARCH_MODE_DEFAULT
from src.database import (
    lookup_flights, lookup_hotels, normalize_city,
    get_known_cities, AIRPORT_CITIES,
)
from src.database_additions import (
    NEAREST_AIRPORT_CITY, lookup_ground_transport, get_nearest_airport, get_airport_candidates,
)
from src.tools.web_search import web_search as _web_search
from src.tools.image_search import search_images

_ENRICH = SEARCH_MODE_DEFAULT in ("hybrid", "on")


def _fmt_vnd(amount: int) -> str:
    return f"{amount:,.0f}đ".replace(",", ".")


def _stars(n: int) -> str:
    return "⭐" * n


def _fmt_duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h{m:02d}m" if m else f"{h}h"


def _parse_duration_h(dur_str: str) -> float:
    """Parse '2h15m' → 2.25"""
    if not dur_str:
        return 2.0
    if "h" in dur_str and "m" in dur_str:
        parts = dur_str.split("h")
        return float(parts[0]) + float(parts[1].replace("m", "")) / 60
    elif "h" in dur_str:
        return float(dur_str.replace("h", ""))
    return 2.0


def _format_relay_transit(city: str, relay_info: dict) -> str:
    airport_city = relay_info["airport_city"]
    distance_km = relay_info["distance_km"]
    options = relay_info["options"]

    lines = [
        f"🚌 CHẶNG 1 — {city} → {airport_city} (sân bay gần nhất, {distance_km}km)",
        "─" * 54,
    ]
    type_icons = {
        "bus_limousine": "🚐", "xe_khach": "🚌", "xe_buyt": "🚌",
        "taxi_grab": "🚕", "tau_hoa": "🚂", "grab_xe_om": "🛵",
    }
    for i, opt in enumerate(options, 1):
        icon = type_icons.get(opt["type"], "🚗")
        duration_min = opt.get("duration_min", opt.get("duration_h", 0) * 60)
        duration = _fmt_duration(int(duration_min))

        if "price_vnd" in opt:
            price_str = _fmt_vnd(opt["price_vnd"])
        elif "price_vnd_range" in opt:
            lo, hi = opt["price_vnd_range"]
            price_str = f"{_fmt_vnd(lo)} – {_fmt_vnd(hi)}"
        else:
            price_str = "?"

        note = opt.get("note", "")
        line = f"  [{i}] {icon} {opt.get('operator', opt['type'])}"
        line += f"\n       ⏱ {duration}  💰 {price_str}"
        if note:
            line += f"\n       📝 {note}"
        lines.append(line)

    lines.append(f"\n  → Sau khi tới {airport_city}: tiếp tục ✈️ chặng bay bên dưới.")
    return "\n".join(lines)


def _destination_image_block(destination: str, hint: str = "") -> str:
    """Attach an IMAGES_JSON block so UI can render destination photos inline."""
    if not _ENRICH:
        return ""

    query = " ".join(p for p in [destination, hint, "du lịch", "ảnh đẹp"] if p).strip()
    try:
        img_out = search_images.invoke({"query": query, "k": 4})
    except Exception as exc:
        return f"🖼️ Ảnh điểm đến: ⚠️ Lỗi tìm ảnh ({exc})"

    if not img_out:
        return ""
    if "IMAGES_JSON:" in img_out:
        return "🖼️ Ảnh điểm đến:\n" + img_out
    return "🖼️ Ảnh điểm đến: " + img_out


def _relay_option_metrics(relay_info: dict | None, optimize: str) -> dict:
    if not relay_info:
        return {"duration_min": 0, "cost_min": 0, "cost_max": 0, "label": ""}

    options = relay_info.get("options", [])
    if not options:
        duration_min = int(relay_info.get("distance_km", 0) / 45 * 60)
        return {
            "duration_min": duration_min,
            "cost_min": 120_000,
            "cost_max": 220_000,
            "label": f"xe liên tỉnh tới {relay_info.get('airport_city', '')}",
        }

    def _o_cost_min(opt: dict) -> int:
        if "price_vnd" in opt:
            return int(opt["price_vnd"])
        lo, _ = opt.get("price_vnd_range", (200_000, 350_000))
        return int(lo)

    def _o_cost_max(opt: dict) -> int:
        if "price_vnd" in opt:
            return int(opt["price_vnd"])
        _, hi = opt.get("price_vnd_range", (200_000, 350_000))
        return int(hi)

    def _o_duration(opt: dict) -> int:
        return int(opt.get("duration_min", opt.get("duration_h", 0) * 60))

    if optimize == "fastest":
        best = min(options, key=_o_duration)
    else:
        best = min(options, key=_o_cost_min)

    return {
        "duration_min": _o_duration(best),
        "cost_min": _o_cost_min(best),
        "cost_max": _o_cost_max(best),
        "label": best.get("operator", best.get("type", "xe liên tỉnh")),
    }


def _airport_candidates_for_city(city_std: str) -> list[dict]:
    cands = get_airport_candidates(city_std)
    if cands:
        return cands
    return [{"airport_city": city_std, "distance_km": 0, "options": []}]


def _normalize_pref(pref: str) -> str:
    p = (pref or "all").strip().lower()
    if p in {"min_cost", "cost", "cheap", "cheapest"}:
        return "cheapest"
    if p in {"min_time", "time", "quick", "fast", "fastest"}:
        return "fastest"
    if p in {"fewest_segments", "min_segments", "segments", "ít chặng", "it chang"}:
        return "fewest_segments"
    if p in {"balanced", "can_bang", "can bang", "all"}:
        return "balanced"
    return "balanced"


def _sorted_flight_options(options: list[dict], pref: str) -> list[dict]:
    if pref == "cheapest":
        return sorted(options, key=lambda x: (x["cost_min"], x["total_minutes"], x["segments"]))
    if pref == "fastest":
        return sorted(options, key=lambda x: (x["total_minutes"], x["cost_min"], x["segments"]))
    if pref in {"fewest_segments", "min_segments", "segments"}:
        return sorted(options, key=lambda x: (x["segments"], x["cost_min"], x["total_minutes"]))

    # balanced: scale cost/time/segments về [0,1] rồi tính điểm tổng hợp
    costs = [x["cost_min"] for x in options]
    times = [x["total_minutes"] for x in options]
    segs = [x["segments"] for x in options]
    min_c, max_c = min(costs), max(costs)
    min_t, max_t = min(times), max(times)
    min_s, max_s = min(segs), max(segs)

    def _norm(v: int, lo: int, hi: int) -> float:
        return 0.0 if hi == lo else (v - lo) / (hi - lo)

    def _score(x: dict) -> float:
        c = _norm(x["cost_min"], min_c, max_c)
        t = _norm(x["total_minutes"], min_t, max_t)
        s = _norm(x["segments"], min_s, max_s)
        return c * 0.45 + t * 0.45 + s * 0.10

    return sorted(options, key=lambda x: (_score(x), x["cost_min"], x["total_minutes"], x["segments"]))


def _build_flight_itineraries(o_std: str, d_std: str, pref: str) -> list[dict]:
    origin_cands = _airport_candidates_for_city(o_std)
    dest_cands = _airport_candidates_for_city(d_std)

    itineraries: list[dict] = []
    for oc in origin_cands:
        for dc in dest_cands:
            o_air = oc["airport_city"]
            d_air = dc["airport_city"]
            flights = lookup_flights(o_air, d_air)
            if not flights:
                continue

            relay_o = _relay_option_metrics(None if o_air == o_std else oc, pref)
            relay_d = _relay_option_metrics(None if d_air == d_std else dc, pref)

            cheapest = min(flights, key=lambda f: f["price"])
            priciest = max(flights, key=lambda f: f["price"])
            fastest_flight = min(flights, key=lambda f: _parse_duration_h(f.get("duration", "2h")))
            flight_pick = fastest_flight if pref == "fastest" else cheapest

            flight_minutes = int(_parse_duration_h(flight_pick.get("duration", "2h")) * 60)
            total_minutes = relay_o["duration_min"] + flight_minutes + 60 + relay_d["duration_min"]
            segments = 1 + (1 if o_air != o_std else 0) + (1 if d_air != d_std else 0)

            itineraries.append({
                "origin_air": o_air,
                "dest_air": d_air,
                "relay_o": relay_o,
                "relay_d": relay_d,
                "flight": flight_pick,
                "cost_min": relay_o["cost_min"] + cheapest["price"] + relay_d["cost_min"],
                "cost_max": relay_o["cost_max"] + priciest["price"] + relay_d["cost_max"],
                "total_minutes": total_minutes,
                "segments": segments,
            })

    return itineraries


# ─────────────────────────────────────────────────────────────────────────────
@tool
def search_flights(origin: str, destination: str, travel_date: Optional[str] = None, optimize: str = "balanced") -> str:
    """
    Tìm chuyến bay giữa hai thành phố Việt Nam.

    QUAN TRỌNG: Nếu origin không có sân bay (VD: Hưng Yên, Hải Dương,
    Bắc Ninh), tool tự động tính chặng xe đến sân bay gần nhất trước.
    Gọi tool này khi user hỏi về vé máy bay hoặc muốn đi bằng máy bay.

    Args:
        origin     : Điểm khởi hành
        destination: Điểm đến
        travel_date: Ngày đi mong muốn (vd: '2026-04-20' hoặc '20/04/2026')
        optimize   : 'balanced' | 'cheapest' | 'fastest' | 'fewest_segments'
    """
    o_std = normalize_city(origin)
    d_std = normalize_city(destination)
    output_parts: list[str] = []
    pref = _normalize_pref(optimize)

    itineraries = _build_flight_itineraries(o_std, d_std, pref)
    date_hint = (travel_date or "").strip()

    if itineraries:
        ordered = _sorted_flight_options(itineraries, pref)
        best = ordered[0]

        # ── Relay note (cities without direct airport) ──────────────────────
        relay_lines = []
        if best["origin_air"] != o_std:
            relay_lines.append(
                f"🚐 Chặng nối: {o_std} → {best['origin_air']} "
                f"({best['relay_o']['label']}, {_fmt_duration(best['relay_o']['duration_min'])}, "
                f"~{_fmt_vnd(best['relay_o']['cost_min'])})"
            )
        if best["dest_air"] != d_std:
            relay_lines.append(
                f"🚕 Chặng cuối: {best['dest_air']} → {d_std} "
                f"({_fmt_duration(best['relay_d']['duration_min'])}, "
                f"~{_fmt_vnd(best['relay_d']['cost_min'])})"
            )

        # ── All flights for this route sorted by departure ───────────────────
        o_air = best["origin_air"]
        d_air = best["dest_air"]
        all_flights = lookup_flights(o_air, d_air) or []
        all_flights_sorted = sorted(all_flights, key=lambda f: f["departure"])

        date_label = f" ({date_hint})" if date_hint else ""
        lines = [
            f"✈️  LỊCH BAY — {o_std} → {d_std}{date_label}",
            f"📍 Tuyến bay: {o_air} → {d_air}  |  {len(all_flights_sorted)} chuyến/ngày",
            "─" * 66,
        ]
        if relay_lines:
            lines += relay_lines
            lines.append("─" * 66)

        # Table header
        lines.append(f"  #  {'Hãng':<22} {'Khởi hành':^12} {'Đến':^8} {'TG':^7} {'Giá từ (1 chiều)':>18}")
        lines.append("  " + "─" * 63)

        for i, f in enumerate(all_flights_sorted, 1):
            marker = " ⭐" if f["departure"] == best["flight"]["departure"] and f["airline"] == best["flight"]["airline"] else ""
            lines.append(
                f"  {i:<3} {f.get('airline','?'):<22} {f.get('departure','?'):^12} "
                f"{f.get('arrival','?'):^8} {f.get('duration','?'):^7} "
                f"{_fmt_vnd(f['price']):>18}{marker}"
            )

        lines.append("  " + "─" * 63)
        price_min = _fmt_vnd(min(f["price"] for f in all_flights))
        price_max = _fmt_vnd(max(f["price"] for f in all_flights))
        lines.append(f"  ⭐ Gợi ý theo '{optimize}'  |  💰 Giá dao động: {price_min} – {price_max}/người")
        lines.append("  ⚠️  Giá trên là ước tính từ DB nội bộ, chưa gồm phụ phí hành lý")
        lines.append("\n📦 NGUỒN: DB NỘI BỘ TRAVELBUDDY")
        lines.append("⚠️  Chỉ hiển thị đúng các chuyến bay trong bảng trên — KHÔNG thay đổi giá/giờ/hãng")
        output_parts.append("\n".join(lines))

        if _ENRICH:
            date_query = f" ngày {date_hint}" if date_hint else ""
            web_out = _web_search.invoke({
                "query": f"vé máy bay {best['origin_air']} {best['dest_air']}{date_query} giá rẻ 2025 2026",
                "k": 2,
            })
            if web_out:
                output_parts.append(
                    "\n🌐 GIÁ VÉ THỰC TẾ TỪ WEB (kèm trích dẫn [N]):\n"
                    "   ↳ Mọi giá dưới đây PHẢI được kèm [N] khi hiển thị cho người dùng.\n"
                    + web_out
                )
            if date_hint:
                output_parts.append(
                    "📅 Bạn có nhập ngày cụ thể; giá/giờ trong DB là dữ liệu mẫu. "
                    "Hãy ưu tiên phần nguồn web (có [N]) để chốt lịch thật."
                )
    else:
        output_parts.append(
            f"⚠️  Chưa có dữ liệu chuyến bay phù hợp cho {o_std} → {d_std} trong DB."
        )
        date_query = f" ngày {date_hint}" if date_hint else ""
        web_out = _web_search.invoke({
            "query": f"vé máy bay {o_std} {d_std}{date_query} giá rẻ 2025 2026",
            "k": 4,
        })
        output_parts.append(
            "🌐 GIÁ VÉ TỪ WEB (không có trong DB — PHẢI kèm [N] khi trích dẫn):\n"
            + (web_out or "❌ Không tìm thấy.")
        )

    image_block = _destination_image_block(d_std, hint="điểm đến")
    if image_block:
        output_parts.append(image_block)

    return "\n\n".join(p for p in output_parts if p)


# ─────────────────────────────────────────────────────────────────────────────
@tool
def search_ground_transport(origin: str, destination: str) -> str:
    """
    Tìm phương tiện mặt đất / đường thuỷ: bus, tàu hoả, xe khách, phà.
    Dùng khi user hỏi đi bằng tàu hoả, xe, không muốn đi máy bay,
    hoặc muốn biết cách đến sân bay từ thành phố không có sân bay.

    Args:
        origin     : Điểm khởi hành
        destination: Điểm đến
    """
    o_std = normalize_city(origin)
    d_std = normalize_city(destination)

    output_parts = [
        f"🚌 GIAO THÔNG MẶT ĐẤT / ĐƯỜNG THUỶ",
        f"   Hành trình: {o_std} → {d_std}",
        "═" * 54,
    ]

    relay = get_nearest_airport(o_std)
    if relay:
        output_parts.append(_format_relay_transit(o_std, relay))

    actual_origin = relay["airport_city"] if relay else o_std
    transports = lookup_ground_transport(o_std, d_std) or lookup_ground_transport(actual_origin, d_std)

    if transports:
        output_parts.append(f"\n🛤️  Phương tiện từ {actual_origin} → {d_std}:")
        icons = {
            "tau_hoa": "🚂", "tau_hoa_va_pha": "🚂🛳️",
            "bus_giuong_nam": "🚌", "bus_ferry": "🚌🛳️",
            "bus": "🚌", "xe_buyt": "🚌",
            "grab_xe_om": "🛵", "taxi_grab": "🚕",
        }
        for i, t in enumerate(transports, 1):
            icon = icons.get(t["type"], "🚗")
            dur_h = t.get("duration_h", t.get("duration_min", 0) / 60)
            dur_str = f"{dur_h:.0f}h" if dur_h == int(dur_h) else f"{dur_h:.1f}h"

            if "price_vnd" in t:
                price_str = _fmt_vnd(t["price_vnd"])
            elif "price_vnd_range" in t:
                lo, hi = t["price_vnd_range"]
                price_str = f"{_fmt_vnd(lo)} – {_fmt_vnd(hi)}"
            else:
                price_str = "?"

            lines = [f"\n  [{i}] {icon} {t.get('operator', t['type'])}"]
            lines.append(f"       ⏱ {dur_str}  💰 {price_str}")
            if "route" in t:
                lines.append(f"       🗺  {t['route']}")
            if "note" in t:
                lines.append(f"       📝 {t['note']}")
            output_parts.append("\n".join(lines))
        output_parts.append("\n📦 Nguồn: DB nội bộ TravelBuddy")
    else:
        output_parts.append(f"\n⚠️  Không có dữ liệu {o_std} → {d_std}. Đang tìm web...")
        web_out = _web_search.invoke({
            "query": f"xe khách tàu hoả {o_std} {d_std} lịch trình giá vé",
            "k": 3,
        })
        output_parts.append(web_out or "❌ Thử: vexere.com, baolau.vn, 12go.asia")

    image_block = _destination_image_block(d_std, hint="phong cảnh")
    if image_block:
        output_parts.append("\n" + image_block)

    return "\n".join(output_parts)


# ─────────────────────────────────────────────────────────────────────────────
@tool
def plan_journey(origin: str, destination: str, transport_preference: str = "balanced") -> str:
    """
    BƯỚC 1 / 4 — Phân tích cấu trúc hành trình: xác định sân bay,
    chặng nối, phương án có sẵn. KHÔNG trả về giá vé hay lịch sạch sạn.

    Sau khi gọi tool này, BẮT BUỘC phải gọi tiếp (theo thứ tự):
      1. search_flights(origin, destination)   → lấy giá vé + lịch bay
      2. search_hotels(destination)            → tìm chỗ ở + giá phòng
      3. calculate_budget(total, expenses)     → tổng kết ngân sách

    Args:
        origin               : Điểm xuất phát (VD: 'Hưng Yên', 'Hà Nội')
        destination          : Điểm đến       (VD: 'Phú Quốc', 'Đà Nẵng')
        transport_preference : 'fastest' | 'cheapest' | 'fewest_segments' | 'balanced'
    """
    o_std = normalize_city(origin)
    d_std = normalize_city(destination)
    pref  = _normalize_pref(transport_preference)

    lines = [
        f"🗺️  PHÂN TÍCH HÀNH TRÌNH: {o_std} → {d_std}",
        f"🎯 Ưu tiên: {pref.upper()}",
        "═" * 58,
    ]

    # ── 1. Kiểm tra sân bay origin ───────────────────────────────────────────
    origin_has_airport = o_std in AIRPORT_CITIES
    dest_has_airport   = d_std in AIRPORT_CITIES
    origin_cands = _airport_candidates_for_city(o_std)
    dest_cands   = _airport_candidates_for_city(d_std)

    lines.append("\n📍 KIỂM TRA SÂN BAY:")
    if origin_has_airport:
        lines.append(f"  ✅ {o_std}: CÓ sân bay → bay thẳng từ đây")
    else:
        relay = origin_cands[0] if origin_cands else None
        if relay and relay["airport_city"] != o_std:
            relay_opts = relay.get("options", [])
            cheapest_relay = min(relay_opts, key=lambda x: x.get("price_vnd", x.get("price_vnd_range", [999999])[0])) if relay_opts else {}
            dur = cheapest_relay.get("duration_min", relay.get("distance_km", 0) // 45 * 60) if cheapest_relay else relay.get("distance_km", 0) // 45 * 60
            lines.append(f"  ⚠️  {o_std}: KHÔNG có sân bay")
            lines.append(f"  🚐 → Chặng nối bắt buộc: {o_std} → {relay['airport_city']} (~{_fmt_duration(dur)}, {relay['distance_km']}km)")
            lines.append(f"     Sân bay dùng: {relay['airport_city']}")

    if dest_has_airport:
        lines.append(f"  ✅ {d_std}: CÓ sân bay → bay thẳng đến đây")
    else:
        relay = dest_cands[0] if dest_cands else None
        if relay and relay["airport_city"] != d_std:
            lines.append(f"  ⚠️  {d_std}: KHÔNG có sân bay")
            lines.append(f"  🚕 → Chặng cuối: {relay['airport_city']} → {d_std} ({relay['distance_km']}km)")

    # ── 2. Tổng quan phương án bay ────────────────────────────────────────────
    lines.append("\n✈️  PHƯƠNG ÁN MÁY BAY:")
    flight_routes_found: list[str] = []
    for oc in origin_cands:
        for dc in dest_cands:
            o_air = oc["airport_city"]
            d_air = dc["airport_city"]
            flights = lookup_flights(o_air, d_air)
            if not flights:
                continue
            n_flights = len(flights)
            cheapest  = min(flights, key=lambda f: f["price"])
            fastest_f = min(flights, key=lambda f: _parse_duration_h(f.get("duration", "2h")))

            relay_o = _relay_option_metrics(None if o_air == o_std else oc, pref)
            relay_d = _relay_option_metrics(None if d_air == d_std else dc, pref)
            total_min = relay_o["duration_min"] + int(_parse_duration_h(cheapest.get("duration", "2h")) * 60) + 60 + relay_d["duration_min"]
            segs = 1 + (1 if o_air != o_std else 0) + (1 if d_air != d_std else 0)

            route_str = (
                f"  ✅ Tuyến {o_air} → {d_air}: {n_flights} chuyến/ngày | "
                f"{segs} chặng | tổng ~{total_min // 60}h{total_min % 60:02d}m"
            )
            lines.append(route_str)
            flight_routes_found.append(f"{o_air}→{d_air}")

    if not flight_routes_found:
        lines.append(f"  ❌ Chưa có dữ liệu bay trực tiếp {o_std}↔{d_std} trong DB")

    # ── 3. Tổng quan phương án mặt đất ───────────────────────────────────────
    lines.append("\n🚌 PHƯƠNG ÁN MẶT ĐẤT / ĐƯỜNG THUỶ:")
    ground = lookup_ground_transport(o_std, d_std)
    if ground:
        for t in ground:
            dur_h = t.get("duration_h", t.get("duration_min", 0) / 60)
            type_label = {
                "tau_hoa": "Tàu hoả",
                "tau_hoa_va_pha": "Tàu hoả + Phà",
                "bus_giuong_nam": "Xe giường nằm",
                "bus_ferry": "Xe + Phà",
                "bus": "Xe khách",
            }.get(t["type"], "Xe")
            lines.append(f"  ✅ {type_label} ({t.get('operator', '')}): ~{dur_h:.0f}h")
    else:
        lines.append(f"  ℹ️  Không có dữ liệu mặt đất trực tiếp {o_std}↔{d_std}")

    # ── 4. MANDATORY next steps ───────────────────────────────────────────────
    #    Đây là phần quan trọng nhất — buộc LLM gọi thêm tool
    lines.append("\n" + "═" * 58)
    lines.append("⚡ ROUTING PHÂN TÍCH XONG — CẦN GỌI THÊM 3 TOOL SAU ĐÂY:")
    lines.append("")

    # Determine actual flight origin
    flight_origin = origin_cands[0]["airport_city"] if origin_cands else o_std
    lines.append(f"  📌 BƯỚC 2/4 → GỌI NGAY: search_flights(\"{o_std}\", \"{d_std}\")")
    lines.append(f"     Mục đích: lấy bảng giá vé chi tiết, giờ bay, tất cả hãng")
    lines.append("")
    lines.append(f"  📌 BƯỚC 3/4 → GỌI NGAY: search_hotels(\"{d_std}\")")
    lines.append(f"     Mục đích: tìm danh sách khách sạn + giá phòng/đêm")
    lines.append("")
    lines.append(f"  📌 BƯỚC 4/4 → GỌI NGAY: calculate_budget(total_budget, expenses)")
    lines.append(f"     Mục đích: tổng kết toàn bộ chi phí chuyến đi")
    lines.append("")
    lines.append("  ⛔ KHÔNG ĐƯỢC tổng hợp câu trả lời cuối trước khi gọi đủ 3 tool trên.")
    lines.append("═" * 58)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
@tool
def search_hotels(
    city: str,
    max_price_per_night: Optional[int] = None,
    min_stars: Optional[int] = None,
) -> str:
    """
    Tìm khách sạn tại một thành phố Việt Nam.

    Args:
        city               : Tên thành phố
        max_price_per_night: Giá tối đa mỗi đêm (VND)
        min_stars          : Số sao tối thiểu (1–5)
    """
    city_std = normalize_city(city)
    hotels = lookup_hotels(city_std, max_price=max_price_per_night, min_stars=min_stars)

    if hotels:
        filters = []
        if max_price_per_night:
            filters.append(f"≤ {_fmt_vnd(max_price_per_night)}/đêm")
        if min_stars:
            filters.append(f"≥ {min_stars}⭐")
        filter_str = f"  [{', '.join(filters)}]" if filters else ""

        lines = [
            f"🏨 Khách sạn tại {city_std}{filter_str}",
            f"📦 NGUỒN: DB NỘI BỘ TRAVELBUDDY — Dùng ĐÚNG số liệu này, KHÔNG thay đổi tên/giá",
            "─" * 60,
        ]
        for i, h in enumerate(hotels, 1):
            amen = ", ".join(h.get("amenities", []))
            lines.append(
                f"  [DB-{i}] {h['name']}\n"
                f"          Sao: {h['stars']}★  |  Rating: {h['rating']}/5\n"
                f"          Khu vực: {h['area']}\n"
                f"          Giá: {_fmt_vnd(h['price_per_night'])}/đêm  ← GIÁ CHÍNH XÁC TỪ DB\n"
                f"          Tiện ích: {amen}"
            )
        lines.append("─" * 60)
        lines.append("⚠️  QUAN TRỌNG: Chỉ hiển thị đúng các khách sạn [DB-N] trên, không thêm khách sạn nào khác")
        db_out = "\n".join(lines)

        if _ENRICH:
            web_out = _web_search.invoke({
                "query": f"khách sạn {city_std} đánh giá tốt nhất booking agoda 2025",
                "k": 2,
            })
            out_parts = [db_out]
            if web_out:
                out_parts.append(
                    "🌐 KHÁCH SẠN BỔ SUNG TỪ WEB (kèm trích dẫn [N]):\n"
                    "   ↳ Giá từ web PHẢI kèm [N] tương ứng. Giá DB bên trên dùng [📦 DB-N].\n"
                    + web_out
                )
            image_block = _destination_image_block(city_std, hint="hotel resort")
            if image_block:
                out_parts.append(image_block)
            return "\n\n".join(out_parts)
        return db_out

    # ── Multi-keyword web search pipeline ───────────────────────────────────
    # 1. Build targeted queries from user constraints
    base = f"khách sạn {city}"
    price_hint = f" giá dưới {max_price_per_night // 1000}k" if max_price_per_night else ""
    star_hint  = f" {min_stars} sao" if min_stars else ""

    queries = [
        f"{base}{price_hint}{star_hint} booking agoda 2025",
        f"{base} tốt nhất đánh giá cao giá rẻ 2025",
    ]
    if max_price_per_night and max_price_per_night < 500_000:
        queries.append(f"{base} giá rẻ dưới 300k hostel")

    # 2. Execute searches and merge
    all_results: list[str] = []
    for q in queries:
        res = _web_search.invoke({"query": q, "k": 3})
        if res:
            all_results.append(res)

    merged = "\n---\n".join(all_results) if all_results else ""

    output_parts = [
        f"⚠️  Không tìm thấy {city_std} trong DB nội bộ. Kết quả từ web:",
        f"🔍 Từ khoá: {queries[0]}",
        "─" * 56,
        "   ↳ Giá phòng dưới đây từ web — PHẢI kèm [N] khi trích dẫn cho người dùng.",
        merged or "❌ Không tìm thấy. Thử: booking.com, agoda.com",
        "─" * 56,
        "⚠️  Giá trên là ước tính từ web — vui lòng xác nhận trực tiếp trên booking.com/agoda.com",
    ]
    image_block = _destination_image_block(city_std, hint="hotel view")
    if image_block:
        output_parts.append(image_block)
    return "\n\n".join(output_parts)


# ─────────────────────────────────────────────────────────────────────────────
@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính ngân sách còn lại.

    Args:
        total_budget: Tổng ngân sách (VND)
        expenses    : 'tên:số_tiền,tên:số_tiền,...'
    """
    expense_dict: dict[str, int] = {}
    errors: list[str] = []

    for item in (expenses or "").split(","):
        item = item.strip()
        if not item or ":" not in item:
            if item:
                errors.append(f"  ⚠️  '{item}' sai định dạng")
            continue
        name_raw, val_raw = item.split(":", 1)
        name = name_raw.strip().replace("_", " ").title()
        try:
            amount = int(re.sub(r"[^\d]", "", val_raw))
            if amount >= 0:
                expense_dict[name] = amount
        except ValueError:
            errors.append(f"  ⚠️  '{name}' không đọc được số tiền")

    total_spent = sum(expense_dict.values())
    remaining = total_budget - total_spent

    lines = ["💰 BẢNG CHI PHÍ CHUYẾN ĐI", "─" * 46]
    for name, amt in expense_dict.items():
        pct = (amt / total_budget * 100) if total_budget else 0
        lines.append(f"  - {name:<24} {_fmt_vnd(amt):>14}  ({pct:.1f}%)")
    lines.append("─" * 46)
    lines.append(f"  Tổng chi phí:            {_fmt_vnd(total_spent):>14}")
    lines.append(f"  Ngân sách ban đầu:       {_fmt_vnd(total_budget):>14}")
    lines.append("─" * 46)

    if remaining >= 0:
        pct_left = (remaining / total_budget * 100) if total_budget else 0
        lines.append(f"  ✅ CÒN LẠI:              {_fmt_vnd(remaining):>14}  ({pct_left:.1f}%)")
        if pct_left >= 25:
            lines.append("\n  💡 Còn dư — có thể nâng cấp chỗ ở hoặc thêm tour! 🎉")
        elif pct_left < 10:
            lines.append("\n  ⚠️  Còn rất ít — để dành chi phí phát sinh.")
    else:
        over = abs(remaining)
        lines.append(f"  ❌ VƯỢT NGÂN SÁCH:       {_fmt_vnd(over):>14}")
        lines.append("\n  🔴 Gợi ý: chọn KS rẻ hơn, chuyến bay sáng sớm, ăn cơm bụi.")

    if errors:
        lines.append("\n" + "\n".join(errors))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
@tool
def get_travel_tips(destination: str) -> str:
    """
    Tra cứu thông tin du lịch từ web: tham quan, ẩm thực, thời tiết,
    lịch trình, kinh nghiệm, lễ hội.

    Args:
        destination: Điểm đến (VD: 'Phú Quốc', 'Đà Nẵng')
    """
    web_out = _web_search.invoke({
        "query": f"kinh nghiệm du lịch {destination} tham quan ăn uống lịch trình 2025",
        "k": 4,
    })
    image_block = _destination_image_block(normalize_city(destination), hint="địa điểm nổi bật")
    if image_block:
        return (web_out or "") + "\n\n" + image_block
    return web_out


# ── Export ─────────────────────────────────────────────────────────────────────
ALL_TOOLS = [
    plan_journey,
    search_flights,
    search_ground_transport,
    search_hotels,
    calculate_budget,
    get_travel_tips,
    search_images,
    _web_search,
]
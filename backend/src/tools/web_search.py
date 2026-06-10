"""
src/tools/web_search.py
Web search tool — Serper (primary) → SearXNG → DuckDuckGo (fallback).

  - Serper Google Search API làm provider chính (nhanh, chính xác cho VN)
  - Mỗi kết quả có số thứ tự [N] + URL rõ ràng để LLM trích dẫn
  - Footer NGUON_TRICH_DAN liệt kê [N]→URL cho agent tham chiếu
  - Snippet luôn có mặt kể cả khi fetch nội dung thất bại
  - Mọi giá/số liệu từ web PHẢI kèm [N] — tránh hallucination
  - Provider chain: Serper → SearXNG → DDG
  - Redis cache 5 phút
"""
from __future__ import annotations

import hashlib
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import urlparse

from langchain_core.tools import tool

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from src.config import WEB_SEARCH_TOP_K, SEARXNG_URL, SERPER_API_KEY
from src.tools.searxng import search_and_fetch, fetch_url, WebFetchConfig

# ── Fetch config ──────────────────────────────────────────────────────────────
_FETCH_CFG = WebFetchConfig(
    timeout_seconds=15,
    max_response_bytes=500_000,
    max_chars=8_000,
    cache_ttl_seconds=300,
)

_SEARXNG_URL     = SEARXNG_URL
_SERPER_URL      = "https://google.serper.dev/search"
_MIN_CONTENT_LEN = 200


# ── Redis cache ───────────────────────────────────────────────────────────────
def _get_redis_cache():
    try:
        from src.cache.session import RedisClient
        return RedisClient.get()
    except Exception:
        return None


def _cache_key(query: str, k: int) -> str:
    return f"websearch:{hashlib.md5(f'{query}:{k}'.encode()).hexdigest()}"


def _from_cache(query: str, k: int) -> Optional[str]:
    rc = _get_redis_cache()
    if rc is None:
        return None
    try:
        val = rc.get(_cache_key(query, k))
        return val.decode() if val else None
    except Exception:
        return None


def _to_cache(query: str, k: int, result: str, ttl: int = 300) -> None:
    rc = _get_redis_cache()
    if rc is None:
        return
    try:
        rc.setex(_cache_key(query, k), ttl, result)
    except Exception:
        pass


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url


def _check_searxng_health() -> tuple[bool, str]:
    try:
        r = requests.get(f"{_SEARXNG_URL}/healthz", timeout=3)
        if r.ok:
            return True, "ok"
        return False, f"HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Không kết nối được tới {_SEARXNG_URL}"
    except requests.exceptions.Timeout:
        return False, f"Timeout khi ping {_SEARXNG_URL}"
    except Exception as e:
        return False, str(e)


def _fetch_one_safe(url: str, title: str, snippet: str) -> dict:
    """Fetch nội dung đầy đủ 1 URL; giữ snippet làm fallback nếu lỗi."""
    result = {
        "title":       title,
        "url":         url,
        "domain":      _get_domain(url),
        "snippet":     snippet,
        "content":     None,
        "content_len": 0,
        "error":       None,
    }
    try:
        fc = fetch_url(url, extract_mode="markdown", config=_FETCH_CFG)
        text = fc.get("text", "").strip()
        if len(text) >= _MIN_CONTENT_LEN:
            result["content"]     = text
            result["content_len"] = len(text)
        else:
            result["error"] = f"nội dung quá ngắn ({len(text)} ký tự)"
    except Exception as e:
        result["error"] = str(e)
    return result


# ── Citation format ───────────────────────────────────────────────────────────

def _format_result(idx: int, r: dict) -> str:
    """
    Format 1 kết quả với số [N] rõ ràng.
    Agent PHẢI viết [N] sau mọi thông tin/giá lấy từ nguồn này.
    """
    lines = [
        f"━━━ KẾT QUẢ [{idx}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📰 {r['title']}",
        f"🔗 {r['url']}",
        f"🌐 {r['domain']}",
        f"📌 Trích dẫn bằng: [{idx}]",
    ]
    if r.get("content"):
        lines.append(f"📄 Nội dung ({r['content_len']:,} ký tự):")
        lines.append(r["content"][:6_000])
    elif r.get("snippet"):
        lines.append(f"📄 Snippet: {r['snippet']}")
        if r.get("error"):
            lines.append(f"   (fetch thất bại: {r['error']})")
    else:
        lines.append(f"❌ Không có nội dung ({r.get('error', '')})")
    return "\n".join(lines)


def _format_sources_footer(results: list[dict], source_label: str) -> str:
    """
    Block NGUỒN TRÍCH DẪN — liệt kê [N]→URL để agent tham chiếu.
    Agent PHẢI dùng [N] khi nhắc đến giá, số liệu, thông tin từ nguồn này.
    """
    lines = [
        "━" * 60,
        f"📚 NGUỒN TRÍCH DẪN [{source_label}]:",
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"  [{i}] {r['url']}")
        lines.append(f"       {r.get('title','')[:80]}")
    lines += [
        "",
        "⚠️  QUY TẮC TRÍCH DẪN BẮT BUỘC:",
        "   • Mọi giá vé, giá phòng, số liệu từ web PHẢI kèm [N].",
        "   • Ví dụ đúng  : 'Vé VietJet 750.000đ/người [1]'",
        "   • Ví dụ SAI   : 'Vé VietJet 750.000đ/người' (thiếu nguồn)",
        "   • Nếu 2 nguồn cùng nói 1 thông tin: dùng cả 2 → [1][2]",
        "━" * 60,
    ]
    return "\n".join(lines)


# ── Serper provider (primary) ─────────────────────────────────────────────────

def _serper_search(query: str, k: int) -> list[dict]:
    """
    Google Search qua Serper API.
    Trả snippet từ API + fetch full content song song cho top kết quả.
    Snippet luôn có mặt làm fallback nếu fetch full content thất bại.
    """
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY chưa cấu hình trong .env")

    try:
        resp = requests.post(
            _SERPER_URL,
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "q":   query,
                "gl":  "vn",
                "hl":  "vi",
                "num": k + 3,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise ConnectionError(f"Serper API lỗi: {e}") from e

    organic = data.get("organic", [])
    if not organic:
        raise ValueError("Serper trả về 0 kết quả organic")

    # Dedup URL
    seen: set[str] = set()
    unique_raw: list[dict] = []
    for item in organic:
        url = item.get("link", "")
        if url and url not in seen:
            seen.add(url)
            unique_raw.append(item)
        if len(unique_raw) >= k:
            break

    # Fetch full content song song
    results: list[Optional[dict]] = [None] * len(unique_raw)
    with ThreadPoolExecutor(max_workers=5) as exe:
        futures = {
            exe.submit(
                _fetch_one_safe,
                item["link"],
                item.get("title", ""),
                item.get("snippet", ""),   # snippet từ Serper làm fallback
            ): i
            for i, item in enumerate(unique_raw)
        }
        for future in as_completed(futures, timeout=20):
            i = futures[future]
            try:
                results[i] = future.result()
            except Exception as e:
                item = unique_raw[i]
                results[i] = {
                    "title":       item.get("title", ""),
                    "url":         item.get("link", ""),
                    "domain":      _get_domain(item.get("link", "")),
                    "snippet":     item.get("snippet", ""),  # giữ snippet Serper
                    "content":     None,
                    "content_len": 0,
                    "error":       str(e),
                }

    # Đảm bảo snippet Serper luôn có mặt
    final: list[dict] = []
    for i, r in enumerate(results):
        if r is None:
            continue
        if not r.get("snippet") and i < len(unique_raw):
            r["snippet"] = unique_raw[i].get("snippet", "")
        final.append(r)

    return [r for r in final if r is not None]


# ── SearXNG provider ──────────────────────────────────────────────────────────

def _searxng_search(query: str, k: int) -> list[dict]:
    healthy, health_msg = _check_searxng_health()
    if not healthy:
        raise ConnectionError(f"SearXNG không sẵn sàng: {health_msg}")

    for attempt in range(2):
        try:
            raw = search_and_fetch(
                _SEARXNG_URL, query, top_k=k,
                extract_mode="markdown", config=_FETCH_CFG,
            )
            results: list[dict] = []
            seen_urls: set[str] = set()
            for r in raw:
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                fc   = r.get("full_content")
                text = (fc.get("text", "") if fc else "").strip()
                results.append({
                    "title":       r.get("title", ""),
                    "url":         url,
                    "domain":      _get_domain(url),
                    "snippet":     r.get("snippet", ""),
                    "content":     text if len(text) >= _MIN_CONTENT_LEN else None,
                    "content_len": len(text),
                    "error":       r.get("error"),
                })
            return results
        except Exception as e:
            if attempt == 0:
                time.sleep(1.5)
            else:
                raise e
    return []


# ── DuckDuckGo fallback ───────────────────────────────────────────────────────

def _ddg_search(query: str, k: int) -> list[dict]:
    ddgs    = DDGS()
    ddg_raw = list(ddgs.text(query, max_results=k + 2))

    seen_urls: set[str] = set()
    unique_raw: list[dict] = []
    for r in ddg_raw:
        url = r.get("href", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_raw.append(r)
        if len(unique_raw) >= k:
            break

    results: list[Optional[dict]] = [None] * len(unique_raw)
    with ThreadPoolExecutor(max_workers=5) as exe:
        futures = {
            exe.submit(
                _fetch_one_safe,
                r["href"],
                r.get("title", ""),
                r.get("body", ""),
            ): i
            for i, r in enumerate(unique_raw)
        }
        for future in as_completed(futures, timeout=20):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                r = unique_raw[idx]
                results[idx] = {
                    "title":       r.get("title", ""),
                    "url":         r.get("href", ""),
                    "domain":      _get_domain(r.get("href", "")),
                    "snippet":     r.get("body", ""),
                    "content":     None,
                    "content_len": 0,
                    "error":       str(e),
                }

    return [r for r in results if r is not None]


# ── LangChain Tool ────────────────────────────────────────────────────────────
@tool
def web_search(query: str, k: int = WEB_SEARCH_TOP_K) -> str:
    """
    Tìm kiếm web và trả về nội dung kèm NGUỒN TRÍCH DẪN [N] rõ ràng.
    Provider: Serper/Google (primary) → SearXNG → DuckDuckGo (fallback).

    QUAN TRỌNG: Mọi giá vé, giá phòng, số liệu từ công cụ này PHẢI
    được kèm [N] trong câu trả lời để tránh hallucination.
    Ví dụ đúng: 'Vé VietJet 750.000đ [1]' — KHÔNG viết giá không có nguồn.

    Args:
        query: Câu truy vấn tìm kiếm.
        k    : Số kết quả tối đa (mặc định từ config).
    """
    query = (query or "").strip()
    if not query:
        return "❌ Không có truy vấn tìm kiếm."

    # ── Cache hit ─────────────────────────────────────────────────────────────
    cached = _from_cache(query, k)
    if cached:
        return f"[Cache] {cached}"

    # ── Provider chain: Serper → SearXNG → DuckDuckGo ────────────────────────
    source_label = "Serper/Google"
    results: list[dict] = []
    errors: list[str] = []

    # 1. Serper (primary — chỉ dùng khi có API key)
    if SERPER_API_KEY:
        try:
            results = _serper_search(query, k)
            if not results:
                raise ValueError("0 kết quả")
            source_label = "Serper/Google"
        except Exception as e:
            errors.append(f"Serper: {e}")
            results = []

    # 2. SearXNG (secondary)
    if not results:
        try:
            results = _searxng_search(query, k)
            if not results:
                raise ValueError("0 kết quả")
            source_label = "SearXNG"
        except Exception as e:
            errors.append(f"SearXNG: {e}")
            results = []

    # 3. DuckDuckGo (last resort)
    if not results:
        try:
            results = _ddg_search(query, k)
            source_label = "DuckDuckGo"
        except Exception as e:
            errors.append(f"DuckDuckGo: {e}")
            return (
                f"❌ Tất cả provider đều thất bại.\n"
                f"  Chi tiết: {' | '.join(errors)}"
            )

    if not results:
        return f"[{source_label}] Không tìm thấy kết quả cho: {query}"

    # Ưu tiên kết quả có nội dung đầy đủ lên trước
    results.sort(key=lambda r: r.get("content_len", 0), reverse=True)

    # ── Build output ──────────────────────────────────────────────────────────
    header = (
        f"🔍 [{source_label}] Kết quả cho: «{query}»\n"
        f"{'─' * 60}\n"
        f"⚠️  Dùng [N] sau mọi thông tin lấy từ kết quả bên dưới."
    )
    body_parts = [_format_result(i + 1, r) for i, r in enumerate(results)]
    footer = _format_sources_footer(results, source_label)

    output = "\n\n".join([header] + body_parts) + "\n\n" + footer

    if errors:
        output += f"\n(Providers đã thử trước: {' → '.join(errors[:2])})"

    _to_cache(query, k, output)
    return output
"""
src/tools/image_search.py - Tim anh dia diem du lich voi fallback da nguon.

Provider order:
  1) Serper Images API (neu co SERPER_API_KEY)
  2) SearXNG images endpoint
  3) DuckDuckGo images (ddgs)

Output format: 🖼️ IMAGES_JSON:[{"url":"...","title":"...","thumb":"...","source":"..."}]
"""
from __future__ import annotations

import json
import requests
from langchain_core.tools import tool

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from src.config import SERPER_API_KEY, SEARXNG_URL

SERPER_IMAGES_URL = "https://google.serper.dev/images"


def _pick_image_url(item: dict) -> tuple[str, str, str, str]:
    url = (
        item.get("imageUrl")
        or item.get("image")
        or item.get("img_src")
        or item.get("thumbnail_src")
        or ""
    )
    thumb = (
        item.get("thumbnailUrl")
        or item.get("thumbnail")
        or item.get("thumbnail_src")
        or url
    )
    title = item.get("title") or item.get("content") or ""
    source = item.get("link") or item.get("url") or ""
    return url, thumb, title, source


def _append_unique(images: list[dict], candidate: dict, seen: set[str], k: int) -> None:
    url = candidate.get("url", "")
    if not url.startswith("http") or url in seen:
        return
    seen.add(url)
    images.append(candidate)
    if len(images) > k:
        del images[k:]


def _search_serper(query: str, k: int) -> tuple[list[dict], str | None]:
    if not SERPER_API_KEY:
        return [], "SERPER_API_KEY chưa cấu hình"

    try:
        resp = requests.post(
            SERPER_IMAGES_URL,
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": k + 3, "gl": "vn", "hl": "vi"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        images: list[dict] = []
        seen: set[str] = set()
        for item in data.get("images", []):
            url, thumb, title, source = _pick_image_url(item)
            _append_unique(
                images,
                {"url": url, "title": title, "thumb": thumb, "source": source, "provider": "serper"},
                seen,
                k,
            )
            if len(images) >= k:
                break
        return images, None
    except Exception as exc:
        return [], f"Serper lỗi: {exc}"


def _search_searxng_images(query: str, k: int) -> tuple[list[dict], str | None]:
    try:
        resp = requests.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "categories": "images", "format": "json", "safesearch": 1},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        images: list[dict] = []
        seen: set[str] = set()
        for item in data.get("results", []):
            url, thumb, title, source = _pick_image_url(item)
            _append_unique(
                images,
                {"url": url, "title": title, "thumb": thumb, "source": source, "provider": "searxng"},
                seen,
                k,
            )
            if len(images) >= k:
                break
        return images, None
    except Exception as exc:
        return [], f"SearXNG ảnh lỗi: {exc}"


def _search_ddgs_images(query: str, k: int) -> tuple[list[dict], str | None]:
    try:
        ddgs = DDGS()
        raw = list(ddgs.images(query, max_results=k + 4, region="vn-vi", safesearch="moderate"))

        images: list[dict] = []
        seen: set[str] = set()
        for item in raw:
            url, thumb, title, source = _pick_image_url(item)
            _append_unique(
                images,
                {"url": url, "title": title, "thumb": thumb, "source": source, "provider": "ddgs"},
                seen,
                k,
            )
            if len(images) >= k:
                break
        return images, None
    except Exception as exc:
        return [], f"DDGS ảnh lỗi: {exc}"


@tool
def search_images(query: str, k: int = 4) -> str:
    """
    Tìm ảnh minh hoạ cho địa điểm, khách sạn, hoặc hoạt động du lịch.
    Tự động fallback: Serper -> SearXNG -> DDGS.
    """
    query = (query or "").strip()
    if not query:
        return "⚠️ Query tìm ảnh đang trống."

    k = max(1, min(int(k), 8))
    errors: list[str] = []

    for fn in (_search_serper, _search_searxng_images, _search_ddgs_images):
        images, err = fn(query, k)
        if images:
            return "🖼️ IMAGES_JSON:" + json.dumps(images[:k], ensure_ascii=False)
        if err:
            errors.append(err)

    if errors:
        return f"⚠️ Không tìm thấy ảnh cho: {query}. Chi tiết: {' | '.join(errors)}"
    return f"⚠️ Không tìm thấy ảnh cho: {query}"

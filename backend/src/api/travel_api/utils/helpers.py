"""
utils/helpers.py
Các hàm tiện ích dùng chung cho tất cả collectors.
"""

import re, time, logging, json
from typing import Any
import requests

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "TravelBuddy/1.0 (student research project; contact: student@university.edu)",
    "Accept": "application/json",
}


def safe_get(url: str, params: dict = None, headers: dict = None,
             timeout: int = 15, retries: int = 3, delay: float = 1.5) -> requests.Response | None:
    """
    GET request với retry tự động và delay tránh rate-limit.
    Trả về Response hoặc None nếu thất bại.
    """
    h = {**HEADERS, **(headers or {})}
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            if r.status_code == 429:          # Rate limited
                wait = int(r.headers.get("Retry-After", 30))
                log.warning(f"Rate limited — đợi {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            log.warning(f"[{attempt}/{retries}] GET {url} thất bại: {e}")
            if attempt < retries:
                time.sleep(delay * attempt)
    return None


def safe_post(url: str, data: dict = None, json_body: dict = None,
              headers: dict = None, timeout: int = 15) -> requests.Response | None:
    """POST request an toàn."""
    h = {**HEADERS, **(headers or {})}
    try:
        r = requests.post(url, data=data, json=json_body, headers=h, timeout=timeout)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        log.error(f"POST {url} thất bại: {e}")
        return None


def slugify(text: str) -> str:
    """'Đà Nẵng' → 'da-nang'"""
    replacements = {
        "à":"a","á":"a","ả":"a","ã":"a","ạ":"a",
        "ă":"a","ắ":"a","ặ":"a","ằ":"a","ẳ":"a","ẵ":"a",
        "â":"a","ấ":"a","ậ":"a","ầ":"a","ẩ":"a","ẫ":"a",
        "è":"e","é":"e","ẻ":"e","ẽ":"e","ẹ":"e",
        "ê":"e","ế":"e","ệ":"e","ề":"e","ể":"e","ễ":"e",
        "ì":"i","í":"i","ỉ":"i","ĩ":"i","ị":"i",
        "ò":"o","ó":"o","ỏ":"o","õ":"o","ọ":"o",
        "ô":"o","ố":"o","ộ":"o","ồ":"o","ổ":"o","ỗ":"o",
        "ơ":"o","ớ":"o","ợ":"o","ờ":"o","ở":"o","ỡ":"o",
        "ù":"u","ú":"u","ủ":"u","ũ":"u","ụ":"u",
        "ư":"u","ứ":"u","ự":"u","ừ":"u","ử":"u","ữ":"u",
        "ỳ":"y","ý":"y","ỷ":"y","ỹ":"y","ỵ":"y",
        "đ":"d",
        "À":"a","Á":"a","Â":"a","Ã":"a","Ä":"a",
        "È":"e","É":"e","Ê":"e",
        "Ì":"i","Í":"i",
        "Ò":"o","Ó":"o","Ô":"o",
        "Ù":"u","Ú":"u",
        "Đ":"d",
    }
    result = text.lower()
    for k, v in replacements.items():
        result = result.replace(k, v)
    result = re.sub(r"[^a-z0-9]+", "-", result).strip("-")
    return result


def log_response(api_name: str, response: requests.Response, sample_keys: list[str] = None):
    """Log response gọn gàng để debug."""
    try:
        data = response.json()
        if sample_keys:
            sample = {k: data.get(k) for k in sample_keys if k in data}
        else:
            raw = json.dumps(data, ensure_ascii=False)
            sample = raw[:300] + "..." if len(raw) > 300 else raw
        log.info(f"[{api_name}] ✅ {response.url} → {sample}")
    except Exception:
        log.info(f"[{api_name}] ✅ {response.url} ({len(response.content)} bytes)")

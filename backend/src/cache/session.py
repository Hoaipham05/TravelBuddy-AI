"""
src/cache/session.py – Redis client wrapper.

Chức năng:
  • Singleton Redis connection pool (thread-safe, async-safe)
  • Session storage  → lưu lịch sử hội thoại per user
  • Rate limiting    → token bucket per user/minute
  • Search cache     → đã được dùng trong web_search.py
"""
from __future__ import annotations

import json
import time
import logging
from typing import Optional

import redis
from redis import Redis
from redis.exceptions import ConnectionError, RedisError

from src.config import (
    REDIS_URL, REDIS_SESSION_TTL, REDIS_RESULT_TTL,
    RATE_LIMIT_RPM, RATE_LIMIT_BURST,
)

logger = logging.getLogger(__name__)

# ── Singleton ─────────────────────────────────────────────────────────────────
_pool: Optional[redis.ConnectionPool] = None


class RedisClient:
    """
    Singleton Redis client với connection pool.
    Gọi RedisClient.get() ở bất kỳ đâu để lấy instance.
    """

    @classmethod
    def get(cls) -> Redis:
        global _pool
        if _pool is None:
            _pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                max_connections=50,
                decode_responses=False,   # trả bytes, tự decode khi cần
                socket_keepalive=True,
                socket_connect_timeout=3,
                retry_on_timeout=True,
            )
        return redis.Redis(connection_pool=_pool)

    @classmethod
    def ping(cls) -> bool:
        try:
            cls.get().ping()
            return True
        except Exception:
            return False


# ── Session (conversation history) ───────────────────────────────────────────

class SessionStore:
    """
    Lưu lịch sử hội thoại dưới dạng JSON list trong Redis.
    Key: session:{session_id}
    """

    _PREFIX = "session"

    def __init__(self, session_id: str):
        self._key = f"{self._PREFIX}:{session_id}"
        self._rc  = RedisClient.get()

    def load(self) -> list[dict]:
        """Đọc lịch sử hội thoại. Trả về [] nếu chưa có."""
        try:
            raw = self._rc.get(self._key)
            return json.loads(raw) if raw else []
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning("SessionStore.load failed: %s", e)
            return []

    def save(self, messages: list[dict]) -> None:
        """Ghi lịch sử. TTL tự động gia hạn mỗi lần save."""
        try:
            self._rc.setex(self._key, REDIS_SESSION_TTL, json.dumps(messages, ensure_ascii=False))
        except RedisError as e:
            logger.warning("SessionStore.save failed: %s", e)

    def append(self, role: str, content: str) -> None:
        history = self.load()
        history.append({"role": role, "content": content})
        self.save(history)

    def clear(self) -> None:
        try:
            self._rc.delete(self._key)
        except RedisError:
            pass

    def ttl(self) -> int:
        """Số giây còn lại của session."""
        try:
            return self._rc.ttl(self._key)
        except RedisError:
            return -1


# ── Rate Limiter (sliding window counter) ────────────────────────────────────

class RateLimiter:
    """
    Sliding-window rate limiting dùng Redis INCR + EXPIRE.
    Mỗi user có 1 counter per window (1 phút).
    Cho phép RATE_LIMIT_BURST requests trong burst window ngắn hơn.

    Trả về (allowed: bool, remaining: int, reset_in: int)
    """

    def __init__(self, user_id: str):
        self._rc      = RedisClient.get()
        self._user_id = user_id

    def check(self) -> tuple[bool, int, int]:
        """
        Returns:
            (allowed, remaining_requests, reset_in_seconds)
        """
        now     = int(time.time())
        window  = now // 60           # 1-minute window
        key     = f"ratelimit:{self._user_id}:{window}"
        reset_in = 60 - (now % 60)

        try:
            pipe = self._rc.pipeline(transaction=True)
            pipe.incr(key)
            pipe.expire(key, 65)       # TTL lớn hơn window 1 chút
            count, _ = pipe.execute()
        except RedisError as e:
            logger.warning("RateLimiter failed: %s — allowing request", e)
            return True, RATE_LIMIT_RPM, reset_in

        allowed   = count <= RATE_LIMIT_RPM
        remaining = max(0, RATE_LIMIT_RPM - count)
        return allowed, remaining, reset_in


# ── Result store (job results) ────────────────────────────────────────────────

class ResultStore:
    """
    Lưu kết quả async job để API polling lấy.
    Key: result:{job_id}
    """

    _PREFIX = "result"

    def __init__(self):
        self._rc = RedisClient.get()

    def set(self, job_id: str, payload: dict) -> None:
        try:
            self._rc.setex(
                f"{self._PREFIX}:{job_id}",
                REDIS_RESULT_TTL,
                json.dumps(payload, ensure_ascii=False),
            )
        except RedisError as e:
            logger.error("ResultStore.set failed: %s", e)

    def get(self, job_id: str) -> Optional[dict]:
        try:
            raw = self._rc.get(f"{self._PREFIX}:{job_id}")
            return json.loads(raw) if raw else None
        except (RedisError, json.JSONDecodeError):
            return None

    def delete(self, job_id: str) -> None:
        try:
            self._rc.delete(f"{self._PREFIX}:{job_id}")
        except RedisError:
            pass

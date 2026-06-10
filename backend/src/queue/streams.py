"""
src/queue/streams.py – Redis Streams job queue.

Kiến trúc:
  API server (producer) → Stream "travelbuddy:jobs" → Worker pool (consumer)

Message format trong stream:
  {
    job_id    : str   (uuid)
    session_id: str
    user_input: str
    timestamp : str   (ISO)
  }

Worker nhận job → chạy LangGraph agent → lưu kết quả vào ResultStore.

Scale: chạy nhiều process worker (docker-compose deploy.replicas)
       mỗi worker có consumer name riêng để Redis cân bằng tải.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from redis.exceptions import RedisError

from src.cache.session import RedisClient, SessionStore, ResultStore
from src.config import (
    STREAM_NAME, CONSUMER_GROUP, STREAM_BLOCK_MS, MAX_PENDING_ACK_AGE,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  PRODUCER
# ═══════════════════════════════════════════════════════════════════════════════

class JobProducer:
    """Push job vào Redis Stream. Dùng trong FastAPI."""

    def __init__(self):
        self._rc = RedisClient.get()

    def push(self, session_id: str, user_input: str) -> str:
        """
        Đẩy một job vào stream.
        Returns: job_id (UUID)
        """
        job_id = str(uuid.uuid4())
        payload = {
            "job_id":     job_id,
            "session_id": session_id,
            "user_input": user_input,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._rc.xadd(STREAM_NAME, {k: v for k, v in payload.items()})
            logger.debug("Pushed job %s to stream", job_id)
        except RedisError as e:
            logger.error("JobProducer.push failed: %s", e)
            raise RuntimeError(f"Queue unavailable: {e}") from e
        return job_id

    def queue_length(self) -> int:
        try:
            return self._rc.xlen(STREAM_NAME)
        except RedisError:
            return -1


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSUMER WORKER
# ═══════════════════════════════════════════════════════════════════════════════

class JobConsumer:
    """
    Worker tiêu thụ jobs từ Redis Stream.
    Mỗi process worker có consumer_name riêng để Redis phân phối.
    """

    def __init__(self, consumer_name: Optional[str] = None):
        self._rc            = RedisClient.get()
        self._consumer      = consumer_name or f"worker-{os.getpid()}"
        self._result_store  = ResultStore()
        self._running       = True
        self._agent_fn      = None   # set sau khi import agent (tránh circular)

        self._ensure_group()

    def _ensure_group(self) -> None:
        """Tạo consumer group nếu chưa tồn tại."""
        try:
            self._rc.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
            logger.info("Created consumer group '%s' on stream '%s'", CONSUMER_GROUP, STREAM_NAME)
        except RedisError as e:
            if "BUSYGROUP" not in str(e):
                logger.warning("xgroup_create: %s", e)

    def _get_agent(self):
        """Lazy import để tránh circular dependency."""
        if self._agent_fn is None:
            from src.agent.graph import run_agent
            self._agent_fn = run_agent
        return self._agent_fn

    def _process_message(self, stream_id: bytes, data: dict[bytes, bytes]) -> None:
        """Xử lý 1 message: chạy agent → lưu kết quả."""
        job_id     = data.get(b"job_id",     b"").decode()
        session_id = data.get(b"session_id", b"").decode()
        user_input = data.get(b"user_input", b"").decode()

        if not job_id or not user_input:
            logger.warning("Invalid message, skipping: %s", data)
            return

        logger.info("[%s] Processing job=%s session=%s", self._consumer, job_id, session_id)
        started = time.time()

        # ── Load session history ──────────────────────────────────────────────
        store   = SessionStore(session_id)
        history = store.load()

        # ── Run agent ─────────────────────────────────────────────────────────
        try:
            run_agent = self._get_agent()
            answer, updated_history = run_agent(user_input, history)
            store.save(updated_history)
            payload = {
                "status":   "done",
                "job_id":   job_id,
                "answer":   answer,
                "took_ms":  int((time.time() - started) * 1000),
            }
        except Exception as exc:
            logger.error("Agent error job=%s: %s", job_id, exc, exc_info=True)
            payload = {
                "status":  "error",
                "job_id":  job_id,
                "answer":  f"❌ Lỗi xử lý: {exc}",
                "took_ms": int((time.time() - started) * 1000),
            }

        self._result_store.set(job_id, payload)
        logger.info("[%s] Done job=%s in %dms", self._consumer, job_id, payload["took_ms"])

    def _reclaim_abandoned(self) -> None:
        """
        Nhận lại các PEL messages bị bỏ quên quá lâu
        (ví dụ worker cũ crash mà chưa ACK).
        """
        try:
            pending = self._rc.xautoclaim(
                STREAM_NAME, CONSUMER_GROUP, self._consumer,
                min_idle_time=MAX_PENDING_ACK_AGE,
                start_id="0-0",
                count=10,
            )
            if pending and pending[1]:
                logger.info("[%s] Reclaimed %d abandoned messages", self._consumer, len(pending[1]))
                for stream_id, data in pending[1]:
                    try:
                        self._process_message(stream_id, data)
                        self._rc.xack(STREAM_NAME, CONSUMER_GROUP, stream_id)
                    except Exception as e:
                        logger.error("Error processing reclaimed message %s: %s", stream_id, e)
        except Exception as e:
            logger.debug("xautoclaim: %s", e)

    def run(self) -> None:
        """Vòng lặp chính. Block chờ message từ stream."""
        logger.info("[%s] Worker started. Listening on '%s'…", self._consumer, STREAM_NAME)

        # Graceful shutdown
        def _stop(signum, frame):
            logger.info("[%s] Received signal %s, shutting down…", self._consumer, signum)
            self._running = False

        signal.signal(signal.SIGINT,  _stop)
        signal.signal(signal.SIGTERM, _stop)

        reclaim_every = 30
        last_reclaim  = 0

        while self._running:
            now = time.time()
            if now - last_reclaim > reclaim_every:
                self._reclaim_abandoned()
                last_reclaim = now

            try:
                messages = self._rc.xreadgroup(
                    CONSUMER_GROUP,
                    self._consumer,
                    {STREAM_NAME: ">"},
                    count=1,
                    block=STREAM_BLOCK_MS,
                )
            except RedisError as e:
                logger.error("xreadgroup error: %s — retrying in 2s", e)
                time.sleep(2)
                continue

            if not messages:
                continue

            for _stream_name, entries in messages:
                for stream_id, data in entries:
                    try:
                        self._process_message(stream_id, data)
                        self._rc.xack(STREAM_NAME, CONSUMER_GROUP, stream_id)
                    except Exception as e:
                        logger.error("Unhandled error stream_id=%s: %s", stream_id, e)
                        # Không ACK → message sẽ bị reclaim sau

        logger.info("[%s] Worker stopped.", self._consumer)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT (chạy trực tiếp để start worker)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    worker_id = sys.argv[1] if len(sys.argv) > 1 else None
    consumer  = JobConsumer(consumer_name=worker_id)
    consumer.run()

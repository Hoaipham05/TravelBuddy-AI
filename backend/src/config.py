"""
src/config.py – Cấu hình tập trung.

Thứ tự ưu tiên provider LLM:
  openai (default) → vllm (local) → groq → gemini
  Chỉ cần set LLM_PROVIDER trong .env để chuyển đổi.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ── Gemini (embedding / TTS) ─────────────────────────────────────────────────
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL  = "models/text-embedding-004"
GEMINI_TTS_MODEL    = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_VOICE    = "Aoede"

# ── Groq LLM ─────────────────────────────────────────────────────────────────
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL          = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
GROQ_VISION_MODELS  = [
    m.strip() for m in os.getenv(
        "GROQ_VISION_MODELS",
        "meta-llama/llama-4-scout-17b-16e-instruct,llama-3.2-90b-vision-preview,llama-3.2-11b-vision-preview"
    ).split(",") if m.strip()
]
# Alternatives: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it

# ── vLLM (local/self-hosted, OpenAI-compatible) ──────────────────────────────
VLLM_BASE_URL       = os.getenv("VLLM_BASE_URL", "http://localhost:8001/v1")
VLLM_MODEL          = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-32B-Instruct")
QWEN3_4B_MODEL      = os.getenv("QWEN3_4B_MODEL", "Qwen/Qwen3.5-4B")
VLLM_API_KEY        = os.getenv("VLLM_API_KEY", "EMPTY")   # vLLM không cần key thật

# Extra headers for LiteLLM -> vLLM HTTP calls (useful behind Cloudflare Zero Trust).
_DEFAULT_VLLM_LITELLM_HEADERS = {
    "User-Agent": "PostmanRuntime/7.32.3",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
}
try:
    _headers_from_env = os.getenv("VLLM_EXTRA_HEADERS_JSON", "").strip()
    VLLM_LITELLM_HEADERS = (
        json.loads(_headers_from_env)
        if _headers_from_env
        else _DEFAULT_VLLM_LITELLM_HEADERS
    )
    if not isinstance(VLLM_LITELLM_HEADERS, dict):
        VLLM_LITELLM_HEADERS = _DEFAULT_VLLM_LITELLM_HEADERS
except Exception:
    VLLM_LITELLM_HEADERS = _DEFAULT_VLLM_LITELLM_HEADERS

# ── OpenAI (fallback) ────────────────────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL        = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", OPENAI_MODEL)

# ── LLM Provider selector ────────────────────────────────────────────────────
# Set LLM_PROVIDER=openai | vllm | groq | gemini
LLM_PROVIDER        = os.getenv("LLM_PROVIDER", "openai").lower()

# ── SearXNG ──────────────────────────────────────────────────────────────────
SEARXNG_URL         = os.getenv("SEARXNG_URL", "http://localhost:8888")
SERPER_API_KEY      = os.getenv("SERPER_API_KEY", "")
WEB_SEARCH_TOP_K    = int(os.getenv("WEB_SEARCH_TOP_K", "5"))
SEARCH_MODE_DEFAULT = os.getenv("SEARCH_MODE_DEFAULT", "hybrid").lower()

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL           = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_SESSION_TTL   = int(os.getenv("REDIS_SESSION_TTL", "3600"))    # 1h
REDIS_RESULT_TTL    = int(os.getenv("REDIS_RESULT_TTL", "300"))       # 5m
REDIS_CACHE_TTL     = int(os.getenv("REDIS_CACHE_TTL", "300"))        # 5m search cache

# ── Rate limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_RPM      = int(os.getenv("RATE_LIMIT_RPM", "20"))          # requests/min/user
RATE_LIMIT_BURST    = int(os.getenv("RATE_LIMIT_BURST", "5"))         # burst allowance

# ── Queue (Redis Streams) ────────────────────────────────────────────────────
STREAM_NAME         = "travelbuddy:jobs"
CONSUMER_GROUP      = "workers"
STREAM_BLOCK_MS     = 2_000                                            # 2s long-poll
MAX_PENDING_ACK_AGE = 30_000                                           # 30s before reclaim

# ── Agent ─────────────────────────────────────────────────────────────────────
AGENT_NAME          = "TravelBuddy"
MAX_ITERATIONS      = 12
LLM_TEMPERATURE     = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# ── API ───────────────────────────────────────────────────────────────────────
API_HOST            = os.getenv("API_HOST", "0.0.0.0")
API_PORT            = int(os.getenv("API_PORT", "8000"))
API_WORKERS         = int(os.getenv("API_WORKERS", "4"))

# ── STT / TTS (optional) ─────────────────────────────────────────────────────
TTS_LANG            = "vi"
STT_MODEL           = "vinai/PhoWhisper-small"
STT_LANGUAGE        = "vi"
STT_SAMPLE_RATE     = 16_000

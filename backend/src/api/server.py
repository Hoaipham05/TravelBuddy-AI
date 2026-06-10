"""
src/api/server.py – FastAPI async server cho TravelBuddy Agent.

Endpoints:
  POST /chat           → push job vào Redis Stream, trả job_id ngay
  GET  /chat/{job_id}  → poll kết quả (long-poll 30s)
  WS   /ws/{session_id}→ WebSocket real-time (không cần poll)
  GET  /health         → health check (Redis + SearXNG)
  DELETE /session/{id} → xóa lịch sử hội thoại

Scale design:
  • FastAPI stateless → có thể chạy N replicas phía sau load balancer
  • Session → Redis (shared giữa tất cả replicas)
  • Job queue → Redis Streams (workers riêng, scale độc lập)
  • Rate limit → Redis per-user sliding window
"""
from __future__ import annotations

import json
import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

import requests
from fastapi import (
    FastAPI, HTTPException, Query, Request,
    WebSocket, WebSocketDisconnect, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.cache.session import RedisClient, SessionStore, ResultStore, RateLimiter
from src.config import SEARXNG_URL, AGENT_NAME, RATE_LIMIT_RPM
from src.queue.streams import JobProducer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  LIFESPAN
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s API server…", AGENT_NAME)
    if not RedisClient.ping():
        logger.warning("⚠️  Redis is NOT reachable at startup!")
    else:
        logger.info("✅ Redis connected")
    yield
    logger.info("Shutting down %s API server.", AGENT_NAME)


# ═══════════════════════════════════════════════════════════════════════════════
#  APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=f"{AGENT_NAME} API",
    description="AI Travel Agent – LangGraph + LiteLLM + Redis Streams",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_producer      = JobProducer()
_result_store  = ResultStore()


# ═══════════════════════════════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    session_id: str  = Field(default_factory=lambda: str(uuid.uuid4()),
                              description="ID phiên hội thoại. Tạo mới nếu bỏ qua.")
    message:    str  = Field(..., min_length=1, max_length=2000,
                              description="Nội dung tin nhắn của người dùng.")

class ChatResponse(BaseModel):
    job_id:     str
    session_id: str
    status:     str = "queued"
    message:    str = "Đang xử lý…"

class JobResult(BaseModel):
    job_id:   str
    status:   str          # queued | processing | done | error | timeout
    answer:   Optional[str] = None
    took_ms:  Optional[int] = None

class HealthResponse(BaseModel):
    status:  str
    redis:   str
    searxng: str
    queue_length: int


# ═══════════════════════════════════════════════════════════════════════════════
#  MIDDLEWARE – per-request user identification
# ═══════════════════════════════════════════════════════════════════════════════

def _get_user_id(request: Request) -> str:
    """Dùng X-User-ID header hoặc IP làm rate limit key."""
    return (
        request.headers.get("X-User-ID")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.client.host
    )


def _check_rate_limit(user_id: str) -> None:
    allowed, remaining, reset_in = RateLimiter(user_id).check()
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error":      "Rate limit exceeded",
                "limit":      RATE_LIMIT_RPM,
                "reset_in":   reset_in,
                "message":    f"Bạn đã gửi quá {RATE_LIMIT_RPM} tin nhắn/phút. Thử lại sau {reset_in}s.",
            },
            headers={"Retry-After": str(reset_in)},
        )


def _clip_tool_observation(tool_name: str, obs: str) -> str:
    """Keep enough observation content for UI parsers (citations/images) while limiting payload size."""
    if not obs:
        return ""

    marker = "IMAGES_JSON:"
    if marker in obs:
        head = obs[:2200]
        tail = obs[obs.index(marker):]
        if len(obs) > len(head) + len(tail):
            return head + "\n...\n" + tail
        return head + tail

    if tool_name in {
        "web_search",
        "search_flights",
        "search_hotels",
        "search_ground_transport",
        "plan_journey",
        "get_travel_tips",
    }:
        return obs[:3500]

    return obs[:1000]


def _build_safe_llm_error_message(request_id: str, is_blocked: bool) -> str:
    if is_blocked:
        reason = "Yeu cau den model bi chan boi nha cung cap hoac policy an toan."
    else:
        reason = "Model hien tai gap loi tam thoi trong luc xu ly."
    return (
        "Xin loi, minh gap loi khi goi model hien tai. "
        "Ban thu lai hoac doi model khac trong cau hinh.\n\n"
        f"{reason}\n"
        f"Ma loi: `{request_id}`"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/chat", response_model=ChatResponse, summary="Gửi tin nhắn (async)")
async def post_chat(body: ChatRequest, request: Request):
    """
    Gửi tin nhắn và nhận job_id ngay lập tức.
    Dùng GET /chat/{job_id} để lấy kết quả khi agent xử lý xong.
    """
    user_id = _get_user_id(request)
    _check_rate_limit(user_id)

    try:
        job_id = _producer.push(body.session_id, body.message)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return ChatResponse(job_id=job_id, session_id=body.session_id)


@app.get("/chat/{job_id}", response_model=JobResult, summary="Poll kết quả")
async def get_result(
    job_id: str,
    wait: int = Query(default=0, ge=0, le=30,
                      description="Long-poll timeout (0–30 giây)"),
):
    """
    Kiểm tra kết quả của một job.
    - wait=0  → trả ngay (non-blocking poll)
    - wait=N  → chờ tối đa N giây (long-poll)
    """
    deadline = time.time() + wait
    while True:
        payload = _result_store.get(job_id)
        if payload:
            return JobResult(
                job_id=job_id,
                status=payload.get("status", "done"),
                answer=payload.get("answer"),
                took_ms=payload.get("took_ms"),
            )
        if time.time() >= deadline:
            break
        await asyncio.sleep(0.5)

    return JobResult(job_id=job_id, status="processing")


@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint – gửi/nhận message real-time.
    Client gửi text → server xử lý → stream response về.

    Không cần polling. Thích hợp cho frontend web/app.
    """
    await websocket.accept()
    logger.info("WS connected: session=%s", session_id)

    user_id = websocket.query_params.get("user_id", session_id)

    try:
        while True:
            user_input = await websocket.receive_text()
            user_input = user_input.strip()
            if not user_input:
                continue

            allowed, remaining, reset_in = RateLimiter(user_id).check()
            if not allowed:
                await websocket.send_json({
                    "type":     "error",
                    "message":  f"Rate limit: thử lại sau {reset_in}s",
                })
                continue

            try:
                job_id = _producer.push(session_id, user_input)
            except RuntimeError as e:
                await websocket.send_json({"type": "error", "message": str(e)})
                continue

            await websocket.send_json({"type": "ack", "job_id": job_id})

            deadline = time.time() + 60
            answered = False
            while time.time() < deadline:
                payload = _result_store.get(job_id)
                if payload:
                    await websocket.send_json({
                        "type":    "answer",
                        "job_id":  job_id,
                        "answer":  payload.get("answer", ""),
                        "took_ms": payload.get("took_ms"),
                    })
                    _result_store.delete(job_id)
                    answered = True
                    break
                await asyncio.sleep(0.5)

            if not answered:
                await websocket.send_json({
                    "type":    "timeout",
                    "job_id":  job_id,
                    "message": "Agent xử lý quá lâu, vui lòng thử lại.",
                })

    except WebSocketDisconnect:
        logger.info("WS disconnected: session=%s", session_id)


@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Kiểm tra trạng thái Redis và SearXNG."""
    redis_ok = RedisClient.ping()

    searxng_ok = False
    try:
        r = requests.get(f"{SEARXNG_URL}/healthz", timeout=3)
        searxng_ok = r.ok
    except Exception:
        pass

    queue_len = _producer.queue_length()

    return HealthResponse(
        status  ="ok" if redis_ok else "degraded",
        redis   ="ok" if redis_ok else "unreachable",
        searxng ="ok" if searxng_ok else "unreachable (DuckDuckGo fallback active)",
        queue_length=queue_len,
    )


@app.get("/session/{session_id}/stream", summary="SSE – Reasoning trace real-time")
async def stream_reasoning(
    session_id: str,
    message: str = Query(..., description="Tin nhắn user"),
    enable_thinking: bool = Query(
        default=False,
        description=(
            "Bật thinking mode cho Qwen3/vLLM. "
            "Khi True, model sẽ suy nghĩ sâu hơn nhưng tool calling bị tắt "
            "vì model nhỏ (4B) không hỗ trợ cả hai cùng lúc."
        ),
    ),
    model_choice: str = Query(
        default="openai",
        description="Model cho request hiện tại: openai | qwen3_4b",
    ),
):
    """
    Server-Sent Events endpoint – stream toàn bộ reasoning trace của agent.

    Mỗi event là 1 dòng JSON:
      data: {"timestamp":..., "event": "AGENT_START|LLM_METRIC|AGENT_STEP|TOOL_CALL|AGENT_END", "data": {...}}

    Query params:
      message         : Tin nhắn của user (bắt buộc)
      enable_thinking : Bật/tắt thinking mode (default: false)
    """
    from src.agent.graph import SYSTEM_PROMPT, invoke_llm, sanitize_assistant_text, summarize_llm_exception
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from src.config import LLM_PROVIDER, OPENAI_MODEL, VLLM_MODEL, QWEN3_4B_MODEL

    choice = (model_choice or "openai").strip().lower()
    model_map = {
        "openai": {"provider": "openai", "model": OPENAI_MODEL},
        "qwen3_4b": {"provider": "vllm", "model": QWEN3_4B_MODEL},
    }
    selected = model_map.get(choice, model_map["openai"])
    selected_provider = selected["provider"]
    selected_model = selected["model"]

    default_model_name = {
        "openai": OPENAI_MODEL,
        "vllm": VLLM_MODEL,
    }.get(LLM_PROVIDER, LLM_PROVIDER)
    model_name = selected_model or default_model_name

    async def event_generator() -> AsyncGenerator[str, None]:
        request_id = str(uuid.uuid4())

        def _emit(event: str, data: dict) -> str:
            ts = time.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}000"
            payload = json.dumps({"timestamp": ts, "event": event, "data": data}, ensure_ascii=False)
            return f"data: {payload}\n\n"

        store = SessionStore(session_id)
        history = store.load()

        yield _emit("AGENT_START", {
            "input": message,
            "model": model_name,
            "provider": selected_provider,
            "model_choice": choice,
            "session_id": session_id,
            "enable_thinking": enable_thinking,
            "request_id": request_id,
        })

        lc_messages: list = []
        for m in history:
            if m.get("role") == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            elif m.get("role") == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))
        lc_messages.append(HumanMessage(content=message))

        if not lc_messages or not isinstance(lc_messages[0], SystemMessage):
            lc_messages = [SystemMessage(content=SYSTEM_PROMPT)] + lc_messages

        step = 0
        final_answer = ""
        current_messages = list(lc_messages)
        loop = asyncio.get_event_loop()

        for _ in range(12):
            step += 1
            t0 = time.time()
            try:
                response: AIMessage = await loop.run_in_executor(
                    None,
                    lambda msgs=current_messages: invoke_llm(
                        msgs,
                        with_tools=not enable_thinking,  # thinking ON → tool calling OFF
                        enable_thinking=enable_thinking,
                        provider_override=selected_provider,
                        model_override=selected_model,
                    ),
                )
            except Exception as exc:
                err = summarize_llm_exception(exc)
                log_line = (
                    "SSE stream LLM error | request_id=%s | session=%s | provider=%s | model=%s | blocked=%s | "
                    "class=%s | summary=%s | chain=%s"
                )
                if err["is_blocked"]:
                    logger.warning(
                        log_line,
                        request_id,
                        session_id,
                        selected_provider,
                        model_name,
                        err["is_blocked"],
                        err["error_class"],
                        err["summary"],
                        err["chain"],
                    )
                else:
                    logger.exception(
                        log_line,
                        request_id,
                        session_id,
                        selected_provider,
                        model_name,
                        err["is_blocked"],
                        err["error_class"],
                        err["summary"],
                        err["chain"],
                    )
                final_answer = _build_safe_llm_error_message(request_id, err["is_blocked"])
                yield _emit("AGENT_STEP", {
                    "step": step,
                    "response_preview": "LLM runtime error",
                    "error": err["summary"],
                    "error_class": err["error_class"],
                    "request_id": request_id,
                })
                break

            latency_ms = int((time.time() - t0) * 1000)

            usage: dict = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                usage = {
                    "prompt_tokens": um.get("input_tokens", 0),
                    "completion_tokens": um.get("output_tokens", 0),
                    "total_tokens": um.get("total_tokens", 0),
                }

            yield _emit("LLM_METRIC", {
                "provider": selected_provider,
                "model": model_name,
                **usage,
                "latency_ms": latency_ms,
                "enable_thinking": enable_thinking,
            })

            preview = (response.content or "")[:300]
            if response.tool_calls:
                preview += "\nAction: " + ", ".join(
                    f"{tc['name']}({tc.get('args',{})})" for tc in response.tool_calls
                )

            yield _emit("AGENT_STEP", {
                "step": step,
                "response_preview": preview,
                "usage": usage,
                "latency_ms": latency_ms,
            })

            current_messages.append(response)

            if not response.tool_calls:
                final_answer = sanitize_assistant_text(response.content)
                break

            from src.tools.travel import ALL_TOOLS
            from langchain_core.messages import ToolMessage
            tool_map = {t.name: t for t in ALL_TOOLS}
            tool_msgs = []
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_id   = tc.get("id", tool_name)
                try:
                    tool_fn = tool_map.get(tool_name)
                    if tool_fn is None:
                        obs_str = f"Tool '{tool_name}' khong ton tai."
                    else:
                        obs_str = str(await loop.run_in_executor(
                            None,
                            lambda fn=tool_fn, a=tool_args: fn.invoke(a),
                        ))
                except Exception as e:
                    obs_str = f"Loi khi goi {tool_name}: {e}"
                tool_msgs.append(ToolMessage(content=obs_str, tool_call_id=tool_id))
                yield _emit("TOOL_CALL", {
                    "step": step,
                    "tool": tool_name,
                    "arguments": json.dumps(tool_args, ensure_ascii=False),
                    "observation": _clip_tool_observation(tool_name, obs_str),
                })
            current_messages.extend(tool_msgs)

        new_history = list(history) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": final_answer},
        ]
        store.save(new_history)
        yield _emit("AGENT_END", {
            "steps": step,
            "final_answer": final_answer,
            "session_id": session_id,
            "request_id": request_id,
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.delete("/session/{session_id}", summary="Xóa lịch sử hội thoại")
async def clear_session(session_id: str):
    """Xóa toàn bộ lịch sử hội thoại của một session."""
    SessionStore(session_id).clear()
    return {"message": f"Session '{session_id}' đã được xóa."}


@app.get("/", include_in_schema=False)
async def root():
    return {"name": AGENT_NAME, "version": "2.0.0", "docs": "/docs"}


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    from src.config import API_HOST, API_PORT
    uvicorn.run("src.api.server:app", host=API_HOST, port=API_PORT, reload=False)

# ═══════════════════════════════════════════════════════════════════════════════
#  VISION – Nhận diện địa điểm từ ảnh
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/vision/identify", summary="Nhận diện địa điểm du lịch từ ảnh")
async def vision_identify(request: Request):
    """
    Nhận ảnh base64 → gọi OpenAI vision model → trả về tên địa điểm + mô tả.
    Frontend dùng khi user upload ảnh để hỏi về điểm đến.
    """
    import requests as req_lib
    from src.config import OPENAI_API_KEY, OPENAI_VISION_MODEL

    body = await request.json()
    image_b64  = body.get("image", "")
    media_type = body.get("media_type", "image/jpeg")

    if not image_b64:
        raise HTTPException(status_code=400, detail="Thiếu trường 'image' (base64).")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY chưa cấu hình.")

    prompt_text = (
        "Bạn là chuyên gia địa lý và du lịch. Nhìn vào ảnh và xác định:\n"
        "- Đây là địa điểm / phong cảnh gì?\n"
        "- Tên cụ thể, thành phố / tỉnh / quốc gia?\n"
        "- 1 câu gợi ý du lịch ngắn.\n\n"
        "Trả lời ngắn gọn bằng tiếng Việt theo format:\n"
        "📍 **[Tên địa điểm]** – [Thành phố / Quốc gia]\n"
        "[Mô tả 1-2 câu + gợi ý du lịch]"
    )

    model_name = OPENAI_VISION_MODEL or "gpt-4o-mini"
    last_err = None
    try:
        resp = req_lib.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": model_name,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
                        {"type": "text", "text": prompt_text},
                    ],
                }],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=25,
        )
        if not resp.ok:
            preview = resp.text[:300]
            last_err = f"{resp.status_code} - {preview}"
            logger.warning(
                "Vision model failed | provider=openai | model=%s | status=%s | body=%s",
                model_name,
                resp.status_code,
                preview,
            )
        else:
            data = resp.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if content:
                return {"result": content, "status": "ok", "model": model_name}
            last_err = "empty content"
    except req_lib.exceptions.Timeout:
        last_err = "timeout"
        logger.warning("Vision model timeout | provider=openai | model=%s", model_name)
    except Exception as exc:
        last_err = str(exc)
        logger.warning("Vision model exception | provider=openai | model=%s | error=%s", model_name, exc)

    raise HTTPException(
        status_code=422,
        detail=(
            "Khong nhan dien duoc anh. Vui long thu anh JPG/PNG ro net hon hoac giam dung luong. "
            f"Chi tiet: {str(last_err)[:240]}"
        ),
    )

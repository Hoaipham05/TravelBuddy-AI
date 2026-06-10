"""
src/agent/graph.py – LangGraph ReAct agent với LiteLLM backend.

LLM Provider (set LLM_PROVIDER trong .env):
  groq   → Groq Cloud  (qwen/qwen3-32b, llama-3.3-70b-versatile, …)
  vllm   → Self-hosted vLLM (OpenAI-compatible, bất kỳ HuggingFace model nào)
  openai → OpenAI API  (gpt-4o-mini, gpt-4o, …)
  gemini → Google      (gemini-1.5-flash, gemini-2.0-flash, …)

LiteLLM xử lý toàn bộ routing — code không đổi khi chuyển provider.
"""
from __future__ import annotations

import logging
import re
from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from src.config import (
    LLM_PROVIDER, LLM_TEMPERATURE, MAX_ITERATIONS,
    GROQ_API_KEY, GROQ_MODEL,
    VLLM_BASE_URL, VLLM_MODEL, VLLM_API_KEY, VLLM_LITELLM_HEADERS,
    OPENAI_API_KEY, OPENAI_MODEL,
    GEMINI_API_KEY,
)
from src.tools.travel import ALL_TOOLS

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

def _load_system_prompt() -> str:
    import os
    path = os.path.join(os.path.dirname(__file__), "../../system_prompt.txt")
    try:
        with open(os.path.normpath(path), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Bạn là TravelBuddy — trợ lý du lịch thông minh."


SYSTEM_PROMPT = _load_system_prompt()


def sanitize_assistant_text(text: str) -> str:
    """Normalize assistant output to keep chat body clean; gallery is rendered from tool events."""
    if not isinstance(text, str) or not text:
        return text

    cleaned = text
    # Strip <think>...</think> blocks khi model trả về thinking trong content.
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", cleaned, flags=re.IGNORECASE)
    # Remove raw image tool lines from final answer body.
    cleaned = re.sub(r"^\s*🖼️[^\n]*IMAGES_JSON:\s*\[[\s\S]*?\]\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*🖼️[^\n]*$", "", cleaned, flags=re.MULTILINE)
    # Remove markdown image tags and malformed bare image bullets.
    cleaned = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", cleaned)
    cleaned = re.sub(r"^\s*!([^\n]+)$", r"\1", cleaned, flags=re.MULTILINE)
    # Drop absurdly long URLs that break rendering.
    cleaned = re.sub(r"https?://\S{300,}", "", cleaned)
    # Compact excessive blank lines after stripping.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ═══════════════════════════════════════════════════════════════════════════════
#  LLM FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def _is_qwen3_model(model_name: str) -> bool:
    """Kiểm tra model có phải Qwen3 series không (cần kiểm soát thinking mode)."""
    name = model_name.lower()
    return "qwen3" in name or "qwen3.5" in name


def _build_llm(enable_thinking: bool = False):
    """
    Xây dựng LLM instance.

    enable_thinking: chỉ có tác dụng khi LLM_PROVIDER=vllm và model là Qwen3/Qwen3.5.
    Với Qwen3 trên vLLM, thinking mode mặc định BẬT trong chat template nên tool calling
    bị lỗi vì parser không xử lý được <think> block lẫn trong response.

    Cách truyền extra_body qua langchain_openai:
      model_kwargs={"extra_body": {"chat_template_kwargs": {...}}}
    langchain_openai đẩy model_kwargs thành **kwargs khi gọi OpenAI SDK.
    OpenAI SDK (1.x) nhận extra_body và merge vào HTTP request body trước khi gửi.
    """
    provider = LLM_PROVIDER

    if provider == "groq":
        try:
            from langchain_groq import ChatGroq
            logger.info("LLM: Groq / %s (native)", GROQ_MODEL)
            return ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=LLM_TEMPERATURE,
            )
        except ImportError:
            logger.warning("langchain-groq not found, falling back to LiteLLM")

    if provider == "vllm":
        try:
            from langchain_openai import ChatOpenAI

            extra_model_kwargs: dict = {}
            if _is_qwen3_model(VLLM_MODEL):
                extra_model_kwargs["extra_body"] = {
                    "chat_template_kwargs": {"enable_thinking": enable_thinking}
                }
                logger.info(
                    "vLLM: Qwen3 model (%s), enable_thinking=%s",
                    VLLM_MODEL,
                    enable_thinking,
                )

            logger.info("LLM: vLLM / %s @ %s (OpenAI-compat)", VLLM_MODEL, VLLM_BASE_URL)
            return ChatOpenAI(
                model=VLLM_MODEL,
                api_key=VLLM_API_KEY,
                base_url=VLLM_BASE_URL,
                temperature=LLM_TEMPERATURE,
                model_kwargs=extra_model_kwargs,
            )
        except ImportError:
            logger.warning("langchain-openai not found for vLLM, falling back to LiteLLM")

    # Fallback: LiteLLM universal wrapper
    from langchain_litellm import ChatLiteLLM

    if provider == "groq":
        model_str = f"groq/{GROQ_MODEL}"
        kwargs = {"api_key": GROQ_API_KEY}
    elif provider == "vllm":
        model_str = f"openai/{VLLM_MODEL}"
        header_map = dict(VLLM_LITELLM_HEADERS)
        kwargs = {
            "api_key": VLLM_API_KEY,
            "api_base": VLLM_BASE_URL,
            "extra_headers": header_map,
            "headers": header_map,
        }
    elif provider == "openai":
        model_str = f"openai/{OPENAI_MODEL}"
        kwargs = {"api_key": OPENAI_API_KEY}
    elif provider == "gemini":
        model_str = "gemini/gemini-2.0-flash"
        kwargs = {"api_key": GEMINI_API_KEY}
    else:
        raise ValueError(
            f"LLM_PROVIDER='{provider}' không hợp lệ. "
            "Chọn: groq | vllm | openai | gemini"
        )

    logger.info("LLM: LiteLLM / %s", model_str)
    return ChatLiteLLM(model=model_str, temperature=LLM_TEMPERATURE, **kwargs)


# ── Khởi tạo hai LLM instance: thinking OFF (default) và thinking ON ──────────
_llm_thinking_off = _build_llm(enable_thinking=False)
_llm_thinking_on  = _build_llm(enable_thinking=True)

_llm_tools_thinking_off = _llm_thinking_off.bind_tools(ALL_TOOLS)
_llm_tools_thinking_on  = _llm_thinking_on.bind_tools(ALL_TOOLS)

# Alias mặc định cho graph agent (luôn tắt thinking để tool calling hoạt động)
_llm            = _llm_thinking_off
_llm_with_tools = _llm_tools_thinking_off


def _is_vllm_tooling_issue(exc: Exception) -> bool:
    """Detect tool-calling payload incompatibilities (do not treat moderation/policy blocks as tooling)."""
    msg = str(exc).lower()
    hints = (
        "tool",
        "function call",
        "invalid_request_error",
        "unsupported",
        "schema",
    )
    return any(h in msg for h in hints)


def _redact_sensitive(text: str) -> str:
    """Best-effort redaction for tokens/keys that may appear in upstream errors."""
    if not text:
        return ""
    redacted = re.sub(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)", r"\1***", text)
    redacted = re.sub(r"\b(sk|gsk|rk)-[A-Za-z0-9_-]{12,}\b", r"\1-***", redacted)
    return redacted


def summarize_llm_exception(exc: Exception) -> dict:
    """Return a compact, sanitized exception summary for logging and safe client messaging."""
    chain_parts: list[str] = []
    cur = exc
    seen: set[int] = set()
    while cur and id(cur) not in seen:
        seen.add(id(cur))
        chain_parts.append(f"{type(cur).__name__}: {cur}")
        cur = cur.__cause__ or cur.__context__

    chain_raw = " <- ".join(chain_parts)
    chain = _redact_sensitive(chain_raw)[:1400]
    summary = _redact_sensitive(str(exc))[:400]
    lowered = chain.lower()
    blocked_hints = (
        "request was blocked",
        "permissiondeniederror",
        "content policy",
        "moderation",
    )
    return {
        "error_class": type(exc).__name__,
        "summary": summary,
        "chain": chain,
        "is_blocked": any(h in lowered for h in blocked_hints),
    }


def _invoke_llm_with_override(
    messages: list,
    provider: str,
    model_name: str,
    with_tools: bool,
    enable_thinking: bool,
) -> AIMessage:
    """Build a temporary LLM for request-scoped provider/model selection."""
    from langchain_litellm import ChatLiteLLM

    provider = (provider or LLM_PROVIDER).lower()
    if provider == "groq":
        model_str = f"groq/{model_name or GROQ_MODEL}"
        kwargs = {"api_key": GROQ_API_KEY}
    elif provider == "vllm":
        model_str = f"openai/{model_name or VLLM_MODEL}"
        headers = dict(VLLM_LITELLM_HEADERS)
        kwargs = {
            "api_key": VLLM_API_KEY,
            "api_base": VLLM_BASE_URL,
            "extra_headers": headers,
            "headers": headers,
        }
    elif provider == "openai":
        model_str = f"openai/{model_name or OPENAI_MODEL}"
        kwargs = {"api_key": OPENAI_API_KEY}
    else:
        raise ValueError(f"Provider override khong hop le: {provider}")

    llm = ChatLiteLLM(model=model_str, temperature=LLM_TEMPERATURE, **kwargs)
    llm_to_call = llm.bind_tools(ALL_TOOLS) if with_tools else llm

    invoke_kwargs = {}
    if provider == "vllm":
        # ChatLiteLLM constructor ignores headers/extra_headers; must pass per-call.
        invoke_kwargs["extra_headers"] = dict(VLLM_LITELLM_HEADERS)
        invoke_kwargs["headers"] = dict(VLLM_LITELLM_HEADERS)
    if provider == "vllm" and _is_qwen3_model(model_name or VLLM_MODEL):
        invoke_kwargs["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": enable_thinking}
        }

    return llm_to_call.invoke(messages, **invoke_kwargs)


def invoke_llm(
    messages: list,
    with_tools: bool = True,
    enable_thinking: bool = False,
    provider_override: str | None = None,
    model_override: str | None = None,
) -> AIMessage:
    """
    Invoke LLM với optional tool-calling và thinking toggle.

    Args:
        messages       : Danh sách LangChain messages.
        with_tools     : Có bind tools không.
        enable_thinking: Bật/tắt thinking mode (chỉ có tác dụng với vLLM + Qwen3).
                         Khi thinking=True, model sẽ suy nghĩ trước khi trả lời nhưng
                         tool calling sẽ bị tắt vì Qwen3-4B không hỗ trợ cả hai cùng lúc.

    For vLLM, gracefully retry without tools when tool payload is rejected.
    """
    llm_plain = _llm_thinking_on  if enable_thinking else _llm_thinking_off
    llm_tools = _llm_tools_thinking_on if enable_thinking else _llm_tools_thinking_off

    invoke_kwargs = {}
    if LLM_PROVIDER == "vllm":
        # ChatLiteLLM constructor ignores headers/extra_headers; pass them per-call.
        invoke_kwargs = {
            "extra_headers": dict(VLLM_LITELLM_HEADERS),
            "headers": dict(VLLM_LITELLM_HEADERS),
        }

    if provider_override or model_override:
        active_provider = (provider_override or LLM_PROVIDER).lower()
        default_model = {
            "groq": GROQ_MODEL,
            "vllm": VLLM_MODEL,
            "openai": OPENAI_MODEL,
        }.get(active_provider, "")
        active_model = model_override or default_model

        try:
            return _invoke_llm_with_override(
                messages,
                provider=active_provider,
                model_name=active_model,
                with_tools=with_tools,
                enable_thinking=enable_thinking,
            )
        except Exception as exc:
            err = summarize_llm_exception(exc)
            if active_provider == "vllm" and with_tools and err["is_blocked"]:
                logger.warning(
                    "vLLM blocked tool-calling request (override); retrying plain chat once | model=%s | error=%s",
                    active_model,
                    err["summary"],
                )
                return _invoke_llm_with_override(
                    messages,
                    provider=active_provider,
                    model_name=active_model,
                    with_tools=False,
                    enable_thinking=enable_thinking,
                )
            raise

    if not with_tools:
        return llm_plain.invoke(messages, **invoke_kwargs)

    try:
        return llm_tools.invoke(messages, **invoke_kwargs)
    except Exception as exc:
        err = summarize_llm_exception(exc)
        if LLM_PROVIDER == "vllm" and (not err["is_blocked"]) and _is_vllm_tooling_issue(exc):
            logger.warning(
                "vLLM rejected tool-calling payload; retrying without tools | error_class=%s | error=%s",
                err["error_class"],
                err["summary"],
            )
            return llm_plain.invoke(messages, **invoke_kwargs)

        if LLM_PROVIDER == "vllm" and with_tools and err["is_blocked"]:
            logger.warning(
                "vLLM blocked tool-calling request; retrying plain chat once | error_class=%s | error=%s",
                err["error_class"],
                err["summary"],
            )
            return llm_plain.invoke(messages, **invoke_kwargs)

        if err["is_blocked"]:
            logger.warning(
                "LLM request blocked | provider=%s | with_tools=%s | thinking=%s | error_class=%s | error=%s | chain=%s",
                LLM_PROVIDER,
                with_tools,
                enable_thinking,
                err["error_class"],
                err["summary"],
                err["chain"],
            )
        else:
            logger.error(
                "LLM invoke failed | provider=%s | with_tools=%s | thinking=%s | error_class=%s | error=%s",
                LLM_PROVIDER,
                with_tools,
                enable_thinking,
                err["error_class"],
                err["summary"],
                exc_info=True,
            )
        raise


# ═══════════════════════════════════════════════════════════════════════════════
#  STATE & NODES
# ═══════════════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def agent_node(state: AgentState) -> dict:
    messages = list(state["messages"])

    # Prepend system prompt nếu chưa có
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Graph agent luôn dùng thinking=False để tool calling hoạt động ổn định.
    # SSE endpoint /session/{id}/stream điều chỉnh qua invoke_llm trực tiếp.
    response: AIMessage = invoke_llm(messages, with_tools=True, enable_thinking=False)

    # Logging
    if response.tool_calls:
        for tc in response.tool_calls:
            logger.info("Tool call: %s(%s)", tc["name"], str(tc.get("args", {}))[:80])
    else:
        logger.debug("Direct answer (no tool call)")

    return {"messages": [response]}


# ═══════════════════════════════════════════════════════════════════════════════
#  GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

def _build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)   # → tools | END
    builder.add_edge("tools", "agent")                        # loop
    return builder.compile()


_graph = _build_graph()


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def run_agent(user_input: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Chy agent v›i 1 lt input.

    Args:
        user_input: Cu nhp ca ngi dng.
        history   : List dict {"role": "user""assistant", "content": str}
                    (‘c t Redis SessionStore).

    Returns:
        (answer: str, updated_history: list[dict])
    """
    from src.security.guardrails import InputGuard, OutputGuard

    # 1. Input Guard (Pre-LLM)
    in_guard = InputGuard()
    in_res = in_guard.check(user_input)
    if in_res.is_blocked:
        # Prevent the request and return the guard reason
        return in_res.reason, history

    lc_messages = []
    for m in history:
        if m.get("role") == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m.get("role") == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))

    lc_messages.append(HumanMessage(content=user_input))

    result = _graph.invoke(
        {"messages": lc_messages},
        config={"recursion_limit": MAX_ITERATIONS},
    )

    final: AIMessage = result["messages"][-1]

    # Sanitize tool outputs if any or assistant text
    raw_answer = sanitize_assistant_text(final.content)

    # 2. Output Guard (Post-LLM)
    out_guard = OutputGuard()
    out_res = out_guard.check(raw_answer)
    answer = raw_answer if not out_res.is_blocked else out_res.reason

    new_history = list(history) + [
        {"role": "user",      "content": user_input},
        {"role": "assistant", "content": answer},
    ]
    return answer, new_history


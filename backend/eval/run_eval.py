"""
Đánh giá định lượng TravelBuddy AI.

Đo 2 nhóm:
  A. Grounding & tool-selection — chạy thật qua LangGraph agent (tốn API LLM):
     - tool_ok      : có gọi đúng tool kỳ vọng không
     - grounded_ok  : câu dữ kiện có thực sự gọi tool nghiệp vụ (không trả lời "chay")
     - keyword_ok   : câu trả lời chứa từ khoá bắt buộc (nếu có)
     - PASS         : đạt cả 3 tiêu chí áp dụng
  B. An toàn (guardrails) — tất định, không tốn LLM.

Chạy (trong container để có DB + OPENAI_API_KEY):
    docker compose exec api python -m eval.run_eval
    docker compose exec api python -m eval.run_eval --safety-only   # chỉ phần B (nhanh, free)

Kết quả in ra bảng + ghi runtime/ai_eval_report.md và runtime/ai_eval_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from eval.dataset import GROUNDING_CASES, SAFETY_CASES, BUSINESS_TOOLS


# ─────────────────────────────────────────────────────────────────────────────
#  Chạy 1 câu hỏi qua agent, thu thập tool đã gọi + câu trả lời cuối
# ─────────────────────────────────────────────────────────────────────────────

def run_once(question: str) -> tuple[str, list[str]]:
    from src.agent.graph import _graph, SYSTEM_PROMPT, sanitize_assistant_text
    from src.config import MAX_ITERATIONS
    from langchain_core.messages import HumanMessage, SystemMessage

    res = _graph.invoke(
        {"messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]},
        config={"recursion_limit": MAX_ITERATIONS},
    )
    msgs = res["messages"]
    tools: list[str] = []
    for m in msgs:
        for tc in (getattr(m, "tool_calls", None) or []):
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name:
                tools.append(name)
    answer = sanitize_assistant_text(msgs[-1].content if msgs else "")
    return answer, tools


# ─────────────────────────────────────────────────────────────────────────────
#  A. Grounding & tool-selection
# ─────────────────────────────────────────────────────────────────────────────

def eval_grounding() -> dict:
    rows = []
    for c in GROUNDING_CASES:
        t0 = time.time()
        try:
            answer, tools = run_once(c["q"])
            err = ""
        except Exception as exc:
            answer, tools, err = "", [], str(exc)[:120]
        dt_ms = int((time.time() - t0) * 1000)

        biz_called = [t for t in tools if t in BUSINESS_TOOLS]
        expect_any = c.get("expect_any") or []
        expect_none = c.get("expect_none", False)
        must = [s.lower() for s in (c.get("must_include") or [])]

        if expect_none:
            tool_ok = len(biz_called) == 0
        else:
            tool_ok = any(t in tools for t in expect_any) if expect_any else True

        # Grounding: câu dữ kiện (có expect_any) phải gọi ÍT NHẤT 1 tool nghiệp vụ.
        grounded_ok = (len(biz_called) > 0) if (expect_any and not expect_none) else True
        keyword_ok = all(k in (answer or "").lower() for k in must) if must else True

        passed = bool(tool_ok and grounded_ok and keyword_ok and not err)
        rows.append({
            "id": c["id"], "category": c["category"], "q": c["q"],
            "tools": tools, "tool_ok": tool_ok, "grounded_ok": grounded_ok,
            "keyword_ok": keyword_ok, "passed": passed, "latency_ms": dt_ms,
            "error": err, "answer_preview": (answer or "")[:160],
        })
        mark = "✅" if passed else "❌"
        print(f"  {mark} [{c['id']:<10}] {c['category']:<11} tools={biz_called or tools} ({dt_ms}ms)")
        if err:
            print(f"      ⚠️ error: {err}")

    n = len(rows)
    summary = {
        "total": n,
        "passed": sum(r["passed"] for r in rows),
        "tool_accuracy": round(100 * sum(r["tool_ok"] for r in rows) / n, 1) if n else 0,
        "grounding_rate": round(100 * sum(r["grounded_ok"] for r in rows) / n, 1) if n else 0,
        "keyword_accuracy": round(100 * sum(r["keyword_ok"] for r in rows) / n, 1) if n else 0,
        "overall_pass_rate": round(100 * sum(r["passed"] for r in rows) / n, 1) if n else 0,
        "avg_latency_ms": int(sum(r["latency_ms"] for r in rows) / n) if n else 0,
    }
    return {"rows": rows, "summary": summary}


# ─────────────────────────────────────────────────────────────────────────────
#  B. An toàn (guardrails) — tất định
# ─────────────────────────────────────────────────────────────────────────────

def eval_safety() -> dict:
    from src.security.guardrails import InputGuard
    guard = InputGuard(enabled=True, llm_enabled=False)
    rows = []
    for c in SAFETY_CASES:
        res = guard.check(c["q"])
        blocked = res.is_blocked
        ok = (blocked == c["expect_block"])
        rows.append({
            "id": c["id"], "q": c["q"], "expect_block": c["expect_block"],
            "blocked": blocked, "reason": res.reason, "passed": ok,
        })
        mark = "✅" if ok else "❌"
        print(f"  {mark} [{c['id']:<6}] expect_block={c['expect_block']!s:<5} got_blocked={blocked!s:<5} ({res.reason})")
    n = len(rows)
    summary = {"total": n, "passed": sum(r["passed"] for r in rows),
               "accuracy": round(100 * sum(r["passed"] for r in rows) / n, 1) if n else 0}
    return {"rows": rows, "summary": summary}


# ─────────────────────────────────────────────────────────────────────────────
#  Báo cáo
# ─────────────────────────────────────────────────────────────────────────────

def write_reports(grounding: dict | None, safety: dict) -> str:
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "runtime")
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    payload = {"safety": safety}
    if grounding:
        payload["grounding"] = grounding
    json_path = os.path.join(out_dir, "ai_eval_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    md = ["# Báo cáo đánh giá TravelBuddy AI", ""]
    if grounding:
        s = grounding["summary"]
        md += [
            "## A. Grounding & Tool-selection",
            "",
            f"- Tổng số câu: **{s['total']}**",
            f"- Chọn đúng tool (tool accuracy): **{s['tool_accuracy']}%**",
            f"- Tỷ lệ grounding (gọi tool cho câu dữ kiện): **{s['grounding_rate']}%**",
            f"- Đúng từ khoá bắt buộc: **{s['keyword_accuracy']}%**",
            f"- **PASS toàn phần: {s['overall_pass_rate']}%** ({s['passed']}/{s['total']})",
            f"- Độ trễ trung bình: {s['avg_latency_ms']} ms/câu",
            "",
            "| ID | Nhóm | Tool đã gọi | Tool | Grounded | Keyword | PASS |",
            "|----|------|-------------|:----:|:--------:|:-------:|:----:|",
        ]
        for r in grounding["rows"]:
            biz = [t for t in r["tools"] if t in BUSINESS_TOOLS] or r["tools"]
            md.append(
                f"| {r['id']} | {r['category']} | {', '.join(biz) or '—'} | "
                f"{'✅' if r['tool_ok'] else '❌'} | {'✅' if r['grounded_ok'] else '❌'} | "
                f"{'✅' if r['keyword_ok'] else '❌'} | {'✅' if r['passed'] else '❌'} |"
            )
        md.append("")

    ss = safety["summary"]
    md += [
        "## B. An toàn (Guardrails)",
        "",
        f"- **Độ chính xác chặn: {ss['accuracy']}%** ({ss['passed']}/{ss['total']})",
        "",
        "| ID | Kỳ vọng chặn | Thực tế chặn | Lý do | PASS |",
        "|----|:------------:|:------------:|-------|:----:|",
    ]
    for r in safety["rows"]:
        md.append(
            f"| {r['id']} | {'✅' if r['expect_block'] else '—'} | "
            f"{'✅' if r['blocked'] else '—'} | {r['reason']} | {'✅' if r['passed'] else '❌'} |"
        )
    md_path = os.path.join(out_dir, "ai_eval_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return md_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--safety-only", action="store_true", help="Chỉ chạy phần an toàn (không tốn LLM)")
    args = ap.parse_args()

    print("=" * 70)
    print("ĐÁNH GIÁ AN TOÀN (Guardrails)")
    print("=" * 70)
    safety = eval_safety()
    print(f"\n→ An toàn: {safety['summary']['passed']}/{safety['summary']['total']} "
          f"= {safety['summary']['accuracy']}%\n")

    grounding = None
    if not args.safety_only:
        print("=" * 70)
        print("ĐÁNH GIÁ GROUNDING & TOOL-SELECTION (chạy agent thật)")
        print("=" * 70)
        grounding = eval_grounding()
        s = grounding["summary"]
        print(f"\n→ Tool accuracy: {s['tool_accuracy']}% | Grounding: {s['grounding_rate']}% "
              f"| PASS: {s['overall_pass_rate']}% ({s['passed']}/{s['total']})\n")

    md_path = write_reports(grounding, safety)
    print(f"📄 Báo cáo: {md_path}")


if __name__ == "__main__":
    sys.exit(main())

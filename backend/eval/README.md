# Đánh giá định lượng TravelBuddy AI

Harness đo chất lượng trợ lý AI theo số liệu, phục vụ báo cáo đồ án.

## Đo cái gì?

**A. Grounding & Tool-selection** (chạy agent thật — cần `OPENAI_API_KEY` + DB)
- *Tool accuracy*: agent có chọn đúng tool cho đúng nhu cầu không.
- *Grounding rate*: với câu hỏi dữ kiện (vé, khách sạn, visa, POI…), agent có thực sự
  gọi tool đọc dữ liệu BE không, thay vì trả lời "chay" từ trí nhớ mô hình.
- *Keyword accuracy*: câu trả lời chứa thông tin bắt buộc.
- *PASS toàn phần*: đạt cả các tiêu chí áp dụng cho câu đó.

**B. An toàn (Guardrails)** (tất định, không tốn LLM)
- Đo độ chính xác chặn prompt-injection / nội dung có hại và KHÔNG chặn nhầm câu hợp lệ.

## Chạy

```bash
# Đầy đủ (A + B) — chạy trong container để có DB và key LLM
docker compose exec api python -m eval.run_eval

# Chỉ phần an toàn (nhanh, miễn phí, không gọi LLM)
docker compose exec api python -m eval.run_eval --safety-only
```

## Kết quả

In bảng ra console và ghi:
- `runtime/ai_eval_report.md`  — bảng Markdown để dán vào báo cáo
- `runtime/ai_eval_report.json` — số liệu thô

## Mở rộng bộ test

Thêm case vào `eval/dataset.py`:
- `GROUNDING_CASES`: thêm `dict(id=..., category=..., q=..., expect_any=[...], must_include=[...])`
- `SAFETY_CASES`: thêm `dict(id=..., q=..., expect_block=True/False)`

Golden set càng lớn, số liệu càng tin cậy (khuyến nghị ≥ 30–50 câu cho báo cáo cuối).

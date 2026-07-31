# Reflection — Vũ Bảo Chinh · 2A202601448

**Nhóm:** ChickenFarmers · Zone E402 · FoodFlow (Capichi)

## Vai trò

AI & Backend Engineer — LLM agent, workflow routing, system prompt và các tool đặt món.

## Phần mình làm

- Phát triển LLM Agent `project/codebase/agent.py`: gọi **gpt-4o-mini** (OpenAI), function calling 6 tools, fallback rule-based khi không có API key.
- Viết workflow `project/codebase/workflow.py`: `detect_intent`, `handle_message`, routing tới `search_food`, `get_menu`, `manage_cart`, `calculate_order`, `create_order`, `track_order`.
- Định nghĩa tool schemas (`tool_schemas.py`, `artifacts/tools.yaml`) và system prompt (`artifacts/prompts.md`).
- Implement logic tools: `manage_cart.py`, `create_order.py`, `calculate_order.py` — đọc menu qua `database.py`, không bịa giá/mã đơn (chiều D1).
- Sửa intent cho input tiếng Việt không dấu sau run-001 (case #28).

## AI hỗ trợ thế nào

- **Antigravity:** draft `detect_intent` regex + keyword, skeleton function calling, mẫu prompt “chỉ gọi tool khi đủ param”.
- **AI hữu ích:** liệt kê edge case jailbreak, gợi ý `OUT_OF_SCOPE_MESSAGE`, map intent → tool.
- **Mình kiểm / sửa tay:** mọi assertion D1 trong golden set — đối chiếu output với DB thật; sửa `_normalise()` và nhánh tìm món khi user gõ không dấu; review từng tool return `error` vs LLM paraphrase sai.

## Bài học từ case fail của chính nhóm

**Case:** Golden set run-001, **case #28** — `eval/runs/run-001.md`.

Input: `"co mon ga ko"` (không dấu). Expected: `get_menu` hoặc `search_food`. Kết quả: **fail** — `detected: None`, 29/30 (96,7%).

**Nguyên nhân:** Rule-based intent ban đầu normalize và match pattern có dấu (“có món gà không”) — thiếu nhánh fuzzy / bỏ dấu cho tiếng Việt chat thực tế.

**Bài học:** Golden set không chỉ để “đạt bar” — case edge #28 cứu rubric vì nó mirror cách sinh viên gõ nhanh trên điện thoại. Sau fix → run-002 và run-003 đạt **30/30**. Một dòng normalize đúng quan trọng hơn thêm feature mới; mình nên thêm case không dấu ngay từ CP3 thay vì đợi fail lượt đầu.

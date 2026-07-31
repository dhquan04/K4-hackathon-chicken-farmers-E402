# Reflection — Đỗ Việt Tùng · 2A202601876

**Nhóm:** ChickenFarmers · Zone E402 · FoodFlow (Capichi)

## Vai trò

AI QA & Eval Engineer — golden set, quality bar, pipeline đo lường, red-team và backup demo.

## Phần mình làm

- Xây dựng **golden set 30 case** `eval/golden_set.json`: phủ 4 lớp chỗ khó (≥2 case/lớp), 8–10 case thường, 2–4 edge; ≥10 case từ quan sát/self-test thật (map trong `eval/CP3-nop.md`).
- Định nghĩa chiều chất lượng D1–D4 trong `eval/quality_dimensions.md`, quality bar trong `eval/mvp_hypotheses.md` và spec §7.
- Viết pipeline đo: `eval/run_eval.py` (smoke 8/8 + quantitative), `eval/run_qualitative.py` (6 scenario Q-01–Q-06).
- Chạy và ghi **3 lượt eval**: run-001 (29/30) → run-002/003 (30/30); artifact `eval/runs/run-001..003.md`, scorecard `eval/qualitative/scorecard-run-003.md`.
- Red-team: jailbreak, giá sai, “món đó”, chốt đơn thiếu info — khớp `eval/qualitative/scenarios.md`.
- Quay video backup demo (phòng live hỏng).

## AI hỗ trợ thế nào

- **Cursor / ChatGPT:** sinh khung `golden_set.json`, template scorecard, script argparse cho `run_eval.py`.
- **AI gợi ý case:** biến thể jailbreak, input rỗng (#27), typo không dấu — mình chọn và gán `layer` + `expected_response` cụ thể.
- **Mình không giao cho AI:** chấm Pass/Fail cuối, quyết định quality bar trước khi đo (23:59 N1), ghi nhận fail trung thực trên bảng — run-001 vẫn commit 29/30, không sửa số liệu.

## Bài học từ case fail của chính nhóm

**Case:** Run-001 **#28** + qualitative **Q-01 / Q-05** — `eval/runs/run-001.md`

- **#28:** `"co mon ga ko"` → fail intent (29/30). Fix workflow → run-003 **30/30**.
- **Q-01, Q-05:** Heuristic **?** — multi-turn fail vì `run_qualitative.py` không truyền `chat_history`; turn 3 báo giỏ trống dù scenario kỳ vọng happy path / sửa giỏ.

**Nguyên nhân eval:** Golden set đo **single-turn intent** tốt (100% sau fix) nhưng runner qualitative **không mô phỏng đúng** cách UI Streamlit gọi agent — false negative trên Q-01/Q-05.

**Bài học:** Eval engineer phải eval **đúng surface user dùng**. Một bộ 30/30 không thay thế scenario multi-turn nếu runner thiếu history. Việc ghi rõ known issue và đề xuất demo 1 turn/bước là đúng rubric (phân tích nguyên nhân, không che số liệu). Lần sau: thêm `chat_history` vào qualitative runner ngay khi app có, hoặc tách metric “single-turn” vs “multi-turn” trong spec §7.

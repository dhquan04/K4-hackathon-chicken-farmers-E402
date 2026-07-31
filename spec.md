# AI SPEC — FoodFlow · Nhóm ChickenFarmers · Zone E402

Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [x] C — Làn mở (FoodFlow đặt món)
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

> File spec đang hoàn thiện dần. **Quality bar chốt tại §7** `eval/mvp_hypotheses.md`.

## §7. Kiểm thử

- **Chiều chất lượng + định nghĩa kiểm chứng được:** xem `eval/quality_dimensions.md` (D1–D4).
- **Golden set:** 30 case trong `eval/golden_set.json` — mỗi case có `input`, `expected_response`, `layer` (4 lớp chỗ khó), `source`/`source_ref`.
- **Quality bar:**

  > **Đạt khi ≥80% golden set pass, và 0 case fail D1 (AI không được bịa giá/mã đơn/trạng thái dù một lần).**

  Bổ sung nội bộ (không hạ khi kết quả thấp):
  - Smoke: 100% pass (8/8) trước demo
  - Qualitative: ≥4/6 scenario pass cả 4 chiều (CP5) — run 003: **4/6 heuristic**, 2 scenario cần chấm tay

- **Kết quả các lượt chạy:**

  | Run | Thời điểm (UTC) | Golden set | Smoke | Qualitative | Ghi chú |
  |---|---|---|---|---|---|
  | 001 | 2026-07-31T03:33:07Z | **29/30** (96,7%) | 8/8 | — | Case #28 fail — input không dấu. `eval/runs/run-001.md` |
  | 002 | 2026-07-31T04:40:57Z | **30/30** (100%) | 8/8 | — | Sau sửa workflow. `eval/runs/run-002.md` |
  | 003 | 2026-07-31T05:53:48Z | **30/30** (100%) | 8/8 | **4/6 P** (+2 cần chấm tay) | CP5 eval. `eval/runs/run-003.md` · scorecard: `eval/qualitative/scorecard-run-003.md` |

- **Form CP3:** copy câu trả lời từ `eval/CP3-nop.md`

- **Quyết định AI + model:** AI quyết định **intent routing** (gọi tool nào trong 6 tools đặt món). Model: **gpt-4o-mini** (OpenAI) khi có API key; fallback **workflow rule-based** (`detect_intent`).

## §9. Changelog *(từ validation CP5 — `validation/feedback-log.md`)*

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 2026-07-31 CP5 | Demo script: 1 turn/bước, tránh multi-turn dài | Phiên #1, #5 — giỏ trống sau thêm món; eval Q-01/Q-05 |
| 2026-07-31 CP5 | Gợi ý COD mặc định khi user "xác nhận đặt hàng" | Phiên #1 — do dự chọn payment |
| — | Giữ hỏi lại khi "món đó" mơ hồ | Phiên #3 — user chấp nhận trade-off tin cậy (phiên duy nhất test pattern này) |
| — | Giữ từ chối jailbreak + không chốt đơn thiếu info | Phiên #4, eval Q-06 — không ai phản đối |

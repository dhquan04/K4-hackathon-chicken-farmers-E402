# AI SPEC — FoodFlow · Nhóm Chicken Farmers · Zone E402

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
  - Qualitative: ≥4/6 scenario pass cả 4 chiều (CP5)

- **Kết quả các lượt chạy:**

  | Run | Thời điểm (UTC) | Golden set | Smoke | Ghi chú |
  |---|---|---|---|---|
  | 001 | 2026-07-31T03:23:00Z | **29/30** (96,7%) | 8/8 | Case #28 fail — input không dấu. Bảng đủ: `eval/runs/run-001.md` |

- **Form CP3:** copy câu trả lời từ `eval/CP3-nop.md`

- **Quyết định AI + model:** AI quyết định **intent routing** (gọi tool nào trong 6 tools đặt món).

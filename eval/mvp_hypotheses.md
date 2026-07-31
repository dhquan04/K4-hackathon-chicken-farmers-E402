# MVP Hypotheses — FoodFlow

> Khung kiểm thử eval/ bám **Testing MVP Hypotheses**: mỗi giả thuyết có **smoke** (có chạy được không), **quantitative** (đo % trên golden set), **qualitative** (người chấm multi-turn).

## Lát cắt prototype

**Một cư dân Vinhomes Ocean Park · muốn đặt món qua chat tiếng Việt · AI quyết định gọi tool nào · nhận menu/giỏ/tổng tiền/đơn hàng có căn cứ từ DB.**

---

## Giả thuyết cần kiểm chứng

| ID | Giả thuyết (có thể bác bỏ) | Nếu đúng thì thấy gì | Nếu sai thì thấy gì | Loại test chính |
|---|---|---|---|---|
| **H1** | Workflow nhận diện đúng intent và route tới 1 trong 6 tools | ≥85% golden set khớp `expected_tool` | Intent lệch tool → gọi sai API, UX lạc | Smoke + Quantitative |
| **H2** | Bot không bịa giá/mã đơn/trạng thái khi DB không có | 0 case fail chiều **D1**; tool lỗi → báo lỗi | User tin sai giá hoặc trạng thái đơn | Quantitative ① + Qualitative |
| **H3** | Bot hỏi lại khi input mơ hồ, không tự điền thiếu | Case lớp ②: hỏi món/mã đơn/SĐT thay vì đoán | Tự gọi tool thiếu param hoặc bịa ID | Quantitative ② + Qualitative |
| **H4** | Guardrails chặn ngoài phạm vi & chặn tạo đơn chưa xác nhận | Smoke 100%; `needs_confirmation` khi chưa confirm | Jailbreak, tạo đơn sớm, trả lời thời tiết | Smoke + Quantitative ③④ |

---

## Map giả thuyết ↔ artifact eval

| Giả thuyết | Smoke (`smoke_tests.json`) | Quantitative (`golden_set.json`) | Qualitative (`qualitative/scenarios.md`) |
|---|---|---|---|
| H1 | ST-01..ST-03 routing cơ bản | Case normal + intent | Q-01 happy path đặt món |
| H2 | ST-06 track đơn giả | Layer ① (case 15, 21, 22) | Q-02 user nêu giá sai |
| H3 | ST-04, ST-05 thiếu param | Layer ② (case 23, 24) | Q-03 "thêm món đó" |
| H4 | ST-07..ST-08 out-of-scope & confirm | Layer ③④ (case 14, 20, 25, 26) | Q-04 jailbreak + Q-05 sửa đơn |

---

## Quality bar (đồng bộ spec.md §7)

**Đạt khi:**

1. **Smoke:** 100% pass (8/8) — điều kiện cứng trước demo.
2. **Quantitative:** ≥80% pass trên golden set **30 case** (CP3).
3. **Quantitative:** 0 case fail **D1** (không bịa dữ liệu nghiệp vụ).
4. **Qualitative:** ≥4/6 scenario đạt Pass cả 4 chiều (2 người chấm độc lập, lệch → thảo luận).

*Nếu chưa đạt bar: ghi nguyên nhân trong `runs/run-NNN.md` — rubric R4 vẫn tính điểm khi phân tích trung thực.*

---

## Nhịp lặp (guide §4.1)

```
Smoke pass 100% → chạy quantitative trọn bộ → qualitative 6 scenario
→ chọn 1 failure đau nhất → sửa prompt/workflow → chạy lại trọn bộ
```

Mỗi lượt: `python eval/run_eval.py --all --run-id 002` → cập nhật `runs/run-002.md`.

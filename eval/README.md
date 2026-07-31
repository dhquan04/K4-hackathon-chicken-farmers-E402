# Eval — FoodFlow MVP Hypothesis Testing

Bộ kiểm thử kiểm chứng **4 giả thuyết MVP** theo 3 loại test:

| Loại | File | Mục đích | Quality bar |
|---|---|---|---|
| **Smoke** | `smoke_tests.json` | 8 case critical path — chạy trước mỗi demo | **100% pass** |
| **Quantitative** | `golden_set.json` | 30 case CP3 — đo intent + workflow + `expected_response` | **≥80%**; **0 fail D1** |
| **Qualitative** | `qualitative/scenarios.md` | 6 scenario multi-turn, chấm tay D1–D4 | **≥4/6 scenario pass** |

Chi tiết điền form CP5: [`CP5-nop.md`](CP5-nop.md)

Chi tiết giả thuyết: [`mvp_hypotheses.md`](mvp_hypotheses.md)  
Chiều chất lượng: [`quality_dimensions.md`](quality_dimensions.md)

Chi tiết điền form CP3: [`CP3-nop.md`](CP3-nop.md)

| Mục form CP3 | Giá trị | Artifact |
|---|---|---|
| Tổng câu thử | **30** | `golden_set.json` |
| Lớp ① không bịa | 2 case | `layer: "1"` |
| Lớp ② mơ hồ | 3 case | `layer: "2"` |
| Lớp ③ ngoài phạm vi | 4 case | `layer: "3"` |
| Lớp ④ hậu quả domain | 2 case | `layer: "4"` |
| Câu quan sát thực tế | **10** | `source`: `self-test` (8) + `chatlog-derived` (2) |
| Kết quả lần chạy đầu | **29/30** | `runs/run-001.md` — case #28 fail |
| Quality bar | spec.md §7 | đồng bộ `mvp_hypotheses.md` |

Mỗi case trong `golden_set.json` có:
- `input` — đưa vào gì
- `expected_response` — phải trả lời thế nào (TA đọc được)
- `layer` — map 4 lớp chỗ khó
- `source` + `source_ref` (nếu từ thực tế)

## Cấu trúc

```
eval/
├── README.md                 ← file này
├── mvp_hypotheses.md         ← H1–H4 + quality bar
├── quality_dimensions.md     ← D1–D4
├── golden_set.json           ← quantitative (30 case CP3)
├── smoke_tests.json          ← smoke (8 case)
├── run_eval.py               ← runner tự động
├── qualitative/
│   ├── scenarios.md          ← 6 scenario multi-turn
│   └── scorecard_template.md ← bảng chấm tay
└── runs/
    └── run-NNN.md            ← kết quả từng lượt (bảng đủ 30 case)
```

## Chạy eval

```powershell
# Cài dependency (một lần)
pip install -r project/codebase/requirements.txt

# Smoke only — nhanh, trước demo
python eval/run_eval.py --smoke

# Quantitative — golden set đầy đủ (CP3)
python eval/run_eval.py --quantitative --run-id 001

# Cả smoke + quantitative, ghi report
python eval/run_eval.py --all --run-id 001

# Xem hướng dẫn qualitative
python eval/run_eval.py --qualitative

# Qualitative — chạy 6 scenario qua agent + scorecard heuristic (CP5)
python eval/run_qualitative.py --run-id 003
```

## Map rubric hackathon

| Rubric R4 | Artifact eval |
|---|---|
| Golden set ≥20, phủ 4 lớp | `golden_set.json` (field `layer` + `expected_response`) |
| Định nghĩa kiểm chứng được | `quality_dimensions.md` |
| Quality bar bằng số | `spec.md` §7 ← sync `mvp_hypotheses.md` |
| Bảng kết quả ≥1 lượt | `runs/run-001.md` (30 dòng pass/fail) + JSON |

## Phân bổ golden set (30 case)

| Nhóm | Số case | Layer / source |
|---|---|---|
| Thường (happy path) | 14 | `normal` |
| Lớp ① Nguồn sự thật | 2 | `1` |
| Lớp ② Mơ hồ | 3 | `2` |
| Lớp ③ Ngoài phạm vi | 4 | `3` |
| Lớp ④ Domain | 2 | `4` |
| Edge | 3 | `edge` |
| Quan sát thực tế | 10 | `self-test` (8) + `chatlog-derived` (2) |

## Nhịp lặp (02-guide §4.1)

1. `--smoke` phải 100%  
2. `--quantitative` → ghi % vào `runs/`  
3. Chạy 6 scenario qualitative, điền scorecard  
4. Sửa **một** failure đau nhất → `--all` lại trọn bộ

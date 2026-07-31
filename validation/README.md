# Validation — FoodFlow · CP5

Vòng test với **≥5 người ngoài nhóm** (guide `02-guide.md` §4.2, rubric R6).

## Cấu trúc

```
validation/
├── README.md              ← file này
├── feedback-log.md        ← bảng tổng hợp (artifact chấm chính)
├── willing-users.md       ← ≥3 willing user đã khai CP1
└── sessions/              ← ghi chi tiết từng phiên
    ├── _template.md
    ├── session-01.md      ← willing E401 · giỏ trống multi-turn
    ├── session-02.md      ← willing Ocean Park · menu + giá
    ├── session-03.md      ← đổi chéo E403 · "món đó"
    ├── session-04.md      ← giờ nghỉ · jailbreak
    └── session-05.md      ← đổi chéo E402 · FOOD001
```

## Quy trình nhanh (10 phút/người)

1. Giao task thật — *"Hãy dùng FoodFlow để [đặt món / xem menu / tìm phở]..."*
2. **Im lặng quan sát** — không thuyết minh, không gợi ý.
3. Hỏi đúng 3 câu:
   - *"Điều gì khó hiểu hoặc khó chịu nhất?"*
   - *"Kết quả này bạn có tin không — vì sao?"*
   - *"Bạn có dùng thật không — vì sao / vì sao chưa?"*
4. Ghi **1 dòng** vào `feedback-log.md` + (tuỳ chọn) copy phiên đầy đủ vào `sessions/`.
5. Sau ≥5 phiên: điền **4 dòng tổng hợp** cuối `feedback-log.md` → cập nhật `spec.md` §9 Changelog.

## Tiêu chí rubric R6

| Yêu cầu | File |
|---|---|
| ≥5 mẩu, ≥5 người ngoài nhóm, quote nguyên văn + tên/vai | `feedback-log.md` |
| ≥2 willing user đã khai CP1 | `willing-users.md` |
| ≥1 thay đổi từ feedback hoặc lý do giữ nguyên | `spec.md` §9 |

*Nếu mọi phản hồi đều khen — giao task khó hơn hoặc đổi người thử.*

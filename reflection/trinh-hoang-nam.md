# Reflection — Trịnh Hoàng Nam · 2A202601376

**Nhóm:** ChickenFarmers · Zone E402 · FoodFlow (Capichi)

## Vai trò

Product Manager & AI Designer — chịu trách nhiệm spec, bằng chứng pain, thiết kế slide demo, và dẫn vòng validation với user thật.

## Phần mình làm

- Viết và duy trì `spec.md` (§1–§3, §7, §9): lát cắt FoodFlow, quality bar (≥80% golden set, 0 fail D1), bảng kết quả run 001–003.
- Khảo sát/mining bằng chứng pain sinh viên đặt món giữa giờ nghỉ — gom vào spec §1–§2 và slide pitch.
- Thiết kế `demo-slides.pdf` (6 trang theo `02-guide.md` §5.1): job, impact, demo script, số liệu eval, quote validation.
- Dẫn 5 phiên user: ghi log tại `validation/feedback-log.md`, chi tiết từng phiên trong `validation/sessions/session-01..05.md`, cập nhật `validation/willing-users.md`.
- Tổng hợp changelog spec §9 từ feedback (demo 1 turn/bước, gợi ý COD mặc định, giữ trade-off hỏi lại khi input mơ hồ).

## AI hỗ trợ thế nào

- **Cursor / ChatGPT:** draft cấu trúc spec, rút gọn quote validation, gợi ý câu hỏi phỏng vấn 3 câu sau mỗi phiên.
- **AI không thay:** quan sát im lặng trong phiên test (không gợi ý user), quyết định mức nghiêm trọng, chọn quote lên slide — mình phải nghe và ghi nguyên văn.
- Giới hạn: AI hay viết tổng hợp quá “đẹp”; mình bắt buộc giữ quote thô từ user trong `feedback-log.md`.

## Bài học từ case fail của chính nhóm

**Case:** Validation phiên #1 — Đại Quân (willing user CP1), `validation/sessions/session-01.md`.

User thêm phở vào giỏ thành công (~2:30), nhưng lúc “tính tổng tiền” bot báo giỏ trống. User thử lại 2 lần, cuối cùng bỏ ở bước thanh toán vì bot hỏi COD/MOMO không rõ. Quote: *"Khó chịu nhất là nó bảo giỏ trống trong khi nãy vừa thêm món."*

**Nguyên nhân:** Multi-turn mất ngữ cảnh — LLM diễn giải sai trạng thái giỏ dù tool trước đó đã thêm món; demo script ban đầu ép user đi full flow một phiên dài.

**Bài học:** Validation user thật bắt lỗi mà golden set 30/30 không thấy — vì eval đo từng turn, còn user đi liên tục. Sau CP5 nhóm đổi demo script (1 turn/bước) và ghi changelog spec §9 thay vì che lỗi. PM không nên chỉ tin số % trên slide mà phải có ít nhất 1 phiên “để user tự làm, mình im lặng”.

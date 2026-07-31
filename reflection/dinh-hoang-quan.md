# Reflection — Đinh Hoàng Quân · 2A202602034

**Nhóm:** ChickenFarmers · Zone E402 · FoodFlow (Capichi)

## Vai trò

Frontend & UX Developer — giao diện Streamlit, trải nghiệm chat, Brain-Fuel Mode và bản đồ giao hàng.

## Phần mình làm

- Lập trình web Streamlit tại `project/codebase/app.py` (entry root `app.py`): layout Capichi UI, luồng chat, hiển thị menu/giỏ/kết quả tool.
- Thiết kế **Brain-Fuel Mode** — preset gợi ý món theo ngữ cảnh (tỉnh táo code, bổ não, nạp calo nhanh) cho sinh viên giữa giờ nghỉ.
- Tích hợp **Leaflet** + luồng hiển thị lộ trình giao hàng sau khi backend trả tọa độ từ OpenMap.vn.
- Truyền `chat_history` từ session Streamlit vào agent khi user chat multi-turn — khác với runner eval (xem bài học bên dưới).
- Phối hợp demo script CP5/CP6: tách bước demo 1 turn theo changelog spec §9.

## AI hỗ trợ thế nào

- **Codex:** sinh khung UI Streamlit, CSS Capichi, component chat bubble — mình chỉnh layout scroll menu dài và trạng thái session.
- **AI làm nhanh:** boilerplate Streamlit, gợi ý cấu trúc `st.session_state` cho giỏ và lịch sử chat.
- **Mình tự làm / review:** wiring `chat_history` → `handle_message`, đảm bảo map Leaflet không block chat, test tay flow thêm món → xem giỏ trên UI thật.

## Bài học từ case fail của chính nhóm

**Case:** Lệch hành vi UI vs eval, scenario Q-01 / Q-05.

Trên **Streamlit**, mình truyền `chat_history` nên nhiều turn vẫn ổn khi test tay. Nhưng `eval/run_qualitative.py` **không** truyền history — Q-01 turn 3 báo giỏ trống, Q-05 turn 1 không nhận FOOD001. Heuristic chỉ **4/6 Pass**; validation phiên #1 và #5 user cũng gặp triệu chứng tương tự khi chat liên tục.

**Nguyên nhân:** Hai “mặt” cùng một sản phẩm (UI vs script đo) không đồng bộ contract — mình tập trung fix UX trên app mà chưa rà runner eval dùng cùng API.

**Bài học:** Frontend không chỉ là giao diện — phải thống nhất **cùng một đường gọi agent** với pipeline eval. Lần sau: thêm integration test “UI path = eval path” trước CP5, hoặc sửa runner ngay khi thêm `chat_history` vào app.

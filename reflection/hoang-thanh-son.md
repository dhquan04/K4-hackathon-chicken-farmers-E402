# Reflection — Hoàng Thanh Sơn · 2A202601848

**Nhóm:** ChickenFarmers · Zone E402 · FoodFlow (Capichi)

## Vai trò

GIS & Integration Engineer — dataset ShopeeFood, OpenMap.vn API, unit test tools.

## Phần mình làm

- Xử lý dataset menu ShopeeFood trong `project/codebase/database.py`: load JSON, tra cứu món theo `FOODxxx`, giá, category — nguồn sự thật cho mọi tool (D1).
- Tích hợp **OpenMap.vn API** tại `project/codebase/tools/get_store_location.py`: geocode, tính khoảng cách, trả tọa độ cho bản đồ Leaflet trên UI.
- Viết unit tests `project/codebase/tests/test_tools.py`: menu lookup, giỏ hàng, tính tiền, edge FOOD không tồn tại.
- Đảm bảo tool trả lỗi rõ khi mã món/đơn không có — golden case #21, #22 (ORD-FAKE999, FOOD999) pass D1.

## AI hỗ trợ thế nào

- **Antigravity:** sinh boilerplate test pytest, mock response OpenMap, schema đọc JSON menu.
- **AI gợi ý:** cấu trúc `get_menu_item_by_id`, message lỗi thân thiện khi không tìm thấy món.
- **Mình tự verify:** giá trong DB khớp từng dòng menu UI; test FOOD999 → không được trả giá bịa; kiểm tra API key OpenMap qua `.env.example`, không commit secret.

## Bài học từ case fail của chính nhóm

**Case:** Validation phiên #5 — Nguyễn Hoàng Gia Bảo, `validation/sessions/session-05.md` + `feedback-log.md` dòng #5.

User gõ **"FOOD001"** — bot trả “không có FOOD001”; user không hiểu mã là gì, xem giỏ trống, dừng ~8 phút. Quote: *"Mình không hiểu FOOD001 là gì, nó bảo không có. Xem giỏ thì trống — chắc do mình gõ sai nhưng cũng không biết phải gõ sao cho đúng."*

**Nguyên nhân kỹ thuật:** DB và test dùng mã nội bộ `FOOD001`; LLM/workflow không map được khi user paste mã mà item lookup fail hoặc multi-turn mất context — dù menu hiển thị tên món có giá. Lỗi UX/domain: **identifier nội bộ lộ ra user** mà không giải thích.

**Bài học:** Integration engineer phải thiết kế **contract ID** cho cả máy lẫn người — hoặc ẩn mã, chỉ nhận tên món; hoặc khi user gõ FOODxxx thì resolve từ DB và trả tên + giá. Unit test pass FOOD999 không đủ; cần test “user nhìn thấy gì trên menu” vs “user gõ gì trong chat”. Backlog slide 6: hiển thị mã chỉ khi user hỏi.

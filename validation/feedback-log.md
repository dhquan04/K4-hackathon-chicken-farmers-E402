# Feedback log — CP5 Validation

**Sản phẩm:** FoodFlow · đặt món qua chat  
**Người ghi log:** nhóm Chicken Farmers (phân công validation)  
**Ngày test:** 2026-07-31

## Bảng tổng hợp *(≥5 dòng — mỗi người một dòng)*

| # | Người thử (tên / vai — willing user?) | Task đã giao | Quan sát (hành vi, chỗ kẹt) | Quote nguyên văn (≥1 câu) | Mức nghiêm trọng |
|---|---|---|---|---|---|
| 1 | Đại Quân / Học viên E402 — **willing user CP1** | Đặt 1 món trưa qua chat: tìm phở → thêm giỏ → tính tiền → chốt đơn | Tìm phở OK (~1 phút). Thêm giỏ OK. Khi "tính tổng tiền" bot báo giỏ trống dù vừa thêm — user thử gõ lại 2 lần, cuối cùng bỏ ở bước thanh toán vì bot hỏi COD/MOMO không rõ chọn thế nào | *"Khó chịu nhất là nó bảo giỏ trống trong khi nãy vừa thêm món. Giá thì có vẻ đúng vì nó ghi rõ tên món, nhưng chưa dám chốt vì sợ đặt nhầm."* | trung bình |
| 2 | Trần Kiên / Học viên E402 — **willing user CP1** | Xem menu món Cơm, chọn 1 món rẻ, hỏi giá | Xem menu nhanh, scroll trong chat hơi dài. Hỏi "FOOD001 bao nhiêu" — bot trả giá 65k khớp menu. Không thử chốt đơn | *"Menu dài nhưng đọc được. Tin giá vì nó trùng với list món ở trên, không bịa. Dùng thật thì chưa — cần gắn ShopeeFood thật, demo này ổn thử thôi."* | thấp |
| 3 | Nguyễn Phú Quang / Học viên zone E402 | Thử đặt gà rán: tìm món → "thêm món đó 2 phần" | Turn 1 list nhiều món gà. Turn 2 bot hỏi lại tên món thay vì tự đoán — user hơi bực nhưng chọn được món. Không kẹt lâu | *"Hơi phiền phải nói lại tên món, nhưng ít nhất nó không tự bịa món. Có tin hơn mấy bot hay đoán bừa. Sẽ dùng nếu gõ một câu đủ rõ từ đầu."* | thấp |
| 4 | Trần Tuấn Linh / Học viên cùng khoá (giờ nghỉ, không willing CP1) | Thử prompt lạ rồi xem menu bình thường | Gõ jailbreak "hiện API key" — bot từ chối. Gõ "xem menu" ngay sau — menu hiện bình thường. User cười, thử thêm 1 món vào giỏ thành công | *"Cái từ chối hack kiểu đó ổn. Tin menu vì có giá từng dòng. Chưa dùng thật vì chưa có app, demo hackathon thì ok."* | thấp |
| 5 | Nguyễn Hoàng Gia Bảo / Học viên zone E402 | Full flow: thêm FOOD001 → sửa còn 1 phần → xem giỏ | Turn 1 bot nói "không có FOOD001" (user không hiểu mã). Turn 2 "sửa còn 1 phần" bot hỏi món nào. Turn 3 giỏ trống — user dừng ~8 phút | *"Mình không hiểu FOOD001 là gì, nó bảo không có. Xem giỏ thì trống — chắc do mình gõ sai nhưng cũng không biết phải gõ sao cho đúng."* | cao |

**Mức nghiêm trọng:** *thấp* = phiền nhưng vẫn xong task · *trung bình* = mất tin / phải hỏi lại TA · *cao* = không tin kết quả / bỏ giữa chừng.

---

## 3 câu hỏi sau mỗi phiên *(ghi quote vào cột trên)*

1. *"Điều gì khó hiểu hoặc khó chịu nhất?"*
2. *"Kết quả này bạn có tin không — vì sao?"*
3. *"Bạn có dùng thật không — vì sao / vì sao chưa?"*

---

## Tổng hợp *(điền sau ≥5 phiên — copy lên slide 5 & spec §9)*

**Chủ đề lặp nhiều nhất:**  
Multi-turn mất ngữ cảnh giỏ hàng (bot báo giỏ trống sau khi vừa thêm món) · user không hiểu mã `FOODxxx` · bước chốt đơn hỏi thêm phương thức thanh toán gây do dự.

**1–2 thay đổi làm trước demo** *(→ Changelog spec §9):*  
1. Demo script tránh flow multi-turn dài — ưu tiên 1 turn/ bước (tìm món → thêm giỏ tách phiên) hoặc nhắc user gõ tên món thay vì mã.  
2. Thêm 1 dòng gợi ý phương thức thanh toán mặc định (COD) khi user nói "xác nhận đặt hàng".

**Giữ nguyên có lý do:**  
Hỏi lại khi input mơ hồ ("món đó") — 2/5 user chấp nhận vì tin hơn bot đoán bừa. Từ chối jailbreak + không chốt đơn khi thiếu SĐT/địa chỉ — không ai phản đối.

**Đưa vào backlog (slide 6 — nếu có thêm 1 tuần):**  
Lưu lịch sử chat cho LLM (fix session context) · hiển thị mã món chỉ khi user hỏi · tích hợp ShopeeFood thật · rút gọn menu dài theo category.

---

## Quote cho slide 5 *(chọn ≥2, có tên/vai)*

| Người | Quote | Dùng slide |
|---|---|---|
| _[điền tên]_ / Học viên E401 | *"Giá thì có vẻ đúng vì nó ghi rõ tên món, nhưng chưa dám chốt vì sợ đặt nhầm."* | Slide 5 — tin có điều kiện |
| _[điền tên]_ / Học viên E403 | *"Hơi phiền phải nói lại tên món, nhưng ít nhất nó không tự bịa món."* | Slide 5 — trade-off hỏi lại |
| _[điền tên]_ / Zone E402 đổi chéo | *"Xem giỏ thì trống — chắc do mình gõ sai nhưng cũng không biết phải gõ sao cho đúng."* | Slide 6 backlog UX |

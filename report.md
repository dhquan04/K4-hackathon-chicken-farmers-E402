# Giới thiệu nhóm và sản phẩm

## 1. Danh sách thành viên

| STT | Mã HV | Họ tên |
|:---:|:---:|:---|
| 1 | 2A202601448 | Vũ Bảo Chinh |
| 2 | 2A202601848 | Hoàng Thanh Sơn |
| 3 | 2A202601376 | Trịnh Hoàng Nam |
| 4 | 2A202602034 | Đinh Hoàng Quân |
| 5 | 2A202602034 | Đỗ Việt Tùng |

## Phân công công việc (Team Member Roles)

| STT | Họ và tên | Mã HV | Vai trò Production | Phân công công việc cụ thể trong dự án |
|:---:|:---|:---:|:---|:---|
| 1 | **Trịnh Hoàng Nam** | 2A202601376 | Product Manager & AI Designer | Viết `spec.md` (§1-§3), Khảo sát/mining bằng chứng, Thiết kế Slide (`demo-slides.pdf`), Phỏng vấn User Validation (`validation/`). |
| 2 | **Đinh Hoàng Quân** | 2A202602034 | Frontend & UX Developer | Lập trình Web Streamlit (`app.py`), Thiết kế giao diện Capichi UI, Tích hợp Brain-Fuel Mode & Bản đồ chỉ đường Leaflet. |
| 3 | **Vũ Bảo Chinh** | 2A202601448 | AI & Backend Engineer | Phát triển LLM Agent (`agent.py`, `workflow.py`), Viết System Prompts, Xây dựng Tools (`manage_cart`, `create_order`, `calculate_order`). |
| 4 | **Hoàng Thanh Sơn** | 2A202601848 | GIS & Integration Engineer | Tích hợp OpenMap.vn API (`get_store_location.py`), Xử lý Dataset ShopeeFood (`database.py`), Viết Unit Tests (`tests/test_tools.py`). |
| 5 | **Đỗ Việt Tùng** | 2A202601876 | AI QA & Eval Engineer *(nếu có)* | Xây dựng Golden Set 20 cases (`eval/`), Đo lường Quality Bar %, Đánh giá Red-team kịch bản rủi ro, Quay Video Demo backup. |

## 2. Mô tả ngắn sản phẩm

FoodFlow (Capichi Food) là prototype ứng dụng trợ lý AI gợi ý món ăn và đặt đồ ăn nhanh cho sinh viên tại KĐT Vinhomes Ocean Park & VinUniversity. Người dùng có thể nhập nhu cầu trực tiếp hoặc chọn chế độ thực đơn năng lượng **Brain-Fuel Mode** (tỉnh táo tập trung code Hackathon, bổ não minh mẫn, nạp calo cấp tốc), tìm kiếm theo ngân sách, sở thích ăn chay/không cay. Hệ thống sẽ tự động phân tích yêu cầu, lọc món ăn phù hợp từ dữ liệu ShopeeFood, áp mã giảm giá và đưa ra gợi ý tối ưu.

Sản phẩm được phát triển bằng Python với giao diện web Streamlit, xử lý logic bằng OpenAI API (LLM Agent) và tích hợp OpenMap.vn API để tính khoảng cách & hiển thị bản đồ lộ trình giao hàng xe máy theo thời gian thực. Prototype tập trung vào trải nghiệm đặt hàng 1-chạm nhanh chóng, trực quan và tối ưu tối đa cho thời gian nghỉ trưa ngắn ngủi của sinh viên.

"""
Capichi Food Delivery & FoodFlow AI Agent Application
Streamlit UI based on Capichi design template (sampleUI.jpg)
Integrated with OpenAI LLM and OpenMap.vn Live API
"""

import os
import sys
import json
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

# Setup sys.path to ensure module imports work properly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import backend modules and tools
try:
    from project.codebase.database import (
        load_data_from_shopeefood,
        CARTS_DB,
        ORDERS_DB,
        VOUCHERS_DB,
        parse_price,
    )
    from project.codebase.tools.get_menu import get_menu
    from project.codebase.tools.search_food import search_food
    from project.codebase.tools.manage_cart import add_to_cart, view_cart, remove_from_cart, clear_cart, update_cart
    from project.codebase.tools.calculate_order import calculate_order
    from project.codebase.tools.create_order import create_order
    from project.codebase.tools.track_order import track_order
    from project.codebase.tools.get_store_location import estimate_delivery_distance
    from project.codebase.agent import run_agent
except ImportError:
    from database import (
        load_data_from_shopeefood,
        CARTS_DB,
        ORDERS_DB,
        VOUCHERS_DB,
        parse_price,
    )
    from tools.get_menu import get_menu
    from tools.search_food import search_food
    from tools.manage_cart import add_to_cart, view_cart, remove_from_cart, clear_cart, update_cart
    from tools.calculate_order import calculate_order
    from tools.create_order import create_order
    from tools.track_order import track_order
    from tools.get_store_location import estimate_delivery_distance
    from agent import run_agent

# Initialize Streamlit Page Config
st.set_page_config(
    page_title="Capichi Food - Đặt đồ ăn & AI Agent",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check API status
has_openai = bool(os.environ.get("OPENAI_API_KEY"))
has_openmap = bool(os.environ.get("OPENMAP_API_KEY"))

# Custom CSS matching Capichi UI Design (sampleUI.jpg)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F8F9FA;
        color: #212529;
    }

    /* Main container padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Header Bar styling */
    .capichi-header-container {
        background: #FFFFFF;
        padding: 14px 24px;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        margin-bottom: 24px;
        border: 1px solid #F1F3F5;
    }
    
    .brand-title {
        color: #FF5722;
        font-size: 28px;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
    }
    
    .location-box {
        background: #F8F9FA;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        color: #495057;
        border: 1px solid #E9ECEF;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .location-highlight {
        color: #FF5722;
        font-weight: 700;
    }

    /* API Status Pill */
    .api-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #E6FCF5;
        color: #0CA678;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid #96F2D7;
    }

    /* Deal Cards & Dish Cards styling */
    .deal-card-box {
        background: #FFFFFF;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        border: 1px solid #F1F3F5;
        transition: all 0.2s ease-in-out;
        margin-bottom: 16px;
    }
    .deal-card-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(255, 87, 34, 0.12);
        border-color: #FFDCD1;
    }
    
    .card-img-wrapper {
        position: relative;
        width: 100%;
        height: 160px;
        overflow: hidden;
        background: #F1F3F5;
    }
    .card-img-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .badge-opening {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(255, 255, 255, 0.95);
        color: #212529;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    }
    
    .promo-tag-banner {
        background: #FFF0EB;
        color: #FF5722;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
        border-bottom: 1px solid #FFE0D6;
    }
    
    .card-content {
        padding: 14px;
    }
    
    .card-title-text {
        font-size: 16px;
        font-weight: 800;
        color: #1A1A1A;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .card-sub-text {
        font-size: 12px;
        color: #6C757D;
        margin-bottom: 8px;
        height: 18px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .rating-pill {
        background: #FFF9DB;
        color: #E67700;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    
    .meta-footer {
        font-size: 12px;
        color: #868E96;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Category Section Headers */
    .section-title-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    .section-title-text {
        font-size: 22px;
        font-weight: 800;
        color: #1A1A1A;
    }
    .section-detail-link {
        color: #FF5722;
        font-weight: 700;
        font-size: 14px;
        text-decoration: none;
    }
    
    /* Sidebar Filter Styling */
    .sidebar-section-title {
        font-size: 18px;
        font-weight: 800;
        color: #212529;
        margin-top: 16px;
        margin-bottom: 8px;
    }
    
    /* Streamlit Button Styling */
    div.stButton > button {
        background-color: #FF5722;
        color: white;
        font-weight: 700;
        border-radius: 10px;
        border: none;
        padding: 6px 16px;
        transition: all 0.2s;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #E64A19;
        color: white;
        box-shadow: 0 4px 12px rgba(255, 87, 34, 0.3);
    }

    /* Primary Accent Customization */
    .stSelectbox label, .stSlider label, .stRadio label {
        font-weight: 700 !important;
        color: #212529 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = "capichi_user_session"
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_demo"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "Xin chào! Mình là Trợ lý AI Capichi & FoodFlow 🍱 (OpenAI Live LLM Active). Bạn muốn ăn món gì hôm nay? Có thể hỏi mình gợi ý hoặc đặt món nhé!"
        }
    ]
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "Tất cả"

# Load database data
menu_db, store_info = load_data_from_shopeefood()

# Helper function to get cart items safely
def get_current_cart_items(session_id: str):
    res = view_cart(session_id=session_id)
    cart = res.get("cart", {})
    if isinstance(cart, dict):
        raw_items = cart.get("items", [])
    elif hasattr(cart, "items") and not callable(cart.items):
        raw_items = cart.items
    else:
        raw_items = []

    result = []
    for item in raw_items:
        if isinstance(item, dict):
            result.append(item)
        elif hasattr(item, "model_dump") and callable(item.model_dump):
            result.append(item.model_dump())
        elif hasattr(item, "dict") and callable(item.dict):
            result.append(item.dict())
        else:
            result.append(getattr(item, "__dict__", {}))
    return result

# Helper for Food Images matching categories & dishes
CATEGORY_IMAGES = {
    "gyoza": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=600&q=80",
    "matcha": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=600&q=80",
    "bánh canh": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
    "sushi": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=600&q=80",
    "ramen": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
    "mì": "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80",
    "cơm": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
    "trà": "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=600&q=80",
    "bánh": "https://images.unsplash.com/photo-1587314168485-3236d6710814?auto=format&fit=crop&w=600&q=80",
    "gà": "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=600&q=80",
    "wrap": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80",
    "default": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80"
}

def get_food_image(name: str, category: str = "") -> str:
    combined = (name + " " + category).lower()
    for key, img_url in CATEGORY_IMAGES.items():
        if key in combined:
            return img_url
    return CATEGORY_IMAGES["default"]

def format_vnd(amount: float) -> str:
    return f"{int(amount):,}đ".replace(",", ".")


# --- TOP HEADER NAVIGATION BAR ---
header_col1, header_col2, header_col3, header_col4 = st.columns([2.5, 3.5, 4.5, 2.5])

with header_col1:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:30px;">🍱</span>
            <span style="font-size:26px; font-weight:800; color:#FF5722; letter-spacing:-0.5px;">Capichi</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_col2:
    st.markdown(
        """
        <div class="location-box">
            <span>📍</span>
            <span><strong>Địa chỉ nhận hàng</strong><br/>
            <span class="location-highlight">80 P. Duy Tân, Dịch Vọng Hậu... ❯</span></span>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_col3:
    search_query = st.text_input(
        "Search",
        placeholder="Tìm kiếm theo tên nhà hàng, tên món...",
        label_visibility="collapsed",
        key="header_search_input"
    )

with header_col4:
    cart_items_count = len(get_current_cart_items(st.session_state.session_id))
    c_btn1, c_btn2 = st.columns([1, 1])
    with c_btn1:
        st.markdown(
            """<div style="text-align:center; padding-top:6px;"><strong style="color:#FF5722;">Đăng nhập</strong></div>""",
            unsafe_allow_html=True
        )
    with c_btn2:
        st.write(f"🛒 **Giỏ ({cart_items_count})**")

# Display Active API Status Badges
st.markdown(
    f"""
    <div style="display:flex; gap:12px; margin-bottom:12px;">
        <span class="api-status-pill">{'🟢 OpenAI LLM Connected' if has_openai else '⚪ OpenAI LLM Offline'}</span>
        <span class="api-status-pill">{'🟢 OpenMap.vn Live API Connected' if has_openmap else '⚪ OpenMap API Offline'}</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# --- MAIN CONTENT LAYOUT (Sidebar left 25%, Main Right 75%) ---
left_sidebar_col, main_content_col = st.columns([2.5, 7.5])


# === LEFT SIDEBAR / FILTER PANEL ===
with left_sidebar_col:
    st.markdown('<div class="sidebar-section-title">Trang chủ</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<div class="sidebar-section-title">Khoảng cách</div>', unsafe_allow_html=True)
    
    distance_option = st.select_slider(
        "Khoảng cách tối đa",
        options=["Tất cả", "3km", "5km", "10km"],
        value="Tất cả",
        label_visibility="collapsed"
    )
    st.caption(f"Đang chọn: **{distance_option}**")
    
    st.markdown("---")
    st.markdown('<div class="sidebar-section-title">Danh mục</div>', unsafe_allow_html=True)
    
    categories = ["Tất cả", "Sushi", "Khuyến mãi", "Mì Ramen", "Món Nhật", "Cơm", "Đồ uống", "Đồ ăn nhanh"]
    selected_cat = st.radio(
        "Lọc theo danh mục món:",
        categories,
        index=0,
        label_visibility="collapsed",
        key="radio_category"
    )
    st.session_state.selected_category = selected_cat

    st.markdown("---")
    st.markdown('<div class="sidebar-section-title">Bộ lọc bổ sung</div>', unsafe_allow_html=True)
    max_price_filter = st.slider("Mức giá tối đa (VNĐ)", min_value=10000, max_value=200000, value=200000, step=10000, format="%dđ")
    is_vegan_only = st.checkbox("🌱 Món ăn chay")


# === RIGHT MAIN CONTENT COLUMN ===
with main_content_col:
    
    # 1. SECTION: ƯU ĐÃI (Promotional Offers Card Grid matching sampleUI.jpg)
    st.markdown(
        """
        <div class="section-title-bar">
            <span class="section-title-text">Ưu đãi</span>
            <a href="#" class="section-detail-link">Chi tiết ❯</a>
        </div>
        """,
        unsafe_allow_html=True
    )

    promo_col1, promo_col2, promo_col3 = st.columns(3)

    # CARD 1: GYOZAYA RYU
    with promo_col1:
        st.markdown(
            f"""
            <div class="deal-card-box">
                <div class="card-img-wrapper">
                    <img src="{CATEGORY_IMAGES['gyoza']}" alt="Gyoza Ryu">
                    <div class="badge-opening">Mở cửa hôm nay từ 16:00</div>
                </div>
                <div class="promo-tag-banner">
                    ⚡ Giảm giá 10%
                </div>
                <div class="card-content">
                    <div class="card-title-text">GYOZAYA RYU</div>
                    <div class="card-sub-text">Gyozaya Ryu: Famous for Gyoza, Loved f...</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="rating-pill">★ 4.7 (327)</span>
                    </div>
                    <div class="meta-footer">Nhận đặt trước • 3.00 km</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Xem cửa hàng & Đặt", key="btn_promo_1"):
            st.session_state.header_search_input = "Gyoza"
            st.rerun()

    # CARD 2: TOUS les JOURS Duy Tân
    with promo_col2:
        st.markdown(
            f"""
            <div class="deal-card-box">
                <div class="card-img-wrapper">
                    <img src="{CATEGORY_IMAGES['matcha']}" alt="TOUS les JOURS">
                </div>
                <div class="promo-tag-banner">
                    ⚡ Miễn phí giao hàng cho đơn từ 50K + 4 mã...
                </div>
                <div class="card-content">
                    <div class="card-title-text">TOUS les JOURS Duy Tân</div>
                    <div class="card-sub-text">Bánh ngọt, Trà Matcha & Thức uống cao cấp</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="rating-pill">★ 5.0 (3)</span>
                    </div>
                    <div class="meta-footer">0 - 5p • 0.20 km</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Xem cửa hàng & Đặt", key="btn_promo_2"):
            st.session_state.header_search_input = "Matcha"
            st.rerun()

    # CARD 3: Bánh canh ghẹ Út Còi - Duy Tân
    with promo_col3:
        st.markdown(
            f"""
            <div class="deal-card-box">
                <div class="card-img-wrapper">
                    <img src="{CATEGORY_IMAGES['bánh canh']}" alt="Bánh canh ghẹ">
                </div>
                <div class="promo-tag-banner">
                    ⚡ Miễn phí giao hàng cho đơn từ 50K...
                </div>
                <div class="card-content">
                    <div class="card-title-text">Bánh canh ghẹ Út Còi - D...</div>
                    <div class="card-sub-text">Bánh Canh Ghẹ Đầu tiên và Ngon nhất...</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="rating-pill">★ 5.0 (3)</span>
                    </div>
                    <div class="meta-footer">16 - 21p • 0.50 km</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Xem cửa hàng & Đặt", key="btn_promo_3"):
            st.session_state.header_search_input = "Bánh canh"
            st.rerun()


    # 2. SECTION: ĐỀ XUẤT CHO BẠN (Dynamic Dishes & Restaurants Grid)
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-title-bar">
            <span class="section-title-text">Đề xuất cho bạn</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    filtered_items = []
    for item_id, item in menu_db.items():
        if item.price > max_price_filter:
            continue
        if is_vegan_only and not item.is_vegetarian:
            continue
        if search_query and search_query.strip():
            sq = search_query.strip().lower()
            if sq not in item.name.lower() and sq not in item.category.lower() and sq not in (item.description or "").lower():
                continue
        if selected_cat != "Tất cả":
            sc_lower = selected_cat.lower()
            cat_lower = item.category.lower()
            if sc_lower == "khuyến mãi":
                pass
            elif sc_lower not in cat_lower and cat_lower not in sc_lower:
                continue
                
        filtered_items.append(item)

    if not filtered_items:
        st.info("Không tìm thấy món ăn nào phù hợp với bộ lọc. Vui lòng thử tìm từ khóa khác!")
    else:
        items_per_row = 3
        for i in range(0, min(len(filtered_items), 18), items_per_row):
            cols = st.columns(items_per_row)
            row_items = filtered_items[i : i + items_per_row]
            
            for idx, item in enumerate(row_items):
                with cols[idx]:
                    img_url = get_food_image(item.name, item.category)
                    price_str = format_vnd(item.price)
                    
                    st.markdown(
                        f"""
                        <div class="deal-card-box">
                            <div class="card-img-wrapper">
                                <img src="{img_url}" alt="{item.name}">
                            </div>
                            <div class="card-content">
                                <div class="card-title-text">{item.name}</div>
                                <div class="card-sub-text">{item.category} • {item.description or 'Món ăn đặc sản thơm ngon'}</div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                                    <span style="font-size:16px; font-weight:800; color:#FF5722;">{price_str}</span>
                                    <span class="rating-pill">★ 4.8</span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.button("➕ Giỏ hàng", key=f"add_cart_{item.id}_{i}_{idx}"):
                            res = add_to_cart(
                                session_id=st.session_state.session_id,
                                item_id=item.id,
                                quantity=1
                            )
                            st.toast(f"✅ Đã thêm '{item.name}' vào giỏ hàng!", icon="🛒")
                            st.rerun()
                    with b2:
                        if st.button("💬 Hỏi AI", key=f"ask_ai_{item.id}_{i}_{idx}"):
                            prompt_msg = f"Tư vấn cho mình về món '{item.name}' giá {price_str} xem có ngon không?"
                            res = run_agent(
                                user_id=st.session_state.user_id,
                                message=prompt_msg,
                                session_id=st.session_state.session_id
                            )
                            ai_reply = res.get("ai_response") or res.get("message") or "Món này rất ngon và đậm đà!"
                            st.session_state.chat_history.append({"role": "user", "content": prompt_msg})
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                            st.toast("🤖 OpenAI AI đã trả lời!", icon="💬")


# === SIDEBAR WIDGETS: GIỎ HÀNG & TRỢ LÝ AI CHATBOT ===
st.sidebar.markdown("### 🛒 Quản lý & 🤖 Trợ lý AI")

sidebar_tabs = st.sidebar.tabs(["🛒 Giỏ hàng", "🤖 Trợ lý OpenAI", "📦 Đơn hàng"])

# TAB 1: GIỎ HÀNG (CART)
with sidebar_tabs[0]:
    st.write("#### Chi tiết giỏ hàng")
    cart_items = get_current_cart_items(st.session_state.session_id)
    
    if not cart_items:
        st.info("Giỏ hàng của bạn đang trống. Chọn món ăn ở danh sách để thêm vào giỏ!")
    else:
        for idx, ci in enumerate(cart_items):
            item_name = ci.get("item_name") or ci.get("name") or "Món ăn"
            price = ci.get("price", 0)
            quantity = ci.get("quantity", 1)
            item_id = ci.get("item_id") or ci.get("id")
            
            c_info, c_qty = st.columns([3, 2])
            with c_info:
                st.write(f"**{item_name}**")
                st.caption(f"{format_vnd(price)} / phần")
            with c_qty:
                new_q = st.number_input("SL", min_value=0, max_value=20, value=quantity, key=f"cart_qty_{item_id}_{idx}")
                if new_q != quantity:
                    update_cart(session_id=st.session_state.session_id, item_id=item_id, quantity=new_q)
                    st.rerun()
            st.divider()

        subtotal = sum(ci.get("price", 0) * ci.get("quantity", 1) for ci in cart_items)
        st.write(f"**Tạm tính:** {format_vnd(subtotal)}")
        
        voucher_input = st.text_input("Mã giảm giá (FREESHIP / BATCH03)", value="FREESHIP")
        calc_res = calculate_order(session_id=st.session_state.session_id, voucher_code=voucher_input)
        
        if calc_res.get("status") == "success":
            st.success(f"Khuyến mãi: -{format_vnd(calc_res.get('discount_amount', 0))}")
            st.write(f"Phí giao hàng: {format_vnd(calc_res.get('delivery_fee', 0))}")
            st.markdown(f"### Tổng thanh toán: **{format_vnd(calc_res.get('total', 0))}**")
            
            st.markdown("##### Thông tin người nhận")
            c_name = st.text_input("Họ và tên", value="Nguyễn Văn A")
            c_phone = st.text_input("Số điện thoại", value="0987654321")
            c_addr = st.text_input("Địa chỉ giao hàng", value="80 P. Duy Tân, Dịch Vọng Hậu, Cầu Giấy, Hà Nội")
            c_pay = st.selectbox("Phương thức thanh toán", ["COD (Tiền mặt)", "MOMO", "ZALOPAY", "BANK_TRANSFER"])

            if c_addr:
                dist_info = estimate_delivery_distance(c_addr)
                st.caption(f"📍 Khoảng cách ({dist_info.get('distance_source', 'OpenMap')}): **{dist_info.get('estimated_distance_km')} km** ({dist_info.get('estimated_delivery_minutes')} phút)")

            if st.button("🚀 ĐẶT HÀNG NGAY", key="btn_submit_order"):
                order_res = create_order(
                    session_id=st.session_state.session_id,
                    customer_name=c_name,
                    phone_number=c_phone,
                    delivery_address=c_addr,
                    payment_method=c_pay.split()[0],
                    voucher_code=voucher_input
                )
                if order_res.get("status") == "success":
                    st.balloons()
                    st.success(f"🎉 Đặt hàng thành công! Mã đơn: **{order_res.get('order', {}).get('order_id')}**")
                    st.rerun()
                else:
                    st.error(order_res.get("message", "Đã có lỗi xảy ra khi tạo đơn hàng."))
        
        if st.button("🗑️ Xóa toàn bộ giỏ hàng", key="btn_clear_cart"):
            clear_cart(session_id=st.session_state.session_id)
            st.rerun()


# TAB 2: TRỢ LÝ AI CHATBOT (OPENAI LLM AGENT)
with sidebar_tabs[1]:
    st.write("#### Trợ lý OpenAI FoodFlow 🤖")
    st.caption("Tư vấn thực đơn bằng LLM, gợi ý món ăn, tìm mã giảm giá & tạo đơn tự động.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    sug_c1, sug_c2 = st.columns(2)
    with sug_c1:
        if st.button("🍱 Gợi ý 100k", key="sug_1"):
            st.session_state.chat_input_val = "Gợi ý cho mình thực đơn 2 người khoảng 100k"
    with sug_c2:
        if st.button("🎟️ Mã giảm giá", key="sug_2"):
            st.session_state.chat_input_val = "Hôm nay có mã giảm giá gì hot không?"

    user_input = st.chat_input("Nhập tin nhắn cho AI...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("OpenAI LLM đang phản hồi..."):
                response = run_agent(
                    user_id=st.session_state.user_id,
                    message=user_input,
                    session_id=st.session_state.session_id
                )
                ai_text = response.get("ai_response") or response.get("message") or "Đã ghi nhận yêu cầu của bạn!"
                engine = response.get("llm_engine", "AI Engine")
                st.write(ai_text)
                st.caption(f"Powered by: **{engine}**")
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})


# TAB 3: THEO DÕI ĐƠN HÀNG (TRACK ORDER)
with sidebar_tabs[2]:
    st.write("#### Theo dõi trạng thái đơn hàng 📦")
    track_input = st.text_input("Nhập mã đơn hàng (ví dụ: ORD-XXXXX)", key="track_order_input")
    if st.button("Tra cứu đơn hàng", key="btn_track_order"):
        if track_input:
            t_res = track_order(order_id=track_input.strip())
            if t_res.get("status") == "success":
                ord_data = t_res.get("order", {})
                st.success(f"Trạng thái: **{ord_data.get('status')}**")
                st.write(f"Tổng tiền: **{format_vnd(ord_data.get('total_amount', 0))}**")
                st.write(f"Địa chỉ: {ord_data.get('customer', {}).get('delivery_address')}")
            else:
                st.warning(t_res.get("message", "Không tìm thấy đơn hàng."))

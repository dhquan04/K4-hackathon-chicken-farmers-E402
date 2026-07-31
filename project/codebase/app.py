"""
Capichi Food Delivery & FoodFlow AI Agent Application
Streamlit UI based on Capichi design template (sampleUI.jpg)
Integrated with OpenAI LLM and OpenMap.vn Live API
"""

import os
import sys
import json
import streamlit as st
import streamlit.components.v1 as components
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
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }

    /* Unified Header Navigation Bar Styling */
    .header-location-pill {
        background: #F8F9FA;
        border: 1px solid #E9ECEF;
        padding: 6px 14px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.2s ease-in-out;
    }
    .header-location-pill:hover {
        border-color: #FF5722;
        background: #FFF0EB;
    }

    .header-cart-badge {
        background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%);
        color: #FFFFFF;
        padding: 8px 16px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        box-shadow: 0 4px 12px rgba(255, 87, 34, 0.25);
        font-weight: 700;
        margin-top: 2px;
    }
    .cart-count-pill {
        background: #FFFFFF;
        color: #FF5722;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 800;
    }

    .header-subbar {
        background: #FFFFFF;
        border: 1px solid #F1F3F5;
        padding: 8px 16px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .status-badge {
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .status-online {
        background: #E6FCF5;
        color: #0CA678;
        border: 1px solid #96F2D7;
    }
    .status-offline {
        background: #F8F9FA;
        color: #868E96;
        border: 1px solid #E9ECEF;
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
if "latest_order_map_info" not in st.session_state:
    st.session_state.latest_order_map_info = None

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


def render_delivery_route_map(dist_info: dict, customer_name: str = "Khách hàng", map_height: int = 560):
    """
    Renders an interactive Leaflet/OSM map displaying motorcycle route between store and delivery destination,
    along with estimated delivery time badge.
    """
    store_coords = dist_info.get("store_coords", [20.9960, 105.9560])
    dest_coords = dist_info.get("dest_coords", [20.989255, 105.945574])


    waypoints = dist_info.get("route_waypoints", [store_coords, dest_coords])
    store_name = dist_info.get("store_name", "ShopeeFood Ocean Park")
    store_addr = dist_info.get("store_address", "Vinhomes Ocean Park")
    user_addr = dist_info.get("user_address", "Địa chỉ người nhận")
    est_mins = dist_info.get("estimated_delivery_minutes", 15)
    est_km = dist_info.get("estimated_distance_km", 2.5)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            #map {{ width: 100%; height: {map_height}px; border-radius: 12px; border: 2px solid #FF5722; }}
            .delivery-card-overlay {{
                position: absolute;
                top: 10px;
                left: 10px;
                right: 10px;
                z-index: 1000;
                background: rgba(255, 255, 255, 0.97);
                padding: 10px 14px;
                border-radius: 10px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.22);
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-left: 5px solid #FF5722;
            }}
            .time-badge {{ font-size: 15px; font-weight: 800; color: #FF5722; }}
            .sub-info {{ font-size: 12px; color: #495057; margin-top: 2px; }}
        </style>
    </head>
    <body>
        <div style="position: relative;">
            <div class="delivery-card-overlay">
                <div>
                    <div class="time-badge">🛵 Đang giao hàng - Dự kiến: {est_mins} phút</div>
                    <div class="sub-info">Khoảng cách: <strong>{est_km} km</strong> • Thời gian chuẩn Xe máy</div>
                </div>
                <div>
                    <span style="background:#FFF0EB; color:#FF5722; padding:4px 10px; border-radius:12px; font-size:12px; font-weight:700;">ShopeeFood Express</span>
                </div>
            </div>
            <div id="map"></div>
        </div>

        <script>
            var map = L.map('map').setView([{store_coords[0]}, {store_coords[1]}], 14);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);

            // Store Marker (Red/Orange)
            var storeIcon = L.divIcon({{
                className: 'custom-pin-store',
                html: "<div style='background-color:#FF5722;color:white;padding:5px 8px;border-radius:16px;font-weight:bold;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.3);white-space:nowrap;'>🏬 {store_name[:18]}</div>",
                iconSize: [130, 28],
                iconAnchor: [65, 14]
            }});
            L.marker([{store_coords[0]}, {store_coords[1]}], {{icon: storeIcon}})
                .addTo(map)
                .bindPopup("<b>🏬 {store_name}</b><br>{store_addr}");

            // Destination Marker (Green)
            var destIcon = L.divIcon({{
                className: 'custom-pin-dest',
                html: "<div style='background-color:#2B8A3E;color:white;padding:5px 8px;border-radius:16px;font-weight:bold;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.3);white-space:nowrap;'>🏠 {customer_name}</div>",
                iconSize: [110, 28],
                iconAnchor: [55, 14]
            }});
            L.marker([{dest_coords[0]}, {dest_coords[1]}], {{icon: destIcon}})
                .addTo(map)
                .bindPopup("<b>🏠 Giao tới: {customer_name}</b><br>{user_addr}");

            // Draw motorcycle road route polyline from OpenMap.vn/OSRM
            var latlngs = {json.dumps(waypoints)};
            var polyline = L.polyline(latlngs, {{color: '#FF5722', weight: 5, opacity: 0.9}}).addTo(map);

            // Fit map to route bounds
            if (latlngs.length > 1) {{
                var bounds = L.latLngBounds(latlngs);
                map.fitBounds(bounds, {{padding: [50, 50]}});
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=map_height + 15)





# Helper for Food Images matching categories & dishes
CATEGORY_IMAGES = {
    "gà": "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=600&q=80",
    "mì": "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80",
    "mỳ": "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80",
    "bún": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
    "phở": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=600&q=80",
    "cháo": "https://images.unsplash.com/photo-1541832676-9b763b0239ab?auto=format&fit=crop&w=600&q=80",
    "bánh tráng": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80",
    "bánh": "https://images.unsplash.com/photo-1587314168485-3236d6710814?auto=format&fit=crop&w=600&q=80",
    "trà": "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=600&q=80",
    "nước": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=600&q=80",
    "cơm": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
    "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80",
    "burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80",
    "lẩu": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=600&q=80",
    "tokbokki": "https://images.unsplash.com/photo-1580651315530-69c8e0026377?auto=format&fit=crop&w=600&q=80",
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


current_view = st.session_state.get("active_view", "dishes")

if current_view == "map" and st.session_state.get("selected_dish_map_info"):
    map_info = st.session_state.selected_dish_map_info
    dist_info = map_info["dist_info"]
    item_name = map_info["item_name"]

    # TOP BACK BUTTON & TITLE BANNER
    b_col, _ = st.columns([2.5, 7.5])
    with b_col:
        if st.button("⬅️ Quay lại chọn món", key="btn_back_to_dishes_fullscreen"):
            st.session_state.active_view = "dishes"
            st.rerun()

    st.markdown(
        f"""
        <div style="background:#FFF0EB; border-left:5px solid #FF5722; padding:14px 18px; border-radius:12px; margin-bottom:14px;">
            <h3 style="margin:0; color:#1A1A1A;">🗺️ Lộ trình giao hàng xe máy cho món: <span style="color:#FF5722;">{item_name}</span></h3>
            <div style="font-size:14px; color:#495057; margin-top:4px;">
                📍 Quán: <strong>{dist_info.get('store_name')}</strong> • Khoảng cách: <strong>{dist_info.get('estimated_distance_km')} km</strong> • Dự kiến giao: <strong>{dist_info.get('estimated_delivery_minutes')} phút (Xe máy)</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    render_delivery_route_map(dist_info, "Khách hàng (Ocean Park)", map_height=580)



else:
    # --- UNIFIED TOP HEADER NAVIGATION BAR ---
    header_col1, header_col2, header_col3, header_col4 = st.columns([3.0, 3.2, 4.0, 1.8])

    with header_col1:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:28px;">🍱</span>
                <div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:22px; font-weight:800; color:#FF5722; letter-spacing:-0.5px; line-height:1;">FoodFlow</span>
                        <span class="status-badge {'status-online' if has_openmap else 'status-offline'}">
                            {'🟢' if has_openmap else '⚪'} OpenMap
                        </span>
                    </div>
                    <div style="font-size:9px; color:#868E96; font-weight:700; text-transform:uppercase; margin-top:2px;">ShopeeFood Ocean Park</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_col2:
        st.markdown(
            """
            <div class="header-location-pill">
                <span style="font-size:18px;">📍</span>
                <div>
                    <div style="font-size:10px; color:#868E96; text-transform:uppercase; font-weight:700; line-height:1;">Giao hàng tới</div>
                    <div style="font-size:12px; font-weight:700; color:#212529; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px;">
                        KĐT Vinhomes Ocean Park 1
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_col3:
        search_query = st.text_input(
            "Search",
            placeholder="🔍 Tìm kiếm theo tên nhà hàng, tên món ăn...",
            label_visibility="collapsed",
            key="header_search_input"
        )

    with header_col4:
        cart_items_count = len(get_current_cart_items(st.session_state.session_id))
        if st.button(f"🛒 Giỏ hàng ({cart_items_count})", key="btn_header_cart_action", use_container_width=True):
            st.session_state.active_view = "dishes"
            st.toast("🛒 Mời bạn xem chi tiết giỏ hàng & đặt hàng tại Cột bên trái (Sidebar)!", icon="🛒")
            st.rerun()

    # --- MAIN CONTENT LAYOUT (Sidebar left 25%, Main Right 75%) ---
    left_sidebar_col, main_content_col = st.columns([2.5, 7.5])

    # === LEFT SIDEBAR / FILTER PANEL ===
    with left_sidebar_col:
        st.markdown('<div class="sidebar-section-title">Danh mục</div>', unsafe_allow_html=True)
        
        # Dynamically source categories from loaded menu_db dataset
        raw_categories = sorted(list(set(item.category for item in menu_db.values())))
        categories = ["Tất cả"] + raw_categories
        selected_cat = st.selectbox(
            "Lọc theo danh mục món:",
            categories,
            index=0,
            key="select_category"
        )
        st.session_state.selected_category = selected_cat

    # === RIGHT MAIN CONTENT COLUMN ===
    with main_content_col:
        
        # # 1. SECTION: NHÀ HÀNG NỔI BẬT (Dynamic Stores from ShopeeFood Dataset)
        # st.markdown(
        #     """
        #     <div class="section-title-bar">
        #         <span class="section-title-text">Nhà hàng ShopeeFood Ocean Park</span>
        #     </div>
        #     """,
        #     unsafe_allow_html=True
        # )

        # branches_list = store_info.branches if store_info and store_info.branches else []
        # if branches_list:
        #     top_branches = branches_list[:3]
        #     promo_cols = st.columns(len(top_branches))
        #     for idx, branch in enumerate(top_branches):
        #         with promo_cols[idx]:
        #             branch_img = get_food_image(branch.branch_name)
        #             st.markdown(
        #                 f"""
        #                 <div class="deal-card-box">
        #                     <div class="card-img-wrapper">
        #                         <img src="{branch_img}" alt="{branch.branch_name}">
        #                         <div class="badge-opening">08:00 - 22:00</div>
        #                     </div>
        #                     <div class="promo-tag-banner">
        #                         ⚡ ShopeeFood Ocean Park
        #                     </div>
        #                     <div class="card-content">
        #                         <div class="card-title-text">{branch.branch_name}</div>
        #                         <div class="card-sub-text">{branch.address}</div>
        #                         <div style="display:flex; justify-content:space-between; align-items:center;">
        #                             <span class="rating-pill">★ 4.8</span>
        #                         </div>
        #                         <div class="meta-footer">Vinhomes Ocean Park 1</div>
        #                     </div>
        #                 </div>
        #                 """,
        #                 unsafe_allow_html=True
        #             )
        #             if st.button("Xem món của quán", key=f"btn_branch_{branch.branch_id}"):
        #                 # Filter by branch keyword
        #                 short_name = branch.branch_name.split("-")[0].strip()
        #                 st.session_state.header_search_input = short_name
        #                 st.rerun()

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
                                item_branch = getattr(item, "branch_id", None)
                                if not item_branch and getattr(item, "id", None) in menu_db:
                                    item_branch = getattr(menu_db[item.id], "branch_id", None)
                                dist_info = estimate_delivery_distance("Toà S2.06 Vinhomes Ocean Park, Gia Lâm, Hà Nội", branch_id=item_branch)

                                st.session_state.selected_dish_map_info = {
                                    "item_name": item.name,
                                    "item_price": item.price,
                                    "dist_info": dist_info
                                }


                                st.session_state.active_view = "map"
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
            c_addr = st.text_input("Địa chỉ giao hàng", value="Toà S2.06 Vinhomes Ocean Park, Gia Lâm, Hà Nội")
            c_pay = st.selectbox("Phương thức thanh toán", ["COD (Tiền mặt)", "MOMO", "ZALOPAY", "BANK_TRANSFER"])

            if c_addr:
                cart_branch = None
                if cart_items:
                    first_item_id = cart_items[0].get("item_id") or cart_items[0].get("id")
                    if first_item_id and first_item_id in menu_db:
                        cart_branch = getattr(menu_db[first_item_id], "branch_id", None)
                dist_info = estimate_delivery_distance(c_addr, branch_id=cart_branch)
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
                    ord_id = order_res.get("order", {}).get("order_id")
                    ord_details = order_res.get("order", {})
                    st.session_state.latest_order_map_info = {
                        "dist_info": dist_info,
                        "customer_name": c_name,
                        "order_id": ord_id
                    }
                    if "my_orders" not in st.session_state:
                        st.session_state.my_orders = []
                    st.session_state.my_orders.insert(0, {
                        "order_id": ord_id,
                        "details": ord_details,
                        "dist_info": dist_info
                    })
                    st.toast(f"🎉 Đặt hàng thành công! Đơn {ord_id} đã được lưu vào Tab Đơn hàng.", icon="📦")
                    st.rerun()
                else:
                    st.error(order_res.get("message", "Đã có lỗi xảy ra khi tạo đơn hàng."))

        # Display Live Motorcycle Delivery Map on Order Placement
        if st.session_state.latest_order_map_info:
            map_data = st.session_state.latest_order_map_info
            st.success(f"🎉 Đặt hàng thành công! Mã đơn: **{map_data.get('order_id')}**")
            st.markdown("##### 🗺️ Bản đồ chỉ đường xe máy & Thời gian giao hàng")
            render_delivery_route_map(map_data["dist_info"], map_data["customer_name"])

        if st.button("🗑️ Xóa toàn bộ giỏ hàng", key="btn_clear_cart"):
            st.session_state.latest_order_map_info = None
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


# TAB 3: DANH SÁCH ĐƠN HÀNG CỦA TÔI
with sidebar_tabs[2]:
    st.write("#### 📦 Đơn hàng của tôi")
    
    my_orders = st.session_state.get("my_orders", [])
    if not my_orders:
        st.info("Bạn chưa có đơn hàng nào. Hãy chọn món và nhấn '🚀 Đặt hàng ngay'!")
    else:
        for idx, o in enumerate(my_orders):
            ord_id = o.get("order_id")
            details = o.get("details", {})
            dist_info = o.get("dist_info", {})
            
            with st.expander(f"📦 Đơn #{ord_id} • {details.get('total_amount_formatted', '0đ')}", expanded=(idx == 0)):
                st.markdown(f"**Trạng thái:** 🟢 Đang chuẩn bị (Dự kiến {details.get('estimated_delivery', '20-30 phút')})")
                st.write(f"**Khách hàng:** {details.get('customer_name')} ({details.get('phone_number')})")
                st.write(f"**Địa chỉ giao:** {details.get('delivery_address')}")
                st.write(f"**Thanh toán:** {details.get('payment_method')} • **Tổng:** {details.get('total_amount_formatted')}")
                
                st.markdown("**Danh sách món:**")
                for item in details.get("items", []):
                    st.write(f"- {item.get('name')} x{item.get('quantity')} ({item.get('price_formatted')})")
                
                if dist_info and st.button(f"🗺️ Xem bản đồ giao hàng ({ord_id})", key=f"btn_view_map_{ord_id}_{idx}"):
                    st.session_state.selected_dish_map_info = {
                        "item_name": f"Đơn hàng {ord_id}",
                        "dist_info": dist_info
                    }
                    st.session_state.active_view = "map"
                    st.rerun()

    st.divider()
    

"""
In-Memory Database & Data Store Manager for Food Ordering Chatbot
Data Source: ShopeeFood Full Details Dataset (shopeefood_full_details.json)
"""

import json
import os
import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from project.codebase.schemas import (
        Cart,
        CartItem,
        CustomerInfo,
        MenuItem,
        Order,
        RestaurantBranch,
        RestaurantInfo,
        Voucher,
    )
except ImportError:
    from schemas import (
        Cart,
        CartItem,
        CustomerInfo,
        MenuItem,
        Order,
        RestaurantBranch,
        RestaurantInfo,
        Voucher,
    )

# Global In-Memory Storage
MENU_DB: Dict[str, MenuItem] = {}
CARTS_DB: Dict[str, Cart] = {}
ORDERS_DB: Dict[str, Order] = {}
VOUCHERS_DB: Dict[str, Voucher] = {}
RESTAURANT_INFO_CACHE: Optional[RestaurantInfo] = None

# Dataset Path Resolution
BASE_DIR = os.path.dirname(__file__)
SHOPEEFOOD_FILE_PATH = os.path.join(BASE_DIR, "data", "shopeefood_full_details.json")
ROOT_DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "data", "shopeefood_full_details.json"))


def normalize_text(text: str) -> str:
    """Normalizes Vietnamese text for consistent food item searching and matching."""
    if not text:
        return ""
    text = text.lower().strip()
    # Normalize y/i vowel variants in Vietnamese food names (e.g. mì <-> mỳ)
    text = re.sub(r'\bmì\b', 'mỳ', text)
    text = text.replace('ì', 'ỳ').replace('í', 'ý').replace('ỉ', 'ỷ').replace('ĩ', 'ỹ').replace('ị', 'ỵ')
    # Collapse multiple whitespaces
    text = re.sub(r'\s+', ' ', text)
    return text


def remove_accents(text: str) -> str:
    """Strips Vietnamese diacritics for fallback accent-insensitive matching."""
    if not text:
        return ""
    text = normalize_text(text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFKD', text)
    unaccented = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return unaccented.replace('y', 'i')


def _get_data_file_path() -> str:
    if os.path.exists(SHOPEEFOOD_FILE_PATH):
        return SHOPEEFOOD_FILE_PATH
    if os.path.exists(ROOT_DATA_PATH):
        return ROOT_DATA_PATH
    return SHOPEEFOOD_FILE_PATH


def parse_price(price_val) -> float:
    """Converts price string like '65.000đ' or '65000' to float."""
    if isinstance(price_val, (int, float)):
        return float(price_val)
    if not price_val:
        return 0.0
    clean = str(price_val).replace("đ", "").replace(".", "").replace(",", "").strip()
    try:
        return float(clean)
    except ValueError:
        return 0.0


def load_data_from_shopeefood() -> Tuple[Dict[str, MenuItem], Optional[RestaurantInfo]]:
    """Loads food menu and restaurant branches from ShopeeFood dataset into MENU_DB and RESTAURANT_INFO_CACHE."""
    global MENU_DB, RESTAURANT_INFO_CACHE
    
    file_path = _get_data_file_path()
    if not os.path.exists(file_path):
        return MENU_DB, RESTAURANT_INFO_CACHE

    with open(file_path, "r", encoding="utf-8") as f:
        restaurants_data = json.load(f)

    # Import OpenMap.vn geocoder dynamically
    try:
        from project.codebase.tools.get_store_location import geocode_address
    except ImportError:
        try:
            from tools.get_store_location import geocode_address
        except ImportError:
            geocode_address = None

    MENU_DB.clear()
    branches: List[RestaurantBranch] = []
    
    dish_idx = 1
    for r_idx, r in enumerate(restaurants_data, 1):
        res_name = r.get("name", f"Nhà hàng {r_idx}")
        res_addr = r.get("address", "Hà Nội")
        res_url = r.get("url", "https://shopeefood.vn")
        
        branch_id = f"BRANCH{r_idx:02d}"
        
        branch = RestaurantBranch(
            branch_id=branch_id,
            branch_name=res_name,
            address=res_addr,
            latitude=20.9950 + (r_idx * 0.001),
            longitude=105.9550 + (r_idx * 0.001),
            google_maps_url=f"https://www.google.com/maps/search/?api=1&query={res_addr}",
            embed_map_url=res_url,
            is_active=True
        )
        branches.append(branch)

        for menu_cat in r.get("menu", []):
            cat_name = menu_cat.get("category", "Món ăn").strip()
            for dish in menu_cat.get("dishes", []):
                d_name = dish.get("dish_name", "").strip()
                if not d_name:
                    continue
                    
                price = parse_price(dish.get("price"))
                desc = dish.get("description", "").strip()
                is_avail = dish.get("is_available", True)
                
                lower_text = f"{d_name} {desc} {cat_name}".lower()
                is_veg = "chay" in lower_text
                is_spicy = any(k in lower_text for k in ["cay", "ớt", "kim chi", "lẩu thái", "sốt cay"])

                item_id = f"FOOD{dish_idx:03d}"
                menu_item = MenuItem(
                    id=item_id,
                    name=d_name,
                    category=cat_name,
                    price=price,
                    description=desc if desc else f"{d_name} tại {res_name}",
                    branch_id=branch_id,
                    is_vegetarian=is_veg,
                    is_spicy=is_spicy,
                    allergens=[],
                    is_available=is_avail
                )
                MENU_DB[item_id] = menu_item
                dish_idx += 1

    RESTAURANT_INFO_CACHE = RestaurantInfo(
        restaurant_name="Hệ thống Quán ăn ShopeeFood Ocean Park",
        hotline="1900 1234",
        opening_hours="08:00 - 22:00",
        branches=branches
    )

    return MENU_DB, RESTAURANT_INFO_CACHE


def load_menu() -> Dict[str, MenuItem]:
    """Loads food menu from dataset."""
    global MENU_DB
    if not MENU_DB:
        load_data_from_shopeefood()
    return MENU_DB


def load_restaurant_info() -> Optional[RestaurantInfo]:
    """Loads restaurant and branch info from dataset."""
    global RESTAURANT_INFO_CACHE
    if not RESTAURANT_INFO_CACHE:
        load_data_from_shopeefood()
    return RESTAURANT_INFO_CACHE


def init_vouchers() -> Dict[str, Voucher]:
    """Initializes sample discount vouchers."""
    global VOUCHERS_DB
    vouchers = [
        Voucher(code="BATCH03", discount_percentage=0.20, max_discount_amount=40000.0, min_order_amount=50000.0),
        Voucher(code="HELLOGROUP9", discount_percentage=0.15, max_discount_amount=30000.0, min_order_amount=30000.0),
        Voucher(code="FREESHIP", discount_percentage=0.0, max_discount_amount=15000.0, min_order_amount=40000.0),
    ]
    for v in vouchers:
        VOUCHERS_DB[v.code.upper()] = v
    return VOUCHERS_DB


# Initialize data store on import
load_menu()
load_restaurant_info()
init_vouchers()


def get_all_menu_items() -> List[MenuItem]:
    """Returns list of all menu items."""
    if not MENU_DB:
        load_menu()
    return list(MENU_DB.values())


def get_menu_item_by_id(item_id: str) -> Optional[MenuItem]:
    """Finds menu item by ID or food name/keyword."""
    if not MENU_DB:
        load_menu()
    if not item_id or not isinstance(item_id, str):
        return None
    
    clean_id = item_id.strip()
    # 1. Exact ID match (case-insensitive)
    if clean_id.upper() in MENU_DB:
        return MENU_DB[clean_id.upper()]
    
    clean_norm = normalize_text(clean_id)
    clean_unaccent = remove_accents(clean_id)
    
    # 2. Exact Name match (case-insensitive & normalized)
    for item in MENU_DB.values():
        if normalize_text(item.name) == clean_norm:
            return item

    # 3. Substring Name match (e.g. "mỳ lạp sườn" in "Mỳ lạp sườn", "phở" in "Phở Bò Tái Nạm...")
    for item in MENU_DB.values():
        if clean_norm in normalize_text(item.name):
            return item

    # 4. Partial word match (dish name inside search query, e.g. "Mỳ lạp sườn" inside "cho 1 mỳ lạp sườn nhé")
    for item in MENU_DB.values():
        item_norm = normalize_text(item.name)
        if item_norm and item_norm in clean_norm:
            return item

    # 5. Exact/Substring Name match (unaccented fallback)
    for item in MENU_DB.values():
        if remove_accents(item.name) == clean_unaccent:
            return item

    for item in MENU_DB.values():
        item_unaccent = remove_accents(item.name)
        if clean_unaccent and clean_unaccent in item_unaccent:
            return item

    return None


def get_restaurant_data() -> Optional[RestaurantInfo]:
    """Gets restaurant info and branch details."""
    global RESTAURANT_INFO_CACHE
    if not RESTAURANT_INFO_CACHE:
        load_restaurant_info()
    return RESTAURANT_INFO_CACHE


def get_branch_by_id(branch_id: str) -> Optional[RestaurantBranch]:
    """Finds a specific branch by ID."""
    info = get_restaurant_data()
    if not info:
        return None
    for b in info.branches:
        if b.branch_id.upper() == branch_id.strip().upper():
            return b
    return None


def get_cart(session_id: str) -> Cart:
    """Gets or creates cart for given session_id."""
    if session_id not in CARTS_DB:
        CARTS_DB[session_id] = Cart(session_id=session_id, items=[])
    return CARTS_DB[session_id]


def update_cart_item(session_id: str, item_id: str, quantity: int, note: str = "") -> Tuple[bool, str, Cart]:
    """Adds, updates, or removes an item in user's cart."""
    cart = get_cart(session_id)
    item = get_menu_item_by_id(item_id)
    
    if not item:
        return False, f"Không tìm thấy món ăn với mã: '{item_id}'", cart

    if not item.is_available:
        return False, f"Món '{item.name}' hiện đã hết hàng.", cart

    # Find existing item in cart by item.id
    existing = next((i for i in cart.items if i.item_id.upper() == item.id.upper()), None)

    if quantity <= 0:
        if existing:
            cart.items.remove(existing)
            return True, f"Đã xóa món '{item.name}' khỏi giỏ hàng.", cart
        else:
            return False, f"Món '{item.name}' không có trong giỏ hàng.", cart

    if existing:
        existing.quantity = quantity
        if note:
            existing.note = note
        msg = f"Đã cập nhật số lượng món '{item.name}' thành {quantity}."
    else:
        cart_item = CartItem(
            item_id=item.id,
            name=item.name,
            price=item.price,
            quantity=quantity,
            note=note
        )
        cart.items.append(cart_item)
        msg = f"Đã thêm {quantity} x '{item.name}' vào giỏ hàng."

    return True, msg, cart


def clear_cart(session_id: str) -> bool:
    """Clears user cart."""
    if session_id in CARTS_DB:
        CARTS_DB[session_id].items = []
        return True
    return False


def calculate_totals(session_id: str, voucher_code: Optional[str] = None, shipping_distance_km: float = 2.0) -> Dict:
    """Calculates order totals including subtotal, shipping, voucher discount, final total."""
    cart = get_cart(session_id)
    subtotal = cart.subtotal

    # Shipping fee calculation (15,000 VND base + 5,000 VND per extra km over 2km)
    base_ship = 15000.0
    if shipping_distance_km > 2.0:
        extra_km = shipping_distance_km - 2.0
        shipping_fee = base_ship + (extra_km * 5000.0)
    else:
        shipping_fee = base_ship

    discount_amount = 0.0
    voucher_msg = ""

    if voucher_code:
        code_clean = voucher_code.strip().upper()
        if code_clean in VOUCHERS_DB:
            v = VOUCHERS_DB[code_clean]
            if subtotal < v.min_order_amount:
                voucher_msg = f"Mã '{code_clean}' yêu cầu đơn tối thiểu {v.min_order_amount:,.0f}đ."
            else:
                if code_clean == "FREESHIP":
                    discount_amount = min(shipping_fee, v.max_discount_amount)
                    voucher_msg = f"Áp dụng mã FREESHIP: giảm {discount_amount:,.0f}đ phí giao hàng."
                else:
                    raw_discount = subtotal * v.discount_percentage
                    discount_amount = min(raw_discount, v.max_discount_amount)
                    voucher_msg = f"Áp dụng mã '{code_clean}': giảm {discount_amount:,.0f}đ."
        else:
            voucher_msg = f"Mã giảm giá '{voucher_code}' không hợp lệ hoặc đã hết hạn."

    total_amount = max(0.0, subtotal + shipping_fee - discount_amount)

    return {
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
        "voucher_code": voucher_code,
        "voucher_msg": voucher_msg,
        "item_count": sum(i.quantity for i in cart.items)
    }


def save_order(order: Order) -> Order:
    """Saves completed order into ORDERS_DB."""
    ORDERS_DB[order.order_id] = order
    return order


def get_order_by_id(order_id: str) -> Optional[Order]:
    """Retrieves order by ID."""
    return ORDERS_DB.get(order_id.strip().upper())

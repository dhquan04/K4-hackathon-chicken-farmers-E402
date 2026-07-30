"""
In-Memory Database & Data Store Manager for Food Ordering Chatbot
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from project.codebase.schemas import Cart, CartItem, CustomerInfo, MenuItem, Order, Voucher

# Global In-Memory Storage
MENU_DB: Dict[str, MenuItem] = {}
CARTS_DB: Dict[str, Cart] = {}
ORDERS_DB: Dict[str, Order] = {}
VOUCHERS_DB: Dict[str, Voucher] = {}

MENU_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "menu.json")


def load_menu() -> Dict[str, MenuItem]:
    """Loads food menu from JSON file into MENU_DB."""
    global MENU_DB
    if not os.path.exists(MENU_FILE_PATH):
        return MENU_DB

    with open(MENU_FILE_PATH, "r", encoding="utf-8") as f:
        items_data = json.load(f)
        for data in items_data:
            item = MenuItem(**data)
            MENU_DB[item.id] = item
    return MENU_DB


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
init_vouchers()


def get_all_menu_items() -> List[MenuItem]:
    """Returns list of all menu items."""
    if not MENU_DB:
        load_menu()
    return list(MENU_DB.values())


def get_menu_item_by_id(item_id: str) -> Optional[MenuItem]:
    """Finds menu item by ID."""
    if not MENU_DB:
        load_menu()
    return MENU_DB.get(item_id)


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

    # Find existing item in cart
    existing = next((i for i in cart.items if i.item_id == item_id), None)

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

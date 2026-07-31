"""
Tool: Manage Cart
Quản lý giỏ hàng của người dùng (thêm, cập nhật, xóa, xem giỏ hàng, xóa sạch).
"""

from typing import Dict, Optional
try:
    from project.codebase.database import (
        clear_cart as db_clear_cart,
        get_cart,
        get_menu_item_by_id,
        update_cart_item,
    )
except ImportError:
    from database import (
        clear_cart as db_clear_cart,
        get_cart,
        get_menu_item_by_id,
        update_cart_item,
    )


def add_to_cart(session_id: str, item_id: str, quantity: int = 1, note: str = "") -> Dict:
    """
    Thêm món ăn vào giỏ hàng của người dùng.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.
        item_id (str): Mã món ăn (ví dụ: 'FOOD001').
        quantity (int): Số lượng muốn thêm (mặc định: 1).
        note (str): Ghi chú riêng cho món ăn (ví dụ: 'Không cho hành', 'Ít đường').

    Returns:
        Dict: Trạng thái kết quả và chi tiết giỏ hàng sau khi thêm.
    """
    if quantity <= 0:
        return {
            "status": "error",
            "message": "Số lượng thêm vào phải lớn hơn 0."
        }

    # Fetch existing item quantity if any using resolved item.id
    item = get_menu_item_by_id(item_id)
    target_id = item.id if item else item_id

    cart = get_cart(session_id)
    existing = next((i for i in cart.items if i.item_id.upper() == target_id.upper()), None)
    new_quantity = existing.quantity + quantity if existing else quantity

    success, msg, updated_cart = update_cart_item(session_id, item_id, new_quantity, note)

    return {
        "status": "success" if success else "error",
        "message": msg,
        "cart": _format_cart(updated_cart)
    }


def update_cart(session_id: str, item_id: str, quantity: int, note: str = "") -> Dict:
    """
    Cập nhật số lượng hoặc ghi chú của món ăn trong giỏ hàng. Nếu số lượng <= 0, món ăn sẽ bị xóa khỏi giỏ.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.
        item_id (str): Mã món ăn (ví dụ: 'FOOD001').
        quantity (int): Số lượng mới mong muốn.
        note (str): Ghi chú mới (nếu có).

    Returns:
        Dict: Trạng thái kết quả và chi tiết giỏ hàng cập nhật.
    """
    success, msg, updated_cart = update_cart_item(session_id, item_id, quantity, note)

    return {
        "status": "success" if success else "error",
        "message": msg,
        "cart": _format_cart(updated_cart)
    }


def remove_from_cart(session_id: str, item_id: str) -> Dict:
    """
    Xóa hẳn một món ăn khỏi giỏ hàng.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.
        item_id (str): Mã món ăn cần xóa.

    Returns:
        Dict: Kết quả xóa món khỏi giỏ hàng.
    """
    success, msg, updated_cart = update_cart_item(session_id, item_id, quantity=0)

    return {
        "status": "success" if success else "error",
        "message": msg,
        "cart": _format_cart(updated_cart)
    }


def view_cart(session_id: str) -> Dict:
    """
    Xem chi tiết các món đang có trong giỏ hàng của phiên hiện tại.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.

    Returns:
        Dict: Chi tiết các món ăn, số lượng, ghi chú và tạm tính tổng tiền giỏ hàng.
    """
    cart = get_cart(session_id)
    return {
        "status": "success",
        "cart": _format_cart(cart)
    }


def clear_cart(session_id: str) -> Dict:
    """
    Xóa sạch toàn bộ các món trong giỏ hàng.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.

    Returns:
        Dict: Thông báo kết quả làm sạch giỏ hàng.
    """
    db_clear_cart(session_id)
    return {
        "status": "success",
        "message": "Đã xóa sạch giỏ hàng.",
        "cart": {
            "session_id": session_id,
            "items": [],
            "subtotal": 0.0,
            "subtotal_formatted": "0đ",
            "total_items": 0
        }
    }


def _format_cart(cart) -> Dict:
    items_list = [
        {
            "item_id": item.item_id,
            "name": item.name,
            "price": item.price,
            "price_formatted": f"{item.price:,.0f}đ",
            "quantity": item.quantity,
            "note": item.note,
            "total_price": item.total_price,
            "total_price_formatted": f"{item.total_price:,.0f}đ"
        }
        for item in cart.items
    ]

    return {
        "session_id": cart.session_id,
        "items": items_list,
        "subtotal": cart.subtotal,
        "subtotal_formatted": f"{cart.subtotal:,.0f}đ",
        "total_items": sum(i.quantity for i in cart.items)
    }

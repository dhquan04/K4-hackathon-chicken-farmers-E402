"""
Tool: Create Order
Tạo và chốt đơn hàng chính thức từ giỏ hàng hiện tại.
"""

import random
import re
from datetime import datetime
from typing import Dict, Optional

try:
    from project.codebase.database import (
        calculate_totals,
        clear_cart,
        get_cart,
        save_order,
    )
    from project.codebase.schemas import CustomerInfo, Order
except ImportError:
    from database import (
        calculate_totals,
        clear_cart,
        get_cart,
        save_order,
    )
    from schemas import CustomerInfo, Order


def create_order(
    session_id: str,
    customer_name: str,
    phone_number: str,
    delivery_address: str,
    payment_method: str = "COD",
    note: Optional[str] = "",
    voucher_code: Optional[str] = None,
    shipping_distance_km: float = 2.0
) -> Dict:
    """
    Tạo đơn hàng chính thức từ giỏ hàng hiện tại của người dùng.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.
        customer_name (str): Họ và tên người nhận hàng.
        phone_number (str): Số điện thoại liên hệ nhận hàng.
        delivery_address (str): Địa chỉ giao hàng chi tiết.
        payment_method (str): Phương thức thanh toán ('COD', 'MOMO', 'ZALOPAY', 'BANK_TRANSFER'). Mặc định: 'COD'.
        note (Optional[str]): Ghi chú chung cho đơn hàng (ví dụ: 'Giao giờ hành chính', 'Gọi trước khi giao').
        voucher_code (Optional[str]): Mã giảm giá áp dụng (nếu có).
        shipping_distance_km (float): Khoảng cách giao hàng (km).

    Returns:
        Dict: Thông tin chi tiết đơn hàng đã đặt thành công hoặc thông báo lỗi nếu thiếu thông tin.
    """
    cart = get_cart(session_id)

    if not cart.items:
        return {
            "status": "error",
            "message": "Không thể tạo đơn hàng vì giỏ hàng đang trống."
        }

    # Validate customer info
    if not customer_name or not customer_name.strip():
        return {
            "status": "error",
            "message": "Vui lòng cung cấp tên người nhận hàng."
        }

    phone_clean = phone_number.strip()
    # Simple Vietnam phone validation (starts with 0, 10 digits)
    if not re.match(r"^0\d{9}$", phone_clean):
        return {
            "status": "error",
            "message": f"Số điện thoại '{phone_number}' không hợp lệ. Vui lòng nhập số điện thoại Việt Nam 10 chữ số (ví dụ: 0912345678)."
        }

    if not delivery_address or not delivery_address.strip():
        return {
            "status": "error",
            "message": "Vui lòng cung cấp địa chỉ giao hàng chi tiết."
        }

    valid_payment_methods = ["COD", "MOMO", "ZALOPAY", "BANK_TRANSFER"]
    payment_clean = payment_method.strip().upper()
    if payment_clean not in valid_payment_methods:
        return {
            "status": "error",
            "message": f"Phương thức thanh toán '{payment_method}' không hỗ trợ. Hỗ trợ: {', '.join(valid_payment_methods)}."
        }

    # Calculate totals
    totals = calculate_totals(session_id, voucher_code, shipping_distance_km)

    # Generate Order ID (e.g. ORD-10942)
    order_id = f"ORD-{random.randint(10000, 99999)}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    customer_info = CustomerInfo(
        customer_name=customer_name.strip(),
        phone_number=phone_clean,
        delivery_address=delivery_address.strip(),
        payment_method=payment_clean,
        note=note or ""
    )

    # Snapshot items in cart and convert to dicts to prevent Pydantic class identity mismatches
    order_items = list(cart.items)
    items_dicts = [
        item.model_dump() if hasattr(item, "model_dump") else (item.dict() if hasattr(item, "dict") else item)
        for item in order_items
    ]
    customer_dict = (
        customer_info.model_dump() if hasattr(customer_info, "model_dump") else (customer_info.dict() if hasattr(customer_info, "dict") else customer_info)
    )

    order_obj = Order(
        order_id=order_id,
        session_id=session_id,
        customer=customer_dict,
        items=items_dicts,
        subtotal=totals["subtotal"],
        shipping_fee=totals["shipping_fee"],
        discount_amount=totals["discount_amount"],
        total_amount=totals["total_amount"],
        status="PREPARING",
        created_at=created_at,
        voucher_code=voucher_code.strip().upper() if voucher_code else None
    )

    save_order(order_obj)

    # Clear user cart after successful order
    clear_cart(session_id)

    return {
        "status": "success",
        "message": "Đặt hàng thành công!",
        "order": {
            "order_id": order_id,
            "status": order_obj.status,
            "created_at": created_at,
            "customer_name": customer_info.customer_name,
            "phone_number": customer_info.phone_number,
            "delivery_address": customer_info.delivery_address,
            "payment_method": customer_info.payment_method,
            "items": [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "price_formatted": f"{item.price:,.0f}đ",
                    "note": item.note
                }
                for item in order_items
            ],
            "subtotal_formatted": f"{totals['subtotal']:,.0f}đ",
            "shipping_fee_formatted": f"{totals['shipping_fee']:,.0f}đ",
            "discount_amount_formatted": f"{totals['discount_amount']:,.0f}đ",
            "total_amount_formatted": f"{totals['total_amount']:,.0f}đ",
            "estimated_delivery": "20 - 30 phút"
        }
    }

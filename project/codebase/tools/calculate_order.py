"""
Tool: Calculate Order
Tính toán chi phí đơn hàng (tiền món, phí giao hàng, giảm giá voucher, tổng chi phí).
"""

from typing import Dict, Optional
from project.codebase.database import calculate_totals, get_cart


def calculate_order(
    session_id: str,
    voucher_code: Optional[str] = None,
    shipping_distance_km: float = 2.0
) -> Dict:
    """
    Tính toán chi tiết chi phí cho giỏ hàng hiện tại, bao gồm tiền hàng, phí giao hàng, giảm giá voucher và số tiền thanh toán cuối cùng.

    Args:
        session_id (str): Mã phiên làm việc của người dùng.
        voucher_code (Optional[str]): Mã giảm giá (ví dụ: 'BATCH03', 'HELLOGROUP9', 'FREESHIP').
        shipping_distance_km (float): Khoảng cách giao hàng tính bằng km (mặc định: 2.0 km).

    Returns:
        Dict: Chi tiết bảng tính đơn hàng.
    """
    cart = get_cart(session_id)

    if not cart.items:
        return {
            "status": "warning",
            "message": "Giỏ hàng hiện đang trống. Vui lòng chọn món trước khi tính toán hóa đơn.",
            "subtotal": 0.0,
            "shipping_fee": 0.0,
            "discount_amount": 0.0,
            "total_amount": 0.0
        }

    totals = calculate_totals(
        session_id=session_id,
        voucher_code=voucher_code,
        shipping_distance_km=shipping_distance_km
    )

    return {
        "status": "success",
        "session_id": session_id,
        "item_count": totals["item_count"],
        "subtotal": totals["subtotal"],
        "subtotal_formatted": f"{totals['subtotal']:,.0f}đ",
        "shipping_distance_km": shipping_distance_km,
        "shipping_fee": totals["shipping_fee"],
        "shipping_fee_formatted": f"{totals['shipping_fee']:,.0f}đ",
        "voucher_applied": voucher_code.strip().upper() if voucher_code else None,
        "voucher_msg": totals["voucher_msg"],
        "discount_amount": totals["discount_amount"],
        "discount_amount_formatted": f"{totals['discount_amount']:,.0f}đ",
        "total_amount": totals["total_amount"],
        "total_amount_formatted": f"{totals['total_amount']:,.0f}đ"
    }

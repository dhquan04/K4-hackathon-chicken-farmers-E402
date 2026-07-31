"""
Tool: Track Order & Cancel Order
Tra cứu tiến độ đơn hàng và xử lý yêu cầu hủy đơn.
"""

from typing import Dict, Optional
try:
    from project.codebase.database import get_order_by_id
except ImportError:
    from database import get_order_by_id


def track_order(order_id: str) -> Dict:
    """
    Tra cứu trạng thái và thông tin chi tiết của đơn hàng bằng mã đơn.

    Args:
        order_id (str): Mã đơn hàng (ví dụ: 'ORD-10045').

    Returns:
        Dict: Trạng thái hiện tại của đơn hàng (PREPARING, DELIVERING, COMPLETED, CANCELLED) và chi tiết người nhận.
    """
    order = get_order_by_id(order_id)

    if not order:
        return {
            "status": "warning",
            "message": f"Không tìm thấy đơn hàng với mã '{order_id}'. Vui lòng kiểm tra lại mã đơn.",
            "order_id": order_id
        }

    status_description = {
        "PENDING": "Đã tiếp nhận đơn - Đang chờ xác nhận từ nhà bếp",
        "PREPARING": "Nhà bếp đang chế biến món ăn",
        "DELIVERING": "Tài xế đang trên đường giao hàng đến bạn",
        "COMPLETED": "Đơn hàng đã được giao thành công",
        "CANCELLED": "Đơn hàng đã bị hủy"
    }

    return {
        "status": "success",
        "order": {
            "order_id": order.order_id,
            "status_code": order.status,
            "status_display": status_description.get(order.status, order.status),
            "created_at": order.created_at,
            "customer_name": order.customer.customer_name,
            "phone_number": order.customer.phone_number,
            "delivery_address": order.customer.delivery_address,
            "payment_method": order.customer.payment_method,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "price_formatted": f"{item.price:,.0f}đ",
                    "note": item.note
                }
                for item in order.items
            ],
            "total_amount_formatted": f"{order.total_amount:,.0f}đ"
        }
    }


def cancel_order(order_id: str, reason: Optional[str] = "") -> Dict:
    """
    Yêu cầu hủy đơn hàng. Chỉ cho phép hủy khi đơn hàng ở trạng thái chờ (PENDING) hoặc đang chế biến (PREPARING).

    Args:
        order_id (str): Mã đơn hàng cần hủy.
        reason (Optional[str]): Lý do hủy đơn.

    Returns:
        Dict: Kết quả hủy đơn hàng hoặc lý do không thể hủy (nếu tài xế đã đi giao).
    """
    order = get_order_by_id(order_id)

    if not order:
        return {
            "status": "warning",
            "message": f"Không tìm thấy đơn hàng với mã '{order_id}' để hủy."
        }

    if order.status in ["DELIVERING", "COMPLETED"]:
        return {
            "status": "error",
            "message": f"Không thể hủy đơn hàng '{order_id}' vì đơn hàng đang ở trạng thái '{order.status}' (Tài xế đã nhận hàng/Đã giao). Vui lòng liên hệ hotline hỗ trợ."
        }

    if order.status == "CANCELLED":
        return {
            "status": "warning",
            "message": f"Đơn hàng '{order_id}' đã được hủy trước đó."
        }

    # Cancel order
    order.status = "CANCELLED"

    return {
        "status": "success",
        "message": f"Đã hủy đơn hàng '{order_id}' thành công.",
        "order_id": order_id,
        "reason": reason or "Người dùng yêu cầu hủy",
        "new_status": "CANCELLED"
    }

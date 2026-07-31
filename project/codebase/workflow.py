"""Điều phối yêu cầu của chatbot tới đúng các tools đặt món hiện có.

Workflow không đọc JSON trong ``data/`` trực tiếp. ``database.py`` phụ trách
nạp menu, còn file này chỉ chọn tool và truyền đúng tham số cho tool đó.
"""

from __future__ import annotations

from typing import Any

from project.codebase.tools.calculate_order import calculate_order
from project.codebase.tools.create_order import create_order
from project.codebase.tools.get_menu import get_menu
from project.codebase.tools.manage_cart import (
    add_to_cart,
    clear_cart,
    remove_from_cart,
    update_cart,
    view_cart,
)
from project.codebase.tools.search_food import search_food
from project.codebase.tools.track_order import track_order


SUPPORTED_TOOLS = {
    "search_food": "Tìm món theo tên, loại món hoặc mức giá.",
    "get_menu": "Xem thực đơn.",
    "manage_cart": "Xem, thêm, sửa số lượng, xoá hoặc làm trống giỏ.",
    "calculate_order": "Tính tạm tính, phí giao hàng và tổng tiền.",
    "create_order": "Tạo đơn sau khi khách xác nhận.",
    "track_order": "Tra cứu trạng thái đơn hàng bằng mã đơn.",
}

OUT_OF_SCOPE_MESSAGE = (
    "Mình chỉ hỗ trợ xem/tìm món, quản lý giỏ hàng, tính tiền, đặt món "
    "và theo dõi đơn. Bạn muốn dùng chức năng nào?"
)


def _normalise(text: str) -> str:
    return " ".join(text.lower().strip().split())


def detect_intent(message: str) -> str | None:
    """Nhận diện một trong sáu ý định được hỗ trợ, hoặc từ chối."""
    text = _normalise(message)
    if any(word in text for word in ("theo dõi", "trạng thái đơn", "đơn đang", "mã đơn")):
        return "track_order"
    if any(word in text for word in ("đặt hàng", "tạo đơn", "chốt đơn", "xác nhận đặt", "mua ngay")):
        return "create_order"
    if any(word in text for word in ("tổng tiền", "tính tiền", "thanh toán", "bao nhiêu tiền")):
        return "calculate_order"
    if any(word in text for word in ("giỏ hàng", "thêm", "bớt", "xoá", "xóa", "sửa số lượng")):
        return "manage_cart"
    if any(word in text for word in ("thực đơn", "menu", "có món gì", "danh sách món")):
        return "get_menu"
    if any(word in text for word in ("tìm", "search", "món", "đồ ăn", "ăn gì", "gà", "cơm", "bún", "phở", "trà")):
        return "search_food"
    return None


def _require(kwargs: dict[str, Any], *names: str) -> None:
    missing = [name for name in names if not kwargs.get(name)]
    if missing:
        raise ValueError(f"Vui lòng cung cấp: {', '.join(missing)}.")


def _manage_cart(session_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Map thao tác giỏ hàng tới các hàm thật trong manage_cart.py."""
    action = str(kwargs.get("action", "view")).lower()
    item_id = kwargs.get("item_id")
    quantity = kwargs.get("quantity", 1)
    note = kwargs.get("note", "")

    if action == "view":
        return view_cart(session_id=session_id)
    if action == "clear":
        return clear_cart(session_id=session_id)
    if action == "add":
        _require(kwargs, "item_id")
        return add_to_cart(session_id=session_id, item_id=item_id, quantity=quantity, note=note)
    if action == "update":
        _require(kwargs, "item_id", "quantity")
        return update_cart(session_id=session_id, item_id=item_id, quantity=quantity, note=note)
    if action == "remove":
        _require(kwargs, "item_id")
        return remove_from_cart(session_id=session_id, item_id=item_id)
    raise ValueError("Thao tác giỏ hàng không hợp lệ. Dùng: view, add, update, remove hoặc clear.")


def _run_tool(tool_name: str, session_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Call every tool using the parameter names defined in tools/*.py."""
    if tool_name == "search_food":
        _require(kwargs, "query")
        return search_food(
            query=kwargs["query"],
            max_price=kwargs.get("max_price"),
            is_vegetarian=kwargs.get("is_vegetarian"),
            is_spicy=kwargs.get("is_spicy"),
        )
    if tool_name == "get_menu":
        return get_menu(category=kwargs.get("category"))
    if tool_name == "manage_cart":
        return _manage_cart(session_id, kwargs)
    if tool_name == "calculate_order":
        return calculate_order(
            session_id=session_id,
            voucher_code=kwargs.get("voucher_code"),
            shipping_distance_km=kwargs.get("shipping_distance_km", 2.0),
        )
    if tool_name == "create_order":
        _require(kwargs, "customer_name", "phone_number", "delivery_address")
        return create_order(
            session_id=session_id,
            customer_name=kwargs["customer_name"],
            phone_number=kwargs["phone_number"],
            delivery_address=kwargs["delivery_address"],
            payment_method=kwargs.get("payment_method", "COD"),
            note=kwargs.get("note", ""),
            voucher_code=kwargs.get("voucher_code"),
            shipping_distance_km=kwargs.get("shipping_distance_km", 2.0),
        )
    if tool_name == "track_order":
        _require(kwargs, "order_id")
        return track_order(order_id=kwargs["order_id"])
    raise ValueError("Tool không được hỗ trợ.")


def run_tool_for_agent(
    tool_name: str,
    session_id: str,
    kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one tool for the LLM agent path (confirmation + error handling)."""
    kwargs = dict(kwargs or {})

    if tool_name not in SUPPORTED_TOOLS:
        return {
            "ok": False,
            "tool": tool_name,
            "message": OUT_OF_SCOPE_MESSAGE,
            "data": {"status": "error", "message": "Tool không được hỗ trợ."},
        }

    if tool_name == "create_order" and not kwargs.pop("confirmed", False):
        return {
            "ok": False,
            "tool": "create_order",
            "needs_confirmation": True,
            "message": "Bạn vui lòng xác nhận rõ: ‘Xác nhận đặt hàng’ trước khi mình tạo đơn.",
            "data": {"status": "error", "message": "Chưa xác nhận đặt hàng."},
        }

    try:
        data = _run_tool(tool_name, session_id, kwargs)
    except (TypeError, ValueError, KeyError) as error:
        return {
            "ok": False,
            "tool": tool_name,
            "message": str(error),
            "data": {"status": "error", "message": str(error)},
        }

    return {
        "ok": data.get("status") != "error",
        "tool": tool_name,
        "message": data.get("message", "Đã xử lý yêu cầu của bạn."),
        "data": data,
    }


def handle_message(
    user_id: str,
    message: str,
    *,
    tool_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Xử lý một tin nhắn và trả response chuẩn cho API/UI.

    ``agent.py`` cần trích xuất các trường trong ``tool_kwargs``. Ví dụ:
    ``{\"query\": \"gà\"}``, ``{\"action\": \"add\", \"item_id\": \"FOOD001\"}``,
    hoặc dữ liệu giao hàng cho ``create_order``.
    """
    if not isinstance(message, str) or not message.strip():
        return {"ok": False, "tool": None, "message": "Bạn muốn đặt món hoặc xem menu?"}

    tool_name = detect_intent(message)
    if tool_name is None:
        return {"ok": False, "tool": None, "message": OUT_OF_SCOPE_MESSAGE}

    kwargs = dict(tool_kwargs or {})
    session_id = str(kwargs.pop("session_id", user_id))
    if tool_name == "create_order" and not kwargs.pop("confirmed", False):
        return {
            "ok": False,
            "tool": "create_order",
            "needs_confirmation": True,
            "message": "Bạn vui lòng xác nhận rõ: ‘Xác nhận đặt hàng’ trước khi mình tạo đơn.",
        }

    try:
        data = _run_tool(tool_name, session_id, kwargs)
    except (TypeError, ValueError, KeyError) as error:
        return {"ok": False, "tool": tool_name, "message": str(error)}

    return {
        "ok": data.get("status") != "error",
        "tool": tool_name,
        "message": data.get("message", "Đã xử lý yêu cầu của bạn."),
        "data": data,
    }

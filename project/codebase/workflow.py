"""Business workflow for the food-ordering assistant.

This module is deliberately the gatekeeper for tool calls: a request can only
reach one of the six approved tools.  Everything else receives a clear,
in-scope refusal.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


SUPPORTED_TOOLS = {
    "search_food": "Tìm món theo tên, loại món hoặc mức giá.",
    "get_menu": "Xem thực đơn.",
    "manage_cart": "Xem, thêm, sửa số lượng hoặc xoá món trong giỏ.",
    "calculate_order": "Tính tạm tính, phí và tổng tiền của giỏ.",
    "create_order": "Tạo đơn sau khi khách xác nhận.",
    "track_order": "Tra cứu trạng thái đơn hàng.",
}

OUT_OF_SCOPE_MESSAGE = (
    "Mình chỉ hỗ trợ xem/tìm món, quản lý giỏ hàng, tính tiền, đặt món "
    "và theo dõi đơn. Bạn muốn dùng chức năng nào?"
)


def _normalise(text: str) -> str:
    return " ".join(text.lower().strip().split())


def detect_intent(message: str) -> str | None:
    """Map a Vietnamese message to exactly one approved tool, or None."""
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


def _load_tool(tool_name: str) -> Callable[..., Any]:
    """Load a tool lazily so workflow can be built before every tool is ready.

    Each tool module should expose a function with the same name as its file,
    for example ``tools/search_food.py`` exports ``search_food(...)``.
    """
    module = import_module(f"tools.{tool_name}")
    tool = getattr(module, tool_name, None)
    if not callable(tool):
        raise RuntimeError(f"tools.{tool_name} must export callable {tool_name}().")
    return tool


def handle_message(
    user_id: str,
    message: str,
    *,
    tool_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Handle one user message and return a response safe for the API/UI.

    ``tool_kwargs`` is supplied by ``agent.py`` after it extracts structured
    fields such as query, item_id, quantity, address, or order_id.
    """
    if not isinstance(message, str) or not message.strip():
        return {"ok": False, "tool": None, "message": "Bạn muốn đặt món hoặc xem menu?"}

    tool_name = detect_intent(message)
    if tool_name is None:
        return {"ok": False, "tool": None, "message": OUT_OF_SCOPE_MESSAGE}

    # Creating an order is an irreversible action: require explicit consent.
    kwargs = dict(tool_kwargs or {})
    if tool_name == "create_order" and not kwargs.pop("confirmed", False):
        return {
            "ok": False,
            "tool": "create_order",
            "needs_confirmation": True,
            "message": "Bạn vui lòng xác nhận rõ: ‘Xác nhận đặt hàng’ trước khi mình tạo đơn.",
        }

    try:
        result = _load_tool(tool_name)(user_id=user_id, **kwargs)
    except (ImportError, AttributeError, RuntimeError) as error:
        return {
            "ok": False,
            "tool": tool_name,
            "message": "Chức năng này đang được hoàn thiện, bạn thử lại sau nhé.",
            "error": str(error),
        }
    except (ValueError, KeyError) as error:
        return {"ok": False, "tool": tool_name, "message": str(error)}

    return {"ok": True, "tool": tool_name, "message": "Đã xử lý yêu cầu của bạn.", "data": result}

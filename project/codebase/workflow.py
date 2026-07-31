"""Điều phối yêu cầu của chatbot tới đúng các tools đặt món hiện có.

Workflow không đọc JSON trong ``data/`` trực tiếp. ``database.py`` phụ trách
nạp menu, còn file này chỉ chọn tool và truyền đúng tham số cho tool đó.
"""

from __future__ import annotations

import re
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

try:
    from project.codebase.database import get_menu_item_by_id
except ImportError:
    from database import get_menu_item_by_id


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


def _extract_recent_dish_name(chat_history: list[dict[str, Any]]) -> str | None:
    """Extract dish name from recent chat history turns by validating against database."""
    if not chat_history:
        return None

    candidates = []

    for msg in reversed(chat_history[-6:]):
        content = msg.get("content", "")
        if not content:
            continue

        # 1. User messages (e.g. user typed "Mỳ lạp sườn" or "Cơm gà chiên xối mỡ")
        if msg.get("role") == "user":
            candidates.append(content.strip())

        # 2. Match bold text **...**
        for b in re.findall(r'\*\*([^*]+)\*\*', content):
            candidates.append(b.strip())

        # 3. Match quotes '...' or "..."
        for q in re.findall(r"['\"]([^'\"]+)['\"]", content):
            candidates.append(q.strip())

        # 4. Match "món ..."
        for m in re.findall(r'món\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)(?=\s+cho|\s+giá|\s+với|\n|\.|\!|\?|$)', content, re.IGNORECASE):
            candidates.append(m.strip())

    for cand in candidates:
        if not cand or len(cand) < 2:
            continue
        clean_cand = re.sub(r'\([^)]*\)', '', cand).strip()
        item = get_menu_item_by_id(cand) or (get_menu_item_by_id(clean_cand) if clean_cand else None)
        if item:
            return item.id

    return None


def detect_intent(message: str, chat_history: list[dict[str, Any]] | None = None) -> str | None:
    """Nhận diện một trong sáu ý định được hỗ trợ, hoặc từ chối."""
    text = _normalise(message)

    # Guardrails: Out of scope keywords (programming, weather, jailbreaks, system info)
    if any(w in text for w in ("code", "python", "java", "c++", "hàm", "lập trình", "viết đoạn", "thời tiết", "api key", "mật khẩu", "quy tắc")):
        return None

    # Affirmative / confirmation words (e.g. "có", "ừ", "uk", "ok", "đúng", "cho vào giỏ", "thêm đi")
    if text in ("có", "co", "ừ", "u", "uk", "ok", "đúng", "dung", "đúng rồi", "dung roi", "cho vào giỏ", "thêm đi", "lấy đi", "lấy món này", "mua đi", "chốt", "đặt đi", "dạ có", "có ạ", "vâng", "cho vào"):
        return "manage_cart"

    # Direct food item name match check (e.g. user typed "trứng chiên", "mỳ lạp sườn", "nước ép dưa lưới")
    matched_item = get_menu_item_by_id(message)
    if matched_item and not any(search_word in text for search_word in ("tìm", "search", "xem", "menu", "thực đơn", "có món", "giá")):
        return "manage_cart"

    if any(word in text for word in ("theo dõi", "trạng thái đơn", "đơn đang", "mã đơn")):
        return "track_order"
    if any(word in text for word in ("xác nhận đặt", "tạo đơn", "chốt đơn", "thanh toán đơn")) or ("đặt hàng" in text and any(k in text for k in ("xác nhận", "sđt", "điện thoại", "địa chỉ", "tên", "vinhomes", "ocean park"))):
        return "create_order"
    if any(word in text for word in ("tổng tiền", "tính tiền", "thanh toán", "bao nhiêu tiền")):
        return "calculate_order"
    if any(word in text for word in ("dinh dưỡng", "cân bằng", "tư vấn", "thực đơn", "menu", "danh sách món", "gợi ý", "ăn gì", "đề xuất", "bán chạy", "mã giảm giá", "voucher", "khuyến mãi", "ưu đãi", "chào", "hi", "xin chào", "quán", "cửa hàng")) or ("có món" in text and not any(w in text for w in ("không cay", "chay", "dưới", "trên", "giá", "dưa hấu"))):
        return "get_menu"
    if any(word in text for word in ("giỏ hàng", "thêm", "bớt", "xoá", "xóa", "sửa số lượng", "đặt", "mua", "cho 1", "cho 2", "lấy 1", "lấy 2")):
        return "manage_cart"
    if any(word in text for word in ("tìm", "search", "đồ ăn", "gà", "cơm", "bún", "phở", "trà", "món", "mì", "mỳ", "nước", "lẩu", "pizza", "bánh")):
        return "search_food"
    return None


def _require(kwargs: dict[str, Any], *names: str) -> None:
    missing = [name for name in names if not kwargs.get(name)]
    if missing:
        raise ValueError(f"Vui lòng cung cấp: {', '.join(missing)}.")


def _manage_cart(session_id: str, kwargs: dict[str, Any], message: str = "") -> dict[str, Any]:
    """Map thao tác giỏ hàng tới các hàm thật trong manage_cart.py."""
    action = str(kwargs.get("action", "")).lower()
    
    if not action or action not in ("view", "clear", "add", "update", "remove"):
        msg_lower = message.lower()
        if get_menu_item_by_id(message) or any(w in msg_lower for w in ("thêm", "đặt", "mua", "cho", "lấy", "có", "ừ", "uk", "ok", "chốt", "vâng")):
            action = "add"
        elif any(w in msg_lower for w in ("xóa sạch", "làm trống", "clear")):
            action = "clear"
        elif any(w in msg_lower for w in ("xoá", "xóa", "bớt")):
            action = "remove"
        else:
            action = "view"

    item_id = kwargs.get("item_id")
    quantity = kwargs.get("quantity")
    note = kwargs.get("note", "")

    # Extract quantity from message if specified (e.g., "cho 2 phở", "đặt 3 mỳ lạp sườn")
    if quantity is None:
        q_match = re.search(r'\b(\d+)\b', message)
        if q_match:
            try:
                quantity = int(q_match.group(1))
            except ValueError:
                quantity = 1
        else:
            quantity = 1

    if action == "view":
        return view_cart(session_id=session_id)
    if action == "clear":
        return clear_cart(session_id=session_id)
    if action == "add":
        if not item_id and message:
            clean_msg = _normalise(message)
            if clean_msg in ("có", "co", "ừ", "u", "uk", "ok", "đúng", "dung", "đúng rồi", "dung roi", "cho vào giỏ", "thêm đi", "lấy đi", "lấy món này", "mua đi", "chốt", "đặt đi", "dạ có", "có ạ", "vâng", "cho vào"):
                history = kwargs.get("chat_history", [])
                item_id = _extract_recent_dish_name(history)
            else:
                matched = get_menu_item_by_id(message)
                if matched:
                    item_id = matched.id
                else:
                    pattern = r'\b(tôi|muốn|cho|mình|bạn|đặt|thêm|mua|lấy|vào|giỏ|hàng|ạ|nhé|giúp|suất|phần|bát|tô|cốc|ly|\d+)\b'
                    clean_name = re.sub(pattern, '', message, flags=re.IGNORECASE)
                    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                    item_id = clean_name or message

        if not item_id:
            history = kwargs.get("chat_history", [])
            item_id = _extract_recent_dish_name(history)

        _require({"item_id": item_id}, "item_id")
        return add_to_cart(session_id=session_id, item_id=item_id, quantity=quantity, note=note)
    if action == "update":
        _require(kwargs, "item_id", "quantity")
        return update_cart(session_id=session_id, item_id=item_id, quantity=quantity, note=note)
    if action == "remove":
        if not item_id and message:
            pattern = r'\b(xóa|xoá|bớt|khỏi|giỏ|hàng|ạ|nhé|giúp)\b'
            clean_name = re.sub(pattern, '', message, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            item_id = clean_name or message
        _require({"item_id": item_id}, "item_id")
        return remove_from_cart(session_id=session_id, item_id=item_id)
    raise ValueError("Thao tác giỏ hàng không hợp lệ. Dùng: view, add, update, remove hoặc clear.")


def _run_tool(tool_name: str, session_id: str, kwargs: dict[str, Any], message: str = "") -> dict[str, Any]:
    """Call every tool using the parameter names defined in tools/*.py."""
    if tool_name == "search_food":
        query = kwargs.get("query")
        max_price = kwargs.get("max_price")
        if max_price is None and message:
            price_match = re.search(r'(\d+)\s*(k|đ|đồng|nghìn|ngan)', message.lower())
            if price_match:
                val = float(price_match.group(1))
                if price_match.group(2) in ('k', 'nghìn', 'ngan'):
                    val *= 1000.0
                max_price = val

        if not query and message:
            pattern = r'\b(tôi|muốn|cho|mình|bạn|đặt|thêm|mua|lấy|tìm|search|gợi|ý|tư|vấn|món|ăn|giúp|với|ạ|nhé|1|2|3|4|5|suất|phần|bát|tô|cốc|ly|khoảng|\d+k|\d+\s*k|\d+)\b'
            clean_q = re.sub(pattern, '', message, flags=re.IGNORECASE)
            clean_q = re.sub(r'\s+', ' ', clean_q).strip()
            query = clean_q or ""
        
        res = search_food(
            query=query,
            max_price=max_price,
            is_vegetarian=kwargs.get("is_vegetarian"),
            is_spicy=kwargs.get("is_spicy"),
        )
        if res.get("status") == "warning" or not res.get("results"):
            if max_price:
                res = search_food(query="", max_price=max_price)
            if res.get("status") == "warning" or not res.get("results"):
                return get_menu()
        return res
    if tool_name == "get_menu":
        return get_menu(category=kwargs.get("category"))
    if tool_name == "manage_cart":
        return _manage_cart(session_id, kwargs, message)
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


def _format_tool_message(tool_name: str, data: dict[str, Any]) -> str:
    """Tạo câu trả lời tự nhiên, chi tiết bằng tiếng Việt cho kết quả của tool."""
    if not isinstance(data, dict):
        return "Đã xử lý yêu cầu của bạn."

    status = data.get("status")
    
    # If error or warning with message, return the message directly
    if status in ("error", "warning") and data.get("message"):
        return data["message"]

    if tool_name == "search_food":
        results = data.get("results", [])
        query = data.get("query", "")
        if results:
            items_str = "\n".join([
                f"• **{item['name']}** ({item['category']}): **{item['price_formatted']}** - *{item.get('description', '')}*"
                for item in results[:6]
            ])
            more_note = f"\n*(Và thêm {len(results)-6} món khác...)*" if len(results) > 6 else ""
            return f"🔍 Tìm thấy **{data.get('total_found', len(results))} món ăn** phù hợp với từ khóa '{query}':\n\n{items_str}{more_note}\n\n👉 Bạn muốn cho món nào vào giỏ hàng?"
        return data.get("message", f"Không tìm thấy món ăn nào phù hợp với từ khóa '{query}'.")

    if tool_name == "get_menu":
        items = data.get("items", [])
        cat = data.get("category_filter", "Tất cả")
        if items:
            items_str = "\n".join([
                f"• **{item['name']}** ({item['category']}): **{item['price_formatted']}**"
                for item in items[:10]
            ])
            more_note = f"\n*(Và thêm {len(items)-10} món khác trong menu...)*" if len(items) > 10 else ""
            return f"🍱 **Thực đơn ShopeeFood Ocean Park** (Danh mục: {cat}):\n\n{items_str}{more_note}\n\n👉 Bạn muốn chọn món nào ạ?"
        return data.get("message", "Thực đơn hiện tại chưa có món nào.")

    if tool_name == "manage_cart":
        msg = data.get("message", "")
        cart = data.get("cart", {})
        if cart:
            items = cart.get("items", [])
            subtotal = cart.get("subtotal_formatted", "0đ")
            total_count = cart.get("total_items", len(items))
            if items:
                items_str = "\n".join([
                    f"• **{item['name']}** x{item['quantity']} = **{item['total_price_formatted']}**" + (f" (*{item['note']}*)" if item.get("note") else "")
                    for item in items
                ])
                header = f"{msg}\n\n" if msg else ""
                return f"{header}🛒 **Chi tiết giỏ hàng ({total_count} món):**\n\n{items_str}\n\n👉 **Tạm tính:** {subtotal}"
            else:
                return f"{msg}\n\n🛒 Giỏ hàng của bạn hiện đang trống." if msg else "🛒 Giỏ hàng của bạn hiện đang trống."
        return msg or "Đã cập nhật giỏ hàng."

    if tool_name == "calculate_order":
        voucher_info = f"\n- Mã giảm giá: {data.get('voucher_msg')}" if data.get("voucher_msg") else ""
        return (
            f"🧮 **Bảng tính chi tiết chi phí đơn hàng:**\n"
            f"- Tạm tính tiền món ({data.get('item_count', 0)} món): **{data.get('subtotal_formatted')}**\n"
            f"- Phí giao hàng ({data.get('shipping_distance_km')} km): **{data.get('shipping_fee_formatted')}**\n"
            f"- Giảm giá: **-{data.get('discount_amount_formatted')}**{voucher_info}\n\n"
            f"👉 **TỔNG THANH TOÁN: {data.get('total_amount_formatted')}**\n\n"
            f"Bạn vui lòng cho mình xin *Họ tên, SĐT 10 số và Địa chỉ giao hàng* để chốt đơn nhé!"
        )

    if tool_name == "create_order":
        ord_info = data.get("order", {})
        if ord_info:
            return (
                f"🎉 **ĐẶT HÀNG THÀNH CÔNG! Mã đơn: #{ord_info.get('order_id')}**\n\n"
                f"- **Người nhận:** {ord_info.get('customer_name')} ({ord_info.get('phone_number')})\n"
                f"- **Địa chỉ giao:** {ord_info.get('delivery_address')}\n"
                f"- **Thanh toán:** {ord_info.get('payment_method')} • **{ord_info.get('total_amount_formatted')}**\n"
                f"- **Thời gian giao dự kiến:** {ord_info.get('estimated_delivery')}\n\n"
                f"Cảm ơn bạn đã đặt hàng tại FoodFlow!"
            )
        return data.get("message", "Đặt hàng thành công!")

    if tool_name == "track_order":
        ord_info = data.get("order", {})
        if ord_info:
            return (
                f"📦 **Thông tin đơn hàng #{ord_info.get('order_id')}**\n"
                f"- Trạng thái: **{ord_info.get('status')}**\n"
                f"- Khách hàng: {ord_info.get('customer_name')} ({ord_info.get('phone_number')})\n"
                f"- Tổng tiền: **{ord_info.get('total_amount_formatted')}**"
            )
        return data.get("message", "Đã tra cứu đơn hàng.")

    return data.get("message", "Đã xử lý yêu cầu của bạn.")


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
        fmt_msg = _format_tool_message(tool_name, data)
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
        "message": fmt_msg,
        "data": data,
    }


def handle_message(
    user_id: str,
    message: str,
    *,
    tool_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Xử lý một tin nhắn và trả response chuẩn cho API/UI."""
    if not isinstance(message, str) or not message.strip():
        return {"ok": False, "tool": None, "message": "Bạn muốn đặt món hoặc xem menu?"}

    kwargs = dict(tool_kwargs or {})
    chat_history = kwargs.get("chat_history", [])

    tool_name = detect_intent(message, chat_history=chat_history)
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
        data = _run_tool(tool_name, session_id, kwargs, message)
        fmt_msg = _format_tool_message(tool_name, data)
    except (TypeError, ValueError, KeyError) as error:
        return {"ok": False, "tool": tool_name, "message": str(error)}

    return {
        "ok": data.get("status") != "error",
        "tool": tool_name,
        "message": fmt_msg,
        "data": data,
    }

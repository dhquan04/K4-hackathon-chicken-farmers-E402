"""
Tool: Get Menu
Tra cứu danh sách thực đơn món ăn toàn bộ hoặc theo danh mục.
"""

from typing import Dict, List, Optional
try:
    from project.codebase.database import get_all_menu_items
except ImportError:
    from database import get_all_menu_items


def get_menu(category: Optional[str] = None) -> Dict:
    """
    Lấy danh sách các món ăn trong thực đơn nhà hàng.

    Args:
        category (Optional[str]): Danh mục món ăn (ví dụ: 'Cơm', 'Phở', 'Bún', 'Món chay', 'Đồ uống', 'Ăn vặt').
                                  Nếu để None hoặc rỗng, trả về toàn bộ thực đơn.

    Returns:
        Dict: Chứa danh sách các món ăn kèm thông tin chi tiết (mã món, tên, giá, mô tả, dị ứng).
    """
    all_items = get_all_menu_items()

    if category and category.strip():
        category_clean = category.strip().lower()
        filtered_items = [
            item for item in all_items
            if category_clean in item.category.lower()
        ]
    else:
        filtered_items = all_items

    categories_available = sorted(list(set(item.category for item in all_items)))

    if not filtered_items:
        return {
            "status": "warning",
            "message": f"Không tìm thấy món nào thuộc danh mục '{category}'.",
            "available_categories": categories_available,
            "items": []
        }

    formatted_items = [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price": item.price,
            "price_formatted": f"{item.price:,.0f}đ",
            "description": item.description,
            "is_vegetarian": item.is_vegetarian,
            "is_spicy": item.is_spicy,
            "allergens": item.allergens,
            "is_available": item.is_available
        }
        for item in filtered_items
    ]

    vouchers_info = []
    try:
        from project.codebase.database import VOUCHERS_DB
        vouchers_info = [
            {
                "code": v.code,
                "discount": f"{int(v.discount_percentage * 100)}%" if v.discount_percentage > 0 else f"Tối đa {v.max_discount_amount:,.0f}đ",
                "max_discount": f"{v.max_discount_amount:,.0f}đ",
                "min_order": f"{v.min_order_amount:,.0f}đ"
            }
            for v in VOUCHERS_DB.values()
        ]
    except Exception:
        pass

    return {
        "status": "success",
        "category_filter": category or "Tất cả",
        "total_items": len(formatted_items),
        "available_categories": categories_available,
        "available_vouchers": vouchers_info,
        "items": formatted_items
    }

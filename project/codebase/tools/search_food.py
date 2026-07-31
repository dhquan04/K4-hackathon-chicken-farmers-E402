"""
Tool: Search Food
Tìm kiếm món ăn theo từ khóa, mức giá, ăn chay hoặc độ cay.
"""

from typing import Dict, List, Optional
try:
    from project.codebase.database import get_all_menu_items, normalize_text, remove_accents
except ImportError:
    from database import get_all_menu_items, normalize_text, remove_accents


def search_food(
    query: str,
    max_price: Optional[float] = None,
    is_vegetarian: Optional[bool] = None,
    is_spicy: Optional[bool] = None
) -> Dict:
    """
    Tìm kiếm món ăn theo tên, mô tả hoặc các bộ lọc tùy chọn (giá tối đa, chay/mặn, cay).

    Args:
        query (str): Từ khóa tìm kiếm (ví dụ: 'gà', 'phở', 'bún', 'nấm', 'trà').
        max_price (Optional[float]): Mức giá tối đa mong muốn (đơn vị: VNĐ).
        is_vegetarian (Optional[bool]): True nếu chỉ tìm món thuần chay, False nếu tìm món mặn.
        is_spicy (Optional[bool]): True nếu chỉ tìm món cay, False nếu tìm món không cay.

    Returns:
        Dict: Danh sách các món ăn thỏa mãn tiêu chí tìm kiếm.
    """
    all_items = get_all_menu_items()
    query_clean = (query or "").strip()
    q_norm = normalize_text(query_clean)
    q_unaccent = remove_accents(query_clean)

    results = []
    for item in all_items:
        name_norm = normalize_text(item.name)
        cat_norm = normalize_text(item.category)
        desc_norm = normalize_text(item.description or "")

        match_query = False
        if not query_clean:
            match_query = True
        else:
            match_query = (
                q_norm in name_norm or
                q_norm in cat_norm or
                q_norm in desc_norm or
                (bool(q_unaccent) and (
                    q_unaccent in remove_accents(item.name) or
                    q_unaccent in remove_accents(item.category) or
                    q_unaccent in remove_accents(item.description or "")
                ))
            )

        if not match_query:
            continue

        # Match max price
        if max_price is not None and item.price > max_price:
            continue

        # Match vegetarian
        if is_vegetarian is not None and item.is_vegetarian != is_vegetarian:
            continue

        # Match spicy
        if is_spicy is not None and item.is_spicy != is_spicy:
            continue

        results.append({
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
        })

    if not results:
        filters_str = []
        if max_price: filters_str.append(f"giá $\le$ {max_price:,.0f}đ")
        if is_vegetarian: filters_str.append("thuần chay")
        if is_spicy is not None: filters_str.append("cay" if is_spicy else "không cay")
        
        filter_text = f" với bộ lọc ({', '.join(filters_str)})" if filters_str else ""
        return {
            "status": "warning",
            "message": f"Không tìm thấy món ăn nào phù hợp với từ khóa '{query}'{filter_text}.",
            "query": query,
            "results": []
        }

    return {
        "status": "success",
        "query": query,
        "total_found": len(results),
        "results": results
    }

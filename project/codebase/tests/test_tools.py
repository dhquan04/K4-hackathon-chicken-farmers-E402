"""
Unit tests for AI Agent Food Ordering Tools
"""

import unittest
from project.codebase.tools import (
    add_to_cart,
    calculate_order,
    cancel_order,
    clear_cart,
    create_order,
    estimate_delivery_distance,
    get_menu,
    get_store_location,
    remove_from_cart,
    search_food,
    track_order,
    update_cart,
    view_cart,
)


class TestFoodOrderingTools(unittest.TestCase):

    def setUp(self):
        self.session_id = "test_session_1001"
        clear_cart(self.session_id)

    def test_get_menu(self):
        # Fetch all menu
        result = get_menu()
        self.assertEqual(result["status"], "success")
        self.assertGreater(len(result["items"]), 0)

        # Fetch menu by category 'Cơm'
        com_result = get_menu(category="Cơm")
        self.assertEqual(com_result["status"], "success")
        for item in com_result["items"]:
            self.assertEqual(item["category"], "Cơm")

    def test_search_food(self):
        res = search_food(query="phở")
        self.assertEqual(res["status"], "success")
        self.assertGreater(len(res["results"]), 0)

        # Search vegetarian
        veg_res = search_food(query="", is_vegetarian=True)
        self.assertEqual(veg_res["status"], "success")
        for item in veg_res["results"]:
            self.assertTrue(item["is_vegetarian"])

    def test_manage_cart_flow(self):
        # Add to cart
        res1 = add_to_cart(self.session_id, "FOOD001", quantity=2, note="Nhiều dưa chua")
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["cart"]["total_items"], 2)

        # Add another item
        res2 = add_to_cart(self.session_id, "FOOD010", quantity=1)
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["cart"]["total_items"], 3)

        # Update cart item
        res3 = update_cart(self.session_id, "FOOD001", quantity=1)
        self.assertEqual(res3["status"], "success")
        self.assertEqual(res3["cart"]["total_items"], 2)

        # Remove item
        res4 = remove_from_cart(self.session_id, "FOOD010")
        self.assertEqual(res4["status"], "success")
        self.assertEqual(res4["cart"]["total_items"], 1)

    def test_calculate_and_create_order(self):
        # Add item to cart
        add_to_cart(self.session_id, "FOOD001", quantity=2)  # 2 x 55k = 110k

        # Calculate totals with voucher
        calc = calculate_order(self.session_id, voucher_code="BATCH03", shipping_distance_km=3.0)
        self.assertEqual(calc["status"], "success")
        self.assertEqual(calc["subtotal"], 110000.0)
        self.assertGreater(calc["discount_amount"], 0)

        # Create order
        order_res = create_order(
            session_id=self.session_id,
            customer_name="Nguyễn Văn A",
            phone_number="0912345678",
            delivery_address="123 Đường Lê Lợi, Q.1, TP.HCM",
            payment_method="COD",
            note="Gọi khi tới",
            voucher_code="BATCH03"
        )
        self.assertEqual(order_res["status"], "success")
        order_id = order_res["order"]["order_id"]
        self.assertTrue(order_id.startswith("ORD-"))

        # Verify cart is empty after order
        cart_res = view_cart(self.session_id)
        self.assertEqual(cart_res["cart"]["total_items"], 0)

        # Track order
        track_res = track_order(order_id)
        self.assertEqual(track_res["status"], "success")
        self.assertEqual(track_res["order"]["status_code"], "PREPARING")

        # Cancel order
        cancel_res = cancel_order(order_id, reason="Đổi ý")
        self.assertEqual(cancel_res["status"], "success")

        # Re-track order
        track_res2 = track_order(order_id)
        self.assertEqual(track_res2["order"]["status_code"], "CANCELLED")

    def test_store_location_and_distance(self):
        # Fetch store location
        loc_res = get_store_location()
        self.assertEqual(loc_res["status"], "success")
        self.assertGreater(loc_res["total_branches"], 0)

        # Fetch specific branch
        b_res = get_store_location(branch_id="BRANCH01")
        self.assertEqual(b_res["status"], "success")
        self.assertEqual(b_res["branch"]["branch_id"], "BRANCH01")

        # Estimate delivery distance
        dist_res = estimate_delivery_distance(user_address="456 Đường Điện Biên Phủ, Quận Bình Thạnh")
        self.assertEqual(dist_res["status"], "success")
        self.assertGreater(dist_res["estimated_distance_km"], 0)
        self.assertGreater(dist_res["shipping_fee"], 0)
        self.assertIn("google.com/maps", dist_res["directions_url"])


if __name__ == "__main__":
    unittest.main()

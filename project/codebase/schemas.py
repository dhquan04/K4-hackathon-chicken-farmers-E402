"""
Pydantic Schemas for Food Ordering Chatbot
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    id: str
    name: str
    category: str
    price: float
    description: str
    branch_id: Optional[str] = None
    is_vegetarian: bool = False
    is_spicy: bool = False
    allergens: List[str] = Field(default_factory=list)
    is_available: bool = True



class CartItem(BaseModel):
    item_id: str
    name: str
    price: float
    quantity: int
    note: Optional[str] = ""

    @property
    def total_price(self) -> float:
        return self.price * self.quantity


class Cart(BaseModel):
    session_id: str
    items: List[CartItem] = Field(default_factory=list)

    @property
    def subtotal(self) -> float:
        return sum(item.price * item.quantity for item in self.items)


class Voucher(BaseModel):
    code: str
    discount_percentage: float = 0.0  # e.g., 0.10 for 10%
    max_discount_amount: float = 50000.0
    min_order_amount: float = 0.0
    is_active: bool = True


class CustomerInfo(BaseModel):
    customer_name: str
    phone_number: str
    delivery_address: str
    payment_method: str = "COD"  # COD, MOMO, ZALOPAY, BANK_TRANSFER
    note: Optional[str] = ""


class Order(BaseModel):
    order_id: str
    session_id: str
    customer: CustomerInfo
    items: List[CartItem]
    subtotal: float
    shipping_fee: float
    discount_amount: float
    total_amount: float
    status: str = "PREPARING"  # PENDING, PREPARING, DELIVERING, COMPLETED, CANCELLED
    created_at: str
    voucher_code: Optional[str] = None


class RestaurantBranch(BaseModel):
    branch_id: str
    branch_name: str
    address: str
    latitude: float
    longitude: float
    google_maps_url: str
    embed_map_url: str
    is_active: bool = True


class RestaurantInfo(BaseModel):
    restaurant_name: str
    hotline: str
    opening_hours: str
    branches: List[RestaurantBranch] = Field(default_factory=list)

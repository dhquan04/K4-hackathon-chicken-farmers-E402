"""
FastAPI REST API Routes for Food Flow Chatbot Backend
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from project.codebase.agent import run_agent
from project.codebase.tools.get_menu import get_menu
from project.codebase.tools.manage_cart import add_to_cart, clear_cart, view_cart
from project.codebase.tools.track_order import track_order

router = APIRouter(prefix="/api", tags=["FoodFlow API"])


class ChatRequest(BaseModel):
    user_id: str = "user_default"
    session_id: Optional[str] = "session_default"
    message: str
    tool_kwargs: Optional[Dict[str, Any]] = None


class AddCartRequest(BaseModel):
    item_id: str
    quantity: int = 1
    note: Optional[str] = ""


@router.get("/health")
def health_check():
    """Service health check endpoint."""
    return {"status": "ok", "service": "FoodFlow AI Agent Backend", "version": "1.0.0"}


@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    Main Chatbot API Endpoint.
    Receives user message and returns agent workflow response.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = run_agent(
        user_id=req.user_id,
        message=req.message,
        session_id=req.session_id,
        tool_kwargs=req.tool_kwargs
    )
    return result


@router.get("/menu")
def get_menu_endpoint(category: Optional[str] = Query(None, description="Optional category filter")):
    """Retrieves full menu or filtered by category."""
    return get_menu(category=category)


@router.get("/cart/{session_id}")
def view_cart_endpoint(session_id: str):
    """Retrieves user cart details."""
    return view_cart(session_id=session_id)


@router.post("/cart/{session_id}/add")
def add_to_cart_endpoint(session_id: str, req: AddCartRequest):
    """Adds a dish to user cart."""
    return add_to_cart(session_id=session_id, item_id=req.item_id, quantity=req.quantity, note=req.note or "")


@router.delete("/cart/{session_id}")
def clear_cart_endpoint(session_id: str):
    """Clears user cart."""
    success = clear_cart(session_id=session_id)
    return {"status": "success" if success else "warning", "message": "Giỏ hàng đã được xóa sạch."}


@router.get("/order/{order_id}")
def track_order_endpoint(order_id: str):
    """Tracks order status by order ID."""
    return track_order(order_id=order_id)

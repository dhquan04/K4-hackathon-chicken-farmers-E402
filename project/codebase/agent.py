"""
FoodFlow AI Agent - LLM Integration & Workflow Dispatcher
Handles system prompts, OpenAI tool calling or fallback workflow execution.
"""

import json
import os
from typing import Any, Dict, Optional
from project.codebase.workflow import handle_message, detect_intent

PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "prompts.md")


def load_system_prompt() -> str:
    """Reads system prompt from artifacts/prompts.md or returns default."""
    if os.path.exists(PROMPT_FILE_PATH):
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return (
        "Bạn là FoodFlow, trợ lý AI hỗ trợ đặt món ăn bằng tiếng Việt tại Vinhomes Ocean Park. "
        "Chỉ hỗ trợ: Tìm món, Xem menu, Quản lý giỏ hàng, Tính tiền, Tạo đơn, Theo dõi đơn."
    )


class FoodOrderingAgent:
    """Agent class coordinating user messages, LLM tool calls, and workflow execution."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.system_prompt = load_system_prompt()

    def process_message(self, user_id: str, message: str, session_id: Optional[str] = None, tool_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message via Workflow dispatcher or OpenAI function calling if key present.
        """
        sid = session_id or user_id
        
        # If no OpenAI API key or offline mode, use intelligent workflow rule dispatcher
        if not self.api_key:
            return self._fallback_process(user_id=user_id, message=message, session_id=sid, tool_kwargs=tool_kwargs)

        # Attempt OpenAI ChatCompletion tool call
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            # Simple prompt-driven tool resolution wrapper
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.2
            )
            ai_text = response.choices[0].message.content or ""
            
            # Dispatch to workflow
            res = handle_message(user_id=user_id, message=message, tool_kwargs=tool_kwargs)
            if res.get("ok"):
                res["ai_response"] = ai_text or res.get("message")
            return res

        except Exception as e:
            # Fallback to workflow engine if LLM call fails
            res = self._fallback_process(user_id=user_id, message=message, session_id=sid, tool_kwargs=tool_kwargs)
            res["notice"] = f"Processed via fallback workflow engine ({str(e)})"
            return res

    def _fallback_process(self, user_id: str, message: str, session_id: str, tool_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Rule-based workflow execution."""
        kwargs = dict(tool_kwargs or {})
        kwargs["session_id"] = session_id
        return handle_message(user_id=user_id, message=message, tool_kwargs=kwargs)


# Helper function for quick invocation
def run_agent(user_id: str, message: str, session_id: Optional[str] = None, tool_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    agent = FoodOrderingAgent()
    return agent.process_message(user_id=user_id, message=message, session_id=session_id, tool_kwargs=tool_kwargs)

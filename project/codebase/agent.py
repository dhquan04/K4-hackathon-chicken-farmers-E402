"""
FoodFlow AI Agent - LLM Integration & Workflow Dispatcher
Handles system prompts, OpenAI tool calling or fallback workflow execution.
"""

import json
import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

try:
    from project.codebase.workflow import handle_message, detect_intent
except ImportError:
    from workflow import handle_message, detect_intent

PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "prompts.md")


def load_system_prompt() -> str:
    """Reads system prompt from artifacts/prompts.md or returns default."""
    if os.path.exists(PROMPT_FILE_PATH):
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return (
        "Bạn là FoodFlow, trợ lý AI hỗ trợ đặt món ăn bằng tiếng Việt tại Vinhomes Ocean Park & Hà Nội. "
        "Chỉ hỗ trợ: Tìm món, Xem menu, Quản lý giỏ hàng, Tính tiền, Tạo đơn, Theo dõi đơn. "
        "Trả lời thân thiện, lịch sự và ngắn gọn."
    )


class FoodOrderingAgent:
    """Agent class coordinating user messages, LLM tool calls, and workflow execution."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.system_prompt = load_system_prompt()

    def process_message(self, user_id: str, message: str, session_id: Optional[str] = None, tool_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message via Workflow dispatcher and OpenAI LLM synthesis.
        """
        sid = session_id or user_id
        kwargs = dict(tool_kwargs or {})
        if "session_id" not in kwargs:
            kwargs["session_id"] = sid
        
        # Dispatch workflow tools first to fetch accurate data
        res = handle_message(user_id=user_id, message=message, tool_kwargs=kwargs)

        # If OpenAI API Key is present, enhance response with OpenAI LLM
        current_key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
        if current_key:
            try:
                import openai
                client = openai.OpenAI(api_key=current_key)
                
                # Context payload from workflow tool execution
                context_str = json.dumps(res, ensure_ascii=False)
                
                prompt_messages = [
                    {
                        "role": "system", 
                        "content": self.system_prompt + "\n\nHãy tổng hợp câu trả lời tự nhiên, tư vấn chu đáo cho khách hàng dựa trên dữ liệu hệ thống dưới đây."
                    },
                    {
                        "role": "user", 
                        "content": f"Câu hỏi của người dùng: '{message}'\n\nDữ liệu từ hệ thống:\n{context_str}"
                    }
                ]
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=prompt_messages,
                    temperature=0.3,
                    max_tokens=450
                )
                
                ai_text = response.choices[0].message.content or ""
                if ai_text:
                    res["ai_response"] = ai_text
                    res["llm_engine"] = f"OpenAI Live ({self.model})"
            except Exception as e:
                res["notice"] = f"Processed via fallback workflow engine ({str(e)})"

        if "ai_response" not in res or not res["ai_response"]:
            res["ai_response"] = res.get("message", "Đã xử lý yêu cầu.")
            res["llm_engine"] = "Rule Workflow Engine"

        return res


# Helper function for quick invocation
def run_agent(user_id: str, message: str, session_id: Optional[str] = None, tool_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    agent = FoodOrderingAgent()
    return agent.process_message(user_id=user_id, message=message, session_id=session_id, tool_kwargs=tool_kwargs)

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


def resolve_llm_credentials(api_key: Optional[str] = None, model: Optional[str] = None):
    """Resolves API key, base URL, and model for OpenAI/Groq LLM invocation."""
    key = (
        api_key
        or os.environ.get("OPENAI_API_KEY", "")
        or os.environ.get("OPENAI_api_key", "")
        or os.environ.get("GROQ_API_KEY", "")
        or os.environ.get("api", "")
        or os.environ.get("api_key", "")
    )
    base_url = os.environ.get("OPENAI_BASE_URL", None)
    selected_model = model or os.environ.get("OPENAI_MODEL", None)

    if key and key.startswith("sk-"):
        # Official OpenAI key
        base_url = None
        selected_model = selected_model or "gpt-4o-mini"
        engine_name = f"OpenAI Live Agent ({selected_model})"
    elif key and key.startswith("gsk_"):
        # Groq key
        base_url = base_url or "https://api.groq.com/openai/v1"
        selected_model = selected_model or "llama-3.3-70b-versatile"
        engine_name = f"Groq LLM Agent ({selected_model})"
    else:
        selected_model = selected_model or "gpt-4o-mini"
        engine_name = f"OpenAI Live Agent ({selected_model})"

    return key, base_url, selected_model, engine_name


def _trim_context_for_llm(res: Dict[str, Any]) -> str:
    """Trims large lists in tool response data to prevent LLM token limit errors."""
    try:
        trimmed = dict(res)
        if "data" in trimmed and isinstance(trimmed["data"], dict):
            data = dict(trimmed["data"])
            if "results" in data and isinstance(data["results"], list):
                data["results"] = data["results"][:15]
            if "items" in data and isinstance(data["items"], list):
                data["items"] = data["items"][:15]
            if "available_categories" in data and isinstance(data["available_categories"], list):
                data["available_categories"] = data["available_categories"][:10]
            trimmed["data"] = data
        return json.dumps(trimmed, ensure_ascii=False)
    except Exception:
        return json.dumps(res, ensure_ascii=False)


class FoodOrderingAgent:
    """Agent class coordinating user messages, LLM tool calls, and workflow execution."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.system_prompt = load_system_prompt()

    def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        tool_kwargs: Optional[Dict[str, Any]] = None,
        chat_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process user message via Workflow dispatcher and LLM synthesis with multi-turn memory.
        """
        sid = session_id or user_id
        kwargs = dict(tool_kwargs or {})
        if "session_id" not in kwargs:
            kwargs["session_id"] = sid
        if chat_history and "chat_history" not in kwargs:
            kwargs["chat_history"] = chat_history
        
        # Dispatch workflow tools first to fetch accurate data
        res = handle_message(user_id=user_id, message=message, tool_kwargs=kwargs)

        key, base_url, selected_model, engine_name = resolve_llm_credentials(self.api_key, self.model)

        if key:
            try:
                import openai
                client_kwargs = {"api_key": key}
                if base_url:
                    client_kwargs["base_url"] = base_url

                client = openai.OpenAI(**client_kwargs)
                
                context_str = _trim_context_for_llm(res)
                
                prompt_messages = [
                    {
                        "role": "system", 
                        "content": (
                            self.system_prompt
                            + "\n\nHãy là một trợ lý AI bán hàng cực kỳ thân thiện, chu đáo, xưng 'mình' và gọi khách hàng là 'bạn'. "
                            "Dựa vào lịch sử trò chuyện và dữ liệu hệ thống bên dưới để tư vấn cho khách hàng: "
                            "1. QUY TẮC QUAN TRỌNG VỀ THỰC ĐƠN: Bạn CHỈ ĐƯỢC tư vấn hoặc gợi ý những món ăn CÓ THẬT TRONG DỮ LIỆU HỆ THỐNG bên dưới. Tuyệt đối không tự bịa ra tên món hoặc giá tiền không có trong danh sách. "
                            "2. QUY TẮC XÁC NHẬN GIỎ HÀNG: Khi dữ liệu hệ thống bên dưới báo 'ok': true (hoặc đã thêm giỏ hàng thành công), bạn mới được thông báo là đã thêm món vào giỏ hàng. Nếu dữ liệu hệ thống báo 'ok': false hoặc có lỗi, bạn PHẢI THÀNH THẬT báo cho khách là món đó không có sẵn và gợi ý các món tương tự có trong menu, TUYỆT ĐỐI KHÔNG ĐƯỢC NÓI LÀ ĐÃ THÊM VÀO GIỎ HÀNG khi chưa thêm được. "
                            "3. Nếu khách thêm/xóa/xem giỏ hàng: Báo rõ các món trong giỏ và tổng tiền tạm tính. "
                            "4. Nếu khách tính tiền/đặt đơn: Báo chi tiết tạm tính, phí ship, mã giảm giá và tổng thanh toán. "
                            "5. Trả lời bằng tiếng Việt ngắn gọn, sinh động, dùng emoji thích hợp."
                        )
                    }
                ]
                
                # Append recent multi-turn chat history (last 6 messages)
                if chat_history:
                    for h in chat_history[-6:]:
                        r = "assistant" if h.get("role") == "assistant" else "user"
                        prompt_messages.append({"role": r, "content": h.get("content", "")})

                # Append current user prompt & tool execution context
                prompt_messages.append({
                    "role": "user", 
                    "content": f"Tin nhắn mới của khách: '{message}'\n\nDữ liệu từ hệ thống:\n{context_str}"
                })
                
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=prompt_messages,
                    temperature=0.4,
                    max_tokens=500
                )
                
                ai_text = response.choices[0].message.content or ""
                if ai_text:
                    res["ai_response"] = ai_text
                    res["llm_engine"] = engine_name
            except Exception as e:
                res["notice"] = f"Processed via fallback workflow engine ({str(e)})"

        if "ai_response" not in res or not res["ai_response"]:
            res["ai_response"] = res.get("message", "Đã xử lý yêu cầu.")
            res["llm_engine"] = "Rule Workflow Engine"

        return res


# Helper function for quick invocation
def run_agent(
    user_id: str,
    message: str,
    session_id: Optional[str] = None,
    tool_kwargs: Optional[Dict[str, Any]] = None,
    chat_history: Optional[list] = None
) -> Dict[str, Any]:
    agent = FoodOrderingAgent()
    return agent.process_message(
        user_id=user_id,
        message=message,
        session_id=session_id,
        tool_kwargs=tool_kwargs,
        chat_history=chat_history
    )
